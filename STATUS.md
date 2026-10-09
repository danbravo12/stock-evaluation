# Status

**Phase:** 1 — Build (data layer, normaliser, scorers, retriever, LLM layer, qualitative agent, Explainer and Critic done)
**Last session:** 2026-10-10

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

- Built the LLM layer (`engine/llm/`, `engine/trace.py`, `config/models.json`): provider-agnostic client over OpenAI-compatible HTTP with record/replay, cost meter (actual and notional), budget guard with a Pacific-day ledger, `complete_json`, tool calling and a JSONL trace recorder. ADR-038 to ADR-040. Verified live on the free tier (model id, JSON mode, tool calling with the tool-result round trip; 4 requests, $0.00) and replayed offline with zero network calls; the smoke fixtures are in `fixtures/llm/`.

- Built the Buffett qualitative agent (`engine/agents/qualitative.py`, `engine/sentences.py`, rubric in `config/search_terms.json`, contracts `Citation` / `QualFinding` / `QualFindings`): one tool loop per criterion with a seeded first search in code, `search` / `get_passage` / `submit_finding`, a 4-turn cap, and citations as sentence pointers from which code builds the quote and exact offsets (ADR-041 to ADR-044, ADR-046). v1 (7af5412) lost 5 of 20 findings to quote mismatches and gave "found" for candid management to all five; **v1.1** replaced free-text quotes with sentence pointers (0 of 20 lost), split the verdict "not assessed" (system could not judge) from "insufficient evidence" (filing does not show it), and tightened the rubric (ADR-047). Recorded for the 5 test tickers on the free tier (35 requests kept; v1.1 used 35 to record and 70 for the variability runs; actual spend $0.00, notional $0.20 over both builds): `docs/qualitative_report.md`. Measured per company: mean 7.0 model calls, 18.8k input + 0.94k output tokens, notional $0.0061. Repeat-run variability (`docs/qualitative_variability.md`): verdicts identical in 20 of 20. 196 offline tests pass. **Verdicts are not frozen: Daniel reviews them first** (doubts and limits in `docs/evaluation_notes.md` items 7–11).

- Froze the qualitative gold set (`eval/expected_qualitative.json`, `eval/qualitative_agreement.py`): the recorded v1.1 verdicts with a human verdict and note per ticker × criterion (Daniel Bravo, reviewed with Claude, 2026-10-10); 17/20 agree, the 3 differences (JPM and DUK capital allocation, GOOGL candid management) are all over-generous (ADR-050). A guard test keeps the replayed agent equal to the recorded verdicts.
- Built the Explainer (`engine/agents/explainer.py`, `config/figure_formats.json`): one call per company, placeholders instead of numbers, templated lines for n/a and data gaps (ADR-048); and the rules-first Critic (`engine/agents/critic.py`, `review.py`, `config/banned_phrases.json`): R1 explanations, R2 citations re-verified against the stored 10-K, R3 banned language, L1 one model check per company, failed items routed to their owner once and re-checked, otherwise a visible warning; it never rewrites (ADR-049, ADR-051). Recorded on the free tier: `docs/critic_report.md`. Result: the Critic caught 3 of 3 gold disagreements and 3 of 3 injected faults, flagged 6 of 13 correct findings (5 genuine rationale overreach), and agreement stayed 17/20 → 17/20 after the retries. 0 explanation or citation rule failures on real data. Per company the review step adds mean 6.6 calls (Explainer 1.0, Critic 1.8, qualitative retries 3.8) and 15.6k input + 1.5k output tokens, notional $0.0061, so about 13.6 calls and $0.012 with the qualitative agent. Requests for this step: 54 (36 kept in `fixtures/llm/`; the rest were two KO trial runs). 244 offline tests pass.

## Waiting on
- Finnhub: written permission to display price and analyst data publicly. Email deferred (2026-10-08): send once first platform results exist, so the request can show what will be displayed. Must be sent and answered before publishing.
  - OK to use Finnhub for development and testing now.
  - **Publish blocker:** no Finnhub data on any public URL until a written reply is received. If refused, apply the ADR-007 fallback before publishing.

