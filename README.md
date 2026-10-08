# Graham & Buffett Equity Research Tool

> **Research and analysis tool. Not financial advice.** It reports which published Graham and Buffett criteria a company meets and why, with sources. It never recommends buying or selling.

Status: early build. See `STATUS.md`, design in `ARCHITECTURE.md`, decisions in `DECISIONS.md`, workflow in `PROCESS.md`.

## Set up and run the tests (offline)

Python 3.10+. The only dependency is Pydantic (pinned in `requirements.txt`).

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m unittest -v

## Fact normaliser coverage report (offline, from the fixtures)

    .venv/bin/python scripts/coverage_report.py     # writes docs/coverage_report.md

## Sections and retrieval report (offline, from the fixtures)

    .venv/bin/python scripts/sections_report.py     # writes docs/sections_report.md

## Scorecard report (offline, from the fixtures)

    .venv/bin/python scripts/score_report.py        # writes docs/scorecard_report.md

## Record EDGAR fixtures (once, needs internet)

    cp .env.example .env      # then set SEC_USER_AGENT
    .venv/bin/python scripts/record_fixtures.py

Fixtures for the test tickers (KO, JPM, GOOGL, TSLA, DUK) are written to `fixtures/` with a `MANIFEST.json`. Development and tests then run in replay mode with no network calls.

Data: U.S. Securities and Exchange Commission, EDGAR (public domain).
