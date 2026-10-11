"""Add the cited passages' text to results written before schema 1.2 (build 4a, ADR-069 amendment). No model, no network.

    .venv/bin/python scripts/backfill_passages.py [results_dir]

Nothing else in a result changes (verdicts, rationales, citations, costs): the passages are read from the recorded fixtures or the local cache of
10-Ks, the schema version becomes 1.2, and the file is validated again. Fails loudly if a cited passage cannot be loaded.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.fetch.edgar import EdgarClient  # noqa: E402
from engine.report import SCHEMA_VERSION, Result, cited_passages, export_schema, result_json  # noqa: E402
from engine.retrieve import Retriever  # noqa: E402
from engine.settings import Settings  # noqa: E402


def _no_network(url, headers, timeout):
    raise RuntimeError("the network is not used by the backfill")


def retriever_for(cik: str, settings: Settings) -> Retriever:
    for client in (EdgarClient("replay", settings), EdgarClient("live", settings, transport=_no_network)):
        r = Retriever(client)
        try:
            r.index(cik)
            return r
        except Exception:
            continue
    raise RuntimeError(f"no local copy of the 10-K for CIK {cik}")


def main() -> None:
    settings = Settings.from_env()
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else settings.results_dir
    for f in sorted(results_dir.glob("[0-9]*[0-9].json")):
        res = Result.model_validate_json(f.read_text(encoding="utf-8"))
        if not res.qualitative:
            continue
        res.passages = cited_passages(res.qualitative, retriever_for(res.plan.cik, settings))
        res.schema_version = SCHEMA_VERSION
        f.write_text(result_json(res), encoding="utf-8")
        print(f"{f.name}: {len(res.passages)} passages")
    export_schema()


if __name__ == "__main__":
    main()
