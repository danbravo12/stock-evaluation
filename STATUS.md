# Status

**Phase:** 1 — Build (data layer, normaliser and scorers done)
**Last session:** 2026-10-08

## How we work (agreed 2026-10-09)
1. **Plan here:** design and decisions happen in the Claude project chat. For each build step, Claude writes one Claude Code prompt (scope, design rules, tests, verification, doc updates, commit message).
2. **Build in Claude Code:** Daniel pastes the prompt into Claude Code on the Mac. Claude Code has internet (SEC, Gemini, Finnhub) and runs git. It builds, tests, updates `DECISIONS.md` / `STATUS.md` / `FILEMAP.md`, commits locally (no push unless asked) and writes a short report.
3. **Review here:** Daniel pastes the report back into the chat. Claude reviews it (incl. spot checks against the fixtures), raises issues or decisions, syncs the docs to the project and writes the next prompt.
- The local folder `~/Projects/StockEvaluation` is the master copy; project docs are synced copies.
- Claude in the chat does not edit code in the folder directly (decided 2026-10-08); doc-only edits it makes are committed by Claude Code in the next step.

## Done
- Brainstormed theme, modes, criteria approach and data sources.
- Drafted process map (`PROCESS.md`) and decision log (`DECISIONS.md`, ADR-001 to ADR-010).
- Set criteria thresholds, G4 dividend rule and sector exceptions (ADR-011 to ADR-013).
- Chose S&P 500 constituent source: Wikipedia snapshot (ADR-014).
- Chose models: Gemini Flash-Lite for runs, small local Gemma 4 for development (ADR-015).
- Chose deployment: static site + laptop batch runs (ADR-016); live mode with access codes planned for milestone 2 (ADR-017).
- Drafted architecture diagram v1 (`ARCHITECTURE.md`: system view, agent hand-offs, component catalogue, run economics). Accepted ADR-018 to ADR-022 (rule-based planner, rules-first critic, typed contracts, coded Finnhub publish gate, keyword search over embeddings) and ADR-023 (progress ledger + paid budget: Gemini 3.1 Flash-Lite, $4 engine cap under a $5 Google spend cap).
- Built repo skeleton and the SEC EDGAR fetcher (replay / live / record modes, throttle, retries, checksummed store; ADR-025). 18 offline tests pass.
- Recorded fixtures for KO, JPM, GOOGL, TSLA, DUK (`fixtures/`, ~4.4 MB, `MANIFEST.json`); all CIKs match expectations; replay check loads everything with zero network calls.

- Built the fact normaliser (`engine/normalise.py`, `engine/contracts.py`, `config/concept_map.json`): one annual series per measure with concept, accession and URL on every value; gaps carry reasons. Pydantic introduced (ADR-029). Rules logged as ADR-026 to ADR-028. 35 offline tests pass; `docs/coverage_report.md` shows coverage for the 5 fixtures.

- Built the deterministic scorers G1–G7 and B1–B4 with stock-split adjustment (`engine/splits.py`, `engine/score/`, `config/sector_rules.json`); results are structured facts with the provenance of every input. ADR-031 to ADR-034. `docs/scorecard_report.md` shows all 5 test companies. G6 and G7 are data gaps until a price is available. Results reviewed and frozen in `eval/expected_scores.json` (guard test); known weaknesses listed in `docs/evaluation_notes.md`.
- Gemini API key created (2026-10-09). Free-tier limits confirmed in AI Studio: Gemini 3.1 Flash-Lite 15 RPM, 250K TPM, 500 requests/day, enough for ~40–80 companies/day (ADR-015, ADR-023).

