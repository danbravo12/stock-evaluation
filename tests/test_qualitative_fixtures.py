"""Qualitative agent on the 5 real recorded 10-Ks and recorded model responses (replay, zero network).

Structural invariants only. Verdicts are deliberately not frozen yet: they are reviewed by hand first (docs/qualitative_report.md).
"""
from __future__ import annotations

import json
import re
import unittest

from engine.agents.qualitative import MAX_SPAN_WORDS, assess_qualitative
from engine.contracts import QUAL_CRITERIA
from engine.fetch.edgar import EdgarClient
from engine.llm.client import LLMClient
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT, Settings
from engine.trace import TraceRecorder

TICKERS = json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"]
# Phrases that would turn a description of a filing into advice (ADR-003); deliberately small
BANNED = [r"\bshould (buy|sell|hold|invest)", r"\binvestors? should\b", r"\b(buy|sell|hold|strong buy) (rating|recommendation)\b", r"\bprice target\b",
          r"\b(under|over)valued\b", r"\bworth (buying|owning)\b", r"\bwe recommend\b", r"\bout ?perform", r"\bgood (investment|buy)\b"]


class TestQualitativeFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = Settings.from_env()
        cls.trace = TraceRecorder("fixtures")
        cls.llm = LLMClient("replay", settings, trace=cls.trace)
        cls.retriever = Retriever(EdgarClient("replay", settings))
        cls.results, cls.docs = {}, {}
        for t in TICKERS:
            cik = cls.retriever.client.lookup_cik(t)[0]
            cls.results[t] = assess_qualitative(cik, t, cls.retriever, cls.llm, cls.trace)
            cls.docs[t] = cls.retriever.index(cik).text

    def test_four_findings_per_company_in_config_order(self):
        for t, fs in self.results.items():
            self.assertEqual([f.criterion for f in fs.findings], list(QUAL_CRITERIA), t)

    def test_every_cited_span_is_exactly_the_document_text(self):
        for t, fs in self.results.items():
            idx = self.retriever.index(fs.cik)
            for f in fs.findings:
                if f.stop_reason != "submitted":
                    self.assertEqual((f.verdict, f.citations), ("not assessed", []), (t, f.criterion))
                    continue
                self.assertIn(f.verdict, ("evidence found", "evidence weak", "insufficient evidence"))
                if f.verdict != "insufficient evidence":
                    self.assertTrue(1 <= len(f.citations) <= 2, (t, f.criterion))
                for c in f.citations:
                    p = idx.by_id[c.passage_id]
                    first, last = c.sentences
                    self.assertTrue(1 <= first <= last <= len(p.sentences) and last - first <= 2)
                    self.assertEqual((c.char_start, c.char_end), (p.sentences[first - 1][0], p.sentences[last - 1][1]))
                    self.assertEqual(self.docs[t][c.char_start:c.char_end], c.quote, (t, f.criterion))
                    self.assertLessEqual(len(c.quote.split()), MAX_SPAN_WORDS)
                    self.assertEqual(c.accession, fs.accession)
                    self.assertTrue(c.passage_id.startswith(fs.accession + ":" + c.item + ":"))

    def test_no_mechanical_citation_failures(self):
        for t, fs in self.results.items():
            for f in fs.findings:
                self.assertNotEqual(f.stop_reason, "invalid_citation", (t, f.criterion))

    def test_no_advice_language_in_rationales(self):
        for t, fs in self.results.items():
            for f in fs.findings:
                for pattern in BANNED:
                    self.assertIsNone(re.search(pattern, f.rationale, re.I), (t, f.criterion, pattern, f.rationale))

    def test_cost_and_token_totals_add_up_and_the_free_tier_costs_nothing(self):
        for t, fs in self.results.items():
            self.assertEqual(fs.totals.llm_calls, sum(f.llm_calls for f in fs.findings), t)
            self.assertEqual(fs.totals.usage.total_tokens, sum(f.usage.total_tokens for f in fs.findings), t)
            self.assertEqual(fs.totals.actual_cost_usd, 0.0, t)
            self.assertGreater(fs.totals.notional_cost_usd, 0.0, t)
            for f in fs.findings:
                self.assertGreaterEqual(f.llm_calls, 1)
                self.assertTrue(f.searches[0].seeded and f.searches[0].passage_ids is not None)

    def test_replay_made_no_network_calls(self):
        self.assertTrue(self.llm.calls)
        self.assertTrue(all(c.replayed and c.actual_cost_usd == 0.0 for c in self.llm.calls))


if __name__ == "__main__":
    unittest.main()
