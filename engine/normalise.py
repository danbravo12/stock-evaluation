"""Fact normaliser: XBRL company facts -> one annual series per measure.

Pure functions over already-loaded JSON (no I/O except `normalise_from_store`).
It reports what the filings say, with the source of every figure. It never
computes ratios or scores (that is the scorers' job) and never guesses: a missing
figure becomes a `Gap` with a reason. Rules: ADR-026 (annual periods and year
labels), ADR-027 (restatements), ADR-028 (concept map, fallback, derived values).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from engine.contracts import AnnualSeries, AnnualValue, Gap, NormalisedFacts
from engine.settings import REPO_ROOT
from engine.universe import cik10

CONCEPT_MAP_PATH = REPO_ROOT / "config" / "concept_map.json"
ANNUAL_FORMS = {"10-K", "10-K/A"}
DURATION_DAYS = range(350, 381)  # a full fiscal year, 52/53-week years included
FYE_TOLERANCE_DAYS = 7
SAME_YEAR_DAYS = 10  # period ends this close together are the same fiscal year
RESTATED_TOLERANCE = 0.005
DISAGREE_TOLERANCE = 0.01


def load_concept_map(path: Path = CONCEPT_MAP_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------- selecting annual facts ----------
def _d(text: str) -> date:
    return date.fromisoformat(text)


def _near_fiscal_year_end(end: date, mmdd: str) -> bool:
    month, day = int(mmdd[:2]), int(mmdd[2:])
    for year in (end.year - 1, end.year, end.year + 1):
        try:
            fye = date(year, month, day)
        except ValueError:  # 29 Feb
            fye = date(year, month, 28)
        if abs((end - fye).days) <= FYE_TOLERANCE_DAYS:
            return True
    return False


def _is_annual(fact: dict, period: str, fye_mmdd: str) -> bool:
    """Full-year duration, or a balance-sheet date on the fiscal year end, from a 10-K.
    Note: the XBRL `fy`/`fp` fields are deliberately not used (ADR-026)."""
    if fact.get("form") not in ANNUAL_FORMS:
        return False
    if period == "duration":
        return "start" in fact and (_d(fact["end"]) - _d(fact["start"])).days in DURATION_DAYS
    return "start" not in fact and _near_fiscal_year_end(_d(fact["end"]), fye_mmdd)


def _facts_of(companyfacts: dict, concept: str) -> dict:
    taxonomy, name = concept.split(":")
    return companyfacts.get("facts", {}).get(taxonomy, {}).get(name, {}).get("units", {})


def _annual_values(companyfacts: dict, concept: str, spec: dict, fye_mmdd: str) -> dict[date, AnnualValue]:
    """Annual values of one concept keyed by period end. Where several filings report
    the same period, the latest-filed value wins; it is flagged if it differs from the
    first-reported one (ADR-027)."""
    taxonomy, name = concept.split(":")
    by_end: dict[date, list[dict]] = {}
    for f in _facts_of(companyfacts, concept).get(spec["unit"], []):
        if _is_annual(f, spec["period"], fye_mmdd):
            by_end.setdefault(_d(f["end"]), []).append(f)
    cik = int(companyfacts["cik"])
    out = {}
    for end, group in by_end.items():
        group.sort(key=lambda f: (f["filed"], f["accn"]))
        first, last = group[0], group[-1]
        restated = _differs(first["val"], last["val"], RESTATED_TOLERANCE)
        out[end] = AnnualValue(
            fiscal_year_end=end, value=last["val"], unit=spec["unit"], concept=name, taxonomy=taxonomy,
            accession=last["accn"], form=last["form"], filed=_d(last["filed"]),
            period_start=_d(last["start"]) if "start" in last else None,
            restated=restated, original_value=first["val"] if restated else None,
            source_url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{last['accn'].replace('-', '')}/",
        )
    return out


def _differs(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) > tolerance * max(abs(a), abs(b))


def _derived_values(parts: list[dict[date, AnnualValue]], concepts: list[str]) -> dict[date, AnnualValue]:
    """Explicit sum of several concepts, only for years where every part exists (ADR-028)."""
    out = {}
    for end in set.intersection(*(set(p) for p in parts)):
        vals = [p[end] for p in parts]
        newest = max(vals, key=lambda v: v.filed)
        out[end] = newest.model_copy(update={
            "value": sum(v.value for v in vals), "concept": "+".join(c.split(":")[1] for c in concepts),
            "restated": any(v.restated for v in vals), "original_value": None,
            "derived": True, "source_concepts": concepts,
        })
    return out


# ---------- one measure ----------
def _candidates(companyfacts: dict, spec: dict, fye_mmdd: str) -> list[tuple[str | None, dict[date, AnnualValue]]]:
    """One (note, end-date -> value) pair per entry of the priority list, in priority order.
    A {"sum": [...]} entry is a derived value; its optional "note" is added to the series
    whenever that entry supplies a year (a one-concept sum is a flagged last resort)."""
    result = []
    for entry in spec["concepts"]:
        if isinstance(entry, dict):
            parts = [_annual_values(companyfacts, c, spec, fye_mmdd) for c in entry["sum"]]
            result.append((entry.get("note"), _derived_values(parts, entry["sum"])))
        else:
            result.append((None, _annual_values(companyfacts, entry, spec, fye_mmdd)))
    return result


def _pick_per_year(measure: str, candidates: list[tuple[str | None, dict[date, AnnualValue]]], spec: dict | None = None) -> tuple[list[AnnualValue], list[str]]:
    """Per fiscal year, take the first concept in priority order that has a value.

    If the spec has `component_guard` (a fraction, ADR-061), a candidate worth less than that fraction of the largest candidate for the same year is
    treated as a component (a segment, or fee income only), not the total, and skipped; the note says so.
    """
    guard = (spec or {}).get("component_guard")
    values, notes = [], []
    for end in sorted(set().union(*(c for _, c in candidates))):
        have = [(note, c[end]) for note, c in candidates if end in c]
        skipped = []
        if guard and len(have) > 1:
            biggest = max(v.value for _, v in have)
            keep = [(n, v) for n, v in have if v.value >= guard * biggest]
            skipped = [v for _, v in have if v.value < guard * biggest]
            have = keep or have
        (note, chosen), others = have[0], [v for _, v in have[1:]]
        values.append(chosen)
        for v in skipped:
            notes.append(f"{end}: {measure} {v.concept}={v.value:g} skipped: below {guard:.0%} of the largest candidate for the year, so a component, not the total")
        if note:
            notes.append(f"{end}: {measure} uses {chosen.concept} alone, {note}")
        for other in others:
            if _differs(chosen.value, other.value, DISAGREE_TOLERANCE):
                notes.append(f"{end}: {measure} {chosen.concept}={chosen.value:g} used; "
                             f"{other.concept}={other.value:g} differs by more than 1%")
    return values, notes


def _why_missing(companyfacts: dict, spec: dict, end: date | None) -> str:
    """Best explanation for a missing figure, from what the listed concepts do contain."""
    concepts = [c for e in spec["concepts"] for c in (e["sum"] if isinstance(e, dict) else [e])]
    other_unit = False
    for concept in concepts:
        units = _facts_of(companyfacts, concept)
        other_unit = other_unit or bool(set(units) - {spec["unit"]})
        for f in units.get(spec["unit"], []):
            if end is None or abs((_d(f["end"]) - end).days) <= SAME_YEAR_DAYS:
                return ("only non-annual data (e.g. quarterly) or an incomplete derived sum "
                        "for this period")
    if other_unit:
        return f"unit mismatch: listed concepts are reported in other units, expected {spec['unit']}"
    return "no listed concept reported"


# ---------- whole company ----------
def _fiscal_years(all_values: list[list[AnnualValue]]) -> list[tuple[date, date]]:
    """Group every period end seen for the company into fiscal years (ends within a few
    days of each other are one year). Used to place gaps."""
    ends = sorted({v.fiscal_year_end for values in all_values for v in values})
    years: list[tuple[date, date]] = []
    for end in ends:
        if years and end - years[-1][0] <= timedelta(days=SAME_YEAR_DAYS):
            years[-1] = (years[-1][0], end)
        else:
            years.append((end, end))
    return years


def normalise(companyfacts: dict, submissions: dict, concept_map: dict, provenance: dict) -> NormalisedFacts:
    """`provenance` = {"fetched_at": ..., "sha256": ...} of the companyfacts response."""
    fye = submissions.get("fiscalYearEnd")
    if not fye:
        raise ValueError("submissions has no fiscalYearEnd; cannot identify fiscal year ends")
    measures = concept_map["measures"]
    picked = {}
    for measure, spec in measures.items():
        picked[measure] = _pick_per_year(measure, _candidates(companyfacts, spec, fye), spec)

    years = _fiscal_years([values for values, _ in picked.values()])
    series = {}
    for measure, spec in measures.items():
        values, notes = picked[measure]
        gaps = []
        if not values:
            gaps.append(Gap(fiscal_year_end=None, reason=_why_missing(companyfacts, spec, None)))
        else:
            have = [v.fiscal_year_end for v in values]
            first = min(i for i, (lo, hi) in enumerate(years) if any(lo <= e <= hi for e in have))
            for lo, hi in years[first:]:
                if not any(lo <= e <= hi for e in have):
                    gaps.append(Gap(fiscal_year_end=hi, reason=_why_missing(companyfacts, spec, hi)))
        series[measure] = AnnualSeries(measure=measure, unit=spec["unit"], values=values, gaps=gaps, notes=notes)

    return NormalisedFacts(
        cik=cik10(companyfacts["cik"]), entity_name=companyfacts["entityName"], fiscal_year_end_mmdd=fye,
        series=series, companyfacts_fetched_at=provenance["fetched_at"], companyfacts_sha256=provenance["sha256"],
    )


def normalise_from_store(client, cik: str, concept_map: dict | None = None) -> NormalisedFacts:
    """Convenience wrapper: read a company through an EdgarClient (replay mode in tests)."""
    facts, submissions = client.companyfacts(cik), client.submissions(cik)  # fetch first: in live mode the store is empty until then
    stored = client.store.get(f"edgar/{cik10(cik)}/companyfacts.json")
    return normalise(facts, submissions, concept_map or load_concept_map(), {"fetched_at": stored.fetched_at, "sha256": stored.sha256})
