"""Sentence segmentation (ADR-046): rules on synthetic text, exact round trip on all five recorded filings."""
from __future__ import annotations

import unittest

from engine.fetch.edgar import EdgarClient
from engine.retrieve import Retriever
from engine.sentences import MAX_WORDS, split_sentences
from engine.settings import Settings

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]


def sents(text: str) -> list[str]:
    return [text[a:b] for a, b in split_sentences(text, 0, len(text))]


class TestRules(unittest.TestCase):
    def test_ordinary_sentences_and_newlines(self):
        self.assertEqual(sents("We sell drinks. Revenue grew 4%.\nSecond line without a stop\nThird."),
                         ["We sell drinks.", "Revenue grew 4%.", "Second line without a stop", "Third."])

    def test_bullets_split_inline_and_at_line_start(self):
        self.assertEqual(sents("Card income decreased: •lower income in CCB, •higher costs.\n- a dash item\n◦ small\n▪ square"),
                         ["Card income decreased:", "•lower income in CCB,", "•higher costs.", "- a dash item", "◦ small", "▪ square"])

    def test_abbreviations_and_decimals_do_not_split(self):
        text = "The U.S. Securities and Exchange Commission, Inc. and Acme Corp. filed No. 5 on Dec. 31, 2025, e.g. in Ohio."
        self.assertEqual(sents(text), [text])
        self.assertEqual(sents("Revenue was $1.5 billion. Margins rose to 12.4% in 2025."), ["Revenue was $1.5 billion.", "Margins rose to 12.4% in 2025."])
        self.assertEqual(sents("J. P. Morgan Chase reported."), ["J. P. Morgan Chase reported."])

    def test_quote_digit_and_bracket_starts_split_lowercase_does_not(self):
        self.assertEqual(sents('He said "stop." "Yes," she said. 2025 was better. (See note.) then continued.'),
                         ['He said "stop."', '"Yes," she said.', "2025 was better.", "(See note.) then continued."])

    def test_long_sentences_are_cut_at_semicolons_then_at_word_60(self):
        words = " ".join(f"w{i}" for i in range(100))
        long_no_semicolon = sents(words + ".")
        self.assertEqual([len(s.split()) for s in long_no_semicolon], [60, 40])
        with_semicolons = sents(" ".join(f"a{i}" for i in range(50)) + "; " + " ".join(f"b{i}" for i in range(50)) + ".")
        self.assertEqual(len(with_semicolons), 2)
        self.assertTrue(with_semicolons[0].endswith(";"))
        self.assertTrue(all(len(s.split()) <= MAX_WORDS for s in sents(" ".join("x" for _ in range(500)) + ".")))

    def test_exact_offsets_inside_a_range_and_nothing_lost(self):
        text = "Header\nOne two. Three four •five six; seven.\nEight."
        start, end = 7, len(text)
        spans = split_sentences(text, start, end)
        self.assertEqual("".join("".join(text[a:b].split()) for a, b in spans), "".join(text[start:end].split()))
        self.assertTrue(all(start <= a < b <= end for a, b in spans))
        self.assertEqual(spans, sorted(spans))
        self.assertEqual(split_sentences("", 0, 0), [])

    def test_deterministic(self):
        t = "A b. C d.\n•e f. G."
        self.assertEqual(split_sentences(t, 0, len(t)), split_sentences(t, 0, len(t)))


class TestRecordedFilings(unittest.TestCase):
    def test_every_passage_of_every_filing_round_trips(self):
        settings = Settings.from_env()
        client = EdgarClient("replay", settings)
        retriever = Retriever(client)
        for t in TICKERS:
            idx = retriever.index(client.lookup_cik(t)[0])
            total = 0
            for p in idx.passages:
                self.assertTrue(p.sentences, p.passage_id)
                prev_end = p.char_start
                for a, b in p.sentences:
                    self.assertTrue(p.char_start <= prev_end <= a < b <= p.char_end, (p.passage_id, a, b))
                    self.assertEqual(idx.text[a:b], idx.text[a:b].strip())
                    self.assertLessEqual(len(idx.text[a:b].split()), MAX_WORDS, (p.passage_id, a, b))
                    prev_end = b
                self.assertEqual("".join("".join(idx.text[a:b].split()) for a, b in p.sentences), "".join(p.text.split()), p.passage_id)
                total += len(p.sentences)
            self.assertGreater(total, len(idx.passages), t)


if __name__ == "__main__":
    unittest.main()
