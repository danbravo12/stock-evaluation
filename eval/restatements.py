"""Diagnosis of the "restatement over ten percent" flag in the whole-index run (build 5, ADR-073 amendment).

    .venv/bin/python -m eval.restatements --freeze     # recomputes from the local SEC cache, writes eval/restatement_diagnosis.json

Two different things were at risk of being counted together:
- a **true restatement**: the same concept, for the same fiscal period, reported again in a later filing with a value more than ten percent different
  (usually a recast for a discontinued operation, an acquisition or a changed presentation); this is what `engine.numeric.diagnose` flags;
- a **concept switch**: a company reports the same measure under one tag in some years and under another in others, so the series changes concept between
  years. That can shift a margin or a growth rate, but it is not a restatement: no single value changes.
The normaliser groups facts per concept, so a switch cannot raise the flag; this module verifies it fact by fact (every flagged value's first and last filing carry
the same concept and the same period) and counts the switches separately.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.normalise import _d, _facts_of, _is_annual, normalise_from_store
from engine.numeric import RESTATEMENT_PCT, SPLIT_DRIVEN
from engine.settings import REPO_ROOT, Settings
from engine.splits import adjust_for_splits

OUT = REPO_ROOT / "eval" / "restatement_diagnosis.json"
SAME_PERIOD_DAYS = 10


def restated_values(nf) -> list[tuple[str, object, float]]:
    """(measure, value, relative change) for every value the run flags: restated, a first-reported value known, per-share measures left out (split-driven)."""
    out = []
    for m, s in nf.series.items():
        if m in SPLIT_DRIVEN:
            continue
        for v in s.values:
            if v.restated and v.original_value:
                now = v.value_before_split if v.value_before_split is not None else v.value
                change = abs(now - v.original_value) / abs(v.original_value)
                if change > RESTATEMENT_PCT:
                    out.append((m, v, change))
    return out


def concept_switch_measures(nf) -> list[str]:
    """Measures whose series uses more than one concept across its years (ignoring derived sums and differences, which name their parts)."""
    return sorted(m for m, s in nf.series.items() if len({v.concept for v in s.values if not v.derived}) > 1)


def check_flagged(nf, companyfacts: dict) -> dict:
    """For each flagged value, look at the underlying annual facts of its concept and period: how many are the same concept and the same period (a true restatement)."""
    true_same, other = 0, []
    for m, v, change in restated_values(nf):
        if v.derived:
            other.append((m, v.fiscal_year_end.isoformat(), "derived value"))
            continue
        facts = [f for f in _facts_of(companyfacts, f"{v.taxonomy}:{v.concept}").get(v.unit, [])
                 if f["end"] == v.fiscal_year_end.isoformat() and _is_annual(f, "duration" if f.get("start") else "instant", nf.fiscal_year_end_mmdd)]
        starts = [_d(f["start"]) for f in facts if f.get("start")]
        if len({f["accn"] for f in facts}) > 1 and (not starts or (max(starts) - min(starts)).days <= SAME_PERIOD_DAYS):
            true_same += 1
        else:
            other.append((m, v.fiscal_year_end.isoformat(), "not the same concept and period in two filings"))
    return {"flagged_values": len(restated_values(nf)), "true_restatements": true_same, "other": other}


def diagnose_all(edgar, ciks: list[str]) -> dict:
    n = with_true = values = with_switch = other_values = 0
    for cik in ciks:
        nf = adjust_for_splits(normalise_from_store(edgar, cik), edgar.companyfacts(cik))
        c = check_flagged(nf, edgar.companyfacts(cik))
        n += 1
        with_true += c["true_restatements"] > 0
        values += c["true_restatements"]
        other_values += len(c["other"])
        sw = concept_switch_measures(nf)
        with_switch += bool(sw)
    return {"scored": n, "companies_with_true_restatement": with_true, "true_restatement_values": values, "flagged_values_that_are_not_true_restatements": other_values,
            "companies_with_concept_switch": with_switch}


def compute() -> dict:
    from engine.fetch.edgar import EdgarClient

    def no_network(url, headers, timeout):
        raise RuntimeError("reads the local cache only")
    edgar = EdgarClient("live", Settings.from_env(), transport=no_network)
    scores = Settings.from_env().results_dir / "scores"
    ciks = []
    for p in sorted(Path(scores).glob("[0-9]*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("score"):
            ciks.append(r["cik"])
    return diagnose_all(edgar, ciks)


if __name__ == "__main__":
    res = compute()
    if "--freeze" in sys.argv:
        OUT.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
