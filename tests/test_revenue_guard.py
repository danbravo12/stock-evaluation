"""Revenue mapping (ADR-061): a component is not the total, and banks without a total-revenue tag get one. Synthetic cases and recorded SEC facts."""
from __future__ import annotations

import unittest
from datetime import date

from engine.contracts import AnnualValue
from engine.fetch.edgar import EdgarClient
from engine.normalise import _pick_per_year, normalise_from_store
from engine.settings import Settings


def val(concept: str, v: float, end=date(2020, 12, 31)) -> AnnualValue:
    return AnnualValue(fiscal_year_end=end, value=v, unit="USD", concept=concept, taxonomy="us-gaap", accession="a", form="10-K", filed=date(2021, 2, 1),
                       period_start=date(2020, 1, 1), source_url="u")


class TestGuardLogic(unittest.TestCase):
    def test_a_component_first_in_priority_is_skipped_and_the_note_says_so(self):
        e = date(2020, 12, 31)
        cands = [(None, {e: val("Revenues", 2.0e9)}), (None, {e: val("RevenueFromContract", 19.0e9)})]
        values, notes = _pick_per_year("revenue", cands, {"component_guard": 0.5})
        self.assertEqual([v.concept for v in values], ["RevenueFromContract"])
        self.assertTrue(any("Revenues=2e+09 skipped: below 50%" in n for n in notes))

    def test_without_the_guard_priority_order_decides_as_before(self):
        e = date(2020, 12, 31)
        cands = [(None, {e: val("Revenues", 2.0e9)}), (None, {e: val("RevenueFromContract", 19.0e9)})]
        values, _ = _pick_per_year("revenue", cands, {})
        self.assertEqual(values[0].concept, "Revenues")

    def test_candidates_within_the_fraction_keep_the_priority_order_and_a_lone_candidate_is_kept(self):
        e = date(2020, 12, 31)
        near = [(None, {e: val("Revenues", 9.0e9)}), (None, {e: val("Contract", 10.0e9)})]
        self.assertEqual(_pick_per_year("revenue", near, {"component_guard": 0.5})[0][0].concept, "Revenues")
        lone = [(None, {e: val("Contract", 0.01e9)})]
        self.assertEqual(_pick_per_year("revenue", lone, {"component_guard": 0.5})[0][0].value, 0.01e9)  # nothing larger to compare with

    def test_the_guard_works_year_by_year(self):
        a, b = date(2019, 12, 31), date(2020, 12, 31)
        cands = [(None, {a: val("Revenues", 19e9, a), b: val("Revenues", 2e9, b)}), (None, {b: val("Contract", 19e9, b)})]
        values, _ = _pick_per_year("revenue", cands, {"component_guard": 0.5})
        self.assertEqual([v.concept for v in values], ["Revenues", "Contract"])


class TestRecordedCompanies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def revenue(self, cik):
        return {v.fiscal_year_end.year: v for v in normalise_from_store(self.client, cik).series["revenue"].values}

    def test_general_mills_no_longer_reports_two_billion_for_2019_to_2024(self):
        rev = self.revenue("0000040704")
        for y in range(2019, 2025):
            self.assertGreater(rev[y].value, 15e9, y)
        self.assertIn("skipped", " ".join(normalise_from_store(self.client, "0000040704").series["revenue"].notes))

    def test_a_bank_without_a_total_revenue_tag_gets_net_interest_plus_noninterest_income(self):
        v = self.revenue("0000035527")[2025]  # Fifth Third
        self.assertTrue(v.derived)
        self.assertEqual(sorted(v.source_concepts), ["us-gaap:InterestIncomeExpenseNet", "us-gaap:NoninterestIncome"])
        self.assertGreater(v.value, 5e9)

    def test_revenues_net_of_interest_expense_is_used_for_goldman_sachs(self):
        v = self.revenue("0000886982")[2025]
        self.assertEqual(v.concept, "RevenuesNetOfInterestExpense")
        self.assertGreater(v.value, 50e9)

    def test_the_five_test_companies_are_unchanged(self):
        # JPM keeps its own total-revenue tag even though the new bank fallbacks exist
        v = self.revenue("0000019617")[2025]
        self.assertEqual(v.concept, "Revenues")


if __name__ == "__main__":
    unittest.main()
