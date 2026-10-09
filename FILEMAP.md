# File Map

What every file in this repo is for, and where planned files will go.
Updated 2026-10-09 · after the qualitative agent v1.1 commit. **Rule:** update this file in the same commit as any file you add, move or delete.

Status: **Built** = exists and tested · **Planned** = designed in `ARCHITECTURE.md`, not yet created.

## At a glance

```
StockEvaluation/
├── README.md, STATUS.md, DECISIONS.md, PROCESS.md, ARCHITECTURE.md, FILEMAP.md   ← project docs
├── .env.example, .gitignore                                                      ← config hygiene
├── .env                                         (local only, git-ignored)        ← your secrets
├── config/  test_tickers.json, concept_map.json, sector_rules.json, search_terms.json, models.json                                 ← test companies; XBRL concept priorities
├── requirements.txt, .venv/ (local only)                                         ← pinned dependency (Pydantic)
├── docs/  coverage_report.md, scorecard_report.md, sections_report.md, qualitative_report.md, evaluation_notes.md                                                       ← normaliser evidence
├── engine/                                                                       ← the Python library (all logic)
│   ├── settings.py, universe.py, contracts.py, normalise.py, splits.py, score/, filing_text.py, sections.py, retrieve.py, trace.py, llm/, agents/
│   └── fetch/  store.py, edgar.py
├── scripts/  record_fixtures.py, coverage_report.py                                                 ← one-off commands
├── tests/  test_edgar.py, test_normalise*.py                                                        ← offline tests
├── fixtures/                                                                     ← recorded SEC data (committed)
│   ├── MANIFEST.json
│   └── edgar/<CIK>/…
└── data/cache/                                  (local only, git-ignored)        ← live HTTP cache
```

## Project docs

| File | Function | Status |
|---|---|---|
| `README.md` | Front door for a stranger: what the tool is, the not-financial-advice disclaimer, how to run tests and record fixtures. Will grow into the full README for v1. | Built (stub) |
| `STATUS.md` | Where the project is: done, waiting on, next steps, notes for the next build step, milestone summaries. | Built |
| `DECISIONS.md` | ADR log: every key decision with context, decision and trade-off (ADR-001 to ADR-047). | Built |
| `PROCESS.md` | The research workflow being automated: inputs, steps, decision points, criteria tables (G1–G7, B1–B4, four qualitative Buffett criteria), failure handling. | Built |
| `ARCHITECTURE.md` | System view, agent hand-off sequence, component catalogue, run economics. | Built |
| `FILEMAP.md` | This file. | Built |

## Configuration and secrets

| File | Function | Status |
|---|---|---|
| `.env.example` | Template listing every setting the tool reads from the environment (`SEC_USER_AGENT`, `FINNHUB_API_KEY`, `GEMINI_API_KEY`), with empty values. Safe to commit. | Built |
| `.env` | Your real values. Read by `engine/settings.py`. **Never committed** (git-ignored, checked with `git check-ignore`). | Local only |
| `requirements.txt` | Exact pinned dependency list (Pydantic 2.13.5, ADR-029). Install with `pip install -r requirements.txt` in `.venv`. | Built |
| `.gitignore` | Keeps `.env`, `data/cache/`, Python caches and `.DS_Store` out of git. | Built |
| `config/concept_map.json` | Per measure: unit, period type, ordered XBRL concepts (with explicit derived sums) and a short reason. Read by the normaliser; reviewable without reading code (ADR-028). | Built |
| `config/sector_rules.json` | SIC code ranges → bank / insurer / utility / other, with a reason per rule; will be confirmed by GICS later (ADR-033). | Built |
| `config/models.json` | Model profiles (base URL, model id, key variable, prices, free-tier limits, source note) and the budget caps (ADR-039, ADR-040). | Built |
| `config/search_terms.json` | Per qualitative Buffett criterion: items to search first, starting queries and why (ADR-037), plus the rubric: `question`, `found_means`, `weak_means`, `insufficient_means` (ADR-043). | Built |
| `config/test_tickers.json` | The five test companies (KO, JPM, GOOGL, TSLA, DUK). Used by the record script now and the evaluation harness later. Rationale per ticker: ADR-024. | Built |

