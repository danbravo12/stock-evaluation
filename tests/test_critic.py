"""Critic: rule checks with injected faults, the model check's inputs, routing, retry once, gate-not-author (offline, scripted model)."""
from __future__ import annotations

import copy
import unittest
from unittest import mock

from engine.agents import review
from engine.agents.critic import (CriticVerdicts, FindingCheck, banned_hits, check_citations, check_explanation, llm_payload, load_rubric,
                                  needs_llm_check)
from engine.agents.explainer import _Item, _Out, explain
from engine.contracts import Citation, Explanation, Explanations
from engine.fetch.edgar import EdgarClient
from engine.filing_text import html_to_text
from engine.retrieve import Retriever
from engine.score import score_ticker
from engine.settings import Settings
from engine.trace import TraceRecorder
from eval.qualitative_agreement import replay_findings
from tests.stubs import StubLLM


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = Settings.from_env()
        cls.edgar = EdgarClient("replay", settings)
        cls.retriever = Retriever(cls.edgar)
        cls.score = score_ticker(cls.edgar, "KO")
        cls.qual = replay_findings(["KO"], cls.retriever)["KO"]
        cik = cls.qual.cik
        ref = cls.edgar.latest_filing(cik, "10-K")
        doc = cls.edgar.filing_document(ref)
        cls.accession, cls.sha = ref.accession, doc.sha256
        cls.text = html_to_text(doc.body.decode("utf-8", errors="replace"))
        cls.idx = cls.retriever.index(cik)

    def expl(self, cid, raw, **kw):
        r = next(x for x in self.score.results if x.id == cid)
        from engine.agents.explainer import PLACEHOLDER, render
        return r, Explanation(criterion=cid, raw=raw, text=kw.get("text", render(raw, r)), placeholders_used=kw.get("used", list(dict.fromkeys(PLACEHOLDER.findall(raw)))))

    def finding(self, name):
        return next(f for f in self.qual.findings if f.criterion == name)


class TestRuleR1(Fixture):
    def test_a_good_explanation_passes(self):
        r, e = self.expl("G1", "Revenue in 2025 was {revenue} (test: {threshold}).")
        self.assertEqual(check_explanation(r, e), [])

    def test_wrong_placeholder(self):
        r, e = self.expl("G1", "Revenue was {revenue} and the ratio {current_ratio}.")
        self.assertIn("invalid placeholder", " ".join(check_explanation(r, e)))
        self.assertIn("{current_ratio}", " ".join(check_explanation(r, e)))

    def test_stray_number_but_years_and_threshold_numbers_are_allowed(self):
        r, e = self.expl("G1", "Revenue was {revenue}, about 48 in the latest year.")
        self.assertIn("stray numeral(s)", " ".join(check_explanation(r, e)))
        self.assertIn("48", " ".join(check_explanation(r, e)))
        r, e = self.expl("G1", "In 2025 revenue was {revenue}, above the 1 billion line.")  # 2025 is the result's year, 1 is in "$1B"
        self.assertEqual(check_explanation(r, e), [])
        r, e = self.expl("G1", "In 2019 revenue was {revenue}.")
        self.assertIn("2019", " ".join(check_explanation(r, e)))

    def test_text_that_is_not_the_rendering_of_the_raw_text(self):
        r, e = self.expl("G1", "Revenue was {revenue}.", text="Revenue was $99.99 billion.")
        self.assertIn("not what rendering", " ".join(check_explanation(r, e)))

    def test_placeholders_used_must_match(self):
        r, e = self.expl("G1", "Revenue was {revenue}.", used=[])
        self.assertIn("placeholders_used", " ".join(check_explanation(r, e)))

    def test_missing_and_templated(self):
        r = next(x for x in self.score.results if x.id == "G6")
        self.assertEqual(check_explanation(r, None), ["no explanation"])
        from engine.agents.explainer import templated_line
        t = templated_line(r)
        ok = Explanation(criterion="G6", raw=t, text=t, templated=True)
        self.assertEqual(check_explanation(r, ok), [])
        bad = Explanation(criterion="G6", raw="Price is high.", text="Price is high.", templated=True)
        self.assertTrue(check_explanation(r, bad))
        llm_written = Explanation(criterion="G6", raw="No price.", text="No price.")
        self.assertIn("must use the templated line", " ".join(check_explanation(r, llm_written)))


