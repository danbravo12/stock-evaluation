"""Agreement between the qualitative agent and the human-reviewed gold set (ADR-050).

    .venv/bin/python -m eval.qualitative_agreement

The gold set (`eval/expected_qualitative.json`) holds, per ticker and criterion, the recorded agent verdict, the human verdict and a note.
Agreement = human verdict equals the verdict under test. "Over-generous" = the verdict under test is more favourable than the human one
(found > weak > insufficient evidence).
"""
from __future__ import annotations

import json

from engine.agents.qualitative import assess_qualitative
from engine.contracts import QUAL_CRITERIA, QualFindings
from engine.fetch.edgar import EdgarClient
from engine.llm.client import LLMClient
from engine.retrieve import Retriever
from engine.settings import REPO_ROOT, Settings
from engine.trace import TraceRecorder

GOLD_PATH = REPO_ROOT / "eval" / "expected_qualitative.json"
RANK = {"insufficient evidence": 0, "evidence weak": 1, "evidence found": 2}


def load_gold() -> dict:
    return json.loads(GOLD_PATH.read_text(encoding="utf-8"))


def replay_findings(tickers: list[str] | None = None, retriever: Retriever | None = None, llm: LLMClient | None = None) -> dict[str, QualFindings]:
    """The recorded agent run, replayed from the fixtures (no network)."""
    settings = Settings.from_env()
    retriever = retriever or Retriever(EdgarClient("replay", settings))
    llm = llm or LLMClient("replay", settings)
    tickers = tickers or json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"]
    return {t: assess_qualitative(retriever.client.lookup_cik(t)[0], t, retriever, llm, TraceRecorder("gold")) for t in tickers}


def agreement(verdicts: dict[str, dict[str, str]], gold: dict) -> dict:
    """verdicts[ticker][criterion] against the human labels. Returns counts and the list of disagreements."""
    rows, wrong = 0, []
    for t, crits in gold["gold"].items():
        for c in QUAL_CRITERIA:
            rows += 1
            got, human = verdicts[t][c], crits[c]["human_verdict"]
            if got != human:
                wrong.append({"ticker": t, "criterion": c, "got": got, "human": human,
                              "direction": "over-generous" if RANK.get(got, -1) > RANK[human] else "too strict"})
    return {"total": rows, "agree": rows - len(wrong), "disagreements": wrong}


def verdicts_of(findings: dict[str, QualFindings]) -> dict[str, dict[str, str]]:
    return {t: {f.criterion: f.verdict for f in fs.findings} for t, fs in findings.items()}


if __name__ == "__main__":
    gold = load_gold()
    result = agreement(verdicts_of(replay_findings()), gold)
    print(f"agent vs human: {result['agree']}/{result['total']} agree ({gold['reviewer']})")
    for d in result["disagreements"]:
        print(f"  {d['ticker']} {d['criterion']}: agent {d['got']!r}, human {d['human']!r} ({d['direction']})")
