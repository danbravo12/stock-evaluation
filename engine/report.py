"""Result (schema 1.0) and the Reporter (ADR-020, ADR-054).

`build_result` assembles what the orchestrator collected into one validated object; `write_result` applies the Finnhub publish gate
(ADR-021), writes `results/<CIK>.json` and exports the JSON Schema for the site. The trace is a separate file so a result stays small.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.contracts import (SEC_SOURCE, CriticReport, DataBundle, Explanation, InputRef, QualFinding, RunPlan, ScoreSet, Summary, TraceEvent)
from engine.settings import REPO_ROOT

SCHEMA_VERSION = "1.0"
DISCLAIMER = ("Research tool, not financial advice. Scores and findings describe public filings; they are not recommendations to buy, sell or hold any security. "
              "Qualitative findings are produced by a language model, checked by code and a second model pass, and can be wrong.")
SCHEMA_PATH = REPO_ROOT / "schema" / "result.schema.json"
FINNHUB_KEY = re.compile(r"^(price|analyst\w*|finnhub\w*)$", re.I)


class RunInfo(BaseModel):
    run_id: str
    engine_commit: str | None = None
    model_profile: str
    mode: Literal["replay", "live", "record"]
    generated_at: str | None = None  # None in replay: a replay reproduces a recorded run, it has no wall-clock time of its own
    timings: dict[str, float] = Field(default_factory=dict)  # seconds per step (0.0 in replay)


class StepRecord(BaseModel):
    step: str
    status: Literal["done", "failed", "skipped"]
    seconds: float = 0.0
    reason: str | None = None


class ScoredCriterion(BaseModel):
    id: str
    name: str
    label: str
    threshold: str
    figures: dict[str, Any] = Field(default_factory=dict)
    by_year: dict[str, Any] = Field(default_factory=dict)
    years: list[int] = Field(default_factory=list)
    year_label: str | None = None
    reason: str | None = None
    flags: list[str] = Field(default_factory=list)
    input_keys: list[str] = Field(default_factory=list)  # "measure:fiscal_year" keys into Scorecard.inputs
    explanation: Explanation | None = None
    critic_status: str | None = None


class Scorecard(BaseModel):
    as_of_year: int
    sector_class: str
    summary: Summary
    criteria: list[ScoredCriterion]
    inputs: list[InputRef]  # every distinct input once, each with concept, accession and URL


class QualItem(BaseModel):
    finding: QualFinding
    critic_status: str | None = None


class AgentCost(BaseModel):
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    actual_cost_usd: float = 0.0
    notional_cost_usd: float = 0.0


class Cost(BaseModel):
    actual_cost_usd: float = 0.0
    notional_cost_usd: float = 0.0
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    by_agent: dict[str, AgentCost] = Field(default_factory=dict)


class Source(BaseModel):
    kind: str
    label: str
    url: str | None = None
    as_of: str | None = None


class ResultWarning(BaseModel):
    where: str  # a step or an item
    message: str


class Result(BaseModel):
    schema_version: str = SCHEMA_VERSION
    disclaimer: str = DISCLAIMER
    run: RunInfo
    plan: RunPlan
    steps: list[StepRecord] = Field(default_factory=list)
    data: DataBundle | None = None
    scorecard: Scorecard | None = None
    qualitative: list[QualItem] = Field(default_factory=list)
    critic: CriticReport | None = None
    cost: Cost = Field(default_factory=Cost)
    sources: list[Source] = Field(default_factory=list)
    attribution: list[str] = Field(default_factory=list)
    trace_path: str | None = None
    warnings: list[ResultWarning] = Field(default_factory=list)


# ---------- assembling ----------
def cost_from_trace(events: list[TraceEvent]) -> Cost:
    """Calls, tokens and cost per agent family (qualitative incl. rewrites, explainer, critic) from the run's LLM-call events."""
    cost = Cost()
    for e in events:
        if e.type != "llm_call" or e.usage is None:
            continue
        a = cost.by_agent.setdefault(e.agent.split("/")[0], AgentCost())
        for t in (a, cost):
            t.input_tokens += e.usage.prompt_tokens
            t.output_tokens += e.usage.completion_tokens
            t.actual_cost_usd += e.actual_cost_usd or 0.0
            t.notional_cost_usd += e.notional_cost_usd or 0.0
        a.calls += 1
        cost.llm_calls += 1
    for t in [cost, *cost.by_agent.values()]:
        t.actual_cost_usd, t.notional_cost_usd = round(t.actual_cost_usd, 6), round(t.notional_cost_usd, 6)
    cost.by_agent = dict(sorted(cost.by_agent.items()))
    return cost


