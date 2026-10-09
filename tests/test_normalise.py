"""Offline tests for the fact normaliser, using small synthetic company facts."""
from __future__ import annotations

import unittest
from datetime import date

from engine.contracts import NormalisedFacts
from engine.normalise import normalise

PROVENANCE = {"fetched_at": "2026-01-01T00:00:00+00:00", "sha256": "abc"}


def fact(end, val, accn, filed, start=None, form="10-K", fy=None, fp="FY"):
    f = {"end": end, "val": val, "accn": accn, "form": form, "filed": filed, "fp": fp, "fy": fy or int(end[:4])}
    if start:
        f["start"] = start
    return f


def facts(concepts: dict, taxonomy="us-gaap") -> dict:
    """concepts: {name: {unit: [fact, ...]}}"""
    return {
        "cik": 21344,
        "entityName": "TEST CO",
        "facts": {taxonomy: {name: {"units": units} for name, units in concepts.items()}},
    }


def run(companyfacts, spec, mmdd="1231", measure="m"):
    cmap = {"measures": {measure: {"_notes": "", **spec}}}
    return normalise(companyfacts, {"fiscalYearEnd": mmdd}, cmap, PROVENANCE).series[measure]


REV = {"unit": "USD", "period": "duration", "concepts": ["us-gaap:Revenues"]}
BAL = {"unit": "USD", "period": "instant", "concepts": ["us-gaap:AssetsCurrent"]}


class TestPeriodSelection(unittest.TestCase):
    def test_annual_duration_chosen_over_quarterly(self):
        cf = facts({"Revenues": {"USD": [
            fact("2024-12-31", 400, "a-1", "2025-02-01", start="2024-01-01"),
            fact("2024-09-30", 300, "q-3", "2024-10-30", start="2024-07-01", form="10-Q"),
            fact("2024-12-31", 100, "x-1", "2025-02-01", start="2024-10-01"),  # a quarter, even in a 10-K
        ]}})
        s = run(cf, REV)
        self.assertEqual([(v.fiscal_year_end, v.value) for v in s.values], [(date(2024, 12, 31), 400)])

    def test_instant_matched_to_fiscal_year_end(self):
        cf = facts({"AssetsCurrent": {"USD": [
            fact("2024-12-31", 50, "a-1", "2025-02-01"),
            fact("2024-06-30", 40, "a-1", "2025-02-01"),  # mid-year date, not a year end
        ]}})
        self.assertEqual([v.value for v in run(cf, BAL).values], [50])

    def test_52_53_week_year_ends(self):
        cf = facts({"Revenues": {"USD": [
            fact("2023-09-30", 1, "a-1", "2023-11-01", start="2022-10-02"),  # 52 weeks
            fact("2024-09-28", 2, "a-2", "2024-11-01", start="2023-10-01"),  # 52 weeks, ends 2 days early
            fact("2025-09-27", 3, "a-3", "2025-11-01", start="2024-09-29"),
        ]}})
        s = run(cf, REV, mmdd="0930")
        self.assertEqual([v.value for v in s.values], [1, 2, 3])
        bal = facts({"AssetsCurrent": {"USD": [fact("2024-09-28", 5, "a-2", "2024-11-01"),
                                               fact("2024-10-20", 6, "a-2", "2024-11-01")]}})
        self.assertEqual([v.value for v in run(bal, BAL, mmdd="0930").values], [5])

    def test_fy_and_fp_are_ignored(self):
        # The FY2023 comparative inside the FY2024 10-K carries fy=2024; it must still land in 2023.
        cf = facts({"Revenues": {"USD": [
            fact("2023-12-31", 10, "a-1", "2025-02-01", start="2023-01-01", fy=2024),
            fact("2024-12-31", 20, "a-1", "2025-02-01", start="2024-01-01", fy=2024),
        ]}})
        self.assertEqual([(v.fiscal_year_end.year, v.value) for v in run(cf, REV).values], [(2023, 10), (2024, 20)])

    def test_unit_mismatch_ignored_and_explained(self):
        cf = facts({"Revenues": {"EUR": [fact("2024-12-31", 9, "a-1", "2025-02-01", start="2024-01-01")]}})
        s = run(cf, REV)
        self.assertEqual(s.values, [])
        self.assertIn("unit mismatch", s.gaps[0].reason)


