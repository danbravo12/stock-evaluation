"""Explainer: placeholder rendering, formats for every figure key, templated lines, one call, retries (offline, scripted model)."""
from __future__ import annotations

import json
import unittest
from unittest import mock

from engine.agents import explainer
from engine.agents.explainer import _Item, _Out, explain, format_value, load_formats, render, templated_line, usable_keys
from engine.fetch.edgar import EdgarClient
from engine.score import score_ticker
from engine.settings import Settings
from engine.trace import TraceRecorder
from tests.stubs import StubLLM

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]


class TestExplainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = EdgarClient("replay", Settings.from_env())
        cls.scores = {t: score_ticker(client, t) for t in TICKERS}

    def result(self, ticker, cid):
        return next(r for r in self.scores[ticker].results if r.id == cid)

    def test_every_figure_key_of_the_five_fixtures_has_a_format(self):
        formats, known = load_formats(), {"usd_billions", "usd_millions", "ratio_2dp", "percent_1dp", "count", "per_share_usd", "years"}
        keys = {k for s in self.scores.values() for r in s.results for k in r.figures}
        self.assertEqual(sorted(keys - set(formats)), [])
        self.assertTrue(set(formats.values()) <= known)

    def test_formats(self):
        self.assertEqual(format_value(47_941_000_000.0, "usd_billions"), "$47.94 billion")
        self.assertEqual(format_value(-2_251_000_000.0, "usd_billions"), "-$2.25 billion")
        self.assertEqual(format_value(8_779_000_000, "usd_millions"), "$8,779 million")
        self.assertEqual(format_value(1.4587660354, "ratio_2dp"), "1.46")
        self.assertEqual(format_value(0.24886, "percent_1dp"), "24.9%")
        self.assertEqual(format_value(9, "count"), "9")
        self.assertEqual(format_value(2.6566666, "per_share_usd"), "$2.66")
        self.assertEqual(format_value([2016, 2018], "years"), "2016, 2018")
        self.assertEqual(format_value([], "years"), "none")
        with self.assertRaises(ValueError):
            format_value(1, "nope")

    def test_render_fills_figures_and_threshold_and_leaves_invalid_ones(self):
        r = self.result("KO", "G2")
        out = render("A current ratio of {current_ratio} and debt of {long_term_debt} (test: {threshold}); {made_up}.", r)
        self.assertIn("1.46", out)
        self.assertIn("$42.12 billion", out)
        self.assertIn(r.threshold, out)
        self.assertIn("{made_up}", out)

    def test_count_placeholders_render_numbers_not_empty_lists(self):
        g3 = self.result("KO", "G3")
        self.assertEqual(g3.figures["loss_years"], [])
        out = render("With {loss_year_count} loss years and {profit_year_count} profitable ones of {years_on_record}; list: {loss_years}.", g3)
        self.assertEqual(out, "With 0 loss years and 10 profitable ones of 10; list: none.")
        tsla = self.result("TSLA", "G3")
        self.assertEqual(render("{loss_year_count} loss years: {loss_years}", tsla), f"{len(tsla.figures['loss_years'])} loss years: " + ", ".join(str(y) for y in tsla.figures["loss_years"]))
        g4 = self.result("KO", "G4")  # a partial pass has no unpaid_years figure at all
        self.assertNotIn("unpaid_years", g4.figures)
        self.assertEqual(render("{paid_year_count} of {years_on_record} paid, {unpaid_year_count} missed", g4), "15 of 15 paid, 0 missed")
        g4f = self.result("TSLA", "G4")
        self.assertEqual(render("{paid_year_count}+{unpaid_year_count}={years_on_record}", g4f).count("+"), 1)
        b4 = self.result("KO", "B4")
        self.assertEqual(render("{depreciation_only_year_count}", b4), "0")
        self.assertIn("loss_year_count", usable_keys(g3))

    def test_every_derived_key_has_a_format_and_none_collides_with_a_real_figure(self):
        formats = load_formats()
        derived = {"loss_year_count", "profit_year_count", "unpaid_year_count", "paid_year_count", "depreciation_only_year_count"}
        self.assertTrue(derived <= set(formats))
        self.assertEqual({formats[k] for k in derived}, {"count"})
        self.assertEqual(derived & {k for s in self.scores.values() for r in s.results for k in r.figures}, set())

    def test_the_v2_prompt_teaches_counts_and_is_not_active_until_the_re_record(self):
        from engine.prompts import active
        self.assertEqual(active("explainer"), "v1")  # fixtures were recorded with v1
        self.assertEqual(explainer.system_prompt(), explainer.SYSTEM_PROMPT)
        self.assertIn("{loss_year_count}", explainer.SYSTEM_PROMPT_V2)
        self.assertNotIn("{loss_year_count}", explainer.SYSTEM_PROMPT)
        with mock.patch.object(explainer, "active_prompt", lambda name: "v2"):
            self.assertEqual(explainer.system_prompt(), explainer.SYSTEM_PROMPT_V2)

    def test_none_figures_are_not_offered_as_placeholders(self):
        r = self.result("TSLA", "G5")
        self.assertIsNone(r.figures["ratio"])
        self.assertNotIn("ratio", usable_keys(r))
        self.assertIn("avg_eps_end", usable_keys(r))

    def test_templated_lines_for_not_applicable_and_data_gap(self):
        self.assertEqual(templated_line(self.result("JPM", "G2")), "Not applicable to this company: bank (ADR-013).")
        self.assertEqual(templated_line(self.result("KO", "G6")), "Cannot be scored: price not available (Finnhub, ADR-007).")

    def test_one_call_covers_only_pass_fail_partial_not_meaningful(self):
        s = self.scores["JPM"]
        pf = [r.id for r in s.results if r.label in ("pass", "fail", "partial_pass", "not_meaningful")]
        out = _Out(explanations=[_Item(criterion=i, text="Described with {threshold}.") for i in pf])
        llm = StubLLM(out)
        trace = TraceRecorder("t")
        e = explain(s, llm, trace)
        self.assertEqual(len(llm.calls), 1)
        sent = json.loads(llm.requests[0]["messages"][1]["content"].split("explain:\n", 1)[1])
        self.assertEqual([c["criterion"] for c in sent], pf)
        self.assertEqual([x.criterion for x in e.items], [r.id for r in s.results])  # ScoreSet order, templated ones included
        self.assertTrue(all(x.templated for x in e.items if x.criterion in ("G2", "G6", "G7", "B2", "B3", "B4")))
        self.assertEqual((e.llm_calls, e.usage.total_tokens), (1, 110))
        self.assertTrue(all("{" not in x.text for x in e.items))

    def test_figures_shown_to_the_model_are_formatted_and_none_is_withheld(self):
        s = self.scores["TSLA"]
        out = _Out(explanations=[_Item(criterion=r.id, text="x {threshold}") for r in s.results if r.label in explainer.LLM_LABELS])
        llm = StubLLM(out)
        explain(s, llm, TraceRecorder("t"))
        sent = json.loads(llm.requests[0]["messages"][1]["content"].split("explain:\n", 1)[1])
        g5 = next(c for c in sent if c["criterion"] == "G5")
        self.assertNotIn("ratio", g5["placeholders"])
        self.assertEqual(g5["placeholders"]["avg_eps_end"], "$2.47")

    def test_retry_sends_only_failed_ids_with_the_critics_message(self):
        s = self.scores["KO"]
        llm = StubLLM(_Out(explanations=[_Item(criterion="G1", text="Revenue was {revenue} (test: {threshold}).")]))
        e = explain(s, llm, TraceRecorder("t"), only={"G1"}, feedback={"G1": "stray numeral 47"})
        user = llm.requests[0]["messages"][1]["content"]
        self.assertIn("stray numeral 47", user)
        self.assertEqual([c["criterion"] for c in json.loads(user.split("explain:\n", 1)[1].split("\n\nA reviewer", 1)[0])], ["G1"])
        self.assertEqual([x.criterion for x in e.items], ["G1"])
        self.assertEqual(e.items[0].placeholders_used, ["revenue", "threshold"])

    def test_no_model_call_when_everything_is_templated(self):
        s = self.scores["KO"]
        llm = StubLLM()
        e = explain(s, llm, TraceRecorder("t"), only={"G6", "G7"})
        self.assertEqual((len(llm.calls), e.llm_calls, [x.templated for x in e.items]), (0, 0, [True, True]))

    def test_a_criterion_the_model_skipped_is_simply_missing_for_the_critic_to_flag(self):
        s = self.scores["KO"]
        e = explain(s, StubLLM(_Out(explanations=[_Item(criterion="G1", text="{revenue}")])), TraceRecorder("t"), only={"G1", "G2"})
        self.assertEqual([x.criterion for x in e.items], ["G1"])


if __name__ == "__main__":
    unittest.main()
