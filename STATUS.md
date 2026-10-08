# Status

**Phase:** 1 — Build (data layer done)
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

## Waiting on
- Finnhub: written permission to display price and analyst data publicly. Email deferred (2026-10-08): send once first platform results exist, so the request can show what will be displayed. Must be sent and answered before publishing.
  - OK to use Finnhub for development and testing now.
  - **Publish blocker:** no Finnhub data on any public URL until a written reply is received. If refused, apply the ADR-007 fallback before publishing.

## Next
1. Create Gemini API key; check free-tier limits for Gemini 3.1 Flash-Lite in AI Studio, and confirm its paid price on Google's pricing page.
2. Fact normaliser (XBRL concepts to one annual series per measure). Known quirks to handle are in the fixture notes below.
3. Send Finnhub permission email once first results exist (publish blocker).
4. Later, before any paid run (ADR-023): measure tokens per company on the 5 test tickers; set the Google project spend cap to $5 *before* enabling billing (card on file required); only then switch `mode: paid`.

## Notes for the normaliser (from the fixtures)
- Revenue is tagged differently per company: KO `Revenues`; JPM `Revenues` plus `InterestAndDividendIncomeOperating`; GOOGL and TSLA split across `Revenues` and `RevenueFromContractWithCustomerExcludingAssessedTax` (GOOGL's latter stops at FY2024); DUK has four revenue tags.
- JPM (bank) has no current assets/liabilities, operating income, D&A or PP&E capex tags (consistent with ADR-013 exceptions; B3 and B4 need a decision for banks).
- GOOGL has no `DepreciationDepletionAndAmortization` or `DepreciationAndAmortization` tag; B4 needs another source or a data gap. KO has `DepreciationDepletionAndAmortization` only.
- No company uses `PaymentsOfDividendsCommonStock`; TSLA has no dividend tags at all (expected, G4 fail); GOOGL has no `CommonStockDividendsPerShareCashPaid` (short dividend record).
- DUK's 10-K is 16.1 MB of HTML (0.7 MB stored); the section extractor must cope with that size.

## Milestone 0 summary (interview-ready)
- **Problem:** Value-investing analysis is slow, inconsistent and poorly sourced; analyst views and fundamentals are rarely seen side by side.
- **Design choice:** Deterministic Python for every numeric criterion; LLM agents only for explanation, cited qualitative judgement and verification.
- **Trade-off:** Licence-clean data (EDGAR public domain; Finnhub only with permission) over convenience, accepting possible data gaps.
- **Result:** Scoped v1 with 24 logged decisions, a process map, architecture v1 and a clear $0 path.
