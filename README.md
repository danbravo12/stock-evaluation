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

## LLM client modes (record / replay)

Tests and development use `replay`: recorded model responses in `fixtures/llm/`, no network, no key needed. To record new ones (free tier, needs `GEMINI_API_KEY` in `.env`; the model profile comes from `config/models.json`, `LLM_PROFILE` in `.env`):

    .venv/bin/python scripts/llm_smoke.py record    # ~4 requests: model id, JSON mode, tool calling
    .venv/bin/python scripts/llm_smoke.py replay    # same calls offline, zero network

Usage and spend are counted in `data/ledger/usage.json` (daily quota resets at midnight Pacific). Paid calls stay off unless `PAID_MODE_ENABLED=true` (ADR-039).

## Qualitative agent report

    .venv/bin/python scripts/qualitative_report.py replay   # offline, writes docs/qualitative_report.md (research output, not financial advice)
    .venv/bin/python scripts/qualitative_report.py record   # free tier only: re-records the ~35 requests (needed after any prompt or rubric change)

## Run the engine (ADR-056)

    .venv/bin/python -m engine.cli analyse KO                    # one company, offline (replay), writes results/0000021344.json and its trace
    .venv/bin/python -m engine.cli analyse MET --mode live       # live: SEC + Gemini free tier (needs SEC_USER_AGENT and GEMINI_API_KEY in .env)
    .venv/bin/python -m engine.cli batch --universe --limit 40   # resumable; stops cleanly at the daily quota, run it again after midnight Pacific
    .venv/bin/python -m engine.cli batch --universe --numeric-only   # all 500 companies, scores only: live SEC data into the cache, no model, no 10-K (about 5 minutes the first time)
    .venv/bin/python scripts/universe_scorecard_report.py        # docs/universe_scorecard_report.md from results/scores/
    .venv/bin/python -m eval.universe_counts                     # compare with the frozen label counts
    .venv/bin/python -m engine.cli status                        # writes PROGRESS.md
    .venv/bin/python -m engine.cli schema                        # writes schema/result.schema.json
    .venv/bin/python scripts/snapshot_universe.py                # S&P 500 snapshot (once, a quarter)

## Explainer + Critic report and the qualitative gold set

    .venv/bin/python scripts/review_report.py replay    # offline, writes docs/critic_report.md (research output, not financial advice)
    .venv/bin/python -m eval.qualitative_agreement      # agent vs the human-reviewed gold set (19/20)

## Scorecard report (offline, from the fixtures)

    .venv/bin/python scripts/score_report.py        # writes docs/scorecard_report.md

## Record EDGAR fixtures (once, needs internet)

    cp .env.example .env      # then set SEC_USER_AGENT
    .venv/bin/python scripts/record_fixtures.py

Fixtures for the test tickers (KO, JPM, GOOGL, TSLA, DUK) are written to `fixtures/` with a `MANIFEST.json`. Development and tests then run in replay mode with no network calls.

Data: U.S. Securities and Exchange Commission, EDGAR (public domain).