class TestRestatement(unittest.TestCase):
    def test_latest_filed_wins_and_original_kept(self):
        cf = facts({"Revenues": {"USD": [
            fact("2023-12-31", 100, "a-1", "2024-02-01", start="2023-01-01"),
            fact("2023-12-31", 120, "a-2", "2025-02-01", start="2023-01-01"),  # restated in the next 10-K
        ]}})
        v = run(cf, REV).values[0]
        self.assertEqual((v.value, v.accession, v.restated, v.original_value), (120, "a-2", True, 100))

    def test_tiny_difference_is_not_a_restatement(self):
        cf = facts({"Revenues": {"USD": [
            fact("2023-12-31", 1000, "a-1", "2024-02-01", start="2023-01-01"),
            fact("2023-12-31", 1003, "a-2", "2025-02-01", start="2023-01-01"),
        ]}})
        v = run(cf, REV).values[0]
        self.assertEqual((v.value, v.restated, v.original_value), (1003, False, None))


class TestConceptFallback(unittest.TestCase):
    SPEC = {"unit": "USD", "period": "duration", "concepts": ["us-gaap:Old", "us-gaap:New"]}

    def test_per_year_fallback_when_company_switches_tags(self):
        cf = facts({
            "Old": {"USD": [fact("2022-12-31", 1, "a-1", "2023-02-01", start="2022-01-01")]},
            "New": {"USD": [fact("2023-12-31", 2, "a-2", "2024-02-01", start="2023-01-01")]},
        })
        s = run(cf, self.SPEC)
        self.assertEqual([(v.concept, v.value) for v in s.values], [("Old", 1), ("New", 2)])

    def test_disagreement_adds_a_note_but_keeps_priority(self):
        both = lambda v: {"USD": [fact("2023-12-31", v, "a-1", "2024-02-01", start="2023-01-01")]}
        s = run(facts({"Old": both(100), "New": both(110)}), self.SPEC)
        self.assertEqual(s.values[0].value, 100)
        self.assertEqual(len(s.notes), 1)
        s = run(facts({"Old": both(100), "New": both(100.5)}), self.SPEC)
        self.assertEqual(s.notes, [])

    def test_derived_sum_only_when_all_parts_exist(self):
        spec = {"unit": "USD", "period": "duration", "concepts": [
            "us-gaap:Direct", {"sum": ["us-gaap:Dep", "us-gaap:Amort"]}]}
        year = lambda end, v, a: {"USD": [fact(end, v, a, "2025-02-01", start=end[:4] + "-01-01")]}
        cf = facts({
            "Dep": {"USD": year("2023-12-31", 7, "a-1")["USD"] + year("2024-12-31", 8, "a-2")["USD"]},
            "Amort": year("2023-12-31", 3, "a-1"),  # no 2024 amortisation
        })
        s = run(cf, spec)
        self.assertEqual(len(s.values), 1)
        v = s.values[0]
        self.assertEqual((v.value, v.derived, v.source_concepts), (10, True, ["us-gaap:Dep", "us-gaap:Amort"]))


class TestLastResortFallback(unittest.TestCase):
    SPEC = {"unit": "USD", "period": "duration", "concepts": [
        "us-gaap:Total",
        {"sum": ["us-gaap:Dep", "us-gaap:Amort"]},
        {"sum": ["us-gaap:Dep"], "note": "excludes amortisation (understates D&A)"},
    ]}

    @staticmethod
    def year(y, v):
        return fact(f"{y}-12-31", v, f"a-{y}", f"{y + 1}-02-01", start=f"{y}-01-01")

    def test_used_only_when_nothing_better_exists_and_is_flagged(self):
        y = self.year
        cf = facts({
            "Total": {"USD": [y(2020, 100)]},                           # 2020: direct concept
            "Dep": {"USD": [y(2020, 7), y(2021, 8), y(2022, 9)]},
            "Amort": {"USD": [y(2021, 2)]},                             # 2021: complete sum; 2022: Dep alone
        })
        s = run(cf, self.SPEC)
        got = {v.fiscal_year_end.year: (v.value, v.derived, v.concept) for v in s.values}
        self.assertEqual(got, {2020: (100, False, "Total"), 2021: (10, True, "Dep+Amort"), 2022: (9, True, "Dep")})
        self.assertEqual(s.values[-1].source_concepts, ["us-gaap:Dep"])
        self.assertEqual(len(s.notes), 3)  # two disagreements (2020, 2021) and the last-resort note (2022)
        self.assertTrue(any("2022-12-31" in n and "understates D&A" in n for n in s.notes))

    def test_nothing_else_means_a_gap_not_a_guess(self):
        spec = {"unit": "USD", "period": "duration", "concepts": ["us-gaap:Total"]}
        self.assertEqual(run(facts({"Dep": {"USD": [self.year(2022, 9)]}}), spec).values, [])


