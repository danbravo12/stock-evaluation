"""Orchestrator (ADR-018, ADR-055): plan -> fetch -> score -> qualitative -> explain and verify -> report, for one company.

Every step is timed and traced. A failing step degrades the result instead of aborting it: the failure goes into `Result.warnings`
and the steps that depend on it are skipped with a reason. Quota, budget and missing-fixture errors are the exception: they propagate,
so a batch stops and the company is not recorded as done (ADR-044).
"""
from __future__ import annotations

import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from engine.agents.qualitative import assess_qualitative
from engine.agents.review import explain_and_verify
from engine.contracts import DataBundle, FilingInfo, RunPlan, ScoreSet
from engine.fetch.edgar import EdgarClient
from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.llm.client import LLMClient, LLMFixtureMissing
from engine.normalise import normalise_from_store
from engine.planner import PRICE_GAP, STEPS, plan_for
from engine.report import (Result, ResultWarning, QualItem, RunInfo, StepRecord, build_scorecard, build_sources, cited_passages, cost_from_trace, write_result)
from engine.retrieve import Retriever
from engine.score import score_company
from engine.score.common import load_sector_rules
from engine.settings import REPO_ROOT, Settings
from engine.splits import adjust_for_splits
from engine.successors import has_annual_report, no_annual_report_message
from engine.trace import TraceRecorder
from engine.universe import Universe, load_universe

PROPAGATE = (QuotaReached, BudgetExceeded, LLMFixtureMissing)  # ADR-044
REQUIRES = {"fetch": [], "score": ["fetch"], "qualitative": ["fetch"], "explain_and_verify": ["score", "qualitative"]}


class LogicalClock:
    """Deterministic trace timestamps for replay: second n of 1970-01-01. Replay reproduces a recorded run; it has no wall-clock time."""

    def __init__(self):
        self.n = 0

    def __call__(self) -> datetime:
        self.n += 1
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.n)


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=True).stdout.strip() or None
    except Exception:
        return None


