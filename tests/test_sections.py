"""Text normalisation, section extraction, passages and BM25 on small synthetic filings (offline)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from engine.filing_text import html_to_text
from engine.retrieve import Bm25, Retriever, tokenise
from engine.sections import HARD_CAP_WORDS, MIN_SECTION_CHARS, extract_sections, make_passages


def filler(tag: str, words: int = 400) -> str:
    """A paragraph of `words` words that contains `tag`, so we can tell which section text came from."""
    return f"<p>{tag} " + " ".join(f"word{i}" for i in range(words)) + ".</p>"


TOC = ("<table><tr><td>Item 1.</td><td>Business</td><td>3</td></tr><tr><td>Item 1A.</td><td>Risk Factors</td><td>9</td></tr>"
       "<tr><td>Item 1B.</td><td>Unresolved Staff Comments</td><td>20</td></tr><tr><td>Item 7.</td><td>Management's Discussion</td><td>30</td></tr>"
       "<tr><td>Item 7A.</td><td>Market Risk</td><td>40</td></tr></table>")


def filing(body: str) -> str:
    return f"<html><body>{TOC}{body}</body></html>"


FULL = filing(
    "<div>ITEM 1. BUSINESS</div>" + filler("REALBUSINESS") + "<div>ITEM 1A. RISK FACTORS</div>" + filler("REALRISK")
    + "<div>ITEM 1B. UNRESOLVED STAFF COMMENTS</div><p>None.</p><div>ITEM 2. PROPERTIES</div><p>x</p>"
    + "<div>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</div>" + filler("REALMDA") + "<div>ITEM 7A. MARKET RISK</div><p>y</p>"
)


class TestHtmlToText(unittest.TestCase):
    def test_hidden_content_is_dropped(self):
        html = ('<html><head><style>.a{}</style></head><body><ix:header><ix:hidden>SECRET1</ix:hidden></ix:header>'
                '<script>var SECRET2</script><div style="display: none">SECRET3</div><p>visible</p></body></html>')
        self.assertEqual(html_to_text(html), "visible")

    def test_table_rows_become_lines_with_pipes(self):
        html = "<table><tr><td>Revenue</td><td></td><td>$</td><td>47,941</td></tr><tr><td>Net income</td><td>13,107</td></tr></table>"
        self.assertEqual(html_to_text(html), "Revenue | $ | 47,941\nNet income | 13,107")

    def test_quotes_nbsp_and_whitespace_are_normalised(self):
        html = "<p>The company’s  “brand”\n  is   strong</p><p>Second</p>"
        self.assertEqual(html_to_text(html), 'The company\'s "brand" is strong\nSecond')

    def test_blocks_make_lines_and_inline_tags_do_not(self):
        self.assertEqual(html_to_text("<div>one</div><div>two <b>bold</b>text</div>a<br>b"), "one\ntwo boldtext\na\nb")

    def test_deterministic(self):
        self.assertEqual(html_to_text(FULL), html_to_text(FULL))


class TestSections(unittest.TestCase):
    def setUp(self):
        self.text = html_to_text(FULL)
        self.sections = extract_sections(self.text, "acc-1", "sha")

    def test_toc_entries_are_not_chosen(self):
        for item, tag in (("1", "REALBUSINESS"), ("1A", "REALRISK"), ("7", "REALMDA")):
            s = self.sections[item]
            self.assertEqual((s.status, s.method), ("found", "item_heading"))
            body = self.text[s.char_start:s.char_end]
            self.assertIn(tag, body)
            self.assertGreaterEqual(s.length, MIN_SECTION_CHARS)
            self.assertNotIn("Unresolved Staff", body)  # stops at the next item heading
        self.assertTrue(self.text[self.sections["1"].char_start:].startswith("ITEM 1. BUSINESS"))

    def test_combined_items_1_and_2_heading(self):
        text = html_to_text(filing("<div>Items 1 and 2. Business and Properties</div>" + filler("COMBINED")
                                   + "<div>Item 1A. Risk Factors</div>" + filler("RISK") + "<div>Item 1B. Unresolved</div>"))
        s = extract_sections(text)["1"]
        self.assertEqual(s.status, "found")
        self.assertIn("COMBINED", text[s.char_start:s.char_end])
        self.assertNotIn("RISK", text[s.char_start:s.char_end])

    def test_missing_section_is_not_found_with_a_reason(self):
        text = html_to_text(filing("<div>Item 1. Business</div>" + filler("B") + "<div>Item 1A. Risk Factors</div>" + filler("R")
                                   + "<div>Item 1B. Unresolved</div>"))
        s = extract_sections(text)["7"]
        self.assertEqual(s.status, "not_found")
        self.assertIn("Item 7", s.reason)
        self.assertIsNone(s.char_start)

    def test_short_stub_falls_back_to_the_section_title(self):
        # Bank pattern: Item 7 is a one-line cross-reference; the real MD&A sits later under its own title.
        body = ("<div>Item 7. Management's Discussion and Analysis</div><p>appears on pages 46-160.</p><div>Item 7A. Market Risk</div><p>See MD&amp;A.</p>"
                "<div>Item 8. Financial Statements</div><p>see below</p>"
                "<div>Management’s discussion and analysis</div>" + filler("REALMDA", 500)
                + "<div>Management's discussion and analysis</div>" + filler("MORE", 300)
                + "<div>Report of Independent Registered Public Accounting Firm</div><p>audit</p>")
        s = extract_sections(html_to_text(filing(body)))["7"]
        self.assertEqual((s.status, s.method), ("found", "title_fallback"))

    def test_title_fallback_stops_at_the_end_marker(self):
        text = html_to_text(filing("<div>Management's discussion and analysis</div>" + filler("MDA")
                                   + "<div>Report of Independent Registered Public Accounting Firm</div>" + filler("AUDIT")))
        s = extract_sections(text)["7"]
        self.assertIn("MDA", text[s.char_start:s.char_end])
        self.assertNotIn("AUDIT", text[s.char_start:s.char_end])

    def test_cross_reference_filer_without_item_headings(self):
        # McDonald's pattern (build 4a): no "Item" headings in the body, only titles; the index at the end is "Item 1 | Business | Page 3".
        index = ("<div>Form 10-K Cross-Reference Index</div><div><table><tr><td>Item 1</td><td>Business</td><td>Page 3</td></tr>"
                 "<tr><td>Item 1A</td><td>Risk Factors</td><td>Page 27</td></tr><tr><td>Item 7</td><td>Management's Discussion and Analysis</td><td>Page 7</td></tr></table></div>")
        body = ("<div>BUSINESS SUMMARY</div>" + filler("BIZ", 500) + "<div>MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS</div>"
                + filler("MDA", 500) + "<div>RISK FACTORS</div>" + filler("RISK", 500) + "<div>Financial Statements and Supplementary Data</div><p>f</p>" + index)
        text = html_to_text("<html><body>" + body + "</body></html>")
        sections = extract_sections(text)
        for item, tag, others in (("1", "BIZ", ("MDA", "RISK")), ("7", "MDA", ("BIZ", "RISK")), ("1A", "RISK", ("BIZ", "MDA"))):
            s = sections[item]
            self.assertEqual((s.status, s.method), ("found", "title_fallback"), item)
            part = text[s.char_start:s.char_end]
            self.assertIn(tag, part)
            for other in others:  # each section ends at the next section's title: MD&A no longer swallows Risk Factors
                self.assertNotIn(other, part, f"Item {item} runs into {other}")


class TestPassages(unittest.TestCase):
    def setUp(self):
        shorts = "".join(f"<p>Short paragraph number {i} about the business of the company.</p>" for i in range(60))
        long_para = "<p>" + " ".join(f"Sentence number {i} says something about the brand." for i in range(120)) + "</p>"
        self.text = html_to_text(filing("<div>Item 1. Business</div>" + shorts + long_para + filler("TAIL", 100) + "<div>Item 1A. Risk Factors</div>"))
        self.section = extract_sections(self.text, "acc-9", "sha")["1"]
        self.passages = make_passages(self.text, self.section)

    def test_offsets_round_trip_exactly(self):
        self.assertGreater(len(self.passages), 5)
        for p in self.passages:
            self.assertEqual(self.text[p.char_start:p.char_end], p.text)
            self.assertGreaterEqual(p.char_start, self.section.char_start)
            self.assertLessEqual(p.char_end, self.section.char_end)

    def test_sizes_ids_and_order(self):
        self.assertEqual([p.passage_id for p in self.passages[:2]], ["acc-9:1:1", "acc-9:1:2"])
        self.assertTrue(all(p.words <= HARD_CAP_WORDS for p in self.passages))
        self.assertTrue(all(a.char_end <= b.char_start for a, b in zip(self.passages, self.passages[1:])))
        self.assertGreater(self.passages[0].words, 50)  # short paragraphs were merged

    def test_deterministic_ids_and_text(self):
        again = make_passages(self.text, extract_sections(self.text, "acc-9", "sha")["1"])
        self.assertEqual(again, self.passages)


class TestBm25(unittest.TestCase):
    def test_tokeniser(self):
        self.assertEqual(tokenise("Principal Products and Services"), ["principal", "product", "service"])
        self.assertEqual(tokenise("business analysis class bonus"), ["business", "analysis", "class", "bonus"])  # no over-stripping

    def test_relevant_passage_ranks_first(self):
        docs = [tokenise(t) for t in ("we repurchased shares and paid dividends to shareholders", "our brand is strong in beverages",
                                      "legal proceedings are described in note 12", "the weather was mild this year")]
        bm = Bm25(docs)
        scores = [bm.score(tokenise("share repurchases dividends"), i)[0] for i in range(4)]
        self.assertEqual(scores.index(max(scores)), 0)
        self.assertEqual(bm.score(tokenise("share repurchases dividends"), 1)[0], 0.0)

    def test_matched_terms_reported(self):
        bm = Bm25([tokenise("dividends and buybacks")])
        self.assertEqual(bm.score(tokenise("dividend buyback acquisition"), 0)[1], ["dividend", "buyback"])  # plurals match, misses are not listed


class FakeClient:
    """Just enough of EdgarClient for the Retriever."""

    def __init__(self, tmp: Path, html: str):
        self.settings = SimpleNamespace(cache_dir=tmp)
        self._html = html.encode()

    def latest_filing(self, cik, form="10-K"):
        return SimpleNamespace(accession="0000000001-26-000001")

    def filing_document(self, ref):
        return SimpleNamespace(body=self._html, sha256="abc123")


class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        html = filing("<div>ITEM 1. BUSINESS</div>" + filler("alpha products", 300) + "<p>We sell beverages and juice to retailers.</p>"
                      + "<div>ITEM 1A. RISK FACTORS</div>" + filler("competition risk", 300) + "<div>ITEM 1B. X</div><p>x</p>")
        self.r = Retriever(FakeClient(Path(self.tmp.name), html))

    def tearDown(self):
        self.tmp.cleanup()

    def test_search_get_passage_and_item_filter(self):
        hits = self.r.search(1, "beverages juice retailers", k=3)
        self.assertEqual(hits[0].item, "1")
        self.assertIn("matched_terms", hits[0].model_dump())
        self.assertEqual(self.r.get_passage(hits[0].passage_id).text, hits[0].text)
        self.assertEqual({h.item for h in self.r.search(1, "word1 word2", items=["1A"], k=10)}, {"1A"})
        self.assertEqual(self.r.search(1, "zzzunknown"), [])

    def test_normalised_text_is_cached_by_document_hash(self):
        self.r.index(1)
        self.assertTrue((Path(self.tmp.name) / "sections" / "abc123.v1.txt").exists())

    def test_unknown_passage_id_raises(self):
        with self.assertRaises(KeyError):
            self.r.get_passage("nope:1:1")


if __name__ == "__main__":
    unittest.main()
