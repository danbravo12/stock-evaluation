"""Qualitative agent: scripted model replies through the real LLMClient (fake transport), a synthetic 10-K, no network."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from engine.agents.qualitative import MAX_QUOTE_WORDS, SYSTEM_PROMPT, assess_qualitative, check_citations, load_criteria, locate_quote
from engine.contracts import QUAL_CRITERIA, QualFinding
from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.llm.client import LLMClient, LLMFixtureMissing
from engine.retrieve import Retriever
from engine.trace import TraceRecorder
from tests.test_llm import Base, FakeTransport
from tests.test_sections import FakeClient, filing

BIZ_A = "Fizz Corp sells sparkling beverages and juice to grocery retailers in 40 countries."
BIZ_B = "Our flagship brand Fizz accounted for 62% of net revenue in fiscal 2025."
BIZ_C = "Our juice plant in Ohio produced 3 million cases of concentrate during the year."
RISK = "Competitors may cut prices and private label products could erode our share of shelf space."
MDA_A = "Net revenue decreased 4% in fiscal 2025 because of an unsuccessful product launch that we discontinued."
MDA_B = "We repurchased 2 million shares for $150 million and paid dividends of $90 million."


def pad(tag: str, words: int = 190) -> str:
    return f"<p>{' '.join(f'{tag}{i}' for i in range(words))}</p>"


BUSINESS = f"<div>ITEM 1. BUSINESS</div><p>{BIZ_A}</p><p>{BIZ_B}</p>{pad('bizpad')}<p>{BIZ_C}</p>{pad('bizend')}"
RISKS = f"<div>ITEM 1A. RISK FACTORS</div><p>{RISK}</p>{pad('riskpad')}<div>ITEM 1B. UNRESOLVED STAFF COMMENTS</div><p>None.</p><div>ITEM 2. PROPERTIES</div><p>x</p>"
MDA = f"<div>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</div><p>{MDA_A}</p><p>{MDA_B}</p>{pad('mdapad')}<div>ITEM 7A. MARKET RISK</div><p>y</p>"
FULL = filing(BUSINESS + RISKS + MDA)
NO_ITEM_7 = filing(BUSINESS + RISKS)


def call(name, args, id="call-1", extra=None):
    tc = {"id": id, "type": "function", "function": {"name": name, "arguments": args if isinstance(args, str) else json.dumps(args)}}
    if extra:
        tc["extra_content"] = extra
    return tc


def reply(*tool_calls, content=None, usage=(1000, 100, 1100), message_extra=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = list(tool_calls)
    message.update(message_extra or {})
    body = {"choices": [{"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": usage[0], "completion_tokens": usage[1], "total_tokens": usage[2]}}
    return 200, {}, json.dumps(body).encode()


def submit(quote, pid, verdict="evidence found", rationale="The filing names its products and customers.", id="call-1"):
    return call("submit_finding", {"verdict": verdict, "rationale": rationale, "citations": [{"passage_id": pid, "quote": quote}]}, id)


def criteria(items: dict[str, list[str]] | None = None, queries: dict[str, list[str]] | None = None) -> dict:
    spec = copy.deepcopy(load_criteria())
    for name in QUAL_CRITERIA:
        spec[name]["items"] = (items or {}).get(name, ["7"])
        spec[name]["queries"] = (queries or {}).get(name, ["unmatchable"])
    return spec


# understandable_business is the only live criterion by default: seeded search finds the Item 1 sentence, the others have items ["7"]
ONLY_BUSINESS = dict(items={"understandable_business": ["1"]}, queries={"understandable_business": ["sparkling beverages juice retailers"]})


class AgentCase(Base):
    def setUp(self):
        super().setUp()
        self.html_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.html_tmp.cleanup)

    def retriever(self, html=NO_ITEM_7) -> Retriever:
        return Retriever(FakeClient(Path(self.html_tmp.name), html))

    def run_agent(self, *responses, html=NO_ITEM_7, spec=None, max_turns=4):
        self.transport = FakeTransport(*responses)
        self.trace = TraceRecorder("test")
        self.llm = LLMClient("live", self.settings(), transport=self.transport, sleep=self.clock.sleep, now=self.clock.now,
                             clock=lambda: 0.0, trace=self.trace)
        self.rt = self.retriever(html)
        self.findings = assess_qualitative(1, "FIZZ", self.rt, self.llm, self.trace, max_turns=max_turns,
                                           criteria=spec or criteria(**ONLY_BUSINESS))
        self.doc = self.rt.index(1).text
        return self.findings.findings[0]

    def pid_of(self, needle: str) -> str:
        return next(p.passage_id for p in self.retriever().index(1).passages if needle in p.text)

    def request(self, i: int) -> dict:
        return json.loads(self.transport.calls[i][2])

    def tool_names(self, i: int) -> list[str]:
        return [t["function"]["name"] for t in self.request(i)["tools"]]


class TestLoop(AgentCase):
    def test_seeded_search_then_immediate_valid_submit(self):
        retr = self.retriever()
        pid = next(p.passage_id for p in retr.index(1).passages if BIZ_A in p.text)
        f = self.run_agent(reply(submit("sells sparkling beverages and juice to grocery retailers", pid)))
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls), ("evidence found", "submitted", 1))
        self.assertEqual(len(self.transport.calls), 1)
        c = f.citations[0]
        self.assertEqual(self.doc[c.char_start:c.char_end], c.quote)
        self.assertEqual((c.passage_id, c.item, c.accession), (pid, "1", "0000000001-26-000001"))
        self.assertTrue(f.searches[0].seeded)
        self.assertEqual(f.tool_calls, 2)  # the seeded search and submit_finding
        first_user = self.request(0)["messages"][1]["content"]
        self.assertIn(pid, first_user)  # the seeded hits are in the first user message
        self.assertIn("Question:", first_user)
        self.assertEqual(self.request(0)["messages"][0]["content"], SYSTEM_PROMPT)
        self.assertEqual(self.request(0)["temperature"], 0.0)

    def test_other_criteria_without_their_section_cost_nothing(self):
        f = self.run_agent(reply(submit("sparkling beverages and juice", "x")), html=NO_ITEM_7)
        others = self.findings.findings[1:]
        self.assertEqual([o.stop_reason for o in others], ["section_missing"] * 3)
        for o in others:
            self.assertEqual((o.llm_calls, o.tool_calls, o.verdict, o.citations), (0, 0, "insufficient evidence", []))
            self.assertIn("Item 7", o.rationale)
        self.assertEqual(f.llm_calls, 1)
        self.assertEqual(len(self.transport.calls), 1)

    def test_search_get_passage_submit_with_unchanged_messages_and_matching_ids(self):
        retr = self.retriever()
        pid = next(p.passage_id for p in retr.index(1).passages if BIZ_C in p.text)
        sig = {"google": {"thought_signature": "sig-abc"}}
        r1 = reply(call("search", {"query": "Ohio plant concentrate"}, "s-1", extra=sig), message_extra={"extra_content": sig})
        r2 = reply(call("get_passage", {"passage_id": pid}, "g-1"))
        r3 = reply(submit("produced 3 million cases of concentrate", pid, id="f-1"))
        f = self.run_agent(r1, r2, r3)
        self.assertEqual((f.verdict, f.llm_calls, f.stop_reason), ("evidence found", 3, "submitted"))
        self.assertEqual(f.tool_calls, 4)  # seeded + search + get_passage + submit
        self.assertEqual([s.seeded for s in f.searches], [True, False])
        self.assertEqual(f.searches[1].queries, ["Ohio plant concentrate"])
        sent = self.request(1)["messages"]
        scripted = json.loads(r1[2])["choices"][0]["message"]
        self.assertEqual(sent[2], scripted)  # appended unchanged, extra_content included
        self.assertEqual(sent[2]["extra_content"], sig)
        self.assertEqual(sent[2]["tool_calls"][0]["extra_content"], sig)
        self.assertEqual((sent[3]["role"], sent[3]["tool_call_id"]), ("tool", "s-1"))
        self.assertIn(pid, sent[3]["content"])
        self.assertEqual(self.request(2)["messages"][-1]["tool_call_id"], "g-1")
        self.assertIn(BIZ_C, self.request(2)["messages"][-1]["content"])

    def test_every_tool_call_in_a_turn_runs_in_order(self):
        retr = self.retriever()
        pid = next(p.passage_id for p in retr.index(1).passages if BIZ_C in p.text)
        f = self.run_agent(reply(call("search", {"query": "Ohio"}, "a"), call("get_passage", {"passage_id": pid}, "b")),
                           reply(submit("Ohio produced", pid)))
        msgs = self.request(1)["messages"]
        self.assertEqual([m["tool_call_id"] for m in msgs if m["role"] == "tool"], ["a", "b"])
        self.assertEqual(f.tool_calls, 4)

    def test_get_passage_works_without_a_prior_search_and_foreign_accession_is_a_tool_error(self):
        retr = self.retriever()
        pid = next(p.passage_id for p in retr.index(1).passages if BIZ_C in p.text)
        f = self.run_agent(reply(call("get_passage", {"passage_id": pid}, "g1"), call("get_passage", {"passage_id": "0000099999-26-000001:1:1"}, "g2"),
                                 call("get_passage", {"passage_id": "0000000001-26-000001:1:999"}, "g3")),
                           reply(submit("produced 3 million cases", pid)))
        tools = [m["content"] for m in self.request(1)["messages"] if m["role"] == "tool"]
        self.assertIn(BIZ_C, tools[0])
        self.assertIn("different filing", tools[1])
        self.assertIn("unknown passage id", tools[2])
        self.assertEqual(f.verdict, "evidence found")  # errors did not break the loop

    def test_plain_text_reply_counts_as_a_turn_and_gets_a_nudge(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(reply(content="I think the business is simple."), reply(submit("sells sparkling beverages", pid)))
        self.assertEqual(f.llm_calls, 2)
        self.assertIn("Use a tool", self.request(1)["messages"][-1]["content"])
        self.assertEqual(f.stop_reason, "submitted")

    def test_turn_cap_offers_only_submit_on_the_last_turn_and_ends_insufficient(self):
        f = self.run_agent(*[reply(call("search", {"query": f"juice {i}"}, f"s{i}")) for i in range(4)])
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls, f.citations), ("insufficient evidence", "turn_cap", 4, []))
        self.assertEqual(len(self.transport.calls), 4)
        for i in range(3):
            self.assertEqual(self.tool_names(i), ["search", "get_passage", "submit_finding"])
        self.assertEqual(self.tool_names(3), ["submit_finding"])
        self.assertIn("last turn", self.request(3)["messages"][-1]["content"])

    def test_search_on_the_last_turn_is_a_tool_error_not_a_crash(self):
        f = self.run_agent(*[reply(call("search", {"query": "juice"}, f"s{i}")) for i in range(4)], max_turns=1)
        self.assertEqual((f.stop_reason, f.llm_calls), ("turn_cap", 1))


class TestCitationSelfCheck(AgentCase):
    def test_invalid_quote_then_corrected_is_accepted(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(reply(submit("sells the world's best beverages", pid)), reply(submit("sells sparkling beverages and juice", pid)))
        self.assertEqual((f.stop_reason, f.llm_calls, f.verdict), ("submitted", 2, "evidence found"))
        error = self.request(1)["messages"][-1]
        self.assertEqual(error["role"], "tool")
        self.assertIn("not found in any passage", error["content"])
        self.assertIn("world's best", error["content"])

    def test_invalid_twice_is_invalid_citation_and_quotes_stay_in_the_trace(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(reply(submit("invented quote one", pid)), reply(submit("invented quote two", pid)))
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls, f.citations), ("insufficient evidence", "invalid_citation", 2, []))
        text = json.dumps([e.model_dump() for e in self.trace.events])
        self.assertIn("invented quote one", text)
        self.assertIn("invented quote two", text)

    def test_quote_from_a_passage_never_retrieved_is_rejected_even_if_it_is_in_the_filing(self):
        pid_c = self.pid_of(BIZ_C)
        pid_a = self.pid_of(BIZ_A)
        narrow = criteria(items={"understandable_business": ["1"]}, queries={"understandable_business": ["sparkling grocery"]})
        self.assertNotIn(BIZ_C, [p.text for p in self.retriever().search(1, "sparkling grocery")])
        f = self.run_agent(reply(submit("produced 3 million cases of concentrate", pid_c)),
                           reply(submit("sells sparkling beverages and juice", pid_a)), spec=narrow)
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 2))
        self.assertIn("was not retrieved", self.request(1)["messages"][-1]["content"])
        self.assertEqual(f.citations[0].passage_id, pid_a)

    def test_whitespace_only_difference_is_accepted_with_exact_offsets(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(reply(submit("grocery  retailers in 40 countries.   Our flagship\nbrand Fizz", pid)))
        self.assertEqual(f.stop_reason, "submitted")
        c = f.citations[0]
        self.assertEqual(self.doc[c.char_start:c.char_end], c.quote)
        self.assertEqual(c.quote, "grocery retailers in 40 countries.\nOur flagship brand Fizz")  # the document's own whitespace
        self.assertEqual(c.quote.count("\n"), 1)

    def test_quote_over_60_words_or_starting_mid_word_is_rejected(self):
        idx = self.retriever().index(1)
        p = idx.passages[0]
        self.assertIsNone(locate_quote("ell sparkling beverages", p, idx.text))
        self.assertIsNotNone(locate_quote("sparkling beverages", p, idx.text))
        big = next(q for q in idx.passages if q.words > 100)
        long_quote = " ".join(big.text.split()[:MAX_QUOTE_WORDS + 1])
        self.assertIsNotNone(locate_quote(long_quote, big, idx.text))  # it is in the text, but too long to cite
        ok, problems = check_citations([{"passage_id": big.passage_id, "quote": long_quote}], {big.passage_id: big}, idx.text)
        self.assertEqual((ok, len(problems)), ([], 1))
        self.assertIn("words", problems[0])

    def test_rejection_messages_say_what_to_change(self):
        idx = self.retriever().index(1)
        big = next(q for q in idx.passages if q.words > 100)
        words = big.text.split()
        retrieved = {big.passage_id: big}
        _, problems = check_citations([{"passage_id": big.passage_id, "quote": " ".join(words[:70])}], retrieved, idx.text)
        suggestion = problems[0].split('for example "')[1].rstrip('"')  # a ready shorter quote...
        self.assertEqual(len(suggestion.split()), 40)
        ok, _ = check_citations([{"passage_id": big.passage_id, "quote": suggestion}], retrieved, idx.text)
        self.assertEqual(len(ok), 1)  # ...that is accepted as it stands
        edited = " ".join(words[:10] + ["CHANGED"] + words[11:20])
        _, problems = check_citations([{"passage_id": big.passage_id, "quote": edited}], retrieved, idx.text)
        prefix = " ".join(words[:10])
        self.assertIn(f'"{prefix}"', problems[0])  # the verified part, offered for resubmission
        self.assertIn(words[10], problems[0])
        resub, _ = check_citations([{"passage_id": big.passage_id, "quote": prefix}], retrieved, idx.text)
        self.assertEqual(len(resub), 1)

    def test_rejection_on_the_last_turn_gets_one_extra_turn(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(*[reply(call("search", {"query": f"juice {i}"}, f"s{i}")) for i in range(3)],
                           reply(submit("bad quote", pid)), reply(submit("sells sparkling beverages", pid)))
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 5))
        self.assertEqual(self.tool_names(4), ["submit_finding"])

    def test_insufficient_verdict_needs_no_citation(self):
        f = self.run_agent(reply(call("submit_finding", {"verdict": "insufficient evidence", "rationale": "The passages do not say how it earns money.", "citations": []})))
        self.assertEqual((f.verdict, f.stop_reason, f.citations), ("insufficient evidence", "submitted", []))


class TestMalformed(AgentCase):
    def test_malformed_twice_is_llm_output_error(self):
        f = self.run_agent(reply(call("submit_finding", {"rationale": "no verdict", "citations": []})), reply(call("submit_finding", "{not json")))
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls), ("insufficient evidence", "llm_output_error", 2))
        self.assertIn("malformed arguments", self.request(1)["messages"][-1]["content"])

    def test_one_correction_is_enough(self):
        pid = self.pid_of(BIZ_A)
        f = self.run_agent(reply(call("search", {"items": ["1"]})), reply(submit("sells sparkling beverages", pid)))
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 2))

    def test_non_insufficient_without_citations_and_bad_items_are_malformed(self):
        f = self.run_agent(reply(call("submit_finding", {"verdict": "evidence found", "rationale": "ok.", "citations": []})),
                           reply(call("search", {"query": "x", "items": ["9"]})))
        self.assertEqual(f.stop_reason, "llm_output_error")


class TestErrorsPropagate(AgentCase):
    class Raising:
        def __init__(self, exc):
            self.exc = exc

        def chat(self, *a, **k):
            raise self.exc

    def assess(self, llm):
        return assess_qualitative(1, "FIZZ", self.retriever(), llm, TraceRecorder("t"), criteria=criteria(**ONLY_BUSINESS))

    def test_quota_and_budget_errors_propagate(self):
        for exc in (QuotaReached("quota reached"), BudgetExceeded("cap")):
            with self.assertRaises(type(exc)):
                self.assess(self.Raising(exc))

    def test_missing_fixture_propagates(self):
        replay = LLMClient("replay", self.settings(), trace=TraceRecorder("t"))
        with self.assertRaises(LLMFixtureMissing):
            self.assess(replay)

    def test_real_quota_error_from_the_client_propagates(self):
        self.write_ledger(requests={"gemini-3.1-flash-lite": {"2026-10-09": 500}})
        with self.assertRaises(QuotaReached):
            self.run_agent(reply(submit("x", "y")))


class TestTotalsAndTrace(AgentCase):
    def full_run(self):
        pid = lambda needle: next(p.passage_id for p in self.retriever(FULL).index(1).passages if needle in p.text)  # noqa: E731
        spec = criteria(items={"understandable_business": ["1"], "durable_competitive_advantage": ["1", "1A"], "candid_management": ["7", "1A"],
                               "rational_capital_allocation": ["7"]},
                        queries={"understandable_business": ["sparkling beverages juice"], "durable_competitive_advantage": ["private label shelf space"],
                                 "candid_management": ["decreased unsuccessful"], "rational_capital_allocation": ["repurchased dividends"]})
        return self.run_agent(reply(submit("sells sparkling beverages", pid(BIZ_A))),
                              reply(submit("could erode our share of shelf space", pid(RISK)), usage=(2000, 200, 2200)),
                              reply(submit("an unsuccessful product launch that we discontinued", pid(MDA_A)), usage=(3000, 50, 3050)),
                              reply(submit("repurchased 2 million shares for $150 million", pid(MDA_B))), html=FULL, spec=spec)

    def test_four_findings_in_config_order_with_totals_that_add_up(self):
        self.full_run()
        fs = self.findings
        self.assertEqual([f.criterion for f in fs.findings], list(QUAL_CRITERIA))
        self.assertTrue(all(f.stop_reason == "submitted" and f.citations for f in fs.findings))
        t = fs.totals
        self.assertEqual(t.llm_calls, 4)
        self.assertEqual(t.llm_calls, len(self.llm.calls))
        self.assertEqual(t.usage.prompt_tokens, sum(c.usage.prompt_tokens for c in self.llm.calls))
        self.assertEqual(t.usage.prompt_tokens, 1000 + 2000 + 3000 + 1000)
        self.assertEqual(t.usage.completion_tokens, 100 + 200 + 50 + 100)
        self.assertAlmostEqual(t.notional_cost_usd, sum(f.notional_cost_usd for f in fs.findings))
        self.assertAlmostEqual(t.notional_cost_usd, sum(c.notional_cost_usd for c in self.llm.calls))
        self.assertAlmostEqual(t.notional_cost_usd, (7000 * 0.25 + 450 * 1.5) / 1e6)
        self.assertEqual(t.actual_cost_usd, 0.0)
        self.assertEqual(fs.accession, "0000000001-26-000001")
        for f in fs.findings:
            self.assertEqual(f.usage.total_tokens, f.usage.prompt_tokens + f.usage.completion_tokens)

    def test_trace_reads_plan_tools_decision_check_stop(self):
        self.full_run()
        mine = [e for e in self.trace.events if e.agent == "qualitative/understandable_business"]
        self.assertEqual([e.type for e in mine], ["note", "tool_call", "llm_call", "tool_call", "tool_call", "note"])
        plan, seeded, llm, check, submit_, stop = mine
        self.assertIn("plan: understandable_business", plan.output)
        self.assertIn("seeded", seeded.input_summary)
        self.assertIn("seeded search", seeded.output)
        self.assertIn("submit_finding", llm.output[0]["tool"])
        self.assertIn("verified", check.output)
        self.assertIn("accepted", submit_.output)
        self.assertIn("stop: submitted", stop.output)
        self.assertEqual([e.step for e in self.trace.events], list(range(1, len(self.trace.events) + 1)))
        agents = {e.agent for e in self.trace.events}
        self.assertEqual(agents, {f"qualitative/{c}" for c in QUAL_CRITERIA})

    def test_section_missing_is_traced_without_a_model_call(self):
        self.run_agent(reply(submit("sparkling beverages", "x")))
        mine = [e for e in self.trace.events if e.agent == "qualitative/candid_management"]
        self.assertEqual([e.type for e in mine], ["note", "note", "note"])
        self.assertIn("section_missing", mine[1].output)


class TestContracts(unittest.TestCase):
    def test_finding_rules(self):
        base = dict(criterion="candid_management", rationale="r", stop_reason="submitted")
        QualFinding(verdict="insufficient evidence", **base)
        with self.assertRaises(ValidationError):
            QualFinding(verdict="evidence found", **base)  # needs a citation
        with self.assertRaises(ValidationError):
            QualFinding(verdict="evidence found", **{**base, "stop_reason": "turn_cap"})


if __name__ == "__main__":
    unittest.main()
