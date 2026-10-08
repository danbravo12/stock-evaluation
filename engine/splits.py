"""Stock-split adjustment (ADR-032).

EDGAR keeps old per-share figures on the share basis of the filing that reported
them, so EPS, dividends per share and share counts jump at every split (Alphabet's
2016 EPS is 27.85, its 2020 EPS 2.93, because of the 2022 20:1 split). We put every
value on today's basis:

1. `candidate_splits` reads the split-ratio facts the company tagged (pure, raw facts).
2. `adjust_for_splits` keeps only candidates that the restated values confirm (a value
   restated from original to new by about the same ratio) and rescales each per-share
   value by the splits that happened AFTER the filing it comes from.

Anything the two sources disagree on becomes a series note; nothing is guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from itertools import product

from engine.contracts import NormalisedFacts

RATIO_CONCEPTS = ("StockholdersEquityNoteStockSplitConversionRatio", "StockholdersEquityNoteStockSplitConversionRatio1")
PER_SHARE = ("eps_diluted", "dividends_per_share")  # divide by the factor
SHARE_COUNT = ("diluted_shares",)  # multiply by the factor
SAME_SPLIT_DAYS = 365
MATCH_TOLERANCE = 0.05  # restated values are rounded to cents


@dataclass(frozen=True)
class Split:
    ratio: float  # 20.0 for a 20-for-1 split, 1/3 for a 1-for-3 reverse split
    date: date  # approximate: only compared with 10-K filing dates


def _snap(ratio: float) -> float:
    """0.3333 -> 1/3, 1.999 -> 2 (ratios are exact fractions in practice)."""
    for r in (ratio, 1 / ratio):
        if abs(r - round(r)) <= 0.005 * r:
            return float(round(r)) if r == ratio else 1 / round(r)
    return ratio


def candidate_splits(companyfacts: dict) -> list[Split]:
    """Split events from the ratio facts. Instant facts date the event (the latest one
    in a cluster is the effective date; earlier ones are announcements). Ratios tagged
    only over periods (Coca-Cola) are dated by the earliest period end."""
    groups: dict[float, list[dict]] = {}
    for concept in RATIO_CONCEPTS:
        for units in companyfacts.get("facts", {}).get("us-gaap", {}).get(concept, {}).get("units", {}).values():
            for f in units:
                if f["val"] > 0 and f["val"] != 1:
                    groups.setdefault(round(f["val"], 2), []).append(f)
    splits = []
    for facts in groups.values():
        ratio = _snap(facts[0]["val"])
        instants = sorted(date.fromisoformat(f["end"]) for f in facts if "start" not in f)
        if not instants:
            splits.append(Split(ratio, min(date.fromisoformat(f["end"]) for f in facts)))
            continue
        cluster = [instants[0]]
        for d in instants[1:] + [None]:
            if d is not None and d - cluster[-1] <= timedelta(days=SAME_SPLIT_DAYS):
                cluster.append(d)
            else:
                splits.append(Split(ratio, cluster[-1]))
                cluster = [d]
    return sorted(splits, key=lambda s: s.date)


def _restatement_ratios(nf: NormalisedFacts) -> list[tuple[str, int, float]]:
    """(measure, year, q) where a restated value moved by a split-like factor q (new basis = old / q)."""
    out = []
    for measure in PER_SHARE + SHARE_COUNT:
        for v in nf.series[measure].values:
            if v.restated and v.value and v.original_value:
                q = v.original_value / v.value if measure in PER_SHARE else v.value / v.original_value
                if abs(q - 1) > MATCH_TOLERANCE and _split_like(q):
                    out.append((measure, v.fiscal_year_end.year, q))
    return out


def _split_like(q: float) -> bool:
    return any(abs(r - round(r)) <= MATCH_TOLERANCE * r and round(r) >= 2 for r in (q, 1 / q))


def _runs(splits: list[Split]):
    """Every run of consecutive splits with its combined ratio (a restatement can span several)."""
    for i in range(len(splits)):
        ratio = 1.0
        for j in range(i, len(splits)):
            ratio *= splits[j].ratio
            yield i, j, ratio


def adjust_for_splits(nf: NormalisedFacts, companyfacts: dict) -> NormalisedFacts:
    candidates = candidate_splits(companyfacts)
    evidence = _restatement_ratios(nf)
    confirmed, notes = set(), []
    unexplained = []
    for measure, year, q in evidence:
        hits = [(i, j) for i, j, r in _runs(candidates) if abs(q / r - 1) <= MATCH_TOLERANCE]
        if not hits:
            unexplained.append(f"{measure} {year} was restated by {q:.3g}x, which no split fact explains")
        for i, j in hits:
            confirmed.update(range(i, j + 1))
    for k, s in enumerate(candidates):
        if k not in confirmed:
            notes.append(f"split ratio {s.ratio:.4g} dated {s.date} has no restated value confirming it; not applied")
    applied = [s for k, s in enumerate(candidates) if k in confirmed]
    notes += sorted(set(unexplained))

    out = nf.model_copy(deep=True)
    for measure in PER_SHARE + SHARE_COUNT:
        series = out.series[measure]
        for k, v in enumerate(series.values):
            factor = 1.0
            for s in applied:
                if s.date > v.filed:
                    factor *= s.ratio
            if abs(factor - 1) > 1e-9:
                new = v.value / factor if measure in PER_SHARE else v.value * factor
                series.values[k] = v.model_copy(update={"value": new, "split_factor": factor, "value_before_split": v.value})
        series.notes += [f"split adjustment: {n}" for n in notes]
    return out