class TestRuleR2(Fixture):
    def run_r2(self, finding, text=None, sha=None, sections=None, passages=None):
        return check_citations(finding, text or self.text, sha or self.sha, self.accession, sections or self.idx.sections, passages or self.idx.by_id)

    def test_real_citations_pass(self):
        for f in self.qual.findings:
            self.assertEqual(self.run_r2(f), [], f.criterion)

    def swapped(self, **change):
        f = copy.deepcopy(self.finding("understandable_business"))
        f.citations[0] = f.citations[0].model_copy(update=change)
        return f

    def test_quote_altered_by_one_character(self):
        c = self.finding("understandable_business").citations[0]
        problems = self.run_r2(self.swapped(quote=c.quote[:-1] + ("!" if c.quote[-1] != "!" else "?")))
        self.assertIn("not the document text", " ".join(problems))

    def test_span_outside_the_cited_passage(self):
        c = self.finding("understandable_business").citations[0]
        p = self.idx.by_id[c.passage_id]
        shift = p.char_end - c.char_start + 5
        moved = self.swapped(char_start=c.char_start + shift, char_end=c.char_end + shift, quote=self.text[c.char_start + shift:c.char_end + shift])
        self.assertIn("outside the passage", " ".join(self.run_r2(moved)))

    def test_wrong_document_sha(self):
        self.assertIn("sha256 does not match", " ".join(self.run_r2(self.finding("understandable_business"), sha="0" * 64)))

    def test_span_outside_a_found_section_and_wrong_item(self):
        f = self.swapped(item="1A")
        probs = " ".join(self.run_r2(f))
        self.assertIn("outside Item 1A", probs)
        self.assertIn("not Item 1A", probs)

    def test_section_not_found_and_wrong_accession(self):
        sections = copy.deepcopy(self.idx.sections)
        sections["1"] = sections["1"].model_copy(update={"status": "not_found"})
        self.assertIn("not a found section", " ".join(self.run_r2(self.finding("understandable_business"), sections=sections)))
        self.assertIn("accession", " ".join(self.run_r2(self.swapped(accession="0000000000-00-000000"))))

    def test_unknown_passage(self):
        self.assertIn("unknown passage", " ".join(self.run_r2(self.swapped(passage_id="nope:1:1"))))


class TestRuleR3(unittest.TestCase):
    def test_advice_and_valuation_language_is_flagged(self):
        for text in ("Investors should buy this stock.", "The shares look undervalued.", "A strong buy.", "We set a price target of 10.", "There is upside from here.",
                     "It may outperform.", "This is a bargain.", "We recommend holding.", "An attractive valuation.", "A hold rating."):
            self.assertTrue(banned_hits(text), text)

    def test_ordinary_corporate_vocabulary_is_not_flagged(self):
        for text in ("The company repurchased shares in a share buyback.", "Customers buy the drinks and the company sells them to retailers.",
                     "Collective bargaining agreements cover many employees.", "Duke is a holding company.", "Plans are on hold.",
                     "Revenue was $47.94 billion, which exceeds the minimum."):
            self.assertEqual(banned_hits(text), [], text)


class TestModelCheckInput(Fixture):
    def test_only_found_or_weak_findings_with_citations_are_judged(self):
        judged = {f.criterion for f in self.qual.findings if needs_llm_check(f)}
        self.assertEqual(judged, {f.criterion for f in self.qual.findings if f.verdict in ("evidence found", "evidence weak") and f.citations})
        self.assertNotIn("candid_management", judged)  # KO's is "insufficient evidence"

    def test_payload_has_the_criterion_two_rubric_lines_quotes_and_rationale_and_nothing_else(self):
        f = self.finding("durable_competitive_advantage")
        p = llm_payload([f], load_rubric())[0]
        self.assertEqual(sorted(p), ["claimed_verdict", "criterion", "definition_of_claimed_verdict", "definition_of_the_verdict_below", "question", "quotes", "rationale"])
        rubric = load_rubric()["durable_competitive_advantage"]
        self.assertEqual((p["definition_of_claimed_verdict"], p["definition_of_the_verdict_below"]), (rubric["found_means"], rubric["weak_means"]))
        self.assertEqual(p["quotes"], [c.quote for c in f.citations])


def verdicts(*items):
    return CriticVerdicts(checks=[FindingCheck(criterion=c, supports_verdict=v, unsupported_claims=u, reason=r) for c, v, u, r in items])


