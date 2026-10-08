"""Scorers on the real fixtures (replay): only what follows with certainty from the data and the rules."""
from __future__ import annotations

import unittest

from engine.fetch.edgar import EdgarClient
from engine.score import score_ticker
from engine.settings import Settings

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]


class TestFixtureScores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = EdgarClient("replay", Settings.from_env())
        cls.scores = {t: score_ticker(client, t) for t in TICKERS}

    def label(self, t, cid):
        return next(r for r in self.scores[t].results if r.id == cid).label

    def test_as_of_year_and_sector_class(self):
        for t, s in self.scores.items():
            self.assertEqual(s.as_of_year, 2025, t)
        self.assertEqual({t: s.sector_class for t, s in self.scores.items()},
                         {"KO": "other", "JPM": "bank", "GOOGL": "other", "TSLA": "other", "DUK": "utility"})

    def test_tesla_fails_earnings_stability_and_dividends(self):
        self.assertEqual((self.label("TSLA", "G3"), self.label("TSLA", "G4")), ("fail", "fail"))

    def test_bank_exceptions(self):
        for cid in ("G2", "B2", "B3", "B4"):
            self.assertEqual(self.label("JPM", cid), "not_applicable", cid)

    def test_duke_uses_the_utility_rule(self):
        g2 = next(r for r in self.scores["DUK"].results if r.id == "G2")
        self.assertIn("utility", g2.threshold)
        self.assertIn("debt_to_equity", g2.figures)

    def test_alphabet_owner_earnings_is_a_data_gap(self):
        self.assertEqual(self.label("GOOGL", "B4"), "data_gap")

    def test_price_criteria_are_gaps_without_a_price(self):
        for t in TICKERS:
            self.assertEqual((self.label(t, "G6"), self.label(t, "G7")), ("data_gap", "data_gap"), t)

    def test_every_input_has_provenance(self):
        for t, s in self.scores.items():
            self.assertTrue(s.inputs)
            for i in s.inputs:
                self.assertTrue(i.concept and i.accession and i.source_url.startswith("https://www.sec.gov/Archives/edgar/data/"), t)

    def test_split_adjusted_inputs_are_flagged(self):
        g5 = next(r for r in self.scores["GOOGL"].results if r.id == "G5")
        self.assertIn("split_adjusted", g5.flags)


if __name__ == "__main__":
    unittest.main()
