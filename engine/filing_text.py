"""10-K HTML -> normalised plain text (ADR-035).

The output is THE citation text: every section offset, passage offset and quote refers to
it, and the Critic later checks quotes verbatim against it. The conversion is deterministic
and uses only the standard library.

Rules: drop script/style, hidden inline-XBRL blocks (`ix:header`, `display:none`); block
boundaries become line breaks; a table row becomes one line with its non-empty cells joined
by " | "; whitespace is collapsed; non-breaking spaces and curly quotes become plain ones.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "head", "ix:header"}
VOID_TAGS = {"br", "hr", "img", "meta", "link", "input", "col"}
BLOCK_TAGS = {"p", "div", "br", "hr", "li", "ul", "ol", "table", "tr", "section", "article", "header", "footer",
              "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "center", "body"}
CELL_TAGS = {"td", "th"}
HIDDEN_STYLE = re.compile(r"display\s*:\s*none", re.I)
CHAR_MAP = str.maketrans({" ": " ", " ": " ", " ": " ", "‘": "'", "’": "'", "“": '"', "”": '"',
                          "​": None, "﻿": None, "­": None})
IX_HEADER = re.compile(r"<ix:header>.*?</ix:header>", re.S | re.I)  # can be megabytes; removing it first is only a speed-up


class _TextBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._line: list[str] = []
        self._stack: list[tuple[str, bool]] = []  # (tag, hidden)
        self._hidden = 0
        self._row: list[str] | None = None  # cells of the current table row
        self._cell: list[str] | None = None

    # --- output helpers ---
    def _emit(self, parts: list[str]):
        text = " ".join("".join(parts).translate(CHAR_MAP).split())
        if text:
            self.lines.append(text)

    def _break(self):
        if self._cell is not None:  # inside a table cell a block boundary is just a space
            self._cell.append(" ")
        elif self._row is None:
            self._emit(self._line)
            self._line = []

    # --- parser events ---
    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            if tag in BLOCK_TAGS and not self._hidden:
                self._break()
            return
        hidden = tag in SKIP_TAGS or bool(HIDDEN_STYLE.search(dict(attrs).get("style") or ""))
        self._stack.append((tag, hidden))
        self._hidden += hidden
        if self._hidden:
            return
        if tag == "tr":
            self._break()
            self._row = []
        elif tag in CELL_TAGS and self._row is not None:
            self._cell = []
        elif tag in BLOCK_TAGS:
            self._break()

    def handle_endtag(self, tag):
        if tag in VOID_TAGS or not any(t == tag for t, _ in self._stack):
            return
        while self._stack:  # pop up to the matching start tag (tolerates sloppy HTML)
            top, hidden = self._stack.pop()
            self._hidden -= hidden
            if top == tag:
                break
        if self._hidden:
            return
        if tag in CELL_TAGS and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).translate(CHAR_MAP).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            row, self._row = self._row, None
            self._emit([" | ".join(c for c in row if c)])
        elif tag in BLOCK_TAGS:
            self._break()

    def handle_data(self, data):
        if self._hidden:
            return
        if self._cell is not None:
            self._cell.append(data)
        elif self._row is None:
            self._line.append(data)

    def close(self):
        super().close()
        self._emit(self._line)


def html_to_text(html: str) -> str:
    builder = _TextBuilder()
    builder.feed(IX_HEADER.sub("", html))
    builder.close()
    return "\n".join(builder.lines)
