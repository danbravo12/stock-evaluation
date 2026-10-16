"""The data behind the site's evaluation page (build 4b, ADR-073): every figure comes from a frozen file in `eval/` or from the committed results, never from the page.

`evaluation_data(stability_rows)` is called by `engine.publish` and written to `data/evaluation.json`; `stability_rows` is one {criterion: stability record} per fully analysed
company. The page (site_src/evaluation.html and assets/js/evaluation.js) only lays these values out.
"""
from __future__ import annotations

import json

from engine.contracts import QUAL_CRITERIA
from engine.settings import REPO_ROOT
from engine.stability import criterion_stats, load_threshold

EVAL = REPO_ROOT / "eval"
TITLES = {"understandable_business": "Understandable business", "durable_competitive_advantage": "Durable competitive advantage", "candid_management": "Candid management",
          "rational_capital_allocation": "Rational capital allocation"}
NUMERIC = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "B1", "B2", "B3", "B4")
DECIDED = ("pass", "partial_pass", "fail")


LABEL = {"g1_min_revenue": "Revenue at least", "g2_current_ratio": "Current ratio at least", "g2_debt_to_net_current": "Long-term debt at most, in times net current assets",
         "g2_utility_debt_equity": "Utilities: long-term debt at most, in times equity", "g5_growth_ratio": "Earnings growth at least, as a multiple",
         "g6_max_pe": "Price at most, in times earnings", "g7_max_pe_x_pb": "Price to earnings times price to book at most",
         "b1_roe": "Return on equity at least", "b1_min_years": "Years the return on equity must be met", "b2_debt_multiple": "Long-term debt at most, in times average net income",
         "b3_margin_ratio": "Recent margin at least, as a share of the ten-year average", "b4_min_positive_years": "Years owner earnings must be positive"}


def display(name: str, v) -> str:
    """A threshold value in words: dollars, percent, times or years."""
    if name == "g1_min_revenue":
        return f"${v / 1e9:g} billion"
    if name in ("b1_roe", "b3_margin_ratio"):
        return f"{round(v * 100, 4):g}%"
    if name in ("b1_min_years", "b4_min_positive_years"):
        return f"{v} years"
    return f"{v:g} times" if name not in ("g2_current_ratio",) else f"{v:g}"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The 95% Wilson score interval for k successes in n trials."""
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (c - m) / d, (c + m) / d


def _load(name: str):
    return json.loads((EVAL / name).read_text(encoding="utf-8"))


def evaluation_data(stability_rows: list[dict]) -> dict:
    agreement = _load("agreement_results.json")
    stats = criterion_stats(stability_rows)
    judged = sum(v["compared"] for v in stats.values())
    changed = sum(v["changed"] for v in stats.values())
    table = []
    for c in QUAL_CRITERIA:
        d, h = agreement["dev"]["per_criterion"][c], agreement["heldout"]["per_criterion"][c]
        table.append({"criterion": c, "name": TITLES[c], "dev_exact": d["exact"], "dev_n": d["n"], "heldout_exact": h["exact"], "heldout_n": h["n"],
                      "changed": stats[c]["changed"], "compared": stats[c]["compared"], "flip_rate": stats[c]["rate"], "low": stats[c]["low"]})
    labels = _load("universe_label_counts.json")
    expected = _load("expected_scores.json")
    frozen_labels = [c["label"] for co in expected.values() for c in co["criteria"].values()]
    decided = {}
    for cid in NUMERIC:
        counts = labels["criteria"].get(cid, {})
        n = sum(counts.get(k, 0) for k in DECIDED)
        decided[cid] = {"decided": n, "pass": counts.get("pass", 0) + counts.get("partial_pass", 0), "data_gap": counts.get("data_gap", 0), "not_applicable": counts.get("not_applicable", 0),
                        "not_meaningful": counts.get("not_meaningful", 0)}
    sens = _load("sensitivity_results.json")
    ranked = sorted(((c, v) for c, v in sens["by_criterion"].items() if v["worst_share"] is not None), key=lambda kv: -kv[1]["worst_share"])
    return {
        "threshold": load_threshold(),
        "dev": {k: agreement["dev"][k] for k in ("items", "labelled", "exact", "within_one", "direction", "kappa", "disagreements")},
        "heldout": {**{k: agreement["heldout"][k] for k in ("items", "labelled", "exact", "within_one", "direction", "kappa", "disagreements", "human_label_counts")},
                    "interval": dict(zip(("low", "high"), wilson(agreement["heldout"]["exact"], agreement["heldout"]["labelled"])), level=0.95)},
        "split": {"heldout": agreement["heldout"]["split"], "dev": agreement["dev"]["split"], "combined": agreement["combined_split"]},
        "criteria": table,
        "stability": {"companies": len([r for r in stability_rows if any(r.values())]), "judged": judged, "borderline": changed, "rate": (changed / judged) if judged else None},
        "history": _load("agreement_history.json")["steps"],
        "critic": _load("critic_summary.json"),
        "numbers": {"frozen_companies": len(expected), "frozen_criteria": len(NUMERIC), "frozen_labels": len(frozen_labels), "universe_scored": labels["scored"],
                    "universe_no_report": labels["no_annual_report"], "criteria": decided, "diagnostics": _load("universe_diagnostics.json"), "triage": _load("numeric_triage.json"), "restatements": _load("restatement_diagnosis.json")},
        "sensitivity": {"delta": sens["delta"], "companies": sens["companies"], "thresholds": [{**t, "label": LABEL[t["name"]], "default_display": display(t["name"], t["default"]), "minus_display": display(t["name"], t["minus"]["value"]),
                                                  "plus_display": display(t["name"], t["plus"]["value"])} for t in sens["thresholds"]], "by_criterion": sens["by_criterion"], "ranking": [c for c, _ in ranked]},
    }
