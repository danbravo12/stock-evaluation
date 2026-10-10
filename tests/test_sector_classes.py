"""GICS sector classes, the REIT flag, SIC fallback (ADR-057, ADR-058) and the numeric-only path (ADR-059). Offline."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import cli
from engine.batch import CompanyLedger, run_numeric_batch
from engine.fetch.edgar import EdgarClient
from engine.normalise import normalise_from_store
from engine.numeric import diagnose, score_numeric
from engine.planner import plan_for
from engine.score import score_company, score_ticker
from engine.score.common import load_sector_rules, resolve_sector, sector_class
from engine.settings import Settings
from engine.splits import adjust_for_splits
from engine.universe import Constituent, Universe, load_universe

REIT_NOTE = "REIT: structurally debt-funded and required to distribute most taxable income; B1/B2 results reflect that structure."
RULES = load_sector_rules()


def res(sub=None, sic=None, cik=None):
    return resolve_sector(RULES, sic=sic, gics_sub_industry=sub, cik=cik)


class TestResolution(unittest.TestCase):
    def test_gics_sub_industries_map_to_the_agreed_classes(self):
        cases = {"Diversified Banks": "bank", "Regional Banks": "bank", "Consumer Finance": "bank", "Life & Health Insurance": "insurer", "Multi-line Insurance": "insurer",
                 "Property & Casualty Insurance": "insurer", "Reinsurance": "insurer", "Insurance Brokers": "other", "Electric Utilities": "utility", "Gas Utilities": "utility",
                 "Multi-Utilities": "utility", "Water Utilities": "utility", "Independent Power Producers & Energy Traders": "other", "Industrial REITs": "reit",
                 "Retail REITs": "reit", "Data Center REITs": "reit", "Telecom Tower REITs": "reit", "Timber REITs": "reit", "Managed Health Care": "other",
                 "Asset Management & Custody Banks": "other", "Investment Banking & Brokerage": "other", "Real Estate Services": "other", "Soft Drinks & Non-alcoholic Beverages": "other"}
        for sub, cls in cases.items():
            self.assertEqual(res(sub)[0], cls, sub)

    def test_gics_beats_sic_and_says_why(self):
        cls, basis, why = res("Managed Health Care", sic=6324)  # SIC would say insurer; the GICS view is health care
        self.assertEqual((cls, basis), ("other", "gics:Managed Health Care (no exception rule)"))
        self.assertTrue(why)
        self.assertEqual(sector_class(6324, RULES), "insurer")
        self.assertEqual(res("Consumer Finance", sic=6141)[0], "bank")
        self.assertIn("gics:Consumer Finance", res("Consumer Finance")[1])
        self.assertTrue(res("Consumer Finance")[2])

    def test_a_cik_override_beats_gics_and_sic(self):
        bny = "0001390777"
        self.assertEqual(res("Asset Management & Custody Banks", cik=bny)[0], "bank")
        self.assertTrue(res("Asset Management & Custody Banks", cik=bny)[1].startswith("override:"))
        self.assertEqual(res("Asset Management & Custody Banks", cik="0000000001")[0], "other")  # an ordinary asset manager
        for cik in RULES["cik_overrides"].values():
            self.assertTrue(cik["why"])

    def test_sic_is_only_the_fallback_for_tickers_outside_the_snapshot(self):
        self.assertEqual(res("Made-up Industry", sic=6021)[0], "other")  # in the snapshot, no rule: ordinary company, SIC not consulted
        self.assertEqual(res("Made-up Industry")[0], "other")
        self.assertEqual(res(None, sic=4911)[0], "utility")  # a ticker outside the snapshot: SIC only
        self.assertEqual(res(None, sic=6311)[0], "insurer")
        self.assertEqual(res(None, sic=None)[0], "other")

    def test_every_rule_has_a_reason_and_a_valid_class(self):
        for name, r in RULES["gics_sub_industries"].items():
            self.assertIn(r["class"], {"bank", "insurer", "utility", "reit"} | ({"other"} if r.get("note") else set()), name)  # an explicit 'other' carries its note
            self.assertTrue(r["why"], name)

    def test_no_reit_insurance_or_utility_sub_industry_of_the_snapshot_silently_falls_to_other(self):
        u = load_universe()
        for r in u.primary:
            s = r.gics_sub_industry
            if "REIT" in s or "Insurance" in s or r.gics_sector == "Utilities":
                self.assertIn(s, RULES["gics_sub_industries"], f"{r.symbol}: {s} has no sector rule")

    def test_the_planner_uses_gics_and_records_the_basis(self):
        row = Constituent(symbol="PLD", security="Prologis", gics_sector="Real Estate", gics_sub_industry="Industrial REITs", cik="0001045609", date_added="")
        p = plan_for("PLD", Universe([row], "2026-01-01", []), sic=6798)
        self.assertEqual((p.sector_class, p.not_applicable, p.sector_basis), ("reit", [], "gics:Industrial REITs"))
        self.assertEqual(p.sector_notes, [REIT_NOTE])
        self.assertEqual(sorted(p.applicable), sorted([f"G{i}" for i in range(1, 8)] + [f"B{i}" for i in range(1, 5)]))


class TestReitFlag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())
        cls.nf = adjust_for_splits(normalise_from_store(cls.client, "0001045609"), cls.client.companyfacts("0001045609"))

    def test_the_reit_note_is_on_the_scoreset_and_the_labels_are_unchanged(self):
        sic = self.client.submissions("0001045609").get("sic")
        as_reit = score_company(self.nf, "PLD", sic, RULES, sector="reit")
        as_other = score_company(self.nf, "PLD", sic, RULES, sector="other")
        self.assertEqual(as_reit.sector_notes, [REIT_NOTE])
        self.assertEqual(as_other.sector_notes, [])
        self.assertEqual([(r.id, r.label, r.figures) for r in as_reit.results], [(r.id, r.label, r.figures) for r in as_other.results])
        self.assertEqual(score_ticker(self.client, "PLD").sector_class, "reit")  # via the snapshot's GICS row

    def test_non_reits_carry_no_note_and_the_five_test_companies_keep_their_classes(self):
        got = {t: score_ticker(self.client, t) for t in ["KO", "JPM", "GOOGL", "TSLA", "DUK"]}
        self.assertEqual({t: s.sector_class for t, s in got.items()}, {"KO": "other", "JPM": "bank", "GOOGL": "other", "TSLA": "other", "DUK": "utility"})
        self.assertTrue(all(s.sector_notes == [] for s in got.values()))


class TestNumericOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = Settings.from_env()
        cls.edgar = EdgarClient("replay", cls.settings)
        cls.universe = load_universe(sec_tickers=cls.edgar.company_tickers())

    def test_one_company_numeric_result_has_score_notes_and_diagnostics_and_never_touches_the_10k_or_a_model(self):
        with mock.patch("engine.llm.client.LLMClient", side_effect=AssertionError("no model client in numeric mode")), \
             mock.patch.object(EdgarClient, "filing_document", side_effect=AssertionError("no 10-K download")), \
             mock.patch.object(EdgarClient, "latest_filing", side_effect=AssertionError("no 10-K lookup")):
            r = score_numeric("PLD", edgar=self.edgar, universe=self.universe)
        self.assertEqual((r["ticker"], r["sector_class"], r["sector_notes"]), ("PLD", "reit", [REIT_NOTE]))
        self.assertEqual(len(r["score"]["results"]), 11)
        self.assertIn("g4_fail_with_13_or_more_paid", r["diagnostics"])
        json.dumps(r)  # JSON-ready

    def test_a_crash_in_one_company_is_a_failed_row_and_the_batch_continues(self):
        def flaky(sym, **kw):
            if sym == "JPM":
                raise KeyError("net_income")
            return score_numeric(sym, **kw)
        with tempfile.TemporaryDirectory() as d:
            ledger = CompanyLedger(Path(d) / "numeric.json")
            out = []
            o = run_numeric_batch(["KO", "JPM", "DUK"], universe=self.universe, ledger=ledger, edgar=self.edgar, scores_dir=Path(d) / "scores", score_fn=flaky, out=out.append)
            self.assertEqual(o.done, ["KO", "JPM", "DUK"])
            rows = {r["ticker"]: r for r in ledger.rows.values()}
            self.assertEqual((rows["KO"]["status"], rows["JPM"]["status"], rows["DUK"]["status"]), ("done", "failed", "done"))
            self.assertIn("KeyError: 'net_income'", rows["JPM"]["message"])
            self.assertEqual(sorted(p.name for p in (Path(d) / "scores").iterdir()), ["0000021344.json", "0001326160.json"])
            again = run_numeric_batch(["KO", "JPM", "DUK"], universe=self.universe, ledger=ledger, edgar=self.edgar, scores_dir=Path(d) / "scores", score_fn=score_numeric, out=out.append)
            self.assertEqual((again.skipped, again.done), (["KO", "DUK"], ["JPM"]))  # failed rows are retried, done rows skipped

    def test_cli_numeric_only_defaults_to_live_writes_scores_and_its_own_ledger(self):
        modes = []

        def fake_edgar(mode, settings):
            modes.append(mode)
            return EdgarClient("replay", settings)
        with tempfile.TemporaryDirectory() as d:
            env = {"LEDGER_PATH": str(Path(d) / "usage.json"), "RESULTS_DIR": str(Path(d) / "results")}
            with mock.patch.dict(os.environ, env), mock.patch.object(cli, "EdgarClient", fake_edgar), mock.patch.object(cli, "PROGRESS_PATH", Path(d) / "P.md"):
                self.assertEqual(cli.main(["batch", "--tickers", "KO", "JPM", "--numeric-only"]), 0)
                self.assertEqual(modes[-1], "live")
                self.assertEqual(sorted(p.name for p in (Path(d) / "results" / "scores").iterdir()), ["0000019617.json", "0000021344.json", "_run.json"])
                self.assertTrue((Path(d) / "numeric.json").exists())
                self.assertFalse((Path(d) / "companies.json").exists())  # does not mark anything as fully analysed
                self.assertEqual(cli.main(["batch", "--tickers", "KO", "--numeric-only", "--mode", "replay"]), 2)

    def test_diagnose_flags_mapping_smells(self):
        nf = normalise_from_store(self.edgar, "0001045609")
        score = score_company(nf, "PLD", None, RULES, sector="reit")
        d = diagnose(nf, score)
        self.assertEqual(d["g4_fail_with_13_or_more_paid"], None)  # fixed by ADR-060
        from tests.synthetic import facts
        years = list(range(2016, 2026))
        syn = facts({"net_income": {y: 100.0 for y in years}, "revenue": {y: (100.0 if y != 2020 else 700.0) for y in years}, "eps_diluted": {y: (1.0 if y != 2018 else -1.0) for y in years}})
        d2 = diagnose(syn, score_company(syn, "T", None, RULES))
        self.assertEqual([j["year"] for j in d2["revenue_jumps"]], [2020, 2021])
        self.assertEqual([m["year"] for m in d2["eps_sign_mismatch"]], [2018])


if __name__ == "__main__":
    unittest.main()
