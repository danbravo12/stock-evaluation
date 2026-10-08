"""Record EDGAR fixtures for the test tickers (ADR-024).

Run once, on a machine with internet access, from the repo root:

    python3 scripts/record_fixtures.py

Needs SEC_USER_AGENT in .env (see .env.example). Uses only the Python standard
library. Makes about 16 requests in total, paced well under SEC's limit, and
writes everything under fixtures/edgar/ plus fixtures/MANIFEST.json.
After this, tests and development run fully offline in replay mode.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.fetch.edgar import EdgarClient, EdgarError  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402

TEST_TICKERS_FILE = REPO_ROOT / "config" / "test_tickers.json"


def main() -> int:
    settings = Settings.from_env()
    tickers = json.loads(TEST_TICKERS_FILE.read_text(encoding="utf-8"))["tickers"]
    try:
        client = EdgarClient("record", settings)
    except EdgarError as e:
        print(f"ERROR: {e}")
        return 1

    manifest = {
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "U.S. Securities and Exchange Commission, EDGAR (public domain)",
        "companies": [],
    }
    print("Recording SEC company ticker file...")
    client.company_tickers()

    failures = 0
    for ticker in tickers:
        try:
            cik, title = client.lookup_cik(ticker)
            print(f"{ticker:<6} CIK {cik}  {title}")
            subs = client.submissions(cik)
            facts = client.companyfacts(cik)
            ref = client.latest_filing(cik, "10-K")
            doc = client.filing_document(ref)
            n_concepts = sum(len(v) for v in facts.get("facts", {}).values())
            print(
                f"       submissions OK · companyfacts OK ({n_concepts} concepts) · "
                f"10-K {ref.accession} filed {ref.filing_date} ({len(doc.body) / 1e6:.1f} MB)"
            )
            manifest["companies"].append(
                {
                    "ticker": ticker,
                    "cik": cik,
                    "name": title,
                    "sic_description": subs.get("sicDescription"),
                    "fiscal_year_end": subs.get("fiscalYearEnd"),
                    "xbrl_concepts": n_concepts,
                    "latest_10k": {
                        "accession": ref.accession,
                        "filing_date": ref.filing_date,
                        "report_date": ref.report_date,
                        "primary_document": ref.primary_document,
                        "url": ref.url,
                        "sha256": doc.sha256,
                    },
                }
            )
        except EdgarError as e:
            failures += 1
            print(f"{ticker:<6} FAILED: {e}")

    manifest["requests_made"] = client.requests_made
    out = settings.fixtures_dir / "MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(tickers) - failures}/{len(tickers)} companies recorded, "
          f"{client.requests_made} requests. Manifest: {out.relative_to(REPO_ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
