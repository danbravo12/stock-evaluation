"""Tiny builders for synthetic NormalisedFacts, shared by the scorer and split tests."""
from __future__ import annotations

from datetime import date

from engine.contracts import AnnualSeries, AnnualValue, NormalisedFacts
from engine.normalise import load_concept_map
from engine.score.common import Facts

UNITS = {m: s["unit"] for m, s in load_concept_map()["measures"].items()}


def value(measure: str, year: int, v: float, **extra) -> AnnualValue:
    fields = dict(
        fiscal_year_end=date(year, 12, 31), value=v, unit=UNITS[measure], concept=measure, taxonomy="us-gaap",
        accession=f"0000000001-{year + 1}-000001", form="10-K", filed=date(year + 1, 2, 1),
        source_url=f"https://www.sec.gov/Archives/edgar/data/1/{year}/",
    )
    fields.update(extra)
    return AnnualValue(**fields)


def facts(data: dict[str, dict[int, float]], **extra) -> NormalisedFacts:
    """data = {measure: {year: value}}; measures not given get an empty series."""
    series = {m: AnnualSeries(measure=m, unit=u, gaps=[], values=[value(m, y, v, **extra) for y, v in sorted(data.get(m, {}).items())])
              for m, u in UNITS.items()}
    return NormalisedFacts(cik="0000000001", entity_name="TEST", fiscal_year_end_mmdd="1231", series=series,
                           companyfacts_fetched_at="2026-01-01T00:00:00+00:00", companyfacts_sha256="x")


def flat(years, v) -> dict[int, float]:
    return {y: v for y in years}


def table(data) -> Facts:
    return Facts(facts(data))
