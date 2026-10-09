"""Buffett qualitative agent (ADR-018, ADR-041 to ADR-045).

One independent tool-using loop per criterion over the company's latest 10-K:

    plan (criterion + seeded queries) -> seeded search (code) -> model turns (search / get_passage) ->
    submit_finding -> citation self-check (code) -> finding

Every verdict except "insufficient evidence" quotes and cites a passage. A quote is accepted only if it appears
(whitespace aside) in a passage this loop retrieved, and its exact offsets in the normalised document text are
computed and round-trip checked here; the Critic re-checks independently later (ADR-042). Quota and budget errors
propagate so the batch stops and resumes from the ledger (ADR-044).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from engine.contracts import (QUAL_CRITERIA, Citation, LLMCall, Passage, QualFinding, QualFindings, QualTotals, SearchHit,
                              SearchRecord, Usage)
from engine.retrieve import FilingIndex, Retriever
from engine.settings import REPO_ROOT
from engine.trace import TraceRecorder
from engine.universe import cik10


SEARCH_TERMS_PATH = REPO_ROOT / "config" / "search_terms.json"
SEED_K = 4  # passages in the seeded search and in every model-requested search
MAX_QUOTE_WORDS = 60
SHORT_QUOTE_WORDS = 40  # what the prompt asks for and what a rejection suggests
MAX_RATIONALE_WORDS = 80  # proxy for "two sentences"
ITEMS = ("1", "1A", "7")
VERDICTS = ("evidence found", "evidence weak", "insufficient evidence")

# Fixed on purpose: the request hash (record/replay) depends on it. Criterion-specific text goes in the first user message.
SYSTEM_PROMPT = """You are a research assistant that reads one company's latest Form 10-K and answers ONE qualitative question about it. \
You are a research tool, not an adviser: never use buy, sell or hold language, price targets, or phrases such as "investors should". \
Describe only what the filing shows.

