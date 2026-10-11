"""Prompt-perturbation stability (build 4a, ADR-072): the paraphrases, how a variant rubric reaches the agent and the Critic, classification and schema 1.2. Offline."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import stability
from engine.agents.qualitative import load_criteria
from engine.contracts import QUAL_CRITERIA
from engine.report import Result, Stability
from engine.settings import REPO_ROOT
from engine.stability import FIELDS, VARIANTS, attach, classify, load_paraphrases, stability_for, variant_criteria
from tests.test_qualitative import AgentCase, BIZ_A, criteria, reply, submit

F, W, I, NA = "evidence found", "evidence weak", "insufficient evidence", "not assessed"
KO = REPO_ROOT / "results" / "0000021344.json"

# words each paraphrase must keep: the examples and thresholds the main wording names (a cheap guard that meaning was not dropped)
ANCHORS = {
    "understandable_business": {"weak_means": ["leading provider of solutions"], "found_means": ["segment", "pricing or sales model"]},
    "durable_competitive_advantage": {"found_means": ["market share", "regulated exclusive franchise", "long-term contracts", "network", "AND", "trade secrets", "patents"],
                                      "weak_means": ["trade secrets", "patents", "scale", "competitors or customers can readily"],
                                      "question": ["brand", "switching costs", "network", "patents", "regulated franchise"]},
    "candid_management": {"weak_means": ["interest rates", "currency", "weather", "regulation", "economy", "product mix", "litigation outcomes", "results may fluctuate", "we face risks"],
                          "found_means": ["write-down", "restatement", "material weakness", "guidance", "missed", "acquisition, investment or project"]},
    "rational_capital_allocation": {"found_means": ["share repurchases", "dividends", "acquisitions", "capital expenditure", "debt repayment", "AND", "policy, priority or rationale",
                                                    "Not every action needs an amount"],
                                    "weak_means": ["amount", "policy, priority or rationale"], "question": ["prices paid were good"]},
}


class TestParaphrases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.para = load_paraphrases()
        cls.main = load_criteria()

    def test_two_variants_cover_every_criterion_and_field(self):
        self.assertEqual(VARIANTS, ("a", "b"))
        for v in VARIANTS:
            self.assertEqual(list(self.para[v]), list(QUAL_CRITERIA))
            for c in QUAL_CRITERIA:
                self.assertEqual(set(self.para[v][c]), set(FIELDS))

    def test_every_field_is_reworded_in_both_variants_and_the_variants_differ(self):
        for c in QUAL_CRITERIA:
            for f in FIELDS:
                texts = {self.main[c][f], self.para["a"][c][f], self.para["b"][c][f]}
                self.assertEqual(len(texts), 3, f"{c}.{f} is identical in two of main, a, b")

    def test_the_named_examples_and_thresholds_are_kept(self):
        for v in VARIANTS:
            for c, fields in ANCHORS.items():
                for f, words in fields.items():
                    for w in words:
                        self.assertIn(w.lower(), self.para[v][c][f].lower(), f"{v}/{c}.{f} lost '{w}'")
                        self.assertIn(w.lower(), self.main[c][f].lower(), f"anchor '{w}' is not in the main wording of {c}.{f}")

    def test_quoted_phrases_and_numbers_are_kept(self):
        for v in VARIANTS:
            for c in QUAL_CRITERIA:
                for f in FIELDS:
                    main = self.main[c][f]
                    for quoted in re.findall(r"(?<![A-Za-z])'([^']{6,}?)'(?![A-Za-z])", main):
                        self.assertIn(quoted, self.para[v][c][f], f"{v}/{c}.{f}")
                    self.assertEqual(re.findall(r"\d+", main), re.findall(r"\d+", self.para[v][c][f]))

    def test_only_question_and_verdict_definitions_are_replaced(self):
        for v in VARIANTS:
            spec = variant_criteria(v)
            for c in QUAL_CRITERIA:
                for key in self.main[c]:
                    if key in FIELDS:
                        self.assertEqual(spec[c][key], self.para[v][c][key])
                    else:
                        self.assertEqual(spec[c][key], self.main[c][key], f"{v}/{c}.{key} must not change")
        self.assertEqual(load_criteria(), self.main)  # the main rubric object is not mutated

    def test_a_missing_field_is_an_error(self):
        broken = json.loads(json.dumps(self.para))
        broken["a"]["candid_management"].pop("weak_means")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps(broken))
            with self.assertRaises(ValueError):
                load_paraphrases(p)


class TestVariantReachesAgentAndCritic(AgentCase):
    def test_the_agent_is_given_the_variant_wording(self):
        spec = variant_criteria("a", base=criteria(items={"understandable_business": ["1"]}, queries={"understandable_business": ["sparkling beverages juice retailers"]}))
        pid, i = self.loc(BIZ_A)
        self.run_agent(reply(submit((pid, i))), spec=spec)
        first = self.request(0)["messages"][1]["content"]
        main = load_criteria()["understandable_business"]
        a = load_paraphrases()["a"]["understandable_business"]
        self.assertIn(a["question"], first)
        self.assertIn(a["found_means"], first)
        self.assertNotIn(main["question"], first)
        self.assertNotIn(main["weak_means"], first)

    def test_the_critic_reads_the_same_variant_rubric(self):
        from engine.agents import review
        captured = {}

        class Stop(Exception):
            pass

        def fake_critic(retriever, llm, trace, **kw):
            captured.update(kw)
            raise Stop

        spec = variant_criteria("b")
        with mock.patch.object(review, "Critic", fake_critic):
            with self.assertRaises(Stop):
                review.explain_and_verify(mock.Mock(), mock.Mock(), retriever=None, llm=None, trace=mock.Mock(), criteria=spec, explanations=mock.Mock())
        self.assertEqual(captured["rubric"], spec)
        self.assertEqual(captured["rubric"]["candid_management"]["question"], load_paraphrases()["b"]["candid_management"]["question"])


class TestClassify(unittest.TestCase):
    def test_stable_when_all_equal(self):
        s = classify({"main": W, "a": W, "b": W})
        self.assertEqual((s.status, s.verdicts), ("stable", {"main": W, "a": W, "b": W}))

    def test_borderline_when_any_differs_and_all_three_verdicts_are_kept(self):
        for v in ({"main": W, "a": W, "b": I}, {"main": F, "a": W, "b": I}, {"main": I, "a": W, "b": W}, {"main": W, "a": F, "b": W}):
            s = classify(v)
            self.assertEqual((s.status, s.verdicts), ("borderline", v))

    def test_not_assessed_is_kept_but_is_not_a_judgement(self):
        s = classify({"main": W, "a": W, "b": NA})
        self.assertEqual((s.status, s.verdicts["b"]), ("stable", NA))
        self.assertEqual(classify({"main": W, "a": F, "b": NA}).status, "borderline")
        self.assertIsNone(classify({"main": W, "a": NA, "b": NA}))
        self.assertIsNone(classify({"main": NA, "a": NA, "b": NA}))

    def test_the_model_rejects_other_statuses(self):
        with self.assertRaises(Exception):
            Stability(status="mostly stable", verdicts={})


class Dirs(unittest.TestCase):
    """A temporary main results folder with the KO result, and a stability folder to put variant results in."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.main, self.stab = self.root / "results", self.root / "stability"
        self.main.mkdir()
        res = json.loads(KO.read_text())
        for q in res["qualitative"]:
            q["stability"] = None  # the committed result may already carry a stability record
        (self.main / "0000021344.json").write_text(json.dumps(res))

    def variant(self, name, verdicts):
        (self.stab / name).mkdir(parents=True, exist_ok=True)
        r = json.loads(KO.read_text())
        for q in r["qualitative"]:
            q["finding"]["verdict"] = verdicts.get(q["finding"]["criterion"], q["finding"]["verdict"])
        (self.stab / name / "0000021344.json").write_text(json.dumps(r))


