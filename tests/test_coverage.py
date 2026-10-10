"""Coverage recovery (ADR-064): derived operating income, REIT revenue, and the capex concepts that were deliberately not added. Offline."""
from __future__ import annotations

import unittest
from datetime import date

from engine.fetch.edgar import EdgarClient
from engine.normalise import _difference_values, load_concept_map, normalise_from_store
from engine.score import score_ticker
from engine.settings import Settings
from tests.synthetic import value

A, B = "us-gaap:Revenues", "us-gaap:CostsAndExpenses"
CHECK = "us-gaap:OperatingIncomeLoss"
BXP, PSA, CPT, CVX, FORD = "0001037540", "0001393311", "0000906345", "0000093410", "0000037996"


def series(measure, data, **extra):
    return {date(y, 12, 31): value(measure, y, v, **extra) for y, v in data.items()}


class TestDifference(unittest.TestCase):
    def parts(self, rev, costs, **extra):
        return [series("revenue", rev, **extra), series("revenue", costs, **extra)]

    def test_difference_is_flagged_derived_with_its_source_concepts(self):
        out = _difference_values(self.parts({2020: 100, 2021: 120}, {2020: 70, 2021: 80}), [A, B], None, 2)
        self.assertEqual({e.year: v.value for e, v in out.items()}, {2020: 30, 2021: 40})
        v = out[date(2021, 12, 31)]
        self.assertTrue(v.derived)
        self.assertEqual((v.source_concepts, v.concept), ([A, B], "Revenues-CostsAndExpenses"))

    def test_both_parts_must_come_from_the_same_filing(self):
        a, b = self.parts({2020: 100, 2021: 120}, {2020: 70, 2021: 80})
        b[date(2021, 12, 31)] = value("revenue", 2021, 80, accession="0000000002-2022-000009")  # a later restatement of one part only
        out = _difference_values([a, b], [A, B], None, 2)
        self.assertEqual(sorted(e.year for e in out), [2020])

    def test_both_parts_must_cover_the_same_fiscal_period(self):
        a, b = self.parts({2020: 100}, {2020: 70})
        b[date(2020, 12, 31)] = value("revenue", 2020, 70, period_start=date(2020, 4, 1))
        a[date(2020, 12, 31)] = value("revenue", 2020, 100, period_start=date(2020, 1, 1))
        self.assertEqual(_difference_values([a, b], [A, B], None, 2), {})

    def test_proof_needs_overlap_years_that_all_agree(self):
        parts = self.parts({y: 100 for y in range(2016, 2022)}, {y: 70 for y in range(2016, 2022)})
        ok = series("operating_income", {2016: 30, 2017: 30})
        self.assertEqual(sorted(e.year for e in _difference_values(parts, [A, B], ok, 2)), list(range(2016, 2022)))
        one = series("operating_income", {2016: 30})
        self.assertEqual(_difference_values(parts, [A, B], one, 2), {})  # one overlapping year is not a proof
        wrong = series("operating_income", {2016: 30, 2017: 25})  # pre-tax scope: differs in one year
        self.assertEqual(_difference_values(parts, [A, B], wrong, 2), {})
        none = series("operating_income", {})
        self.assertEqual(_difference_values(parts, [A, B], none, 2), {})  # a company that never tags it: nothing derived

    def test_tolerance_is_one_percent(self):
        parts = self.parts({2020: 1000, 2021: 1000}, {2020: 700, 2021: 700})
        self.assertTrue(_difference_values(parts, [A, B], series("operating_income", {2020: 302, 2021: 299}), 2))
        self.assertEqual(_difference_values(parts, [A, B], series("operating_income", {2020: 310, 2021: 300}), 2), {})

    def test_the_proof_reaches_forward_only(self):
        parts = self.parts({y: 100 for y in range(2012, 2022)}, {y: 70 for y in range(2012, 2022)})
        check = series("operating_income", {2017: 30, 2018: 30})  # the company started tagging the concept in 2017
        self.assertEqual(sorted(e.year for e in _difference_values(parts, [A, B], check, 2)), list(range(2017, 2022)))


