"""Run the section extractor over every analysed company's 10-K and print found / not_found per item (build 4a).

    .venv/bin/python scripts/sections_audit.py [--save before.json] [--compare before.json]

Reads the recorded fixtures first, then the local cache of 10-Ks fetched in live mode; never the network. The companies are the ones with a
committed full analysis in results/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.fetch.edgar import EdgarClient  # noqa: E402
from engine.retrieve import Retriever  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402


def _no_network(url, headers, timeout):
    raise RuntimeError("the network is not used by the audit")


def audit() -> dict[str, dict[str, list]]:
    settings = Settings.from_env()
    out = {}
    for f in sorted((REPO_ROOT / "results").glob("[0-9]*[0-9].json")):
        plan = json.loads(f.read_text(encoding="utf-8"))["plan"]
        for client in (EdgarClient("replay", settings), EdgarClient("live", settings, transport=_no_network)):
            try:
                idx = Retriever(client).index(plan["cik"])
            except Exception:
                continue
            out[plan["ticker"]] = {k: [s.status, s.length, s.method] for k, s in idx.sections.items()}
            break
        else:
            out[plan["ticker"]] = {"error": ["10-K not available locally", 0, None]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save")
    ap.add_argument("--compare")
    a = ap.parse_args()
    now = audit()
    before = json.loads(Path(a.compare).read_text()) if a.compare else None
    n_found = sum(v[0] == "found" for d in now.values() for v in d.values())
    n_all = sum(len(d) for d in now.values())
    print(f"{len(now)} companies, {n_found} of {n_all} items found")
    for t, d in now.items():
        for item, (status, length, method) in d.items():
            line = f"{t:6} Item {item:3} {status:9} {length:8} {method}"
            if before and t in before and item in before[t] and before[t][item][:3] != [status, length, method]:
                line += f"   (before: {before[t][item][0]} {before[t][item][1]} {before[t][item][2]})"
            if not before or "before:" in line or status != "found":
                print(line)
    if a.save:
        Path(a.save).write_text(json.dumps(now, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
