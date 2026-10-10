"""Rankings builder (ADR-062): score maths, threshold, ties, exclusions, schema, Finnhub guard, determinism. Offline, on synthetic score files and the committed sample results."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from engine import cli
from engine.rankings import (ANALYSTS_PENDING, CRITERIA, FINANCIAL_MIN_DECIDED, MIN_DECIDED, PENDING, SCHEMA_PATH, VALUATION_CAVEAT, Rankings, build_rankings, export_rankings_schema, rankings_json,
                             wilson_lower_bound, write_rankings)
from engine.report import PublishGateError, finnhub_fields
from engine.settings import REPO_ROOT
from engine.universe import Constituent, Universe


def labels(**over):
    """11 labels: G1 to G5 and B1 to B4 pass, G6 and G7 data gaps (they get the price reason below, so the builder reads them as pending); `over` overrides single criteria."""
    out = {c: "pass" for c in CRITERIA}
    out.update({"G6": "data_gap", "G7": "data_gap"})
    out.update(over)
    return out


def score_file(cik, ticker, lab, **extra):
    def row(c):
        r = {"id": c, "label": lab[c]}
        if c in ("G6", "G7") and lab[c] == "data_gap":
            r["reason"] = "price not available (Finnhub, ADR-007)"
        return r
    d = {"status": "scored", "ticker": ticker, "cik": cik, "name": f"{ticker} Inc", "gics_sector": "Industrials", "gics_sub_industry": "Machinery", "sector_class": "other",
         "sector_notes": [], "source_notes": [], "fetched_at": "2026-10-10", "score": {"as_of_year": 2025, "results": [row(c) for c in CRITERIA]}}
    d.update(extra)
    return d


def universe(symbols):
    rows = [Constituent(symbol=s, security=f"{s} Inc", gics_sector="Industrials", gics_sub_industry="Machinery", cik=f"{i + 1:010d}", date_added="") for i, s in enumerate(symbols)]
    return Universe(rows, "2026-01-01", [s for s in symbols])


class Env:
    """A temporary scores dir and results dir; `put` writes one company's score file."""

    def __init__(self):
        self._d = tempfile.TemporaryDirectory()
        self.results = Path(self._d.name)
        self.scores = self.results / "scores"
        self.scores.mkdir()

    def put(self, u, symbol, lab=None, **extra):
        cik = u.row_for(symbol).cik
        (self.scores / f"{cik}.json").write_text(json.dumps(score_file(cik, symbol, lab if lab is not None else labels(), **extra)), encoding="utf-8")

    def build(self, u):
        return build_rankings(u, self.scores, self.results)

    def close(self):
        self._d.cleanup()


class RankingsCase(unittest.TestCase):
    def setUp(self):
        self.env = Env()
        self.addCleanup(self.env.close)

    def ranked(self, r):
        return [x.symbol for x in r.criteria_ranking.ranked]


class TestScoreMaths(RankingsCase):
    def test_met_decided_gaps_and_pending(self):
        u = universe(["AAA"])
        # G1, G3, G4, G5 pass; G2 fail; B1 partial; B2 fail -> 7 decided, 5 met; B3 is a data gap; B4 does not apply; G6 and G7 wait for a price
        self.env.put(u, "AAA", labels(G2="fail", B1="partial_pass", B2="fail", B3="data_gap", B4="not_applicable"))
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.met, row.decided, row.data_gaps, row.percent_met, row.score), (5, 7, 1, 71.4, round(wilson_lower_bound(5, 7), 3)))
        self.assertEqual((row.labels["G6"], row.labels["G7"], row.labels["B3"]), (PENDING, PENDING, "data_gap"))
        self.assertEqual(list(row.labels), CRITERIA)

    def test_pending_valuation_is_not_a_gap_and_a_real_gap_still_is(self):
        u = universe(["AAA"])
        self.env.put(u, "AAA", labels())
        f = self.env.scores / f"{u.row_for('AAA').cik}.json"
        d = json.loads(f.read_text())
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.data_gaps, row.decided), (0, 9))  # G6 and G7 are neither gaps nor decided
        for r in d["score"]["results"]:
            if r["id"] == "G6":
                r["reason"] = "missing: eps_diluted [2025]"  # a gap for another reason stays a gap
        f.write_text(json.dumps(d))
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.labels["G6"], row.labels["G7"], row.data_gaps), ("data_gap", PENDING, 1))

    def test_partial_pass_counts_as_met(self):
        u = universe(["AAA"])
        self.env.put(u, "AAA", labels(G4="partial_pass"))
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.met, row.decided, row.percent_met), (9, 9, 100.0))

    def test_wilson_lower_bound_known_values(self):
        self.assertAlmostEqual(wilson_lower_bound(9, 9), 0.7006, places=3)
        self.assertAlmostEqual(wilson_lower_bound(0, 9), 0.0, places=6)
        self.assertAlmostEqual(wilson_lower_bound(5, 10), 0.2366, places=3)
        self.assertEqual(wilson_lower_bound(0, 0), 0.0)
        self.assertLess(wilson_lower_bound(5, 5), wilson_lower_bound(9, 10))
        self.assertLess(wilson_lower_bound(3, 3), wilson_lower_bound(5, 5))

    def test_evidence_beats_a_short_perfect_list(self):
        u = universe(["SEVEN", "NINE", "EIGHT"])
        self.env.put(u, "SEVEN", labels(B3="not_applicable", B4="not_applicable"))  # 7 of 7
        self.env.put(u, "NINE", labels())                                           # 9 of 9
        self.env.put(u, "EIGHT", labels(B4="not_applicable"))                       # 8 of 8
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["NINE", "EIGHT", "SEVEN"])
        self.assertEqual([x.score for x in r.criteria_ranking.ranked], [0.701, 0.676, 0.646])


