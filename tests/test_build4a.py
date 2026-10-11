"""Build 4a: small fixes (section finder, citation cap message, latest-fiscal-year rule, self-contained results). Offline."""
from __future__ import annotations

import copy
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine.agents.critic import SYSTEM_PROMPT, SYSTEM_PROMPT_V21, llm_payload, load_rubric
from engine.agents.qualitative import check_citations, load_criteria
from engine.contracts import Passage
from engine.prompts import year_rule_text
from engine.fetch.edgar import EdgarClient
from engine.publish import MissingPassageError, build_site
from engine.report import Result
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT, Settings
from tests.test_qualitative import AgentCase, BIZ_A, NO_ITEM_7, criteria, reply, submit
from tests.test_site import SAMPLES, sample_rankings, sample_results


def v21(agent_versions=("qualitative", "critic")):
    """Pin the prompt version to v2.1 (the active one is v2 until the refresh run)."""
    return mock.patch("engine.prompts.active", lambda agent: "v2.1" if agent in agent_versions else "v2")


class TestCitationCapMessage(unittest.TestCase):
    SENTENCES = ["First " + "word " * 48 + "ends.", "Second " + "word " * 68 + "ends.", "Third " + "word " * 38 + "ends.", "Fourth is short."]
    DOC = " ".join(SENTENCES)

    def passage(self):
        spans, pos = [], 0
        for sent in self.SENTENCES:
            spans.append((pos, pos + len(sent)))
            pos += len(sent) + 1
        return Passage(passage_id="acc:1:1", accession="acc", item="1", n=1, char_start=0, char_end=len(self.DOC), words=len(self.DOC.split()), text=self.DOC, sentences=spans)

    def test_v21_lists_the_words_of_each_sentence(self):
        p = self.passage()
        ok, problems = check_citations([{"passage_id": p.passage_id, "first": 1, "last": 3}], {p.passage_id: p}, self.DOC, None, word_counts=True)
        self.assertEqual(ok, [])
        counts = [len(self.DOC[a:b].split()) for a, b in p.sentences[:3]]
        self.assertIn("Words per sentence: " + ", ".join(f"[{i}] {n} words" for i, n in enumerate(counts, start=1)), problems[0])
        self.assertIn("the limit is 120", problems[0])

    def test_v2_message_is_unchanged(self):
        p = self.passage()
        _, problems = check_citations([{"passage_id": p.passage_id, "first": 1, "last": 3}], {p.passage_id: p}, self.DOC, None)
        self.assertTrue(problems[0].endswith("the limit is 120. Cite fewer sentences"))

    def test_recorded_rejections_of_o_and_met(self):
        """The three recorded over-cap rejections, rebuilt from the local 10-Ks (skipped where they are not cached): each message names every sentence's words."""
        cases = [("0000726728", "0000726728-26-000011:1:2", 1, 4, 124), ("0001099219", "0001099219-26-000013:1A:43", 1, 7, 217),
                 ("0001099219", "0001099219-26-000013:1A:50", 1, 9, 187)]
        settings = Settings.from_env()

        def no_network(url, headers, timeout):
            raise RuntimeError("no network")
        for cik, pid, first, last, words in cases:
            retriever = Retriever(EdgarClient("live", settings, transport=no_network))
            try:
                idx = retriever.index(cik)
            except Exception:
                self.skipTest("the 10-K is not in the local cache")
            p = idx.by_id[pid]
            ok, problems = check_citations([{"passage_id": pid, "first": first, "last": last}], {pid: p}, idx.text, None, word_counts=True)
            self.assertEqual(ok, [], pid)
            self.assertIn(f"{words} words; the limit is 120", problems[0])
            for i in range(first, last + 1):
                a, b = p.sentences[i - 1]
                self.assertIn(f"[{i}] {len(idx.text[a:b].split())} words", problems[0])


