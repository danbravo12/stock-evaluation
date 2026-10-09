"""Critic (ADR-010, ADR-019, ADR-049): rule checks first, then one model call per company. It gates; it never authors.

R1  explanations: every criterion has one; placeholders valid for that criterion; no stray numerals; text reproducible from the ScoreSet.
R2  citations: the 10-K is reloaded from the store and re-converted here; the document's sha256 must match the section record, then
    text[start:end] == quote, the span lies inside the cited passage and inside a found section of the stated item. (Deliberately does
    not import the qualitative agent's pointer checker.)
R3  banned advice/valuation language in explanations and rationales (config/banned_phrases.json).
L1  for found/weak findings with citations: do the quotes support the claimed verdict? Sees only the criterion, the rubric line for the
    claimed verdict and the one below it, the quotes and the rationale.

Checks are pure functions so faults can be injected in tests. `Critic` wires them to a filing and a model client.
"""
from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field

from engine.agents.explainer import PLACEHOLDER, load_formats, render, templated_line, usable_keys
from engine.contracts import CheckResult, CriterionResult, Explanation, Explanations, Passage, QualFinding, ScoreSet, Usage, FilingSection
from engine.filing_text import html_to_text
from engine.settings import REPO_ROOT
from engine.trace import TraceRecorder

BANNED_PATH = REPO_ROOT / "config" / "banned_phrases.json"
SEARCH_TERMS_PATH = REPO_ROOT / "config" / "search_terms.json"
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

SYSTEM_PROMPT = """You are a strict reviewer with two jobs. Judge only from what you are shown; use no outside knowledge.

Job 1, findings. For each finding you see a criterion, the definitions of the verdict that was claimed and of the one below it, the quoted sentences from \
a company's 10-K, and a rationale. Return, in "checks":
- supports_verdict: "yes" if the quotes show what the claimed verdict's definition requires; "overstated" if the quotes only support the lower verdict (for example they assert something without the specifics the claimed definition needs); "no" if the quotes do not bear on the criterion or support neither.
- unsupported_claims: claims in the rationale (figures, facts, policies, causes) that the quotes do not contain. Ignore the standard remark that a 10-K is a limited guide to candour. Empty list if none.
- reason: at most 30 words.

Job 2, explanations. For each explanation you see a scorecard criterion, its result word, and a plain-English sentence or two written for it. Result words: \
pass = the test was met; partial_pass = the test was met on the shorter record that exists (it must not sound like a failure); fail = the test was not met; \
not_meaningful = the test cannot be interpreted. Return, in "explanation_checks":
- agrees_with_label: "yes" if the text is consistent with the result word, "no" if it contradicts it or suggests another result.
- reads_correctly: "yes" if the wording is correct, "no" if it uses a wrong term (for example "first-year average" for a 3-year average), has broken grammar, or says something the criterion does not mean.
- reason: at most 30 words.
Reply with only a JSON object: {"checks": [{"criterion": "<name>", "supports_verdict": "...", "unsupported_claims": [], "reason": "..."}], \
"explanation_checks": [{"criterion": "<id>", "agrees_with_label": "yes", "reads_correctly": "yes", "reason": "..."}]}. Use empty lists for a job with nothing to review."""


class FindingCheck(BaseModel):
    criterion: str
    supports_verdict: Literal["yes", "overstated", "no"]
    unsupported_claims: list[str] = Field(default_factory=list)
    reason: str = ""


class ExplanationCheck(BaseModel):
    criterion: str
    agrees_with_label: Literal["yes", "no"]
    reads_correctly: Literal["yes", "no"]
    reason: str = ""


class CriticVerdicts(BaseModel):
    checks: list[FindingCheck] = Field(default_factory=list)
    explanation_checks: list[ExplanationCheck] = Field(default_factory=list)


def load_banned() -> dict:
    return json.loads(BANNED_PATH.read_text(encoding="utf-8"))


