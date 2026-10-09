"""Guard for the qualitative gold set (ADR-050): the replayed agent still gives the recorded verdicts, and agreement with the
human labels is 17 of 20 with every disagreement over-generous. Refresh the gold set only by deliberate, reviewed edits."""
from __future__ import annotations

import unittest

from eval.qualitative_agreement import agreement, load_gold, replay_findings, verdicts_of


class TestExpectedQualitative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gold = load_gold()
        cls.verdicts = verdicts_of(replay_findings())

    def test_replayed_agent_verdicts_equal_the_recorded_ones(self):
        for t, crits in self.gold["gold"].items():
            for c, rec in crits.items():
                self.assertEqual(self.verdicts[t][c], rec["agent_verdict"], f"{t} {c}")

    def test_agreement_is_17_of_20_and_all_disagreements_are_over_generous(self):
        result = agreement(self.verdicts, self.gold)
        self.assertEqual((result["agree"], result["total"]), (17, 20))
        self.assertEqual({(d["ticker"], d["criterion"]) for d in result["disagreements"]},
                         {("JPM", "rational_capital_allocation"), ("GOOGL", "candid_management"), ("DUK", "rational_capital_allocation")})
        self.assertTrue(all(d["direction"] == "over-generous" for d in result["disagreements"]))

    def test_every_entry_has_a_note_and_the_reviewer_line(self):
        self.assertEqual(self.gold["reviewer"], "Daniel Bravo, reviewed with Claude, 2026-10-10")
        for t, crits in self.gold["gold"].items():
            self.assertEqual(len(crits), 4)
            for rec in crits.values():
                self.assertTrue(rec["note"])


if __name__ == "__main__":
    unittest.main()
