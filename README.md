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
    .venv/bin/python -m engine.cli rankings                      # site_data/rankings.json: criteria ranking from results/scores/ (no model, no network)
    .venv/bin/python -m engine.cli publish --serve               # build site/ and preview it at http://127.0.0.1:8000/ (Finnhub gate, banned phrases and SEC-link checks run first)
    .venv/bin/python -m engine.cli publish                       # build site/ only (git-ignored; publish the folder to any static host)
    .venv/bin/python -m engine.cli deploy --dry-run              # build site/, run every gate and the secret scan over site/ and the whole git history, print what would be pushed
    .venv/bin/python -m engine.cli status                        # writes PROGRESS.md
    .venv/bin/python -m engine.cli schema                        # writes schema/result.schema.json and schema/rankings.schema.json
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

## Deploying the site (GitHub Pages)

The site is static and every URL is relative, so it works as a project site at `https://<your-user>.github.io/stock-evaluation/`. `deploy` publishes only the built `site/` folder to a `gh-pages` branch; the code and the recorded data go to GitHub only when you push `main`. Steps for Daniel, once:

1. On GitHub create a **public** repository named `stock-evaluation` (no README, no licence: the repository already has them).
2. In this folder: `git remote add origin git@github.com:<your-user>/stock-evaluation.git` (or the https address), then `git push -u origin main`.
3. Check first, publish nothing: `.venv/bin/python -m engine.cli deploy --dry-run`. It builds `site/`, runs the Finnhub gate, the banned-phrase scan, the link and schema checks and a **secret scan of the site and of every commit ever made** (Google and Finnhub keys, other token shapes, and the exact values in your `.env`), then prints what it would push.
4. Publish: `.venv/bin/python -m engine.cli deploy`. It refuses if any check or the secret scan fails, or if there is no remote; it never forces a push.
5. In the repository on GitHub: Settings, Pages, Build and deployment, Source "Deploy from a branch", branch `gh-pages`, folder `/ (root)`. The address appears there after a minute.

Repeat steps 3 and 4 after any new run or rankings build (`python -m engine.cli rankings`, then `deploy`). Do not push a build made while `FINNHUB_PUBLIC_OK` is on unless Finnhub's written permission has arrived (ADR-007).

## Data and licences

- **Code:** MIT licence (`LICENSE`), copyright Daniel Bravo.
- **Filings and financial figures:** U.S. Securities and Exchange Commission, EDGAR (public domain). Each figure on the site links to the filing it came from.
- **S&P 500 membership:** the Wikipedia list of S&P 500 companies, as of the snapshot date shown in the site footer, under CC BY-SA 4.0 and attributed there. Company names are shown as Wikipedia lists them, with "(The)" moved to the front.
- **Prices and analyst opinions:** none are published. The valuation tests (G6, G7) show as pending and the analyst ranking is empty until the data provider's written permission for public display exists (ADR-007, ADR-021); the build refuses to publish such fields without it.
- **Model-written text:** the explanations, the four qualitative judgements and the Critic's checks were generated by Gemini 3.1 Flash-Lite (Google, free tier), checked by code and a second model pass, and can be wrong; each links to the filing text it relies on.
- **Typefaces:** Public Sans and Source Serif 4, SIL Open Font License 1.1 (licences in `site_src/assets/fonts/`), served from the site itself.
- Research tool, not financial advice.