## Next
1. Orchestrator + Reporter (ADR-018, ADR-020). `explain_and_verify` is the review step it calls; the orchestrator must treat `QuotaReached` / `BudgetExceeded` as "company not done" and resume from the ledger (ADR-044), and the Reporter must show `warning` items and the Critic's detail, plus "not assessed" reasons.
2. Retrieval evaluation set (small): 20–30 questions on the 5 test tickers labelled with their correct passages; report BM25 recall@5. If it shows missed evidence, that is ADR-022's trigger for hybrid retrieval in v1; the same set is the seed for V2-3.
3. Rationale overreach at the source (`docs/evaluation_notes.md` items 9 and 12): the Critic sees it in about half of the found/weak findings but one retry does not remove it. Options: ask for shorter rationales built only from cited sentences, a stricter output format, or a stronger model.
4. Send Finnhub permission email once first results exist (publish blocker).
5. Later, before any paid run (ADR-023): the full per-company cost is now measured (about 13.6 calls and 34k input + 2.4k output tokens, notional $0.012, see `docs/critic_report.md` and `docs/qualitative_report.md`; roughly $6 for the whole S&P 500, above the $4 engine cap); set the Google project spend cap to $5 *before* enabling billing (card on file required); only then switch `mode: paid`.
6. Compare Gemini 3.1 Flash-Lite with hosted Gemma 4 31B (free, 14,400 requests/day) on the evaluation harness (ADR-015), including Gemma as the **Critic** on the same gold set (ADR-051: shared blind spots).
7. **Before the full S&P 500 run:** review the `SalesRevenueGoodsNet` risk (it is the last revenue fallback; for some companies it is a component such as Tesla's automotive sales, so it could fill a missing year with a partial figure). Also run the section extractor over a wider sample of 10-K layouts than the five fixtures.

## Later (v2, only after v1 ships)
1. Read-only MCP server over the published results JSON (`DECISIONS.md` V2-1). First v2 item: $0, reuses the v1 results schema.
2. Cross-provider model comparison on Amazon Bedrock (V2-2), after the free Gemini vs Gemma comparison (Next #6). Decide the separate Bedrock allowance before building.
3. Cross-company "Ask the filings": hybrid BM25 + vector retrieval over S&P 500 10-K passages (V2-3), also exposed as an MCP tool. Depends on the retrieval evaluation set (Next #2).

## Notes carried forward (normaliser and scorers)
- GOOGL has no D&A tag (total D&A is a company-extension tag missing from companyfacts) and `Depreciation` only from 2021, so even with the ADR-030 fallback B4 stays a data gap for most of its 10-year window.
- **Decided 2026-10-08:** G4 counts "years on record" from the net income series and a year as paid only if dividends per share > 0 (fallback: dividends paid > 0); zeros count as not paid (ADR-012 amendment). Depreciation alone is a flagged conservative D&A fallback (ADR-030).
- **Known limitation:** mixing different revenue tags across years (DUK) can shift margins by up to ~9% between years; report it in the evaluation rather than hide it.
- GOOGL history is shorter: revenue/net income from 2013, dividends only 2024–2025, diluted shares 2022–2025, EPS missing 2015. KO revenue starts 2016 (10 values).
- JPM long-term debt exists only for 2008–2013 (bank; B2 is already not applicable). JPM `Revenues` is total net revenue.
- Revenue tags switch within a company (DUK uses four); the concept used is recorded per value. Fallback concepts can mean slightly different things (e.g. `ProfitLoss` includes minorities), which produces "differs by more than 1%" notes.
- Restated values are flagged (`restated`, `original_value`); the latest filed value is used.
- DUK's 10-K is 16.1 MB of HTML (0.7 MB stored); the section extractor must cope with that size.

## Notes carried forward (qualitative agent)
- Recorded with the free tier only (`PAID_MODE_ENABLED` unset). The replay report is byte-identical across runs; `fixtures/llm/` holds exactly what `scripts/qualitative_report.py replay` uses, plus the three smoke fixtures. Changing the system prompt, tool schemas, rubric text or `search_terms.json` queries changes request hashes: re-record (about 35 requests) and prune orphaned fixtures (list of used hashes: `data/cache/trace/qualitative_used_hashes.txt`).
- Citations are sentence pointers (ADR-046); the only mechanical failure mode left is the model pointing at a passage it was not shown or a bad range (one correction, then `invalid_citation` → "not assessed"). Quota use: 7 requests per company, so about 55 companies a day on the free tier for this agent alone.
- Changing the segmenter (`engine/sentences.py`) changes the numbers the model sees: re-record too.
- `get_passage` was never called by the model (search results carry full passage text); it stays as a tool for models that ask for it.
- Run-to-run variability measured: identical at temperature 0 for identical prompts (20 of 20), but small prompt/rubric changes did move verdicts earlier, so wording sensitivity is the real risk (`docs/evaluation_notes.md` item 11).
- Seeded search + `llm` and `trace` should share one `TraceRecorder`, so model calls and tool calls interleave (the script does).

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

## Milestone 2a summary (interview-ready): agents
- **Problem:** An LLM that writes about a company can invent a number, misquote a filing, or slide into advice; a reviewer cannot tell from the output alone.
- **Design choice:** Make the unsafe things impossible rather than unlikely. The model *points* at filing sentences and *names* figures with placeholders; code builds the quotes (exact offsets) and writes the numbers. A rules-first Critic then re-verifies everything it can without a model (placeholders, stray digits, quotes against the re-loaded 10-K and its hash, banned language) and uses one narrow model check only for "does this quote support this verdict". Failures go back to their owner once, then show as warnings; the Critic never rewrites. A small human-reviewed gold set (20 labels) turns "the Critic works" into numbers.
- **Trade-off:** Stiffer prose and a few mechanical limits (sentence boundaries decide the quote; one reviewer, 20 labels; same model as the agents; the Critic never looks at "insufficient evidence", so it cannot find false negatives).
- **Result:** 0 mechanical citation failures (5 of 20 before sentence pointers); 0 wrong figures or stray numbers in 55 explanations; Critic caught 3/3 gold-set disagreements and 3/3 injected faults but also flagged 6 of 13 correct findings (5 real rationale overreach), and routed retries did not improve agreement (17/20 → 17/20); about 13.6 model calls and $0.012 notional per company, $0 actual on the free tier; 244 offline tests.
