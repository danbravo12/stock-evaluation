"""Sentence segmentation with exact offsets (ADR-046).

The qualitative agent cites passages by sentence number, so the boundaries must be deterministic and every sentence
must be a slice of the document text: `document[start:end]`. Over-splitting is acceptable; losing text is not.

Breaks: at every newline; before every bullet character ("•", "◦", "▪", and "-" at the start of a line); after sentence-final
punctuation followed by whitespace and an uppercase letter, digit, quote, bracket or bullet, except after common
abbreviations and initials. A "sentence" over MAX_WORDS words is cut at "; ", else after word CUT_WORDS, repeatedly.
"""
from __future__ import annotations

import re

MAX_WORDS = 80
CUT_WORDS = 60
BULLETS = "•◦▪"
ABBREVIATIONS = frozenset("""u.s u.k inc corp co ltd plc no nos approx e.g i.e vs mr mrs ms dr st jr sr fig ca
jan feb mar apr jun jul aug sep sept oct nov dec""".split())
BOUNDARY = re.compile(r"""([.!?]["'”’)\]]*)(\s+)(?=["'“‘(\[]?[A-Z0-9•◦▪])""")
BEFORE_PERIOD = re.compile(r"[A-Za-z][A-Za-z.]*$")


def _is_abbreviation(before: str) -> bool:
    m = BEFORE_PERIOD.search(before)
    if not m:
        return False
    token = m.group(0).lower()
    return token in ABBREVIATIONS or len(token) == 1 or "." in token  # "U.S", an initial ("J. P. Morgan"), "e.g"


def _bullet_segments(text: str, start: int, end: int) -> list[tuple[int, int]]:
    cuts = [start]
    for i in range(start, end):
        ch = text[i]
        if (ch in BULLETS or (ch == "-" and (i == start or text[i - 1] == "\n") and text[i + 1:i + 2] == " ")) and i > cuts[-1]:
            cuts.append(i)
    cuts.append(end)
    return [(cuts[k], cuts[k + 1]) for k in range(len(cuts) - 1)]


def _sentence_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    seg = text[start:end]
    spans, prev = [], 0
    for m in BOUNDARY.finditer(seg):
        if m.group(1)[0] == "." and _is_abbreviation(seg[:m.start()]):
            continue
        spans.append((start + prev, start + m.end(1)))
        prev = m.end(2)
    spans.append((start + prev, end))
    return spans


def _trim(text: str, a: int, b: int) -> tuple[int, int] | None:
    while a < b and text[a].isspace():
        a += 1
    while b > a and text[b - 1].isspace():
        b -= 1
    return (a, b) if b > a else None


def _cut_long(text: str, a: int, b: int) -> list[tuple[int, int]]:
    if len(text[a:b].split()) <= MAX_WORDS:
        return [(a, b)]
    pieces = []
    if "; " in text[a:b]:
        cur = a
        for m in re.finditer(r";\s+", text[a:b]):
            pieces.append((cur, a + m.start() + 1))
            cur = a + m.end()
        pieces.append((cur, b))
    else:
        pieces = [(a, b)]
    out = []
    for pa, pb in pieces:
        while len(text[pa:pb].split()) > MAX_WORDS:
            words = list(re.finditer(r"\S+", text[pa:pb]))
            out.append((pa, pa + words[CUT_WORDS - 1].end()))
            pa = pa + words[CUT_WORDS].start()
        out.append((pa, pb))
    return out


def split_sentences(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Sentence spans (start, end) inside text[start:end], in order, each trimmed and non-empty."""
    out = []
    pos = start
    for line in text[start:end].split("\n"):
        line_start, pos = pos, pos + len(line) + 1
        for a, b in _bullet_segments(text, line_start, line_start + len(line)):
            for sa, sb in _sentence_spans(text, a, b):
                span = _trim(text, sa, sb)
                if span:
                    out.extend(_cut_long(text, *span))
    return out
