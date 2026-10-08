"""Unit tests for the scorers on small synthetic series (offline)."""
from __future__ import annotations

import json
import unittest

from engine.contracts import ScoreSet
from engine.score import score_company, summarise
from engine.score.buffett import b1_return_on_equity, b2_conservative_debt, b3_stable_margins, b4_owner_earnings
from engine.score.common import load_sector_rules, sector_class
from engine.score.graham import (g1_size, g2_financial_strength, g3_earnings_stability, g4_dividend_record,
                                 g5_earnings_growth, g6_moderate_pe, g7_price_vs_assets)
from tests.synthetic import facts, flat, table

Y10 = range(2015, 2025)  # ten fiscal years, as-of 2024
AS_OF = 2024


class TestSectorClass(unittest.TestCase):
    def test_sic_ranges(self):
        rules = load_sector_rules()
        for sic, expected in ((6021, "bank"), (6035, "bank"), (6311, "insurer"), (6411, "insurer"), (4931, "utility"),
                              (4911, "utility"), (7370, "other"), (None, "other"), ("6022", "bank")):
            self.assertEqual(sector_class(sic, rules), expected, sic)


class TestG1(unittest.TestCase):
    def test_edges_and_gap(self):
        self.assertEqual(g1_size(table({"revenue": {AS_OF: 1e9}}), AS_OF).label, "pass")
        self.assertEqual(g1_size(table({"revenue": {AS_OF: 1e9 - 1}}), AS_OF).label, "fail")
        r = g1_size(table({"revenue": {2020: 5e9}}), AS_OF)
        self.assertEqual(r.label, "data_gap")


class TestG2(unittest.TestCase):
    def data(self, ca=200, cl=100, debt=100, equity=100):
        return table({"current_assets": {AS_OF: ca}, "current_liabilities": {AS_OF: cl},
                      "long_term_debt": {AS_OF: debt}, "stockholders_equity": {AS_OF: equity}})

    def test_edges(self):
        self.assertEqual(g2_financial_strength(self.data(), AS_OF, "other").label, "pass")  # ratio 2.0, debt = net current assets
        self.assertEqual(g2_financial_strength(self.data(ca=199), AS_OF, "other").label, "fail")
        self.assertEqual(g2_financial_strength(self.data(debt=101), AS_OF, "other").label, "fail")

    def test_missing_debt_is_a_gap_not_zero(self):
        r = g2_financial_strength(table({"current_assets": {AS_OF: 200}, "current_liabilities": {AS_OF: 100}}), AS_OF, "other")
        self.assertEqual(r.label, "data_gap")
        self.assertIn("long_term_debt", r.reason)

    def test_utility_rule_and_bank_exception(self):
        self.assertEqual(g2_financial_strength(self.data(ca=50, debt=200, equity=100), AS_OF, "utility").label, "pass")
        self.assertEqual(g2_financial_strength(self.data(debt=201, equity=100), AS_OF, "utility").label, "fail")
        for sector in ("bank", "insurer"):
            self.assertEqual(g2_financial_strength(self.data(), AS_OF, sector).label, "not_applicable")


class TestG3(unittest.TestCase):
    def test_pass_fail(self):
        self.assertEqual(g3_earnings_stability(table({"net_income": flat(Y10, 1)}), AS_OF).label, "pass")
        data = flat(Y10, 1)
        data[2018] = -1
        r = g3_earnings_stability(table({"net_income": data}), AS_OF)
        self.assertEqual((r.label, r.figures["loss_years"]), ("fail", [2018]))

    def test_short_record_is_labelled_and_a_hole_is_a_gap(self):
        r = g3_earnings_stability(table({"net_income": flat(range(2018, 2025), 1)}), AS_OF)
        self.assertEqual((r.label, r.year_label), ("pass", "7 yrs on record"))
        hole = flat(Y10, 1)
        del hole[2020]
        self.assertEqual(g3_earnings_stability(table({"net_income": hole}), AS_OF).label, "data_gap")


