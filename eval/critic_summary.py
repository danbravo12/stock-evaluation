"""What the Critic did over the 25 analysed companies, computed from the committed results (build 4b, ADR-073).

    .venv/bin/python -m eval.critic_summary --freeze     # writes eval/critic_summary.json

Counts: items checked, flagged on the first pass, repairs by path and outcome, items that end with a warning; the findings of the dev set where a repair
turned a verdict the human labelled correctly into a wrong one; and how many findings are "insufficient evidence" (the Critic never reviews those, so a
false negative cannot be caught).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from eval.agreement import DEV_PATH, load_human_dev
from engine.settings import REPO_ROOT
from engine.universe import load_universe

OUT = REPO_ROOT / "eval" / "critic_summary.json"
QUAL = ("understandable_business", "durable_competitive_advantage", "candid_management", "rational_capital_allocation")


def summarise(results_dir: Path = REPO_ROOT / "results") -> dict:
    results = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(results_dir).glob("[0-9]*[0-9].json"))]
    results = [r for r in results if r.get("critic")]
    items = flagged = 0
    flagged_by = {"explanation": 0, "finding": 0}
    final = {"passed": 0, "passed_after_retry": 0, "warning": 0}
    repairs: dict[str, dict[str, int]] = {}
    for r in results:
        crit = r["critic"]
        items += len(crit["final"])
        first = {(c["owner"], c["item"]) for c in crit["checks"] if c["attempt"] == 0 and c["status"] == "fail"}
        flagged += len(first)
        flagged_by["explanation"] += sum(o == "explainer" for o, _ in first)
        flagged_by["finding"] += sum(o == "qualitative" for o, _ in first)
        for v in crit["final"].values():
            final[v] += 1
        for rep in crit["repairs"]:
            repairs.setdefault(rep["path"], {}).setdefault(rep["outcome"], 0)
            repairs[rep["path"]][rep["outcome"]] += 1
    verdicts = [q["finding"]["verdict"] for r in results for q in r["qualitative"]]
    # dev set: the agent-only verdict (before the repairs) is `agent_verdict` in the gold file
    gold = json.loads(DEV_PATH.read_text(encoding="utf-8"))["gold"]
    human, universe, made_worse, fixed = load_human_dev(), load_universe(), [], []
    for t, crits in gold.items():
        path = Path(results_dir) / f"{universe.row_for(t).cik}.json"
        final_v = {q["finding"]["criterion"]: q["finding"]["verdict"] for q in json.loads(path.read_text(encoding="utf-8"))["qualitative"]}
        for c, rec in crits.items():
            before, after, h = rec["agent_verdict"], final_v[c], human[t][c]
            if before == h and after != h:
                made_worse.append({"ticker": t, "criterion": c, "before": before, "after": after, "human": h})
            if before != h and after == h:
                fixed.append({"ticker": t, "criterion": c, "before": before, "after": after, "human": h})
    return {"companies": len(results), "items": items, "flagged_first_pass": flagged, "flagged_by": flagged_by, "final": final, "repairs": repairs,
            "findings": len(verdicts), "insufficient_evidence": verdicts.count("insufficient evidence"), "not_assessed": verdicts.count("not assessed"),
            "dev_repair_made_worse": made_worse, "dev_repair_fixed": fixed}


if __name__ == "__main__":
    s = summarise()
    if "--freeze" in sys.argv:
        OUT.write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(s, indent=1))
