"""Typed hand-off contracts (ADR-020). Only the fact normaliser's output so far."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

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
    split_factor: float = 1.0  # cumulative stock-split ratio applied (ADR-032); 1.0 = untouched
    value_before_split: float | None = None
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


# ---------- scoring (ScoreSet) ----------
Label = Literal["pass", "fail", "partial_pass", "not_applicable", "not_meaningful", "data_gap"]


class InputRef(BaseModel):
    """One input value a criterion used, with its provenance."""

    measure: str
    fiscal_year: int
    fiscal_year_end: date
    value: float
    unit: str
    concept: str
    accession: str
    source_url: str
    flags: list[str] = Field(default_factory=list)  # derived / restated / split_adjusted


class CriterionResult(BaseModel):
    """Structured facts only; the Explainer (LLM) writes the prose later."""

    id: str  # G1..G7, B1..B4
    name: str
    label: Label
    threshold: str
    figures: dict[str, Any] = Field(default_factory=dict)
    by_year: dict[str, Any] = Field(default_factory=dict)
    years: list[int] = Field(default_factory=list)  # fiscal years the test used
    year_label: str | None = None  # G4: "partial (15 of 20 yrs)" or "N yrs on record"
    reason: str | None = None  # why not_applicable / data_gap / not_meaningful
    flags: list[str] = Field(default_factory=list)
    inputs: list[InputRef] = Field(default_factory=list)


class Summary(BaseModel):
    graham_met: int
    graham_applicable: int
    buffett_met: int  # quantitative criteria only; the 4 qualitative ones come later
    buffett_applicable: int
    data_gaps: int
    not_meaningful: int
    not_applicable: int
    percent_met: float | None  # met / applicable, over G and B quantitative


class ScoreSet(BaseModel):
    cik: str
    ticker: str
    as_of_year: int
    sector_class: str
    results: list[CriterionResult]
    summary: Summary
    inputs: list[InputRef]  # every distinct input used, once


# ---------- 10-K sections, passages and search (ADR-035 to ADR-037) ----------
class FilingSection(BaseModel):
    """Where one item of a 10-K sits in the normalised text, or why it was not found."""

    item: str  # "1", "1A", "7"
    status: Literal["found", "not_found"]
    method: Literal["item_heading", "title_fallback"] | None = None
    char_start: int | None = None
    char_end: int | None = None
    length: int = 0
    reason: str | None = None  # why not_found
    accession: str
    sha256: str  # of the source document (not of the normalised text)


class Passage(BaseModel):
    """A citable chunk: document_text[char_start:char_end] == text, exactly."""

    passage_id: str  # "{accession}:{item}:{n}"
    accession: str
    item: str
    n: int
    char_start: int
    char_end: int
    words: int
    text: str


class SearchHit(BaseModel):
    passage_id: str
    item: str
    score: float
    matched_terms: list[str]
    char_start: int
    char_end: int
    text: str