class TestRecordedOperatingIncome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def op(self, cik):
        return {v.fiscal_year_end.year: v for v in normalise_from_store(self.client, cik).series["operating_income"].values}

    def test_boston_properties_stopped_tagging_in_2018_and_the_difference_continues_the_series(self):
        op = self.op(BXP)
        self.assertEqual({y: v.derived for y, v in op.items() if y >= 2014}, {y: y >= 2018 for y in range(2014, 2026)})
        v = op[2021]
        self.assertEqual(v.source_concepts, ["us-gaap:Revenues", "us-gaap:CostsAndExpenses"])
        self.assertIn(v.accession.replace("-", ""), v.source_url)  # the accession of the filing both parts come from
        self.assertIn("/data/1037540/", v.source_url)
        self.assertAlmostEqual(op[2017].value / 1e9, 0.91, places=2)  # reported
        self.assertAlmostEqual(op[2018].value / 1e9, 0.93, places=2)  # derived, same order of magnitude: no break in the series

    def test_b3_for_the_companies_that_gain_a_score(self):
        b3 = {t: next(r for r in score_ticker(self.client, t).results if r.id == "B3") for t in ("BXP", "PSA")}
        self.assertEqual({t: r.label for t, r in b3.items()}, {"BXP": "pass", "PSA": "fail"})
        self.assertIn("derived", b3["BXP"].flags)

    def test_pre_tax_scope_is_never_derived(self):  # Chevron: Revenues - CostsAndExpenses equals pre-tax income in all 19 years
        nf = normalise_from_store(self.client, CVX)
        self.assertEqual(nf.series["operating_income"].values, [])
        self.assertEqual(next(r for r in score_ticker(self.client, "CVX").results if r.id == "B3").label, "data_gap")

    def test_a_company_that_started_tagging_later_is_not_back_filled(self):  # Ford: OperatingIncomeLoss from 2017
        op = self.op(FORD)
        self.assertTrue(op)
        self.assertEqual(min(y for y, v in op.items() if not v.derived), 2017)
        self.assertFalse(any(v.derived for y, v in op.items() if y < 2017))

    def test_companies_with_a_tag_are_unchanged(self):
        for t in ("KO", "GOOGL", "TSLA", "DUK"):
            nf = normalise_from_store(self.client, self.client.lookup_cik(t)[0])
            self.assertFalse(any(v.derived for v in nf.series["operating_income"].values), t)


class TestReitRevenue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def test_camden_revenue_is_rental_income_not_the_fee_component(self):
        nf = normalise_from_store(self.client, CPT)
        rev = {v.fiscal_year_end.year: v for v in nf.series["revenue"].values}
        self.assertEqual({v.concept for y, v in rev.items() if y >= 2017}, {"OperatingLeaseLeaseIncome"})
        self.assertGreater(rev[2025].value, 1.4e9)
        self.assertTrue(any("RevenueFromContractWithCustomerExcludingAssessedTax" in n and "component" in n for n in nf.series["revenue"].notes))  # the guard still skips it
        self.assertEqual(next(r for r in score_ticker(self.client, "CPT").results if r.id == "G1").label, "pass")

    def test_the_partial_line_guard_and_priority_are_unchanged_for_ordinary_companies(self):
        for t in ("KO", "JPM", "GOOGL", "TSLA", "DUK"):
            nf = normalise_from_store(self.client, self.client.lookup_cik(t)[0])
            self.assertFalse(any("Lease" in v.concept for v in nf.series["revenue"].values), t)

    def test_lease_income_is_last_in_the_priority_list(self):
        concepts = load_concept_map()["measures"]["revenue"]["concepts"]
        self.assertEqual(concepts[-2:], ["us-gaap:OperatingLeaseLeaseIncome", "us-gaap:OperatingLeasesIncomeStatementLeaseRevenue"])


class TestCapexConceptsStayTotals(unittest.TestCase):
    def test_only_total_capex_concepts_are_mapped(self):
        """ADR-064: PaymentsForCapitalImprovements, the real-estate acquisition and development lines and the 'other' lines are components or a different scope."""
        self.assertEqual(load_concept_map()["measures"]["capex"]["concepts"],
                         ["us-gaap:PaymentsToAcquirePropertyPlantAndEquipment", "us-gaap:PaymentsToAcquireProductiveAssets"])


if __name__ == "__main__":
    unittest.main()
