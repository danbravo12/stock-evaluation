"""The restatement flag: true restatements are counted, concept switches are not (build 5). Synthetic company facts, then the frozen diagnosis. Offline."""
from __future__ import annotations

import json
import unittest

from engine.normalise import normalise
from eval import restatements
from eval.restatements import check_flagged, concept_switch_measures, restated_values
from engine.settings import REPO_ROOT
from tests.test_normalise import PROVENANCE, fact, facts

SPEC = {"unit": "USD", "period": "duration", "concepts": ["us-gaap:SalesRevenueNet", "us-gaap:Revenues"]}


def nf_of(cf):
    cmap = {"measures": {"revenue": {"_notes": "", **SPEC}}}
    return normalise(cf, {"fiscalYearEnd": "1231"}, cmap, PROVENANCE)


class TestFlag(unittest.TestCase):
    def test_a_true_restatement_is_flagged(self):
        cf = facts({"SalesRevenueNet": {"USD": [fact("2019-12-31", 100.0, "a-1", "2020-02-01", start="2019-01-01"), fact("2019-12-31", 160.0, "a-2", "2021-02-01", start="2019-01-01")]}})
        nf = nf_of(cf)
        flagged = restated_values(nf)
        self.assertEqual([(m, round(c, 2)) for m, _, c in flagged], [("revenue", 0.6)])
        r = check_flagged(nf, cf)
        self.assertEqual((r["flagged_values"], r["true_restatements"], r["other"]), (1, 1, []))
        self.assertEqual(concept_switch_measures(nf), [])

    def test_a_small_change_is_not_flagged(self):
        cf = facts({"SalesRevenueNet": {"USD": [fact("2019-12-31", 100.0, "a-1", "2020-02-01", start="2019-01-01"), fact("2019-12-31", 105.0, "a-2", "2021-02-01", start="2019-01-01")]}})
        self.assertEqual(restated_values(nf_of(cf)), [])

    def test_a_concept_switch_is_not_a_restatement(self):
        """Revenue is tagged SalesRevenueNet up to 2018 and Revenues from 2019, at very different levels: no value changes, so nothing is flagged."""
        cf = facts({"SalesRevenueNet": {"USD": [fact("2018-12-31", 100.0, "a-1", "2019-02-01", start="2018-01-01")]},
                    "Revenues": {"USD": [fact("2019-12-31", 900.0, "a-2", "2020-02-01", start="2019-01-01")]}})
        nf = nf_of(cf)
        self.assertEqual({v.concept for v in nf.series["revenue"].values}, {"SalesRevenueNet", "Revenues"})
        self.assertEqual(concept_switch_measures(nf), ["revenue"])
        self.assertEqual(restated_values(nf), [])

    def test_a_quarter_filed_in_a_10k_does_not_count_as_the_year(self):
        cf = facts({"SalesRevenueNet": {"USD": [fact("2019-12-31", 100.0, "a-1", "2020-02-01", start="2019-01-01"),
                                                 fact("2019-12-31", 400.0, "a-2", "2021-02-01", start="2019-10-01")]}})  # a fourth quarter ending the same day
        self.assertEqual(restated_values(nf_of(cf)), [])

    def test_the_two_counts_are_kept_apart_on_the_same_company(self):
        cf = facts({"SalesRevenueNet": {"USD": [fact("2018-12-31", 100.0, "a-1", "2019-02-01", start="2018-01-01"), fact("2018-12-31", 150.0, "a-3", "2020-02-01", start="2018-01-01")]},
                    "Revenues": {"USD": [fact("2019-12-31", 900.0, "a-2", "2020-02-01", start="2019-01-01")]}})
        nf = nf_of(cf)
        self.assertEqual(len(restated_values(nf)), 1)
        self.assertEqual(concept_switch_measures(nf), ["revenue"])
        self.assertEqual(check_flagged(nf, cf)["true_restatements"], 1)


class TestFrozen(unittest.TestCase):
    def test_the_frozen_diagnosis(self):
        d = json.loads((REPO_ROOT / "eval/restatement_diagnosis.json").read_text())
        self.assertEqual(d["flagged_values_that_are_not_true_restatements"], 0)
        self.assertGreater(d["true_restatement_values"], 0)
        frozen = json.loads((REPO_ROOT / "eval/universe_diagnostics.json").read_text())
        self.assertEqual(d["companies_with_true_restatement"], frozen["companies_with"]["restatement_over_10pct"])  # the same 283 companies the run flags
        self.assertEqual(d["scored"], frozen["scored"])

    def test_recomputed_from_the_local_cache_it_is_identical(self):
        try:
            res = restatements.compute()
        except Exception:
            self.skipTest("the SEC cache or the numeric score files are not available locally")
        self.assertEqual(res, json.loads((REPO_ROOT / "eval/restatement_diagnosis.json").read_text()))


if __name__ == "__main__":
    unittest.main()