class TestAttach(Dirs):

    def test_nothing_happens_until_both_variants_exist(self):
        self.variant("a", {})
        self.assertIsNone(stability_for("0000021344", self.main, self.stab))
        self.assertEqual(attach(["0000021344"], self.main, self.stab), {})
        self.assertTrue(all(q["stability"] is None for q in json.loads((self.main / "0000021344.json").read_text())["qualitative"]))

    def test_attach_marks_only_the_findings_that_changed_and_leaves_the_rest_alone(self):
        before = json.loads((self.main / "0000021344.json").read_text())
        main_verdict = {q["finding"]["criterion"]: q["finding"]["verdict"] for q in before["qualitative"]}
        other = I if main_verdict["candid_management"] != I else W
        self.variant("a", {"candid_management": other})
        self.variant("b", {})
        done = attach(["0000021344"], self.main, self.stab)
        self.assertEqual(set(done), {"0000021344"})
        after = json.loads((self.main / "0000021344.json").read_text())
        Result.model_validate(after)  # still a valid schema 1.2 result
        by = {q["finding"]["criterion"]: q["stability"] for q in after["qualitative"]}
        self.assertEqual(by["candid_management"]["status"], "borderline")
        self.assertEqual(by["candid_management"]["verdicts"], {"main": main_verdict["candid_management"], "a": other, "b": main_verdict["candid_management"]})
        for c in QUAL_CRITERIA:
            if c != "candid_management":
                self.assertEqual(by[c]["status"], "stable", c)
        for q in after["qualitative"]:  # the finding itself is untouched
            q["stability"] = None
        for q in before["qualitative"]:
            q["stability"] = None
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()


