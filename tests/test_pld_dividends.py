"""Prologis (REIT) dividends: the first live run showed G4 failing in years it paid. Recorded PLD facts guard the concept order (ADR-060)."""
from __future__ import annotations

import unittest

from engine.fetch.edgar import EdgarClient
from engine.normalise import normalise_from_store
from engine.score import score_ticker
from engine.settings import Settings


class TestPldDividends(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def test_cash_paid_wins_over_the_tiny_declared_amounts(self):
        nf = normalise_from_store(self.client, "0001045609")
        by_year = {v.fiscal_year_end.year: v for v in nf.series["dividends_per_share"].values}
        self.assertTrue(all(v.concept.endswith("CommonStockDividendsPerShareCashPaid") for y, v in by_year.items() if y >= 2017), {y: v.concept for y, v in by_year.items()})
        self.assertAlmostEqual(by_year[2019].value, 2.12)
        self.assertAlmostEqual(by_year[2025].value, 4.04)

    def test_g4_no_longer_reports_unpaid_years(self):
        g4 = next(r for r in score_ticker(self.client, "PLD").results if r.id == "G4")
        self.assertEqual(g4.label, "partial_pass")  # paid in every year on record (15 of the 20 asked for)
        self.assertEqual(g4.figures, {"years_on_record": 15})
        self.assertTrue(all(y["paid"] and y["value"] > 1.0 for y in g4.by_year.values()))


class TestDividendGuard(unittest.TestCase):
    """The guard (0.5 of the larger candidate) must also keep Trane's real dividends when CashPaid reads $0 (found by checking the change on the whole index)."""

    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def test_trane_keeps_its_declared_dividend_where_cash_paid_reads_zero(self):
        by_year = {v.fiscal_year_end.year: v for v in normalise_from_store(self.client, "0001466258").series["dividends_per_share"].values}
        self.assertGreater(by_year[2017].value, 1.0)
        self.assertGreater(by_year[2018].value, 1.0)
        g4 = next(r for r in score_ticker(self.client, "TT").results if r.id == "G4")
        self.assertEqual(g4.label, "partial_pass")

    def test_synthetic_both_directions(self):
        from datetime import date
        from engine.contracts import AnnualValue
        from engine.normalise import _pick_per_year

        def v(c, x):
            return AnnualValue(fiscal_year_end=date(2020, 12, 31), value=x, unit="USD/shares", concept=c, taxonomy="us-gaap", accession="a", form="10-K", filed=date(2021, 2, 1),
                               period_start=date(2020, 1, 1), source_url="u")
        e = date(2020, 12, 31)
        spec = {"component_guard": 0.5}
        self.assertEqual(_pick_per_year("d", [(None, {e: v("CashPaid", 3.84)}), (None, {e: v("Declared", 0.01)})], spec)[0][0].concept, "CashPaid")
        self.assertEqual(_pick_per_year("d", [(None, {e: v("CashPaid", 0.0)}), (None, {e: v("Declared", 1.4)})], spec)[0][0].concept, "Declared")
        self.assertEqual(_pick_per_year("d", [(None, {e: v("CashPaid", 0.0)}), (None, {e: v("Declared", 0.0)})], spec)[0][0].concept, "CashPaid")  # both zero: priority order


if __name__ == "__main__":
    unittest.main()