def load_rubric() -> dict:
    return json.loads(SEARCH_TERMS_PATH.read_text(encoding="utf-8"))["criteria"]


# ---------- pure rule checks: each returns a list of problems (empty = pass) ----------
def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in NUMBER.findall(text)}


def check_explanation(result: CriterionResult, expl: Explanation | None, formats: dict[str, str] | None = None) -> list[str]:
    """R1 for one criterion."""
    if expl is None:
        return ["no explanation"]
    if expl.templated:
        return [] if expl.text == expl.raw == templated_line(result) else ["templated line differs from the one built from the result's reason"]
    problems = []
    if result.label in ("not_applicable", "data_gap"):
        problems.append("a not_applicable/data_gap result must use the templated line")
    valid = set(usable_keys(result)) | {"threshold"}
    used = list(dict.fromkeys(PLACEHOLDER.findall(expl.raw)))
    bad = [k for k in used if k not in valid]
    if bad:
        problems.append(f"invalid placeholder(s) for {result.id}: {', '.join('{' + k + '}' for k in bad)} (valid: {', '.join(sorted(valid))})")
    if sorted(used) != sorted(expl.placeholders_used):
        problems.append("placeholders_used does not match the placeholders in the text")
    allowed = {str(y) for y in result.years} | _numbers(result.threshold)
    stray = sorted(n for n in _numbers(PLACEHOLDER.sub(" ", expl.raw)) if n not in allowed)
    if stray:
        problems.append(f"stray numeral(s) not from a placeholder, a fiscal year of this result or its threshold: {', '.join(stray)}")
    if render(expl.raw, result, formats) != expl.text:
        problems.append("text is not what rendering the raw text from the ScoreSet gives")
    return problems


def check_citations(finding: QualFinding, text: str, doc_sha256: str, accession: str, sections: dict[str, FilingSection],
                    passages: dict[str, Passage]) -> list[str]:
    """R2 for one finding. `text` is the 10-K converted again from the stored document; `doc_sha256` is that document's hash."""
    problems = []
    for i, c in enumerate(finding.citations, start=1):
        tag = f"citation {i} ({c.passage_id})"
        sec = sections.get(c.item)
        if c.accession != accession:
            problems.append(f"{tag}: accession {c.accession} is not the filing's {accession}")
        if sec is None or sec.status != "found":
            problems.append(f"{tag}: Item {c.item} is not a found section")
        else:
            if sec.sha256 != doc_sha256:
                problems.append(f"{tag}: the document's sha256 does not match the section record")
            if not (sec.char_start <= c.char_start < c.char_end <= sec.char_end):
                problems.append(f"{tag}: span {c.char_start}-{c.char_end} lies outside Item {c.item} ({sec.char_start}-{sec.char_end})")
        p = passages.get(c.passage_id)
        if p is None:
            problems.append(f"{tag}: unknown passage")
        else:
            if p.item != c.item:
                problems.append(f"{tag}: passage is in Item {p.item}, not Item {c.item}")
            if not (p.char_start <= c.char_start < c.char_end <= p.char_end):
                problems.append(f"{tag}: span {c.char_start}-{c.char_end} lies outside the passage ({p.char_start}-{p.char_end})")
        if text[c.char_start:c.char_end] != c.quote:
            problems.append(f"{tag}: the quote is not the document text at {c.char_start}-{c.char_end}")
    return problems


def banned_hits(text: str, banned: dict | None = None) -> list[str]:
    """R3: descriptions of banned phrases found in `text`."""
    banned = banned or load_banned()
    clean = text
    for pat in banned["allow"]:
        clean = re.sub(pat, lambda m: " " * len(m.group(0)), clean, flags=re.I)
    hits = []
    for ph in banned["phrases"]:
        m = re.search(ph["pattern"], clean, flags=re.I)
        if m:
            hits.append(f"'{m.group(0).strip()}' ({ph['reason']})")
    return hits


