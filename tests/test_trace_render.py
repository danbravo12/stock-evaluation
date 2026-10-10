"""Plain-language trace rendering (ADR-067), the Critic's sentences, plurals and display names. Offline, on the 5 recorded traces."""
from __future__ import annotations

import json
import re
import unittest

from engine.fetch.edgar import EdgarClient
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT, Settings
from engine.trace_render import LANES, critic_notes, handoff, money, plural, render_trace
from engine.universe import display_name

SAMPLES = {"KO": "0000021344", "JPM": "0000019617", "GOOGL": "0001652044", "TSLA": "0001318605", "DUK": "0001326160"}
RAW = re.compile(r'\{"|\[\d|=|\[|\]|\{|\}')


def load(cik):
    events = [json.loads(l) for l in (REPO_ROOT / "results" / f"{cik}.trace.jsonl").read_text().splitlines() if l.strip()]
    return events, json.loads((REPO_ROOT / "results" / f"{cik}.json").read_text())


class TestRenderers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rendered = {t: render_trace(*load(c)) for t, c in SAMPLES.items()}

    def test_every_event_of_every_recorded_trace_has_a_renderer(self):
        for t, c in SAMPLES.items():
            events, _ = load(c)
            r = self.rendered[t]
            self.assertEqual(len(r["steps"]), len(events), t)
            self.assertTrue(all(s["kind"] != "unknown" and s["title"] for s in r["steps"]), t)

    def test_no_raw_json_or_key_value_text_in_titles_or_details(self):
        for t, r in self.rendered.items():
            for s in r["steps"]:
                self.assertIsNone(RAW.search(s["title"]), f"{t} step {s['n']}: {s['title']}")
                for d in s["details"]:
                    self.assertNotIn('{"', d, f"{t} step {s['n']}")
                    self.assertIsNone(re.search(r"\b[a-z_]{3,}=\S", d), f"{t} step {s['n']}: {d}")

    def test_titles_for_the_main_event_types(self):
        events, res = load(SAMPLES["JPM"])
        steps = {s["n"]: s for s in render_trace(events, res)["steps"]}
        self.assertEqual(steps[1]["title"], "Planned the run for JPM")
        self.assertIn("Tests that do not apply to this kind of company: G2, B2, B3, B4.", steps[1]["details"])
        self.assertEqual(steps[31]["title"], 'Planned: search Item 7 first, starting queries: "share repurchases buyback", "dividends", "acquisitions", and others')
        self.assertEqual(steps[32]["title"], 'Searched Item 7 for "share repurchases buyback", "dividends", "acquisitions", and others: 4 passages')
        self.assertEqual(steps[33]["title"], "Model call 1 for rational capital allocation: 2,374 tokens in, 199 out, ~$0.0009 at paid rates")
        self.assertEqual(steps[9]["title"], "Pointer check: rejected, a citation covered more than three sentences")
        self.assertEqual(steps[12]["title"], "Pointer check: quote built from the filing and verified")
        self.assertEqual(steps[13]["title"], "Model submitted: evidence found, citing passage 7:56 sentences 4 to 6; passage 7:72 sentences 1 to 2")
        self.assertEqual(steps[34]["title"], "Model submission malformed: it gave more than 2 citations")
        self.assertEqual(steps[41]["title"], "Explainer wrote 11 lines; figures filled in by code from the scorecard")
        self.assertEqual(steps[43]["title"], "Critic: explanation check passed for 11 items")
        self.assertEqual(steps[47]["title"], "Critic: second-model review found 2 problems in 7 items")
        self.assertEqual(steps[48]["title"], "Critic sent 2 findings back for repair")
        self.assertEqual(steps[49]["title"].split(":")[0], "Rationale rewrite for understandable business")

    def test_the_submitted_step_shows_the_built_quote(self):
        events, res = load(SAMPLES["KO"])
        sub = [s for s in render_trace(events, res)["steps"] if s["title"].startswith("Model submitted")]
        self.assertEqual(len(sub), 4)
        self.assertTrue(all(s["quote"] for s in sub))
        self.assertIn("Our finished product operations generate net operating revenues", sub[0]["quote"])

    def test_the_critic_objection_is_a_sentence(self):
        events, res = load(SAMPLES["KO"])
        step = next(s for s in render_trace(events, res)["steps"] if s["title"].startswith("Critic: second-model review found"))
        self.assertEqual(step["details"], ["The Critic objected to the understandable business rationale: it says \"It also notes direct-to-consumer sales through Costa retail stores\", which the quoted sentences don't show."])

    def test_hand_offs_are_only_the_real_ones(self):
        for t, r in self.rendered.items():
            lanes = [g["lane"] for g in r["groups"]]
            for prev, g in zip([None] + r["groups"], r["groups"]):
                if prev is None:
                    self.assertIsNone(g["handoff"])
                elif prev["lane"] == g["lane"]:
                    self.assertIsNone(g["handoff"], f"{t}: no hand-off between two loops of the same agent")
                else:
                    self.assertTrue(g["handoff"].startswith("Hand-off: "), t)
            self.assertEqual(lanes[:2], ["orchestrator", "scorers"], t)
            self.assertEqual(lanes[-1], "reporter", t)
        ko = [g["handoff"] for g in self.rendered["KO"]["groups"] if g["handoff"]]
        self.assertEqual(len(ko), 9)
        self.assertIn("the Critic sends the findings that failed back", ko[5])
        self.assertIn("the repaired findings go back to the Critic", ko[6])
        self.assertEqual(handoff("critic", "reporter"), "Hand-off: critic hands over to reporter.")

    def test_group_summaries_and_repairs(self):
        groups = {g["title"]: g for g in self.rendered["KO"]["groups"]}
        self.assertEqual(groups["Rational capital allocation"]["summary"], "1 search, 1 model call, evidence found, 2 citations")
        self.assertEqual(groups["Durable competitive advantage"]["summary"], "2 searches, 2 model calls, evidence found, 1 citation")
        jpm = self.rendered["JPM"]["groups"]
        self.assertEqual([g["title"] for g in jpm if g["repair"]], ["Repair: Understandable business", "Repair: Rational capital allocation"])
        self.assertTrue(all(g["steps"] for g in jpm))
        self.assertEqual(sorted(n for g in jpm for n in g["steps"]), list(range(1, len(self.rendered["JPM"]["steps"]) + 1)))

    def test_running_totals_end_at_the_result_cost(self):
        for t, c in SAMPLES.items():
            _, res = load(c)
            last = self.rendered[t]["steps"][-1]["total"]
            self.assertEqual(last["calls"], res["cost"]["llm_calls"], t)
            self.assertAlmostEqual(last["cost_usd"], res["cost"]["notional_cost_usd"], places=5, msg=t)

    def test_lanes_are_the_six_agents_in_order(self):
        self.assertEqual([l for l, _ in LANES], ["orchestrator", "scorers", "qualitative", "explainer", "critic", "reporter"])

    def test_with_the_recorded_filing_each_search_lists_its_passages(self):
        client = EdgarClient("replay", Settings.from_env())
        retriever = Retriever(client)
        events, res = load(SAMPLES["KO"])
        steps = render_trace(events, res, retriever=retriever, cik=SAMPLES["KO"])["steps"]
        seeded = next(s for s in steps if s["kind"] == "search")
        self.assertEqual(len([d for d in seeded["details"] if d.startswith("Passage")]), 4)
        self.assertTrue(any(d.startswith("Passage 1:8: Our finished product operations") for d in seeded["details"]))
        self.assertTrue(all(len(d.split()) <= 26 for d in seeded["details"] if d.startswith("Passage")))
        model_search = next(s for s in steps if s["kind"] == "search" and "The model chose this search itself." in s["details"])
        self.assertRegex(model_search["title"], r": \d passages?$")


