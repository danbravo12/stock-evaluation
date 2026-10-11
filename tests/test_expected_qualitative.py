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

    def test_agreement_is_16_of_20_agent_only_under_prompt_v2_1(self):
        """Agent only (before the Critic's repairs). 19 of 20 with prompt v1, 14 of 20 with v2, 16 of 20 with v2.1 (build 4a); the figure after the repairs is in
        eval/agreement.py (15 of 20, `docs/evaluation_notes.md` item 26). All differences are weak-versus-found or weak-versus-insufficient borderline calls."""
        result = agreement(self.verdicts, self.gold)
        self.assertEqual((result["agree"], result["total"]), (16, 20))
        self.assertEqual({(d["ticker"], d["criterion"]): d["direction"] for d in result["disagreements"]},
                         {("KO", "durable_competitive_advantage"): "too strict", ("KO", "candid_management"): "over-generous", ("GOOGL", "durable_competitive_advantage"): "over-generous",
                          ("TSLA", "rational_capital_allocation"): "over-generous"})

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
