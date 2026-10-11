"""Critic: rule checks with injected faults, the model check's inputs, routing, retry once, gate-not-author (offline, scripted model)."""
from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from engine.agents import review
from engine.agents.critic import (CriticVerdicts, ExplanationCheck, FindingCheck, banned_hits, check_citations, check_explanation, llm_payload, load_rubric,
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
        f = self.finding("understandable_business")  # KO: a "found" verdict, so the definitions are those of found and weak
        self.assertEqual(f.verdict, "evidence found")
        p = llm_payload([f], load_rubric())[0]
        self.assertEqual(sorted(p), ["claimed_verdict", "criterion", "definition_of_claimed_verdict", "definition_of_the_verdict_below", "question", "quotes", "rationale"])
        rubric = load_rubric()["understandable_business"]
        self.assertEqual((p["definition_of_claimed_verdict"], p["definition_of_the_verdict_below"]), (rubric["found_means"], rubric["weak_means"]))
        self.assertEqual(p["quotes"], [c.quote for c in f.citations])


def verdicts(*items, ex=()):
    return CriticVerdicts(checks=[FindingCheck(criterion=c, supports_verdict=v, unsupported_claims=u, reason=r) for c, v, u, r in items],
                          explanation_checks=[ExplanationCheck(criterion=c, agrees_with_label=a, reads_correctly=b, reason=r) for c, a, b, r in ex])


class TestRoutingAndRepair(Fixture):
    ALL = ("understandable_business", "durable_competitive_advantage", "rational_capital_allocation")

    def good(self):
        return [(c, "yes", [], "ok") for c in self.ALL]

    def explanations(self, bad: dict[str, str] | None = None) -> Explanations:
        """Hand-written explanations (one template per label) with optional raw overrides to inject faults."""
        from engine.agents.explainer import PLACEHOLDER, render, templated_line
        items = []
        for r in self.score.results:
            if r.label in ("not_applicable", "data_gap"):
                t = templated_line(r)
                items.append(Explanation(criterion=r.id, raw=t, text=t, templated=True))
            else:
                raw = (bad or {}).get(r.id, "The result is described here (test: {threshold}).")
                items.append(Explanation(criterion=r.id, raw=raw, text=render(raw, r), placeholders_used=list(dict.fromkeys(PLACEHOLDER.findall(raw)))))
        return Explanations(cik=self.score.cik, ticker="KO", items=items)

    def go(self, llm, *, bad=None, retry=None, rewrite=None, trace=None):
        trace = trace or TraceRecorder("t")
        no_retry = mock.Mock(side_effect=AssertionError("no constrained retry expected"))
        no_rewrite = mock.Mock(side_effect=AssertionError("no rationale rewrite expected"))
        self.retry, self.rewrite = retry or no_retry, rewrite or no_rewrite
        with mock.patch.object(review, "constrained_retry", self.retry), mock.patch.object(review, "rewrite_rationale", self.rewrite):
            return review.explain_and_verify(self.score, self.qual, retriever=self.retriever, llm=llm, trace=trace, explanations=self.explanations(bad)), trace

    def orig(self, name):
        return self.finding(name)

    def test_everything_passes_without_repairs(self):
        llm = StubLLM(verdicts(*self.good()))
        res, _ = self.go(llm)
        self.assertEqual(set(res.critic.final.values()), {"passed"})
        self.assertEqual((len(llm.calls), res.critic.llm_calls, res.critic.repairs), (1, 1, []))
        self.assertEqual(res.qual, self.qual)
        self.assertEqual({c.attempt for c in res.critic.checks}, {0})
        sent = llm.requests[0]["messages"][1]["content"]
        self.assertIn('"explanations"', sent)  # explanations and findings go to the model in the same call

    def test_explanation_rule_failure_goes_to_the_explainer_for_that_item_only_and_is_rechecked(self):
        retry = _Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue} (test: {threshold}).")])
        llm = StubLLM(verdicts(*self.good()), retry, verdicts())
        res, _ = self.go(llm, bad={"G1": "Revenue was 48 billion {made_up}."})
        self.assertEqual(res.critic.final["G1"], "passed_after_retry")
        self.assertEqual(sum(v != "passed" for v in res.critic.final.values()), 1)
        self.assertEqual(llm.requests[1]["model"], "_Out")
        user = llm.requests[1]["messages"][1]["content"]
        self.assertIn("invalid placeholder", user)
        self.assertIn('"criterion": "G1"', user)
        self.assertNotIn('"criterion": "G2"', user)
        self.assertEqual([c.attempt for c in res.critic.checks if c.item == "G1" and c.check == "R1"], [0, 1])
        self.assertEqual([(r.item, r.path, r.outcome) for r in res.critic.repairs], [("G1", "explanation_retry", "accepted")])

    def test_explanation_meaning_failure_from_the_model_check_routes_to_the_explainer(self):
        retry = _Out(explanations=[_Item(criterion="G2", text="The balance sheet misses the test (test: {threshold}).")])
        bad = ("G2", "no", "yes", "says pass for a fail")
        llm = StubLLM(verdicts(*self.good(), ex=[bad]), retry, verdicts(ex=[("G2", "yes", "yes", "ok")]))
        res, _ = self.go(llm)
        self.assertEqual(res.critic.final["G2"], "passed_after_retry")
        self.assertIn("agrees_with_label=no", llm.requests[1]["messages"][1]["content"])
        self.assertIn("G2", llm.requests[2]["messages"][1]["content"])  # the re-check reviews the new text
        self.assertEqual(res.critic.llm_calls, 2)

    def test_reads_correctly_failure_also_routes_to_the_explainer(self):
        retry = _Out(explanations=[_Item(criterion="B4", text="Owner earnings (test: {threshold}).")])
        llm = StubLLM(verdicts(*self.good(), ex=[("B4", "yes", "no", "wrong term")]), retry, verdicts(ex=[("B4", "yes", "yes", "ok")]))
        res, _ = self.go(llm)
        self.assertEqual(res.critic.final["B4"], "passed_after_retry")

    def test_banned_language_in_an_explanation_goes_to_the_explainer(self):
        retry = _Out(explanations=[_Item(criterion="G2", text="The balance sheet misses the test (test: {threshold}).")])
        llm = StubLLM(verdicts(*self.good()), retry, verdicts())
        res, _ = self.go(llm, bad={"G2": "Investors should avoid this: it looks overvalued."})
        self.assertEqual(res.critic.final["G2"], "passed_after_retry")
        self.assertIn("banned language", llm.requests[1]["messages"][1]["content"])

    def test_verdict_failure_goes_to_the_constrained_retry_and_rationale_only_failure_to_the_rewrite(self):
        lower = self.orig("understandable_business").model_copy(update={"verdict": "evidence weak", "rationale": "Weaker, within the quotes.", "llm_calls": 2})
        retry = mock.Mock(return_value=(lower, "submitted"))
        rewrite = mock.Mock(return_value="A rationale that stays within the quotes.")
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "needs more specifics"),
                               ("durable_competitive_advantage", "yes", ["a claim not in the quotes"], "adds a claim"),
                               ("rational_capital_allocation", "yes", [], "ok")),
                      verdicts(("understandable_business", "yes", [], "ok"), ("durable_competitive_advantage", "yes", [], "ok")))
        res, _ = self.go(llm, retry=retry, rewrite=rewrite)
        retry.assert_called_once()
        self.assertEqual(retry.call_args.args[5].criterion, "understandable_business")
        self.assertIn("needs more specifics", retry.call_args.kwargs["reason"])
        rewrite.assert_called_once()
        self.assertEqual(rewrite.call_args.args[0].criterion, "durable_competitive_advantage")
        self.assertIn("a claim not in the quotes", " ".join(rewrite.call_args.args[2]))
        final = {f.criterion: f for f in res.qual.findings}
        self.assertEqual(final["understandable_business"], lower)  # the agent's lower verdict, kept as it is
        d = final["durable_competitive_advantage"]
        self.assertEqual((d.rationale, d.verdict, d.citations), ("A rationale that stays within the quotes.", self.orig("durable_competitive_advantage").verdict, self.orig("durable_competitive_advantage").citations))
        self.assertEqual({r.item: (r.path, r.outcome) for r in res.critic.repairs},
                         {"understandable_business": ("constrained_retry", "accepted"), "durable_competitive_advantage": ("rationale_rewrite", "accepted")})
        self.assertEqual(res.critic.final["understandable_business"], "passed_after_retry")
        self.assertEqual(res.critic.final["durable_competitive_advantage"], "passed_after_retry")
        self.assertEqual(res.critic.llm_calls, 2)

    def test_a_rewrite_that_still_fails_keeps_the_original_rationale_and_warns(self):
        rewrite = mock.Mock(return_value="Another rationale with the same problem.")
        llm = StubLLM(verdicts(("understandable_business", "yes", ["Costa retail stores"], "claim not in quotes"), *self.good()[1:]),
                      verdicts(("understandable_business", "yes", ["Costa retail stores"], "still there")))
        res, _ = self.go(llm, rewrite=rewrite)
        f = next(x for x in res.qual.findings if x.criterion == "understandable_business")
        self.assertEqual(f.rationale, self.orig("understandable_business").rationale)  # original kept
        self.assertEqual(res.critic.final["understandable_business"], "warning")
        self.assertEqual(res.critic.repairs[0].outcome, "rejected_by_recheck")
        self.assertEqual(rewrite.call_count, 1)  # one repair only

    def test_a_failed_constrained_retry_keeps_the_original_finding_and_warns_and_the_critic_never_alters_a_verdict(self):
        for outcome in ("not_submitted", "no_change"):
            gone = self.orig("understandable_business").model_copy(update={"verdict": "not assessed", "stop_reason": "turn_cap", "citations": [], "rationale": "No finding.", "llm_calls": 3, "tool_calls": 2})
            retry = mock.Mock(return_value=(gone, outcome))
            llm = StubLLM(verdicts(("understandable_business", "no", [], "off topic"), *self.good()[1:]))
            res, _ = self.go(llm, retry=retry)
            kept = next(x for x in res.qual.findings if x.criterion == "understandable_business")
            self.assertEqual((kept.verdict, kept.citations, kept.rationale), (self.orig("understandable_business").verdict, self.orig("understandable_business").citations, self.orig("understandable_business").rationale))
            self.assertEqual(res.critic.final["understandable_business"], "warning")
            self.assertEqual(res.critic.repairs[0].outcome, outcome)
            self.assertIn(outcome, next(c.detail for c in res.critic.checks if c.check == "RETRY"))
            self.assertEqual(kept.llm_calls, self.orig("understandable_business").llm_calls + 3)  # the dropped attempt still counts

    def test_a_retry_that_fails_the_recheck_is_dropped_and_its_cost_still_counts(self):
        lower = self.orig("understandable_business").model_copy(update={"verdict": "evidence weak", "llm_calls": 2})
        retry = mock.Mock(return_value=(lower, "submitted"))
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "r"), *self.good()[1:]), verdicts(("understandable_business", "overstated", [], "still")))
        res, _ = self.go(llm, retry=retry)
        kept = next(x for x in res.qual.findings if x.criterion == "understandable_business")
        self.assertEqual(kept.verdict, self.orig("understandable_business").verdict)
        self.assertEqual(kept.llm_calls, self.orig("understandable_business").llm_calls + 2)
        self.assertEqual(res.critic.final["understandable_business"], "warning")
        self.assertEqual(res.qual.totals.llm_calls, self.qual.totals.llm_calls + 2)

    def test_cost_totals_add_up(self):
        lower = self.orig("understandable_business").model_copy(update={"verdict": "evidence weak", "llm_calls": 2})
        retry = mock.Mock(return_value=(lower, "submitted"))
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "r"), *self.good()[1:]), verdicts(("understandable_business", "yes", [], "ok")))
        res, _ = self.go(llm, retry=retry)
        self.assertEqual(res.critic.llm_calls, 2)
        self.assertEqual(res.critic.usage.total_tokens, 220)
        self.assertAlmostEqual(res.critic.notional_cost_usd, 0.0002)
        self.assertEqual(res.qual.totals.llm_calls, self.qual.totals.llm_calls + 2)  # original loop + the retry

    def test_trace_shows_critic_then_owner_then_recheck_in_order(self):
        retry_expl = _Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue}.")])
        lower = self.orig("understandable_business").model_copy(update={"verdict": "evidence weak"})

        def fake_retry(*a, **k):
            a[4].note("qualitative/understandable_business", "retry ran")
            return lower, "submitted"
        llm = StubLLM(verdicts(("understandable_business", "overstated", [], "r"), *self.good()[1:]), retry_expl, verdicts(("understandable_business", "yes", [], "ok")))
        res, trace = self.go(llm, bad={"G1": "Revenue was 48 billion."}, retry=mock.Mock(side_effect=fake_retry))
        texts = [(e.agent, str(e.output) + e.input_summary) for e in trace.events]

        def first(pred):
            return next(i for i, (a, t) in enumerate(texts) if pred(a, t))
        i0 = first(lambda a, t: a == "critic" and "attempt 0" in t)
        i_route = first(lambda a, t: a == "critic" and "routing" in t)
        i_expl = first(lambda a, t: a == "explainer")
        i_qual = first(lambda a, t: a == "qualitative/understandable_business")
        i1 = first(lambda a, t: a == "critic" and "attempt 1" in t)
        i_final = first(lambda a, t: a == "critic" and t.startswith("final"))
        self.assertTrue(i0 < i_route < min(i_expl, i_qual) <= max(i_expl, i_qual) < i1 < i_final, (i0, i_route, i_expl, i_qual, i1, i_final))
        self.assertEqual([e.step for e in trace.events], list(range(1, len(trace.events) + 1)))


