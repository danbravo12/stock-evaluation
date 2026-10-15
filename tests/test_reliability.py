"""Criterion reliability (ADR-072 amendment, schema 1.3): threshold and computation on synthetic data, the note only at or above the threshold, additive schema. Offline."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine import stability
from engine.contracts import QUAL_CRITERIA
from engine.report import SCHEMA_VERSION, Result, Stability
from engine.settings import REPO_ROOT
from engine.stability import attach, criterion_stats, load_threshold
from tests.test_stability import Dirs, F, I, W, KO
from tests.test_stability_copy import NODE, run_node_note

C0, C1, C2, C3 = QUAL_CRITERIA


def st(status):
    return None if status is None else Stability(status=status, verdicts={"main": F, "a": F, "b": F if status == "stable" else W})


class TestThreshold(unittest.TestCase):
    def test_the_threshold_lives_in_config(self):
        self.assertEqual(load_threshold(), 0.30)
        self.assertEqual(json.loads((REPO_ROOT / "config/reliability.json").read_text())["low_flip_rate_threshold"], 0.30)
        self.assertEqual(SCHEMA_VERSION, "1.4")

    def test_computation_counts_only_findings_with_a_status(self):
        companies = [{C0: st("stable"), C1: st("borderline"), C2: st("borderline"), C3: None},
                     {C0: st("stable"), C1: st("stable"), C2: st("borderline"), C3: None},
                     {C0: st("stable"), C1: st("stable"), C2: st("stable"), C3: st("stable")}]
        r = criterion_stats(companies, 0.30)
        self.assertEqual((r[C0]["compared"], r[C0]["changed"], r[C0]["low"]), (3, 0, False))
        self.assertEqual((r[C1]["compared"], r[C1]["changed"]), (3, 1))
        self.assertAlmostEqual(r[C1]["rate"], 1 / 3)
        self.assertTrue(r[C1]["low"])
        self.assertEqual((r[C2]["changed"], r[C2]["compared"], r[C2]["low"]), (2, 3, True))
        self.assertEqual((r[C3]["compared"], r[C3]["changed"], r[C3]["low"]), (1, 0, False))  # a finding without a status is not compared

    def test_at_the_threshold_counts_below_does_not(self):
        three_of_ten = [{C0: st("borderline" if i < 3 else "stable")} for i in range(10)]
        self.assertTrue(criterion_stats(three_of_ten, 0.30)[C0]["low"])
        two_of_ten = [{C0: st("borderline" if i < 2 else "stable")} for i in range(10)]
        self.assertFalse(criterion_stats(two_of_ten, 0.30)[C0]["low"])
        self.assertTrue(criterion_stats(two_of_ten, 0.20)[C0]["low"])  # the threshold is a parameter, not a constant

    def test_nothing_compared_is_not_low(self):
        r = criterion_stats([{C0: None}], 0.30)
        self.assertEqual((r[C0]["rate"], r[C0]["low"]), (None, False))

    def test_dicts_from_published_results_work_too(self):
        r = criterion_stats([{C0: {"status": "borderline", "verdicts": {}}}, {C0: {"status": "stable", "verdicts": {}}}], 0.30)
        self.assertEqual((r[C0]["changed"], r[C0]["compared"], r[C0]["low"]), (1, 2, True))


class TestAttachWritesReliability(Dirs):
    def second_company(self):
        res = json.loads((self.main / "0000021344.json").read_text())
        res["plan"]["cik"] = "0000099999"
        (self.main / "0000099999.json").write_text(json.dumps(res))  # a company with no variant runs

    def test_low_criteria_are_marked_on_every_result_and_others_are_not(self):
        main_v = {q["finding"]["criterion"]: q["finding"]["verdict"] for q in json.loads((self.main / "0000021344.json").read_text())["qualitative"]}
        other = I if main_v[C2] != I else W
        self.variant("a", {C2: other})
        self.variant("b", {})
        self.second_company()
        attach(["0000021344", "0000099999"], self.main, self.stab, 0.30, human={C2: (0, 6)})
        for cik in ("0000021344", "0000099999"):
            res = json.loads((self.main / f"{cik}.json").read_text())
            Result.model_validate(res)
            self.assertEqual(res["schema_version"], "1.4")
            for q in res["qualitative"]:
                if q["finding"]["criterion"] == C2:
                    self.assertEqual((q["reliability"], q["reliability_basis"]), ("low", {"changed": 1, "compared": 1, "human_agreed": 0, "human_of": 6}))
                else:
                    self.assertIsNone(q["reliability"])
                    self.assertIsNone(q["reliability_basis"])
        self.assertIsNone(json.loads((self.main / "0000099999.json").read_text())["qualitative"][0]["stability"])  # no variants, so no stability record

    def test_a_threshold_above_every_rate_marks_nothing_and_clears_old_marks(self):
        self.variant("a", {C2: I if I != json.loads(KO.read_text())["qualitative"][2]["finding"]["verdict"] else W})
        self.variant("b", {})
        attach(["0000021344"], self.main, self.stab, 0.30)
        attach(["0000021344"], self.main, self.stab, 1.01)
        self.assertTrue(all(q["reliability"] is None for q in json.loads((self.main / "0000021344.json").read_text())["qualitative"]))

    def test_schema_1_2_results_still_validate(self):
        old = json.loads(KO.read_text())
        old["schema_version"] = "1.2"
        for q in old["qualitative"]:
            q.pop("reliability", None)
            q.pop("reliability_basis", None)
        r = Result.model_validate(old)
        self.assertTrue(all(q.reliability is None for q in r.qualitative))


class TestCommitted(unittest.TestCase):
    def test_marks_in_the_committed_results_follow_the_stability_records(self):
        rows = []
        results = [json.loads(f.read_text()) for f in sorted((REPO_ROOT / "results").glob("[0-9]*[0-9].json"))]
        for r in results:
            if any(q["stability"] for q in r["qualitative"]):
                rows.append({q["finding"]["criterion"]: q["stability"] for q in r["qualitative"]})
        stats = criterion_stats(rows)
        for r in results:
            for q in r["qualitative"]:
                if r["schema_version"] in ("1.3", "1.4"):
                    low = stats[q["finding"]["criterion"]]["low"]
                    self.assertEqual(q["reliability"], "low" if low else None, r["plan"]["ticker"])
                    if low:
                        b = stats[q["finding"]["criterion"]]
                        self.assertEqual({k: q["reliability_basis"][k] for k in ("changed", "compared")}, {"changed": b["changed"], "compared": b["compared"]})
                        self.assertIsNotNone(q["reliability_basis"]["human_of"])


@unittest.skipUnless(NODE, "node is not installed")
class TestNoteRenders(unittest.TestCase):
    def test_only_low_items_get_the_note(self):
        out = run_node_note([{"reliability": "low", "reliability_basis": {"changed": 13, "compared": 25}}, {"reliability": "low", "reliability_basis": {"changed": 13, "compared": 25, "human_agreed": 2, "human_of": 6}}, {"reliability": None, "reliability_basis": None}, {}, {"reliability": "low"}])
        self.assertEqual(out[0], "Low reliability: this verdict changed with the question's wording for 13 of 25 companies.")
        self.assertEqual(out[1], "Low reliability: this verdict changed with the question's wording for 13 of 25 companies, and agreed with a human reviewer on 2 of 6 held-out companies.")
        self.assertEqual(out[2:], [None, None, None])  # not low, empty, or low without its basis


class TestPublishedFigures(unittest.TestCase):
    def test_how_it_works_reads_the_computed_figures_and_the_page_has_no_typed_rates(self):
        html = (REPO_ROOT / "site_src/how-it-works.html").read_text()
        self.assertIn("data/stability.json", html)
        publish = (REPO_ROOT / "engine/publish.py").read_text()
        self.assertIn("criterion_stats(stability_rows, threshold)", publish)


if __name__ == "__main__":
    unittest.main()