class TestGroupsAndTies(RankingsCase):
    def test_the_main_ranking_needs_seven_decided_tests(self):
        self.assertEqual((MIN_DECIDED, FINANCIAL_MIN_DECIDED), (7, 4))
        u = universe(["SEVEN", "SIX"])
        self.env.put(u, "SEVEN", labels(B3="not_applicable", B4="not_applicable"))
        self.env.put(u, "SIX", labels(B2="not_applicable", B3="not_applicable", B4="not_applicable"))
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["SEVEN"])
        ins = r.criteria_ranking.insufficient_data
        self.assertEqual([(x.symbol, x.group, x.rank, x.score, x.met, x.decided) for x in ins], [("SIX", "insufficient_data", None, None, 6, 6)])
        self.assertEqual(r.counts.model_dump(), {"universe": 2, "ranked": 1, "ranked_financials": 0, "insufficient_data": 1, "excluded": 0})

    def test_banks_and_insurers_are_ranked_separately_from_four_decided_tests(self):
        u = universe(["BANK", "INS", "THIN", "IND"])
        five = labels(G2="not_applicable", B2="not_applicable", B3="not_applicable", B4="not_applicable")  # G1, G3, G4, G5, B1: 5 decided
        self.env.put(u, "BANK", five, sector_class="bank")
        self.env.put(u, "INS", {**five, "B1": "fail"}, sector_class="insurer")                         # 4 of 5
        self.env.put(u, "THIN", {**five, "G5": "data_gap", "B1": "data_gap"}, sector_class="bank")      # 3 decided
        self.env.put(u, "IND", five)                                                                    # an ordinary company with 5 decided: not enough for the main ranking
        r = self.env.build(u)
        cr = r.criteria_ranking
        self.assertEqual(self.ranked(r), [])
        self.assertEqual([(x.symbol, x.rank, x.group) for x in cr.ranked_financials], [("BANK", 1, "financials"), ("INS", 2, "financials")])
        self.assertEqual(sorted(x.symbol for x in cr.insufficient_data), ["IND", "THIN"])
        self.assertEqual(cr.ranked_financials[0].score, round(wilson_lower_bound(5, 5), 3))  # the same score as everyone else
        self.assertEqual(r.counts.ranked_financials, 2)

    def test_ties_higher_met_then_fewer_gaps_then_symbol(self):
        u = universe(["ZZ", "AA", "BB", "CC", "DD", "EE"])
        self.env.put(u, "AA", labels())                                                                    # 9 of 9
        self.env.put(u, "BB", labels(B4="data_gap"))                                                      # 8 of 8, 1 gap
        self.env.put(u, "EE", labels(B3="not_applicable", B4="not_applicable"))                           # 7 of 7, no gaps
        self.env.put(u, "CC", labels(B3="data_gap", B4="data_gap"))                                       # 7 of 7, 2 gaps
        self.env.put(u, "ZZ", labels(B3="data_gap", B4="data_gap"))                                       # same as CC: symbol decides
        self.env.put(u, "DD", labels(G2="fail", G3="fail", G4="fail"))                                    # 6 of 9
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["AA", "BB", "EE", "CC", "ZZ", "DD"])
        self.assertEqual([x.rank for x in r.criteria_ranking.ranked], [1, 2, 3, 4, 5, 6])

    def test_the_order_does_not_depend_on_the_snapshot_order_or_file_order(self):
        syms = ["Q", "P", "O", "N"]
        for order in (syms, list(reversed(syms))):
            env = Env()
            self.addCleanup(env.close)
            u = universe(order)
            for s in syms:
                env.put(u, s, labels())
            self.assertEqual([x.symbol for x in env.build(u).criteria_ranking.ranked], ["N", "O", "P", "Q"])


