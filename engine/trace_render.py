"""Plain-language rendering of a recorded run (ADR-067).

`render_trace` turns the trace events of one analysis (`results/<CIK>.trace.jsonl`) into numbered steps with a plain title and detail lines, groups them per agent run,
and marks the real hand-offs between the planner, the scorers, the qualitative agent, the Explainer, the Critic and the Reporter. `critic_notes` writes the Critic's
checks, the agents' work and the cost as sentences for the company page. Nothing here is shown as raw JSON or key=value text; the raw events stay in the results folder.
"""
from __future__ import annotations

import json
import re
from typing import Callable

LANES = [("orchestrator", "Planner and orchestrator"), ("scorers", "Scorers"), ("qualitative", "Qualitative agent"), ("explainer", "Explainer"), ("critic", "Critic"),
         ("reporter", "Reporter")]
CRITERION = {"understandable_business": "understandable business", "durable_competitive_advantage": "durable competitive advantage", "candid_management": "candid management",
             "rational_capital_allocation": "rational capital allocation"}
CHECK = {"R1": "explanation check", "R2": "quote check", "R3": "language check", "L1": "second-model review"}
SENTENCE_CAP = "a citation covered more than three sentences"
STOP = {"submitted": "it submitted a finding", "turn_cap": "it ran out of turns", "invalid_citation": "its citations could not be verified", "section_missing": "the section it needed was not in the filing",
        "llm_output_error": "the model's reply could not be read"}
PASSAGE = re.compile(r"\d{10}-\d{2}-\d{6}:[0-9A-Za-z]+:\d+")


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def money(x: float | None) -> str:
    if x is None:
        return "no cost recorded"
    return "under $0.0001" if 0 < x < 0.0001 else f"${x:.4f}"


def crit_name(crit: str) -> str:
    return CRITERION.get(crit, crit.replace("_", " "))


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def items_text(items: list[str] | None) -> str:
    items = [str(i) for i in (items or [])]
    if not items:
        return "the whole filing"
    return f"Item {items[0]}" if len(items) == 1 else "Items " + ", ".join(items[:-1]) + " and " + items[-1]


def queries_text(qs: list[str], limit: int = 3) -> str:
    shown = ", ".join(f"\"{q}\"" for q in qs[:limit])
    return shown + (", and others" if len(qs) > limit else "")


def short_passage(pid: str) -> str:
    parts = pid.split(":")
    return f"passage {parts[1]}:{parts[2]}" if len(parts) == 3 else pid


def sentences_text(first: int, last: int) -> str:
    return f"sentence {first}" if first == last else f"sentences {first} to {last}"


def snippet(text: str, words: int = 20) -> str:
    text = re.sub(r"^Item \S+\s*", "", re.sub(r"\[\d+\]\s*", "", text)).strip()
    w = text.split()
    return " ".join(w[:words]) + (" …" if len(w) > words else "")


def citations_text(cits: list[dict]) -> str:
    return "; ".join(f"{short_passage(c['passage_id'])} {sentences_text(c['first'], c['last'])}" for c in cits) if cits else "nothing"


def reject_reason(text: str) -> str:
    if "consecutive sentences" in text:
        return SENTENCE_CAP
    m = re.search(r"at most (\d+) citations", text)
    if m:
        return f"it gave more than {m.group(1)} citations"
    if "unknown passage" in text or "never retrieved" in text:
        return "a citation pointed at a passage the agent had not been shown"
    return "the pointers did not match the filing"


def _args(event: dict) -> list[dict]:
    out = event.get("output")
    return [o for o in out if isinstance(o, dict) and "tool" in o] if isinstance(out, list) else []


def _json_in(summary: str) -> dict:
    m = re.search(r"\((\{.*)\)?$", summary or "")
    if not m:
        return {}
    text = m.group(1)
    for end in (text, text.rstrip(")")):
        try:
            return json.loads(end)
        except ValueError:
            continue
    return {}