class TestRewriteAndBudget(Fixture):
    def test_the_rewrite_sees_only_the_question_the_verdict_the_quotes_and_the_problems(self):
        from engine.agents.repair import _Rewrite, rewrite_rationale
        f = self.finding("understandable_business")
        llm = StubLLM(_Rewrite(rationale="Within the quotes."))
        out = rewrite_rationale(f, "Q?", ["claim X is not in the quotes"], llm, TraceRecorder("t"), "KO")
        self.assertEqual(out, "Within the quotes.")
        user = llm.requests[0]["messages"][1]["content"]
        self.assertEqual(sorted(json.loads(user)), ["problems_with_the_old_rationale", "question", "quotes", "verdict"])
        self.assertNotIn(f.rationale, user)  # the old rationale is not shown
        self.assertEqual(llm.requests[0]["kwargs"]["agent"], "qualitative/understandable_business/rewrite")
        self.assertEqual(json.loads(user)["quotes"], [c.quote for c in f.citations])

    def test_an_empty_or_long_rewrite_is_refused(self):
        from engine.agents.repair import _Rewrite, rewrite_rationale
        f = self.finding("understandable_business")
        for text in ("", "word " * 81):
            self.assertIsNone(rewrite_rationale(f, "Q?", [], StubLLM(_Rewrite(rationale=text)), TraceRecorder("t"), "KO"))

    def test_budget_cap_is_six_dollars(self):
        from engine.llm.client import load_models_config
        self.assertEqual(load_models_config()["budget"]["total_usd_cap"], 6.0)


if __name__ == "__main__":
    unittest.main()