class TestRowsAndExclusions(RankingsCase):
    def test_a_row_carries_sector_class_notes_year_and_the_valuation_caveat(self):
        u = universe(["REIT"])
        self.env.put(u, "REIT", labels(), sector_class="reit", sector_notes=["REIT: note"], source_notes=["Figures from predecessor registrant X"], gics_sector="Real Estate")
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.gics_sector, row.sector_class, row.notes, row.as_of_fiscal_year, row.caveats), ("Real Estate", "reit", ["REIT: note", "Figures from predecessor registrant X"], 2025, [VALUATION_CAVEAT]))
        self.assertEqual((row.symbol, row.name, row.cik, row.has_full_analysis, row.analysis_path, row.group), ("REIT", "REIT Inc", "0000000001", False, None, "main"))

    def test_the_valuation_caveat_goes_when_g6_and_g7_are_decided(self):
        u = universe(["AAA", "BBB"])
        self.env.put(u, "AAA", labels(G6="pass", G7="fail"))
        self.env.put(u, "BBB", labels())
        r = self.env.build(u)
        by = {x.symbol: x for x in r.criteria_ranking.ranked}
        self.assertEqual((by["AAA"].caveats, by["BBB"].caveats), ([], [VALUATION_CAVEAT]))
        self.assertEqual((by["AAA"].decided, by["BBB"].decided), (11, 9))
        self.assertEqual(r.caveats, [VALUATION_CAVEAT])
        only = Env()
        self.addCleanup(only.close)
        only.put(u, "AAA", labels(G6="pass", G7="pass"))
        only.put(u, "BBB", labels(G6="fail", G7="pass"))
        self.assertEqual(only.build(u).caveats, [])

    def test_names_are_display_names(self):
        u = Universe([Constituent(symbol="KO", security="Coca-Cola Company (The)", gics_sector="Consumer Staples", gics_sub_industry="Soft Drinks", cik="0000000001", date_added="")], "2026-01-01", ["KO"])
        self.env.put(u, "KO", labels(), name="Coca-Cola Company (The)")
        self.assertEqual(self.env.build(u).criteria_ranking.ranked[0].name, "The Coca-Cola Company")

    def test_no_annual_report_is_excluded_with_its_reason(self):
        u = universe(["OK", "NEW"])
        self.env.put(u, "OK", labels())
        cik = u.row_for("NEW").cik
        (self.env.scores / f"{cik}.json").write_text(json.dumps({"status": "no_annual_report", "ticker": "NEW", "cik": cik, "name": "NEW Inc", "message": "No annual report (10-K) filed yet; listed since 2026-06-29.", "score": None}))
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["OK"])
        self.assertEqual([(e.symbol, e.status, e.reason) for e in r.excluded], [("NEW", "no_annual_report", "No annual report (10-K) filed yet; listed since 2026-06-29.")])
        self.assertNotIn("NEW", [x.symbol for x in r.criteria_ranking.insufficient_data])

    def test_a_company_without_any_result_is_excluded_not_dropped(self):
        u = universe(["OK", "MISSING"])
        self.env.put(u, "OK", labels())
        r = self.env.build(u)
        self.assertEqual([(e.symbol, e.status) for e in r.excluded], [("MISSING", "not_scored")])
        self.assertEqual(r.counts.universe, 2)

    def test_files_of_companies_outside_the_snapshot_are_ignored(self):
        u = universe(["IN"])
        self.env.put(u, "IN", labels())
        (self.env.scores / "0009999999.json").write_text(json.dumps(score_file("0009999999", "OUT", labels(G6="pass", G7="pass"))))
        self.assertEqual(self.ranked(self.env.build(u)), ["IN"])

    def test_full_analysis_is_flagged_and_a_full_result_can_stand_in_for_a_missing_score_file(self):
        ko = json.loads((REPO_ROOT / "results" / "0000021344.json").read_text())
        u = Universe([Constituent(symbol="KO", security="Coca-Cola Company (The)", gics_sector="Consumer Staples", gics_sub_industry="Soft Drinks & Non-alcoholic Beverages", cik="0000021344", date_added="")], "2026-01-01", ["KO"])
        (self.env.results / "0000021344.json").write_text(json.dumps(ko))
        row = self.env.build(u).criteria_ranking.ranked[0]  # no score file: the scorecard of the full result is used
        self.assertEqual((row.has_full_analysis, row.analysis_path, row.sector_class, row.as_of_fiscal_year), (True, "results/0000021344.json", "other", ko["scorecard"]["as_of_year"]))
        self.assertEqual(row.met, ko["scorecard"]["summary"]["graham_met"] + ko["scorecard"]["summary"]["buffett_met"])
        self.assertEqual((row.labels["G6"], row.data_gaps), (PENDING, 0))
        self.env.put(u, "KO", labels(G2="fail"))  # with a score file, the numbers come from it and the flag stays
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.has_full_analysis, row.met), (True, 8))

    def test_data_as_of_and_attribution(self):
        u = universe(["A", "B"])
        self.env.put(u, "A", labels(), fetched_at="2026-10-09")
        self.env.put(u, "B", labels(), fetched_at="2026-10-11")
        r = self.env.build(u)
        self.assertEqual(r.data_as_of.model_dump(), {"sec_fetched_from": "2026-10-09", "sec_fetched_to": "2026-10-11", "constituents_snapshot": "2026-01-01"})
        self.assertEqual(r.attribution[0], "Constituents: Wikipedia, as of 2026-01-01 (CC BY-SA)")
        self.assertIn("U.S. Securities and Exchange Commission", r.attribution[1])
        self.assertIn("not financial advice", r.disclaimer)


