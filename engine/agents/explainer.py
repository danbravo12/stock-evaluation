"""Explainer (ADR-005, ADR-019, ADR-048): one plain-English line per numeric criterion.

The model never writes a figure. It writes `{figure_key}` (and `{threshold}`), and code renders the value from the criterion's own
`figures` with the format in config/figure_formats.json, so a number in an explanation cannot be wrong. not_applicable and data_gap
results get a templated line from their `reason`, without a model call. The Critic checks the output (rules first, ADR-019).
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel

from engine.prompts import active as active_prompt
from engine.contracts import CriterionResult, Explanation, Explanations, ScoreSet, Usage
from engine.settings import REPO_ROOT
from engine.trace import TraceRecorder

FORMATS_PATH = REPO_ROOT / "config" / "figure_formats.json"
PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
LLM_LABELS = ("pass", "fail", "partial_pass", "not_meaningful")
MAX_WORDS = 45

SYSTEM_PROMPT = """You write short plain-English explanations of scorecard results for a research tool about a company's financial statements. \
It is not investment advice.

For each criterion write one or two sentences, at most 45 words, saying what the figures show against the threshold.
Rules:
- Never write a figure yourself. Write its placeholder in braces, for example {revenue} or {ratio}; the system replaces it with the value only (for example "$47.94 billion" or "2.43"), so always name the quantity in words before it: "a current ratio of {current_ratio}", "long-term debt of {long_term_debt}". Use only the placeholder keys listed for that criterion.
- Give the threshold, if at all, last and in parentheses as "(test: {threshold})"; never use it in the middle of a sentence. Use the terms of the criterion's own name and threshold ("3-year average", "owner earnings") correctly.
- Write no other digits, except a fiscal year listed for that criterion.
- Do not just restate the result word (pass, fail, partial, not meaningful); say what the figures show.
- No investment opinion, advice or valuation language (no buy, sell, hold, cheap, expensive, attractive, undervalued). Describe the company's statements only.
- For a "not meaningful" result, explain why from the reason given.
What the result words mean (do not restate the word, but never contradict it):
- pass: the test was met.
- partial_pass: the test was met on the shorter record that exists (for example a dividend test on the years on record). Say this neutrally, such as "on the {years_on_record} years on record"; never use wording that sounds like a failure.
- fail: the test was not met.
- not_meaningful: the test cannot be interpreted; explain why from the reason.

Examples of the style wanted (placeholders in braces):
- Good: "Revenue in 2025 was {revenue}, comfortably above the minimum size (test: {threshold})."
- Good (partial pass): "Dividends were paid in every one of the {years_on_record} years on record, which is all the history available for this test (test: {threshold})."
- Good: "Net income was positive in each of the {years_on_record} years on record, with no loss years (test: {threshold})."
- Bad: "Net income was positive with none years showing a loss." (broken grammar)
- Bad: "Dividends were paid, but this does not cover the full period required." (sounds like a failure for a partial pass)
- Bad: "The three-year average rose from the first-year average ..." (a three-year average is not a first-year average; use the names in the criterion)
Reply with only a JSON object: {"explanations": [{"criterion": "<id>", "text": "<your sentences with placeholders>"}]}"""


SYSTEM_PROMPT_V2 = """You write short plain-English explanations of scorecard results for a research tool about a company's financial statements. \
It is not investment advice.

