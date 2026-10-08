"""Frozen expected scores for the 5 test companies (start of the evaluation harness).

`snapshot()` reduces a ScoreSet to what the guard test compares: per criterion the label,
year label and the key figures rounded to 4 significant digits, so drift in numbers is
caught as well as label flips. To refresh after a deliberate, reviewed change:

    .venv/bin/python -m eval.snapshot
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.fetch.edgar import EdgarClient
from engine.score import score_ticker
from engine.settings import REPO_ROOT, Settings

EXPECTED_PATH = REPO_ROOT / "eval" / "expected_scores.json"


def _round(v):
    if isinstance(v, float):
        return float(f"{v:.4g}")
    if isinstance(v, list):
        return [_round(x) for x in v]
    return v


def snapshot(score_set) -> dict:
    return {
        "as_of_year": score_set.as_of_year,
        "sector_class": score_set.sector_class,
        "criteria": {
            r.id: {"label": r.label, "year_label": r.year_label, "figures": {k: _round(v) for k, v in r.figures.items()}}
            for r in score_set.results
        },
    }


def current_snapshots() -> dict:
    client = EdgarClient("replay", Settings.from_env())
    tickers = json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"]
    return {t: snapshot(score_ticker(client, t)) for t in tickers}


if __name__ == "__main__":
    EXPECTED_PATH.write_text(json.dumps(current_snapshots(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {EXPECTED_PATH.relative_to(REPO_ROOT)}")
