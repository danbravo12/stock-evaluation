"""Rationale rewrite (ADR-052): the cheap repair for a finding whose verdict stands but whose rationale says more than its quotes.

One model call that sees only the criterion's question, the verdict, the cited quotes and what to remove. The verdict and the
citations are not touched. The Critic re-checks the result; if it still fails the original finding is kept with a warning.
"""
from __future__ import annotations

from pydantic import BaseModel

from engine.agents.qualitative import MAX_RATIONALE_WORDS
from engine.contracts import QualFinding
from engine.trace import TraceRecorder

import json

SYSTEM_PROMPT = """You rewrite the rationale of one finding about a company's 10-K. You are given the question, the verdict, the quoted sentences that \
support it, and the problems with the old rationale (claims the quotes do not show, or banned wording). Write a new rationale of at most two sentences \
(under 80 words) that states only what the quotes show and is consistent with the verdict. Add no claim, figure, name or policy that is not in the quotes. \
Use no buy, sell or hold language and do not mention a reviewer.
Reply with only a JSON object: {"rationale": "<new rationale>"}"""


class _Rewrite(BaseModel):
    rationale: str


def rewrite_rationale(finding: QualFinding, question: str, problems: list[str], llm, trace: TraceRecorder, ticker: str) -> str | None:
    """The new rationale, or None if the model's answer is empty or too long."""
    payload = {"question": question, "verdict": finding.verdict, "quotes": [c.quote for c in finding.citations], "problems_with_the_old_rationale": problems}
    out = llm.complete_json([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(payload, indent=1, ensure_ascii=False)}],
                            _Rewrite, agent=f"qualitative/{finding.criterion}/rewrite", company=ticker, temperature=0.0)
    text = out.rationale.strip()
    if not text or len(text.split()) > MAX_RATIONALE_WORDS:
        trace.note(f"qualitative/{finding.criterion}/rewrite", "rewrite rejected: empty or over 80 words")
        return None
    return text
