"""Explain and verify (ADR-010, ADR-049, ADR-052): the Explainer and the Critic together, with routed repairs.

    explanations -> Critic (rules, then one model call) -> each failed item goes to its owner once, by the path that fits the failure:
        explanation                       -> Explainer re-run for that criterion (with the Critic's message)
        finding, rationale only           -> rationale rewrite (verdict and citations untouched)
        finding, verdict failure          -> constrained retry (cite something new, or lower the verdict)
    -> the Critic re-checks the repaired items -> a repair that still fails is dropped: the ORIGINAL finding stays, marked `warning`

The Critic never rewrites a verdict or a sentence itself. Discarded attempts still count in the cost totals.
"""
from __future__ import annotations

from collections import defaultdict

from engine.agents.critic import Critic
from engine.agents.explainer import explain
from engine.agents.qualitative import constrained_retry, qual_totals
from engine.agents.repair import rewrite_rationale
from engine.contracts import (QUAL_CRITERIA, CheckResult, CriticReport, Explanations, QualFinding, QualFindings, Repair, ReviewResult, ScoreSet, Usage)
from engine.trace import TraceRecorder


def _sum_usage(calls) -> Usage:
    return Usage(prompt_tokens=sum(c.usage.prompt_tokens for c in calls), completion_tokens=sum(c.usage.completion_tokens for c in calls),
                 total_tokens=sum(c.usage.total_tokens for c in calls), reasoning_tokens=sum(c.usage.reasoning_tokens for c in calls))


def _add_usage(a: Usage, b: Usage) -> Usage:
    return Usage(prompt_tokens=a.prompt_tokens + b.prompt_tokens, completion_tokens=a.completion_tokens + b.completion_tokens,
                 total_tokens=a.total_tokens + b.total_tokens, reasoning_tokens=a.reasoning_tokens + b.reasoning_tokens)


def _merge_explanations(base: Explanations, retry: Explanations) -> Explanations:
    new = {e.criterion: e for e in retry.items}
    return Explanations(cik=base.cik, ticker=base.ticker, items=[new.get(e.criterion, e) for e in base.items], llm_calls=base.llm_calls + retry.llm_calls,
                        usage=_add_usage(base.usage, retry.usage), actual_cost_usd=base.actual_cost_usd + retry.actual_cost_usd,
                        notional_cost_usd=base.notional_cost_usd + retry.notional_cost_usd)


def _failures(checks: list[CheckResult]) -> dict[tuple[str, str], str]:
    """(owner, item) -> the Critic's message, for every failing check."""
    msgs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for c in checks:
        if c.status == "fail":
            msgs[(c.owner, c.item)].append(f"[{c.check}] {c.detail}")
    return {k: " ".join(v) for k, v in msgs.items()}


def absorb(base: QualFinding, other: QualFinding | None = None, calls=()) -> QualFinding:
    """`base` with the cost of a discarded attempt added (another finding's loop, or plain model calls)."""
    usage, n_llm, n_tool, actual, notional = base.usage, base.llm_calls, base.tool_calls, base.actual_cost_usd, base.notional_cost_usd
    if other is not None:
        usage, n_llm, n_tool = _add_usage(usage, other.usage), n_llm + other.llm_calls, n_tool + other.tool_calls
        actual, notional = actual + other.actual_cost_usd, notional + other.notional_cost_usd
    calls = list(calls)
    if calls:
        usage, n_llm = _add_usage(usage, _sum_usage(calls)), n_llm + len(calls)
        actual, notional = actual + sum(c.actual_cost_usd for c in calls), notional + sum(c.notional_cost_usd for c in calls)
    return base.model_copy(update={"usage": usage, "llm_calls": n_llm, "tool_calls": n_tool, "actual_cost_usd": actual, "notional_cost_usd": notional})