class TestPairFlips(Dirs):
    def test_main_against_one_variant_needs_only_those_two_runs(self):
        main_v = {q["finding"]["criterion"]: q["finding"]["verdict"] for q in json.loads(KO.read_text())["qualitative"]}
        self.variant("a", {"candid_management": I if main_v["candid_management"] != I else W, "durable_competitive_advantage": NA})
        r = stability.pair_flips([("KO", "0000021344"), ("XX", "0000000000")], "main", "a", self.main, self.stab)
        self.assertEqual(r["companies"], 1)  # the second company has no results at all
        self.assertEqual(r["per_criterion"]["candid_management"], {"n": 1, "differ": 1})
        self.assertEqual(r["per_criterion"]["durable_competitive_advantage"], {"n": 0, "differ": 0})  # a "not assessed" verdict is not compared
        self.assertEqual(r["per_criterion"]["understandable_business"], {"n": 1, "differ": 0})
        self.assertEqual((r["n"], r["differ"]), (3, 1))


class TestCommittedStability(unittest.TestCase):
    def test_every_stability_record_matches_the_runs_it_came_from(self):
        n = 0
        for f in sorted((REPO_ROOT / "results").glob("[0-9]*[0-9].json")):
            cik = f.stem
            res = json.loads(f.read_text())
            a, b = REPO_ROOT / "results/stability/a" / f.name, REPO_ROOT / "results/stability/b" / f.name
            for q in res["qualitative"]:
                st, c = q["stability"], q["finding"]["criterion"]
                if st is None:
                    continue
                n += 1
                self.assertTrue(a.exists() and b.exists(), cik)
                self.assertEqual(st["verdicts"], {"main": q["finding"]["verdict"], "a": stability.verdicts_of(a)[c], "b": stability.verdicts_of(b)[c]}, (cik, c))
                self.assertEqual(st["status"], classify(st["verdicts"]).status, (cik, c))
            if not (a.exists() and b.exists()):
                self.assertTrue(all(q["stability"] is None for q in res["qualitative"]), f"{cik} has no complete set of variant runs, so no stability record")
        self.assertGreaterEqual(n, 20)  # at least the five dev companies

    def test_variant_results_are_separate_files_with_their_own_run_ids(self):
        for v in VARIANTS:
            for f in sorted((REPO_ROOT / "results/stability" / v).glob("[0-9]*[0-9].json")):
                r = json.loads(f.read_text())
                self.assertTrue(r["run"]["run_id"].endswith(f"-live-{v}"), f.name)
                self.assertEqual(r["run"]["mode"], "live")
                self.assertTrue(r["trace_path"].startswith(f"results/stability/{v}/"))
                self.assertTrue(all(q["stability"] is None for q in r["qualitative"]))
                self.assertTrue((REPO_ROOT / "results" / f.name).exists())


