"""Threshold sensitivity of the numeric criteria (build 4b, ADR-074).

    .venv/bin/python -m eval.sensitivity            # recompute from the local SEC cache and compare with eval/sensitivity_results.json
    .venv/bin/python -m eval.sensitivity --freeze   # rewrite the frozen file

Each numeric threshold is moved down and up by 20% on its own (a count of years is rounded to a whole year), every company is scored again with
`engine.score.score_company`, and the labels are compared with the baseline: how many companies change label, per criterion and per direction.
No model and no network: the SEC data comes from the local cache (the same data the numeric batch read), so the result is deterministic.
G6 and G7 compare a price with earnings; there is no price data yet (ADR-007), so they have no labels to move and are listed as not testable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.normalise import normalise_from_store
from engine.planner import plan_for
from engine.score import score_company
from engine.score.common import load_sector_rules
from engine.score.thresholds import CRITERION, DEFAULT, NAMES, override, scaled
from engine.settings import REPO_ROOT
from engine.splits import adjust_for_splits

FROZEN_PATH = REPO_ROOT / "eval" / "sensitivity_results.json"
DELTA = 0.20
DECIDED = ("pass", "partial_pass", "fail")
NOT_TESTABLE = {"g6_max_pe", "g7_max_pe_x_pb"}  # need a share price


def labels_of(score) -> dict[str, str]:
    return {r.id: r.label for r in score.results}


def sensitivity(prepared: list[tuple], delta: float = DELTA) -> dict:
    """`prepared` is [(nf, ticker, sic, rules, sector, notes)] for every company. Returns the frozen structure."""
    base = [labels_of(score_company(nf, t, sic, rules, None, sector=sector, sector_notes_=notes)) for nf, t, sic, rules, sector, notes in prepared]
    decided = {}
    for lab in base:
        for cid, l in lab.items():
            if l in DECIDED:
                decided[cid] = decided.get(cid, 0) + 1
    rows = []
    for name in NAMES:
        row = {"name": name, "criterion": CRITERION[name], "default": getattr(DEFAULT, name), "testable": name not in NOT_TESTABLE}
        for tag, factor in (("minus", 1 - delta), ("plus", 1 + delta)):
            value = scaled(name, factor)
            changed, to_fail, to_pass = 0, 0, 0
            if row["testable"]:
                with override(**{name: value}):
                    for (nf, t, sic, rules, sector, notes), b in zip(prepared, base):
                        new = labels_of(score_company(nf, t, sic, rules, None, sector=sector, sector_notes_=notes))
                        for cid, l in new.items():
                            if l != b[cid]:
                                changed += 1
                                to_fail += l == "fail"
                                to_pass += l in ("pass", "partial_pass")
            row[tag] = {"value": value, "changed": changed, "to_fail": to_fail, "to_pass": to_pass}
        rows.append(row)
    by_criterion = {}
    for cid in sorted(decided, key=lambda x: (x[0], int(x[1:]))):
        mine = [r for r in rows if r["criterion"] == cid and r["testable"]]
        worst = max((max(r["minus"]["changed"], r["plus"]["changed"]) for r in mine), default=None)
        by_criterion[cid] = {"decided": decided[cid], "thresholds": len(mine), "worst_changed": worst, "worst_share": (worst / decided[cid]) if worst is not None and decided[cid] else None}
    return {"delta": delta, "companies": len(prepared), "baseline_decided": decided, "thresholds": rows, "by_criterion": by_criterion}


def prepare_all(edgar, universe, symbols: list[str]) -> list[tuple]:
    """Normalise and split-adjust each company once (the expensive part) from the local cache."""
    rules = load_sector_rules()
    out = []
    for sym in symbols:
        row = universe.row_for(sym)
        sic = edgar.submissions(row.cik).get("sic")
        plan = plan_for(sym, universe, sic, rules)
        nf = adjust_for_splits(normalise_from_store(edgar, row.cik), edgar.companyfacts(row.cik))
        out.append((nf, plan.ticker, sic, rules, plan.sector_class, plan.sector_notes))
    return out


def scored_symbols(universe, scores_dir: Path) -> list[str]:
    """The companies the numeric run scored (a score file with a score), in snapshot order."""
    done = set()
    for p in Path(scores_dir).glob("[0-9]*.json"):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("score"):
            done.add(r["cik"])
    return [r.symbol for r in universe.primary if r.cik in done]


def compute() -> dict:
    from engine.fetch.edgar import EdgarClient
    from engine.settings import Settings
    from engine.universe import load_universe

    def no_network(url, headers, timeout):
        raise RuntimeError("the sensitivity run reads the local cache only")
    settings = Settings.from_env()
    edgar = EdgarClient("live", settings, transport=no_network)
    universe = load_universe()
    return sensitivity(prepare_all(edgar, universe, scored_symbols(universe, settings.results_dir / "scores")))


def render(res: dict) -> str:
    lines = [f"Threshold sensitivity, each threshold moved by {res['delta']:.0%}, {res['companies']} companies", ""]
    for r in res["thresholds"]:
        if not r["testable"]:
            lines.append(f"{r['criterion']} {r['name']}: not testable (no price data)")
        else:
            lines.append(f"{r['criterion']} {r['name']} {r['default']}: -> {r['minus']['value']}: {r['minus']['changed']} change, +> {r['plus']['value']}: {r['plus']['changed']} change")
    lines += [""] + [f"{c}: worst case {v['worst_changed']} of {v['decided']} decided ({v['worst_share']:.1%})" for c, v in res["by_criterion"].items() if v["worst_changed"] is not None]
    return "\n".join(lines)


if __name__ == "__main__":
    res = compute()
    if "--freeze" in sys.argv:
        FROZEN_PATH.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {FROZEN_PATH}")
    print(render(res))
    if FROZEN_PATH.exists() and "--freeze" not in sys.argv:
        print("\nidentical to the frozen file" if json.loads(FROZEN_PATH.read_text()) == json.loads(json.dumps(res)) else "\nDIFFERS from the frozen file")
