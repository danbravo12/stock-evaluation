# File Map

What every file in this repo is for, and where planned files will go.
Updated 2026-10-12 · after build 4a (evaluation harness, stability runs). **Rule:** update this file in the same commit as any file you add, move or delete.

Status: **Built** = exists and tested · **Planned** = designed in `ARCHITECTURE.md`, not yet created.

## At a glance

```
StockEvaluation/
├── README.md, STATUS.md, PROGRESS.md, DECISIONS.md, PROCESS.md, ARCHITECTURE.md, FILEMAP.md   ← project docs
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
| `README.md` | Front door for a first-time reader: what the tool is, the not-financial-advice disclaimer, how to run tests and record fixtures. Will grow into the full README for v1. | Built (stub) |
| `STATUS.md` | Where the project is: done, waiting on, next steps, notes for the next build step, milestone summaries. | Built |
| `DECISIONS.md` | ADR log: every key decision with context, decision and trade-off (ADR-001 to ADR-068). | Built |
| `PROCESS.md` | The research workflow being automated: inputs, steps, decision points, criteria tables (G1–G7, B1–B4, four qualitative Buffett criteria), failure handling. | Built |
| `ARCHITECTURE.md` | System view, agent hand-off sequence, component catalogue, run economics. | Built |
| `FILEMAP.md` | This file. | Built |

## Configuration and secrets

| File | Function | Status |
|---|---|---|
| `.env.example` | Template listing every setting the tool reads from the environment (`SEC_USER_AGENT`, `FINNHUB_API_KEY`, `GEMINI_API_KEY`), with empty values. Safe to commit. | Built |
| `.env` | Your real values. Read by `engine/settings.py`. **Never committed** (git-ignored, checked with `git check-ignore`). | Local only |
| `requirements.txt` | Exact pinned dependency list (Pydantic 2.13.5, ADR-029). Install with `pip install -r requirements.txt` in `.venv`. | Built |
| `LICENSE` | MIT, copyright Daniel Bravo. | Built |
| `config/showcase.json` | The 20 showcase companies with a group, a one-line reason each, and the five test companies' reasons; resolved against the rankings by `publish` (ADR-070). | Built |
| `config/site.json` | The one place the repository address is set; `publish` writes it into every page and the manifest. | Built |
| `config/secret_scan_allow.json` | Regexes the secret scan ignores (empty; each entry needs a stated reason). | Built |
| `.gitignore` | Keeps `.env`, `data/cache/`, Python caches and `.DS_Store` out of git. | Built |
| `config/concept_map.json` | Per measure: unit, period type, ordered XBRL concepts (with explicit derived sums) and a short reason. Read by the normaliser; reviewable without reading code (ADR-028). | Built |
| `config/sector_rules.json` | Sector class by GICS sub-industry with per-CIK overrides, each with a reason and an optional `note` that travels with the results; SIC ranges only for tickers outside the snapshot (ADR-057, amended 2026-10-11). | Built |
| `config/registrant_successors.json` | Successor CIK → predecessor CIK(s) with the evidence filing (form, accession, URL, quote), reason and the visible note; Exxon (ADR-063). | Built |
| `config/models.json` | Model profiles (base URL, model id, key variable, prices, free-tier limits, source note) and the budget caps (ADR-039, ADR-040). | Built |
| `config/prompt_versions.json` | Active prompt version per agent: qualitative v2.1, Explainer v2, Critic v2.1 (latest-fiscal-year rule, word counts in the cap error; ADR-069 amendment). | Built |
| `config/universe_primary.json` | Primary symbol of each dual share class (GOOGL, FOXA, NWSA): one analysis per CIK (ADR-053). | Built |
| `config/figure_formats.json` | Figure key → display format for the Explainer's placeholders (usd_billions, usd_millions, ratio_2dp, percent_1dp, count, per_share_usd, years); a test checks every key the scorers produce (ADR-048). | Built |
| `config/banned_phrases.json` | Advice and valuation phrases the Critic's R3 forbids (regex, reason each) and an allowlist for ordinary vocabulary such as "share buyback" (ADR-049). | Built |
| `config/search_terms.json` | Per qualitative Buffett criterion: items to search first, starting queries and why (ADR-037), plus the rubric: `question`, `found_means`, `weak_means`, `insufficient_means` (ADR-043). | Built |
| `config/reliability.json` | The flip-rate threshold (30%) at or above which a qualitative criterion is marked low reliability (ADR-072 amendment). | Built |
| `config/qualitative_paraphrases.json` | Two paraphrases (A, B) of each qualitative criterion's question and three verdict definitions, meaning unchanged, for the stability runs (ADR-072). | Built |
| `config/label_packet.json` | The packet's generic queries and passages per criterion (ADR-071). | Built |
| `config/test_tickers.json` | The five test companies (KO, JPM, GOOGL, TSLA, DUK). Used by the record script now and the evaluation harness later. Rationale per ticker: ADR-024. | Built |

## Engine (`engine/`)

The engine is a library, so the batch command, the tests and the future live app (ADR-017) all call the same code.

| File | Function | Status |
|---|---|---|
| `engine/__init__.py` | Marks `engine` as a Python package. | Built |
| `engine/settings.py` | Loads `.env` (small built-in loader, no dependency) and exposes a `Settings` object: SEC User-Agent, fixtures and cache folders, request interval. | Built |
| `engine/universe.py` | `normalise_ticker()` and `cik10()`, plus the S&P 500 snapshot: HTML table parser, CSV writer and loader, `validate_universe` (row count, duplicates, CIKs against SEC's ticker file, dual-class primary rule), `Universe` with one row per CIK (ADR-014, ADR-053). | Built |
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
| `engine/agents/explainer.py` | The Explainer: `explain(scoreset, llm, trace, only=, feedback=)` makes one call per company for pass/fail/partial/not-meaningful criteria, with `{placeholders}` rendered by code from `figures` (`render`, `format_value`); templated lines for n/a and data gaps (ADR-048). | Built |
| `engine/agents/critic.py` | The Critic's checks: pure functions `check_explanation` (R1), `check_citations` (R2, independent of the agent's checker), `banned_hits` (R3), `llm_review` (L1: findings and explanation meaning in one call), and the `Critic` class that runs them against the re-loaded 10-K (ADR-049). | Built |
| `engine/agents/repair.py` | `rewrite_rationale`: the cheap repair for a finding whose verdict stands but whose rationale says more than its quotes; one call, sees only the question, verdict, quotes and problems (ADR-052). | Built |
| `engine/agents/review.py` | `explain_and_verify(scoreset, qual, ...)`: Explainer, Critic, one repair per failed item by the path that fits (explanation retry, rationale rewrite, constrained retry), re-check; a failed repair keeps the original with a warning; returns `ReviewResult` (explanations, qualitative findings, `CriticReport`). No orchestrator yet. | Built |
| `engine/prompts.py` | `active(agent)`, `at_least(agent, version)`: which prompt version an agent uses, from `config/prompt_versions.json`; `year_rule_text` fills the fiscal-year end date into a criterion's year rule. | Built |
| `engine/planner.py` | `plan_for(ticker, universe, sic)`: scope check, sector class, which criteria apply or are not applicable (ADR-013), planned gaps (price), steps; out-of-scope tickers get a plan only (ADR-018). | Built |
| `engine/orchestrator.py` | `analyse(ticker, mode=...)`: plan → fetch → score → qualitative → explain and verify → report for one company; timed and traced; failing steps degrade, dependants skip with a reason; quota, budget and missing-fixture errors propagate (ADR-055). | Built |
| `engine/report.py` | `Result` (schema 1.0) and its parts, `write_result` (round-trip validation, Finnhub publish gate, `results/<CIK>.json`), `export_schema`, `cost_from_trace` (ADR-054). | Built |
| `engine/numeric.py` | `score_numeric(symbol, edgar=, universe=)`: fetch, normalise, split-adjust, classify and score one company with no 10-K and no model, plus `diagnose` (gaps, notes, split factors, restatements, plausibility flags) and `write_numeric` (ADR-059). | Built |
| `engine/batch.py` | `CompanyLedger` (`data/ledger/companies.json`), `run_batch` (resumable, stops cleanly on quota or cap), `run_numeric_batch` (numeric-only; own ledger `numeric.json`; a crash is a failed row), `progress_markdown` (ADR-056, ADR-059). | Built |
| `engine/cli.py` | `python -m engine.cli analyse | batch | rankings | status | schema`. | Built |
| `engine/successors.py` | Registrant successors and companies without a 10-K: `load_successors`, `has_annual_report`, `NoAnnualReport`, the message "No annual report (10-K) filed yet; listed since <date>." (ADR-063). | Built |
| `engine/deploy.py` | `deploy`: build, every gate, secret scan, then the `gh-pages` push through a git worktree; `--dry-run` prints what would be pushed; refuses without a remote or on any finding (ADR-068). | Built |
| `engine/secrets_scan.py` | Secret scan over files and over every blob and commit message of the git history (gzip unpacked), key shapes plus the exact values of `.env`, redacted findings (ADR-068). | Built |
| `engine/evaluation.py` | `evaluation_data(stability_rows)`: the data behind the evaluation page, read from the frozen files in `eval/` and the results; Wilson interval, threshold display strings (ADR-073). | Built |
| `engine/score/thresholds.py` | The twelve numeric thresholds in one frozen dataclass with `override` (a context manager) and `scaled`; the scorers read them from here so the sensitivity test can move them (ADR-074). | Built |
| `engine/stability.py` | Paraphrases and `variant_criteria`, `classify` (stable / borderline), `attach` (writes `stability` onto the main results), `collect`, `flip_stats`, `pair_flips`, `dev_correlation` with a Fisher exact test (ADR-072). | Built |
| `engine/trace_render.py` | `render_trace` (events → numbered plain-language steps, groups, hand-offs, running totals) and `critic_notes` (the Critic's checks, the agent's work and the cost as sentences), `plural`, `money` (ADR-067). | Built |
| `engine/publish.py` | `build_site`: builds the git-ignored `site/` from `site_src/`, `site_data/` and `results/` (reduced score files, results, traces as arrays, cited passages, documents, manifest); Finnhub gate, banned phrases and SEC-link checks fail the build; `serve` (ADR-065). | Built |
| `engine/rankings.py` | Rankings builder: `build_rankings(universe, scores_dir, results_dir)` → `Rankings` (criteria ranking with the decided ≥ 6 threshold and exact tie-breaks, insufficient-data group, empty analyst section, excluded companies), `write_rankings` (round-trip validation and the Finnhub gate), `export_rankings_schema` (ADR-062). | Built |
| `engine/agents/__init__.py` | Package for the LLM agents. | Built |
| `engine/agents/qualitative.py` | The Buffett qualitative agent: `assess_qualitative(cik, ticker, retriever, llm, trace)` runs one tool loop per criterion (seeded search, `search` / `get_passage` / `submit_finding`, 4-turn cap). Passages are shown as numbered sentences and cited by pointer; code builds the quote and exact offsets; "not assessed" is assigned from the stop reason (ADR-041 to ADR-047). | Built |
| `engine/fetch/__init__.py` | Marks `fetch` as a package. | Built |
| `engine/fetch/store.py` | `ResponseStore`: saves each raw response as gzip plus a `.meta.json` (URL, fetch time, SHA-256, size) and verifies the checksum on read. Backs both the cache and the fixtures (ADR-025). | Built |
| `engine/fetch/edgar.py` | `EdgarClient`: the data fetcher's EDGAR tools. `company_tickers`, `lookup_cik`, `submissions`, `companyfacts`, `latest_filing` (skips 10-K/A; both read a registrant successor's predecessor, `source_for`, ADR-063), `filing_document`. Three modes: replay (fixtures only, no network), live (cache, fetch on miss), record (fetch and write fixtures). Declared User-Agent, ~6 requests/s, retries with `Retry-After`. | Built |

## Static site (`site_src/`, built into `site/`)

| Path | Function | Status |
|---|---|---|
| `site_src/index.html`, `assets/js/index.js` | Rankings: description, disclaimer, data as-of, coverage, showcase links, search, sector filter, sort, 11-mark strips, insufficient-data and excluded folds, pending analyst section, score footnote. | Built |
| `site_src/company.html`, `assets/js/company.js` | Scorecard of one company with the evidence pane (figures, chart, inputs with SEC links, highlighted cited passages, second-reader checks); deep links; plain-language gap reasons. | Built |
| `site_src/trace.html`, `assets/js/trace.js` | Replay of the recorded agent run: numbered steps grouped by agent, hand-over lines, play, step and arrow keys, running calls and cost. | Built |
| `site_src/how-it-works.html`, `doc.html`, `assets/js/doc.js` | Process, architecture diagram (inline SVG), cost, evaluation, what it gets wrong, sources, production changes; a plain-text viewer for the linked repository documents. | Built |
| `site_src/evaluation.html`, `assets/js/evaluation.js` | The evaluation page, laid out from `data/evaluation.json`; prose only, no figures in the source (ADR-073). | Built |
| `site_src/assets/js/common.js`, `assets/site.css`, `assets/fonts/`, `assets/img/architecture.svg` | Shared helpers (marks, formats, plain reasons), design tokens and layout, self-hosted Public Sans and Source Serif 4 (OFL licences beside them), the architecture drawing. | Built |
| `site/` | Output of `python -m engine.cli publish` (git-ignored). | Local only |
| `results/stability/{a,b}/` | Full results and traces of the paraphrase runs (run ids `<SYMBOL>-live-a`, `-b`); never replace the main results (ADR-072). | Built |
| `docs/stability_report.md` | Flip rates, borderline findings, the dev-set correlation and the paraphrases side by side. Shown in the site's document viewer. | Built |
| `docs/screenshots/` | Review screenshots (git-ignored). | Local only |

## Scripts (`scripts/`)

| File | Function | Status |
|---|---|---|
| `scripts/record_fixtures.py` | One-off: records SEC data for the test tickers and writes `fixtures/MANIFEST.json`. Needs internet and `SEC_USER_AGENT`. Last run 2026-10-08, 26 requests. | Built |
| `scripts/llm_smoke.py` | Smoke test of the LLM client: model id check, JSON mode, tool calling with a round trip. `record` (live, ~4 free requests) or `replay` (offline). | Built |
| `scripts/sections_report.py` | Extracts sections from the 5 fixtures and writes `docs/sections_report.md` (status, opening text, top passages per criterion). | Built |
| `scripts/qualitative_report.py` | Runs the qualitative agent on the 5 test tickers and writes `docs/qualitative_report.md`. `record` (live, free tier only, refuses in paid mode) or `replay` (offline, identical report); optional ticker arguments. Also writes the trace and the list of fixture hashes used (git-ignored, under `data/cache/trace/`). | Built |
| `scripts/snapshot_universe.py` | Fetches the Wikipedia constituents table once (MediaWiki API), records the raw response in `fixtures/universe/`, writes `data/universe/sp500_<date>.csv`, validates it. `--offline` re-parses the recording. | Built |
| `scripts/sector_class_report.py` | Offline: writes `docs/sector_class_review.md`, every company whose class changes against SIC and every financial left "other", with reasons (ADR-057). | Built |
| `scripts/universe_scorecard_report.py` | Reads `results/scores/` and writes `docs/universe_scorecard_report.md`: run size, label distribution by criterion and class, data gaps, notes, anomaly lists. | Built |
| `scripts/universe_report.py` | `--fetch-sic` (live, once) records each company's SIC code to `data/universe/sic_<date>.csv`; writes `docs/universe_report.md`: SIC against GICS sector classes. | Built |
| `scripts/review_report.py` | Runs Explainer + Critic on the 5 tickers against the recorded qualitative run, injects 3 faults into the model check, and writes `docs/critic_report.md` (explanations, every check, retries, gold-set table, Critic scorecard, cost). `record` (free tier only) or `replay` (offline, identical). | Built |
| `scripts/qualitative_variability.py` | Runs the 5 tickers N extra times live with the response store bypassed (`use_store=False`), compares with the recorded run and writes `docs/qualitative_variability.md`. Free tier only; stops if today's ledger count would pass 400. | Built |
| `scripts/sections_audit.py` | Offline: runs the section extractor over every analysed company's 10-K (fixtures, then the local cache) and prints found / not_found per item; `--save` / `--compare` give a before → after (build 4a). | Built |
| `scripts/stability_run.py` | `refresh` (the 20 showcase companies with the active prompts), `a` and `b` (paraphrase runs over the 25 analysed companies, results in `results/stability/<variant>/`); resumable across Pacific days, free tier only (ADR-072). | Built |
| `scripts/stability_report.py` | Writes `docs/stability_report.md` from the main and variant results (`--attach` also writes `stability` onto the main results). | Built |
| `scripts/label_packet.py` | Writes the blind labelling packet for the held-out companies (`docs/labelling/heldout_packet.md`, git-ignored) from their 10-Ks only, or `--ingest` a filled packet into `eval/heldout_labels.json` (ADR-071). | Built |
| `scripts/backfill_passages.py` | Offline: adds the cited passages' text to results written before schema 1.2 and re-exports `schema/result.schema.json`; nothing else in a result changes (build 4a). | Built |
| `scripts/score_report.py` | Scores the 5 fixtures (replay) and writes `docs/scorecard_report.md`. | Built |
| `scripts/coverage_report.py` | Runs the normaliser on the 5 fixtures (replay) and writes `docs/coverage_report.md`. | Built |

## Docs output (`docs/`)

| File | Function | Status |
|---|---|---|
| `docs/scorecard_report.md` | Summary table and, per company, every criterion's result, figures, threshold, years, flags and source filings. | Built |
| `docs/sections_report.md` | Per company and item: status, method, length, opening text; then the top 3 passages per qualitative criterion. Preview of what the agent sees. | Built |
| `docs/qualitative_report.md` | Per company and criterion: verdict, rationale, quoted text with accession, item, passage and offsets, searches made, stop reason, calls, tokens and notional cost; summary table and calls and tokens per company. Verdicts are not frozen: they are reviewed by hand. | Built |
| `docs/universe_scorecard_report.md` | The numeric run over the index: 498 scored, 2 without a 10-K, label distribution per criterion and sector class, data gaps by reason, the 15 most common normaliser notes, anomaly lists (G4, revenue jumps, EPS sign, restatements, splits). | Built |
| `docs/sector_class_review.md` | GICS against SIC: the 51 class changes, the financials left "other" and Daniel's decisions of 2026-10-11, with reasons and notes. | Built |
| `docs/universe_report.md` | Snapshot size, dual classes, SIC-derived against GICS-implied sector classes (12 disagreements) and the 35 financials no exception covers. | Built |
| `docs/critic_report.md` | Per company: rendered explanations, every Critic check with attempt and detail, retries and final statuses; then the gold-set table, the Critic scorecard (caught / false alarms / agreement after retry), fault injection and cost per company. | Built |
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
| `tests/test_pld_dividends.py` | Prologis' and Trane's recorded facts: cash-paid dividends win over tiny declared amounts, and Trane's declared dividends survive a $0 cash-paid tag; G4 correct for both (ADR-060, ADR-061). | Built |
| `tests/test_sector_classes.py` | GICS mapping, overrides, precedence, SIC only as fallback, no REIT/insurance/utility sub-industry unmapped, REIT note and unchanged labels, numeric-only path (no model, no 10-K, crash = failed row, CLI default live). | Built |
| `tests/test_revenue_guard.py` | Component guard logic and recorded General Mills, Fifth Third, Goldman Sachs (ADR-061). | Built |
| `tests/test_decisions.py` | Financial classes and notes, G4 unknown years (synthetic and Federal Realty's recorded facts), Exxon successor (true accessions, note, evidence in the successor's own history), `no_annual_report` in the numeric batch and the full path (ADR-057, ADR-012, ADR-063). | Built |
| `tests/test_coverage.py` | Validated derived difference (same filing and period, overlap proof, forward only), Boston Properties, Public Storage, Chevron and Ford on recorded facts, Camden lease revenue, capex concepts stay totals (ADR-064). | Built |
| `tests/test_showcase.py` | The showcase config is valid and every reason shown on the page is checked against the committed rankings (ADR-070). | Built |
| `tests/test_figures_copy.py` | Runs the page's figure formatting with node: an empty list is a sentence, never a label followed by "none". | Built |
| `tests/test_deploy.py` | Scanner patterns and redaction, history scan (deleted secret, gzip fixture, commit message, `.env` value, this repository clean), dry run, planted secret / gate / broken link refuse, push to a local bare remote (ADR-068). | Built |
| `tests/test_trace_render.py` | Every event of the 5 recorded traces renders; no raw JSON or key=value text; titles, hand-offs, group summaries, running totals, Critic sentences, plurals, display names (ADR-067). | Built |
| `tests/test_site.py` | Publish output deterministic, disclaimer on every page, planted Finnhub field / banned word / non-SEC link fail the build, links and data paths resolve, JSON validates against the schemas, no third-party requests, no `innerHTML` from data, index size (ADR-065). | Built |
| `tests/test_rankings.py` | Score maths, threshold, exact ties, exclusions, caveat, analyst section, Finnhub gate, schema, determinism, CLI, and checks of the committed `site_data/rankings.json` (ADR-062). | Built |
| `tests/test_universe_counts.py` | The frozen label counts: consistency, tolerance logic, and the local run when `results/scores/` exists. | Built |
| `tests/test_universe.py` | Parsing, validation (count, duplicates, CIK checks, dual-class primary rule), CSV round trip, and the committed snapshot against SEC's ticker file. | Built |
| `tests/test_orchestrator.py` | Planner rules per sector class (and agreement with the scorers), out-of-scope ticker, step degradation and skip reasons, propagating errors, trace order, two replays byte-identical, JSON Schema validation, Finnhub gate, cost by agent, resumable batch, PROGRESS text, CLI. | Built |
| `tests/stubs.py` | `StubLLM`: a scripted model client for Explainer and Critic tests. | Built |
| `tests/test_explainer.py` | Formats, placeholder rendering, every fixture figure key has a format, None figures withheld, templated lines, one call per company, retry with feedback. | Built |
| `tests/test_critic.py` | Rule faults (wrong placeholder, stray number, altered quote, span outside the passage, wrong sha, banned phrase, "share buyback" not flagged), the model check's inputs, routing to owners, one retry then warning, never alters a verdict, cost totals, trace order. | Built |
| `tests/test_critic_fixtures.py` | Replay of the recorded review on the 5 companies: structure, R2 on real findings, 3 injected faults flagged, gold-set disagreements caught, no network. | Built |
| `tests/test_expected_qualitative.py` | Guard: replayed agent verdicts equal the recorded ones; agreement 19/20 with the one disagreement over-generous; every changed label has a dated reason. | Built |
| `tests/test_sentences.py` | Segmentation rules on synthetic text (bullets, newlines, abbreviations, decimals, long-sentence cuts, nothing lost) and exact round trip of every passage of the 5 recorded filings. | Built |
| `tests/test_qualitative.py` | 29 offline tests of the agent with scripted model replies through the real client (fake transport) on a synthetic 10-K: seeded search, search / get_passage / submit, unchanged assistant messages and tool-call ids, turn cap and last-turn tools, pointer citations (exact quote from sentence numbers, out-of-range, last before first, over 3 sentences, over 120 words, never-retrieved passage, one correction then `invalid_citation`, one extra turn), verdict per stop reason, malformed arguments, section_missing, quota and budget propagation, totals and trace order. | Built |
| `tests/test_qualitative_fixtures.py` | Replay of all 5 real runs with zero network: four findings each, every cited span equals `document_text[start:end]` and its sentence offsets, no mechanical citation failures, no advice words, totals add up. Structural only; verdicts not frozen. | Built |
| `tests/test_evaluation_page.py` | The page renders from the data (run with node), follows changed data, has no digit or numeric literal of its own, Wilson interval, the built site carries it and links it. | Built |
| `tests/test_sensitivity.py` | Thresholds module (defaults, scaling, override restores), the method on the five fixtures, determinism, the frozen file and its recomputation from the cache. | Built |
| `tests/test_reliability.py` | The threshold and the per-criterion computation on synthetic data (at, below, above), attach writing and clearing `reliability`, the note rendering only for low criteria, schema 1.2 results still valid. | Built |
| `tests/test_stability.py` | Paraphrase structure and anchors, the variant rubric reaching the agent and the Critic, classification (stable / borderline / not assessed), attach, flip rates, dev correlation, Fisher exact, the committed stability records against the runs they came from. | Built |
| `tests/test_stability_copy.py` | The company page's borderline sentence and rows, run with node. | Built |
| `tests/test_heldout.py` | The frozen held-out list, the packet (structure, eight passages per criterion, deterministic, no agent output), the ingest round trip and the agreement maths on synthetic cases including a hand-computed weighted kappa (ADR-071). | Built |
| `tests/test_build4a.py` | Build 4a: the citation cap message with per-sentence words (incl. the recorded O and MetLife rejections), the latest-fiscal-year rule reaching the agent and the Critic only from v2.1, results carrying their cited passages, publish from a clean checkout and its failure on a missing passage text, schema 1.2 additive. | Built |
| `tests/test_sections.py` | Synthetic-filing tests: HTML normalisation, TOC not chosen, combined headings, title fallback and stub handling, not_found reasons, passage offsets and determinism, BM25, the Retriever and its text cache. | Built |
| `tests/test_sections_fixtures.py` | Real 10-Ks (replay): every item found or explained, sections not opening on the TOC, offsets round-trip, DUK's 16 MB filing under 10 s. | Built |
| `tests/test_expected_scores.py` | Guard: fails if any label or key figure differs from `eval/expected_scores.json`. | Built |
| `tests/test_score_fixtures.py` | Certain facts about the 5 real companies' scores (replay). | Built |
| `tests/test_normalise.py` | 13 synthetic-data tests: annual vs quarterly, instants, 52/53-week years, `fy`/`fp` ignored, restatement, per-year fallback, notes, derived sums, gaps, unit mismatch, model validation. | Built |
| `tests/test_normalise_fixtures.py` | Real-fixture checks (replay): ≥10 years of core measures, TSLA losses, JPM bank gaps, provenance on every value. | Built |
| `tests/test_edgar.py` | 18 offline tests with a fake transport: modes, User-Agent rules, retries (incl. `Retry-After` and connection errors), throttle, 403/404 handling, checksum tampering, 10-K selection, provenance surviving record → replay. | Built |

## Results (`results/`, `schema/`) and universe data

| Path | Function | Status |
|---|---|---|
| `results/scores/<CIK>.json` | Numeric-only results of the whole index (git-ignored, local). | Built |
| `results/<CIK>.json`, `results/<CIK>.trace.jsonl` | One `Result` (schema 1.1) and its trace per analysed company. Git-ignored except the 5 test tickers and the 20 showcase companies, which are committed so the site can be rebuilt (ADR-054, ADR-070). | Built |
| `site_data/rankings.json` | The criteria ranking of the index (and the empty analyst section), built by `python -m engine.cli rankings`; committed as the input of the static site (ADR-062). | Built |
| `schema/rankings.schema.json` | JSON Schema of `Rankings`, exported by `python -m engine.cli schema`; a test fails if it is stale. | Built |
| `schema/result.schema.json` | JSON Schema of `Result`, exported by `python -m engine.cli schema`; a test fails if it is stale. | Built |
| `PROGRESS.md` | Written by `status` and after every batch: done / warnings / failed / remaining, spend, measured calls per company, projection. | Built |
| `data/universe/sp500_<date>.csv`, `sic_<date>.csv` | The constituents snapshot and each company's SIC code (committed, small). | Built |
| `fixtures/universe/` | The raw MediaWiki response behind the snapshot. | Built |

## Recorded model responses (`fixtures/llm/`)

Committed, so LLM-using tests replay offline. The three smoke-test calls (JSON mode, tool request, answer after the tool result), the 35 requests the qualitative report replays (5 companies, 4 criteria) and the 36 the review report adds (Explainer, Critic, retries, 3 fault cases), gzip + `.meta.json` like the SEC fixtures; each file holds the request, the provider's response and the original latency, never the API key.

## Evaluation (`eval/`)

| File | Function | Status |
|---|---|---|
| `eval/snapshot.py` | Reduces a `ScoreSet` to label + key figures (4 significant digits); `python -m eval.snapshot` rewrites the frozen file after a reviewed change. | Built |
| `eval/expected_qualitative.json` | Gold set for the qualitative agent: per ticker and criterion the recorded agent verdict, the human-reviewed verdict and a note (reviewer line inside). Labels judge the filing under the current rubric; changes are kept in `label_history`. 1 of 20 labels differs from the agent's verdict. | Built |
| `eval/qualitative_agreement.py` | Replays the recorded agent run and prints agreement with the gold set (19/20) and the disagreements; `agreement()` is reused by the Critic evaluation. | Built |
| `eval/agreement_results.json` | Frozen output of `python -m eval.agreement --freeze`: dev and held-out agreement, the splits by criterion reliability and finding stability (ADR-073). | Built |
| `eval/heldout_packet_labelled.md` | The filled labelling packet: filing text and Daniel's verdicts only. | Built |
| `eval/agreement_history.json` | Dev agreement at v1.1, v2 and v2.1, typed once with sources. | Built |
| `eval/critic_summary.py`, `eval/critic_summary.json` | What the Critic flagged, repaired and made worse over the 25 companies, computed from the results and frozen. | Built |
| `eval/universe_diagnostics.py`, `eval/universe_diagnostics.json` | How many companies still carry each anomaly flag in the whole-index run. | Built |
| `eval/numeric_triage.json` | What the numeric triage found and fixed (typed once from evaluation notes 19 and 20). | Built |
| `eval/sensitivity.py`, `eval/sensitivity_results.json` | Threshold sensitivity: every numeric threshold moved by 20%, labels that change per criterion; recomputed from the local SEC cache and frozen (ADR-074). | Built |
| `eval/heldout.json` | The frozen held-out list (AAPL, MSFT, PG, NEE, CAT, JNJ), why, the disclosure that agent verdicts for them already exist (ADR-071). | Built |
| `eval/heldout_labels.json` | Template for the 24 human labels (empty until Daniel labels the packet). | Built |
| `eval/packet.py` | The packet builder (`build_packet`, `fixed_retrieval`) and the reader of a filled packet; never reads an agent result. | Built |
| `eval/agreement.py` | `python -m eval.agreement`: agreement of the final agent verdicts with the human labels, dev and held-out separately: exact, within one level, direction, per criterion, weighted kappa. | Built |
| `eval/universe_label_counts.json` | Frozen per-criterion label counts (and per sector class) of the 498-company numeric run, with the tolerance rule. | Built |
| `eval/universe_counts.py` | `count_labels`, `compare` (tolerance max(5, 2%)) and `--freeze`; run as `python -m eval.universe_counts`. | Built |
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
| `engine/cli.py` rest: `rank`, `eval`, `publish` | Rankings builder, evaluation harness, publish step with the Finnhub gate. | ADR-004, ADR-016, ADR-021 |
| `results/`, `PROGRESS.md` | One JSON per company, `rankings.json`, run ledger output. | ADR-016, ADR-023 |
| `eval/` (rest) | Rest of the evaluation harness: ±20% threshold sensitivity, model comparison, failure cases. | ADR-011, ADR-015 |
| `site/` | Static website for GitHub Pages. | ADR-016 |
