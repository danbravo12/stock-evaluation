"""Numeric-only analysis (ADR-059): fetch, normalise, split-adjust and score one company. No 10-K download, no model.

Used for the whole S&P 500 in one run. Besides the ScoreSet it keeps `diagnostics` (gaps, normaliser notes, split factors, restatements and a few
plausibility flags) so the anomalies that smell like mapping bugs can be listed afterwards without re-reading every company's facts.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from engine.contracts import NormalisedFacts, ScoreSet
from engine.normalise import normalise_from_store
from engine.planner import plan_for
from engine.score import score_company
from engine.score.common import fiscal_year, load_sector_rules
from engine.splits import adjust_for_splits
from engine.universe import Universe

RESTATEMENT_PCT = 0.10
SPLIT_DRIVEN = {"eps_diluted", "diluted_shares", "dividends_per_share"}  # companies restate these for splits themselves: not a restatement of results
REVENUE_JUMP = 3.0


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def diagnose(nf: NormalisedFacts, score: ScoreSet) -> dict:
    """Facts about the normalised data that help find mapping bugs; all derived from the NormalisedFacts and the ScoreSet."""
    gaps, notes, splits, restated = [], [], {}, []
    for m, s in nf.series.items():
        for g in s.gaps:
            gaps.append({"measure": m, "year": g.fiscal_year_end.year if g.fiscal_year_end else None, "reason": g.reason})
        notes += [{"measure": m, "note": n} for n in s.notes]
        n_split = [v for v in s.values if v.split_factor != 1.0]
        if n_split:
            splits[m] = {"values": len(n_split), "max_factor": max(v.split_factor for v in n_split)}
        for v in s.values:
            if v.restated and v.original_value and m not in SPLIT_DRIVEN:
                now = v.value_before_split if v.value_before_split is not None else v.value  # a split adjustment is not a restatement
                change = abs(now - v.original_value) / abs(v.original_value)
                if change > RESTATEMENT_PCT:
                    restated.append({"measure": m, "year": fiscal_year(v), "original": v.original_value, "restated": v.value, "change": round(change, 3)})
    rev = {fiscal_year(v): v.value for v in nf.series["revenue"].values}  # fiscal-year labels, so 52/53-week years do not collide
    jumps = [{"year": y, "from": rev[y - 1], "to": rev[y], "ratio": round(rev[y] / rev[y - 1], 2)} for y in sorted(rev)
             if y - 1 in rev and rev[y - 1] > 0 and rev[y] > 0 and not (1 / REVENUE_JUMP <= rev[y] / rev[y - 1] <= REVENUE_JUMP)]
    ni = {fiscal_year(v): v.value for v in nf.series["net_income"].values}
    eps = {fiscal_year(v): v.value for v in nf.series["eps_diluted"].values}
    sign_mismatch = [{"year": y, "eps": eps[y], "net_income": ni[y]} for y in sorted(eps) if y in ni and _sign(eps[y]) != 0 and _sign(ni[y]) != 0 and _sign(eps[y]) != _sign(ni[y])]
    g4 = next((r for r in score.results if r.id == "G4"), None)
    suspicious_g4 = None
    if g4 and g4.label == "fail":
        unpaid, n = g4.figures.get("unpaid_years", []), g4.figures.get("years_on_record", 0)
        if n and n - len(unpaid) >= 13:
            suspicious_g4 = {"years_on_record": n, "unpaid_years": unpaid, "values": {y: g4.by_year[y]["value"] for y in map(str, unpaid) if y in g4.by_year}}
    return {"gaps": gaps, "notes": notes, "split_adjusted": splits, "restated_over_10pct": restated, "revenue_jumps": jumps, "eps_sign_mismatch": sign_mismatch,
            "g4_fail_with_13_or_more_paid": suspicious_g4}


def score_numeric(symbol: str, *, edgar, universe: Universe, rules: dict | None = None) -> dict:
    """One company's numeric result as a JSON-ready dict. Raises on any failure (the batch records it)."""
    t0 = time.perf_counter()
    rules = rules or load_sector_rules()
    row = universe.row_for(symbol)
    if row is None:
        raise ValueError(f"{symbol} is not in the S&P 500 snapshot")
    sic = edgar.submissions(row.cik).get("sic")
    plan = plan_for(symbol, universe, sic, rules)
    nf = adjust_for_splits(normalise_from_store(edgar, row.cik), edgar.companyfacts(row.cik))
    score = score_company(nf, plan.ticker, sic, rules, None, sector=plan.sector_class)
    return {"ticker": plan.ticker, "cik": row.cik, "name": row.security, "gics_sector": row.gics_sector, "gics_sub_industry": row.gics_sub_industry, "sic": sic,
            "sector_class": plan.sector_class, "sector_basis": plan.sector_basis, "sector_notes": score.sector_notes,
            "score": score.model_dump(mode="json"), "diagnostics": diagnose(nf, score), "seconds": round(time.perf_counter() - t0, 2)}


def write_numeric(result: dict, scores_dir: Path) -> Path:
    scores_dir.mkdir(parents=True, exist_ok=True)
    path = scores_dir / f"{result['cik']}.json"
    path.write_text(json.dumps(result, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    return path
