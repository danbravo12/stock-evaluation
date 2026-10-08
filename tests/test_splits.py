"""Split adjustment: synthetic cases and the real GOOGL / TSLA / KO / DUK fixtures."""
from __future__ import annotations

import unittest
from datetime import date

from engine.fetch.edgar import EdgarClient
from engine.normalise import normalise_from_store
from engine.score.common import Facts
from engine.settings import Settings
from engine.splits import adjust_for_splits, candidate_splits
from tests.synthetic import facts, value


def ratio_facts(*instants):
    """Company facts with split-ratio instant facts: (date, ratio)."""
    return {"facts": {"us-gaap": {"StockholdersEquityNoteStockSplitConversionRatio1": {
        "units": {"pure": [{"end": d, "val": r, "form": "10-Q", "filed": d} for d, r in instants]}}}}}


class TestSynthetic(unittest.TestCase):
    def eps_series(self):
        nf = facts({"eps_diluted": {2018: 8.0, 2019: 2.5}})
        vals = nf.series["eps_diluted"].values
        # 2019 was first reported as 10.0 and restated to 2.5 in a 10-K filed after the split
        vals[1] = vals[1].model_copy(update={"filed": date(2021, 2, 1), "restated": True, "original_value": 10.0})
        return nf

    def test_values_filed_before_the_split_are_rescaled_and_recorded(self):
        out = adjust_for_splits(self.eps_series(), ratio_facts(("2020-06-01", 4)))
        a, b = out.series["eps_diluted"].values
        self.assertEqual((a.value, a.split_factor, a.value_before_split), (2.0, 4.0, 8.0))
        self.assertEqual((b.value, b.split_factor), (2.5, 1.0))  # filed after the split: already on the new basis

    def test_share_counts_are_multiplied(self):
        nf = facts({"eps_diluted": {2018: 8.0, 2019: 2.5}, "diluted_shares": {2018: 100.0}})
        nf.series["eps_diluted"].values[1] = nf.series["eps_diluted"].values[1].model_copy(
            update={"filed": date(2021, 2, 1), "restated": True, "original_value": 10.0})
        out = adjust_for_splits(nf, ratio_facts(("2020-06-01", 4)))
        self.assertEqual(out.series["diluted_shares"].values[0].value, 400.0)

    def test_split_without_restatement_evidence_is_not_applied_but_noted(self):
        out = adjust_for_splits(facts({"eps_diluted": {2018: 8.0}}), ratio_facts(("2020-06-01", 4)))
        self.assertEqual(out.series["eps_diluted"].values[0].value, 8.0)
        self.assertTrue(any("not applied" in n for n in out.series["eps_diluted"].notes))

    def test_restatement_no_split_fact_explains_is_noted(self):
        out = adjust_for_splits(self.eps_series(), {"facts": {}})
        self.assertTrue(any("no split fact explains" in n for n in out.series["eps_diluted"].notes))
        self.assertEqual(out.series["eps_diluted"].values[0].value, 8.0)  # nothing guessed

    def test_announcement_and_effective_dates_are_one_split(self):
        splits = candidate_splits(ratio_facts(("2022-02-01", 20), ("2022-07-15", 20), ("2014-04-02", 2)))
        self.assertEqual([(s.ratio, s.date) for s in splits], [(2.0, date(2014, 4, 2)), (20.0, date(2022, 7, 15))])

    def test_input_is_not_mutated(self):
        nf = self.eps_series()
        adjust_for_splits(nf, ratio_facts(("2020-06-01", 4)))
        self.assertEqual(nf.series["eps_diluted"].values[0].value, 8.0)


class TestFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = EdgarClient("replay", Settings.from_env())
        cls.adj = {}
        for t in ("KO", "GOOGL", "TSLA", "DUK"):
            cik = client.lookup_cik(t)[0]
            cls.adj[t] = (adjust_for_splits(normalise_from_store(client, cik), client.companyfacts(cik)), client.companyfacts(cik))

    def eps(self, t, year):
        return Facts(self.adj[t][0]).get("eps_diluted", year)

    def test_alphabet_20_for_1_in_2022(self):
        v = self.eps("GOOGL", 2016)
        self.assertEqual(v.split_factor, 20.0)
        self.assertAlmostEqual(v.value, v.value_before_split / 20)
        self.assertLess(v.value, 2.0)  # 27.85 before adjustment
        self.assertEqual(self.eps("GOOGL", 2025).split_factor, 1.0)

    def test_tesla_5_for_1_in_2020_and_3_for_1_in_2022(self):
        self.assertEqual(self.eps("TSLA", 2015).split_factor, 15.0)  # both splits came after its latest filing
        self.assertEqual(self.eps("TSLA", 2018).split_factor, 3.0)  # restated for 5:1 already, 3:1 still to come
        self.assertEqual(self.eps("TSLA", 2020).split_factor, 1.0)
        self.assertAlmostEqual(self.eps("TSLA", 2018).value, -0.38, places=2)

    def test_coca_cola_2_for_1_in_2012(self):
        v = self.eps("KO", 2007)
        self.assertEqual(v.split_factor, 2.0)
        self.assertAlmostEqual(v.value, 1.285, places=2)
        shares = Facts(self.adj["KO"][0]).get("diluted_shares", 2007)
        self.assertEqual(shares.split_factor, 2.0)
        self.assertGreater(shares.value, 4e9)

    def test_duke_reverse_split_applied_but_merger_ratio_is_not(self):
        self.assertEqual(len(candidate_splits(self.adj["DUK"][1])), 2)  # a 1-for-3 reverse split and a merger exchange ratio
        v = self.eps("DUK", 2008)
        self.assertAlmostEqual(v.split_factor, 1 / 3)
        self.assertTrue(any("0.8708" in n and "not applied" in n for n in self.adj["DUK"][0].series["eps_diluted"].notes))


if __name__ == "__main__":
    unittest.main()