def explain_and_verify(scoreset: ScoreSet, qual: QualFindings, *, retriever, llm, trace: TraceRecorder, criteria: dict | None = None,
                       explanations: Explanations | None = None) -> ReviewResult:
    """`explanations` may be passed to review ones produced elsewhere (tests inject faults this way); otherwise the Explainer runs."""
    critic = Critic(retriever, llm, trace)
    expl = explanations or explain(scoreset, llm, trace)
    critic_calls, checks, repairs = [], [], []

    trace.note("critic", "attempt 0: checking explanations and findings")
    start = len(llm.calls)
    checks += critic.check(scoreset, expl, qual.findings, attempt=0)
    critic_calls += llm.calls[start:]

    failed = _failures(checks)
    fail_expl = {item: msg for (owner, item), msg in failed.items() if owner == "explainer"}
    fail_qual = {item: msg for (owner, item), msg in failed.items() if owner == "qualitative"}

    def failing(item, attempt=0):
        return [c for c in checks if c.item == item and c.attempt == attempt and c.status == "fail" and c.owner == "qualitative"]

    path_of = {}
    for crit in fail_qual:
        kinds = {c.kind for c in failing(crit)}
        path_of[crit] = "constrained_retry" if (kinds & {"verdict", "citation"} or not kinds - {None}) else "rationale_rewrite"
    if failed:
        trace.note("critic", f"routing: explainer gets {sorted(fail_expl) or 'nothing'}; qualitative agent gets "
                             + (", ".join(f"{c} ({p})" for c, p in path_of.items()) or "nothing") + "; one repair each")
    if fail_expl:
        before = expl
        expl = _merge_explanations(expl, explain(scoreset, llm, trace, only=set(fail_expl), feedback=fail_expl))

    findings = list(qual.findings)
    replaced: list[QualFinding] = []
    candidates: dict[str, QualFinding] = {}
    for crit in QUAL_CRITERIA:
        if crit not in fail_qual:
            continue
        k = next(i for i, f in enumerate(findings) if f.criterion == crit)
        orig = findings[k]
        if path_of[crit] == "constrained_retry":
            result, outcome = constrained_retry(qual.cik, qual.ticker, retriever, llm, trace, orig, reason=fail_qual[crit], criteria=criteria)
            if outcome == "submitted":
                candidates[crit] = result
            else:  # nothing usable came back: the original stays
                findings[k] = absorb(orig, result)
                repairs.append(Repair(item=crit, path="constrained_retry", outcome=outcome, detail=result.rationale, llm_calls=result.llm_calls))
                checks.append(CheckResult(check="RETRY", item=crit, status="fail", owner="qualitative", attempt=1,
                                          detail=f"the constrained retry ended without a usable finding ({outcome}); the original finding stands"))
        else:
            start = len(llm.calls)
            problems = [f"{c.check}: {c.detail}" for c in failing(crit)]
            new_text = rewrite_rationale(orig, critic.rubric[crit]["question"], problems, llm, trace, qual.ticker)
            spent = llm.calls[start:]
            if new_text is None:
                findings[k] = absorb(orig, calls=spent)
                repairs.append(Repair(item=crit, path="rationale_rewrite", outcome="invalid_rewrite", detail="the rewrite was empty or too long", llm_calls=len(spent)))
                checks.append(CheckResult(check="RETRY", item=crit, status="fail", owner="qualitative", attempt=1, detail="the rationale rewrite was unusable; the original finding stands"))
            else:
                findings[k] = absorb(orig, calls=spent)  # the rewrite's cost belongs to the finding either way
                candidates[crit] = findings[k].model_copy(update={"rationale": new_text})

    if fail_expl or candidates:
        trace.note("critic", "attempt 1: re-checking the repaired items")
        trial = [candidates.get(f.criterion, f) for f in findings]
        start = len(llm.calls)
        new_checks = critic.check(scoreset, expl, trial, attempt=1, only_explanations=set(fail_expl), only_qual=set(candidates))
        critic_calls += llm.calls[start:]
        checks += new_checks
        for crit, cand in candidates.items():
            k = next(i for i, f in enumerate(findings) if f.criterion == crit)
            ok = not any(c.item == crit and c.status == "fail" for c in new_checks)
            path = path_of[crit]
            if ok:
                if path == "constrained_retry":
                    replaced.append(findings[k])
                findings[k] = cand
            elif path == "constrained_retry":
                findings[k] = absorb(findings[k], cand)  # the attempt is dropped; its cost still counts
            repairs.append(Repair(item=crit, path=path, outcome="accepted" if ok else "rejected_by_recheck",
                                  detail="" if ok else "; ".join(c.detail for c in new_checks if c.item == crit and c.status == "fail"), llm_calls=cand.llm_calls if path == "constrained_retry" else 1))
    for item in fail_expl:
        repairs.append(Repair(item=item, path="explanation_retry", outcome="accepted" if not any(c.item == item and c.attempt == 1 and c.status == "fail" for c in checks) else "rejected_by_recheck",
                              detail=fail_expl[item][:200], llm_calls=0))

    still = {(c.owner, c.item) for c in checks if c.attempt == 1 and c.status == "fail"}
    first = {(c.owner, c.item) for c in checks if c.attempt == 0 and c.status == "fail"}
    final = {}
    for r in scoreset.results:
        final[r.id] = "warning" if ("explainer", r.id) in still else ("passed_after_retry" if ("explainer", r.id) in first else "passed")
    for crit in QUAL_CRITERIA:
        final[crit] = "warning" if ("qualitative", crit) in still else ("passed_after_retry" if ("qualitative", crit) in first else "passed")
    notable = {k: v for k, v in final.items() if v != "passed"}
    trace.note("critic", ("final: " + ", ".join(f"{k}={v}" for k, v in notable.items())) if notable else "final: all items passed")

    report = CriticReport(cik=qual.cik, ticker=qual.ticker, checks=checks, final=final, repairs=repairs, llm_calls=len(critic_calls), usage=_sum_usage(critic_calls),
                          actual_cost_usd=sum(c.actual_cost_usd for c in critic_calls), notional_cost_usd=sum(c.notional_cost_usd for c in critic_calls))
    new_qual = QualFindings(cik=qual.cik, ticker=qual.ticker, accession=qual.accession, findings=findings, totals=qual_totals(findings + replaced))
    return ReviewResult(explanations=expl, qual=new_qual, critic=report)
