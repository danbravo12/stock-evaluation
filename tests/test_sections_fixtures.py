"""Section extraction and retrieval on the 5 real recorded 10-Ks (replay, offline)."""
from __future__ import annotations

import tempfile
import time
import unittest

from engine.fetch.edgar import EdgarClient
from engine.retrieve import Retriever
from engine.sections import MIN_SECTION_CHARS
from engine.settings import Settings

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]


class TestFixtureSections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = EdgarClient("replay", Settings.from_env())
        cls.tmp = tempfile.TemporaryDirectory()  # cold cache: also times the full conversion
        cls.retriever = Retriever(cls.client, cls.tmp.name)
        cls.idx, cls.seconds = {}, {}
        for t in TICKERS:
            start = time.time()
            cls.idx[t] = cls.retriever.index(cls.client.lookup_cik(t)[0])
            cls.seconds[t] = time.time() - start

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_item_is_found_or_explained(self):
        for t, idx in self.idx.items():
            self.assertEqual(sorted(idx.sections), ["1", "1A", "7"])
            for s in idx.sections.values():
                if s.status == "found":
                    self.assertGreaterEqual(s.length, MIN_SECTION_CHARS, f"{t} {s.item}")
                    self.assertTrue(s.method and s.sha256 and s.accession)
                else:
                    self.assertTrue(s.reason, f"{t} {s.item}")

    def test_sections_do_not_open_on_the_table_of_contents(self):
        for t, idx in self.idx.items():
            for s in idx.sections.values():
                if s.status == "found":
                    opening = idx.text[s.char_start:s.char_start + 400]
                    self.assertNotRegex(opening, r"\| \d+\s*$", f"{t} {s.item}")  # a TOC row ends with a page number

    def test_bank_mdna_uses_the_title_fallback(self):
        self.assertEqual(self.idx["JPM"].sections["7"].method, "title_fallback")
        self.assertEqual(self.idx["KO"].sections["7"].method, "item_heading")

    def test_every_passage_round_trips_its_offsets(self):
        for t, idx in self.idx.items():
            self.assertGreater(len(idx.passages), 50, t)
            for p in idx.passages:
                self.assertEqual(idx.text[p.char_start:p.char_end], p.text, p.passage_id)

    def test_duke_16mb_filing_is_extracted_and_indexed_quickly(self):
        print(f"\nDUK cold extraction + indexing: {self.seconds['DUK']:.1f}s ({len(self.idx['DUK'].passages)} passages)")
        self.assertLess(self.seconds["DUK"], 10)

    def test_search_returns_citable_passages(self):
        cik = self.client.lookup_cik("KO")[0]
        hits = self.retriever.search(cik, "share repurchases dividends", items=["7"], k=3)
        self.assertEqual(len(hits), 3)
        self.assertTrue(all(h.item == "7" and h.score > 0 for h in hits))
        self.assertEqual(self.retriever.get_passage(hits[0].passage_id).text, hits[0].text)


if __name__ == "__main__":
    unittest.main()
