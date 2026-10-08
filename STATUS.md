# Status

**Phase:** 1 — Build (data layer, normaliser and scorers done)
**Last session:** 2026-10-08

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

## Waiting on
- Finnhub: written permission to display price and analyst data publicly. Email deferred (2026-10-08): send once first platform results exist, so the request can show what will be displayed. Must be sent and answered before publishing.
  - OK to use Finnhub for development and testing now.
  - **Publish blocker:** no Finnhub data on any public URL until a written reply is received. If refused, apply the ADR-007 fallback before publishing.

## Next
1. Create Gemini API key; check free-tier limits for Gemini 3.1 Flash-Lite in AI Studio, and confirm its paid price on Google's pricing page.
2. 10-K section extraction (Items 1, 1A, 7) and the keyword retriever (ADR-022).
3. Send Finnhub permission email once first results exist (publish blocker).
4. Later, before any paid run (ADR-023): measure tokens per company on the 5 test tickers; set the Google project spend cap to $5 *before* enabling billing (card on file required); only then switch `mode: paid`.
5. **Before the full S&P 500 run:** review the `SalesRevenueGoodsNet` risk (it is the last revenue fallback; for some companies it is a component such as Tesla's automotive sales, so it could fill a missing year with a partial figure).

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
