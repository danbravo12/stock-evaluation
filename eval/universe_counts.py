"""Label counts over the whole S&P 500 numeric run, frozen with a tolerance guard (ADR-059).

    .venv/bin/python -m eval.universe_counts            # compare results/scores/ with eval/universe_label_counts.json
    .venv/bin/python -m eval.universe_counts --freeze   # rewrite the frozen file after a reviewed change

The frozen counts are the evidence that a later change to a rule, a concept map or the normaliser did not silently move hundreds of labels.
`compare` allows each count to move by max(MIN_ABS, REL x scored companies); anything beyond that is listed.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from engine.settings import REPO_ROOT

FROZEN_PATH = REPO_ROOT / "eval" / "universe_label_counts.json"
SCORES_DIR = REPO_ROOT / "results" / "scores"
MIN_ABS, REL = 5, 0.02
LABELS = ("pass", "partial_pass", "fail", "not_applicable", "not_meaningful", "data_gap")


def count_labels(scores_dir: Path = SCORES_DIR) -> dict:
    per, by_class = defaultdict(Counter), defaultdict(lambda: defaultdict(Counter))
    n = 0
    classes = Counter()
    for p in sorted(Path(scores_dir).glob("*.json")):
        if p.name.startswith("_"):
            continue
        r = json.loads(p.read_text(encoding="utf-8"))
        n += 1
        classes[r["sector_class"]] += 1
        for c in r["score"]["results"]:
            per[c["id"]][c["label"]] += 1
            by_class[r["sector_class"]][c["id"]][c["label"]] += 1
    return {"scored": n, "sector_classes": dict(sorted(classes.items())),
            "criteria": {cid: {l: per[cid][l] for l in LABELS if per[cid][l]} for cid in sorted(per, key=lambda x: (x[0], int(x[1:])))},
            "by_sector_class": {cls: {cid: dict(c) for cid, c in sorted(d.items(), key=lambda kv: (kv[0][0], int(kv[0][1:])))} for cls, d in sorted(by_class.items())}}


def compare(frozen: dict, current: dict, min_abs: int = MIN_ABS, rel: float = REL) -> list[str]:
    """Differences beyond the tolerance, as readable lines (empty list = within tolerance)."""
    tol = max(min_abs, rel * max(frozen["scored"], current["scored"]))
    out = []
    if abs(frozen["scored"] - current["scored"]) > tol:
        out.append(f"companies scored: {frozen['scored']} -> {current['scored']}")
    for cid in sorted(set(frozen["criteria"]) | set(current["criteria"])):
        for l in LABELS:
            a, b = frozen["criteria"].get(cid, {}).get(l, 0), current["criteria"].get(cid, {}).get(l, 0)
            if abs(a - b) > tol:
                out.append(f"{cid} {l}: {a} -> {b}")
    return out


if __name__ == "__main__":
    cur = count_labels()
    if "--freeze" in sys.argv:
        FROZEN_PATH.write_text(json.dumps(cur, indent=1) + "\n", encoding="utf-8")
        print(f"froze {cur['scored']} companies to {FROZEN_PATH.relative_to(REPO_ROOT)}")
    else:
        diffs = compare(json.loads(FROZEN_PATH.read_text()), cur)
        print("within tolerance" if not diffs else "\n".join(diffs))
        sys.exit(1 if diffs else 0)