Rules:
- Judge only the filing text you are shown. Use no outside knowledge of the company.
- The company's own marketing language ("leading", "world-class", "trusted brand") is a claim, not evidence. Evidence is concrete: figures, named products, segments or actions, admitted setbacks.
- Tools: search (find passages), get_passage (read one passage in full), submit_finding (finish). Call submit_finding exactly once when you can decide.
- Cite with quotes. Each quote must be copied exactly from a passage you were shown: one contiguous stretch of its text, character for character. Never join sentences that are not next to each other, add or drop punctuation, use ellipses or reword. Choose the one or two sentences that matter and keep each quote to about 40 words; more than 60 words is rejected, as is any quote that cannot be found in those passages.
- verdict is one of "evidence found", "evidence weak", "insufficient evidence". Unless the verdict is "insufficient evidence", give 1 or 2 citations.
- rationale: at most two sentences, about what the filing shows.
- If the passages shown do not settle the question, you may search again, but prefer "insufficient evidence" to guessing."""

TOOLS = [
    {"type": "function", "function": {
        "name": "search",
        "description": "Keyword search of the company's 10-K. Returns the top 4 passages with their ids.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Words to look for, e.g. 'share repurchases dividends'."},
            "items": {"type": "array", "items": {"type": "string", "enum": list(ITEMS)},
                      "description": "Optional: restrict to 10-K items (1 Business, 1A Risk Factors, 7 MD&A)."}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_passage",
        "description": "Return the full text of one passage of this company's 10-K by its id.",
        "parameters": {"type": "object", "properties": {"passage_id": {"type": "string"}}, "required": ["passage_id"]}}},
    {"type": "function", "function": {
        "name": "submit_finding",
        "description": "Finish: give the verdict, a short rationale and verbatim quotes from passages you were shown.",
        "parameters": {"type": "object", "properties": {
            "verdict": {"type": "string", "enum": list(VERDICTS)},
            "rationale": {"type": "string", "description": "At most two sentences, about what the filing shows."},
            "citations": {"type": "array", "maxItems": 2, "items": {"type": "object", "properties": {
                "passage_id": {"type": "string"},
                "quote": {"type": "string", "description": "Exact text from that passage; about 40 words, never more than 60."}},
                "required": ["passage_id", "quote"]}}},
            "required": ["verdict", "rationale", "citations"]}}},
]
SUBMIT_ONLY = [TOOLS[2]]


def load_criteria() -> dict:
    return json.loads(SEARCH_TERMS_PATH.read_text(encoding="utf-8"))["criteria"]


# ---------- quote checking (pure functions) ----------
def _collapse(text: str) -> tuple[str, list[int]]:
    """Whitespace runs -> one space, ends stripped; plus, for each output character, its index in `text`."""
    out, where, prev_space = [], [], True
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                where.append(i)
                prev_space = True
        else:
            out.append(ch)
            where.append(i)
            prev_space = False
    if out and out[-1] == " ":
        out.pop()
        where.pop()
    return "".join(out), where


def locate_quote(quote: str, passage: Passage, document: str) -> tuple[int, int] | None:
    """Offsets (start, end) of `quote` in `document` inside `passage`, comparing after collapsing whitespace only.

    The match must start and end on a word edge (no quoting half a word) and `document[start:end]` must
    round-trip to the quote once whitespace is collapsed. None when the quote is not in the passage.
    """
    q = " ".join(quote.split())
    if not q:
        return None
    hay, where = _collapse(passage.text)
    pos = hay.find(q)
    while pos != -1:
        end = pos + len(q)
        edge_ok = (not (q[0].isalnum() and pos > 0 and hay[pos - 1].isalnum())
                   and not (q[-1].isalnum() and end < len(hay) and hay[end].isalnum()))
        if edge_ok:
            start, stop = passage.char_start + where[pos], passage.char_start + where[end - 1] + 1
            if " ".join(document[start:stop].split()) == q:
                return start, stop
        pos = hay.find(q, pos + 1)
    return None


def _diagnose(words: list[str], retrieved: dict[str, Passage], document: str) -> str:
    """Why a quote was not found: its longest leading run of words that does occur in a retrieved passage (a ready, verified
    quote the model can resubmit), and what the text says next."""
    for n in range(min(len(words) - 1, MAX_QUOTE_WORDS), 3, -1):
        for p in retrieved.values():
            span = locate_quote(" ".join(words[:n]), p, document)
            if span:
                nxt = document[span[1]:p.char_end].split()[:8]
                return (f"; the longest part of it that is in the text is \"{' '.join(document[span[0]:span[1]].split())}\" (passage {p.passage_id}), "
                        f"which you may submit as your quote; the text then continues \"{' '.join(nxt)}\", not as you wrote it")
    return ""


def check_citations(raw: list[dict], retrieved: dict[str, Passage], document: str) -> tuple[list[Citation], list[str]]:
    """Verify each {passage_id, quote} against the passages retrieved in this loop.

    Returns (verified citations, one problem string per rejected quote). The cited passage is tried first; if the quote
    is in another retrieved passage the citation is attributed to that one, so the passage_id always points at the true location.
    A rejection says what to change: a quote over the word limit comes with a ready, shorter contiguous quote from the same
    passage; a quote that is not found says where it first departs from the text.
    """
    ok, problems = [], []
    for c in raw:
        quote = str(c.get("quote", ""))
        pid = str(c.get("passage_id", ""))
        words = quote.split()
        shown = f'"{" ".join(words)[:100]}"'
        if not words:
            problems.append(f"{shown}: empty quote")
            continue
        order = ([retrieved[pid]] if pid in retrieved else []) + [p for k, p in retrieved.items() if k != pid]
        hit = next(((p, span) for p in order if (span := locate_quote(quote, p, document))), None)
        if hit and len(words) > MAX_QUOTE_WORDS:
            shorter = " ".join(words[:SHORT_QUOTE_WORDS])
            problems.append(f"{shown}: {len(words)} words; the limit is {MAX_QUOTE_WORDS}. The text is in passage {hit[0].passage_id}; quote a shorter "
                            f"contiguous part, for example \"{shorter}\"")
        elif hit:
            p, (a, b) = hit
            ok.append(Citation(passage_id=p.passage_id, accession=p.accession, item=p.item, char_start=a, char_end=b, quote=document[a:b]))
        else:
            note = "" if pid in retrieved else f" (passage {pid!r} was not retrieved in this session)"
            over = f"; also {len(words)} words, over the limit of {MAX_QUOTE_WORDS}" if len(words) > MAX_QUOTE_WORDS else ""
            problems.append(f"{shown}: not found in any passage you were shown{note}{over}{_diagnose(words, retrieved, document)}")
    return ok, problems


class _BadArgs(Exception):
    """Malformed tool arguments: becomes a corrective tool message."""


@dataclass
class _Run:
    """Mutable state of one criterion's loop."""

    calls: list[LLMCall] = field(default_factory=list)
    searches: list[SearchRecord] = field(default_factory=list)
    retrieved: dict[str, Passage] = field(default_factory=dict)
    tool_calls: int = 0
    malformed: int = 0
    rejected: int = 0
    stop: str | None = None
    verdict: str | None = None
    rationale: str = ""
    citations: list[Citation] = field(default_factory=list)


