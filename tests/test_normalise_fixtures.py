"""Normaliser checks against the real recorded fixtures (replay mode, no network)."""
from __future__ import annotations

import unittest

from engine.fetch.edgar import EdgarClient
from engine.normalise import load_concept_map, normalise_from_store
from engine.settings import Settings

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]


class TestFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = EdgarClient("replay", Settings.from_env())
        cmap = load_concept_map()
        cls.facts = {t: normalise_from_store(client, client.lookup_cik(t)[0], cmap) for t in TICKERS}

    def test_ten_years_of_core_measures(self):
        for t, nf in self.facts.items():
            for m in ("revenue", "net_income", "eps_diluted"):
                self.assertGreaterEqual(len(nf.series[m].values), 10, f"{t} {m}")

    def test_tesla_lost_money_in_an_early_year(self):
        early = [v for v in self.facts["TSLA"].series["net_income"].values if v.fiscal_year_end.year <= 2019]
        self.assertTrue(any(v.value < 0 for v in early))

    def test_bank_has_no_current_assets_or_liabilities(self):
        for m in ("current_assets", "current_liabilities"):
            s = self.facts["JPM"].series[m]
            self.assertEqual(s.values, [])
            self.assertIsNone(s.gaps[0].fiscal_year_end)

    def test_ko_revenue_reaches_back_to_2007_or_2008(self):
        self.assertLessEqual(self.facts["KO"].series["revenue"].values[0].fiscal_year_end.year, 2008)

    def test_tesla_depreciation_falls_back_to_flagged_depreciation_alone(self):
        s = self.facts["TSLA"].series["depreciation_amortization"]
        recent = {v.fiscal_year_end.year: v for v in s.values if v.fiscal_year_end.year >= 2022}
        self.assertEqual(sorted(recent), [2022, 2023, 2024, 2025])
        self.assertTrue(all(v.derived and v.source_concepts == ["us-gaap:Depreciation"] for v in recent.values()))
        self.assertTrue(any("understates D&A" in n for n in s.notes))

    def test_alphabet_depreciation_is_still_mostly_a_gap(self):
        s = self.facts["GOOGL"].series["depreciation_amortization"]
        self.assertTrue(all(v.fiscal_year_end.year >= 2021 for v in s.values))
        self.assertLessEqual(len(s.values), 5)  # nothing before 2021, so 2013–2020 stay uncovered

    def test_duke_dividends_paid_covers_recent_years(self):
        years = {v.fiscal_year_end.year for v in self.facts["DUK"].series["dividends_paid"].values}
        self.assertTrue({2023, 2024, 2025} <= years)

    def test_every_value_has_provenance(self):
        for t, nf in self.facts.items():
            for s in nf.series.values():
                for v in s.values:
                    self.assertTrue(v.concept and v.accession and v.filed, f"{t} {s.measure}")
                    self.assertTrue(v.source_url.startswith("https://www.sec.gov/Archives/edgar/data/"))


if __name__ == "__main__":
    unittest.main()
