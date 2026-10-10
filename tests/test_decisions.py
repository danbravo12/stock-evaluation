"""Daniel's decisions of 2026-10-11 (ADR-057 and ADR-012 amendments), registrant successors and companies without a 10-K (ADR-063). Offline."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.batch import CompanyLedger, row_from_result, run_numeric_batch
from engine.fetch.edgar import EdgarClient, NoAnnualReportError
from engine.normalise import normalise_from_store
from engine.numeric import score_numeric
from engine.orchestrator import analyse
from engine.planner import plan_for
from engine.score import score_company, score_ticker
from engine.score.common import load_sector_rules
from engine.score.graham import g4_dividend_record
from engine.settings import Settings
from engine.splits import adjust_for_splits
from engine.successors import NoAnnualReport, has_annual_report
from engine.universe import load_universe
from tests.synthetic import flat, table

RULES = load_sector_rules()
IB_NOTE = "Insurance broker: holds client fiduciary funds, which depress the current ratio; it does not carry underwriting risk."
IPP_NOTE = "Not rate-regulated, so Graham's utility variant does not apply."
BRK_NOTE = "Conglomerate with large insurance operations; consolidated figures mix insurance and industrial balance sheets."
XOM_NOTE = "Figures from predecessor registrant Exxon Mobil Corp (CIK 34088) until ExxonMobil Holdings files its first 10-K."


class TestFinancialClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.u = load_universe()

    def plan(self, symbol):
        return plan_for(symbol, self.u, None)

    def test_brokers_dealers_are_banks_by_sub_industry(self):
        syms = [r.symbol for r in self.u.primary if r.gics_sub_industry == "Investment Banking & Brokerage"]
        self.assertEqual(sorted(syms), ["GS", "HOOD", "IBKR", "MS", "RJF", "SCHW"])
        for sym in syms:
            p = self.plan(sym)
            self.assertEqual((p.sector_class, [x.id for x in p.not_applicable], p.sector_notes), ("bank", ["G2", "B2", "B3", "B4"], []), sym)
            self.assertEqual(p.sector_basis, "gics:Investment Banking & Brokerage", sym)  # a rule, no longer per-CIK overrides

    def test_insurance_brokers_are_other_with_the_note(self):
        syms = [r.symbol for r in self.u.primary if r.gics_sub_industry == "Insurance Brokers"]
        self.assertGreaterEqual(len(syms), 5)
        for sym in syms:
            p = self.plan(sym)
            self.assertEqual((p.sector_class, p.not_applicable, p.sector_notes), ("other", [], [IB_NOTE]), sym)

    def test_independent_power_producers_are_other_with_the_note(self):
        syms = [r.symbol for r in self.u.primary if r.gics_sub_industry == "Independent Power Producers & Energy Traders"] + ["VST", "CEG"]  # VST and CEG: GICS says Electric Utilities
        self.assertIn("NRG", syms)
        for sym in syms:
            p = self.plan(sym)
            self.assertEqual((p.sector_class, p.sector_notes), ("other", [IPP_NOTE]), sym)

    def test_regulated_utilities_keep_the_utility_variant_without_a_note(self):
        p = self.plan("DUK")
        self.assertEqual((p.sector_class, p.sector_notes), ("utility", []))

    def test_berkshire_is_other_with_the_note(self):
        p = self.plan("BRK-B")
        self.assertEqual((p.sector_class, p.not_applicable, p.sector_notes), ("other", [], [BRK_NOTE]))

    def test_the_reit_note_is_unchanged(self):
        self.assertEqual(self.plan("PLD").sector_class, "reit")
        self.assertTrue(self.plan("PLD").sector_notes[0].startswith("REIT: structurally debt-funded"))

    def test_the_scorers_carry_the_same_note_as_the_plan(self):
        client = EdgarClient("replay", Settings.from_env())
        nf = adjust_for_splits(normalise_from_store(client, "0000886982"), client.companyfacts("0000886982"))  # Goldman Sachs fixture
        s = score_company(nf, "GS", client.submissions("0000886982").get("sic"), RULES, gics_sub_industry="Investment Banking & Brokerage")
        self.assertEqual((s.sector_class, s.sector_notes), ("bank", []))
        self.assertEqual({r.id for r in s.results if r.label == "not_applicable"}, {"G2", "B2", "B3", "B4"})

    def test_a_rule_note_replaces_the_class_note(self):
        from engine.score.common import sector_notes
        self.assertEqual(sector_notes("other", RULES, gics_sub_industry="Insurance Brokers"), [IB_NOTE])
        self.assertEqual(sector_notes("other", RULES, gics_sub_industry="Independent Power Producers & Energy Traders"), [IPP_NOTE])
        self.assertEqual(sector_notes("other", RULES, gics_sub_industry="Soft Drinks & Non-alcoholic Beverages"), [])
        self.assertEqual(sector_notes("other", RULES, cik="0001067983"), [BRK_NOTE])


class TestG4UnknownYears(unittest.TestCase):
    Y15 = list(range(2011, 2026))

    def data(self, dps, ni_years=None):
        return table({"dividends_per_share": dps, "net_income": flat(ni_years or self.Y15, 1.0)})

    def test_a_missing_year_between_paid_years_is_a_data_gap_naming_the_year(self):
        dps = flat(self.Y15, 0.5)
        del dps[2016]
        r = g4_dividend_record(self.data(dps), 2025)
        self.assertEqual((r.label, r.reason), ("data_gap", "dividend data missing for 2016"))
        self.assertEqual(r.figures["unknown_years"], [2016])
        self.assertIsNone(r.by_year["2016"]["paid"])

    def test_several_missing_years_are_all_named(self):
        dps = flat(self.Y15, 0.5)
        del dps[2014], dps[2015], dps[2020]
        self.assertEqual(g4_dividend_record(self.data(dps), 2025).reason, "dividend data missing for 2014, 2015, 2020")

    def test_a_confirmed_unpaid_year_fails_even_when_other_years_are_unknown(self):
        dps = flat(self.Y15, 0.5)
        del dps[2014]
        dps[2018] = 0.0
        r = g4_dividend_record(self.data(dps), 2025)
        self.assertEqual((r.label, r.figures["unpaid_years"], r.figures["unknown_years"]), ("fail", [2018], [2014]))

    def test_years_before_the_first_paid_year_stay_unpaid(self):  # Alphabet, Amazon, Tesla pattern
        r = g4_dividend_record(self.data(flat(range(2024, 2026), 0.2)), 2025)
        self.assertEqual((r.label, r.figures["unpaid_years"], "unknown_years" in r.figures), ("fail", list(range(2011, 2024)), False))
        none = g4_dividend_record(self.data({}), 2025)
        self.assertEqual((none.label, none.figures["unpaid_years"]), ("fail", self.Y15))

    def test_years_after_the_last_paid_year_stay_unpaid(self):
        r = g4_dividend_record(self.data(flat(range(2011, 2022), 0.5)), 2025)
        self.assertEqual((r.label, r.figures["unpaid_years"]), ("fail", [2022, 2023, 2024, 2025]))

    def test_a_stray_cash_payment_does_not_open_a_span_for_a_late_payer(self):  # Alphabet's $47M in 2015
        t = table({"dividends_per_share": flat(range(2024, 2026), 0.2), "dividends_paid": {2015: 47e6}, "net_income": flat(range(2013, 2026), 1.0)})
        r = g4_dividend_record(t, 2025)
        self.assertEqual((r.label, r.figures["unpaid_years"]), ("fail", [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]))

    def test_without_per_share_data_the_span_comes_from_cash_paid(self):
        paid = flat(self.Y15, 5e6)
        del paid[2019]
        t = table({"dividends_paid": paid, "net_income": flat(self.Y15, 1.0)})
        self.assertEqual(g4_dividend_record(t, 2025).reason, "dividend data missing for 2019")

    def test_complete_records_are_labelled_as_before(self):
        r = g4_dividend_record(self.data(flat(self.Y15, 0.5)), 2025)
        self.assertEqual((r.label, r.year_label, r.figures), ("partial_pass", "partial (15 of 20 yrs)", {"years_on_record": 15}))


class TestFederalRealty(unittest.TestCase):
    """Federal Realty (REIT, CIK 34903): the clearest false-fail found in the universe run (docs/evaluation_notes.md item 20). Recorded facts, SEC data only."""

    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())
        cls.nf = adjust_for_splits(normalise_from_store(cls.client, "0000034903"), cls.client.companyfacts("0000034903"))

    def g4(self, nf):
        return next(r for r in score_company(nf, "FRT", 6798, RULES, sector="reit").results if r.id == "G4")

    def test_2011_is_paid_through_the_equity_statement_line(self):
        r = self.g4(self.nf)
        # per-share dividends are tagged from 2012 only; 2011 has the statement-of-equity line DividendsCommonStockCash (ADR-012 fallback, 2026-10-12)
        self.assertEqual((r.label, r.by_year["2011"]["source"], r.by_year["2011"]["paid"]), ("partial_pass", "dividends_paid", True))

    def test_a_year_missing_inside_the_recorded_record_is_a_data_gap(self):
        """Federal Realty's real facts with 2016 removed (and the record starting in 2012, the first year with dividend data)."""
        nf = self.nf.model_copy(deep=True)
        for m in ("dividends_per_share", "dividends_paid"):
            nf.series[m].values = [v for v in nf.series[m].values if v.fiscal_year_end.year != 2016]
        nf.series["net_income"].values = [v for v in nf.series["net_income"].values if v.fiscal_year_end.year != 2011]
        r = self.g4(nf)
        self.assertEqual((r.label, r.reason, r.figures["unknown_years"]), ("data_gap", "dividend data missing for 2016", [2016]))

    def test_the_other_recorded_companies_are_unchanged(self):
        for t, label in (("KO", "partial_pass"), ("DUK", "partial_pass"), ("GOOGL", "fail"), ("TSLA", "fail")):
            g4 = next(r for r in score_ticker(self.client, t).results if r.id == "G4")
            self.assertEqual(g4.label, label, t)
            self.assertNotIn("unknown_years", g4.figures, t)


class TestRegistrantSuccessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())

    def test_the_successor_is_read_through_its_predecessor_until_it_files_a_10k(self):
        self.assertFalse(has_annual_report(self.client.submissions("0002115436")))
        self.assertEqual(self.client.source_for("0002115436"), ("0000034088", XOM_NOTE))
        self.assertEqual(self.client.source_for("0000034088"), ("0000034088", None))
        self.assertEqual(self.client.companyfacts("0002115436")["cik"], 34088)

    def test_every_value_keeps_its_true_accession_and_url(self):
        nf = normalise_from_store(self.client, "0002115436")
        self.assertEqual(nf.cik, "0000034088")
        vals = [v for s in nf.series.values() for v in s.values]
        self.assertTrue(vals)
        self.assertTrue(all("/data/34088/" in v.source_url and v.accession.replace("-", "") in v.source_url for v in vals))  # older years were filed through an agent: still true accessions
        newest = max(vals, key=lambda v: v.fiscal_year_end)
        self.assertEqual(newest.accession, "0000034088-26-000045")  # the FY2025 10-K
        ref = self.client.latest_filing("0002115436")
        self.assertEqual((ref.cik, ref.accession), ("0000034088", "0000034088-26-000045"))

    def test_the_config_records_its_evidence(self):
        entry = self.client.successors["0002115436"]
        self.assertEqual(entry["evidence"]["form"], "8-K12B")
        self.assertEqual(entry["evidence"]["accession"], "0001193125-26-291990")
        self.assertIn("000119312526291990", entry["evidence"]["url"])
        self.assertTrue(entry["reason"] and entry["predecessors"] == ["0000034088"])
        forms = self.client.submissions("0002115436")["filings"]["recent"]
        i = forms["accessionNumber"].index(entry["evidence"]["accession"])
        self.assertEqual((forms["form"][i], forms["filingDate"][i]), ("8-K12B", "2026-07-01"))  # the evidence filing is in the successor's own history

    def test_once_the_successor_files_its_own_10k_it_is_read_directly(self):
        c = EdgarClient("replay", Settings.from_env())
        own = {"filings": {"recent": {"form": ["10-K", "8-K12B"]}}}
        c.submissions = lambda cik: own if str(cik).lstrip("0") == "2115436" else EdgarClient.submissions(c, cik)
        self.assertEqual(c.source_for("0002115436"), ("0002115436", None))

    def test_the_numeric_result_carries_the_note_and_the_predecessors_figures(self):
        u = load_universe()
        r = score_numeric("XOM", edgar=self.client, universe=u)
        self.assertEqual((r["status"], r["cik"], r["source_notes"]), ("scored", "0002115436", [XOM_NOTE]))
        self.assertTrue(all("/data/34088/" in i["source_url"] for i in r["score"]["inputs"]))
        self.assertEqual(r["score"]["as_of_year"], 2025)

    def test_a_company_that_is_not_a_successor_has_no_source_note(self):
        u = load_universe()
        self.assertEqual(score_numeric("KO", edgar=self.client, universe=u)["source_notes"], [])

    def test_the_full_result_shows_the_note(self):
        u = load_universe()
        s = Settings.from_env()
        with tempfile.TemporaryDirectory() as d:
            # the qualitative path needs the predecessor's 10-K text, which is not recorded: only the plan and fetch are checked
            from unittest import mock
            with mock.patch("engine.orchestrator.assess_qualitative", side_effect=RuntimeError("no model in this test")):
                r = analyse("XOM", mode="replay", settings=s, universe=u, edgar=self.client, results_dir=Path(d), commit="t", write=False)
        self.assertIn(XOM_NOTE, r.plan.notes)
        fetch = next(st for st in r.steps if st.step == "fetch")  # the 10-K text itself is not recorded; the lookup must go to the predecessor's filing
        self.assertIn("edgar/0000034088/10-K/0000034088-26-000045", fetch.reason)


class TestNoAnnualReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())
        cls.u = load_universe()

    def test_spin_offs_have_no_succession_and_no_annual_report(self):
        for cik in ("0002089271", "0002128626"):
            self.assertNotIn(cik, self.client.successors)
            self.assertFalse(has_annual_report(self.client.submissions(cik)))
        with self.assertRaises(NoAnnualReportError):
            self.client.latest_filing("0002089271")

    def test_the_numeric_batch_records_a_status_not_a_failure(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = CompanyLedger(Path(d) / "numeric.json")
            out = []
            run_numeric_batch(["HONA", "VYLR", "KO"], universe=self.u, ledger=ledger, edgar=self.client, scores_dir=Path(d) / "scores", out=out.append)
            rows = {r["ticker"]: r for r in ledger.rows.values()}
            self.assertEqual({t: r["status"] for t, r in rows.items()}, {"HONA": "no_annual_report", "VYLR": "no_annual_report", "KO": "done"})
            self.assertEqual(rows["HONA"]["message"], "No annual report (10-K) filed yet; listed since 2026-06-29.")
            self.assertEqual(rows["VYLR"]["message"], "No annual report (10-K) filed yet; listed since 2026-10-01.")
            import json
            f = json.loads((Path(d) / "scores" / "0002089271.json").read_text())
            self.assertEqual((f["status"], f["score"], f["message"]), ("no_annual_report", None, rows["HONA"]["message"]))
            self.assertFalse(any("FAILED" in line for line in out))

    def test_a_later_run_checks_again(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = CompanyLedger(Path(d) / "numeric.json")
            run_numeric_batch(["HONA"], universe=self.u, ledger=ledger, edgar=self.client, scores_dir=Path(d) / "s", out=lambda m: None)
            again = run_numeric_batch(["HONA"], universe=self.u, ledger=ledger, edgar=self.client, scores_dir=Path(d) / "s", out=lambda m: None)
            self.assertEqual((again.done, again.skipped), (["HONA"], []))

    def test_the_full_path_reports_it_in_the_result_and_the_ledger(self):
        s = Settings.from_env()
        with tempfile.TemporaryDirectory() as d:
            r = analyse("HONA", mode="replay", settings=s, universe=self.u, edgar=self.client, results_dir=Path(d), commit="t")
        self.assertIsNone(r.scorecard)
        self.assertEqual({st.status for st in r.steps if st.step != "report"}, {"skipped"})
        self.assertEqual(r.cost.llm_calls, 0)
        self.assertEqual([w.message for w in r.warnings], ["No annual report (10-K) filed yet; listed since 2026-06-29."])
        key, row = row_from_result(r)
        self.assertEqual((key, row["status"]), ("0002089271", "no_annual_report"))

    def test_a_failure_is_still_a_failure(self):
        from engine.report import Result
        s = Settings.from_env()
        from unittest import mock
        with tempfile.TemporaryDirectory() as d, mock.patch("engine.orchestrator.normalise_from_store", side_effect=RuntimeError("boom")):
            r = analyse("KO", mode="replay", settings=s, universe=self.u, edgar=self.client, results_dir=Path(d), commit="t", write=False)
        self.assertEqual(row_from_result(r)[1]["status"], "failed")
        self.assertIsInstance(r, Result)


if __name__ == "__main__":
    unittest.main()
