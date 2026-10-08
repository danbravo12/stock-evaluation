"""Filing retriever: the qualitative agent's tools `search` and `get_passage` (ADR-022, ADR-037).

An index is built per company from its latest 10-K (read through the EdgarClient, so replay mode
works offline): HTML -> normalised text (cached by document hash) -> sections -> passages -> BM25.
Outputs are plain Pydantic objects so they can be dropped straight into the agent's trace.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from engine.contracts import FilingSection, Passage, SearchHit
from engine.filing_text import html_to_text
from engine.sections import extract_sections, make_passages
from engine.universe import cik10

TEXT_VERSION = 1  # bump when html_to_text changes, so cached text is rebuilt
K1, B = 1.5, 0.75
STOPWORDS = frozenset("a an and are as at be by for from has have in is it its of on or that the this to was we were which with our".split())


def tokenise(text: str) -> list[str]:
    """Lowercase alphanumerics, no stopwords, a trailing plural 's' stripped (no stemming library)."""
    tokens = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
            w = w[:-1]
        tokens.append(w)
    return tokens


class Bm25:
    def __init__(self, docs: list[list[str]]):
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avg_len = sum(self.len) / len(docs) if docs else 0.0
        df = Counter(t for tf in self.tf for t in tf)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query_terms: list[str], i: int) -> tuple[float, list[str]]:
        total, matched = 0.0, []
        for t in dict.fromkeys(query_terms):  # each distinct query term once
            f = self.tf[i].get(t, 0)
            if f:
                matched.append(t)
                total += self.idf[t] * f * (K1 + 1) / (f + K1 * (1 - B + B * self.len[i] / self.avg_len))
        return total, matched


class FilingIndex:
    def __init__(self, text: str, sections: dict[str, FilingSection], passages: list[Passage]):
        self.text, self.sections, self.passages = text, sections, passages
        self.bm25 = Bm25([tokenise(p.text) for p in passages])
        self.by_id = {p.passage_id: p for p in passages}


class Retriever:
    def __init__(self, client, cache_dir: Path | None = None):
        self.client = client
        self.cache_dir = Path(cache_dir or client.settings.cache_dir) / "sections"
        self._indexes: dict[str, FilingIndex] = {}
        self._by_accession: dict[str, FilingIndex] = {}

    # ---------- building ----------
    def _normalised_text(self, sha256: str, body: bytes) -> str:
        path = self.cache_dir / f"{sha256}.v{TEXT_VERSION}.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
        text = html_to_text(body.decode("utf-8", errors="replace"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    def index(self, cik: str | int) -> FilingIndex:
        cik = cik10(cik)
        if cik not in self._indexes:
            ref = self.client.latest_filing(cik, "10-K")
            doc = self.client.filing_document(ref)
            text = self._normalised_text(doc.sha256, doc.body)
            sections = extract_sections(text, ref.accession, doc.sha256)
            passages = [p for s in sections.values() if s.status == "found" for p in make_passages(text, s)]
            self._indexes[cik] = self._by_accession[ref.accession] = FilingIndex(text, sections, passages)
        return self._indexes[cik]

    # ---------- the agent's tools ----------
    def search(self, cik: str | int, query: str, items: list[str] | None = None, k: int = 5) -> list[SearchHit]:
        """Top-k passages for a query, optionally restricted to items such as ["1", "1A"]."""
        idx = self.index(cik)
        terms = tokenise(query)
        hits = []
        for i, p in enumerate(idx.passages):
            if items and p.item not in items:
                continue
            score, matched = idx.bm25.score(terms, i)
            if matched:
                hits.append(SearchHit(passage_id=p.passage_id, item=p.item, score=round(score, 4), matched_terms=matched,
                                      char_start=p.char_start, char_end=p.char_end, text=p.text))
        return sorted(hits, key=lambda h: (-h.score, h.passage_id))[:k]

    def search_many(self, cik: str | int, queries: list[str], items: list[str] | None = None, k: int = 5) -> list[SearchHit]:
        """Several queries at once: a passage's score is the sum over queries, so passages matching more of them rank higher."""
        merged: dict[str, SearchHit] = {}
        for q in queries:
            for h in self.search(cik, q, items, k=10**6):
                if h.passage_id in merged:
                    m = merged[h.passage_id]
                    merged[h.passage_id] = m.model_copy(update={"score": round(m.score + h.score, 4),
                                                                 "matched_terms": sorted(set(m.matched_terms) | set(h.matched_terms))})
                else:
                    merged[h.passage_id] = h
        return sorted(merged.values(), key=lambda h: (-h.score, h.passage_id))[:k]

    def get_passage(self, passage_id: str) -> Passage:
        accession = passage_id.split(":")[0]
        idx = self._by_accession.get(accession)
        if idx is None or passage_id not in idx.by_id:
            raise KeyError(f"unknown passage {passage_id!r} (index the company first with search)")
        return idx.by_id[passage_id]
