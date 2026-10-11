"""The blind labelling packet and its labels (build 4a, ADR-071).

    build_packet(tickers, ...)  -> markdown: per company and criterion the question, the full rubric and the passages of a fixed retrieval
    parse_filled_packet(text)   -> {ticker: {criterion: {"human_verdict", "note"}}} from a packet the reviewer filled in

The packet never reads an agent result, a trace or a fixture of model replies: only the company's 10-K (through the Retriever), `config/search_terms.json`
(the rubric and each criterion's own queries) and `config/label_packet.json`. The retrieval is the same for every company and does not depend on any model.
"""
from __future__ import annotations

import json
import re

from engine.contracts import QUAL_CRITERIA
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT

CONFIG = REPO_ROOT / "config" / "label_packet.json"
RUBRIC = REPO_ROOT / "config" / "search_terms.json"
SHORT = {"found": "evidence found", "weak": "evidence weak", "insufficient": "insufficient evidence"}
TITLES = {"understandable_business": "Understandable business", "durable_competitive_advantage": "Durable competitive advantage",
          "candid_management": "Candid management", "rational_capital_allocation": "Rational capital allocation"}
VERDICT_LINE = re.compile(r"^\*\*Verdict:\*\*\s*(.*?)\s*$", re.I)
NOTE_LINE = re.compile(r"^\*\*Note:\*\*\s*(.*?)\s*$", re.I)
ITEM_HEAD = re.compile(r"^### ([A-Z.\-]+) · (\w+)\s*$")
PLACEHOLDER = "…"


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def fixed_retrieval(retriever: Retriever, cik: str, spec: dict, config: dict):
    """The criterion's own queries plus the generic ones, over its items; the top passages, shown in filing order."""
    queries = list(spec["queries"]) + list(config["generic_queries"])
    hits = retriever.search_many(cik, queries, spec["items"], k=config["passages_per_criterion"])
    idx = retriever.index(cik)
    passages = [idx.by_id[h.passage_id] for h in hits]
    return sorted(passages, key=lambda p: ({"1": 0, "1A": 1, "7": 2}.get(p.item, 9), p.n))


def _quote(text: str) -> str:
    return "\n".join("> " + line if line else ">" for line in text.split("\n"))


def build_packet(companies: list[tuple[str, str]], retriever: Retriever, *, config: dict | None = None, rubric: dict | None = None,
                 heldout: dict | None = None) -> str:
    """`companies` is [(ticker, cik)]. Returns the packet as markdown. Deterministic for a fixed filing and fixed config."""
    config = config or load_config()
    rubric = rubric or json.loads(RUBRIC.read_text(encoding="utf-8"))["criteria"]
    n_items = len(companies) * len(QUAL_CRITERIA)
    out = ["# Held-out labelling packet", "",
           f"{len(companies)} companies × {len(QUAL_CRITERIA)} criteria = {n_items} items. **Research material, not financial advice.** "
           "The passages come from each company's latest Form 10-K and were picked by a fixed keyword retrieval, not by the analysis tool.", "",
           "## How to label", "",
           "1. For each item read the question and the rubric, then the passages. A passage is only a starting point: open the filing at the SEC link if you need more, "
           "and judge what the **filing** shows, not only what the passages show.",
           "2. Pick one verdict for the item: `found`, `weak` or `insufficient`, using the rubric's meanings and applying the latest-fiscal-year rule where it is given.",
           f"3. Write it on the Verdict line (replace `{PLACEHOLDER}`), with an optional note on the Note line. Do not change anything else in the file.",
           "4. Do not look at the website's verdicts for these companies until every item is labelled. If you have already seen some, say so in the first note of the file.",
           "5. When all items are done, run `python scripts/label_packet.py --ingest docs/labelling/heldout_packet.md` to write `eval/heldout_labels.json`.", ""]
    if heldout:
        out += [f"List frozen {heldout['frozen']} (`eval/heldout.json`).", ""]
    for ticker, cik in companies:
        idx = retriever.index(cik)
        ref = retriever.client.latest_filing(cik, "10-K")
        out += ["---", "", f"## {ticker}", "", f"Form 10-K, accession {ref.accession}, filed {ref.filing_date}, period {ref.report_date}. [Open the filing on sec.gov]({ref.url})", ""]
        missing = [f"Item {i}" for i, s in idx.sections.items() if s.status != "found"]
        if missing:
            out += [f"Sections not located in this filing's text by the tool: {', '.join(missing)}. Use the SEC link for them.", ""]
        for name in QUAL_CRITERIA:
            spec = rubric[name]
            out += [f"### {ticker} · {name}", "", f"**{TITLES[name]}.** {spec['question']}", "",
                    f"- **found** (\"evidence found\"): {spec['found_means']}",
                    f"- **weak** (\"evidence weak\"): {spec['weak_means']}",
                    f"- **insufficient** (\"insufficient evidence\"): {spec['insufficient_means']}"]
            if spec.get("year_rule"):
                out.append(f"- **Year rule:** {spec['year_rule']}")
            if spec.get("rationale_note"):
                note = spec["rationale_note"].split("if your verdict")[0].strip().removeprefix("Limitation:").strip().rstrip(";,")
                out.append(f"- **Limitation:** {note}.")
            out += ["", f"Passages ({', '.join('Item ' + i for i in spec['items'])}), in filing order:", ""]
            for p in fixed_retrieval(retriever, cik, spec, config):
                out += [f"**[{p.passage_id}]** Item {p.item} · [filing]({ref.url})", "", _quote(p.text), ""]
            out += [f"**Verdict:** {PLACEHOLDER}  _(found / weak / insufficient)_", "", f"**Note:** ", ""]
    return "\n".join(out) + "\n"


def parse_filled_packet(text: str) -> tuple[dict, list[str]]:
    """Labels from a filled-in packet, and the problems found (an item without a verdict, or a verdict that is not found / weak / insufficient)."""
    labels: dict[str, dict[str, dict]] = {}
    problems: list[str] = []
    current = None
    for line in text.split("\n"):
        m = ITEM_HEAD.match(line)
        if m:
            current = (m.group(1), m.group(2))
            labels.setdefault(current[0], {})[current[1]] = {"human_verdict": None, "note": ""}
            continue
        if current is None:
            continue
        v = VERDICT_LINE.match(line)
        if v:
            raw = re.sub(r"_?\(found / weak / insufficient\)_?", "", v.group(1)).strip(" _*`").lower()
            if raw in SHORT:
                labels[current[0]][current[1]]["human_verdict"] = SHORT[raw]
            elif raw in ("", PLACEHOLDER):
                problems.append(f"{current[0]} {current[1]}: no verdict yet")
            else:
                problems.append(f"{current[0]} {current[1]}: {raw!r} is not found, weak or insufficient")
            continue
        n = NOTE_LINE.match(line)
        if n:
            labels[current[0]][current[1]]["note"] = n.group(1)
    return labels, problems
