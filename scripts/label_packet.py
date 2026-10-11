"""Build the blind labelling packet for the held-out companies, or read a filled-in one back (build 4a, ADR-071).

    .venv/bin/python scripts/label_packet.py                      # writes docs/labelling/heldout_packet.md (git-ignored)
    .venv/bin/python scripts/label_packet.py --ingest <file.md>   # writes eval/heldout_labels.json from a filled-in packet

Offline: reads the 10-Ks from the recorded fixtures or the local cache, never the network and never an agent result.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.packet import build_packet, parse_filled_packet  # noqa: E402
from engine.contracts import QUAL_CRITERIA  # noqa: E402
from engine.fetch.edgar import EdgarClient  # noqa: E402
from engine.retrieve import Retriever  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402
from engine.universe import load_universe  # noqa: E402

HELDOUT = REPO_ROOT / "eval" / "heldout.json"
LABELS = REPO_ROOT / "eval" / "heldout_labels.json"
PACKET = REPO_ROOT / "docs" / "labelling" / "heldout_packet.md"


def _no_network(url, headers, timeout):
    raise RuntimeError("the network is not used by the packet")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest")
    ap.add_argument("--out", default=str(PACKET))
    a = ap.parse_args()
    heldout = json.loads(HELDOUT.read_text(encoding="utf-8"))
    if a.ingest:
        labels, problems = parse_filled_packet(Path(a.ingest).read_text(encoding="utf-8"))
        template = json.loads(LABELS.read_text(encoding="utf-8"))
        for t, crits in labels.items():
            for c, v in crits.items():
                if t in template["labels"] and c in template["labels"][t]:
                    template["labels"][t][c] = v
        LABELS.write_text(json.dumps(template, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{sum(v['human_verdict'] is not None for c in template['labels'].values() for v in c.values())} of {heldout['items']} items labelled")
        for p in problems:
            print("  " + p)
        return
    settings = Settings.from_env()
    universe = load_universe()
    companies = [(t, universe.row_for(t).cik) for t in heldout["companies"]]
    retriever = None
    for client in (EdgarClient("replay", settings), EdgarClient("live", settings, transport=_no_network)):
        r = Retriever(client)
        try:
            for _, cik in companies:
                r.index(cik)
            retriever = r
            break
        except Exception:
            continue
    if retriever is None:
        sys.exit("the 10-Ks of the held-out companies are not available locally (fixtures or data/cache)")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_packet(companies, retriever, heldout=heldout), encoding="utf-8")
    print(f"wrote {out} ({len(companies) * len(QUAL_CRITERIA)} items)")


if __name__ == "__main__":
    main()
