"""Command line: analyse one ticker, run a resumable batch, write PROGRESS.md (ADR-056).

    python -m engine.cli analyse KO [--mode replay|live|record]
    python -m engine.cli batch [--tickers KO JPM | --universe] [--limit N] [--force] [--mode ...]
    python -m engine.cli batch --universe --numeric-only   # the whole index, scores only, live SEC data, no model
    python -m engine.cli rankings                           # site_data/rankings.json from results/scores/ (no model, no network)
    python -m engine.cli publish [--serve]                  # build site/ from site_src/, site_data/ and results/ (Finnhub gate, banned phrases, link checks)
    python -m engine.cli deploy [--dry-run]                 # build, run every gate and the secret scan, then push site/ to the gh-pages branch (never without a remote)
    python -m engine.cli status
    python -m engine.cli schema
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

from engine.batch import CompanyLedger, progress_markdown, run_batch, run_numeric_batch
from engine.fetch.edgar import EdgarClient
from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.orchestrator import analyse
from engine.publish import SITE_OUT, build_site, serve
from engine.rankings import OUTPUT_PATH, Rankings, build_rankings, export_rankings_schema, write_rankings
from engine.report import export_schema
from engine.settings import REPO_ROOT, Settings
from engine.universe import load_universe, normalise_ticker

PROGRESS_PATH = REPO_ROOT / "PROGRESS.md"


def ledger_for(settings: Settings) -> CompanyLedger:
    return CompanyLedger(settings.ledger_path.with_name("companies.json"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m engine.cli", description="Graham & Buffett equity research engine (research tool, not financial advice)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("analyse", "batch"):
        p = sub.add_parser(name)
        p.add_argument("--mode", choices=["replay", "live", "record"], default=None, help="default replay; live with --numeric-only")
        p.add_argument("--results-dir", default=None)
    sub.choices["analyse"].add_argument("ticker")
    b = sub.choices["batch"]
    b.add_argument("--tickers", nargs="+")
    b.add_argument("--universe", action="store_true", help="every company in the latest snapshot (one per CIK)")
    b.add_argument("--limit", type=int)
    b.add_argument("--force", action="store_true")
    b.add_argument("--numeric-only", action="store_true", help="fetch live, normalise and score only: no 10-K download, no model (ADR-059)")
    pb = sub.add_parser("publish", help="build the static site into site/ (ADR-065)")
    pb.add_argument("--serve", action="store_true", help="then serve it locally with http.server")
    pb.add_argument("--port", type=int, default=8000)
    pb.add_argument("--out", default=None)
    dp = sub.add_parser("deploy", help="publish site/ to the gh-pages branch of the origin remote (ADR-068)")
    dp.add_argument("--dry-run", action="store_true", help="build, check and scan, then print what would be pushed")
    sub.add_parser("status")
    sub.add_parser("schema", help="write schema/result.schema.json and schema/rankings.schema.json")
    r = sub.add_parser("rankings", help="build site_data/rankings.json: criteria ranking from the numeric scores (ADR-062)")
    r.add_argument("--results-dir", default=None)
    r.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    if a.cmd == "schema":
        print("wrote", export_schema().relative_to(REPO_ROOT), "and", export_rankings_schema().relative_to(REPO_ROOT))
        return 0
    settings = Settings.from_env()
    if a.cmd == "deploy":
        from engine.deploy import DeployRefused, deploy, summary
        try:
            rep = deploy(settings=settings, dry_run=a.dry_run)
        except DeployRefused as e:
            print("REFUSED:", e)
            return 4
        print(summary(rep, SITE_OUT))
        if not a.dry_run:
            print(f"Pushed to {rep.remote}, branch gh-pages.")
        return 0
    if a.cmd == "publish":
        out = Path(a.out) if a.out else SITE_OUT
        m = build_site(out, settings=settings)
        print(f"built {out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out}: {m['counts']['scored']} company score files, {m['counts']['full_analysis']} full analyses, commit {m['build_commit']}")
        if a.serve:
            serve(out, a.port)
        return 0
    if a.cmd == "rankings":
        results_dir = Path(a.results_dir) if a.results_dir else settings.results_dir
        out = write_rankings(build_rankings(load_universe(), results_dir / "scores", results_dir), Path(a.out) if a.out else OUTPUT_PATH, finnhub_public_ok=settings.finnhub_public_ok)
        r = Rankings.model_validate_json(out.read_text(encoding="utf-8"))
        print(f"wrote {out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out}: {r.counts.ranked} ranked, {r.counts.ranked_financials} banks and insurers ranked, {r.counts.insufficient_data} insufficient data, {r.counts.excluded} excluded")
        return 0
    if a.cmd in ("analyse", "batch"):
        a.mode = a.mode or ("live" if getattr(a, "numeric_only", False) else "replay")
    if getattr(a, "numeric_only", False):
        # EDGAR fair access: a declared User-Agent and at most ~6 requests a second
        settings = dataclasses.replace(settings, sec_min_interval_s=max(settings.sec_min_interval_s, 0.17))
    edgar = EdgarClient(a.mode, settings) if a.cmd in ("analyse", "batch") else EdgarClient("replay", settings)
    universe = load_universe(sec_tickers=edgar.company_tickers())

    if a.cmd == "status":
        text = progress_markdown(ledger_for(settings), universe)
        PROGRESS_PATH.write_text(text, encoding="utf-8")
        print(text)
        return 0
    results_dir = a.results_dir
    if a.cmd == "analyse":
        try:
            r = analyse(a.ticker, mode=a.mode, settings=settings, universe=universe, edgar=edgar, results_dir=results_dir)
        except (QuotaReached, BudgetExceeded) as e:
            print(f"STOPPED: {e}")
            return 3
        print(f"{r.plan.ticker}: {'in scope' if r.plan.in_scope else 'OUT OF SCOPE: ' + str(r.plan.out_of_scope_reason)} · {r.cost.llm_calls} model calls · "
              f"notional ${r.cost.notional_cost_usd:.4f} · actual ${r.cost.actual_cost_usd:.4f} · {len(r.warnings)} warnings")
        for w in r.warnings:
            print(f"  warning [{w.where}] {w.message}")
        return 0 if r.plan.in_scope else 1
    symbols = [p.symbol for p in universe.primary] if a.universe else [normalise_ticker(t) for t in (a.tickers or [])]
    if not symbols:
        print("Give --tickers or --universe.")
        return 2
    if a.numeric_only:
        if a.mode == "replay":
            print("--numeric-only reads live SEC data into the cache; use --mode live (the default).")
            return 2
        ledger = CompanyLedger(settings.ledger_path.with_name("numeric.json"))
        scores_dir = (Path(results_dir) if results_dir else settings.results_dir) / "scores"
        t0 = time.time()
        outcome = run_numeric_batch(symbols, universe=universe, ledger=ledger, edgar=edgar, scores_dir=scores_dir, limit=a.limit, force=a.force)
        elapsed = time.time() - t0
        rows = ledger.rows.values()
        summary = {"processed_this_run": len(outcome.done), "skipped": len(outcome.skipped), "seconds_this_run": round(elapsed, 1), "edgar_requests_this_run": edgar.requests_made,
                   "done": sum(r["status"] == "done" for r in rows), "failed": sum(r["status"] == "failed" for r in rows)}
        scores_dir.mkdir(parents=True, exist_ok=True)
        (scores_dir / "_run.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        print(f"numeric batch: {summary}")
        return 0
    ledger = ledger_for(settings)
    outcome = run_batch(symbols, mode=a.mode, settings=settings, universe=universe, ledger=ledger, limit=a.limit, force=a.force, edgar=edgar, results_dir=results_dir)
    PROGRESS_PATH.write_text(progress_markdown(ledger, universe), encoding="utf-8")
    print(f"batch: {len(outcome.done)} analysed, {len(outcome.skipped)} skipped (already done); PROGRESS.md updated")
    return 3 if outcome.stopped else 0


if __name__ == "__main__":
    sys.exit(main())