class TestG4(unittest.TestCase):
    Y15 = range(2010, 2025)

    def data(self, dps=None, paid=None, ni_years=None):
        return table({"net_income": flat(ni_years or self.Y15, 1), "dividends_per_share": dps or {}, "dividends_paid": paid or {}})

    def test_full_record_is_a_partial_pass(self):
        r = g4_dividend_record(self.data(dps=flat(self.Y15, 0.5)), AS_OF)
        self.assertEqual((r.label, r.year_label), ("partial_pass", "partial (15 of 20 yrs)"))

    def test_short_record_label_uses_net_income_years(self):
        years = range(2018, 2025)
        r = g4_dividend_record(self.data(dps=flat(years, 0.5), ni_years=years), AS_OF)
        self.assertEqual((r.label, r.year_label), ("partial_pass", "7 yrs on record"))

    def test_long_listed_late_payer_fails(self):  # Alphabet pattern: financials for 13 years, dividends only at the end
        r = g4_dividend_record(self.data(dps=flat(range(2023, 2025), 0.2), ni_years=range(2012, 2025)), AS_OF)
        self.assertEqual(r.label, "fail")
        self.assertEqual(r.figures["years_on_record"], 13)

    def test_per_share_first_then_cash_paid_and_zero_is_unpaid(self):
        dps = flat(self.Y15, 0.5)
        del dps[2012]
        dps[2013] = 0.0  # reported zero: not paid, even though cash paid is positive
        paid = {2012: 5.0, 2013: 5.0}
        r = g4_dividend_record(self.data(dps=dps, paid=paid), AS_OF)
        self.assertEqual(r.by_year["2012"]["source"], "dividends_paid")
        self.assertTrue(r.by_year["2012"]["paid"])
        self.assertEqual(r.figures["unpaid_years"], [2013])  # per-share zero wins over cash paid

    def test_no_dividend_fact_is_unpaid(self):
        r = g4_dividend_record(self.data(dps=flat(range(2011, 2025), 0.5)), AS_OF)
        self.assertEqual((r.label, r.by_year["2010"]["source"]), ("fail", "none"))


class TestG5(unittest.TestCase):
    def eps(self, start, end):
        d = flat(Y10, 0)
        for y in (2015, 2016, 2017):
            d[y] = start
        for y in (2022, 2023, 2024):
            d[y] = end
        return table({"eps_diluted": d})

    def test_edges(self):
        self.assertEqual(g5_earnings_growth(self.eps(1.0, 1.33), AS_OF).label, "pass")
        self.assertEqual(g5_earnings_growth(self.eps(1.0, 1.32), AS_OF).label, "fail")

    def test_negative_or_zero_start_is_not_meaningful_and_shows_averages(self):
        r = g5_earnings_growth(self.eps(-0.5, 2.0), AS_OF)
        self.assertEqual(r.label, "not_meaningful")
        self.assertEqual((r.figures["avg_eps_start"], r.figures["avg_eps_end"]), (-0.5, 2.0))

    def test_missing_year_is_a_gap(self):
        d = flat(Y10, 1.0)
        del d[2016]
        self.assertEqual(g5_earnings_growth(table({"eps_diluted": d}), AS_OF).label, "data_gap")


class TestG6G7(unittest.TestCase):
    def data(self):
        return table({"eps_diluted": flat(Y10, 2.0), "stockholders_equity": {AS_OF: 1000.0}, "diluted_shares": {AS_OF: 100.0}})

    def test_no_price_is_a_data_gap(self):
        for fn in (g6_moderate_pe, g7_price_vs_assets):
            r = fn(self.data(), AS_OF, None)
            self.assertEqual(r.label, "data_gap")
            self.assertIn("Finnhub", r.reason)

    def test_g6_edge(self):  # 15 x avg EPS 2.0 = 30
        self.assertEqual(g6_moderate_pe(self.data(), AS_OF, 30.0).label, "pass")
        self.assertEqual(g6_moderate_pe(self.data(), AS_OF, 30.01).label, "fail")

    def test_g7_uses_book_value_per_share_proxy(self):  # BVPS 10; price 20 -> P/E 10 x P/B 2 = 20
        r = g7_price_vs_assets(self.data(), AS_OF, 20.0)
        self.assertEqual((r.label, round(r.figures["pe_x_pb"], 6)), ("pass", 20.0))
        self.assertEqual(g7_price_vs_assets(self.data(), AS_OF, 25.0).label, "fail")  # 12.5 x 2.5 = 31.25


