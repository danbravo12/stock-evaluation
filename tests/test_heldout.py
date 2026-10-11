"""Held-out set, blind labelling packet and agreement maths (build 4a, ADR-071). Offline."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval import agreement, packet
from eval.agreement import compare, weighted_kappa
from engine.contracts import QUAL_CRITERIA
from engine.fetch.edgar import EdgarClient
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT, Settings
from engine.universe import load_universe

HELDOUT = json.loads((REPO_ROOT / "eval/heldout.json").read_text())
DEV = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]
F, W, I = "evidence found", "evidence weak", "insufficient evidence"


def verdicts(*rows):
    """verdicts("T", F, W, I, F) -> {"T": {criterion: verdict}} in criterion order."""
    t, *vs = rows
    return {t: dict(zip(QUAL_CRITERIA, vs))}


class TestHeldoutList(unittest.TestCase):
    def test_the_frozen_list(self):
        self.assertEqual(HELDOUT["companies"], ["AAPL", "MSFT", "PG", "NEE", "CAT", "JNJ"])
        self.assertEqual(len(HELDOUT["companies"]) * len(HELDOUT["criteria"]), HELDOUT["items"], 24)
        self.assertEqual(HELDOUT["criteria"], list(QUAL_CRITERIA))
        self.assertFalse(set(HELDOUT["companies"]) & set(DEV), "the held-out companies must not be dev companies")
        self.assertIn("Daniel may have seen", HELDOUT["disclosure"])
        self.assertEqual(HELDOUT["frozen"], "2026-10-12")

    def test_no_agent_output_in_the_frozen_files(self):
        for name in ("eval/heldout.json", "eval/heldout_labels.json"):
            text = (REPO_ROOT / name).read_text()
            self.assertNotIn("agent_verdict", text, name)
            self.assertNotIn("rationale", text, name)

    def test_label_template_covers_every_item(self):
        labels = json.loads((REPO_ROOT / "eval/heldout_labels.json").read_text())["labels"]
        self.assertEqual(list(labels), HELDOUT["companies"])
        for t, crits in labels.items():
            self.assertEqual(list(crits), list(QUAL_CRITERIA), t)

    def test_the_packet_is_git_ignored(self):
        self.assertIn("docs/labelling/", (REPO_ROOT / ".gitignore").read_text().split("\n"))


class TestAgreementMaths(unittest.TestCase):
    def test_kappa_perfect_and_hand_computed(self):
        self.assertAlmostEqual(weighted_kappa([(0, 0), (1, 1), (2, 2), (2, 2)]), 1.0)
        # worked by hand: observed 0.125, expected 0.4375 -> 1 - 0.125/0.4375 = 5/7
        self.assertAlmostEqual(weighted_kappa([(0, 0), (1, 1), (2, 2), (2, 1)]), 5 / 7)

    def test_kappa_penalises_far_misses_more_than_near_ones(self):
        near = weighted_kappa([(0, 0), (1, 1), (2, 2), (1, 2)])
        far = weighted_kappa([(0, 0), (1, 1), (2, 2), (0, 2)])
        self.assertGreater(near, far)

    def test_kappa_chance_level_and_undefined(self):
        self.assertAlmostEqual(weighted_kappa([(0, 1), (1, 0), (2, 2), (2, 2), (0, 2), (2, 0)]), weighted_kappa([(0, 1), (1, 0), (2, 2), (2, 2), (0, 2), (2, 0)]))
        self.assertIsNone(weighted_kappa([(1, 1), (1, 1)]))  # both raters use one level only: chance agreement is perfect
        self.assertIsNone(weighted_kappa([]))

    def test_exact_within_one_and_direction(self):
        human = {"A": dict(zip(QUAL_CRITERIA, [F, F, W, I])), "B": dict(zip(QUAL_CRITERIA, [W, W, I, I]))}
        agent = {"A": dict(zip(QUAL_CRITERIA, [F, W, F, I])),   # same, stricter by 1, generous by 1, same
                 "B": dict(zip(QUAL_CRITERIA, [F, I, I, "not assessed"]))}  # generous by 1, stricter by 1, same, not assessed
        r = compare(agent, human)
        self.assertEqual((r["labelled"], r["exact"], r["within_one"]), (8, 3, 7))  # not assessed is neither exact nor within one
        self.assertEqual(r["direction"], {"agent_more_generous": 2, "agent_stricter": 2, "not_assessed": 1})
        self.assertEqual(r["kappa"]["n"], 7)
        self.assertEqual(r["kappa"]["excluded_not_assessed"], 1)
        self.assertEqual(len(r["disagreements"]), 5)

    def test_two_levels_apart_is_not_within_one(self):
        r = compare(verdicts("A", F, I, W, W), verdicts("A", I, F, W, W))
        self.assertEqual((r["exact"], r["within_one"]), (2, 2))
        self.assertEqual(r["direction"]["agent_more_generous"], 1)

    def test_per_criterion_breakdown(self):
        human = {"A": dict(zip(QUAL_CRITERIA, [F, F, F, F])), "B": dict(zip(QUAL_CRITERIA, [F, F, F, F]))}
        agent = {"A": dict(zip(QUAL_CRITERIA, [F, W, F, F])), "B": dict(zip(QUAL_CRITERIA, [F, W, W, F]))}
        r = compare(agent, human)["per_criterion"]
        self.assertEqual([(r[c]["exact"], r[c]["within_one"], r[c]["n"]) for c in QUAL_CRITERIA], [(2, 2, 2), (0, 2, 2), (1, 2, 2), (2, 2, 2)])

    def test_unlabelled_items_are_left_out_and_counted(self):
        human = {"A": {c: None for c in QUAL_CRITERIA}}
        human["A"][QUAL_CRITERIA[0]] = F
        r = compare(verdicts("A", F, F, F, F), human)
        self.assertEqual((r["items"], r["labelled"], r["unlabelled"], r["exact"]), (4, 1, 3, 1))

    def test_a_missing_agent_result_counts_as_not_assessed(self):
        r = compare({}, {"A": dict(zip(QUAL_CRITERIA, [F, F, F, F]))})
        self.assertEqual((r["exact"], r["direction"]["not_assessed"]), (0, 4))

    def test_dev_set_figures_match_the_committed_results(self):
        rep = agreement.report()
        dev = rep["dev"]
        self.assertEqual((dev["labelled"], dev["items"]), (20, 20))
        self.assertGreaterEqual(dev["within_one"], dev["exact"])
        self.assertEqual(rep["heldout"]["labelled"], 0 if all(v["human_verdict"] is None for c in json.loads((REPO_ROOT / "eval/heldout_labels.json").read_text())["labels"].values() for v in c.values()) else rep["heldout"]["labelled"])


class TestPacket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = Settings.from_env()
        cls.retriever = Retriever(EdgarClient("replay", cls.settings))
        cls.ko = packet.build_packet([("KO", "0000021344")], cls.retriever)

    def test_structure(self):
        self.assertEqual(self.ko.count("**Verdict:**"), 4)
        self.assertEqual(self.ko.count("**Note:**"), 4)
        for c in QUAL_CRITERIA:
            self.assertIn(f"### KO · {c}", self.ko)
        rubric = json.loads((REPO_ROOT / "config/search_terms.json").read_text())["criteria"]
        for c in QUAL_CRITERIA:
            for k in ("question", "found_means", "weak_means", "insufficient_means"):
                self.assertIn(rubric[c][k], self.ko)
        self.assertIn(rubric["candid_management"]["year_rule"], self.ko)
        self.assertIn("https://www.sec.gov/Archives/edgar/data/21344/", self.ko)

    def test_eight_passages_per_criterion_with_item_and_id(self):
        import re
        sections = re.split(r"^### KO · ", self.ko, flags=re.M)[1:]
        self.assertEqual(len(sections), 4)
        for s in sections:
            ids = re.findall(r"^\*\*\[(\d{10}-\d\d-\d+:(?:1|1A|7):\d+)\]\*\* Item (1|1A|7) ", s, flags=re.M)
            self.assertEqual(len(ids), 8, s[:80])
            self.assertTrue(all(i.split(":")[1] == item for i, item in ids))

    def test_deterministic(self):
        again = packet.build_packet([("KO", "0000021344")], Retriever(EdgarClient("replay", self.settings)))
        self.assertEqual(again, self.ko)

    def test_retrieval_is_the_same_whatever_a_model_said(self):
        # the passages are a function of the filing and two config files only
        cfg = packet.load_config()
        rubric = json.loads((REPO_ROOT / "config/search_terms.json").read_text())["criteria"]
        got = packet.fixed_retrieval(self.retriever, "0000021344", rubric["durable_competitive_advantage"], cfg)
        direct = self.retriever.search_many("0000021344", rubric["durable_competitive_advantage"]["queries"] + cfg["generic_queries"], ["1", "1A"], k=8)
        self.assertEqual({p.passage_id for p in got}, {h.passage_id for h in direct})

    def test_no_agent_output_in_the_packet(self):
        """None of the recorded agent rationales or verdicts for these companies appear, and the code that writes the packet cannot read a result."""
        res = json.loads((REPO_ROOT / "results/0000021344.json").read_text())
        for q in res["qualitative"]:
            self.assertNotIn(q["finding"]["rationale"], self.ko)
            self.assertNotIn(q["finding"]["rationale"][:60], self.ko)
        # the only verdict words are the rubric's definitions and the label options
        for line in self.ko.split("\n"):
            if line.startswith("**Verdict:**"):
                self.assertEqual(line, "**Verdict:** …  _(found / weak / insufficient)_")
        for src in ("eval/packet.py", "scripts/label_packet.py"):
            text = (REPO_ROOT / src).read_text()
            for forbidden in ("results_dir", "results/", ".trace", "QualFinding", "critic", "Critic(", "complete_json", "LLMClient"):
                self.assertNotIn(forbidden, text, f"{src} mentions {forbidden}")

    def test_heldout_packet_has_no_agent_rationales(self):
        universe = load_universe()
        companies = [(t, universe.row_for(t).cik) for t in HELDOUT["companies"]]

        def no_network(url, headers, timeout):
            raise RuntimeError("no network")
        retriever = Retriever(EdgarClient("live", self.settings, transport=no_network))
        try:
            for _, cik in companies:
                retriever.index(cik)
        except Exception:
            self.skipTest("the held-out 10-Ks are not in the local cache")
        text = packet.build_packet(companies, retriever, heldout=HELDOUT)
        self.assertEqual(text.count("**Verdict:**"), 24)
        for _, cik in companies:
            res = json.loads((REPO_ROOT / f"results/{cik}.json").read_text())
            for q in res["qualitative"]:
                f = q["finding"]
                self.assertNotIn(f["rationale"], text)
                self.assertNotIn(f["rationale"][:60], text)
        import re
        # the text outside the quoted filing passages never mentions the tool's agents
        own = "\n".join(l for l in text.split("\n") if not l.startswith(">"))
        for word in ("Critic", "Gemini", "language model", "trace"):
            self.assertIsNone(re.search(rf"\b{word}\b", own), word)


class TestIngest(unittest.TestCase):
    def test_round_trip(self):
        filled = ("### AAPL · understandable_business\n\n**Verdict:** found  _(found / weak / insufficient)_\n\n**Note:** clear\n\n"
                  "### AAPL · durable_competitive_advantage\n\n**Verdict:** weak\n\n**Note:** \n\n"
                  "### AAPL · candid_management\n\n**Verdict:** …  _(found / weak / insufficient)_\n\n**Note:** \n\n"
                  "### AAPL · rational_capital_allocation\n\n**Verdict:** maybe\n\n**Note:** x\n")
        labels, problems = packet.parse_filled_packet(filled)
        self.assertEqual(labels["AAPL"]["understandable_business"], {"human_verdict": F, "note": "clear"})
        self.assertEqual(labels["AAPL"]["durable_competitive_advantage"]["human_verdict"], W)
        self.assertIsNone(labels["AAPL"]["candid_management"]["human_verdict"])
        self.assertEqual(len(problems), 2)
        self.assertIn("no verdict yet", problems[0])
        self.assertIn("'maybe' is not found, weak or insufficient", problems[1])


if __name__ == "__main__":
    unittest.main()