class _CriterionLoop:
    def __init__(self, name: str, spec: dict, cik: str, ticker: str, retriever: Retriever, idx: FilingIndex, accession: str,
                 llm, trace: TraceRecorder, max_turns: int):
        self.name, self.spec, self.cik, self.ticker = name, spec, cik, ticker
        self.retriever, self.idx, self.accession, self.llm, self.trace = retriever, idx, accession, llm, trace
        self.max_turns, self.agent = max_turns, f"qualitative/{name}"
        self.run = _Run()

    # ---------- result ----------
    def _finding(self, verdict: str, rationale: str, citations: list[Citation], stop_reason: str) -> QualFinding:
        usage = Usage()
        for c in self.run.calls:
            usage = Usage(prompt_tokens=usage.prompt_tokens + c.usage.prompt_tokens, completion_tokens=usage.completion_tokens + c.usage.completion_tokens,
                          total_tokens=usage.total_tokens + c.usage.total_tokens, reasoning_tokens=usage.reasoning_tokens + c.usage.reasoning_tokens)
        self.trace.note(self.agent, f"stop: {stop_reason}; verdict: {verdict}; {len(self.run.calls)} model calls, {self.run.tool_calls} tool calls")
        return QualFinding(criterion=self.name, verdict=verdict, rationale=rationale, citations=citations, searches=self.run.searches,
                           llm_calls=len(self.run.calls), tool_calls=self.run.tool_calls, stop_reason=stop_reason, usage=usage,
                           actual_cost_usd=sum(c.actual_cost_usd for c in self.run.calls), notional_cost_usd=sum(c.notional_cost_usd for c in self.run.calls))

    def _insufficient(self, rationale: str, stop_reason: str) -> QualFinding:
        return self._finding("insufficient evidence", rationale, [], stop_reason)

    # ---------- the loop ----------
    def execute(self) -> QualFinding:
        spec = self.spec
        self.trace.note(self.agent, f"plan: {self.name}; items {spec['items']}; seeded queries {spec['queries']}")
        missing = {i: s.reason for i, s in self.idx.sections.items() if i in spec["items"] and s.status != "found"}
        if len(missing) == len(spec["items"]):
            reason = "; ".join(f"Item {i} not found in the filing ({r})" for i, r in missing.items())
            self.trace.note(self.agent, f"section_missing: {reason}; no model call")
            return self._insufficient(f"{reason}.", "section_missing")

        hits = self.retriever.search_many(self.cik, spec["queries"], spec["items"], k=SEED_K)
        self._remember(hits)
        self.run.searches.append(SearchRecord(queries=list(spec["queries"]), items=list(spec["items"]), seeded=True, passage_ids=[h.passage_id for h in hits]))
        self.run.tool_calls += 1
        self.trace.tool_call(self.agent, "search_many", {"queries": spec["queries"], "items": spec["items"], "k": SEED_K, "seeded": True},
                             "seeded search (decided in code, before the first model call): " + self._hit_summary(hits))

        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": self._first_message(hits, missing)}]
        limit, notes, extended = self.max_turns, [], False
        turn = 0
        while turn < limit:
            turn += 1
            last = turn == limit
            if last:
                notes.append(f"This is your last turn (turn {turn} of {limit}). Only submit_finding is available now: submit your finding from the "
                             "passages you have seen, with verdict \"insufficient evidence\" if they do not settle the question.")
            if notes:
                messages.append({"role": "user", "content": " ".join(notes)})
                notes = []
            call = self.llm.chat(messages, tools=SUBMIT_ONLY if last else TOOLS, temperature=0.0, company=self.ticker, agent=self.agent)
            self.run.calls.append(call)
            messages.append(call.message)  # unchanged: Gemini thought signatures live in extra_content
            if not call.tool_calls:
                notes.append("Use a tool: call search, get_passage or submit_finding.")
                continue
            for tc in call.tool_calls:
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": self._tool(tc, last)})
                if self.run.stop:
                    break
            if self.run.stop:
                break
            if self.run.rejected == 1 and turn == limit and not extended:
                limit, extended = limit + 1, True  # the one corrected submission may exceed the turn cap by one

        r = self.run
        if r.stop == "submitted":
            return self._finding(r.verdict, r.rationale, r.citations, "submitted")
        if r.stop == "invalid_citation":
            return self._insufficient("The quotes in the submitted finding could not be verified against the retrieved passages, so no finding is recorded.", "invalid_citation")
        if r.stop == "llm_output_error":
            return self._insufficient("The model's tool arguments were malformed twice, so no finding is recorded.", "llm_output_error")
        return self._insufficient(f"No finding was submitted within {limit} turns.", "turn_cap")

    # ---------- messages ----------
    def _first_message(self, hits: list[SearchHit], missing: dict) -> str:
        s = self.spec
        lines = [f"Company: {self.ticker}. Filing: Form 10-K, accession {self.accession}.",
                 f"Criterion: {self.name}", f"Question: {s['question']}",
                 f"\"evidence found\" means: {s['found_means']}", f"\"evidence weak\" means: {s['weak_means']}",
                 f"\"insufficient evidence\" means: {s['insufficient_means']}",
                 "The company's own promotional language is a claim, not evidence; \"evidence found\" needs concrete specifics in the filing.",
                 f"You have up to {self.max_turns} turns, including this one."]
        if missing:
            lines.append("Not available in this filing: " + "; ".join(f"Item {i} ({r})" for i, r in missing.items()) + ".")
        lines.append(f"\nA starting search of Item(s) {', '.join(s['items'])} has already been run for you ({len(hits)} passages). Use search for more.\n")
        lines += [f"[{h.passage_id}] Item {h.item}\n{h.text}\n" for h in hits] or ["(The starting search matched no passages.)"]
        return "\n".join(lines)

    @staticmethod
    def _hit_summary(hits: list[SearchHit]) -> str:
        return f"{len(hits)} hits: " + ", ".join(f"{h.passage_id} (item {h.item}, score {h.score})" for h in hits) if hits else "no hits"

    def _remember(self, hits: list[SearchHit]) -> None:
        for h in hits:
            self.run.retrieved[h.passage_id] = self.idx.by_id[h.passage_id]

    # ---------- tools ----------
    def _tool(self, tc, last: bool) -> str:
        self.run.tool_calls += 1
        args = tc.arguments
        try:
            if "_unparsed" in args:
                raise _BadArgs("the arguments were not valid JSON")
            if tc.name == "search" and not last:
                result = self._search(args)
            elif tc.name == "get_passage" and not last:
                result = self._get_passage(args)
            elif tc.name == "submit_finding":
                result = self._submit(args)
            else:
                avail = "submit_finding" if last else "search, get_passage, submit_finding"
                result = f"Tool error: {tc.name!r} is not available now. Available: {avail}."
        except _BadArgs as e:
            self.run.malformed += 1
            result = f"Tool error: malformed arguments for {tc.name}: {e}. Call it again with arguments matching its schema."
            if self.run.malformed >= 2:
                self.run.stop = "llm_output_error"
        shown = {k: args.get(k) for k in ("verdict", "rationale")} if tc.name == "submit_finding" else args
        self.trace.tool_call(self.agent, tc.name, shown, result)
        return result

    def _search(self, args: dict) -> str:
        query, items = args.get("query"), args.get("items")
        if not isinstance(query, str) or not query.strip():
            raise _BadArgs("'query' must be a non-empty string")
        if items is not None and (not isinstance(items, list) or any(i not in ITEMS for i in items)):
            raise _BadArgs(f"'items' must be a list drawn from {list(ITEMS)}")
        hits = self.retriever.search(self.cik, query, items or None, k=SEED_K)
        self._remember(hits)
        self.run.searches.append(SearchRecord(queries=[query], items=items or None, passage_ids=[h.passage_id for h in hits]))
        if not hits:
            return "No passages matched. Try different words or other items."
        return "\n".join(f"[{h.passage_id}] Item {h.item} (score {h.score})\n{h.text}\n" for h in hits)

    def _get_passage(self, args: dict) -> str:
        pid = args.get("passage_id")
        if not isinstance(pid, str) or not pid:
            raise _BadArgs("'passage_id' must be a string")
        self.retriever.index(self.cik)  # index on first use: works without a prior search
        accession = pid.split(":")[0]
        if accession != self.accession:
            return f"Tool error: passage {pid!r} belongs to a different filing ({accession}); this company's 10-K is {self.accession}."
        p = self.idx.by_id.get(pid)
        if p is None:
            return f"Tool error: unknown passage id {pid!r} in filing {self.accession}. Use ids returned by search."
        self.run.retrieved[pid] = p
        return f"[{p.passage_id}] Item {p.item}\n{p.text}"

    def _submit(self, args: dict) -> str:
        verdict, rationale, raw = args.get("verdict"), args.get("rationale"), args.get("citations")
        if verdict not in VERDICTS:
            raise _BadArgs(f"'verdict' must be one of {list(VERDICTS)}")
        if not isinstance(rationale, str) or not rationale.strip():
            raise _BadArgs("'rationale' must be a non-empty string")
        if len(rationale.split()) > MAX_RATIONALE_WORDS:
            raise _BadArgs(f"'rationale' must be at most two short sentences (under {MAX_RATIONALE_WORDS} words)")
        if not isinstance(raw, list) or any(not isinstance(c, dict) for c in raw):
            raise _BadArgs("'citations' must be a list of {passage_id, quote} objects")
        if len(raw) > 2:
            raise _BadArgs("give at most 2 citations")
        if verdict != "insufficient evidence" and not raw:
            raise _BadArgs(f"verdict {verdict!r} needs 1 or 2 citations")
        citations, problems = check_citations(raw, self.run.retrieved, self.idx.text)
        outcome = ("rejected: " + " | ".join(problems)) if problems else ("verified: " + "; ".join(
            f"{c.passage_id} [{c.char_start}:{c.char_end}] \"{c.quote[:80]}\"" for c in citations) if citations else "no citations to check")
        self.trace.tool_call(self.agent, "citation_check", {"quotes": len(raw)}, outcome)
        if problems and verdict == "insufficient evidence":
            citations = []  # an insufficient verdict does not need quotes: drop the bad ones rather than reject
        elif problems:
            self.run.rejected += 1
            if self.run.rejected >= 2:
                self.run.stop = "invalid_citation"
                self.trace.note(self.agent, "rejected quotes kept: " + " | ".join(problems))
                return "Rejected again; no finding recorded."
            return ("Rejected: " + " | ".join(problems) + ". Resubmitting the same text will fail again. Submit again with each quote copied exactly (one contiguous stretch, at most 60 words) from passages "
                    "you were shown: " + ", ".join(self.run.retrieved) + ".")
        self.run.stop, self.run.verdict, self.run.rationale, self.run.citations = "submitted", verdict, rationale.strip(), citations
        return "Finding accepted."