# ---------- the model check ----------
def rubric_lines(criterion: str, verdict: str, rubric: dict) -> tuple[str, str]:
    spec = rubric[criterion]
    return (spec["found_means"], spec["weak_means"]) if verdict == "evidence found" else (spec["weak_means"], spec["insufficient_means"])


def llm_payload(findings: list[QualFinding], rubric: dict) -> list[dict]:
    out = []
    for f in findings:
        claimed, below = rubric_lines(f.criterion, f.verdict, rubric)
        out.append({"criterion": f.criterion, "question": rubric[f.criterion]["question"], "claimed_verdict": f.verdict,
                    "definition_of_claimed_verdict": claimed, "definition_of_the_verdict_below": below,
                    "quotes": [c.quote for c in f.citations], "rationale": f.rationale})
    return out


def explanation_payload(items: list[tuple[CriterionResult, Explanation]]) -> list[dict]:
    return [{"criterion": r.id, "name": r.name, "result": r.label, "year_label": r.year_label, "threshold": r.threshold, "text": e.text} for r, e in items]


def llm_review(findings: list[QualFinding], explanations: list[tuple[CriterionResult, Explanation]], llm, ticker: str,
               rubric: dict | None = None) -> CriticVerdicts:
    """The Critic's one model call per company: found/weak findings and the written explanations together."""
    rubric = rubric or load_rubric()
    body = {"findings": llm_payload(findings, rubric), "explanations": explanation_payload(explanations)}
    return llm.complete_json([{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": "To review:\n" + json.dumps(body, indent=1, ensure_ascii=False)}],
                             CriticVerdicts, agent="critic", company=ticker, temperature=0.0)


def llm_check(findings: list[QualFinding], llm, ticker: str, rubric: dict | None = None) -> list[FindingCheck]:
    """Findings only (used for fault injection)."""
    return llm_review(findings, [], llm, ticker, rubric).checks


def explanation_failed(c: ExplanationCheck) -> bool:
    return c.agrees_with_label != "yes" or c.reads_correctly != "yes"


def explanation_detail(c: ExplanationCheck) -> str:
    return f"agrees_with_label={c.agrees_with_label}; reads_correctly={c.reads_correctly}; {c.reason}"


def llm_failed(c: FindingCheck) -> bool:
    return c.supports_verdict != "yes" or bool(c.unsupported_claims)


def llm_detail(c: FindingCheck) -> str:
    claims = ("; unsupported: " + " | ".join(c.unsupported_claims)) if c.unsupported_claims else ""
    return f"supports_verdict={c.supports_verdict}{claims}; {c.reason}"


def needs_llm_check(f: QualFinding) -> bool:
    return f.stop_reason == "submitted" and f.verdict in ("evidence found", "evidence weak") and bool(f.citations)


class Critic:
    """Runs the checks for one company against its filing. `retriever.client` is the EdgarClient (store); `llm` the model client."""

    def __init__(self, retriever, llm, trace: TraceRecorder, *, banned: dict | None = None, rubric: dict | None = None):
        self.retriever, self.llm, self.trace = retriever, llm, trace
        self.banned, self.rubric = banned or load_banned(), rubric or load_rubric()

    def _filing(self, cik: str):
        ref = self.retriever.client.latest_filing(cik, "10-K")
        doc = self.retriever.client.filing_document(ref)  # the store verifies the stored checksum
        idx = self.retriever.index(cik)
        return ref.accession, doc.sha256, html_to_text(doc.body.decode("utf-8", errors="replace")), idx

    def _log(self, check: str, attempt: int, results: list[CheckResult], extra: str = "") -> None:
        failed = [r for r in results if r.status == "fail"]
        self.trace.tool_call("critic", f"check_{check}", {"attempt": attempt, "items": len(results)},
                             f"{len(results) - len(failed)} passed, {len(failed)} failed" + (": " + " | ".join(f"{r.item}: {r.detail}" for r in failed) if failed else "") + extra)

    def check(self, scoreset: ScoreSet, expl: Explanations, findings: list[QualFinding], *, attempt: int,
              only_explanations: set[str] | None = None, only_qual: set[str] | None = None) -> list[CheckResult]:
        """All checks for the selected items (None = all). Returns one CheckResult per (check, item)."""
        formats = load_formats()
        by_expl = {e.criterion: e for e in expl.items}
        results: list[CheckResult] = []
        # R1 and R3 on explanations
        r1, r3e = [], []
        for r in scoreset.results:
            if only_explanations is not None and r.id not in only_explanations:
                continue
            probs = check_explanation(r, by_expl.get(r.id), formats)
            r1.append(CheckResult(check="R1", item=r.id, status="fail" if probs else "pass", detail="; ".join(probs), owner="explainer", attempt=attempt))
            hits = banned_hits(by_expl[r.id].text, self.banned) if r.id in by_expl else []
            r3e.append(CheckResult(check="R3", item=r.id, status="fail" if hits else "pass", detail="banned language: " + "; ".join(hits) if hits else "", owner="explainer", attempt=attempt))
        # R2 and R3 on findings
        todo = [f for f in findings if only_qual is None or f.criterion in only_qual]
        r2, r3q = [], []
        if any(f.citations for f in todo):
            accession, sha, text, idx = self._filing(scoreset.cik)
            passages = idx.by_id
            for f in todo:
                probs = check_citations(f, text, sha, accession, idx.sections, passages)
                r2.append(CheckResult(check="R2", item=f.criterion, status="fail" if probs else "pass", detail="; ".join(probs), owner="qualitative", attempt=attempt, kind="citation" if probs else None))
        else:
            r2 = [CheckResult(check="R2", item=f.criterion, status="pass", detail="no citations to check", owner="qualitative", attempt=attempt) for f in todo]
        for f in todo:
            hits = banned_hits(f.rationale, self.banned)
            r3q.append(CheckResult(check="R3", item=f.criterion, status="fail" if hits else "pass", detail="banned language in rationale: " + "; ".join(hits) if hits else "", owner="qualitative", attempt=attempt, kind="rationale" if hits else None))
        self._log("R1", attempt, r1)
        self._log("R2", attempt, r2)
        self._log("R3", attempt, r3e + r3q)
        results += r1 + r2 + r3e + r3q
        # L1: one model call for the found/weak findings with citations and the written explanations
        l1 = []
        judged = [f for f in todo if needs_llm_check(f)]
        reviewed = [(r, by_expl[r.id]) for r in scoreset.results
                    if r.id in by_expl and not by_expl[r.id].templated and (only_explanations is None or r.id in only_explanations)]
        if judged or reviewed:
            out = llm_review(judged, reviewed, self.llm, scoreset.ticker, self.rubric)
            verdicts = {c.criterion: c for c in out.checks}
            ex_checks = {c.criterion: c for c in out.explanation_checks}
            for f in judged:
                c = verdicts.get(f.criterion)
                if c is None:
                    l1.append(CheckResult(check="L1", item=f.criterion, status="pass", detail="the model returned no judgement for this finding (not checked)", owner="qualitative", attempt=attempt))
                else:
                    failed_ = llm_failed(c)
                    l1.append(CheckResult(check="L1", item=f.criterion, status="fail" if failed_ else "pass", detail=llm_detail(c), owner="qualitative", attempt=attempt,
                                          kind=("verdict" if c.supports_verdict != "yes" else "rationale") if failed_ else None, claims=list(c.unsupported_claims)))
            for r, _ in reviewed:
                c = ex_checks.get(r.id)
                if c is None:
                    l1.append(CheckResult(check="L1", item=r.id, status="pass", detail="the model returned no judgement for this explanation (not checked)", owner="explainer", attempt=attempt))
                else:
                    l1.append(CheckResult(check="L1", item=r.id, status="fail" if explanation_failed(c) else "pass", detail=explanation_detail(c), owner="explainer", attempt=attempt))
        self._log("L1", attempt, l1, "" if (judged or reviewed) else " (nothing to judge)")
        return results + l1