class TestCriticSentences(unittest.TestCase):
    def test_sentences_not_key_values(self):
        for t, c in SAMPLES.items():
            _, res = load(c)
            n = critic_notes(res)
            for item, v in n["critic"].items():
                for sentence in v["sentences"] + [v["status"]] + ([v["ran"]] if v["ran"] else []):
                    self.assertIsNone(re.search(r"supports_verdict|\w=\w|\{", sentence), f"{t} {item}: {sentence}")

    def test_repaired_rationale_in_words(self):
        _, res = load(SAMPLES["KO"])
        v = critic_notes(res)["critic"]["understandable_business"]
        self.assertEqual(v["status"], "Passed after one repair")
        self.assertEqual(v["sentences"], ["The Critic objected to the understandable business rationale: it says \"It also notes direct-to-consumer sales through Costa retail stores\", which the quoted sentences don't show.",
                                          "The rationale was rewritten from the quotes and passed the re-check."])
        self.assertTrue(v["objected"])
        plain = critic_notes(res)["critic"]["G1"]
        self.assertEqual((plain["status"], plain["objected"]), ("Passed all checks", False))

    def test_verdict_objection_in_words(self):
        _, res = load(SAMPLES["JPM"])
        v = critic_notes(res)["critic"]["rational_capital_allocation"]
        self.assertTrue(v["sentences"][0].startswith("The Critic objected to the rational capital allocation verdict: the quoted sentences don't fully support it"))
        self.assertIn("The agent was asked to cite something new or lower its verdict and passed the re-check.", v["sentences"])

    def test_agent_and_cost_sentences_use_real_plurals(self):
        _, res = load(SAMPLES["KO"])
        n = critic_notes(res)
        self.assertEqual(n["cost"], "The agents made 10 model calls and read 21,797 tokens, writing 2,120. On the free tier that cost $0.00; at paid rates it would have cost about $0.0086.")
        self.assertRegex(n["qualitative"]["rational_capital_allocation"], r"^The agent made 1 model call and \d+ tool calls?, including 1 search of the filing")
        self.assertIn("2 searches", n["qualitative"]["durable_competitive_advantage"])


class TestSmallHelpers(unittest.TestCase):
    def test_plural_and_money(self):
        self.assertEqual((plural(1, "search", "searches"), plural(2, "search", "searches"), plural(0, "model call"), plural(1500, "token")), ("1 search", "2 searches", "0 model calls", "1,500 tokens"))
        self.assertEqual((money(0.00071), money(0.00001), money(0.0), money(None)), ("$0.0007", "under $0.0001", "$0.0000", "no cost recorded"))

    def test_display_names(self):
        self.assertEqual(display_name("Coca-Cola Company (The)"), "The Coca-Cola Company")
        self.assertEqual(display_name("Walt Disney Company (The)"), "The Walt Disney Company")
        self.assertEqual(display_name("Apple Inc."), "Apple Inc.")
        self.assertEqual(display_name("Brown–Forman"), "Brown–Forman")

    def test_the_rankings_use_display_names_and_the_csv_keeps_the_raw_value(self):
        rk = json.loads((REPO_ROOT / "site_data" / "rankings.json").read_text())
        rows = rk["criteria_ranking"]["ranked"] + rk["criteria_ranking"]["insufficient_data"]
        self.assertFalse([r["name"] for r in rows if r["name"].endswith("(The)")])
        self.assertIn("The Coca-Cola Company", [r["name"] for r in rows])
        csv_text = next((REPO_ROOT / "data" / "universe").glob("sp500_*.csv")).read_text(encoding="utf-8")
        self.assertIn("Coca-Cola Company (The)", csv_text)


if __name__ == "__main__":
    unittest.main()
