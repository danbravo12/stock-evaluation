# Graham & Buffett Equity Research Tool

> **Research and analysis tool. Not financial advice.** It reports which published Graham and Buffett criteria a company meets and why, with sources. It never recommends buying or selling.

**Live site: https://danbravo12.github.io/stock-evaluation/**

This tool turns SEC filings into a scorecard for each S&P 500 company: eleven tests from Benjamin Graham's defensive-investor criteria and Warren Buffett's published principles, computed as plain arithmetic, plus four questions about the annual report that language-model agents answer by quoting the 10-K. It is different in four ways. Every figure links to the filing it came from. Every judgement quotes the sentences of the 10-K it relies on, and the quote is built by code, not by the model. Every agent run is recorded and can be replayed step by step. And the tool marks its own unreliable judgements: it asks each question three ways, flags verdicts that change with the wording, and marks the questions where that happens often.

## A two-minute tour

1. [**The rankings**](https://danbravo12.github.io/stock-evaluation/index.html): the S&P 500 ranked by how many of the decided tests each company meets, with the data gaps and the companies that cannot be ranked listed instead of hidden.
2. [**A company with the evidence pane open on a judgement**](https://danbravo12.github.io/stock-evaluation/company.html?cik=0000021344#candid_management): Coca-Cola, candid management. The pane shows the verdict, the quoted sentences in the 10-K with a link to the filing, the Critic's checks, the three verdicts it got when the question was reworded, and the Low reliability note.
3. [**Its trace replay**](https://danbravo12.github.io/stock-evaluation/trace.html?cik=0000021344): every step of the run in plain language, from the planner to the Critic, with what each agent was handed and what it returned.
4. [**The evaluation page**](https://danbravo12.github.io/stock-evaluation/evaluation.html): agreement with a human reviewer on a held-out set, where the tool is weak, the Critic's record and how many labels change when each threshold moves.
5. [**How it works**](https://danbravo12.github.io/stock-evaluation/how-it-works.html): the process, the architecture, the cost and what it gets wrong.

## Architecture in brief

![Architecture of the analysis pipeline](site_src/assets/img/architecture.svg)

A rule-based **planner and orchestrator** decides, per company, which tests apply (banks and insurers have no current assets or operating income; utilities use Graham's utility variant) and runs the steps in order, timing and tracing each. The **scorers** (G1 to G7, B1 to B4) are deterministic Python over normalised SEC facts and never call a model. The **qualitative agent** runs one tool loop per question over the latest 10-K (search, read a passage, submit a finding) and cites sentence pointers. The **Explainer** writes one plain line per score with placeholders; code fills in the numbers. The **Critic** re-opens the filing and verifies every quote, checks the lines and scans for advice language, asks a model whether the quotes support each verdict, and sends a failed item back to its author once (a rationale rewrite or a constrained retry); the repair is kept only if it passes the re-check. The **reporter** writes one validated JSON file per company, which the static site only displays. More in [`ARCHITECTURE.md`](ARCHITECTURE.md); every decision is logged in [`DECISIONS.md`](DECISIONS.md).

## Cost

Measured over the 25 analysed companies: about 11 model calls and 28,000 input plus 2,400 output tokens per company, which cost **$0.00** on the Gemini free tier and would cost about **$0.011** at paid rates (Gemini 3.1 Flash-Lite, $0.25 and $1.50 per million input and output tokens). Scoring the whole index needs no model. Over the whole project, including the evaluation and stability runs (1,357 requests): actual spend **$0.00**, notional spend at paid rates about **$1.21**, from the usage ledger.

### With a production budget

A stronger model for the judgement questions and the Critic (and a model from a different provider as a second reader); licensed price and analyst data, which would turn on the two price tests and the analyst ranking; more raters and a larger held-out set, so agreement could be reported with narrow intervals and the rubric reviewed against it; agent analysis of the whole index (about 475 companies remain, about $5 at paid rates or about eleven days of free quota); and a live mode where a visitor can analyse a company on request (ADR-017).

## Evaluation in three lines

- On a held-out set of 24 judgements labelled blind by one person, the tool agrees on 13 and is within one level on 17; it is clearly weaker on durable competitive advantage and candid management.
- Those two questions are the ones the tool marks Low reliability because their verdicts often change with the wording; criteria without the mark agreed on 11 of 12 held-out judgements, marked criteria on 2 of 12.
- The numeric tests are frozen and checked by hand, and moving any threshold by 20% changes few labels except for stable margins, owner earnings and earnings growth. Details and limits: [evaluation page](https://danbravo12.github.io/stock-evaluation/evaluation.html).

## Running it locally

### Set up and run the tests (offline)

Python 3.10+. The only dependency is Pydantic (pinned in `requirements.txt`).

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m unittest -v

### Fact normaliser coverage report (offline, from the fixtures)

    .venv/bin/python scripts/coverage_report.py     # writes docs/coverage_report.md

### Sections and retrieval report (offline, from the fixtures)

    .venv/bin/python scripts/sections_report.py     # writes docs/sections_report.md

### LLM client modes (record / replay)

Tests and development use `replay`: recorded model responses in `fixtures/llm/`, no network, no key needed. To record new ones (free tier, needs `GEMINI_API_KEY` in `.env`; the model profile comes from `config/models.json`, `LLM_PROFILE` in `.env`):

    .venv/bin/python scripts/llm_smoke.py record    # ~4 requests: model id, JSON mode, tool calling
    .venv/bin/python scripts/llm_smoke.py replay    # same calls offline, zero network

Usage and spend are counted in `data/ledger/usage.json` (daily quota resets at midnight Pacific). Paid calls stay off unless `PAID_MODE_ENABLED=true` (ADR-039).

### Qualitative agent report

    .venv/bin/python scripts/qualitative_report.py replay   # offline, writes docs/qualitative_report.md (research output, not financial advice)
    .venv/bin/python scripts/qualitative_report.py record   # free tier only: re-records the ~35 requests (needed after any prompt or rubric change)

### Run the engine (ADR-056)

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

### Explainer + Critic report and the qualitative gold set

    .venv/bin/python scripts/review_report.py replay    # offline, writes docs/critic_report.md (research output, not financial advice)
    .venv/bin/python -m eval.qualitative_agreement      # agent (agent-only replay) vs the human-reviewed gold set
    .venv/bin/python -m eval.agreement                  # final verdicts vs the human labels, dev and held-out sets separately (exact, within one level, kappa)

### Scorecard report (offline, from the fixtures)

    .venv/bin/python scripts/score_report.py        # writes docs/scorecard_report.md

### Record EDGAR fixtures (once, needs internet)

    cp .env.example .env      # then set SEC_USER_AGENT
    .venv/bin/python scripts/record_fixtures.py

Fixtures for the test tickers (KO, JPM, GOOGL, TSLA, DUK) are written to `fixtures/` with a `MANIFEST.json`. Development and tests then run in replay mode with no network calls.

Data: U.S. Securities and Exchange Commission, EDGAR (public domain).

### The showcase

`config/showcase.json` lists the companies with a full agent analysis beyond the five test companies, with a one-line reason each (the rankings page shows them): the top of the ranking (AMAT, FAST, COST), large familiar companies (MSFT, AAPL, NVDA, META, JNJ, PG, MCD, CAT) and the cases the rules handle (XOM predecessor registrant, BRK-B conglomerate, UNH managed care, MET insurer, GS broker-dealer as bank, PLD and O REITs, NEE utility variant, VST power producer). To add one: add it to the file, run `python -m engine.cli batch --tickers <SYMBOL> --mode live` (free tier; resumes after midnight Pacific if the daily limit is reached; never enable paid mode for this), `python -m engine.cli rankings`, add `!results/<CIK>.*` to `.gitignore`, then `publish`.

### Deploying the site (GitHub Pages)

The site is static and every URL is relative, so it works as a project site at `https://<your-user>.github.io/stock-evaluation/`. `deploy` publishes only the built `site/` folder to a `gh-pages` branch; the code and the recorded data go to GitHub only when you push `main`. Steps, once:

1. On GitHub create a **public** repository named `stock-evaluation` (no README, no licence: the repository already has them).
2. In this folder: `git remote add origin git@github.com:<your-user>/stock-evaluation.git` (or the https address), then `git push -u origin main`.
3. Check first, publish nothing: `.venv/bin/python -m engine.cli deploy --dry-run`. It builds `site/`, runs the Finnhub gate, the banned-phrase scan, the link and schema checks and a **secret scan of the site and of every commit ever made** (Google and Finnhub keys, other token shapes, and the exact values in your `.env`), then prints what it would push.
4. Publish: `.venv/bin/python -m engine.cli deploy`. It refuses if any check or the secret scan fails, or if there is no remote; it never forces a push.
5. In the repository on GitHub: Settings, Pages, Build and deployment, Source "Deploy from a branch", branch `gh-pages`, folder `/ (root)`. The address appears there after a minute.

Repeat steps 3 and 4 after any new run or rankings build (`python -m engine.cli rankings`, then `deploy`). Do not push a build made while `FINNHUB_PUBLIC_OK` is on unless Finnhub's written permission has arrived (ADR-007).

## Project documents

- [`DECISIONS.md`](DECISIONS.md): every design decision, with context, alternatives and trade-offs.
- [`PROCESS.md`](PROCESS.md): the research workflow the tool automates and the criteria tables.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): system view, agent hand-offs, components and run economics.
- [`docs/evaluation_notes.md`](docs/evaluation_notes.md): what the tool gets wrong, with counts.
- [`STATUS.md`](STATUS.md), [`FILEMAP.md`](FILEMAP.md): where the project stands and what every file is for.

## Data and licences

- **Code:** MIT licence (`LICENSE`), copyright Daniel Bravo.
- **Filings and financial figures:** U.S. Securities and Exchange Commission, EDGAR (public domain). Each figure on the site links to the filing it came from.
- **S&P 500 membership:** the Wikipedia list of S&P 500 companies, as of the snapshot date shown in the site footer, under CC BY-SA 4.0 and attributed there. Company names are shown as Wikipedia lists them, with "(The)" moved to the front.
- **Prices and analyst opinions:** none are published. The valuation tests (G6, G7) show as pending and the analyst ranking is empty until the data provider's written permission for public display exists (ADR-007, ADR-021); the build refuses to publish such fields without it.
- **Model-written text:** the explanations, the four qualitative judgements and the Critic's checks were generated by Gemini 3.1 Flash-Lite (Google, free tier), checked by code and a second model pass, and can be wrong; each links to the filing text it relies on.
- **Typefaces:** Public Sans and Source Serif 4, SIL Open Font License 1.1 (licences in `site_src/assets/fonts/`), served from the site itself.
- Research tool, not financial advice.

