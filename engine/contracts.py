"""Typed hand-off contracts (ADR-020). Only the fact normaliser's output so far."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

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
    sentences: list[tuple[int, int]] = Field(default_factory=list)  # document offsets of each sentence (engine/sentences.py)


class SearchHit(BaseModel):
    passage_id: str
    item: str
    score: float
    matched_terms: list[str]
    char_start: int
    char_end: int
    text: str


# ---------- LLM calls and trace (ADR-038 to ADR-040, ADR-020) ----------
class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0  # includes thinking tokens when the provider reports them
    total_tokens: int = 0
    reasoning_tokens: int = 0  # informational: the thinking part of completion_tokens, when reported


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class LLMCall(BaseModel):
    """One model call, in a provider-neutral shape, with its cost record."""

    profile: str
    model: str
    request_hash: str
    replayed: bool  # served from fixtures or cache: no network, no spend
    paid: bool  # True only for a call billed beyond the free-tier quota
    latency_s: float  # of the original call, also when replayed
    usage: Usage
    actual_cost_usd: float  # 0 on the free tier and for replays
    notional_cost_usd: float  # tokens x paid price: what the call would cost on the paid tier
    finish_reason: str | None = None
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    message: dict[str, Any] = Field(default_factory=dict)  # raw assistant message: append it to the history as is


class TraceEvent(BaseModel):
    run_id: str
    step: int
    agent: str
    type: Literal["llm_call", "tool_call", "note"]
    ts: str  # ISO 8601 UTC
    input_summary: str = ""
    output: Any = None
    usage: Usage | None = None
    latency_s: float | None = None
    actual_cost_usd: float | None = None
    notional_cost_usd: float | None = None
    replayed: bool | None = None


# ---------- qualitative agent (ADR-018, ADR-041 to ADR-045) ----------
QUAL_CRITERIA = ("understandable_business", "durable_competitive_advantage", "candid_management", "rational_capital_allocation")
# "insufficient evidence": the filing, as retrieved, does not show it. "not assessed": the system could not judge (any stop_reason but "submitted").
Verdict = Literal["evidence found", "evidence weak", "insufficient evidence", "not assessed"]
StopReason = Literal["submitted", "turn_cap", "invalid_citation", "section_missing", "llm_output_error"]


class Citation(BaseModel):
    """A cited span of a passage, by sentence pointer: normalised_document_text[char_start:char_end] == quote, exactly (ADR-035, ADR-042).

    The model gives passage_id and sentence numbers; code builds the quote and the offsets, so they cannot mismatch (ADR-046)."""

    passage_id: str
    accession: str
    item: str
    char_start: int
    char_end: int
    quote: str
    sentences: list[int]  # [first, last], 1-based inclusive, within the passage


class SearchRecord(BaseModel):
    """One retrieval the agent ran: the seeded search (decided in code) or one the model asked for."""

    queries: list[str]
    items: list[str] | None = None
    seeded: bool = False
    passage_ids: list[str] = Field(default_factory=list)


class QualFinding(BaseModel):
    criterion: Literal[QUAL_CRITERIA]  # type: ignore[valid-type]
    verdict: Verdict
    rationale: str  # at most two sentences, about the filing only
    citations: list[Citation] = Field(default_factory=list)  # 0-2; at least 1 unless the verdict is "insufficient evidence"
    searches: list[SearchRecord] = Field(default_factory=list)
    llm_calls: int = 0
    tool_calls: int = 0  # every tool call executed, including the seeded search
    stop_reason: StopReason
    usage: Usage = Field(default_factory=Usage)
    actual_cost_usd: float = 0.0
    notional_cost_usd: float = 0.0

    @model_validator(mode="after")
    def _consistent(self):
        if len(self.citations) > 2:
            raise ValueError("at most 2 citations")
        if self.stop_reason != "submitted":
            if self.verdict != "not assessed" or self.citations:
                raise ValueError(f"stop_reason {self.stop_reason!r} can only end in 'not assessed' without citations")
        elif self.verdict == "not assessed":
            raise ValueError("a submitted finding is found, weak or insufficient")
        elif self.verdict != "insufficient evidence" and not self.citations:
            raise ValueError(f"verdict {self.verdict!r} needs at least one citation")
        return self


class QualTotals(BaseModel):
    llm_calls: int = 0
    tool_calls: int = 0
    usage: Usage = Field(default_factory=Usage)
    actual_cost_usd: float = 0.0
    notional_cost_usd: float = 0.0


class QualFindings(BaseModel):
    cik: str
    ticker: str
    accession: str  # the 10-K every citation refers to
    findings: list[QualFinding]  # exactly four, in config order
    totals: QualTotals

    @model_validator(mode="after")
    def _four_in_order(self):
        if [f.criterion for f in self.findings] != list(QUAL_CRITERIA):
            raise ValueError(f"findings must be exactly {list(QUAL_CRITERIA)} in that order")
        return self