def _lane(e: dict) -> str:
    a, out = e["agent"], e.get("output")
    if a == "orchestrator":
        if isinstance(out, str) and out.startswith("score:"):
            return "scorers"
        if isinstance(out, str) and out.startswith("report:"):
            return "reporter"
        return "orchestrator"
    return a.split("/")[0]


class Renderer:
    def __init__(self, result: dict | None, retriever=None, cik: str | None = None):
        self.result, self.retriever, self.cik = result or {}, retriever, cik
        self.final_quotes: dict[tuple, str] = {}
        for q in self.result.get("qualitative", []):
            for c in q["finding"].get("citations", []):
                self.final_quotes[(c["passage_id"], tuple(c.get("sentences", [])))] = c["quote"]
        self.checks = (self.result.get("critic") or {}).get("checks", [])
        self.last_args: dict[str, dict] = {}
        self.model_calls: dict[str, int] = {}
        self.repair_phase = False
        self.prev_agent: str | None = None
        self.plans: dict[str, tuple[list[str], list[str]]] = {}

    # ---- retrieval replay (only when a recorded 10-K is available)
    def hits(self, items, queries, many: bool):
        if not (self.retriever and self.cik):
            return None
        try:
            return self.retriever.search_many(self.cik, queries, items or None, k=4) if many else self.retriever.search(self.cik, queries[0], items or None, k=4)
        except Exception:
            return None

    def hit_lines(self, hits, ids_fallback):
        if hits:
            return [f"{cap(short_passage(h.passage_id))}: {snippet(h.text)}" for h in hits]
        return [cap(short_passage(i)) for i in ids_fallback]

    # ---- one event
    def one(self, e: dict) -> dict:
        typ, agent, out, summ = e["type"], e["agent"], e.get("output"), e.get("input_summary") or ""
        lane = _lane(e)
        if agent != self.prev_agent:  # a new loop (a repair is a new loop): model calls are counted again
            self.model_calls[agent] = 0
            self.prev_agent = agent
        s = {"lane": lane, "kind": "unknown", "title": "", "details": [], "quote": None}
        crit = agent.split("/")[1] if agent.startswith("qualitative/") else None
        name = crit_name(crit) if crit else ""
        usage = e.get("usage")
        if usage:
            s["tokens"] = {"in": usage["prompt_tokens"], "out": usage["completion_tokens"]}
        if e.get("latency_s") is not None:
            s["latency_s"] = e["latency_s"]
        if e.get("notional_cost_usd") is not None:
            s["cost_usd"] = e["notional_cost_usd"]
        if e.get("replayed"):
            s["replayed"] = True
        text = out if isinstance(out, str) else ""

        # ---------- orchestrator, scorers, reporter
        if agent == "orchestrator":
            if text.startswith("plan:"):
                m = re.match(r"plan: (\S+) in_scope=(\w+); not applicable \[(.*)\]", text)
                tk, scope, na = m.group(1), m.group(2) == "True", [x.strip(" '") for x in m.group(3).split(",") if x.strip()]
                s.update(kind="plan", title=f"Planned the run for {tk}")
                s["details"] = ([f"{tk} is in the S&P 500 list, so it is in scope."] if scope else [f"{tk} is not in scope."]) + \
                               ([f"Tests that do not apply to this kind of company: {', '.join(na)}."] if na else ["All eleven tests apply."])
            elif text.startswith("fetch:"):
                s.update(kind="fetch", title="Fetched the SEC figures and the latest 10-K", details=["Company facts and the annual report were read from the recorded SEC data."])
            elif text.startswith("score:"):
                s.update(kind="score", title="Scorers computed the tests", details=["Plain arithmetic in code, no model: each test uses figures from the SEC filings and keeps the filing each figure came from."])
            elif text.startswith("qualitative:"):
                s.update(kind="done", title="The qualitative agents finished", details=["Four questions about the annual report were answered, each with cited sentences or a stated lack of evidence."])
            elif text.startswith("explain_and_verify:"):
                s.update(kind="done", title="The Explainer and the Critic finished")
            elif text.startswith("report:"):
                n = int(re.search(r"(\d+) warnings", text).group(1))
                s.update(kind="report", title=f"Reporter wrote the result file with {plural(n, 'warning')}", details=["The file is checked against its schema before it is written."])
            return s

        # ---------- qualitative agent (and its rewrite)
        if agent.startswith("qualitative"):
            rewrite = agent.endswith("/rewrite")
            if typ == "note" and text.startswith("plan:"):
                m = re.match(r"plan: (\w+); items \[(.*?)\]; seeded queries \[(.*)\]", text)
                items = [x.strip(" '") for x in m.group(2).split(",") if x.strip()]
                qs = [x.strip(" '") for x in re.findall(r"'([^']*)'", m.group(3))]
                self.plans[agent] = (items, qs)
                s.update(kind="plan", title=f"Planned: search {items_text(items)} first, starting queries: {queries_text(qs)}")
                s["details"] = [f"Question: {name}.", f"All starting queries: {', '.join(qs)}."]
            elif typ == "tool_call" and summ.startswith("search_many("):
                a = _json_in(summ)
                p_items, p_qs = self.plans.get(agent, ([], []))
                items, qs = a.get("items") or p_items, a.get("queries") or p_qs  # long argument lists are cut in the trace: the plan note has them
                ids = PASSAGE.findall(text)
                hits = self.hits(items, qs, True)
                n = len(hits) if hits else len(ids)
                s.update(kind="search", title=f"Searched {items_text(items)} for {queries_text(qs)}: {plural(n, 'passage')}")
                s["details"] = ["The first search is chosen by code before the first model call, so every run starts from the same evidence."] + self.hit_lines(hits, ids)
            elif typ == "tool_call" and summ.startswith("search("):
                a = _json_in(summ)
                q = a.get("query", "").replace('"', "").strip()
                ids = PASSAGE.findall(text)[:1]
                hits = self.hits(a.get("items"), [q], False)
                n = len(hits) if hits else None
                s.update(kind="search", title=f"Searched {items_text(a.get('items'))} for \"{q}\"" + (f": {plural(n, 'passage')}" if n is not None else ""))
                s["details"] = ["The model chose this search itself."] + self.hit_lines(hits, ids)
            elif typ == "llm_call":
                self.model_calls[agent] = self.model_calls.get(agent, 0) + 1
                u = usage or {}
                if rewrite:
                    body = "".join(re.findall(r'"rationale": "(.*?)(?:"|…)', text)) or ""
                    s.update(kind="rewrite", title=f"Rationale rewrite for {name}: {u.get('prompt_tokens', 0):,} tokens in, {u.get('completion_tokens', 0):,} out, ~{money(e.get('notional_cost_usd'))} at paid rates")
                    s["details"] = ["The model saw only the question, the verdict and the quoted sentences, and rewrote the rationale to say no more than they show."] + ([f"New rationale: {body}"] if body else [])
                else:
                    n = self.model_calls[agent]
                    s.update(kind="model", title=f"Model call {n} for {name}: {u.get('prompt_tokens', 0):,} tokens in, {u.get('completion_tokens', 0):,} out, ~{money(e.get('notional_cost_usd'))} at paid rates")
                    d = []
                    for a in _args(e):
                        ar = a["arguments"]
                        if a["tool"] == "search":
                            d.append(f"The model decided to search {items_text(ar.get('items'))} for \"{ar.get('query', '')}\".")
                        elif a["tool"] == "submit_finding":
                            self.last_args[agent] = ar
                            d.append(f"The model decided to submit its finding: {ar.get('verdict', 'no verdict')}, citing {citations_text(ar.get('citations', []))}.")
                            if ar.get("rationale"):
                                d.append(f"Its rationale: {ar['rationale']}")
                        else:
                            d.append(f"The model called the tool {a['tool'].replace('_', ' ')}.")
                    s["details"] = d or ["The model replied in plain text instead of calling a tool."]
            elif typ == "tool_call" and summ.startswith("citation_check("):
                if text.startswith("verified:"):
                    s.update(kind="pointer", title="Pointer check: quote built from the filing and verified")
                    s["details"] = ["Code, not the model, builds each quote from the sentence numbers and checks it sits inside the filing."]
                    for pid, a, b, c0, c1 in re.findall(r"(\S+:\S+:\d+) sentences (\d+)-(\d+) \[(\d+):(\d+)\]", text):
                        s["details"].append(f"{cap(short_passage(pid))}, {sentences_text(int(a), int(b))}, characters {c0} to {c1} of the normalised text.")
                else:
                    s.update(kind="pointer", title=f"Pointer check: rejected, {reject_reason(text)}", details=["Nothing was accepted from this submission."])
            elif typ == "tool_call" and summ.startswith("submit_finding("):
                ar = self.last_args.get(agent, {})
                if text.startswith("Finding accepted"):
                    cits = ar.get("citations", [])
                    s.update(kind="submit", title=f"Model submitted: {ar.get('verdict', 'a finding')}, citing {citations_text(cits)}")
                    d = [f"Verdict: {ar.get('verdict', 'unknown')}."] + ([f"Rationale: {ar['rationale']}"] if ar.get("rationale") else [])
                    quotes = [self.final_quotes.get((c["passage_id"], (c["first"], c["last"]))) for c in cits]
                    s["quote"] = " … ".join(q for q in quotes if q) or None
                    s["details"] = d + (["The quoted text below was built by code from the cited sentences."] if s["quote"] else [])
                elif text.startswith("Rejected"):
                    s.update(kind="submit", title=f"Model submission rejected: {reject_reason(text)}", details=["The model was told why and asked to submit again."])
                else:
                    s.update(kind="submit", title=f"Model submission malformed: {reject_reason(text)}", details=["The model was asked to call the tool again with arguments in the right format."])
            elif typ == "tool_call" and text.startswith("Tool error"):
                s.update(kind="submit", title=f"Model submission malformed: {reject_reason(text)}", details=["The model was asked to call the tool again with arguments in the right format."])
            elif typ == "note" and text.startswith("stop:"):
                m = re.match(r"stop: (\w+)(?:; verdict: ([^;]+))?; (\d+) model calls, (\d+) tool calls", text)
                reason, verdict, mc, tc = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
                verdict_part = f": {verdict}" if verdict else ""
                s.update(kind="stop", title=f"Finished {name}{verdict_part}, after {plural(mc, 'model call')} and {plural(tc, 'tool call')}",
                         details=[f"The loop ended because {STOP.get(reason, reason.replace('_', ' '))}."])
            return s

        # ---------- Explainer
        if agent == "explainer":
            if typ == "llm_call":
                u = usage or {}
                crits = list(dict.fromkeys(re.findall(r'"criterion\\?": \\?"([GB]\d)', text)))
                s.update(kind="model", title=f"Explainer model call: {u.get('prompt_tokens', 0):,} tokens in, {u.get('completion_tokens', 0):,} out, ~{money(e.get('notional_cost_usd'))} at paid rates")
                s["details"] = ["The model wrote one sentence per test with placeholders instead of numbers" + (f", for {', '.join(crits)}." if crits else ".")]
            else:
                m = re.match(r"explained (\d+) of (\d+) criteria \((\d+) by the model, (\d+) templated\)", text)
                s.update(kind="explained", title=f"Explainer wrote {plural(int(m.group(1)), 'line')}; figures filled in by code from the scorecard",
                         details=[f"{m.group(3)} written by the model and {m.group(4)} templated for tests that are data gaps or do not apply."])
            return s

        # ---------- Critic
        if agent == "critic":
            if typ == "note":
                if text.startswith("attempt"):
                    n = int(re.match(r"attempt (\d+)", text).group(1))
                    s.update(kind="critic", title="Critic started its first pass" if n == 0 else "Critic re-checked the repaired items",
                             details=["The Critic is a second reviewer, partly code and partly a model, that re-checks every explanation and quote." if n == 0 else "Only the items that were sent back are checked again."])
                elif text.startswith("routing:"):
                    items = re.findall(r"(\w+) \((rationale_rewrite|constrained_retry)\)", text)
                    self.repair_phase = bool(items)
                    s.update(kind="routing", title=f"Critic sent {plural(len(items), 'finding')} back for repair" if items else "Critic had nothing to send back")
                    s["details"] = [f"{cap(crit_name(c))}: " + ("rationale rewrite (the verdict stands, the rationale is rewritten from the quotes)." if p == "rationale_rewrite"
                                    else "constrained retry (the agent must cite something new or lower its verdict).") for c, p in items]
                elif text.startswith("final:"):
                    if "all items passed" in text:
                        s.update(kind="final", title="Critic's final result: every item passed", details=["No repair was needed."])
                    else:
                        items = re.findall(r"(\w+)=(\w+)", text)
                        s.update(kind="final", title="Critic's final result: " + ", ".join(f"{crit_name(c)} {'passed after one repair' if st == 'passed_after_retry' else st.replace('_', ' ')}" for c, st in items),
                                 details=["Each repaired item was checked once more and now passes."])
            elif typ == "tool_call":
                m = re.match(r"check_(\w\d)\(\{\"attempt\": (\d+)", summ)
                chk, attempt = m.group(1), int(m.group(2))
                n = re.match(r"(\d+) passed, (\d+) failed", text)
                p, f = int(n.group(1)), int(n.group(2))
                what = CHECK[chk]
                if "nothing to judge" in text:
                    s.update(kind="check", title=f"Critic: {what} had nothing to judge", details=["No repaired item needed a second look."])
                elif f == 0:
                    s.update(kind="check", title=f"Critic: {what} passed for {plural(p, 'item')}")
                else:
                    s.update(kind="check", title=f"Critic: {what} found {plural(f, 'problem')} in {plural(p + f, 'item')}")
                    fails = [c for c in self.checks if c["check"] == chk and c["attempt"] == attempt and c["status"] != "pass"]
                    s["details"] = [x for c in fails for x in objection_sentences(c)] or ["See the checks on the company page."]
            elif typ == "llm_call":
                u = usage or {}
                s.update(kind="model", title=f"Critic model call: {u.get('prompt_tokens', 0):,} tokens in, {u.get('completion_tokens', 0):,} out, ~{money(e.get('notional_cost_usd'))} at paid rates",
                         details=["The model judged whether the quoted sentences support each finding's verdict and rationale."])
            return s
        return s


