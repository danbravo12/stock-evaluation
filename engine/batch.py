"""Company ledger, batch runner and PROGRESS.md (ADR-023 sections 1 and 2, ADR-056).

The company ledger (`data/ledger/companies.json`, next to the request ledger) holds one row per company: status, model, calls, tokens,
actual and notional cost, timestamp. A batch skips companies that are done (or done with warnings) unless forced, and stops cleanly when
the free quota or the budget cap is reached, so running it again the next Pacific day resumes where it stopped.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.llm.client import LLMFixtureMissing, load_models_config
from engine.orchestrator import analyse
from engine.report import Result
from engine.settings import Settings
from engine.universe import Universe

STATUSES = ("done", "warning", "failed")


class CompanyLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.rows: dict[str, dict] = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.rows, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def upsert(self, key: str, row: dict) -> None:
        self.rows[key] = row
        self.save()

    def status_of(self, key: str) -> str | None:
        return self.rows.get(key, {}).get("status")


def row_from_result(result: Result, now: datetime | None = None) -> tuple[str, dict]:
    key = result.plan.cik or result.plan.ticker
    status = "failed" if (result.scorecard is None or not result.plan.in_scope) else ("warning" if result.warnings else "done")
    c = result.cost
    return key, {"ticker": result.plan.ticker, "cik": result.plan.cik, "status": status, "model": result.run.model_profile, "mode": result.run.mode,
                 "calls": c.llm_calls, "input_tokens": c.input_tokens, "output_tokens": c.output_tokens, "actual_cost_usd": c.actual_cost_usd,
                 "notional_cost_usd": c.notional_cost_usd, "warnings": len(result.warnings),
                 "message": "; ".join(w.message for w in result.warnings)[:400],
                 "finished_at": (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()}


@dataclass
class BatchOutcome:
    done: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    stopped: str | None = None  # why the batch stopped early (quota / budget / missing fixture)


def run_batch(symbols: list[str], *, mode: str, settings: Settings, universe: Universe, ledger: CompanyLedger, limit: int | None = None, force: bool = False,
              analyse_fn: Callable[..., Result] = analyse, out: Callable[[str], None] = print, now: Callable[[], datetime] | None = None, **kwargs) -> BatchOutcome:
    """Analyse `symbols` in order. Companies already done are skipped (resume); the first quota or budget error stops the batch cleanly."""
    outcome = BatchOutcome()
    attempted = 0
    for sym in symbols:
        row = universe.row_for(sym)
        key = (universe.primary_of(row).cik if row and universe.primary_of(row) else sym)
        if not force and ledger.status_of(key) in ("done", "warning"):
            outcome.skipped.append(sym)
            continue
        if limit is not None and attempted >= limit:
            break
        attempted += 1
        try:
            result = analyse_fn(sym, mode=mode, settings=settings, universe=universe, **kwargs)
        except QuotaReached as e:
            outcome.stopped = f"Free-tier quota reached ({e}). Resume after midnight Pacific: run the same command again; finished companies are skipped."
            break
        except BudgetExceeded as e:
            outcome.stopped = f"Budget cap reached ({e}). Raise the cap in config/models.json or wait; run the same command again to resume."
            break
        except LLMFixtureMissing as e:
            outcome.stopped = f"No recorded model response for {sym} in replay mode ({str(e)[:120]}). Use --mode live or record."
            break
        k, r = row_from_result(result, now() if now else None)
        ledger.upsert(k, r)
        outcome.done.append(sym)
        out(f"{sym}: {r['status']} · {r['calls']} calls · {r['input_tokens'] + r['output_tokens']:,} tokens · notional ${r['notional_cost_usd']:.4f} · actual ${r['actual_cost_usd']:.4f}"
            + (f" · {r['warnings']} warnings" if r["warnings"] else ""))
    if outcome.stopped:
        out("STOPPED: " + outcome.stopped)
    return outcome


def progress_markdown(ledger: CompanyLedger, universe: Universe, config: dict | None = None) -> str:
    """The text of PROGRESS.md: counts, spend, measured calls per company, projected paid cost and free-tier days (deterministic given the ledger)."""
    config = config or load_models_config()
    profile = config["profiles"][config["default_profile"]]
    free = profile.get("free_tier") or {}
    quota = max((free.get("rpd", 0) - config["budget"]["daily_safety_margin"]), 1)
    total = len(universe.primary)
    rows = ledger.rows
    by = {s: [r for r in rows.values() if r["status"] == s] for s in STATUSES}
    attempted = len(rows)
    remaining = max(total - sum(1 for r in universe.primary if rows.get(r.cik, {}).get("status") in ("done", "warning")), 0)
    ok = by["done"] + by["warning"]
    mean = lambda f: (sum(f(r) for r in ok) / len(ok)) if ok else 0.0  # noqa: E731
    calls, notional = mean(lambda r: r["calls"]), mean(lambda r: r["notional_cost_usd"])
    actual_total, notional_total = sum(r["actual_cost_usd"] for r in rows.values()), sum(r["notional_cost_usd"] for r in rows.values())
    last = max((r["finished_at"] for r in rows.values()), default="n/a")
    cap = config["budget"]["total_usd_cap"]
    L = ["# Progress", "", f"S&P 500 coverage of the analysis engine. {universe.attribution}. Research output, not financial advice.", "",
         f"Last company finished: {last}. Universe: {total} companies (one per CIK).", "",
         "| Status | Companies |", "|---|---|",
         f"| Done | {len(by['done'])} |", f"| Done with warnings | {len(by['warning'])} |", f"| Failed | {len(by['failed'])} |", f"| Remaining (not yet analysed) | {remaining} |", "",
         "## Spend", "",
         f"- Actual: **${actual_total:.4f}** (free-tier calls cost nothing). Notional at paid rates ($0.25 / $1.50 per million input / output tokens): **${notional_total:.4f}**.",
         f"- Engine cap: ${cap:.2f} (config/models.json).", "",
         "## Measured per company", ""]
    if ok:
        L += [f"- Mean model calls: {calls:.1f}; mean tokens: {mean(lambda r: r['input_tokens']):,.0f} in / {mean(lambda r: r['output_tokens']):,.0f} out; mean notional cost ${notional:.4f}."]
    else:
        L += ["- No company finished yet."]
    L += ["", "## Projection for the remaining companies", ""]
    if ok and remaining:
        L += [f"- Free tier: {remaining * calls:,.0f} calls at ~{quota} requests a day is about **{remaining * calls / quota:.0f} days**.",
              f"- All on the paid tier: about **${remaining * notional:.2f}**" + (" (under the cap)." if remaining * notional <= cap - actual_total else " (over the cap: the hybrid order of ADR-023 applies).")]
    elif not remaining:
        L += ["- Nothing remaining."]
    else:
        L += ["- Not available until a company has finished."]
    if by["failed"]:
        L += ["", "## Failed", ""] + [f"- {r['ticker']}: {r['message'] or 'no scorecard'}" for r in sorted(by["failed"], key=lambda r: r["ticker"])]
    if by["warning"]:
        L += ["", "## Done with warnings", ""] + [f"- {r['ticker']}: {r['warnings']} warning(s)" for r in sorted(by["warning"], key=lambda r: r["ticker"])]
    return "\n".join(L) + "\n"
