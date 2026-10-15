"""Agreement between the qualitative agent and human labels, for the dev set and the held-out set separately (build 4a, ADR-071).

    .venv/bin/python -m eval.agreement [--results-dir DIR] [--json]

Dev set:      eval/expected_qualitative.json  (KO, JPM, GOOGL, TSLA, DUK; the rubric was tuned on these, so the figures overstate accuracy)
Held-out set: eval/heldout_labels.json        (AAPL, MSFT, PG, NEE, CAT, JNJ; labelled blind before anyone looked at further agent output)
The agent's verdict is the one in the final result (`results/<CIK>.json`, after the Critic's repairs). Levels: found (2) > weak (1) > insufficient (0).

Rules (stated so the numbers can be checked):
- exact agreement: agent verdict equals the human one; a "not assessed" agent verdict is a disagreement.
- within one level: the two are at most one level apart; "not assessed" is not within one level of anything.
- direction (among the disagreements the agent assessed): "more generous" = agent level above the human one, "stricter" = below; "not assessed" is counted on its own.
- Cohen's weighted kappa with linear weights over the three levels, on the items the agent assessed (a "not assessed" verdict has no place on the scale; the
  number excluded is reported). None when chance agreement is perfect (one rater uses one level only and the other agrees).
- items without a human label yet are left out and counted as unlabelled.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.contracts import QUAL_CRITERIA
from engine.settings import REPO_ROOT
from engine.universe import load_universe

LEVEL = {"insufficient evidence": 0, "evidence weak": 1, "evidence found": 2}
DEV_PATH = REPO_ROOT / "eval" / "expected_qualitative.json"
HELDOUT_PATH = REPO_ROOT / "eval" / "heldout_labels.json"
FROZEN_PATH = REPO_ROOT / "eval" / "agreement_results.json"


def weighted_kappa(pairs: list[tuple[int, int]], levels: int = 3) -> float | None:
    """Cohen's kappa with linear disagreement weights |i-j|/(levels-1). pairs = (agent level, human level). None if undefined."""
    n = len(pairs)
    if n == 0:
        return None
    obs = [[0.0] * levels for _ in range(levels)]
    for a, h in pairs:
        obs[a][h] += 1 / n
    row = [sum(obs[i]) for i in range(levels)]
    col = [sum(obs[i][j] for i in range(levels)) for j in range(levels)]
    w = lambda i, j: abs(i - j) / (levels - 1)  # noqa: E731
    observed = sum(w(i, j) * obs[i][j] for i in range(levels) for j in range(levels))
    expected = sum(w(i, j) * row[i] * col[j] for i in range(levels) for j in range(levels))
    if expected == 0:
        return None
    return 1 - observed / expected


def compare(agent: dict[str, dict[str, str]], human: dict[str, dict[str, str | None]]) -> dict:
    """agent[ticker][criterion] -> verdict, human[ticker][criterion] -> verdict or None. Returns the agreement figures."""
    rows = []
    for t, crits in human.items():
        for c in QUAL_CRITERIA:
            h = crits.get(c)
            if h is None:
                rows.append({"ticker": t, "criterion": c, "human": None, "agent": agent.get(t, {}).get(c)})
                continue
            rows.append({"ticker": t, "criterion": c, "human": h, "agent": agent.get(t, {}).get(c, "not assessed")})
    labelled = [r for r in rows if r["human"] is not None]
    assessed = [r for r in labelled if r["agent"] in LEVEL]

    def tally(rs):
        exact = sum(r["agent"] == r["human"] for r in rs)
        within = sum(r["agent"] in LEVEL and abs(LEVEL[r["agent"]] - LEVEL[r["human"]]) <= 1 for r in rs)
        return {"n": len(rs), "exact": exact, "within_one": within}

    out = {"items": len(rows), "labelled": len(labelled), "unlabelled": len(rows) - len(labelled), **tally(labelled)}
    out["direction"] = {"agent_more_generous": sum(r["agent"] in LEVEL and LEVEL[r["agent"]] > LEVEL[r["human"]] for r in labelled),
                        "agent_stricter": sum(r["agent"] in LEVEL and LEVEL[r["agent"]] < LEVEL[r["human"]] for r in labelled),
                        "not_assessed": sum(r["agent"] not in LEVEL for r in labelled)}
    out["per_criterion"] = {c: tally([r for r in labelled if r["criterion"] == c]) for c in QUAL_CRITERIA}
    out["kappa"] = {"weighted_linear": weighted_kappa([(LEVEL[r["agent"]], LEVEL[r["human"]]) for r in assessed]), "n": len(assessed), "excluded_not_assessed": len(labelled) - len(assessed)}
    out["disagreements"] = [{"ticker": r["ticker"], "criterion": r["criterion"], "agent": r["agent"], "human": r["human"]} for r in labelled if r["agent"] != r["human"]]
    return out


def load_human_dev(path: Path = DEV_PATH) -> dict[str, dict[str, str]]:
    gold = json.loads(Path(path).read_text(encoding="utf-8"))["gold"]
    return {t: {c: v["human_verdict"] for c, v in crits.items()} for t, crits in gold.items()}


