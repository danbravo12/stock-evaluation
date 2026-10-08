"""Guard: fails if any score changes from the reviewed, frozen results in eval/expected_scores.json.

A failure means a rule, a concept map entry, a fixture or the split logic changed the output.
Review the difference; if it is deliberate, refresh with `.venv/bin/python -m eval.snapshot`.
"""
from __future__ import annotations

import json
import unittest

from eval.snapshot import EXPECTED_PATH, current_snapshots


class TestExpectedScores(unittest.TestCase):
    def test_scores_match_frozen_expectations(self):
        expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        actual = current_snapshots()
        self.assertEqual(sorted(actual), sorted(expected))
        for ticker, snap in expected.items():
            self.assertEqual(actual[ticker]["as_of_year"], snap["as_of_year"], ticker)
            self.assertEqual(actual[ticker]["sector_class"], snap["sector_class"], ticker)
            for cid, want in snap["criteria"].items():
                self.assertEqual(actual[ticker]["criteria"][cid], want, f"{ticker} {cid}")


if __name__ == "__main__":
    unittest.main()
