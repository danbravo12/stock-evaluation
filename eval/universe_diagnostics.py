"""How many companies still show each anomaly flag in the whole-index numeric run (build 4b, ADR-073).

    .venv/bin/python -m eval.universe_diagnostics --freeze     # writes eval/universe_diagnostics.json from results/scores/

The flags come from `engine.numeric.diagnose` (stored in every score file): revenue jumps of 3x or more, diluted EPS with the opposite sign to net income, restatements
over 10%, a dividend fail with 13 or more paid years. What was found and fixed along the way is in `eval/numeric_triage.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.settings import REPO_ROOT

OUT = REPO_ROOT / "eval" / "universe_diagnostics.json"
SCORES = REPO_ROOT / "results" / "scores"


def summarise(scores_dir: Path = SCORES) -> dict:
    n = jumps = sign = restated = g4 = gaps = 0
    for p in sorted(Path(scores_dir).glob("[0-9]*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if not r.get("score"):
            continue
        d = r["diagnostics"]
        n += 1
        jumps += bool(d["revenue_jumps"])
        sign += bool(d["eps_sign_mismatch"])
        restated += bool(d["restated_over_10pct"])
        g4 += bool(d["g4_fail_with_13_or_more_paid"])
        gaps += any(c["label"] == "data_gap" and c["id"] not in ("G6", "G7") for c in r["score"]["results"])
    return {"scored": n, "companies_with": {"revenue_jump": jumps, "eps_sign_mismatch": sign, "restatement_over_10pct": restated, "g4_fail_with_13_or_more_paid_years": g4,
                                            "a_data_gap_outside_g6_g7": gaps}}


if __name__ == "__main__":
    s = summarise()
    if "--freeze" in sys.argv:
        OUT.write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(s, indent=1))