For each criterion write one or two sentences, at most 45 words, saying what the figures show against the threshold.
Rules:
- Never write a figure yourself. Write its placeholder in braces, for example {revenue} or {ratio}; the system replaces it with the value only (for example "$47.94 billion" or "2.43"), so always name the quantity in words before it: "a current ratio of {current_ratio}", "long-term debt of {long_term_debt}". Use only the placeholder keys listed for that criterion.
- Give the threshold, if at all, last and in parentheses as "(test: {threshold})"; never use it in the middle of a sentence. Use the terms of the criterion's own name and threshold ("3-year average", "owner earnings") correctly.
- Write no other digits, except a fiscal year listed for that criterion.
- When a figure is a list of years, say how many with its count placeholder ({loss_year_count}, {profit_year_count}, {unpaid_year_count}, {paid_year_count}, {depreciation_only_year_count}); use the list itself ({loss_years}, {unpaid_years}) only to name the years, and never write "none years".
- Do not just restate the result word (pass, fail, partial, not meaningful); say what the figures show.
- No investment opinion, advice or valuation language (no buy, sell, hold, cheap, expensive, attractive, undervalued). Describe the company's statements only.
- For a "not meaningful" result, explain why from the reason given.
What the result words mean (do not restate the word, but never contradict it):
- pass: the test was met.
- partial_pass: the test was met on the shorter record that exists (for example a dividend test on the years on record). Say this neutrally, such as "on the {years_on_record} years on record"; never use wording that sounds like a failure.
- fail: the test was not met.
- not_meaningful: the test cannot be interpreted; explain why from the reason.

Examples of the style wanted (placeholders in braces):
- Good: "Revenue in 2025 was {revenue}, comfortably above the minimum size (test: {threshold})."
- Good (partial pass): "Dividends were paid in every one of the {years_on_record} years on record, which is all the history available for this test (test: {threshold})."
- Good: "Net income was positive in each of the {years_on_record} years on record, with {loss_year_count} loss years (test: {threshold})."
- Good: "Dividends were paid in {paid_year_count} of the {years_on_record} years on record and missed in {unpaid_year_count} (test: {threshold})."
- Bad: "Net income was positive with none years showing a loss." (broken grammar; use the count)
- Bad: "Dividends were paid, but this does not cover the full period required." (sounds like a failure for a partial pass)
- Bad: "The three-year average rose from the first-year average ..." (a three-year average is not a first-year average; use the names in the criterion)
Reply with only a JSON object: {"explanations": [{"criterion": "<id>", "text": "<your sentences with placeholders>"}]}"""




class _Item(BaseModel):
    criterion: str
    text: str


class _Out(BaseModel):
    explanations: list[_Item]


def system_prompt() -> str:
    return SYSTEM_PROMPT_V2 if active_prompt("explainer") == "v2" else SYSTEM_PROMPT


def load_formats() -> dict[str, str]:
    return json.loads(FORMATS_PATH.read_text(encoding="utf-8"))["formats"]


def format_value(value, fmt: str) -> str:
    if fmt == "usd_billions":
        return f"{'-' if value < 0 else ''}${abs(value) / 1e9:,.2f} billion"
    if fmt == "usd_millions":
        return f"{'-' if value < 0 else ''}${abs(value) / 1e6:,.0f} million"
    if fmt == "ratio_2dp":
        return f"{value:.2f}"
    if fmt == "percent_1dp":
        return f"{value * 100:.1f}%"
    if fmt == "count":
        return f"{int(value)}"
    if fmt == "per_share_usd":
        return f"{'-' if value < 0 else ''}${abs(value):.2f}"
    if fmt == "years":
        return ", ".join(str(int(y)) for y in value) if value else "none"
    raise ValueError(f"unknown figure format {fmt!r}")


def figure_values(result: CriterionResult) -> dict:
    """The criterion's figures plus derived counts for year lists, so a sentence can say "0 loss years" without printing an empty list."""
    vals = dict(result.figures)
    n = vals.get("years_on_record")
    if result.id == "G3" and n is not None:
        vals["loss_year_count"] = len(vals.get("loss_years") or [])
        vals["profit_year_count"] = n - vals["loss_year_count"]
    if result.id == "G4" and n is not None:
        vals["unpaid_year_count"] = len(vals.get("unpaid_years") or [])
        vals["paid_year_count"] = n - vals["unpaid_year_count"] - len(vals.get("unknown_years") or [])
    if result.id == "B4" and "years_with_depreciation_only" in vals:
        vals["depreciation_only_year_count"] = len(vals["years_with_depreciation_only"] or [])
    return vals


def offered(key: str, result: CriterionResult) -> bool:
    """Whether the model is told about a key. Derived counts are offered only under prompt v2 (v1 requests must stay as recorded)."""
    return key in result.figures or active_prompt("explainer") == "v2"