class TestConceptMapTags(unittest.TestCase):
    """The tags added after the first coverage report (KO and DUK)."""

    @classmethod
    def setUpClass(cls):
        from engine.normalise import load_concept_map
        cls.cmap = load_concept_map()["measures"]

    def test_older_ko_revenue_tag_only_fills_uncovered_years(self):
        y = TestLastResortFallback.year
        cf = facts({"Revenues": {"USD": [y(2016, 10), y(2017, 11)]},
                    "SalesRevenueGoodsNet": {"USD": [y(2008, 5), y(2016, 10), y(2017, 11)]}})
        s = run(cf, self.cmap["revenue"])
        self.assertEqual([(v.fiscal_year_end.year, v.concept) for v in s.values],
                         [(2008, "SalesRevenueGoodsNet"), (2016, "Revenues"), (2017, "Revenues")])

    def test_dividends_paid_switches_to_ordinary_dividends(self):
        y = TestLastResortFallback.year
        cf = facts({"PaymentsOfDividends": {"USD": [y(2020, 3)]}, "PaymentsOfOrdinaryDividends": {"USD": [y(2020, 3), y(2021, 4)]}})
        s = run(cf, self.cmap["dividends_paid"])
        self.assertEqual([(v.fiscal_year_end.year, v.concept) for v in s.values],
                         [(2020, "PaymentsOfDividends"), (2021, "PaymentsOfOrdinaryDividends")])


class TestGaps(unittest.TestCase):
    def test_missing_measure_and_missing_year(self):
        cmap = {"measures": {
            "a": {"_notes": "", **REV},
            "b": {"_notes": "", "unit": "USD", "period": "duration", "concepts": ["us-gaap:Other"]},
            "c": {"_notes": "", "unit": "USD", "period": "duration", "concepts": ["us-gaap:Absent"]},
        }}
        yr = lambda y, v: fact(f"{y}-12-31", v, f"a-{y}", f"{y + 1}-02-01", start=f"{y}-01-01")
        cf = facts({"Revenues": {"USD": [yr(2022, 1), yr(2023, 2), yr(2024, 3)]},
                    "Other": {"USD": [yr(2022, 1), yr(2024, 3)]}})
        out = normalise(cf, {"fiscalYearEnd": "1231"}, cmap, PROVENANCE).series
        self.assertEqual([g.fiscal_year_end for g in out["b"].gaps], [date(2023, 12, 31)])
        self.assertEqual(out["c"].gaps[0].fiscal_year_end, None)
        self.assertEqual(out["c"].gaps[0].reason, "no listed concept reported")

    def test_only_quarterly_data_is_explained(self):
        cf = facts({"Revenues": {"USD": [fact("2024-09-30", 3, "q", "2024-10-30", start="2024-07-01", form="10-Q")]}})
        self.assertIn("non-annual", run(cf, REV).gaps[0].reason)


class TestOutput(unittest.TestCase):
    def test_validates_as_pydantic_model_and_has_provenance(self):
        cf = facts({"Revenues": {"USD": [fact("2024-12-31", 4, "0000021344-25-000011", "2025-02-01", start="2024-01-01")]}})
        out = normalise(cf, {"fiscalYearEnd": "1231"}, {"measures": {"revenue": {"_notes": "", **REV}}}, PROVENANCE)
        again = NormalisedFacts.model_validate(out.model_dump())
        v = again.series["revenue"].values[0]
        self.assertEqual(v.source_url, "https://www.sec.gov/Archives/edgar/data/21344/000002134425000011/")
        self.assertEqual((again.cik, again.companyfacts_sha256), ("0000021344", "abc"))


class TestNormaliseFromStoreLiveOrder(unittest.TestCase):
    def test_the_store_is_read_only_after_the_first_fetch(self):
        """Found by the first live run (MET): in live mode the store has nothing until companyfacts() has fetched it."""
        from types import SimpleNamespace
        from unittest import mock
        from engine.normalise import normalise_from_store

        class LiveLike:
            def __init__(self):
                self.fetched = False
                self.store = SimpleNamespace(get=lambda key: SimpleNamespace(fetched_at="2026-01-01T00:00:00+00:00", sha256="x") if self.fetched else None)

            def companyfacts(self, cik):
                self.fetched = True
                return {"facts": {}}

            def submissions(self, cik):
                return {}
        with mock.patch("engine.normalise.normalise", side_effect=lambda facts, sub, cmap, meta: meta):
            self.assertEqual(normalise_from_store(LiveLike(), "1")["sha256"], "x")


if __name__ == "__main__":
    unittest.main()

