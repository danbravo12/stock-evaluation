"""Guard for the qualitative gold set (ADR-050): the replayed agent still gives the recorded verdicts, and agreement with the
human labels is 19 of 20 (two capital-allocation labels were revised under the ADR-052 rubric, see label_history). Refresh the gold set only by deliberate, reviewed edits."""
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

    def test_agreement_is_19_of_20_and_the_one_disagreement_is_over_generous(self):
        result = agreement(self.verdicts, self.gold)
        self.assertEqual((result["agree"], result["total"]), (19, 20))
        self.assertEqual({(d["ticker"], d["criterion"]) for d in result["disagreements"]}, {("GOOGL", "candid_management")})
        self.assertTrue(all(d["direction"] == "over-generous" for d in result["disagreements"]))

    def test_every_changed_label_has_a_dated_history_entry_with_a_reason(self):
        changed = 0
        for t, crits in self.gold["gold"].items():
            for c, rec in crits.items():
                for h in rec.get("label_history", []):
                    changed += 1
                    self.assertTrue(h["date"] and h["reason"] and h["old"] != h["new"], (t, c))
                    self.assertEqual(h["new"], rec["human_verdict"])
        self.assertEqual(changed, 2)
        self.assertIn("CURRENT rubric", self.gold["label_policy"])

    def test_every_entry_has_a_note_and_the_reviewer_line(self):
        self.assertEqual(self.gold["reviewer"], "Daniel Bravo, reviewed with Claude, 2026-10-10")
        for t, crits in self.gold["gold"].items():
            self.assertEqual(len(crits), 4)
            for rec in crits.values():
                self.assertTrue(rec["note"])


if __name__ == "__main__":
    unittest.main()