def usable_keys(result: CriterionResult) -> list[str]:
    """Placeholder keys a sentence may use: present, not None, and with a format."""
    formats = load_formats()
    return [k for k, v in figure_values(result).items() if v is not None and k in formats]


def render(raw: str, result: CriterionResult, formats: dict[str, str] | None = None) -> str:
    """Fill {placeholders}. An invalid placeholder is left as written so the Critic can flag it."""
    formats = formats or load_formats()

    def fill(m: re.Match) -> str:
        key = m.group(1)
        if key == "threshold":
            return result.threshold
        v = figure_values(result).get(key)
        if v is None or key not in formats:
            return m.group(0)
        return format_value(v, formats[key])

    return PLACEHOLDER.sub(fill, raw)


def templated_line(result: CriterionResult) -> str:
    reason = (result.reason or "no reason recorded").rstrip(".")
    return f"Not applicable to this company: {reason}." if result.label == "not_applicable" else f"Cannot be scored: {reason}."


def _context(r: CriterionResult) -> dict:
    formats = load_formats()
    return {"criterion": r.id, "name": r.name, "result": r.label, "threshold": r.threshold,
            "placeholders": {k: format_value(figure_values(r)[k], formats[k]) for k in usable_keys(r) if offered(k, r)},
            "fiscal_years_you_may_write": r.years, "year_label": r.year_label, "reason": r.reason, "flags": r.flags}


def explain(scoreset: ScoreSet, llm, trace: TraceRecorder, *, only: set[str] | None = None,
            feedback: dict[str, str] | None = None) -> Explanations:
    """Explanations in ScoreSet order. `only` limits it to those criterion ids (a Critic-routed retry), `feedback` maps an id to the
    Critic's message about the previous attempt."""
    formats = load_formats()
    todo = [r for r in scoreset.results if (only is None or r.id in only)]
    asking = [r for r in todo if r.label in LLM_LABELS]
    items: dict[str, Explanation] = {r.id: Explanation(criterion=r.id, raw=(t := templated_line(r)), text=t, templated=True)
                                     for r in todo if r.label not in LLM_LABELS}
    start, usage = len(llm.calls), Usage()
    if asking:
        payload = [_context(r) for r in asking]
        notes = {r.id: feedback[r.id] for r in asking if feedback and r.id in feedback}
        user = "Criteria to explain:\n" + json.dumps(payload, indent=1, ensure_ascii=False)
        if notes:
            user += "\n\nA reviewer rejected your previous text for these criteria; write them again so the problem is fixed:\n" + json.dumps(notes, indent=1)
        out = llm.complete_json([{"role": "system", "content": system_prompt()}, {"role": "user", "content": user}], _Out,
                                agent="explainer", company=scoreset.ticker, temperature=0.0)
        by_id = {i.criterion: i.text.strip() for i in out.explanations}
        for r in asking:
            if r.id in by_id:
                raw = by_id[r.id]
                items[r.id] = Explanation(criterion=r.id, raw=raw, text=render(raw, r, formats),
                                          placeholders_used=list(dict.fromkeys(PLACEHOLDER.findall(raw))))
    calls = llm.calls[start:]
    for c in calls:
        usage = Usage(prompt_tokens=usage.prompt_tokens + c.usage.prompt_tokens, completion_tokens=usage.completion_tokens + c.usage.completion_tokens,
                      total_tokens=usage.total_tokens + c.usage.total_tokens, reasoning_tokens=usage.reasoning_tokens + c.usage.reasoning_tokens)
    ordered = [items[r.id] for r in todo if r.id in items]
    trace.note("explainer", f"explained {len(ordered)} of {len(todo)} criteria ({len(asking)} by the model, {len(todo) - len(asking)} templated); {len(calls)} model calls")
    return Explanations(cik=scoreset.cik, ticker=scoreset.ticker, items=ordered, llm_calls=len(calls), usage=usage,
                        actual_cost_usd=sum(c.actual_cost_usd for c in calls), notional_cost_usd=sum(c.notional_cost_usd for c in calls))