## Engine (`engine/`)

The engine is a library, so the batch command, the tests and the future live app (ADR-017) all call the same code.

| File | Function | Status |
|---|---|---|
| `engine/__init__.py` | Marks `engine` as a Python package. | Built |
| `engine/settings.py` | Loads `.env` (small built-in loader, no dependency) and exposes a `Settings` object: SEC User-Agent, fixtures and cache folders, request interval. | Built |
| `engine/universe.py` | `normalise_ticker()`, the single place tickers are standardised (`brk.b` → `BRK-B`), and `cik10()`, which zero-pads CIKs for EDGAR URLs (ADR-014). Will also hold the S&P 500 snapshot loader and validator. | Built (partial) |
| `engine/contracts.py` | Pydantic models: `AnnualValue`, `Gap`, `AnnualSeries`, `NormalisedFacts`, the scorers' `InputRef`, `CriterionResult`, `Summary`, `ScoreSet`, the filing and LLM models (`Passage`, `SearchHit`, `LLMCall`, `TraceEvent`) and the qualitative agent's `Citation`, `SearchRecord`, `QualFinding` (four verdicts incl. "not assessed"), `QualTotals`, `QualFindings` (ADR-020's contracts so far). | Built |
| `engine/normalise.py` | Fact normaliser: company facts → one annual series per measure, with concept, accession and URL on every value, restatement flags, explicit derived values and gaps with reasons (ADR-026 to ADR-028). | Built |
| `engine/splits.py` | Stock-split adjustment: reads the company's split-ratio facts, keeps those confirmed by restated values, rescales EPS, dividends per share and share counts to today's basis, records `split_factor` (ADR-032). | Built |
| `engine/score/common.py` | Fiscal-year keys, windows, sector class, result builders (ADR-031, ADR-033). | Built |
| `engine/score/graham.py` | G1–G7, pure functions. | Built |
| `engine/score/buffett.py` | B1–B4, pure functions. | Built |
| `engine/score/__init__.py` | `score_company`, `summarise`, and `score_ticker` (normalise → split-adjust → score through an EdgarClient). | Built |
| `engine/filing_text.py` | 10-K HTML → normalised plain text; the citation text all offsets and quotes refer to (ADR-035). | Built |
| `engine/sections.py` | Finds Items 1, 1A and 7 (longest candidate, title fallback, explicit not_found) and cuts them into passages with exact offsets (ADR-036, ADR-037). | Built |
| `engine/retrieve.py` | `Retriever`: builds a per-company index (text cache by document hash) with pure-Python BM25; the agent's tools `search`, `search_many` and `get_passage` (ADR-037). | Built |
| `engine/llm/client.py` | `LLMClient`: OpenAI-compatible chat over `urllib` with replay / live / record modes (and `use_store=False` for variability runs), retries, `complete_json` (one repair), tool calls, `list_models` (ADR-038, ADR-040). | Built |
| `engine/llm/budget.py` | Run ledger (`data/ledger/usage.json`) and budget guard: RPM pacing, Pacific-day quota with safety margin, paid-mode switch and caps (ADR-039). | Built |
| `engine/llm/cost.py` | Notional and actual cost from usage and profile prices; cost projection before a call. | Built |
| `engine/trace.py` | `TraceRecorder`: one JSONL event per LLM call, tool call or note (ADR-020). | Built |
| `engine/sentences.py` | Deterministic sentence segmentation with exact document offsets (newlines, bullets, sentence ends, abbreviations, long-sentence cuts); stored on every `Passage` (ADR-046). | Built |
| `engine/agents/__init__.py` | Package for the LLM agents. | Built |
| `engine/agents/qualitative.py` | The Buffett qualitative agent: `assess_qualitative(cik, ticker, retriever, llm, trace)` runs one tool loop per criterion (seeded search, `search` / `get_passage` / `submit_finding`, 4-turn cap). Passages are shown as numbered sentences and cited by pointer; code builds the quote and exact offsets; "not assessed" is assigned from the stop reason (ADR-041 to ADR-047). | Built |
| `engine/fetch/__init__.py` | Marks `fetch` as a package. | Built |
| `engine/fetch/store.py` | `ResponseStore`: saves each raw response as gzip plus a `.meta.json` (URL, fetch time, SHA-256, size) and verifies the checksum on read. Backs both the cache and the fixtures (ADR-025). | Built |
| `engine/fetch/edgar.py` | `EdgarClient`: the data fetcher's EDGAR tools. `company_tickers`, `lookup_cik`, `submissions`, `companyfacts`, `latest_filing` (skips 10-K/A), `filing_document`. Three modes: replay (fixtures only, no network), live (cache, fetch on miss), record (fetch and write fixtures). Declared User-Agent, ~6 requests/s, retries with `Retry-After`. | Built |

## Scripts (`scripts/`)

| File | Function | Status |
|---|---|---|
| `scripts/record_fixtures.py` | One-off: records SEC data for the test tickers and writes `fixtures/MANIFEST.json`. Needs internet and `SEC_USER_AGENT`. Last run 2026-10-08, 26 requests. | Built |
| `scripts/llm_smoke.py` | Smoke test of the LLM client: model id check, JSON mode, tool calling with a round trip. `record` (live, ~4 free requests) or `replay` (offline). | Built |
| `scripts/sections_report.py` | Extracts sections from the 5 fixtures and writes `docs/sections_report.md` (status, opening text, top passages per criterion). | Built |
| `scripts/qualitative_report.py` | Runs the qualitative agent on the 5 test tickers and writes `docs/qualitative_report.md`. `record` (live, free tier only, refuses in paid mode) or `replay` (offline, identical report); optional ticker arguments. Also writes the trace and the list of fixture hashes used (git-ignored, under `data/cache/trace/`). | Built |
| `scripts/qualitative_variability.py` | Runs the 5 tickers N extra times live with the response store bypassed (`use_store=False`), compares with the recorded run and writes `docs/qualitative_variability.md`. Free tier only; stops if today's ledger count would pass 400. | Built |
| `scripts/score_report.py` | Scores the 5 fixtures (replay) and writes `docs/scorecard_report.md`. | Built |
| `scripts/coverage_report.py` | Runs the normaliser on the 5 fixtures (replay) and writes `docs/coverage_report.md`. | Built |

## Docs output (`docs/`)

| File | Function | Status |
|---|---|---|
| `docs/scorecard_report.md` | Summary table and, per company, every criterion's result, figures, threshold, years, flags and source filings. | Built |
| `docs/sections_report.md` | Per company and item: status, method, length, opening text; then the top 3 passages per qualitative criterion. Preview of what the agent sees. | Built |
| `docs/qualitative_report.md` | Per company and criterion: verdict, rationale, quoted text with accession, item, passage and offsets, searches made, stop reason, calls, tokens and notional cost; summary table and calls and tokens per company. Verdicts are not frozen: they are reviewed by hand. | Built |
| `docs/qualitative_variability.md` | Per company and criterion: verdicts of the recorded run and two live repeat runs, agreement, whether the cited passage changed; overall "identical in X of 20"; calls and tokens per run. Live result, not replayable. | Built |
| `docs/evaluation_notes.md` | Known weaknesses of the tool, one short item each (what, why, impact, planned handling). Start of the evaluation write-up. | Built |
| `docs/coverage_report.md` | Measure × company matrix of years covered, concepts used, restatements, gaps and notes. Evaluation evidence for the README. | Built |

## Tests (`tests/`)

| File | Function | Status |
|---|---|---|
| `tests/__init__.py` | Marks `tests` as a package so `python3 -m unittest` finds the tests. | Built |
| `tests/synthetic.py` | Builders for small synthetic `NormalisedFacts`, shared by the scorer and split tests. | Built |
| `tests/test_score.py` | Synthetic-series tests per criterion: edges, labels, sector exceptions, never-assume-zero, G5 negative base, B4 missing years, G6/G7 with a price. | Built |
| `tests/test_splits.py` | Split adjustment on synthetic cases and the GOOGL, TSLA, KO and DUK fixtures. | Built |
| `tests/test_llm.py` | 34 offline tests with a fake transport and injected clock: request hashing, record/replay, cost maths, pacing, Pacific-midnight reset, quota and caps, 429/400/5xx handling, JSON repair, tool calls, trace, key-secrecy scans. | Built |
| `tests/test_expected_qualitative.py` | Guard: replayed agent verdicts equal the recorded ones; agreement 17/20 with every disagreement over-generous. | Built |
| `tests/test_sentences.py` | Segmentation rules on synthetic text (bullets, newlines, abbreviations, decimals, long-sentence cuts, nothing lost) and exact round trip of every passage of the 5 recorded filings. | Built |
| `tests/test_qualitative.py` | 29 offline tests of the agent with scripted model replies through the real client (fake transport) on a synthetic 10-K: seeded search, search / get_passage / submit, unchanged assistant messages and tool-call ids, turn cap and last-turn tools, pointer citations (exact quote from sentence numbers, out-of-range, last before first, over 3 sentences, over 120 words, never-retrieved passage, one correction then `invalid_citation`, one extra turn), verdict per stop reason, malformed arguments, section_missing, quota and budget propagation, totals and trace order. | Built |
| `tests/test_qualitative_fixtures.py` | Replay of all 5 real runs with zero network: four findings each, every cited span equals `document_text[start:end]` and its sentence offsets, no mechanical citation failures, no advice words, totals add up. Structural only; verdicts not frozen. | Built |
| `tests/test_sections.py` | Synthetic-filing tests: HTML normalisation, TOC not chosen, combined headings, title fallback and stub handling, not_found reasons, passage offsets and determinism, BM25, the Retriever and its text cache. | Built |
| `tests/test_sections_fixtures.py` | Real 10-Ks (replay): every item found or explained, sections not opening on the TOC, offsets round-trip, DUK's 16 MB filing under 10 s. | Built |
| `tests/test_expected_scores.py` | Guard: fails if any label or key figure differs from `eval/expected_scores.json`. | Built |
| `tests/test_score_fixtures.py` | Certain facts about the 5 real companies' scores (replay). | Built |
| `tests/test_normalise.py` | 13 synthetic-data tests: annual vs quarterly, instants, 52/53-week years, `fy`/`fp` ignored, restatement, per-year fallback, notes, derived sums, gaps, unit mismatch, model validation. | Built |
| `tests/test_normalise_fixtures.py` | Real-fixture checks (replay): ≥10 years of core measures, TSLA losses, JPM bank gaps, provenance on every value. | Built |
| `tests/test_edgar.py` | 18 offline tests with a fake transport: modes, User-Agent rules, retries (incl. `Retry-After` and connection errors), throttle, 403/404 handling, checksum tampering, 10-K selection, provenance surviving record → replay. | Built |

## Recorded model responses (`fixtures/llm/`)

Committed, so LLM-using tests replay offline. The three smoke-test calls (JSON mode, tool request, answer after the tool result) and the 35 requests the qualitative report replays (5 companies, 4 criteria), gzip + `.meta.json` like the SEC fixtures; each file holds the request, the provider's response and the original latency, never the API key.

## Evaluation (`eval/`)

| File | Function | Status |
|---|---|---|
| `eval/snapshot.py` | Reduces a `ScoreSet` to label + key figures (4 significant digits); `python -m eval.snapshot` rewrites the frozen file after a reviewed change. | Built |
| `eval/expected_qualitative.json` | Gold set for the qualitative agent: per ticker and criterion the recorded agent verdict, the human-reviewed verdict and a note (reviewer line inside). 3 of 20 labels differ, all over-generous. | Built |
| `eval/qualitative_agreement.py` | Replays the recorded agent run and prints agreement with the gold set (17/20) and the disagreements; `agreement()` is reused by the Critic evaluation. | Built |
| `eval/expected_scores.json` | Frozen, reviewed results for the 5 test companies and 11 criteria. | Built |

## Recorded data (`fixtures/`)

Committed, so tests and development run offline and give the same answer every time. Snapshot as of 2026-10-08; ~4.4 MB on disk.

| Path | Function |
|---|---|
| `fixtures/MANIFEST.json` | Index of the recording: when, source attribution (SEC EDGAR, public domain), and per company the CIK, name, sector description, fiscal year end, XBRL concept count and latest 10-K (accession, dates, URL, SHA-256). |
| `fixtures/edgar/company_tickers.json.*` | SEC's ticker → CIK file, used to resolve tickers and validate the S&P 500 list. |
| `fixtures/edgar/<CIK>/submissions.json.*` | The company's filing history; used to find the latest 10-K. |
| `fixtures/edgar/<CIK>/companyfacts.json.*` | All XBRL-tagged financial figures since ~2009; the raw input to every numeric criterion. |
| `fixtures/edgar/<CIK>/10-K/<accession>/<doc>.htm.*` | The latest 10-K document; the raw input for the qualitative agent (Items 1, 1A, 7). |

Every item is a pair: `*.gz` (the body) and `*.meta.json` (where and when it came from, plus a checksum).

| CIK | Company | Latest 10-K |
|---|---|---|
| `0000021344` | Coca-Cola (KO) | `ko-20251231.htm` |
| `0000019617` | JPMorgan Chase (JPM) | `jpm-20251231.htm` |
| `0001652044` | Alphabet (GOOGL) | `goog-20251231.htm` |
| `0001318605` | Tesla (TSLA) | `tsla-20251231.htm` |
| `0001326160` | Duke Energy (DUK) | `duk-20251231.htm` |

## Local only, not in git

| Path | Function |
|---|---|
| `.env` | Secrets and personal details (see above). |
| `data/ledger/usage.json` | Run ledger: requests per Pacific day, spend, notional spend (ADR-039). |
| `data/cache/` | HTTP cache used by live runs, `llm/` (live model responses), `trace/`, and `sections/` (normalised 10-K text keyed by document hash). Safe to delete; it refills. |

## Planned (not yet created)

Names are proposals and may change when built. Each follows a component in `ARCHITECTURE.md` §3.

| Planned path | Function | Decision |
|---|---|---|
| `data/constituents/sp500_<date>.csv` | Dated Wikipedia snapshot of the S&P 500 with CIK and sector. | ADR-014 |
| `engine/contracts.py` (rest) | Remaining hand-off objects (`RunPlan`, `DataBundle`, `Explanations`, `CriticReport`, `Result`) join the normaliser's models. | ADR-020 |
| `engine/fetch/finnhub.py` | Price and analyst counts, through the same store. | ADR-007 |
| `engine/agents/` (rest) | Explainer and Critic (the qualitative agent is built). | ADR-005, ADR-010, ADR-018, ADR-019 |
| `engine/orchestrator.py` | Planner and run driver; writes the trace. | ADR-018 |
| `engine/report.py` | Builds the versioned results JSON. | ADR-020 |
| `scripts/run.py` (`run · rank · eval · status · publish`) | Batch command line. | ADR-016, ADR-021, ADR-023 |
| `results/`, `PROGRESS.md` | One JSON per company, `rankings.json`, run ledger output. | ADR-016, ADR-023 |
| `eval/` (rest) | Rest of the evaluation harness: ±20% threshold sensitivity, model comparison, failure cases. | ADR-011, ADR-015 |
| `site/` | Static website for GitHub Pages. | ADR-016 |
