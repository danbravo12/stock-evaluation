"""The frozen label counts of the whole-universe numeric run (ADR-059): tolerance logic offline, live comparison when results/scores exists locally."""
from __future__ import annotations

import json
import unittest

from eval.universe_counts import FROZEN_PATH, LABELS, SCORES_DIR, compare, count_labels

FROZEN = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))


class TestFrozenCounts(unittest.TestCase):
    def test_the_frozen_file_is_internally_consistent(self):
        n = FROZEN["scored"]
        self.assertGreaterEqual(n, 490)
        self.assertEqual(sum(FROZEN["sector_classes"].values()), n)
        self.assertEqual(set(FROZEN["criteria"]), {f"G{i}" for i in range(1, 8)} | {f"B{i}" for i in range(1, 5)})
        for cid, c in FROZEN["criteria"].items():
            self.assertEqual(sum(c.values()), n, cid)  # every scored company has exactly one label per criterion
            self.assertTrue(set(c) <= set(LABELS))
        self.assertEqual(FROZEN["criteria"]["G6"], {"data_gap": n})  # no price yet
        self.assertEqual(FROZEN["criteria"]["G7"], {"data_gap": n})

    def test_small_drift_is_tolerated_and_a_shift_of_hundreds_of_labels_is_reported(self):
        small = json.loads(json.dumps(FROZEN))
        small["criteria"]["B1"]["pass"] += 4
        small["criteria"]["B1"]["fail"] -= 4
        self.assertEqual(compare(FROZEN, small), [])
        big = json.loads(json.dumps(FROZEN))
        big["criteria"]["G4"]["partial_pass"] -= 150
        big["criteria"]["G4"]["fail"] += 150
        diffs = compare(FROZEN, big)
        self.assertEqual(len(diffs), 2)
        self.assertIn("G4 fail", diffs[0] + diffs[1])
        fewer = json.loads(json.dumps(FROZEN))
        fewer["scored"] -= 60
        self.assertTrue(any("companies scored" in d for d in compare(FROZEN, fewer)))

    def test_the_local_run_matches_the_frozen_counts(self):
        if not any(SCORES_DIR.glob("*.json")):
            self.skipTest("results/scores/ is local and git-ignored: run `python -m engine.cli batch --universe --numeric-only`")
        self.assertEqual(compare(FROZEN, count_labels()), [])


if __name__ == "__main__":
    unittest.main()
