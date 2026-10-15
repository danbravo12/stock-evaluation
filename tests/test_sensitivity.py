"""Threshold sensitivity (build 4b, ADR-074): the thresholds module, the method on the recorded fixtures, determinism and the frozen file. Offline."""
from __future__ import annotations

import json
import unittest

from eval import sensitivity
from eval.sensitivity import labels_of, prepare_all, sensitivity as run
from engine.fetch.edgar import EdgarClient
from engine.score import score_company
from engine.score.common import load_sector_rules
from engine.score.thresholds import CURRENT, DEFAULT, NAMES, T, override, scaled
from engine.settings import REPO_ROOT, Settings
from engine.universe import load_universe

TICKERS = json.loads((REPO_ROOT / "config/test_tickers.json").read_text())["tickers"]


class TestThresholds(unittest.TestCase):
    def test_defaults_are_the_published_thresholds(self):
        d = DEFAULT
        self.assertEqual((d.g1_min_revenue, d.g2_current_ratio, d.g5_growth_ratio, d.b1_roe, d.b1_min_years, d.b2_debt_multiple, d.b3_margin_ratio, d.b4_min_positive_years),
                         (1e9, 2.0, 1.33, 0.15, 7, 4.0, 0.9, 8))
        self.assertEqual((d.g6_max_pe, d.g7_max_pe_x_pb, d.g2_utility_debt_equity), (15.0, 22.5, 2.0))

    def test_scaling_rounds_year_counts_and_leaves_no_float_noise(self):
        self.assertEqual((scaled("b1_min_years", 0.8), scaled("b1_min_years", 1.2)), (6, 8))  # 5.6 and 8.4
        self.assertEqual((scaled("b4_min_positive_years", 0.8), scaled("b4_min_positive_years", 1.2)), (6, 10))  # 6.4 and 9.6
        self.assertEqual((scaled("b3_margin_ratio", 0.8), scaled("g1_min_revenue", 1.2)), (0.72, 1.2e9))
        self.assertEqual(len(NAMES), 12)

    def test_override_restores_on_exit_and_after_an_error(self):
        with override(g1_min_revenue=5.0):
            self.assertEqual(T().g1_min_revenue, 5.0)
            with override(b1_roe=0.5):
                self.assertEqual((T().g1_min_revenue, T().b1_roe), (5.0, 0.5))
        self.assertEqual(T(), DEFAULT)
        with self.assertRaises(ZeroDivisionError):
            with override(g1_min_revenue=5.0):
                1 / 0
        self.assertEqual(T(), DEFAULT)
        self.assertIs(CURRENT, DEFAULT)


class TestMethodOnFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        edgar = EdgarClient("replay", Settings.from_env())
        cls.prepared = prepare_all(edgar, load_universe(), TICKERS)
        cls.res = run(cls.prepared)

    def test_the_baseline_labels_are_the_frozen_scorer_results(self):
        expected = json.loads((REPO_ROOT / "eval/expected_scores.json").read_text())
        for nf, t, sic, rules, sector, notes in self.prepared:
            got = labels_of(score_company(nf, t, sic, rules, None, sector=sector, sector_notes_=notes))
            for cid, label in got.items():
                self.assertEqual(label, expected[t]["criteria"][cid]["label"], (t, cid))

    def test_changes_are_counted_per_direction_and_a_threshold_touches_only_its_criterion(self):
        for row in self.res["thresholds"]:
            for tag in ("minus", "plus"):
                c = row[tag]
                self.assertLessEqual(c["to_fail"] + c["to_pass"], c["changed"])
        g1 = next(r for r in self.res["thresholds"] if r["name"] == "g1_min_revenue")
        self.assertEqual((g1["minus"]["changed"], g1["plus"]["changed"]), (0, 0))  # all five test companies are far above $1B
        # moving only a G2 threshold changes G2 labels and nothing else: compare every other criterion's labels
        nf, t, sic, rules, sector, notes = self.prepared[0]
        base = labels_of(score_company(nf, t, sic, rules, None, sector=sector, sector_notes_=notes))
        with override(g2_current_ratio=100.0):
            moved = labels_of(score_company(nf, t, sic, rules, None, sector=sector, sector_notes_=notes))
        self.assertEqual({c for c in base if base[c] != moved[c]} - {"G2"}, set())

    def test_price_tests_are_not_testable_and_report_no_change(self):
        for name in ("g6_max_pe", "g7_max_pe_x_pb"):
            row = next(r for r in self.res["thresholds"] if r["name"] == name)
            self.assertFalse(row["testable"])
            self.assertEqual((row["minus"]["changed"], row["plus"]["changed"]), (0, 0))

    def test_a_large_move_changes_labels_in_the_expected_direction(self):
        res = run(self.prepared, delta=0.99)  # revenue >= $10M or >= $1.99B: KO, JPM, GOOGL, TSLA, DUK all have revenue far above or near it
        b1 = next(r for r in res["thresholds"] if r["name"] == "b1_roe")
        self.assertGreater(b1["plus"]["to_fail"], 0)   # a much higher ROE bar turns passes into fails
        self.assertEqual(b1["plus"]["to_pass"], 0)
        self.assertGreater(b1["minus"]["to_pass"], 0)  # and a much lower one turns fails into passes
        self.assertEqual(b1["minus"]["to_fail"], 0)

    def test_deterministic_and_the_scorers_are_back_to_their_defaults_afterwards(self):
        self.assertEqual(run(self.prepared), self.res)
        self.assertEqual(T(), DEFAULT)


class TestFrozenFile(unittest.TestCase):
    def test_structure_and_headline(self):
        frozen = json.loads((REPO_ROOT / "eval/sensitivity_results.json").read_text())
        self.assertEqual(frozen["delta"], 0.2)
        self.assertEqual([r["name"] for r in frozen["thresholds"]], NAMES)
        self.assertEqual(frozen["companies"], json.loads((REPO_ROOT / "eval/universe_label_counts.json").read_text())["scored"])
        for cid, v in frozen["by_criterion"].items():  # decided counts agree with the frozen label counts
            counts = json.loads((REPO_ROOT / "eval/universe_label_counts.json").read_text())["criteria"][cid]
            self.assertEqual(v["decided"], sum(counts.get(k, 0) for k in ("pass", "partial_pass", "fail")), cid)

    def test_recomputed_from_the_local_cache_it_is_identical(self):
        try:
            res = sensitivity.compute()
        except Exception:
            self.skipTest("the SEC cache or the numeric score files are not available locally")
        self.assertEqual(json.loads(json.dumps(res)), json.loads((REPO_ROOT / "eval/sensitivity_results.json").read_text()))


if __name__ == "__main__":
    unittest.main()