def analyse(ticker: str, *, mode: str = "replay", settings: Settings | None = None, universe: Universe | None = None, edgar: EdgarClient | None = None,
            llm: LLMClient | None = None, results_dir: Path | None = None, run_id: str | None = None, clock: Callable[[], float] | None = None,
            now: Callable[[], datetime] | None = None, commit: str | None = None, write: bool = True, criteria: dict | None = None,
            explanations=None) -> Result:
    """Analyse one ticker end to end and (by default) write `results/<CIK>.json` and its trace. Inject `clock`, `now` and `run_id` for determinism.

    `criteria` replaces the rubric (question and verdict wording) for the agent and the Critic: the stability runs use it for the paraphrases (ADR-070).
    `explanations` (an Explanations object from an earlier run of the same scores) is reviewed instead of calling the Explainer again.
    """
    settings = settings or Settings.from_env()
    edgar = edgar or EdgarClient(mode, settings)
    universe = universe or load_universe(sec_tickers=edgar.company_tickers())
    replay = mode == "replay"
    clock = clock or (lambda: 0.0 if replay else time.perf_counter())
    wall = now or (LogicalClock() if replay else (lambda: datetime.now(timezone.utc)))
    results_dir = Path(results_dir) if results_dir else settings.results_dir

    # ---- plan (also resolves the canonical symbol: one analysis per CIK)
    row = universe.row_for(ticker)
    primary = universe.primary_of(row) if row else None
    symbol = primary.symbol if primary else ticker.upper()
    run_id = run_id or f"{symbol}-{mode}"
    cik_for_paths = primary.cik if primary else None
    trace_file = (results_dir / f"{cik_for_paths}.trace.jsonl") if (write and cik_for_paths) else None
    if trace_file:
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        trace_file.unlink(missing_ok=True)
    trace = TraceRecorder(run_id, trace_file, now=wall)
    if llm is None:
        llm = LLMClient(mode, settings, trace=trace)
    previous_trace, llm.trace, calls_before = llm.trace, trace, len(llm.calls)

    plan: RunPlan | None = None
    steps: list[StepRecord] = []
    warnings: list[ResultWarning] = []
    timings: dict[str, float] = {}
    outputs: dict[str, object] = {}
    state = {r: "pending" for r in STEPS}

    def run(step: str, fn):
        needs = [d for d in REQUIRES.get(step, []) if state[d] != "done"]
        if needs:
            reason = f"depends on {', '.join(needs)}, which did not complete"
            state[step] = "skipped"
            steps.append(StepRecord(step=step, status="skipped", reason=reason))
            warnings.append(ResultWarning(where=step, message=f"skipped: {reason}"))
            trace.note("orchestrator", f"{step}: skipped ({reason})")
            return None
        t0 = clock()
        try:
            out = fn()
        except PROPAGATE:
            raise
        except Exception as e:  # degrade, never abort the whole company
            seconds = round(clock() - t0, 3)
            msg = f"{type(e).__name__}: {str(e)[:300]}"
            state[step] = "failed"
            timings[step] = seconds
            steps.append(StepRecord(step=step, status="failed", seconds=seconds, reason=msg))
            warnings.append(ResultWarning(where=step, message=f"failed: {msg}"))
            trace.note("orchestrator", f"{step}: FAILED ({msg})")
            return None
        seconds = round(clock() - t0, 3)
        state[step] = "done"
        timings[step] = seconds
        steps.append(StepRecord(step=step, status="done", seconds=seconds))
        trace.note("orchestrator", f"{step}: done")
        return out

    try:
        sic = None
        if row is not None:
            try:
                sic = edgar.submissions(row.cik).get("sic")
            except PROPAGATE:
                raise
            except Exception as e:
                warnings.append(ResultWarning(where="plan", message=f"SIC code unavailable ({type(e).__name__}); sector class defaults to 'other'"))
        plan: RunPlan = plan_for(symbol, universe, sic)
        trace.note("orchestrator", f"plan: {symbol} in_scope={plan.in_scope}; not applicable {[x.id for x in plan.not_applicable]}")
        if not plan.in_scope:
            for s in STEPS[:-1]:
                steps.append(StepRecord(step=s, status="skipped", reason=plan.out_of_scope_reason))
            state.update({s: "skipped" for s in STEPS[:-1]})
            warnings.append(ResultWarning(where="plan", message=plan.out_of_scope_reason or "out of scope"))
        elif not has_annual_report(edgar.submissions(edgar.source_for(plan.cik)[0])):  # a new registrant: no 10-K yet, nothing to score (ADR-063)
            msg = no_annual_report_message(row.date_added)
            for s in STEPS[:-1]:
                steps.append(StepRecord(step=s, status="skipped", reason=msg))
            state.update({s: "skipped" for s in STEPS[:-1]})
            warnings.append(ResultWarning(where="plan", message=msg))
        else:
            cik = plan.cik
            source_note = edgar.source_for(cik)[1]
            if source_note:  # a registrant successor read through its predecessor (ADR-063): the note stays visible in the result
                plan.notes.append(source_note)

            def fetch() -> DataBundle:
                nf = adjust_for_splits(normalise_from_store(edgar, cik), edgar.companyfacts(cik))
                ref = edgar.latest_filing(cik, "10-K")
                doc = edgar.filing_document(ref)
                outputs["retriever"] = Retriever(edgar)
                stored = edgar.store.get(f"edgar/{cik}/companyfacts.json")
                sub = edgar.store.get(f"edgar/{cik}/submissions.json")
                return DataBundle(cik=cik, ticker=symbol, entity_name=nf.entity_name, sic=str(sic) if sic else None,
                                  filing=FilingInfo(accession=ref.accession, form=ref.form, filing_date=ref.filing_date, report_date=ref.report_date, url=ref.url),
                                  price=None, gaps=[PRICE_GAP],
                                  as_of={"companyfacts": stored.fetched_at[:10] if stored else "", "submissions": sub.fetched_at[:10] if sub else "",
                                         "10-K": ref.filing_date},
                                  facts=nf)

            bundle = run("fetch", fetch)
            outputs["bundle"] = bundle
            score: ScoreSet | None = run("score", lambda: score_company(bundle.facts, symbol, sic, load_sector_rules(), None, sector=plan.sector_class, sector_notes_=plan.sector_notes))
            qual = run("qualitative", lambda: assess_qualitative(cik, symbol, outputs["retriever"], llm, trace, criteria=criteria))
            review = run("explain_and_verify", lambda: explain_and_verify(score, qual, retriever=outputs["retriever"], llm=llm, trace=trace, criteria=criteria, explanations=explanations))
            outputs.update(score=score, qual=qual, review=review)
    finally:
        llm.trace = previous_trace

    # ---- report
    t0 = clock()
    bundle, score, qual, review = (outputs.get(k) for k in ("bundle", "score", "qual", "review"))
    assert plan is not None
    final_qual = review.qual if review else qual
    status = review.critic.final if review else {}
    if review:
        for item, st in status.items():
            if st == "warning":
                detail = "; ".join(c.detail for c in review.critic.checks if c.item == item and c.attempt == 1 and c.status == "fail") or "see critic checks"
                warnings.append(ResultWarning(where=item, message=f"the Critic still objects after one repair: {detail[:300]}"))
    for f in (final_qual.findings if final_qual else []):
        if f.verdict == "not assessed":
            warnings.append(ResultWarning(where=f.criterion, message=f"not assessed ({f.stop_reason}): {f.rationale}"))
    qual_items = [QualItem(finding=f, critic_status=status.get(f.criterion)) for f in (final_qual.findings if final_qual else [])]
    result = Result(
        run=RunInfo(run_id=run_id, engine_commit=commit if commit is not None else git_commit(), model_profile=llm.profile_name, mode=mode,
                    generated_at=None if replay else wall().replace(microsecond=0).isoformat(), timings=timings),
        plan=plan, steps=steps, data=bundle,
        scorecard=build_scorecard(score, {e.criterion: e for e in review.explanations.items} if review else {}, status) if score else None,
        qualitative=qual_items,
        passages=cited_passages(qual_items, outputs["retriever"]) if qual_items and "retriever" in outputs else {},
        critic=review.critic if review else None,
        cost=cost_from_trace([e for e in trace.events]), sources=build_sources(plan.cik or "", bundle, score),
        attribution=[universe.attribution, "Filings and XBRL data: U.S. Securities and Exchange Commission, EDGAR (public domain)"],
        trace_path=(trace_file.relative_to(REPO_ROOT).as_posix() if trace_file and trace_file.is_relative_to(REPO_ROOT) else (trace_file.name if trace_file else None)),
        warnings=warnings)
    result.steps.append(StepRecord(step="report", status="done", seconds=round(clock() - t0, 3)))
    trace.note("orchestrator", f"report: {len(warnings)} warnings")
    if write and plan.cik:
        write_result(result, results_dir, finnhub_public_ok=settings.finnhub_public_ok)
    return result
