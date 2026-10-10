"""Rankings builder (ADR-062): score maths, threshold, ties, exclusions, schema, Finnhub guard, determinism. Offline, on synthetic score files and the committed sample results."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from engine import cli
from engine.rankings import (ANALYSTS_PENDING, CRITERIA, MIN_DECIDED, SCHEMA_PATH, VALUATION_CAVEAT, Rankings, build_rankings, export_rankings_schema, rankings_json,
                             write_rankings)
from engine.report import PublishGateError, finnhub_fields
from engine.settings import REPO_ROOT
from engine.universe import Constituent, Universe


def labels(met=0, partial=0, fail=0, na=0, nm=0, gap=0, **fixed):
    """11 labels: the given counts first (over G1 to G5 and B1 to B4, so G6 and G7 are the last ones to be filled), then padded with data gaps; `fixed` overrides single criteria."""
    seq = ["pass"] * met + ["partial_pass"] * partial + ["fail"] * fail + ["not_applicable"] * na + ["not_meaningful"] * nm + ["data_gap"] * gap
    seq += ["data_gap"] * (len(CRITERIA) - len(seq))
    order = [c for c in CRITERIA if c not in ("G6", "G7")] + ["G6", "G7"]
    out = dict(zip(order, seq))
    out.update(fixed)
    return out


def score_file(cik, ticker, lab, **extra):
    d = {"status": "scored", "ticker": ticker, "cik": cik, "name": f"{ticker} Inc", "gics_sector": "Industrials", "gics_sub_industry": "Machinery", "sector_class": "other",
         "sector_notes": [], "source_notes": [], "fetched_at": "2026-10-10", "score": {"as_of_year": 2025, "results": [{"id": c, "label": lab[c]} for c in CRITERIA]}}
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
    def test_met_decided_and_what_is_left_out(self):
        u = universe(["AAA"])
        # 3 pass + 1 partial = 4 met; 2 fail; 1 not_applicable, 1 not_meaningful, 2 data_gap (G6, G7) left out
        self.env.put(u, "AAA", labels(met=3, partial=1, fail=2, na=1, nm=1, gap=3))
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.met, row.decided, row.data_gaps, row.score), (4, 6, 3, round(4 / 6, 6)))
        self.assertEqual(list(row.labels), CRITERIA)

    def test_partial_pass_counts_as_met(self):
        u = universe(["AAA"])
        self.env.put(u, "AAA", labels(met=5, partial=1))
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.met, row.decided, row.score), (6, 6, 1.0))
        self.assertEqual(row.labels["B1"], "partial_pass")

    def test_the_fraction_decides_not_the_count(self):
        u = universe(["BIG", "SMALL", "MID"])
        self.env.put(u, "BIG", labels(met=8, fail=2))        # 0.8
        self.env.put(u, "SMALL", labels(met=5, fail=1))      # 0.8333
        self.env.put(u, "MID", labels(met=7, fail=3))        # 0.7
        self.assertEqual(self.ranked(self.env.build(u)), ["SMALL", "BIG", "MID"])

    def test_close_fractions_are_compared_exactly(self):
        u = universe(["A", "B"])
        self.env.put(u, "A", labels(met=10, fail=1))  # 10/11
        self.env.put(u, "B", labels(met=9, fail=1))   # 9/10 = 0.9 < 0.90909
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["A", "B"])
        self.assertEqual([x.rank for x in r.criteria_ranking.ranked], [1, 2])


class TestThresholdAndTies(RankingsCase):
    def test_ranked_only_from_six_decided(self):
        self.assertEqual(MIN_DECIDED, 6)
        u = universe(["SIX", "FIVE"])
        self.env.put(u, "SIX", labels(met=6))
        self.env.put(u, "FIVE", labels(met=5))
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["SIX"])
        ins = r.criteria_ranking.insufficient_data
        self.assertEqual([(x.symbol, x.rank, x.score, x.met, x.decided) for x in ins], [("FIVE", None, None, 5, 5)])
        self.assertEqual(r.counts.model_dump(), {"universe": 2, "ranked": 1, "insufficient_data": 1, "excluded": 0})

    def test_ties_more_met_then_fewer_gaps_then_symbol(self):
        u = universe(["ZZ", "AA", "BB", "CC", "DD"])
        self.env.put(u, "ZZ", labels(met=6, fail=0, gap=5))     # 6/6, 5 gaps
        self.env.put(u, "AA", labels(met=8, fail=0, gap=3))     # 8/8, 3 gaps: more met wins over the 6/6s
        self.env.put(u, "BB", labels(met=6, fail=0, na=1, gap=4))  # 6/6, 4 gaps: fewer gaps than ZZ
        self.env.put(u, "CC", labels(met=6, fail=0, gap=5))     # 6/6, 5 gaps, same as ZZ: symbol decides (CC before ZZ)
        self.env.put(u, "DD", labels(met=3, fail=3, gap=5))     # 0.5
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["AA", "BB", "CC", "ZZ", "DD"])
        self.assertEqual([x.rank for x in r.criteria_ranking.ranked], [1, 2, 3, 4, 5])

    def test_the_order_does_not_depend_on_the_snapshot_order_or_file_order(self):
        syms = ["Q", "P", "O", "N"]
        for order in (syms, list(reversed(syms))):
            env = Env()
            self.addCleanup(env.close)
            u = universe(order)
            for s in syms:
                env.put(u, s, labels(met=7))
            self.assertEqual([x.symbol for x in env.build(u).criteria_ranking.ranked], ["N", "O", "P", "Q"])


class TestRowsAndExclusions(RankingsCase):
    def test_a_row_carries_sector_class_notes_year_and_the_valuation_caveat(self):
        u = universe(["REIT"])
        self.env.put(u, "REIT", labels(met=7), sector_class="reit", sector_notes=["REIT: note"], source_notes=["Figures from predecessor registrant X"], gics_sector="Real Estate")
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.gics_sector, row.sector_class, row.notes, row.as_of_fiscal_year, row.caveats), ("Real Estate", "reit", ["REIT: note", "Figures from predecessor registrant X"], 2025, [VALUATION_CAVEAT]))
        self.assertEqual((row.symbol, row.name, row.cik, row.has_full_analysis, row.analysis_path), ("REIT", "REIT Inc", "0000000001", False, None))

    def test_the_valuation_caveat_goes_when_g6_and_g7_are_decided(self):
        u = universe(["AAA", "BBB"])
        self.env.put(u, "AAA", labels(met=9, G6="pass", G7="fail"))
        self.env.put(u, "BBB", labels(met=9))
        r = self.env.build(u)
        by = {x.symbol: x for x in r.criteria_ranking.ranked}
        self.assertEqual((by["AAA"].caveats, by["BBB"].caveats), ([], [VALUATION_CAVEAT]))
        self.assertEqual(r.caveats, [VALUATION_CAVEAT])
        only = Env()
        self.addCleanup(only.close)
        only.put(u, "AAA", labels(met=9, G6="pass", G7="pass"))
        only.put(u, "BBB", labels(met=9, G6="fail", G7="pass"))
        self.assertEqual(only.build(u).caveats, [])

    def test_no_annual_report_is_excluded_with_its_reason(self):
        u = universe(["OK", "NEW"])
        self.env.put(u, "OK", labels(met=7))
        cik = u.row_for("NEW").cik
        (self.env.scores / f"{cik}.json").write_text(json.dumps({"status": "no_annual_report", "ticker": "NEW", "cik": cik, "name": "NEW Inc", "message": "No annual report (10-K) filed yet; listed since 2026-06-29.", "score": None}))
        r = self.env.build(u)
        self.assertEqual(self.ranked(r), ["OK"])
        self.assertEqual([(e.symbol, e.status, e.reason) for e in r.excluded], [("NEW", "no_annual_report", "No annual report (10-K) filed yet; listed since 2026-06-29.")])
        self.assertNotIn("NEW", [x.symbol for x in r.criteria_ranking.insufficient_data])

    def test_a_company_without_any_result_is_excluded_not_dropped(self):
        u = universe(["OK", "MISSING"])
        self.env.put(u, "OK", labels(met=7))
        r = self.env.build(u)
        self.assertEqual([(e.symbol, e.status) for e in r.excluded], [("MISSING", "not_scored")])
        self.assertEqual(r.counts.universe, 2)

    def test_files_of_companies_outside_the_snapshot_are_ignored(self):
        u = universe(["IN"])
        self.env.put(u, "IN", labels(met=7))
        (self.env.scores / "0009999999.json").write_text(json.dumps(score_file("0009999999", "OUT", labels(met=11))))
        self.assertEqual(self.ranked(self.env.build(u)), ["IN"])

    def test_full_analysis_is_flagged_and_a_full_result_can_stand_in_for_a_missing_score_file(self):
        ko = json.loads((REPO_ROOT / "results" / "0000021344.json").read_text())
        u = Universe([Constituent(symbol="KO", security="Coca-Cola", gics_sector="Consumer Staples", gics_sub_industry="Soft Drinks & Non-alcoholic Beverages", cik="0000021344", date_added="")], "2026-01-01", ["KO"])
        (self.env.results / "0000021344.json").write_text(json.dumps(ko))
        row = self.env.build(u).criteria_ranking.ranked[0]  # no score file: the scorecard of the full result is used
        self.assertEqual((row.has_full_analysis, row.analysis_path, row.sector_class, row.as_of_fiscal_year), (True, "results/0000021344.json", "other", ko["scorecard"]["as_of_year"]))
        self.assertEqual(row.met, ko["scorecard"]["summary"]["graham_met"] + ko["scorecard"]["summary"]["buffett_met"])
        self.env.put(u, "KO", labels(met=7))  # with a score file, the numbers come from it and the flag stays
        row = self.env.build(u).criteria_ranking.ranked[0]
        self.assertEqual((row.has_full_analysis, row.met), (True, 7))

    def test_data_as_of_and_attribution(self):
        u = universe(["A", "B"])
        self.env.put(u, "A", labels(met=7), fetched_at="2026-10-09")
        self.env.put(u, "B", labels(met=7), fetched_at="2026-10-11")
        r = self.env.build(u)
        self.assertEqual(r.data_as_of.model_dump(), {"sec_fetched_from": "2026-10-09", "sec_fetched_to": "2026-10-11", "constituents_snapshot": "2026-01-01"})
        self.assertEqual(r.attribution[0], "Constituents: Wikipedia, as of 2026-01-01 (CC BY-SA)")
        self.assertIn("U.S. Securities and Exchange Commission", r.attribution[1])
        self.assertIn("not financial advice", r.disclaimer)


class TestAnalystsFinnhubAndSchema(RankingsCase):
    def setUp(self):
        super().setUp()
        self.u = universe(["AAA", "BBB"])
        self.env.put(self.u, "AAA", labels(met=7))
        self.env.put(self.u, "BBB", labels(met=6, fail=1))
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
        self.assertEqual(finnhub_fields({"x": {"analyst_buy": 12}}), ["x.analyst_buy"])  # the guard itself still bites

    def test_the_write_applies_the_publish_gate(self):
        self.r.criteria_ranking.ranked[0].labels["price"] = "12.3"  # a Finnhub-shaped field sneaking into a row
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
        self.assertNotIn("generated", rankings_json(self.r))  # no wall-clock time

    def test_cli_builds_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "site" / "rankings.json"
            self.assertEqual(cli.main(["rankings", "--results-dir", str(self.env.results), "--out", str(out)]), 0)
            r = Rankings.model_validate_json(out.read_text())
        self.assertEqual(r.counts.universe, 500)  # the real snapshot; with these two synthetic CIKs nobody is scored


class TestCommittedRankings(unittest.TestCase):
    """site_data/rankings.json is committed; these checks need no local score files."""

    @classmethod
    def setUpClass(cls):
        cls.path = REPO_ROOT / "site_data" / "rankings.json"
        cls.data = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.r = Rankings.model_validate(cls.data)

    def test_it_validates_and_adds_up(self):
        jsonschema.validate(self.data, json.loads(SCHEMA_PATH.read_text()))
        c = self.r.counts
        self.assertEqual(c.ranked + c.insufficient_data + c.excluded, c.universe)
        self.assertEqual(c.ranked, len(self.r.criteria_ranking.ranked))
        self.assertEqual(self.r.caveats, [VALUATION_CAVEAT])
        self.assertEqual(finnhub_fields(self.data), [])
        self.assertEqual(self.r.ranking_by_analysts.rows, [])

    def test_ranks_follow_the_rule(self):
        rows = self.r.criteria_ranking.ranked
        self.assertEqual([x.rank for x in rows], list(range(1, len(rows) + 1)))
        keys = [(-x.met / x.decided, -x.met, x.data_gaps, x.symbol) for x in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertTrue(all(x.decided >= MIN_DECIDED and x.score == round(x.met / x.decided, 6) for x in rows))
        self.assertTrue(all(x.decided < MIN_DECIDED and x.rank is None for x in self.r.criteria_ranking.insufficient_data))
        self.assertTrue(all(VALUATION_CAVEAT in x.caveats for x in rows))

    def test_the_sample_companies_have_a_full_analysis_and_the_new_registrants_are_excluded(self):
        every = {x.symbol: x for x in self.r.criteria_ranking.ranked + self.r.criteria_ranking.insufficient_data}
        self.assertTrue(all(every[t].has_full_analysis for t in ("KO", "JPM", "GOOGL", "TSLA", "DUK")))
        self.assertEqual({e.symbol: e.status for e in self.r.excluded}, {"HONA": "no_annual_report", "VYLR": "no_annual_report"})

    def test_notes_travel_with_the_rows(self):
        every = {x.symbol: x for x in self.r.criteria_ranking.ranked + self.r.criteria_ranking.insufficient_data}
        self.assertTrue(every["PLD"].notes[0].startswith("REIT:"))
        self.assertTrue(every["XOM"].notes[0].startswith("Figures from predecessor registrant Exxon Mobil Corp (CIK 34088)"))
        self.assertTrue(every["MRSH"].notes[0].startswith("Insurance broker:"))
        self.assertEqual(every["NRG"].notes, ["Not rate-regulated, so Graham's utility variant does not apply."])


if __name__ == "__main__":
    unittest.main()