class TestB1(unittest.TestCase):
    def data(self, good_years):
        equity = flat(range(2014, 2025), 100.0)
        ni = {y: 15.0 if y in good_years else 14.0 for y in Y10}  # ROE 15% exactly, or 14%
        return table({"net_income": ni, "stockholders_equity": equity})

    def test_seven_of_ten(self):
        self.assertEqual(b1_return_on_equity(self.data(range(2018, 2025)), AS_OF).label, "pass")
        self.assertEqual(b1_return_on_equity(self.data(range(2019, 2025)), AS_OF).label, "fail")

    def test_uses_average_of_opening_and_closing_equity(self):
        equity = flat(range(2014, 2025), 100.0)
        equity[2023], equity[2024] = 100.0, 200.0  # average 150
        r = b1_return_on_equity(table({"net_income": flat(Y10, 30.0), "stockholders_equity": equity}), AS_OF)
        self.assertAlmostEqual(r.by_year["2024"], 0.2)

    def test_non_positive_equity_is_not_meaningful_and_missing_opening_equity_is_a_gap(self):
        equity = flat(range(2014, 2025), 100.0)
        equity[2019] = -5.0
        self.assertEqual(b1_return_on_equity(table({"net_income": flat(Y10, 20.0), "stockholders_equity": equity}), AS_OF).label, "not_meaningful")
        no_opening = flat(range(2015, 2025), 100.0)
        self.assertEqual(b1_return_on_equity(table({"net_income": flat(Y10, 20.0), "stockholders_equity": no_opening}), AS_OF).label, "data_gap")


class TestB2(unittest.TestCase):
    def data(self, debt, ni=10.0):
        return table({"long_term_debt": {AS_OF: debt}, "net_income": flat(Y10, ni)})

    def test_edges_and_negative_earnings(self):
        self.assertEqual(b2_conservative_debt(self.data(40.0), AS_OF, "other").label, "pass")
        self.assertEqual(b2_conservative_debt(self.data(40.1), AS_OF, "other").label, "fail")
        r = b2_conservative_debt(self.data(1.0, ni=-5.0), AS_OF, "other")
        self.assertEqual((r.label, r.figures["avg_net_income_3y"]), ("fail", -5.0))

    def test_missing_debt_is_a_gap_and_banks_are_exempt(self):
        self.assertEqual(b2_conservative_debt(table({"net_income": flat(Y10, 10.0)}), AS_OF, "other").label, "data_gap")
        self.assertEqual(b2_conservative_debt(self.data(1.0), AS_OF, "bank").label, "not_applicable")


class TestB3(unittest.TestCase):
    def data(self, margins):
        return table({"revenue": flat(Y10, 100.0), "operating_income": {y: 100.0 * m for y, m in zip(Y10, margins)}})

    def test_pass_and_fail_cases(self):
        self.assertEqual(b3_stable_margins(self.data([0.2] * 10), AS_OF, "other").label, "pass")
        self.assertEqual(b3_stable_margins(self.data([0.2] * 9 + [-0.01]), AS_OF, "other").label, "fail")  # one loss year
        self.assertEqual(b3_stable_margins(self.data([0.3] * 7 + [0.2] * 3), AS_OF, "other").label, "fail")  # recent decline: 0.2 < 0.9 x 0.27
        self.assertEqual(b3_stable_margins(self.data([0.3] * 7 + [0.26] * 3), AS_OF, "other").label, "pass")  # 0.26 >= 0.9 x 0.288

    def test_bank_and_gap(self):
        self.assertEqual(b3_stable_margins(self.data([0.2] * 10), AS_OF, "bank").label, "not_applicable")
        self.assertEqual(b3_stable_margins(table({"revenue": flat(Y10, 100.0)}), AS_OF, "other").label, "data_gap")


