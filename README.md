# Graham & Buffett Equity Research Tool

> **Research and analysis tool. Not financial advice.** It reports which published Graham and Buffett criteria a company meets and why, with sources. It never recommends buying or selling.

Status: early build. See `STATUS.md`, design in `ARCHITECTURE.md`, decisions in `DECISIONS.md`, workflow in `PROCESS.md`.

## Run the tests (offline, standard library only)

    python3 -m unittest -v

## Record EDGAR fixtures (once, needs internet)

    cp .env.example .env      # then set SEC_USER_AGENT
    python3 scripts/record_fixtures.py

Fixtures for the test tickers (KO, JPM, GOOGL, TSLA, DUK) are written to `fixtures/` with a `MANIFEST.json`. Development and tests then run in replay mode with no network calls.

Data: U.S. Securities and Exchange Commission, EDGAR (public domain).
