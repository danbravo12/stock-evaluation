"""Fetch the S&P 500 constituents once and freeze them (ADR-014, ADR-053).

    .venv/bin/python scripts/snapshot_universe.py            # fetch via the MediaWiki API, record the raw response, write the CSV
    .venv/bin/python scripts/snapshot_universe.py --offline  # re-parse the recorded response (no network)

The raw API response goes to fixtures/universe/ (checksummed store, like EDGAR); the parsed table to data/universe/sp500_<date>.csv.
The snapshot is validated against SEC's company_tickers fixture. Never run at analysis time: analyses read the CSV.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.fetch.edgar import EdgarClient  # noqa: E402
from engine.fetch.store import ResponseStore  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402
from engine.universe import UNIVERSE_DIR, latest_snapshot_path, parse_constituents_html, validate_universe, write_csv  # noqa: E402

URL = "https://en.wikipedia.org/w/api.php?action=parse&page=List_of_S%26P_500_companies&prop=text&format=json&formatversion=2"
KEY = "wikipedia/sp500_constituents.json"


def main(offline: bool) -> int:
    settings = Settings.from_env()
    store = ResponseStore(settings.fixtures_dir / "universe")
    if offline:
        hit = store.get(KEY)
        if hit is None:
            print("No recorded response; run without --offline.")
            return 1
        body = hit.body
        fetched = latest_snapshot_path().stem.removeprefix("sp500_") if list(UNIVERSE_DIR.glob("sp500_*.csv")) else hit.fetched_at[:10]
    else:
        ua = settings.sec_user_agent or "StockEvaluation research tool (personal project)"
        req = urllib.request.Request(URL, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
        store.put(KEY, URL, body, "application/json")
        fetched = date.today().isoformat()
    html = json.loads(body)["parse"]["text"]
    rows = parse_constituents_html(html)
    sec = EdgarClient("replay", settings).company_tickers()
    problems = validate_universe(rows, sec)
    out = UNIVERSE_DIR / f"sp500_{fetched}.csv"
    write_csv(rows, out)
    print(f"{len(rows)} rows -> {out.relative_to(REPO_ROOT)}")
    for p in problems:
        print("  PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main("--offline" in sys.argv))