def load_human_heldout(path: Path = HELDOUT_PATH) -> dict[str, dict[str, str | None]]:
    labels = json.loads(Path(path).read_text(encoding="utf-8"))["labels"]
    return {t: {c: v["human_verdict"] for c, v in crits.items()} for t, crits in labels.items()}


def load_agent_verdicts(tickers, results_dir: Path) -> dict[str, dict[str, str]]:
    """Final verdicts per ticker from `<results_dir>/<CIK>.json`."""
    universe = load_universe()
    out = {}
    for t in tickers:
        path = Path(results_dir) / f"{universe.row_for(t).cik}.json"
        if path.exists():
            out[t] = {q["finding"]["criterion"]: q["finding"]["verdict"] for q in json.loads(path.read_text(encoding="utf-8"))["qualitative"]}
    return out


def load_agent_items(tickers, results_dir: Path) -> dict[str, dict[str, dict]]:
    """Per ticker and criterion: the final verdict, the criterion's reliability mark and the finding's stability status, from `<results_dir>/<CIK>.json`."""
    universe = load_universe()
    out = {}
    for t in tickers:
        path = Path(results_dir) / f"{universe.row_for(t).cik}.json"
        if path.exists():
            out[t] = {q["finding"]["criterion"]: {"verdict": q["finding"]["verdict"], "reliability": "low" if q.get("reliability") == "low" else "normal",
                                                  "stability": (q.get("stability") or {}).get("status")} for q in json.loads(path.read_text(encoding="utf-8"))["qualitative"]}
    return out


def split_agreement(items: dict, human: dict) -> dict:
    """Exact agreement by group: criteria marked low reliability against the rest (ADR-072 amendment), and findings that were stable against borderline under rewording.
    A finding without a stability status (fewer than two assessed verdicts) is in neither stability group."""
    def group(key, value):
        rows = [(items[t][c], h) for t, crits in human.items() for c, h in crits.items() if h is not None and t in items and c in items[t]]
        sel = [(i, h) for i, h in rows if i[key] == value]
        return {"n": len(sel), "exact": sum(i["verdict"] == h for i, h in sel)}
    return {"criterion_reliability": {"normal": group("reliability", "normal"), "low": group("reliability", "low")},
            "finding_stability": {"stable": group("stability", "stable"), "borderline": group("stability", "borderline")}}


def report(results_dir: Path = REPO_ROOT / "results") -> dict:
    dev, held = load_human_dev(), load_human_heldout()
    rep = {"dev": compare(load_agent_verdicts(dev, results_dir), dev), "heldout": compare(load_agent_verdicts(held, results_dir), held)}
    rep["dev"]["split"] = split_agreement(load_agent_items(dev, results_dir), dev)
    rep["heldout"]["split"] = split_agreement(load_agent_items(held, results_dir), held)
    both = {**{("dev", t): v for t, v in dev.items()}, **{("heldout", t): v for t, v in held.items()}}
    items = {**{("dev", t): v for t, v in load_agent_items(dev, results_dir).items()}, **{("heldout", t): v for t, v in load_agent_items(held, results_dir).items()}}
    rep["combined_split"] = split_agreement(items, both)
    h = [v for crits in held.values() for v in crits.values() if v is not None]
    rep["heldout"]["human_label_counts"] = {k: h.count(k) for k in LEVEL}
    return rep


def render(rep: dict) -> str:
    lines = []
    names = {"dev": "Dev set (KO, JPM, GOOGL, TSLA, DUK; the rubric was tuned on these)", "heldout": "Held-out set (AAPL, MSFT, PG, NEE, CAT, JNJ)"}
    for key in ("dev", "heldout"):
        r = rep[key]
        lines += [f"## {names[key]}", ""]
        if not r["labelled"]:
            lines += [f"No labels yet ({r['items']} items).", ""]
            continue
        k = r["kappa"]["weighted_linear"]
        lines += [f"- items labelled: {r['labelled']} of {r['items']}",
                  f"- exact agreement: {r['exact']}/{r['labelled']} ({r['exact'] / r['labelled']:.0%})",
                  f"- within one level: {r['within_one']}/{r['labelled']} ({r['within_one'] / r['labelled']:.0%})",
                  f"- disagreements: agent more generous {r['direction']['agent_more_generous']}, stricter {r['direction']['agent_stricter']}, not assessed {r['direction']['not_assessed']}",
                  "- weighted kappa (linear): " + ("undefined" if k is None else f"{k:.2f}") + f" on {r['kappa']['n']} items ({r['kappa']['excluded_not_assessed']} not assessed left out)", "",
                  "| criterion | exact | within one |", "|---|---|---|"]
        lines += [f"| {c} | {v['exact']}/{v['n']} | {v['within_one']}/{v['n']} |" for c, v in r["per_criterion"].items()]
        sp = r["split"]
        lines += ["", "Agreement by group (exact): " + "; ".join(f"{name} {v['exact']}/{v['n']}" for grp in sp.values() for name, v in grp.items())]
        lines += [""] + [f"- {d['ticker']} {d['criterion']}: agent {d['agent']}, human {d['human']}" for d in r["disagreements"]] + [""]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=str(REPO_ROOT / "results"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--freeze", action="store_true", help="write eval/agreement_results.json")
    a = ap.parse_args()
    rep = report(Path(a.results_dir))
    if a.freeze:
        FROZEN_PATH.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=1) if a.json else render(rep))