class TestStatistics(unittest.TestCase):
    def rows(self):
        v = lambda m, a, b: {"main": m, "a": a, "b": b}  # noqa: E731
        spec = [("T1", "understandable_business", v(F, F, F)), ("T1", "candid_management", v(W, I, W)), ("T2", "candid_management", v(F, W, I)),
                ("T2", "durable_competitive_advantage", v(W, W, NA)), ("T3", "candid_management", v(NA, NA, W))]
        return [{"ticker": t, "criterion": c, "verdicts": vs, "status": (classify(vs).status if classify(vs) else None)} for t, c, vs in spec]

    def test_flip_rates(self):
        s = stability.flip_stats(self.rows())
        self.assertEqual((s["findings"], s["judged"], s["not_judged"]), (5, 4, 1))
        self.assertEqual(s["overall"], {"n": 4, "borderline": 2, "rate": 0.5})
        self.assertEqual(s["per_criterion"]["candid_management"], {"n": 2, "borderline": 2, "rate": 1.0})
        self.assertEqual(s["per_criterion"]["understandable_business"]["borderline"], 0)
        self.assertEqual(s["per_criterion"]["rational_capital_allocation"], {"n": 0, "borderline": 0, "rate": None})
        self.assertEqual(s["pairs"], {"main_vs_a": {"n": 4, "differ": 2}, "main_vs_b": {"n": 3, "differ": 1}, "a_vs_b": {"n": 3, "differ": 2}})
        self.assertEqual(s["spread"], {"one_level": 1, "two_levels": 1})  # W/I/W moves one level; F/W/I moves two
        self.assertEqual(s["not_assessed_verdicts"], 3)

    def test_dev_correlation_when_the_disagreements_are_the_borderline_findings(self):
        rows = [{"ticker": "T", "criterion": c, "verdicts": {"main": W, "a": W if i >= 2 else I, "b": W}, "status": "stable" if i >= 2 else "borderline"} for i, c in enumerate(QUAL_CRITERIA)]
        human = {"T": {QUAL_CRITERIA[0]: F, QUAL_CRITERIA[1]: F, QUAL_CRITERIA[2]: W, QUAL_CRITERIA[3]: W}}  # disagree on the two borderline ones only
        r = stability.dev_correlation(rows, human)
        self.assertEqual(r["cells"], {"borderline": {"disagree": 2, "agree": 0}, "stable": {"disagree": 0, "agree": 2}})
        self.assertEqual((r["disagree_rate_borderline"], r["disagree_rate_stable"], r["share_of_disagreements_that_are_borderline"], r["phi"]), (1.0, 0.0, 1.0, 1.0))
        self.assertAlmostEqual(r["fisher_p_one_sided"], 1 / 6)  # C(2,2)*C(2,0)/C(4,2)

    def test_fisher_exact_known_value(self):
        # the tea-tasting table [[3, 1], [1, 3]]: P(>=3) = (16 + 1) / 70
        self.assertAlmostEqual(stability.fisher_one_sided(3, 1, 1, 3), 17 / 70)
        self.assertEqual(stability.fisher_one_sided(0, 0, 0, 0), 1.0)

    def test_dev_correlation_leaves_out_unjudged_and_unlabelled_items(self):
        rows = [{"ticker": "T", "criterion": QUAL_CRITERIA[0], "verdicts": {"main": NA, "a": NA, "b": NA}, "status": None},
                {"ticker": "U", "criterion": QUAL_CRITERIA[0], "verdicts": {"main": W, "a": W, "b": W}, "status": "stable"}]
        r = stability.dev_correlation(rows, {"T": {QUAL_CRITERIA[0]: W}})
        self.assertEqual((r["unjudged"], r["cells"]["stable"]), (1, {"disagree": 0, "agree": 0}))