class TestB4(unittest.TestCase):
    def data(self, ni=10.0, da=5.0, capex=8.0, drop=None):
        d = {"net_income": flat(Y10, ni), "depreciation_amortization": flat(Y10, da), "capex": flat(Y10, capex)}
        if drop:
            del d["capex"][drop]
        return table(d)

    def test_pass_and_fail(self):
        self.assertEqual(b4_owner_earnings(self.data(), AS_OF, "other").label, "fail")  # flat: last 3 avg is not above first 3
        growing = {"net_income": {y: 10.0 + y - 2015 for y in Y10}, "depreciation_amortization": flat(Y10, 5.0), "capex": flat(Y10, 8.0)}
        self.assertEqual(b4_owner_earnings(table(growing), AS_OF, "other").label, "pass")
        negative = dict(growing, capex=flat(Y10, 30.0))
        self.assertEqual(b4_owner_earnings(table(negative), AS_OF, "other").label, "fail")

    def test_needs_all_ten_years(self):
        r = b4_owner_earnings(self.data(drop=2019), AS_OF, "other")
        self.assertEqual(r.label, "data_gap")
        self.assertEqual(r.years, [2019])
        self.assertIn("capex", r.reason)

    def test_bank_is_exempt(self):
        self.assertEqual(b4_owner_earnings(self.data(), AS_OF, "insurer").label, "not_applicable")

    def test_depreciation_only_years_are_flagged(self):
        nf = facts({"net_income": {y: 10.0 + y - 2015 for y in Y10}, "depreciation_amortization": flat(Y10, 5.0), "capex": flat(Y10, 8.0)})
        da = nf.series["depreciation_amortization"]
        da.values[-1] = da.values[-1].model_copy(update={"derived": True, "source_concepts": ["us-gaap:Depreciation"]})
        from engine.score.common import Facts
        r = b4_owner_earnings(Facts(nf), AS_OF, "other")
        self.assertIn("depreciation_only", r.flags)
        self.assertEqual(r.figures["years_with_depreciation_only"], [2024])


class TestScoreSet(unittest.TestCase):
    def healthy(self):
        growing = {y: 10.0 + (y - 2015) for y in Y10}
        return facts({
            "revenue": flat(Y10, 5e9), "net_income": growing, "eps_diluted": growing, "operating_income": flat(Y10, 1e9),
            "current_assets": flat(Y10, 300.0), "current_liabilities": flat(Y10, 100.0), "long_term_debt": flat(Y10, 50.0),
            "stockholders_equity": flat(range(2014, 2025), 50.0), "depreciation_amortization": flat(Y10, 5.0), "capex": flat(Y10, 8.0),
            "dividends_per_share": flat(range(2010, 2025), 1.0), "diluted_shares": flat(Y10, 10.0),
        })

    def test_summary_validation_and_no_advice_language(self):
        s = score_company(self.healthy(), "TEST", 3711, load_sector_rules())
        self.assertEqual((s.as_of_year, s.sector_class), (AS_OF, "other"))
        self.assertEqual(s.summary.data_gaps, 2)  # G6, G7: no price
        self.assertEqual((s.summary.graham_met, s.summary.graham_applicable), (5, 5))
        again = ScoreSet.model_validate(s.model_dump())
        self.assertEqual(again, s)
        text = json.dumps(s.model_dump(mode="json")).lower()
        for banned in ("buy", "sell", "undervalued", "overvalued", "recommend"):
            self.assertNotIn(banned, text)

    def test_price_turns_the_gaps_into_results(self):
        s = score_company(self.healthy(), "TEST", 3711, load_sector_rules(), price=100.0)
        self.assertEqual(s.summary.data_gaps, 0)

    def test_summary_counts_labels_separately(self):
        from engine.contracts import CriterionResult
        mk = lambda i, label: CriterionResult(id=i, name="", label=label, threshold="")
        s = summarise([mk("G1", "pass"), mk("G2", "fail"), mk("G3", "partial_pass"), mk("G4", "data_gap"), mk("G5", "not_meaningful"),
                       mk("B1", "pass"), mk("B2", "not_applicable")])
        self.assertEqual((s.graham_met, s.graham_applicable, s.buffett_met, s.buffett_applicable), (2, 3, 1, 1))
        self.assertEqual((s.data_gaps, s.not_meaningful, s.not_applicable), (1, 1, 1))
        self.assertAlmostEqual(s.percent_met, 0.75)


if __name__ == "__main__":
    unittest.main()
