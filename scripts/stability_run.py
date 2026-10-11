"""Live runs for build 4a (ADR-072), resumable across Pacific days: the budget guard stops cleanly and the same command continues.

    .venv/bin/python scripts/stability_run.py refresh     # the 20 showcase companies with the active (v2.1) prompts, results/<CIK>.json replaced
    .venv/bin/python scripts/stability_run.py a           # paraphrase A, all 25 companies, results/stability/a/
    .venv/bin/python scripts/stability_run.py b           # paraphrase B
    options: --limit N (companies to attempt), --tickers X Y (subset)

The five test companies are refreshed by recording their fixtures (`scripts/qualitative_report.py record`, `scripts/review_report.py record`) and replaying; the variant
runs read their SEC data from the fixtures and call the model live. A variant run reuses the main run's Explainer output (the numeric explanations do not depend on
the qualitative wording) and runs the qualitative agent and the Critic with the reworded rubric. Free tier only: refuses to run when PAID_MODE_ENABLED is set.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.batch import CompanyLedger, run_batch  # noqa: E402
from engine.contracts import Explanations  # noqa: E402
from engine.fetch.edgar import EdgarClient  # noqa: E402
from engine.orchestrator import analyse  # noqa: E402
from engine.report import Result  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402
from engine.stability import STABILITY_DIR, variant_criteria  # noqa: E402
from engine.universe import load_universe  # noqa: E402

TEST = json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"]
SHOWCASE = [e["symbol"] for e in json.loads((REPO_ROOT / "config" / "showcase.json").read_text())["showcase"]]
LEDGERS = REPO_ROOT / "data" / "ledger"


def analysed_tickers() -> list[str]:
    return TEST + SHOWCASE


def variant_analyse(symbol: str, *, mode: str, settings: Settings, universe, variant: str, **_):
    cik = universe.primary_of(universe.row_for(symbol)).cik
    main = Result.model_validate_json((settings.results_dir / f"{cik}.json").read_text(encoding="utf-8"))
    expl = Explanations(cik=cik, ticker=main.plan.ticker, items=[c.explanation for c in main.scorecard.criteria if c.explanation])
    edgar = EdgarClient("replay" if symbol in TEST else "live", settings)
    return analyse(symbol, mode="live", settings=settings, universe=universe, edgar=edgar, results_dir=STABILITY_DIR / variant, run_id=f"{symbol}-live-{variant}",
                   criteria=variant_criteria(variant), explanations=expl)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["refresh", "a", "b"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tickers", nargs="+")
    a = ap.parse_args()
    settings = Settings.from_env()
    if settings.paid_mode_enabled:
        sys.exit("PAID_MODE_ENABLED is set: this run is free tier only")
    universe = load_universe()
    if a.what == "refresh":
        symbols = a.tickers or SHOWCASE
        ledger = CompanyLedger(LEDGERS / "refresh_v2_1.json")
        outcome = run_batch(symbols, mode="live", settings=settings, universe=universe, ledger=ledger, limit=a.limit)
    else:
        symbols = a.tickers or analysed_tickers()
        ledger = CompanyLedger(LEDGERS / f"stability_{a.what}.json")

        def fn(symbol, **kw):
            return variant_analyse(symbol, variant=a.what, **kw)
        outcome = run_batch(symbols, mode="live", settings=settings, universe=universe, ledger=ledger, limit=a.limit, analyse_fn=fn)
    print(f"done {len(outcome.done)}, skipped {len(outcome.skipped)}" + (f", stopped: {outcome.stopped}" if outcome.stopped else ""))
    return 2 if outcome.stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