def assess_qualitative(cik: str | int, ticker: str, retriever: Retriever, llm, trace: TraceRecorder, *, max_turns: int = 4,
                       criteria: dict | None = None) -> QualFindings:
    """Judge the four qualitative Buffett criteria for one company from its latest 10-K.

    `llm` is an LLMClient; give it the same TraceRecorder as `trace` so model calls and tool calls interleave in one trace.
    Raises QuotaReached / BudgetExceeded / LLMFixtureMissing (and other LLMError) unchanged: the caller stops the batch.
    """
    cik = cik10(cik)
    spec = criteria or load_criteria()
    idx = retriever.index(cik)
    accession = next(iter(idx.sections.values())).accession
    findings = [_CriterionLoop(name, spec[name], cik, ticker, retriever, idx, accession, llm, trace, max_turns).execute() for name in QUAL_CRITERIA]
    totals = QualTotals(llm_calls=sum(f.llm_calls for f in findings), tool_calls=sum(f.tool_calls for f in findings),
                        usage=Usage(prompt_tokens=sum(f.usage.prompt_tokens for f in findings), completion_tokens=sum(f.usage.completion_tokens for f in findings),
                                    total_tokens=sum(f.usage.total_tokens for f in findings), reasoning_tokens=sum(f.usage.reasoning_tokens for f in findings)),
                        actual_cost_usd=sum(f.actual_cost_usd for f in findings), notional_cost_usd=sum(f.notional_cost_usd for f in findings))
    return QualFindings(cik=cik, ticker=ticker, accession=accession, findings=findings, totals=totals)