def objection_sentences(c: dict) -> list[str]:
    """The Critic's objection in words (one or two sentences), never the raw check text."""
    name = cap(crit_name(c["item"])) if c["item"] in CRITERION else c["item"]
    claims = c.get("claims") or []
    if c["check"] == "L1" and c.get("kind") == "rationale":
        quoted = " and ".join(f"\"{x.rstrip('.')}\"" for x in claims) or "a claim"
        return [f"The Critic objected to the {name.lower()} rationale: it says {quoted}, which the quoted sentences don't show."]
    if c["check"] == "L1":
        reason = re.sub(r"^supports_verdict=\w+;\s*", "", c.get("detail", "")).strip()
        reason = re.sub(r"^unsupported:\s*", "", reason).split("; ")[-1].strip()
        return [f"The Critic objected to the {name.lower()} verdict: the quoted sentences don't fully support it, so it looks overstated." + (f" Reason given: {reason}" if reason else "")]
    what = {"R1": "an explanation that its figures do not reproduce", "R2": "a quote that could not be verified in the filing", "R3": "advice language"}.get(c["check"], "a problem")
    return [f"The Critic found {what} for {name}." + (f" {c['detail']}" if c.get("detail") else "")]


def handoff(prev: str, nxt: str, repair: bool = False) -> str:
    table = {("orchestrator", "scorers"): "the orchestrator passes the normalised SEC figures to the scorers.",
             ("scorers", "qualitative"): "scoring is done; the orchestrator starts the qualitative agent on the 10-K, one loop per question.",
             ("orchestrator", "qualitative"): "the orchestrator starts the qualitative agent on the 10-K, one loop per question.",
             ("qualitative", "orchestrator"): "the qualitative agent is done; the orchestrator moves on.",
             ("orchestrator", "explainer"): "the orchestrator passes the scorecard to the Explainer.",
             ("explainer", "critic"): "the Explainer's lines and the agent's findings go to the Critic.",
             ("critic", "qualitative"): "the Critic sends the findings that failed back to the qualitative agent for one repair.",
             ("qualitative", "critic"): "the repaired findings go back to the Critic for a re-check.",
             ("critic", "orchestrator"): "the Critic is done; the orchestrator collects the results.",
             ("orchestrator", "reporter"): "the orchestrator passes everything to the Reporter.",
             ("scorers", "orchestrator"): "scoring is done; the orchestrator continues."}
    names = dict(LANES)
    return "Hand-off: " + table.get((prev, nxt), f"{names[prev].lower()} hands over to {names[nxt].lower()}.")


