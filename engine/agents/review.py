"""Explain and verify (ADR-010, ADR-049): the Explainer and the Critic together, with routed retries. No orchestrator yet.

    explanations -> Critic (rules, then one model call) -> failed items go to their owner, once -> Critic re-checks those items
    -> still failing: keep the item and attach a visible warning

The Critic never rewrites a verdict or a sentence. A retried qualitative criterion is the agent's own new output (it saw the Critic's
reason in its first message); if that still fails, the agent's latest output is kept and marked `warning`.
"""
from __future__ import annotations

from collections import defaultdict

from engine.agents.critic import Critic
from engine.agents.explainer import explain
from engine.agents.qualitative import qual_totals, reassess_criterion
from engine.contracts import (QUAL_CRITERIA, CheckResult, CriticReport, Explanations, QualFindings, ReviewResult, ScoreSet, Usage)
from engine.trace import TraceRecorder


def _sum_usage(calls) -> Usage:
    return Usage(prompt_tokens=sum(c.usage.prompt_tokens for c in calls), completion_tokens=sum(c.usage.completion_tokens for c in calls),
                 total_tokens=sum(c.usage.total_tokens for c in calls), reasoning_tokens=sum(c.usage.reasoning_tokens for c in calls))


def _merge_explanations(base: Explanations, retry: Explanations) -> Explanations:
    new = {e.criterion: e for e in retry.items}
    return Explanations(cik=base.cik, ticker=base.ticker, items=[new.get(e.criterion, e) for e in base.items],
                        llm_calls=base.llm_calls + retry.llm_calls, usage=Usage(
                            prompt_tokens=base.usage.prompt_tokens + retry.usage.prompt_tokens, completion_tokens=base.usage.completion_tokens + retry.usage.completion_tokens,
                            total_tokens=base.usage.total_tokens + retry.usage.total_tokens, reasoning_tokens=base.usage.reasoning_tokens + retry.usage.reasoning_tokens),
                        actual_cost_usd=base.actual_cost_usd + retry.actual_cost_usd, notional_cost_usd=base.notional_cost_usd + retry.notional_cost_usd)


def _failures(checks: list[CheckResult]) -> dict[tuple[str, str], str]:
    """(owner, item) -> the Critic's message, for every failing check."""
    msgs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for c in checks:
        if c.status == "fail":
            msgs[(c.owner, c.item)].append(f"[{c.check}] {c.detail}")
    return {k: " ".join(v) for k, v in msgs.items()}


def explain_and_verify(scoreset: ScoreSet, qual: QualFindings, *, retriever, llm, trace: TraceRecorder, criteria: dict | None = None,
                       explanations: Explanations | None = None) -> ReviewResult:
    """`explanations` may be passed to review ones produced elsewhere (tests inject faults this way); otherwise the Explainer runs."""
    critic = Critic(retriever, llm, trace)
    expl = explanations or explain(scoreset, llm, trace)
    critic_calls = []
    checks: list[CheckResult] = []

    trace.note("critic", "attempt 0: checking explanations and findings")
    start = len(llm.calls)
    checks += critic.check(scoreset, expl, qual.findings, attempt=0)
    critic_calls += llm.calls[start:]

    failed = _failures(checks)
    fail_expl = {item: msg for (owner, item), msg in failed.items() if owner == "explainer"}
    fail_qual = {item: msg for (owner, item), msg in failed.items() if owner == "qualitative"}
    findings = list(qual.findings)
    replaced = []
    if failed:
        trace.note("critic", f"routing: explainer gets {sorted(fail_expl) or 'nothing'}, qualitative agent gets {sorted(fail_qual) or 'nothing'}; one retry each")
    if fail_expl:
        expl = _merge_explanations(expl, explain(scoreset, llm, trace, only=set(fail_expl), feedback=fail_expl))
    for crit in QUAL_CRITERIA:
        if crit in fail_qual:
            k = next(i for i, f in enumerate(findings) if f.criterion == crit)
            replaced.append(findings[k])
            findings[k] = reassess_criterion(qual.cik, qual.ticker, retriever, llm, trace, crit, feedback=fail_qual[crit], criteria=criteria)
    if failed:
        trace.note("critic", "attempt 1: re-checking the retried items")
        start = len(llm.calls)
        checks += critic.check(scoreset, expl, findings, attempt=1, only_explanations=set(fail_expl), only_qual=set(fail_qual))
        critic_calls += llm.calls[start:]
        for f in findings:  # a retry that ends "not assessed" leaves nothing the Critic could confirm: warn rather than call it passed
            if f.criterion in fail_qual and f.verdict == "not assessed":
                checks.append(CheckResult(check="RETRY", item=f.criterion, status="fail", owner="qualitative", attempt=1,
                                          detail=f"the retried loop ended 'not assessed' ({f.stop_reason}): there is no finding left to confirm"))

    still = {(c.owner, c.item) for c in checks if c.attempt == 1 and c.status == "fail"}
    first = {(c.owner, c.item) for c in checks if c.attempt == 0 and c.status == "fail"}
    final = {}
    for r in scoreset.results:
        final[r.id] = "warning" if ("explainer", r.id) in still else ("passed_after_retry" if ("explainer", r.id) in first else "passed")
    for crit in QUAL_CRITERIA:
        final[crit] = "warning" if ("qualitative", crit) in still else ("passed_after_retry" if ("qualitative", crit) in first else "passed")
    trace.note("critic", "final: " + ", ".join(f"{k}={v}" for k, v in final.items() if v != "passed") if any(v != "passed" for v in final.values()) else "final: all items passed")

    report = CriticReport(cik=qual.cik, ticker=qual.ticker, checks=checks, final=final, llm_calls=len(critic_calls), usage=_sum_usage(critic_calls),
                          actual_cost_usd=sum(c.actual_cost_usd for c in critic_calls), notional_cost_usd=sum(c.notional_cost_usd for c in critic_calls))
    new_qual = QualFindings(cik=qual.cik, ticker=qual.ticker, accession=qual.accession, findings=findings, totals=qual_totals(findings + replaced))
    return ReviewResult(explanations=expl, qual=new_qual, critic=report)