def build_scorecard(score: ScoreSet, expl: dict[str, Explanation], status: dict[str, str]) -> Scorecard:
    criteria = [ScoredCriterion(id=r.id, name=r.name, label=r.label, threshold=r.threshold, figures=r.figures, by_year=r.by_year, years=r.years, year_label=r.year_label,
                                reason=r.reason, flags=r.flags, input_keys=sorted({f"{i.measure}:{i.fiscal_year}" for i in r.inputs}),
                                explanation=expl.get(r.id), critic_status=status.get(r.id)) for r in score.results]
    return Scorecard(as_of_year=score.as_of_year, sector_class=score.sector_class, summary=score.summary, criteria=criteria, inputs=score.inputs)


def build_sources(cik: str, bundle: DataBundle | None, score: ScoreSet | None) -> list[Source]:
    if bundle is None:
        return []
    src = [Source(kind="sec_filing", label=f"Form 10-K {bundle.filing.accession}", url=bundle.filing.url, as_of=bundle.filing.filing_date),
           Source(kind="sec_xbrl", label="XBRL company facts", url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", as_of=bundle.as_of.get("companyfacts")),
           Source(kind="sec_submissions", label="Filing history", url=f"https://data.sec.gov/submissions/CIK{cik}.json", as_of=bundle.as_of.get("submissions"))]
    seen = {s.url for s in src}
    for i in (score.inputs if score else []):
        if i.source_url not in seen:
            seen.add(i.source_url)
            src.append(Source(kind="sec_filing", label=f"Filing used for {i.measure} {i.fiscal_year}", url=i.source_url, as_of=None))
    return src


# ---------- the publish gate and writing ----------
def finnhub_fields(obj: Any, path: str = "") -> list[str]:
    """Paths of Finnhub-sourced fields that carry a value: a `price`, `analyst*` or `finnhub*` key that is not null / empty (ADR-021)."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            if FINNHUB_KEY.match(k) and v not in (None, "", [], {}):
                found.append(here)
            found += finnhub_fields(v, here)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found += finnhub_fields(v, f"{path}[{i}]")
    return found


class PublishGateError(RuntimeError):
    pass


def result_json(result: Result) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def write_result(result: Result, results_dir: Path, *, finnhub_public_ok: bool = False) -> Path:
    """Validate (round trip), apply the Finnhub gate, write `<results_dir>/<CIK>.json`; returns the path."""
    text = result_json(result)
    Result.model_validate_json(text)  # fails loudly if what we are about to write does not satisfy the schema
    if not finnhub_public_ok:
        leaked = finnhub_fields(json.loads(text))
        if leaked:
            raise PublishGateError(f"Finnhub-sourced fields in a result while FINNHUB_PUBLIC_OK is off (ADR-021): {leaked}")
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    cik = result.plan.cik or result.plan.ticker
    path = results_dir / f"{cik}.json"
    path.write_text(text, encoding="utf-8")
    return path


def export_schema(path: Path = SCHEMA_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(Result.model_json_schema(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["Result", "SCHEMA_VERSION", "DISCLAIMER", "SEC_SOURCE", "write_result", "export_schema", "build_scorecard", "build_sources", "cost_from_trace", "finnhub_fields"]
