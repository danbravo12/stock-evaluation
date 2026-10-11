"""Explainer + Critic on the 5 real companies from recorded responses (replay, zero network). Structure and the recorded Critic scorecard."""
from __future__ import annotations

import importlib.util
import json
import unittest

from engine.agents.critic import check_explanation, banned_hits, llm_check, llm_failed
from engine.agents.review import explain_and_verify
from engine.fetch.edgar import EdgarClient
from engine.llm.client import LLMClient
from engine.retrieve import Retriever
from engine.score import score_ticker
from engine.settings import REPO_ROOT, Settings
from engine.trace import TraceRecorder
from eval.qualitative_agreement import RANK, agreement, load_gold, replay_findings, verdicts_of

TICKERS = json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"]


class TestCriticFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = Settings.from_env()
        edgar = EdgarClient("replay", settings)
        cls.retriever = Retriever(edgar)
        cls.findings = replay_findings(None, cls.retriever, LLMClient("replay", settings))
        cls.llm = LLMClient("replay", settings)
        cls.scores = {t: score_ticker(edgar, t) for t in TICKERS}
        cls.trace = TraceRecorder("fixtures")
        cls.results = {t: explain_and_verify(cls.scores[t], cls.findings[t], retriever=cls.retriever, llm=cls.llm, trace=cls.trace) for t in TICKERS}
        spec = importlib.util.spec_from_file_location("review_report", REPO_ROOT / "scripts" / "review_report.py")
        cls.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.script)

    def test_every_criterion_has_one_explanation_in_scoreset_order(self):
        for t, r in self.results.items():
            self.assertEqual([e.criterion for e in r.explanations.items], [x.id for x in self.scores[t].results], t)

    def test_explanations_that_passed_have_no_stray_numbers_or_banned_words(self):
        for t, r in self.results.items():
            by_id = {x.id: x for x in self.scores[t].results}
            for e in r.explanations.items:
                if r.critic.final[e.criterion] != "warning":
                    self.assertEqual(check_explanation(by_id[e.criterion], e), [], (t, e.criterion))
                    self.assertEqual(banned_hits(e.text), [], (t, e.criterion))
                self.assertNotIn("{", e.text if r.critic.final[e.criterion] != "warning" else "")

    def test_citation_rule_passes_on_every_real_finding(self):
        for t, r in self.results.items():
            bad = [c for c in r.critic.checks if c.check == "R2" and c.status == "fail"]
            self.assertEqual(bad, [], t)

    def test_the_critic_never_changes_a_finding_it_did_not_send_back(self):
        for t, r in self.results.items():
            before = {f.criterion: f for f in self.findings[t].findings}
            for f in r.qual.findings:
                if r.critic.final[f.criterion] == "passed":
                    self.assertEqual(f, before[f.criterion], (t, f.criterion))

    def test_final_statuses_follow_the_checks(self):
        for t, r in self.results.items():
            first = {c.item for c in r.critic.checks if c.attempt == 0 and c.status == "fail"}
            again = {c.item for c in r.critic.checks if c.attempt == 1 and c.status == "fail"}
            for item, status in r.critic.final.items():
                self.assertEqual(status, "warning" if item in again else "passed_after_retry" if item in first else "passed", (t, item))

    def test_fault_injection_cases_are_all_flagged(self):
        faults = self.script.fault_cases(self.findings)
        self.assertEqual(len(faults), 3)
        for desc, f in faults:
            check = llm_check([f], self.llm, "KO" if "KO" in desc else "TSLA")[0]
            self.assertTrue(llm_failed(check), (desc, check))

    def test_recorded_scorecard_what_the_critic_flagged_of_the_gold_set_disagreements(self):
        """Measured with prompt v2.1 (build 4a): of the three over-generous disagreements the Critic's first pass flagged one (TSLA capital allocation, which stays 'found' with a
        visible Critic warning after its repair). With prompt v2 it flagged one of four, with v1 all three. Frozen here so a change shows up."""
        gold = load_gold()
        flagged = {(t, c.item) for t, r in self.results.items() for c in r.critic.checks if c.attempt == 0 and c.status == "fail"}
        over = {(t, crit) for t, crits in gold["gold"].items() for crit, rec in crits.items()
                if rec["agent_verdict"] != rec["human_verdict"] and RANK[rec["agent_verdict"]] > RANK[rec["human_verdict"]]}
        self.assertEqual(over, {("KO", "candid_management"), ("GOOGL", "durable_competitive_advantage"), ("TSLA", "rational_capital_allocation")})
        self.assertEqual(over & flagged, {("TSLA", "rational_capital_allocation")})
        after = agreement({t: {f.criterion: f.verdict for f in r.qual.findings} for t, r in self.results.items()}, gold)
        self.assertEqual(after["total"], 20)
        print(f"\nCritic: agent-only {agreement(verdicts_of(self.findings), gold)['agree']}/20 -> after the Critic {after['agree']}/20")

    def test_replay_made_no_network_calls_and_cost_nothing(self):
        self.assertTrue(self.llm.calls)
        self.assertTrue(all(c.replayed and c.actual_cost_usd == 0.0 for c in self.llm.calls))
        for r in self.results.values():
            self.assertEqual(r.critic.actual_cost_usd, 0.0)
            self.assertEqual(r.explanations.llm_calls, 1)


if __name__ == "__main__":
    unittest.main()