def render_trace(events: list[dict], result: dict | None = None, *, retriever=None, cik: str | None = None) -> dict:
    r = Renderer(result, retriever, cik)
    steps: list[dict] = []
    for i, e in enumerate(events):
        s = r.one(e)
        s.update(n=i + 1, raw_step=e.get("step", i + 1), agent=e["agent"], type=e["type"])
        if s["kind"] == "unknown":
            raise ValueError(f"no renderer for trace event {e.get('step')}: {e['type']} from {e['agent']}")
        s["repair"] = r.repair_phase and s["lane"] == "qualitative"
        steps.append(s)
    # groups: contiguous steps of the same lane and agent run
    groups: list[dict] = []
    for s in steps:
        key = (s["lane"], s["agent"])
        if groups and groups[-1]["key"] == key:
            groups[-1]["steps"].append(s["n"])
        else:
            groups.append({"key": key, "lane": s["lane"], "steps": [s["n"]], "repair": s["repair"]})
    by_n = {s["n"]: s for s in steps}
    prev_lane = None
    out_groups = []
    for gi, g in enumerate(groups):
        ss = [by_n[n] for n in g["steps"]]
        crit = g["key"][1].split("/")[1] if g["lane"] == "qualitative" else None
        searches = sum(1 for s in ss if s["kind"] == "search")
        calls = sum(1 for s in ss if s["kind"] in ("model", "rewrite"))
        if g["lane"] == "qualitative":
            title = ("Repair: " if g["repair"] else "") + cap(crit_name(crit))
            stop = next((s for s in ss if s["kind"] == "stop"), None)
            tail = (stop["title"].split(": ", 1)[1].split(", after")[0] if stop and ": " in stop["title"] else None)
            subs = sum(1 for s in ss if s["kind"] == "submit" and s["title"].startswith("Model submitted"))
            cits = 0
            for s in ss:
                if s["kind"] == "submit" and s["title"].startswith("Model submitted") and "citing" in s["title"]:
                    cits = len(re.findall(r"sentences? \d+", s["title"]))
            if g["key"][1].endswith("/rewrite"):
                summary = f"{plural(calls, 'model call')}, rationale rewritten from the quotes"
            else:
                summary = f"{plural(searches, 'search', 'searches')}, {plural(calls, 'model call')}" + (f", {tail}" if tail else "") + (f", {plural(cits, 'citation')}" if subs else "")
        elif g["lane"] == "critic":
            title = "Critic"
            checks = sum(1 for s in ss if s["kind"] == "check")
            bad = sum(1 for s in ss if s["kind"] == "check" and "found" in s["title"])
            summary = f"{plural(checks, 'check')}, {'no objections' if not bad else plural(bad, 'check') + ' with objections'}" + (", findings sent back" if any(s["kind"] == "routing" and "back for repair" in s["title"] for s in ss) else "")
        elif g["lane"] == "explainer":
            title, summary = "Explainer", "one model call, figures filled in by code"
        elif g["lane"] == "scorers":
            title, summary = "Scorers", "the tests computed in code, no model"
        elif g["lane"] == "reporter":
            title, summary = "Reporter", "result file written"
        else:
            title, summary = "Planner and orchestrator", plural(len(ss), "step")
        entry = {"id": gi + 1, "lane": g["lane"], "title": title, "summary": summary, "steps": g["steps"], "repair": g["repair"], "handoff": None}
        if prev_lane is not None and prev_lane != g["lane"]:
            entry["handoff"] = handoff(prev_lane, g["lane"], g["repair"])
        prev_lane = g["lane"]
        out_groups.append(entry)
    # running totals (calls, tokens, cost at paid rates)
    calls = tokens = 0
    cost = 0.0
    for s in steps:
        if s["type"] == "llm_call":
            calls += 1
            tokens += s.get("tokens", {}).get("in", 0) + s.get("tokens", {}).get("out", 0)
            cost += s.get("cost_usd", 0.0)
        s["total"] = {"calls": calls, "tokens": tokens, "cost_usd": round(cost, 6)}
    gid = {n: g["id"] for g in out_groups for n in g["steps"]}
    for s in steps:
        s["group"] = gid[s["n"]]
    return {"lanes": [{"id": i, "name": n} for i, n in LANES], "groups": out_groups, "steps": steps}


