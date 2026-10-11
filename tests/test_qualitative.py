"""Qualitative agent: scripted model replies through the real LLMClient (fake transport), a synthetic 10-K, no network."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from pydantic import ValidationError

from engine.agents.qualitative import MAX_SPAN_WORDS, SYSTEM_PROMPT, SYSTEM_PROMPT_V2, TOOLS, prompt_parts, assess_qualitative, check_citations, constrained_retry, load_criteria, render_passage
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


def submit(ptr, verdict="evidence found", rationale="The filing names its products and customers.", id="call-1"):
    """ptr = (passage_id, first[, last]) or a list of them."""
    ptrs = ptr if isinstance(ptr, list) else [ptr]
    cites = [{"passage_id": t[0], "first": t[1], "last": t[2] if len(t) > 2 else t[1]} for t in ptrs]
    return call("submit_finding", {"verdict": verdict, "rationale": rationale, "citations": cites}, id)


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
        # These synthetic tests exercise the v1 prompt (at most 3 consecutive sentences); v2, the active version since the 2026-10-12 re-record, has its own class below.
        self.pin_v1 = mock.patch("engine.agents.qualitative.active_prompt", lambda name: "v1")
        self.pin_v1.start()
        self.addCleanup(self.pin_v1.stop)
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

    def loc(self, needle: str) -> tuple[str, int]:
        """(passage id, 1-based sentence number) of the sentence containing `needle`."""
        idx = self.retriever().index(1)
        for p in idx.passages:
            for i, (a, b) in enumerate(p.sentences, start=1):
                if needle in idx.text[a:b]:
                    return p.passage_id, i
        raise AssertionError(needle)

    def request(self, i: int) -> dict:
        return json.loads(self.transport.calls[i][2])

    def tool_names(self, i: int) -> list[str]:
        return [t["function"]["name"] for t in self.request(i)["tools"]]


class TestLoop(AgentCase):
    def test_seeded_search_then_immediate_valid_submit(self):
        pid, i = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, i))))
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls), ("evidence found", "submitted", 1))
        self.assertEqual(len(self.transport.calls), 1)
        c = f.citations[0]
        self.assertEqual(c.quote, BIZ_A)  # the quote is built by code from the pointer
        self.assertEqual(self.doc[c.char_start:c.char_end], c.quote)
        self.assertEqual((c.passage_id, c.item, c.accession, c.sentences), (pid, "1", "0000000001-26-000001", [i, i]))
        self.assertTrue(f.searches[0].seeded)
        self.assertEqual(f.tool_calls, 2)  # the seeded search and submit_finding
        first_user = self.request(0)["messages"][1]["content"]
        self.assertIn(f"[{pid}] Item 1\n[1] ITEM 1.", first_user)  # numbered sentences under a passage header
        self.assertIn(f"[{i}] {BIZ_A}", first_user)
        self.assertIn("Question:", first_user)
        self.assertEqual(self.request(0)["messages"][0]["content"], SYSTEM_PROMPT)
        self.assertEqual(self.request(0)["temperature"], 0.0)
        props = self.request(0)["tools"][2]["function"]["parameters"]["properties"]["citations"]["items"]["properties"]
        self.assertEqual(sorted(props), ["first", "last", "passage_id"])

    def test_other_criteria_without_their_section_are_not_assessed_and_cost_nothing(self):
        pid, i = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, i))), html=NO_ITEM_7)
        others = self.findings.findings[1:]
        self.assertEqual([o.stop_reason for o in others], ["section_missing"] * 3)
        for o in others:
            self.assertEqual((o.llm_calls, o.tool_calls, o.verdict, o.citations), (0, 0, "not assessed", []))
            self.assertIn("Item 7", o.rationale)
        self.assertEqual(f.llm_calls, 1)
        self.assertEqual(len(self.transport.calls), 1)

    def test_search_get_passage_submit_with_unchanged_messages_and_matching_ids(self):
        pid, i = self.loc(BIZ_C)
        sig = {"google": {"thought_signature": "sig-abc"}}
        r1 = reply(call("search", {"query": "Ohio plant concentrate"}, "s-1", extra=sig), message_extra={"extra_content": sig})
        r2 = reply(call("get_passage", {"passage_id": pid}, "g-1"))
        r3 = reply(submit((pid, i), id="f-1"))
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
        self.assertIn(f"[{i}] {BIZ_C}", self.request(2)["messages"][-1]["content"])

    def test_every_tool_call_in_a_turn_runs_in_order(self):
        pid, i = self.loc(BIZ_C)
        f = self.run_agent(reply(call("search", {"query": "Ohio"}, "a"), call("get_passage", {"passage_id": pid}, "b")), reply(submit((pid, i))))
        msgs = self.request(1)["messages"]
        self.assertEqual([m["tool_call_id"] for m in msgs if m["role"] == "tool"], ["a", "b"])
        self.assertEqual(f.tool_calls, 4)

    def test_get_passage_works_without_a_prior_search_and_foreign_accession_is_a_tool_error(self):
        pid, i = self.loc(BIZ_C)
        f = self.run_agent(reply(call("get_passage", {"passage_id": pid}, "g1"), call("get_passage", {"passage_id": "0000099999-26-000001:1:1"}, "g2"),
                                 call("get_passage", {"passage_id": "0000000001-26-000001:1:999"}, "g3")), reply(submit((pid, i))))
        tools = [m["content"] for m in self.request(1)["messages"] if m["role"] == "tool"]
        self.assertIn(BIZ_C, tools[0])
        self.assertIn("different filing", tools[1])
        self.assertIn("unknown passage id", tools[2])
        self.assertEqual(f.verdict, "evidence found")  # errors did not break the loop

    def test_plain_text_reply_counts_as_a_turn_and_gets_a_nudge(self):
        f = self.run_agent(reply(content="I think the business is simple."), reply(submit(self.loc(BIZ_A))))
        self.assertEqual(f.llm_calls, 2)
        self.assertIn("Use a tool", self.request(1)["messages"][-1]["content"])
        self.assertEqual(f.stop_reason, "submitted")

    def test_turn_cap_offers_only_submit_on_the_last_turn_and_is_not_assessed(self):
        f = self.run_agent(*[reply(call("search", {"query": f"juice {i}"}, f"s{i}")) for i in range(4)])
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls, f.citations), ("not assessed", "turn_cap", 4, []))
        self.assertIn("4 turns", f.rationale)
        self.assertEqual(len(self.transport.calls), 4)
        for i in range(3):
            self.assertEqual(self.tool_names(i), ["search", "get_passage", "submit_finding"])
        self.assertEqual(self.tool_names(3), ["submit_finding"])
        self.assertIn("last turn", self.request(3)["messages"][-1]["content"])

    def test_search_on_the_last_turn_is_a_tool_error_not_a_crash(self):
        f = self.run_agent(*[reply(call("search", {"query": "juice"}, f"s{i}")) for i in range(4)], max_turns=1)
        self.assertEqual((f.stop_reason, f.llm_calls), ("turn_cap", 1))

    def test_insufficient_verdict_is_a_submitted_finding_about_the_filing(self):
        f = self.run_agent(reply(call("submit_finding", {"verdict": "insufficient evidence", "rationale": "The passages say nothing on how it earns money.", "citations": []})))
        self.assertEqual((f.verdict, f.stop_reason, f.citations), ("insufficient evidence", "submitted", []))

    def test_rubric_and_note_reach_the_first_message(self):
        spec = criteria(**ONLY_BUSINESS)
        spec["understandable_business"]["rationale_note"] = "NOTE-FOR-RATIONALE"
        self.run_agent(reply(submit(self.loc(BIZ_A))), spec=spec)
        first = self.request(0)["messages"][1]["content"]
        self.assertIn("NOTE-FOR-RATIONALE", first)
        self.assertIn(spec["understandable_business"]["found_means"], first)
        self.assertIn("argues against", json.dumps(load_criteria()))  # the 'evidence against' rule is in the real rubric text


class TestPointerCitations(AgentCase):
    def test_multi_sentence_span_gives_the_exact_document_text(self):
        pid, i = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, i, i + 1))))
        c = f.citations[0]
        self.assertEqual(c.quote, BIZ_A + "\n" + BIZ_B)  # includes the document's own line break
        self.assertEqual(self.doc[c.char_start:c.char_end], c.quote)
        self.assertEqual(c.sentences, [i, i + 1])

    def test_out_of_range_then_corrected_is_accepted(self):
        pid, i = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, 99))), reply(submit((pid, i))))
        self.assertEqual((f.stop_reason, f.llm_calls, f.verdict), ("submitted", 2, "evidence found"))
        error = self.request(1)["messages"][-1]
        self.assertEqual(error["role"], "tool")
        self.assertIn("<= last <=", error["content"])  # names the valid range
        self.assertIn(pid, error["content"])

    def test_every_kind_of_bad_pointer_is_rejected_then_invalid_citation(self):
        pid, i = self.loc(BIZ_A)
        self.assertGreaterEqual(len(self.retriever().index(1).by_id[pid].sentences), 4)
        bad = {"out of range": (pid, 0, 1), "last before first": (pid, i + 1, i), "four sentences": (pid, 1, 4),
               "non-integer": (pid, "1", "2"), "unknown passage": ("0000000001-26-000001:1:999", 1, 1)}
        for name, (p, a, b) in bad.items():
            with self.subTest(name):
                bad_call = call("submit_finding", {"verdict": "evidence found", "rationale": "ok.", "citations": [{"passage_id": p, "first": a, "last": b}]})
                f = self.run_agent(reply(bad_call), reply(bad_call))
                self.assertEqual((f.verdict, f.stop_reason, f.llm_calls, f.citations), ("not assessed", "invalid_citation", 2, []))
                self.assertTrue(any(str(e.output).startswith("Rejected:") for e in self.trace.events))  # (identical requests are served from the cache, so look at the trace)

    def test_over_120_words_is_rejected(self):
        idx = self.retriever().index(1)
        big = next(p for p in idx.passages if p.words > 150)
        spans = [len(idx.text[a:b].split()) for a, b in big.sentences]
        first = next(k for k in range(len(spans) - 2) if sum(spans[k:k + 3]) > MAX_SPAN_WORDS)
        _, problems = check_citations([{"passage_id": big.passage_id, "first": first + 1, "last": first + 3}], {big.passage_id: big}, idx.text)
        self.assertIn("words; the limit is 120", problems[0])

    def test_passage_never_retrieved_is_rejected_even_if_it_is_in_the_filing(self):
        pid_c, ic = self.loc(BIZ_C)
        pid_a, ia = self.loc(BIZ_A)
        narrow = criteria(items={"understandable_business": ["1"]}, queries={"understandable_business": ["sparkling grocery"]})
        f = self.run_agent(reply(submit((pid_c, ic))), reply(submit((pid_a, ia))), spec=narrow)
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 2))
        self.assertIn("was not shown to you", self.request(1)["messages"][-1]["content"])
        self.assertEqual(f.citations[0].passage_id, pid_a)

    def test_passage_found_by_the_models_own_search_may_be_cited(self):
        pid_c, ic = self.loc(BIZ_C)
        f = self.run_agent(reply(call("search", {"query": "Ohio plant"}, "s")), reply(submit((pid_c, ic))))
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 2))

    def test_rejected_pointers_stay_in_the_trace(self):
        pid, _ = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, 77))), reply(submit((pid, 88))))
        text = json.dumps([e.model_dump() for e in self.trace.events])
        self.assertIn('"first": 77', text)
        self.assertIn('"first": 88', text)
        self.assertEqual(f.stop_reason, "invalid_citation")

    def test_rejection_on_the_last_turn_gets_one_extra_turn(self):
        pid, i = self.loc(BIZ_A)
        f = self.run_agent(*[reply(call("search", {"query": f"juice {k}"}, f"s{k}")) for k in range(3)], reply(submit((pid, 99))), reply(submit((pid, i))))
        self.assertEqual((f.stop_reason, f.llm_calls), ("submitted", 5))
        self.assertEqual(self.tool_names(4), ["submit_finding"])

    def test_bad_pointers_with_an_insufficient_verdict_are_dropped_not_rejected(self):
        pid, _ = self.loc(BIZ_A)
        f = self.run_agent(reply(submit((pid, 99), verdict="insufficient evidence", rationale="Nothing relevant.")))
        self.assertEqual((f.verdict, f.stop_reason, f.citations, f.llm_calls), ("insufficient evidence", "submitted", [], 1))


class TestWordCapPromptV2(AgentCase):
    """ADR-046 amendment: a citation is a contiguous range of at most 120 words, not at most 3 sentences. Active since the re-record of 2026-10-12."""

    def v2(self):
        return mock.patch("engine.agents.qualitative.active_prompt", lambda name: "v2")

    def test_v2_is_the_active_version_and_v1_stays_available(self):
        from engine.prompts import active
        self.pin_v1.stop()  # look at the real configuration, not the v1 pin of the synthetic tests
        self.assertEqual(active("qualitative"), "v2")
        self.assertIsNone(prompt_parts()[3])  # no sentence cap: the word cap applies
        self.assertEqual(prompt_parts("v1")[3], 3)

    def test_v2_accepts_a_long_range_that_v1_refuses_and_still_caps_the_words(self):
        pid, _ = self.loc(BIZ_A)
        with self.v2():
            f = self.run_agent(reply(submit((pid, 1, 4))))  # four sentences of passage 1
            self.assertEqual((f.stop_reason, f.llm_calls, f.citations[0].sentences), ("submitted", 1, [1, 4]))
            sent = self.request(0)
            self.assertEqual(sent["messages"][0]["content"], SYSTEM_PROMPT_V2)
            self.assertIn("up to 120 words", json.dumps(sent["tools"]))
            self.assertNotIn("at most first + 2", json.dumps(sent["tools"]))
            idx = self.retriever().index(1)
            big = next(p for p in idx.passages if p.words > 150)
            ok, problems = check_citations([{"passage_id": big.passage_id, "first": 1, "last": len(big.sentences)}], {big.passage_id: big}, idx.text, None)
            self.assertEqual(ok, [])
            self.assertIn("words; the limit is 120", problems[0])

    def test_v1_prompt_and_tools_are_unchanged(self):
        self.assertIn("at most 3 consecutive sentences", SYSTEM_PROMPT)
        self.assertNotIn("at most 3 consecutive sentences", SYSTEM_PROMPT_V2)
        self.assertIn("at most first + 2", json.dumps(TOOLS))


class TestConstrainedRetry(AgentCase):
    """The Critic-routed retry for a verdict failure (ADR-052): cite something new, or lower the verdict; at most 3 turns."""

    def start(self):
        self.pid, self.i = self.loc(BIZ_A)
        self.orig = self.run_agent(reply(submit((self.pid, self.i))))  # "evidence found", citing BIZ_A

    def retry(self, finding, *responses):
        self.transport = FakeTransport(*responses)
        self.trace = TraceRecorder("t")
        self.llm = LLMClient("live", self.settings(), transport=self.transport, sleep=self.clock.sleep, now=self.clock.now, clock=lambda: 0.0, trace=self.trace)
        self.rt = self.retriever()
        return constrained_retry(1, "FIZZ", self.rt, self.llm, self.trace, finding, reason="needs a figure, not an assertion", criteria=criteria(**ONLY_BUSINESS))

    def test_first_message_gives_the_reason_the_verdict_the_citations_and_the_two_options(self):
        self.start()
        pid_c, ic = self.loc(BIZ_C)
        res, outcome = self.retry(self.orig, reply(submit((pid_c, ic))))
        first = self.request(0)["messages"][1]["content"]
        self.assertIn("needs a figure, not an assertion", first)
        self.assertIn('earlier verdict was "evidence found"', first)
        self.assertIn(BIZ_A, first)  # the earlier citation is shown
        self.assertIn("exactly two options", first)
        self.assertIn("lower verdict", first)
        self.assertEqual((outcome, res.verdict), ("submitted", "evidence found"))  # a new citation keeps the verdict
        self.assertEqual(res.citations[0].passage_id, pid_c)

    def test_same_verdict_without_a_new_citation_gets_one_error_then_the_retry_ends(self):
        self.start()
        same = submit((self.pid, self.i))
        res, outcome = self.retry(self.orig, reply(same), reply(same))
        self.assertEqual((outcome, res.stop_reason, res.verdict, res.llm_calls), ("no_change", "turn_cap", "not assessed", 2))
        self.assertIn("at least one sentence you have not cited before", self.request(1)["messages"][-1]["content"])
        self.assertEqual(len(self.transport.calls), 2)

    def test_a_lower_verdict_is_accepted_even_with_the_same_citation(self):
        self.start()
        res, outcome = self.retry(self.orig, reply(submit((self.pid, self.i), verdict="evidence weak", rationale="Only a general statement.")))
        self.assertEqual((outcome, res.verdict, res.llm_calls), ("submitted", "evidence weak", 1))

    def test_a_higher_verdict_is_refused(self):
        self.start()
        weak = self.orig.model_copy(update={"verdict": "evidence weak"})
        pid_c, ic = self.loc(BIZ_C)
        res, outcome = self.retry(weak, reply(submit((pid_c, ic), verdict="evidence found")), reply(submit((pid_c, ic), verdict="evidence weak")))
        self.assertIn("not raise it", self.request(1)["messages"][-1]["content"])
        self.assertEqual((outcome, res.verdict), ("submitted", "evidence weak"))

    def test_three_turns_at_most_and_the_last_offers_only_submit(self):
        self.start()
        res, outcome = self.retry(self.orig, *[reply(call("search", {"query": f"juice {k}"}, f"s{k}")) for k in range(3)])
        self.assertEqual((outcome, res.stop_reason, len(self.transport.calls)), ("not_submitted", "turn_cap", 3))
        self.assertEqual(self.tool_names(2), ["submit_finding"])


class TestMalformed(AgentCase):
    def test_malformed_twice_is_llm_output_error_and_not_assessed(self):
        f = self.run_agent(reply(call("submit_finding", {"rationale": "no verdict", "citations": []})), reply(call("submit_finding", "{not json")))
        self.assertEqual((f.verdict, f.stop_reason, f.llm_calls), ("not assessed", "llm_output_error", 2))
        self.assertIn("malformed arguments", self.request(1)["messages"][-1]["content"])

    def test_one_correction_is_enough(self):
        f = self.run_agent(reply(call("search", {"items": ["1"]})), reply(submit(self.loc(BIZ_A))))
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
            self.run_agent(reply(submit(("x", 1))))


class TestTotalsAndTrace(AgentCase):
    def full_run(self):
        spec = criteria(items={"understandable_business": ["1"], "durable_competitive_advantage": ["1", "1A"], "candid_management": ["7", "1A"],
                               "rational_capital_allocation": ["7"]},
                        queries={"understandable_business": ["sparkling beverages juice"], "durable_competitive_advantage": ["private label shelf space"],
                                 "candid_management": ["decreased unsuccessful"], "rational_capital_allocation": ["repurchased dividends"]})
        self.rt = self.retriever(FULL)
        loc = self.loc_full
        return self.run_agent(reply(submit(loc(BIZ_A))), reply(submit(loc(RISK)), usage=(2000, 200, 2200)),
                              reply(submit(loc(MDA_A)), usage=(3000, 50, 3050)), reply(submit(loc(MDA_B))), html=FULL, spec=spec)

    def loc_full(self, needle):
        idx = self.retriever(FULL).index(1)
        for p in idx.passages:
            for i, (a, b) in enumerate(p.sentences, start=1):
                if needle in idx.text[a:b]:
                    return p.passage_id, i
        raise AssertionError(needle)

    def test_four_findings_in_config_order_with_totals_that_add_up(self):
        self.full_run()
        fs = self.findings
        self.assertEqual([f.criterion for f in fs.findings], list(QUAL_CRITERIA))
        self.assertTrue(all(f.stop_reason == "submitted" and f.citations for f in fs.findings))
        t = fs.totals
        self.assertEqual(t.llm_calls, 4)
        self.assertEqual(t.llm_calls, len(self.llm.calls))
        self.assertEqual(t.usage.prompt_tokens, 1000 + 2000 + 3000 + 1000)
        self.assertEqual(t.usage.completion_tokens, 100 + 200 + 50 + 100)
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
        self.assertEqual({e.agent for e in self.trace.events}, {f"qualitative/{c}" for c in QUAL_CRITERIA})

    def test_section_missing_is_traced_without_a_model_call(self):
        self.run_agent(reply(submit(self.loc(BIZ_A))))
        mine = [e for e in self.trace.events if e.agent == "qualitative/candid_management"]
        self.assertEqual([e.type for e in mine], ["note", "note", "note"])
        self.assertIn("section_missing", mine[1].output)


class TestContracts(unittest.TestCase):
    def test_every_stop_reason_maps_to_the_right_verdict(self):
        base = dict(criterion="candid_management", rationale="r")
        QualFinding(verdict="insufficient evidence", stop_reason="submitted", **base)
        for reason in ("turn_cap", "invalid_citation", "section_missing", "llm_output_error"):
            QualFinding(verdict="not assessed", stop_reason=reason, **base)
            with self.assertRaises(ValidationError):
                QualFinding(verdict="insufficient evidence", stop_reason=reason, **base)
        with self.assertRaises(ValidationError):
            QualFinding(verdict="not assessed", stop_reason="submitted", **base)
        with self.assertRaises(ValidationError):
            QualFinding(verdict="evidence found", stop_reason="submitted", **base)  # needs a citation


if __name__ == "__main__":
    unittest.main()