- Built the 10-K section extractor and keyword retriever (`engine/filing_text.py`, `engine/sections.py`, `engine/retrieve.py`, `config/search_terms.json`): Items 1, 1A and 7 found in all 5 recorded 10-Ks (JPM's Item 7 via the title fallback), passages with exact citation offsets, BM25 `search` / `get_passage`. ADR-035 to ADR-037. `docs/sections_report.md` previews what the agent will see; the search is a mixed first baseline (see its ADR-037 trade-off).

## Waiting on
- Finnhub: written permission to display price and analyst data publicly. Email deferred (2026-10-08): send once first platform results exist, so the request can show what will be displayed. Must be sent and answered before publishing.
  - OK to use Finnhub for development and testing now.
  - **Publish blocker:** no Finnhub data on any public URL until a written reply is received. If refused, apply the ADR-007 fallback before publishing.

## Next
1. LLM client + cost meter + budget guard (ADR-015, ADR-023). Confirm `GEMINI_API_KEY` is in `.env` (key from fwdanielbravo@gmail.com, project "Dashboard-ui"); never in chat or git.
2. Qualitative agent: tool loop over `search` / `get_passage`, citations required (ADR-018).
3. Send Finnhub permission email once first results exist (publish blocker).
4. Later, before any paid run (ADR-023): measure tokens per company on the 5 test tickers; set the Google project spend cap to $5 *before* enabling billing (card on file required); only then switch `mode: paid`.
5. When the agents exist: compare Gemini 3.1 Flash-Lite with hosted Gemma 4 31B (free, 14,400 requests/day) on the evaluation harness (ADR-015).
6. **Before the full S&P 500 run:** review the `SalesRevenueGoodsNet` risk (it is the last revenue fallback; for some companies it is a component such as Tesla's automotive sales, so it could fill a missing year with a partial figure). Also run the section extractor over a wider sample of 10-K layouts than the five fixtures.

## Notes carried forward (normaliser and scorers)
- GOOGL has no D&A tag (total D&A is a company-extension tag missing from companyfacts) and `Depreciation` only from 2021, so even with the ADR-030 fallback B4 stays a data gap for most of its 10-year window.
- **Decided 2026-10-08:** G4 counts "years on record" from the net income series and a year as paid only if dividends per share > 0 (fallback: dividends paid > 0); zeros count as not paid (ADR-012 amendment). Depreciation alone is a flagged conservative D&A fallback (ADR-030).
- **Known limitation:** mixing different revenue tags across years (DUK) can shift margins by up to ~9% between years; report it in the evaluation rather than hide it.
- GOOGL history is shorter: revenue/net income from 2013, dividends only 2024–2025, diluted shares 2022–2025, EPS missing 2015. KO revenue starts 2016 (10 values).
- JPM long-term debt exists only for 2008–2013 (bank; B2 is already not applicable). JPM `Revenues` is total net revenue.
- Revenue tags switch within a company (DUK uses four); the concept used is recorded per value. Fallback concepts can mean slightly different things (e.g. `ProfitLoss` includes minorities), which produces "differs by more than 1%" notes.
- Restated values are flagged (`restated`, `original_value`); the latest filed value is used.
- DUK's 10-K is 16.1 MB of HTML (0.7 MB stored); the section extractor must cope with that size.

## Milestone 0 summary (interview-ready)
- **Problem:** Value-investing analysis is slow, inconsistent and poorly sourced; analyst views and fundamentals are rarely seen side by side.
- **Design choice:** Deterministic Python for every numeric criterion; LLM agents only for explanation, cited qualitative judgement and verification.
- **Trade-off:** Licence-clean data (EDGAR public domain; Finnhub only with permission) over convenience, accepting possible data gaps.
- **Result:** Scoped v1 with 24 logged decisions, a process map, architecture v1 and a clear $0 path.

## Milestone 1 summary (interview-ready): deterministic engine
- **Problem:** Turning public filings into 10 years of comparable figures is the hard, error-prone part of value analysis: companies tag the same item differently, switch tags, restate earlier years, and older per-share figures are never adjusted for later stock splits (Alphabet's 2016 EPS reads 27.85 against 2.93 for 2020).
- **Design choice:** Recorded, checksummed SEC fixtures (no live calls in development); a reviewable concept map with per-value provenance (tag, filing, URL); explicit rules for annual periods, restatements and splits; pure-Python scorers for G1–G7 and B1–B4; results frozen in `eval/expected_scores.json` with a test that fails on any drift.
- **Trade-off:** Report gaps instead of guessing (Alphabet B4 is a data gap; price-based G6/G7 wait for Finnhub); accept documented simplifications for v1 (ROE on total equity, sector class from SIC codes, depreciation-only D&A fallback) and list what the tool gets wrong in `docs/evaluation_notes.md`.
- **Result:** Five test companies scored with every figure traceable to an SEC filing; 94 offline tests; 34 logged decisions; $0 spent. Results checked by hand against raw data before freezing (e.g. Duke's owner earnings negative in all 10 years).