# ---------- sentences for the company page
PASS_WORD = {"passed": "Passed all checks", "passed_after_retry": "Passed after one repair", "passed_after_repair": "Passed after one repair", "warning": "Still objected to after one repair"}


def critic_notes(result: dict) -> dict:
    """{item: {status, sentences}} for every numeric criterion and qualitative finding, plus the agent and cost sentences, all as plain sentences."""
    critic = result.get("critic") or {}
    out: dict = {"critic": {}, "qualitative": {}}
    for item, final in critic.get("final", {}).items():
        checks = [c for c in critic.get("checks", []) if c["item"] == item]
        fails = [c for c in checks if c["status"] != "pass" and c["attempt"] == 0]
        sentences: list[str] = []
        for c in fails:
            sentences += objection_sentences(c)
        for rp in [x for x in critic.get("repairs", []) if x["item"] == item]:
            did = ("The rationale was rewritten from the quotes" if rp["path"] == "rationale_rewrite" else "The agent was asked to cite something new or lower its verdict")
            sentences.append(did + (" and passed the re-check." if final in ("passed", "passed_after_retry", "passed_after_repair") and rp["outcome"] == "accepted" else ", but the Critic still objects."))
        ran = [CHECK[k] for k in ("R1", "R2", "R3", "L1") if any(c["check"] == k for c in checks)]
        out["critic"][item] = {"status": PASS_WORD.get(final, final.replace("_", " ")), "sentences": sentences or ["Every check passed on the first pass."],
                               "ran": f"Checks run: {', '.join(ran)}." if ran else None, "objected": bool(fails)}
    for q in result.get("qualitative", []):
        f = q["finding"]
        searches = len(f.get("searches", []))
        out["qualitative"][f["criterion"]] = (f"The agent made {plural(f['llm_calls'], 'model call')} and {plural(f['tool_calls'], 'tool call')}, including {plural(searches, 'search', 'searches')} of the filing, "
                                              f"and stopped because {STOP.get(f.get('stop_reason', 'submitted'), 'it was done')}.")
    c = result.get("cost") or {}
    if c:
        out["cost"] = (f"The agents made {plural(c['llm_calls'], 'model call')} and read {c['input_tokens']:,} tokens, writing {c['output_tokens']:,}. On the free tier that cost "
                       f"${c['actual_cost_usd']:.2f}; at paid rates it would have cost about {money(c['notional_cost_usd'])}.")
    return out