class TestYearRule(AgentCase):
    SPEC = dict(items={"candid_management": ["1"]}, queries={"candid_management": ["sparkling beverages juice retailers"]})

    def first_message(self, *, version):
        spec = criteria(**self.SPEC)
        with mock.patch("engine.prompts.active", lambda agent: version):
            self.run_agent(reply(submit((self.loc(BIZ_A)[0], self.loc(BIZ_A)[1]), verdict="evidence weak")), spec=spec)
        return self.request(0)["messages"][1]["content"]

    def test_the_rule_is_in_both_rubric_entries_it_is_meant_for(self):
        rules = {k: v.get("year_rule") for k, v in load_criteria().items()}
        self.assertTrue(rules["candid_management"] and rules["rational_capital_allocation"])
        self.assertEqual(rules["candid_management"], rules["rational_capital_allocation"])
        self.assertIn("latest fiscal year", rules["rational_capital_allocation"])
        self.assertIn("prior-year comparative", rules["rational_capital_allocation"])
        self.assertIsNone(rules["understandable_business"])

    def test_the_agent_sees_the_rule_from_v21(self):
        rule = year_rule_text(load_criteria()["candid_management"], "2025-12-31")
        self.assertIn("the one that ended 2025-12-31", rule)
        self.assertIn(rule, self.first_message(version="v2.1"))
        self.assertNotIn("latest fiscal year", self.first_message(version="v2"))  # the recorded v2 requests are unchanged
        self.assertEqual(year_rule_text(load_criteria()["candid_management"], None).count("{"), 0)  # no date known: the clause is dropped, no placeholder left

    def test_the_critic_sees_the_same_line_from_v21(self):
        rubric = load_rubric()
        from engine.contracts import Citation, QualFinding
        f = QualFinding(criterion="rational_capital_allocation", verdict="evidence found", rationale="r", stop_reason="submitted",
                        citations=[Citation(passage_id="a:7:1", accession="a", item="7", char_start=0, char_end=3, quote="abc", sentences=[1, 1])])
        with v21():
            payload = llm_payload([f], rubric, "2025-12-31")[0]
        self.assertEqual(payload["year_rule"], year_rule_text(rubric["rational_capital_allocation"], "2025-12-31"))
        self.assertIn("ended 2025-12-31", payload["year_rule"])
        with mock.patch("engine.prompts.active", lambda agent: "v2"):
            self.assertNotIn("year_rule", llm_payload([f], rubric)[0])
        self.assertIn("year_rule", SYSTEM_PROMPT_V21)
        self.assertNotIn("year_rule", SYSTEM_PROMPT)

    def test_the_critic_payload_of_other_criteria_has_no_rule(self):
        rubric = load_rubric()
        from engine.contracts import Citation, QualFinding
        f = QualFinding(criterion="understandable_business", verdict="evidence found", rationale="r", stop_reason="submitted",
                        citations=[Citation(passage_id="a:1:1", accession="a", item="1", char_start=0, char_end=3, quote="abc", sentences=[1, 1])])
        with v21():
            self.assertNotIn("year_rule", llm_payload([f], rubric)[0])


class TestSelfContainedResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.results = sample_results(cls.tmp / "results")
        cls.rankings = sample_rankings(cls.tmp / "rk")
        empty = cls.tmp / "empty"
        empty.mkdir()
        # a clean checkout: no recorded 10-Ks, no local cache
        cls.clean = dataclasses.replace(Settings.from_env(), fixtures_dir=empty, cache_dir=empty)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_every_committed_result_carries_the_text_of_each_cited_passage(self):
        for f in sorted((REPO_ROOT / "results").glob("[0-9]*[0-9].json")):
            res = json.loads(f.read_text())
            self.assertEqual(res["schema_version"], "1.2", f.name)
            for q in res["qualitative"]:
                for c in q["finding"]["citations"]:
                    p = res["passages"][c["passage_id"]]
                    a = c["char_start"] - p["char_start"]
                    self.assertEqual(p["text"][a:a + len(c["quote"])], c["quote"], f"{f.name} {c['passage_id']}")

    def test_publish_from_a_clean_checkout_shows_the_passages(self):
        out = self.tmp / "site"
        build_site(out, results_dir=self.results, rankings_path=self.rankings, settings=self.clean, commit="test")
        for cik in SAMPLES:
            res = json.loads((out / f"data/results/{cik}.json").read_text())
            passages = json.loads((out / f"data/results/{cik}.passages.json").read_text())
            for q in res["qualitative"]:
                for c in q["finding"]["citations"]:
                    self.assertIn(c["quote"], passages[c["passage_id"]]["text"])

    def test_publish_fails_when_a_cited_passage_text_is_missing(self):
        results = self.tmp / "broken"
        results.mkdir()
        for c in SAMPLES:
            for suffix in (".json", ".trace.jsonl"):
                (results / f"{c}{suffix}").write_bytes((self.results / f"{c}{suffix}").read_bytes())
        path = results / "0000021344.json"
        res = json.loads(path.read_text())
        res["passages"].pop(next(iter(res["passages"])))
        path.write_text(json.dumps(res))
        with self.assertRaises(MissingPassageError):
            build_site(self.tmp / "site-broken", results_dir=results, rankings_path=self.rankings, settings=self.clean, commit="test")
        self.assertFalse((self.tmp / "site-broken").exists())

    def test_schema_1_2_is_additive(self):
        old = json.loads((REPO_ROOT / "results/0000021344.json").read_text())
        old.pop("passages")
        old["schema_version"] = "1.1"
        for q in old["qualitative"]:
            q.pop("stability")
        r = Result.model_validate(old)  # a 1.1 result still validates
        self.assertEqual(r.passages, {})
        self.assertTrue(all(q.stability is None for q in r.qualitative))


if __name__ == "__main__":
    unittest.main()
