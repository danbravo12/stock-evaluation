# Decision Log (ADRs)

Each entry: context → decision → trade-off. Status: **Accepted**, **Pending** (waiting on an external answer) or **Superseded**.

---

### ADR-001 — Theme: evaluate stocks against Graham and Buffett criteria
**Status:** Accepted · 2026-10-07
**Context:** Need a domain with clear, explainable criteria so the agent design (not model capability) is the demo.
**Decision:** Evaluate companies against Benjamin Graham's defensive-investor criteria and Warren Buffett's published principles.
**Trade-off:** Classic criteria are dated (Graham's are from the 1970s), so few modern stocks pass all of them. Treated as a talking point, not a flaw.

### ADR-002 — Universe: S&P 500 only
**Status:** Accepted · 2026-10-07
**Context:** Free structured financial data (SEC EDGAR) covers US filers only.
**Decision:** v1 covers S&P 500 constituents. Other tickers return "outside v1 scope".
**Trade-off:** No ASX or international coverage; would need paid or different data sources.

### ADR-003 — Output is an explained scorecard, never a verdict
**Status:** Accepted · 2026-10-07
**Context:** Must stay a research tool, not financial advice.
**Decision:** Output is "Graham X/7 · Buffett Y/8", with each criterion's figure, threshold, source, date and plain-English explanation. No buy/sell language, no "undervalued".
**Trade-off:** Less punchy than a rating, but defensible and transparent.

### ADR-004 — The platform does not adjudicate between criteria and analysts
**Status:** Accepted · 2026-10-07
**Context:** The two rankings will often disagree.
**Decision:** Show the criteria ranking and the analyst ranking side by side with no linking commentary. Users draw their own conclusions. Any agreement/disagreement statistics stay in the README/evaluation notes, not the UI.
**Trade-off:** Gives up a headline claim in exchange for neutrality and credibility.

### ADR-005 — Deterministic scoring in Python; LLM for explanation and qualitative judgement only
**Status:** Accepted · 2026-10-07
**Context:** Graham criteria and Buffett's quantitative tests are arithmetic. LLMs are unreliable at arithmetic and cost money.
**Decision:** All numeric criteria are computed by Python scripts. LLMs (a) explain results and (b) assess the four qualitative Buffett criteria from 10-K text, with mandatory citations.
**Trade-off:** Less "AI" on the surface; stronger story about choosing the right tool for each step. The agentic behaviour lives in planning, filing retrieval, qualitative judgement and the critic.

### ADR-006 — Two modes: discovery and ticker entry
**Status:** Accepted · 2026-10-07
**Decision:** Discovery mode shows both rankings for the S&P 500; ticker mode analyses any S&P 500 ticker.
**Trade-off:** The full S&P 500 scorecard is cheap (no LLM); the LLM analysis will be pre-computed for a featured set to stay at $0 (see open questions).

### ADR-007 — Data sources: EDGAR for fundamentals, Finnhub for price and analyst consensus
**Status:** Pending (Finnhub permission) · 2026-10-07
**Context:** Finnhub's free tier is personal-use only; redistribution needs written approval. EDGAR is public domain.
**Decision:** All criteria use EDGAR. Finnhub supplies current price and analyst recommendation counts. Finnhub is used freely for development and testing (personal use, within free-tier terms). **Publish gate:** no Finnhub data goes on a public URL until Finnhub has replied in writing. Requested written permission for public display.
**Fallback if refused:** analyst panel becomes a "bring your own key" live mode; price-dependent Graham criteria (P/E, P/E×P/B) show as data gaps on the public site.
**Trade-off:** Licence-clean design costs two criteria in the worst case. Shows governance over convenience.

### ADR-008 — No price charts or Alpaca in v1
**Status:** Accepted · 2026-10-07
**Context:** Alpaca offers free price history but adds a third provider and its own licensing question.
**Decision:** Drop price charts and Alpaca from v1.
**Trade-off:** Less visual polish; simpler build and fewer licensing risks.

### ADR-009 — "Evaluated against principles", not impersonation
**Status:** Accepted · 2026-10-07
**Decision:** The tool never writes in Buffett's or Graham's voice or attributes quotes to them. It says "evaluated against Graham/Buffett principles".
**Trade-off:** Less playful; avoids misattribution risk.

### ADR-010 — Critic step as a verification gate
**Status:** Accepted · 2026-10-07
**Decision:** A Critic checks that (1) every figure in the explanation matches the script output, (2) every qualitative judgement cites a filing passage, (3) no recommendation-style language appears. One retry, then show with a visible warning.
**Trade-off:** Extra LLM call per run; small cost, large credibility gain.

### ADR-011 — Criteria thresholds
**Status:** Accepted · 2026-10-07
**Context:** Graham published exact rules; Buffett published principles only.
**Decision:** Graham criteria G1–G7 kept as written in *The Intelligent Investor* (1973), except G1 size updated to revenue ≥ $1B (inflation-adjusted $100M). Buffett quantitative criteria set as documented interpretations: B1 ROE ≥ 15% in ≥ 7 of 10 yrs; B2 long-term debt ≤ 4× 3-yr avg net income; B3 operating margin positive every year and last-3-yr avg ≥ 90% of 10-yr avg; B4 owner earnings (NI + D&A − capex) positive in ≥ 8 of 10 yrs and growing. Full table in `PROCESS.md` §5.
**Trade-off:** Buffett thresholds are judgement calls. Mitigated by stating them openly in the README and by a ±20% threshold sensitivity test in the evaluation harness.

### ADR-012 — G4 dividend record: 15-year window, always "partial"
**Status:** Accepted · 2026-10-07
**Context:** Graham requires 20 years of uninterrupted dividends; EDGAR structured data covers ~15–17 years.
**Decision:** Test a fixed 15-year window. A pass is always labelled "partial (15 of 20 yrs)". Companies with a shorter record (recent listings, spin-offs) pass if they paid a dividend every year on record, labelled "N yrs on record". No dividend in any year = fail.
**Trade-off:** Lenient for short-record companies; transparency comes from the label rather than a stricter rule.

### ADR-013 — Sector exceptions and ranking basis
**Status:** Accepted · 2026-10-07
**Context:** Some criteria are meaningless for certain companies.
**Decision:** Banks/insurers: G2 and B2 "not applicable". Utilities: G2 uses Graham's utility rule (debt ≤ 2× equity). Negative or near-zero equity: B1 "not meaningful". Criteria ranking uses % of applicable criteria met; data gaps reported separately.
**Trade-off:** Scorecard denominators vary by company; avoids penalising companies for tests that don't fit them.
**Amended 2026-10-08:** banks and insurers also get **B3 (stable margins)** and **B4 (owner earnings)** as "not applicable". The recorded JPM fixture has no operating income, D&A or capex tags, and both tests assume an industrial income statement. Bank-specific substitutes (e.g. pre-tax margin) were rejected: they would be the tool's own invented rules, not Graham's or Buffett's, and add scope. Banks and insurers are therefore scored on fewer applicable criteria; the varying denominator already handles this, and the scorecard states which tests were skipped and why.

### ADR-014 — S&P 500 constituents from a Wikipedia snapshot
**Status:** Accepted · 2026-10-07
**Context:** The official S&P constituent list is paid. Wikipedia's "List of S&P 500 companies" is free and includes CIK (direct EDGAR mapping) and GICS sector (drives ADR-013 exceptions).
**Decision:** Save a dated CSV snapshot; never scrape at run time. Validate on load: ~503 rows, every CIK present and matching SEC's company ticker file, no duplicate symbols. Analyse once per CIK (Alphabet, Fox, News Corp have two share classes). Normalise ticker formats (e.g. BRK.B / BRK-B) in one function. Refresh manually each quarter. Attribute: "Constituents: Wikipedia, as of [date]" (CC BY-SA).
**Trade-off:** Community-edited source may lag or be wrong; mitigated by snapshot validation against SEC data.

### ADR-015 — Models: Gemini Flash-Lite for runs, small local Gemma 4 for development
**Status:** Accepted · 2026-10-07
**Context:** Hard $0 target. Developer laptop has 8 GB RAM, so only the smallest open-weight models run locally (Gemma 4 E2B/E4B), too weak for cited 10-K reasoning.
**Decision:** Development uses recorded fixtures plus Gemma 4 E2B/E4B via Ollama for smoke tests. Analysis runs use Gemini Flash-Lite on the free tier (no card; ~500 requests/day reported, large context). Model is one config setting (OpenAI-compatible endpoint, model name, key env var). Fallback order, decided by evaluation results: Gemini Flash (same key) → Claude Haiku 4.5 (paid, < $1 for featured set, prepaid credits with auto-reload off).
**Amended 2026-10-08 (ADR-023):** the run model is pinned to **Gemini 3.1 Flash-Lite** for every company (free and paid runs), so results across the index come from one model. Paid use of it is governed by ADR-023.
**Trade-off:** Free-tier limits are unpublished and may change; free-tier prompts may be used by Google (acceptable — inputs are public SEC filings). The lightest model tier must prove citation accuracy in the evaluation harness. Comparing the small local and cloud models on the same harness is itself an evaluation result.

### ADR-016 — Static website + engine run in batches on the laptop
**Status:** Accepted · 2026-10-07
**Context:** $0 hosting; no public endpoint that can spend quota; reliable interview demo.
**Decision:** The engine (Python + agents) runs on the laptop in batches and writes one results file (JSON) per company. The public website is static (GitHub Pages): it only displays those files — no AI calls, no API keys, no server. Number-based criteria pre-computed for all S&P 500 companies; LLM analysis extended across the index over ~1 week of free-tier runs. Every page shows "data as of [date]".
**Trade-off:** Results only as fresh as the last batch run. Gains: $0 hosting, no quota abuse, keys never leave the laptop, demo can't fail because an API is down.

### ADR-017 — Live mode behind access codes (milestone 2)
**Status:** Accepted (milestone 2) · 2026-10-07
**Context:** A reviewer watching the agents run live is more convincing than a replay.
**Decision:** After v1 ships, add an optional live app on a free Python host (e.g. Streamlit Community Cloud) running the same engine. Access codes per reviewer (e.g. 5 runs/day each), a global daily cap, codes revocable. Gemini key held in the host's secrets. No Finnhub data in live mode until Finnhub permission is received. Engine built now as a library callable by both the batch command and the future app.
**Trade-off:** Second component to maintain; free hosts sleep (first load can take ~1 minute — wake before interviews). Leaked code worst case: free quota exhausted for the day, never a bill.

### ADR-018 — Rule-based planner; "agent" reserved for LLM steps
**Status:** Accepted · 2026-10-08
**Context:** Each company's run plan is fully determined by its sector (ADR-013) and which data exists. An LLM planner would add a call and non-determinism, and would always produce the same plan, which a reviewer would spot as theatre.
**Decision:** The Planner is Python rules that build a per-company `RunPlan` (applicable criteria, skipped steps and why). The agentic loop lives in the Buffett qualitative agent, which chooses which 10-K sections and queries to search and when it has enough evidence (keyword search over Items 1, 1A and 7; no embeddings). The former "Data agent" is renamed "Data fetcher", since it is deterministic tool code.
**Trade-off:** Fewer LLM components on the diagram; the agentic claim rests on the qualitative agent's tool loop and the critic's routed retries, so both must be clearly visible in the trace replay.

### ADR-019 — Critic: rule checks first, LLM only for judgement
**Status:** Accepted · 2026-10-08
**Context:** Three of the four ADR-010 checks can be decided by code.
**Decision:** Rules check (1) every figure in the explanation matches `ScoreSet` after number normalisation, (2) every quote appears verbatim in the cached 10-K, (3) no phrase from a banned-language list. One LLM call checks (4) whether each quote supports its verdict. Failures are routed back to the step that produced them; only failed items are retried, once.
**Trade-off:** Number matching needs careful normalisation ("$1.2B" vs 1,200,000,000) to avoid false flags. Gains: one LLM call instead of three, and checks that can't hallucinate.

### ADR-020 — Typed hand-off contracts and a versioned results schema
**Status:** Accepted · 2026-10-08
**Decision:** Every hand-off passes a typed object (`RunPlan`, `DataBundle`, `ScoreSet`, `QualFindings`, `Explanations`, `CriticReport`, `Result`) defined as Pydantic models. The results JSON carries `schema_version` and is validated before it is written. The static site reads only these files.
**Trade-off:** Schema work up front. Gains: the trace replay, the evaluation harness and the future live app (ADR-017) all reuse the same contracts.

### ADR-021 — Finnhub publish gate enforced in code
**Status:** Accepted · 2026-10-08
**Context:** ADR-007 forbids Finnhub data on a public URL until written permission arrives; a manual rule is easy to forget.
**Decision:** The `publish` command removes every Finnhub-sourced field unless `FINNHUB_PUBLIC_OK=true` is set in config. An evaluation-harness test fails if any Finnhub field appears in the publish output while the flag is off.
**Trade-off:** A little extra code; removes the risk of publishing licensed data by mistake.

### ADR-022 — Keyword search over 10-K sections; no embeddings or vector store in v1
**Status:** Accepted · 2026-10-08
**Context:** The qualitative agent searches only three sections (Items 1, 1A, 7) of one 10-K per company, a few dozen pages. Vector stores pay off on large document collections.
**Decision:** The filing retriever chunks the three sections and ranks chunks with keyword search (BM25, plain Python). The agent runs several searches per criterion, starting from a fixed list of search terms per Buffett criterion (e.g. durable advantage: "competitive advantage", "brand", "switching costs", "pricing power"), and may rephrase when a search returns nothing.
**Trade-off:** Keyword search misses synonyms, which the term lists and rephrasing mitigate. Gains: $0, no embedding model or index to maintain, and exact quotes the Critic can verify verbatim (ADR-019). **Revisit when:** the evaluation harness shows evidence a human reviewer finds but the agent misses, or the corpus grows (multiple years of 10-Ks, transcripts, cross-company search). A $0 upgrade path exists: a small local embedding model with FAISS or Chroma.

### ADR-023 — Progress ledger and a hard-capped paid budget to finish the S&P 500 faster
**Status:** Accepted · 2026-10-08
**Context:** On the free tier, cited LLM analysis of ~500 companies takes 1–2 weeks of laptop batch runs. A small paid budget can finish it in hours. Gemini 3.1 Flash-Lite costs $0.25 / $1.50 per million input/output tokens (≈ $9 for the full index at an estimated ~40k in / 5k out per company), or half that through the Batch API (≈ $4.40). Both are estimates to be replaced by measurements. Paid use needs a card on file; Google's project spend cap (AI Studio, since March 2026) takes ~10 minutes to take effect, and overage in that window is billable.
**Decision:**
1. **Run ledger** (one row per company: status, model, calls, tokens, actual $, notional $, timestamp). Batches resume from it.
2. **`status` command** and an auto-written `PROGRESS.md` after each batch (done / warnings / failed / spent / projected cost and days to finish). The public site shows a coverage line.
3. **Budget config:** `mode` (free | paid), `total_usd_cap` = $4.00 (engine), `per_company_usd_cap`, stop at 100% of the engine cap. The budget guard checks projected cost before every call and stops cleanly.
4. **Belt and braces:** Google project spend cap set to **$5** before billing is enabled; the engine cap ($4) sits below it to absorb the ~10-minute enforcement lag.
5. **Hybrid order:** each day's free-tier quota is used first; paid calls only cover the remainder, up to the cap. Whatever the cap doesn't cover finishes on the free tier.
6. **Gate:** paid mode cannot be switched on until (a) the evaluation harness passes on the test tickers (ADR-024) and (b) measured tokens per company project the remaining paid cost under $4.
7. **Batch API (50% off) is a later optimisation, not v1.** The qualitative agent is a multi-step tool loop; the Batch API is asynchronous, so each step would become a separate batch round across all companies. That needs a step-resumable orchestrator and is scope creep for v1. Revisit only if measured cost on the standard tier won't fit the cap.
**Trade-off:** Spends real money (≤ $5) and needs a card on file, in exchange for finishing the index quickly and the line "full S&P 500 analysed for $X, every cent tracked". With 3.1 Flash-Lite at standard rates the full index likely won't fit $4, so the hybrid order and free-tier days remain part of the plan; choosing 2.5 Flash-Lite (~$3) would fit but gives up the newer model.

### ADR-024 — Test tickers: KO, JPM, GOOGL, TSLA, DUK
**Status:** Accepted · 2026-10-08
**Context:** The evaluation harness and recorded fixtures need a small set of companies that exercise different rules, not four similar ones.
**Decision:** Fixtures and harness cases are built for:
- **KO** (Coca-Cola): baseline case. Long dividend record, stable earnings; expected to pass many criteria.
- **JPM** (JPMorgan): bank. Tests ADR-013 exceptions (G2, B2 not applicable) and varying denominators.
- **GOOGL** (Alphabet): two share classes analysed once per CIK (ADR-014), short dividend record (ADR-012), high P/E. Expected to fail several criteria.
- **TSLA** (Tesla): losses in the early years of the window and no dividends (expected fails on G3, G4, B1), very high P/E, and contested qualitative questions (management candour, capital allocation). A stress test that the qualitative agent judges only from cited 10-K text, not outside reputation, and that the Critic catches opinionated or advice-style wording.
- **DUK** (Duke Energy): utility. Tests Graham's utility variant of G2 (debt ≤ 2× equity, ADR-013), and a capital-heavy business where B2 (debt vs earnings) and B4 (owner earnings after capex) are likely to fail.
**Trade-off:** Five companies' fixtures to record and maintain instead of three, in exchange for covering every sector exception and the main failure modes. These are test tickers; the demo's featured set is still an open question.

### ADR-025 — One checksummed response store behind three fetch modes (replay / live / record)
**Status:** Accepted · 2026-10-08
**Context:** The architecture says the cache is the only door to the outside world (ARCHITECTURE.md §1), and development must not make live calls. SEC also requires a declared User-Agent, which is personal and must not land in git. One 10-K can be 16 MB of HTML.
**Decision:** A single `ResponseStore` saves each raw response as gzip (fixed mtime, so identical content gives identical bytes) plus a `.meta.json` with URL, fetch time, SHA-256, size and content type. It backs both the git-ignored HTTP cache (`data/cache/`) and the committed `fixtures/`. `EdgarClient` has three modes: `replay` (fixtures only, a miss raises, never touches the network; the default for tests and development), `live` (cache, fetch on miss) and `record` (always fetch, write fixtures). Reads verify the checksum and fail on mismatch. Meta files record the URL only, never request headers. Standard library only; transport, sleep and clock are injectable so every test runs offline. Throttle is 0.15 s between requests (~6/s, under SEC's 10/s limit); retries 429/5xx/connection errors at 1, 2 and 4 s (honouring `Retry-After`); 403 and 404 fail immediately.
**Trade-off:** Fixtures are a frozen snapshot (latest 10-K and facts as of 2026-10-08) and go stale until re-recorded. Gains: reproducible tests, provenance (URL + hash) for every figure, no personal details in git, ~4 MB of repo for five companies despite 16 MB raw filings.

---

## Open questions
- Which companies form the featured set for the demo script (test tickers in ADR-024 are candidates).
- Whether to include a neutral scatter view of both rankings.