class TestRoutingAndRetry(Fixture):
    ALL = ("understandable_business", "durable_competitive_advantage", "rational_capital_allocation")

    def explanations(self, bad: dict[str, str] | None = None) -> Explanations:
        """A clean set of explanations written by hand (one template per label), with optional raw overrides to inject faults."""
        items = []
        for r in self.score.results:
            from engine.agents.explainer import PLACEHOLDER, render, templated_line
            if r.label in ("not_applicable", "data_gap"):
                t = templated_line(r)
                items.append(Explanation(criterion=r.id, raw=t, text=t, templated=True))
            else:
                raw = (bad or {}).get(r.id, "The result is described here (test: {threshold}).")
                items.append(Explanation(criterion=r.id, raw=raw, text=render(raw, r), placeholders_used=list(dict.fromkeys(PLACEHOLDER.findall(raw)))))
        return Explanations(cik=self.score.cik, ticker="KO", items=items)

    def go(self, llm, *, bad=None, reassess=None, trace=None):
        trace = trace or TraceRecorder("t")
        with mock.patch.object(review, "reassess_criterion", reassess or mock.Mock(side_effect=AssertionError("no qualitative retry expected"))):
            return review.explain_and_verify(self.score, self.qual, retriever=self.retriever, llm=llm, trace=trace, explanations=self.explanations(bad)), trace

    def test_everything_passes_without_retries(self):
        llm = StubLLM(verdicts(*[(c, "yes", [], "ok") for c in self.ALL]))
        res, _ = self.go(llm)
        self.assertEqual(set(res.critic.final.values()), {"passed"})
        self.assertEqual((len(llm.calls), res.critic.llm_calls, res.critic.usage.total_tokens), (1, 1, 110))
        self.assertEqual(res.qual, self.qual)
        self.assertEqual({c.attempt for c in res.critic.checks}, {0})

    def test_explanation_failure_goes_to_the_explainer_only_for_that_item_and_is_rechecked(self):
        retry = _Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue} (test: {threshold}).")])
        llm = StubLLM(verdicts(*[(c, "yes", [], "ok") for c in self.ALL]), retry)
        res, trace = self.go(llm, bad={"G1": "Revenue was 48 billion {made_up}."})
        self.assertEqual(res.critic.final["G1"], "passed_after_retry")
        self.assertEqual(sum(v != "passed" for v in res.critic.final.values()), 1)
        self.assertEqual(llm.requests[1]["model"], "_Out")
        user = llm.requests[1]["messages"][1]["content"]
        self.assertIn("invalid placeholder", user)  # the Critic's message reached the Explainer
        self.assertIn('"criterion": "G1"', user)
        self.assertNotIn('"criterion": "G2"', user)
        self.assertEqual(next(e for e in res.explanations.items if e.criterion == "G1").text, f"Revenue was $47.94 billion (test: {self.score.results[0].threshold}).")
        self.assertEqual([c.attempt for c in res.critic.checks if c.item == "G1" and c.check == "R1"], [0, 1])
        self.assertEqual(res.explanations.llm_calls, 1)  # the retry (this test injected the first set)

    def test_still_failing_explanation_keeps_the_item_with_a_warning_after_exactly_one_retry(self):
        still_bad = _Out(explanations=[_Item(criterion="G1", text="Revenue was 99 billion.")])
        llm = StubLLM(verdicts(*[(c, "yes", [], "ok") for c in self.ALL]), still_bad)
        res, _ = self.go(llm, bad={"G1": "Revenue was 48 billion."})
        self.assertEqual(res.critic.final["G1"], "warning")
        self.assertEqual(len(llm.calls), 2)  # critic, one retry; no second retry
        self.assertEqual(next(e for e in res.explanations.items if e.criterion == "G1").text, "Revenue was 99 billion.")  # kept, not rewritten by the Critic

    def test_banned_language_in_an_explanation_goes_to_the_explainer(self):
        retry = _Out(explanations=[_Item(criterion="G2", text="The balance sheet misses the test (test: {threshold}).")])
        llm = StubLLM(verdicts(*[(c, "yes", [], "ok") for c in self.ALL]), retry)
        res, _ = self.go(llm, bad={"G2": "Investors should avoid this: it looks overvalued."})
        self.assertEqual(res.critic.final["G2"], "passed_after_retry")
        self.assertIn("banned language", llm.requests[1]["messages"][1]["content"])

    def test_qualitative_failure_goes_to_the_agent_with_the_critics_reason_and_the_agents_new_output_is_kept(self):
        old = self.finding("understandable_business")
        new = old.model_copy(update={"rationale": "A shorter rationale that stays within the quotes.", "llm_calls": 2})
        reassess = mock.Mock(return_value=new)
        llm = StubLLM(verdicts(("understandable_business", "overstated", ["Costa retail stores"], "claim not in quotes"),
                               ("durable_competitive_advantage", "yes", [], "ok"), ("rational_capital_allocation", "yes", [], "ok")),
                      verdicts(("understandable_business", "yes", [], "ok")))
        res, _ = self.go(llm, reassess=reassess)
        reassess.assert_called_once()
        self.assertIn("Costa retail stores", reassess.call_args.kwargs["feedback"])
        self.assertEqual(reassess.call_args.args[5], "understandable_business")
        self.assertEqual(res.critic.final["understandable_business"], "passed_after_retry")
        self.assertEqual(next(f for f in res.qual.findings if f.criterion == "understandable_business"), new)
        # the recheck judged only the retried finding
        self.assertEqual(len(llm.requests[1]["messages"][1]["content"].split('"criterion": "understandable_business"')), 2)
        self.assertNotIn("durable_competitive_advantage", llm.requests[1]["messages"][1]["content"])
        # totals include the discarded first attempt
        self.assertEqual(res.qual.totals.llm_calls, self.qual.totals.llm_calls + new.llm_calls)

    def test_critic_never_alters_a_verdict_even_when_it_says_no(self):
        reassess = mock.Mock(side_effect=lambda *a, **k: self.finding(a[5]))  # the agent stands by its finding
        no = ("understandable_business", "no", [], "the quotes do not bear on the criterion")
        llm = StubLLM(verdicts(no, ("durable_competitive_advantage", "yes", [], "ok"), ("rational_capital_allocation", "yes", [], "ok")), verdicts(no))
        res, _ = self.go(llm, reassess=reassess)
        self.assertEqual(reassess.call_count, 1)  # one retry only
        self.assertEqual(res.critic.final["understandable_business"], "warning")
        self.assertEqual([f.verdict for f in res.qual.findings], [f.verdict for f in self.qual.findings])
        self.assertEqual(res.qual.findings, self.qual.findings)

    def test_a_retry_that_ends_not_assessed_is_a_warning_not_a_pass(self):
        gone = self.finding("understandable_business").model_copy(update={"verdict": "not assessed", "stop_reason": "turn_cap", "citations": [], "rationale": "No finding was submitted within 4 turns."})
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "r"), ("durable_competitive_advantage", "yes", [], "ok"), ("rational_capital_allocation", "yes", [], "ok")))
        res, _ = self.go(llm, reassess=mock.Mock(return_value=gone))
        self.assertEqual(res.critic.final["understandable_business"], "warning")
        self.assertIn("turn_cap", next(c.detail for c in res.critic.checks if c.check == "RETRY"))
        self.assertEqual(next(f for f in res.qual.findings if f.criterion == "understandable_business").verdict, "not assessed")  # the agent's output, kept as is

    def test_unsupported_claims_fail_even_when_the_verdict_is_supported(self):
        reassess = mock.Mock(side_effect=lambda *a, **k: self.finding(a[5]))
        llm = StubLLM(verdicts(("understandable_business", "yes", ["a figure not in the quotes"], "adds a figure"),
                               ("durable_competitive_advantage", "yes", [], "ok"), ("rational_capital_allocation", "yes", [], "ok")),
                      verdicts(("understandable_business", "yes", [], "ok")))
        res, _ = self.go(llm, reassess=reassess)
        self.assertEqual(res.critic.final["understandable_business"], "passed_after_retry")

    def test_cost_totals_add_up(self):
        retry = _Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue}.")])
        llm = StubLLM(verdicts(*[(c, "yes", [], "ok") for c in self.ALL]), retry)
        res, _ = self.go(llm, bad={"G1": "Revenue was 48 billion."})
        self.assertEqual(res.critic.llm_calls, 1)  # one critic call; the retry is the Explainers
        self.assertEqual(res.critic.usage.total_tokens, 110 * res.critic.llm_calls)
        self.assertAlmostEqual(res.critic.notional_cost_usd, 0.0001 * res.critic.llm_calls)
        self.assertEqual(res.explanations.usage.total_tokens, 110)

    def test_trace_shows_critic_then_owner_then_recheck_in_order(self):
        reassess = mock.Mock(side_effect=lambda *a, **k: (a[4].note("qualitative/understandable_business", "retry ran"), self.finding(a[5]))[1])
        retry = _Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue}.")])
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "r"), ("durable_competitive_advantage", "yes", [], "ok"), ("rational_capital_allocation", "yes", [], "ok")),
                      retry, verdicts(("understandable_business", "yes", [], "ok")))
        res, trace = self.go(llm, bad={"G1": "Revenue was 48 billion."}, reassess=reassess)
        texts = [(e.agent, str(e.output) + e.input_summary) for e in trace.events]

        def first(pred):
            return next(i for i, (a, t) in enumerate(texts) if pred(a, t))
        i_check0 = first(lambda a, t: a == "critic" and "attempt 0" in t)
        i_route = first(lambda a, t: a == "critic" and "routing" in t)
        i_expl = first(lambda a, t: a == "explainer")
        i_qual = first(lambda a, t: a == "qualitative/understandable_business")
        i_check1 = first(lambda a, t: a == "critic" and "attempt 1" in t)
        i_final = first(lambda a, t: a == "critic" and t.startswith("final"))
        self.assertTrue(i_check0 < i_route < min(i_expl, i_qual) <= max(i_expl, i_qual) < i_check1 < i_final, (i_check0, i_route, i_expl, i_qual, i_check1, i_final))
        self.assertEqual([e.step for e in trace.events], list(range(1, len(trace.events) + 1)))


if __name__ == "__main__":
    unittest.main()
