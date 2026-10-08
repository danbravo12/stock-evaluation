"""Typed hand-off contracts (ADR-020). Only the fact normaliser's output so far."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

SEC_SOURCE = "U.S. Securities and Exchange Commission, EDGAR (public domain)"


class AnnualValue(BaseModel):
    """One figure for one fiscal year, with where it came from."""

    fiscal_year_end: date  # the period end date: the only year label we trust (ADR-026)
    value: float
    unit: str
    concept: str
    taxonomy: str
    accession: str
    form: str
    filed: date
    period_start: date | None = None  # None for balance-sheet (instant) figures
    restated: bool = False
    original_value: float | None = None  # first-reported value, set when restated
    derived: bool = False
    source_concepts: list[str] = Field(default_factory=list)
    source_url: str  # filing folder on sec.gov


class Gap(BaseModel):
    fiscal_year_end: date | None  # None: the whole measure is missing
    reason: str


class AnnualSeries(BaseModel):
    measure: str
    unit: str
    values: list[AnnualValue]  # sorted by fiscal_year_end
    gaps: list[Gap]
    notes: list[str] = Field(default_factory=list)


class NormalisedFacts(BaseModel):
    cik: str
    entity_name: str
    fiscal_year_end_mmdd: str
    series: dict[str, AnnualSeries]
    source: str = SEC_SOURCE
    companyfacts_fetched_at: str
    companyfacts_sha256: str