class TestAnalystsFinnhubAndSchema(RankingsCase):
    def setUp(self):
        super().setUp()
        self.u = universe(["AAA", "BBB"])
        self.env.put(self.u, "AAA", labels())
        self.env.put(self.u, "BBB", labels(G2="fail"))
        self.r = self.env.build(self.u)

    def test_the_analyst_section_is_empty_with_its_reason(self):
        self.assertEqual(self.r.ranking_by_analysts.model_dump(), {"status": "pending", "reason": ANALYSTS_PENDING, "rows": []})
        self.assertEqual(ANALYSTS_PENDING, "pending Finnhub permission (ADR-007, ADR-021)")

    def test_no_finnhub_fields_and_no_text_linking_the_two_rankings(self):
        data = json.loads(rankings_json(self.r))
        self.assertEqual(finnhub_fields(data), [])
        text = rankings_json(self.r).lower()
        for word in ("agree", "disagree", "contradict", "versus", "outperform", "better than the analysts"):
            self.assertNotIn(word, text)
        self.assertEqual(finnhub_fields({"x": {"analyst_buy": 12}}), ["x.analyst_buy"])

    def test_the_write_applies_the_publish_gate(self):
        self.r.criteria_ranking.ranked[0].labels["price"] = "12.3"
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PublishGateError):
                write_rankings(self.r, Path(d) / "r.json")
            self.assertFalse((Path(d) / "r.json").exists())
            write_rankings(self.r, Path(d) / "r.json", finnhub_public_ok=True)
            self.assertTrue((Path(d) / "r.json").exists())

    def test_output_validates_against_the_committed_schema_and_the_schema_is_current(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        jsonschema.validate(json.loads(rankings_json(self.r)), schema)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(export_rankings_schema(Path(d) / "s.json").read_text(), SCHEMA_PATH.read_text(), "schema/rankings.schema.json is stale: run `python -m engine.cli schema`")
        with self.assertRaises(jsonschema.ValidationError):
            bad = json.loads(rankings_json(self.r))
            del bad["criteria_ranking"]["ranked"][0]["met"]
            jsonschema.validate(bad, schema)

    def test_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = write_rankings(self.env.build(self.u), Path(d) / "a.json"), write_rankings(self.env.build(self.u), Path(d) / "b.json")
            self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertNotIn("generated", rankings_json(self.r))

    def test_cli_builds_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "site" / "rankings.json"
            self.assertEqual(cli.main(["rankings", "--results-dir", str(self.env.results), "--out", str(out)]), 0)
            r = Rankings.model_validate_json(out.read_text())
        self.assertEqual(r.counts.universe, 500)


class TestCommittedRankings(unittest.TestCase):
    """site_data/rankings.json is committed; these checks need no local score files."""

    @classmethod
    def setUpClass(cls):
        cls.path = REPO_ROOT / "site_data" / "rankings.json"
        cls.data = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.r = Rankings.model_validate(cls.data)
        cr = cls.r.criteria_ranking
        cls.every = {x.symbol: x for x in cr.ranked + cr.ranked_financials + cr.insufficient_data}

    def test_it_validates_and_adds_up(self):
        jsonschema.validate(self.data, json.loads(SCHEMA_PATH.read_text()))
        c, cr = self.r.counts, self.r.criteria_ranking
        self.assertEqual(c.ranked + c.ranked_financials + c.insufficient_data + c.excluded, c.universe)
        self.assertEqual((c.ranked, c.ranked_financials), (len(cr.ranked), len(cr.ranked_financials)))
        self.assertEqual(self.r.caveats, [VALUATION_CAVEAT])
        self.assertEqual(finnhub_fields(self.data), [])
        self.assertEqual(self.r.ranking_by_analysts.rows, [])

    def test_groups_thresholds_and_order(self):
        cr = self.r.criteria_ranking
        for rows, floor in ((cr.ranked, MIN_DECIDED), (cr.ranked_financials, FINANCIAL_MIN_DECIDED)):
            self.assertEqual([x.rank for x in rows], list(range(1, len(rows) + 1)))
            keys = [(-round(wilson_lower_bound(x.met, x.decided), 9), -x.met, x.data_gaps, x.symbol) for x in rows]
            self.assertEqual(keys, sorted(keys))
            self.assertTrue(all(x.decided >= floor and x.score == round(wilson_lower_bound(x.met, x.decided), 3) for x in rows))
        self.assertTrue(all(x.sector_class not in ("bank", "insurer") and x.group == "main" for x in cr.ranked))
        self.assertTrue(all(x.sector_class in ("bank", "insurer") and x.group == "financials" for x in cr.ranked_financials))
        self.assertTrue(all(x.rank is None and x.score is None and x.group == "insufficient_data" for x in cr.insufficient_data))
        for x in cr.insufficient_data:
            self.assertTrue(x.decided < (FINANCIAL_MIN_DECIDED if x.sector_class in ("bank", "insurer") else MIN_DECIDED), x.symbol)
        self.assertTrue(all(VALUATION_CAVEAT in x.caveats for x in cr.ranked))

    def test_pending_valuation_is_not_a_gap(self):
        for x in self.every.values():
            self.assertEqual(x.data_gaps, sum(l == "data_gap" for l in x.labels.values()), x.symbol)
            self.assertEqual(x.decided, sum(l in ("pass", "partial_pass", "fail") for l in x.labels.values()), x.symbol)
            self.assertEqual((x.labels["G6"], x.labels["G7"]), (PENDING, PENDING), x.symbol)

    def test_the_sample_companies_have_a_full_analysis_and_the_new_registrants_are_excluded(self):
        self.assertTrue(all(self.every[t].has_full_analysis for t in ("KO", "JPM", "GOOGL", "TSLA", "DUK")))
        self.assertEqual({e.symbol: e.status for e in self.r.excluded}, {"HONA": "no_annual_report", "VYLR": "no_annual_report"})

    def test_notes_and_display_names_travel_with_the_rows(self):
        self.assertTrue(self.every["PLD"].notes[0].startswith("REIT:"))
        self.assertTrue(self.every["XOM"].notes[0].startswith("Figures from predecessor registrant Exxon Mobil Corp (CIK 34088)"))
        self.assertTrue(self.every["MRSH"].notes[0].startswith("Insurance broker:"))
        self.assertEqual(self.every["NRG"].notes, ["Not rate-regulated, so Graham's utility variant does not apply."])
        self.assertEqual(self.every["KO"].name, "The Coca-Cola Company")


if __name__ == "__main__":
    unittest.main()
