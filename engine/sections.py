"""Find Items 1, 1A and 7 in the normalised 10-K text and cut them into passages (ADR-036, ADR-037).

Pure functions over text. All offsets refer to the normalised text from `filing_text.html_to_text`.

Section rule: heading candidates are lines such as "Item 1A. Risk Factors". A section runs from its
heading to the next item heading. The table of contents has the same headings, so the candidate
with the longest section wins, and it must be at least MIN_SECTION_CHARS long. If none qualifies
(some banks keep a cross-reference index), the section title on a line of its own is tried the same
way. If that fails too, the section is reported as not_found with a reason: nothing is guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from engine.contracts import FilingSection, Passage
from engine.sentences import split_sentences

MIN_SECTION_CHARS = 2000
MAX_HEADING_WORDS = 25
TARGET_WORDS = 200  # merge short paragraphs up to about this many words
HARD_CAP_WORDS = 350

# item -> (title pattern for the fallback, labels of the headings that end it)
SECTIONS = {
    "1": (r"business", {"1A", "1B", "1C", "2"}),
    "1A": (r"risk factors", {"1B", "1C", "2"}),
    "7": (r"management's discussion and analysis(?: of financial condition and results of operations)?", {"7A", "8"}),
}
ITEM_HEADING = re.compile(r"^items?\s+((?:\d{1,2}[a-c]?(?![a-z0-9])\s*(?:,|and|&)?\s*)+)", re.I)
END_TITLE = re.compile(r"^(report of independent registered public accounting firm|financial statements and supplementary data)\b", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


@dataclass(frozen=True)
class Line:
    start: int
    end: int  # exclusive, without the newline
    text: str


def _lines(text: str) -> list[Line]:
    out, pos = [], 0
    for t in text.split("\n"):
        out.append(Line(pos, pos + len(t), t))
        pos += len(t) + 1
    return out


def _heading_labels(line: Line) -> set[str]:
    """{'1', '2'} for 'Items 1 and 2. Business and Properties'; empty if the line is not an item heading."""
    m = ITEM_HEADING.match(line.text)
    if not m or len(line.text.split()) > MAX_HEADING_WORDS:
        return set()
    return {label.upper() for label in re.findall(r"\d{1,2}[a-c]?", m.group(1), re.I)}


def _section_from(candidates: list[int], lines: list[Line], is_end) -> tuple[int, int] | None:
    """Longest (start line, end line) among candidate heading lines; each ends at the next end marker."""
    best, ends = None, [i for i, ln in enumerate(lines) if is_end(ln)]
    for c in candidates:
        nxt = next((e for e in ends if e > c), None)
        if nxt is None:
            continue  # never run to the end of the document
        length = lines[nxt].start - lines[c].start
        if best is None or length > best[0]:
            best = (length, c, nxt)
    return None if best is None else (best[1], best[2])


def extract_sections(text: str, accession: str = "", sha256: str = "") -> dict[str, FilingSection]:
    lines = _lines(text)
    headings = {i: _heading_labels(ln) for i, ln in enumerate(lines)}
    headings = {i: labels for i, labels in headings.items() if labels}
    out = {}
    for item, (title, end_labels) in SECTIONS.items():
        base = dict(item=item, accession=accession, sha256=sha256)
        attempts = [
            ("item_heading", [i for i, lb in headings.items() if item in lb], lambda ln, e=end_labels: bool(_heading_labels(ln) & e)),
            ("title_fallback", [i for i, ln in enumerate(lines) if re.fullmatch(rf"{title}\s*[.:]?", ln.text, re.I)],
             lambda ln, e=end_labels: bool(_heading_labels(ln) & e) or bool(END_TITLE.match(ln.text))),
        ]
        longest = {}
        for method, candidates, is_end in attempts:
            found = _section_from(candidates, lines, is_end)
            if found:
                start, end = lines[found[0]].start, lines[found[1]].start - 1  # drop the newline before the next heading
                longest[method] = end - start
                if end - start >= MIN_SECTION_CHARS:
                    out[item] = FilingSection(status="found", method=method, char_start=start, char_end=end, length=end - start, **base)
                    break
            else:
                longest[method] = 0
        else:
            reason = (f"no 'Item {item}' heading gives a section of {MIN_SECTION_CHARS}+ chars (longest {longest['item_heading']}); "
                      f"no title line gives one either (longest {longest['title_fallback']})")
            out[item] = FilingSection(status="not_found", reason=reason, **base)
    return out


# ---------- passages ----------
def _split_paragraph(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split a paragraph longer than the hard cap at sentence ends into chunks of about TARGET_WORDS."""
    cuts = [start] + [start + m.end() for m in SENTENCE_END.finditer(text[start:end])] + [end + 1]
    pieces = [(cuts[i], cuts[i + 1] - 1) for i in range(len(cuts) - 1)]  # sentence spans (without trailing space)
    chunks, cur = [], None
    for a, b in pieces:
        words = len(text[a:b].split())
        if words > HARD_CAP_WORDS:  # a single enormous "sentence": cut on word boundaries
            if cur:
                chunks.append(cur)
                cur = None
            spans = [m.span() for m in re.finditer(r"\S+", text[a:b])]
            for k in range(0, len(spans), TARGET_WORDS):
                chunks.append((a + spans[k][0], a + spans[min(k + TARGET_WORDS, len(spans)) - 1][1]))
        elif cur and len(text[cur[0]:cur[1]].split()) + words > TARGET_WORDS:
            chunks.append(cur)
            cur = (a, b)
        else:
            cur = (cur[0], b) if cur else (a, b)
    if cur:
        chunks.append(cur)
    return chunks


def make_passages(text: str, section: FilingSection) -> list[Passage]:
    """Cut a found section into passages: short paragraphs merged up to ~200 words, long ones split at sentence ends."""
    assert section.status == "found"
    spans: list[tuple[int, int]] = []  # passage spans, in order
    acc: tuple[int, int] | None = None
    acc_words = 0
    pos = section.char_start
    for line in text[section.char_start:section.char_end].split("\n"):
        start, end = pos, pos + len(line)
        pos = end + 1
        words = len(line.split())
        if not words:
            continue
        if words > HARD_CAP_WORDS:
            if acc:
                spans.append(acc)
                acc = None
            spans.extend(_split_paragraph(text, start, end))
        elif acc and acc_words + words <= TARGET_WORDS:
            acc, acc_words = (acc[0], end), acc_words + words
        else:
            if acc:
                spans.append(acc)
            acc, acc_words = (start, end), words
    if acc:
        spans.append(acc)
    return [Passage(passage_id=f"{section.accession}:{section.item}:{n}", accession=section.accession, item=section.item, n=n,
                    char_start=a, char_end=b, words=len(text[a:b].split()), text=text[a:b],
                    sentences=split_sentences(text, a, b))
            for n, (a, b) in enumerate(spans, start=1)]
