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
**Amended 2026-10-08 (correction):** "years on record" means years for which the company has annual financial data in EDGAR (its net income series), **not** years with dividend data. As first written, a company that is long listed but only recently started paying (Alphabet: financials from 2013, dividends from 2024) would have passed as "2 yrs on record". A year counts as paid only if dividends per share is above zero; if per-share data is missing for a year, dividends paid above zero is used instead, and the source is shown. Zero-valued dividend facts (Alphabet reports $0 in several years) count as not paid. A one-off non-dividend payment can still show up in the cash-paid tag (Alphabet, $47M in 2015), which is why per-share data takes priority.


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
**Confirmed 2026-10-09 (AI Studio, free tier, project "Dashboard-ui"):** Gemini 3.1 Flash-Lite = 15 requests/min, 250K tokens/min, **500 requests/day**. Paid: $0.25 / $1.50 per 1M input/output tokens; Batch $0.125 / $0.75 (ai.google.dev pricing page). Free-tier prompts may be used by Google to improve products; paid-tier prompts are not. Gemini 2.5 Flash-Lite free tier is only 20 requests/day, so it is not a free fallback. Hosted Gemma 4 31B (30 RPM, 16K TPM, 14,400 RPD) is a free candidate to compare on the evaluation harness, not adopted.


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

### ADR-026 — Annual period selection and fiscal-year labelling
**Status:** Accepted · 2026-10-08
**Context:** EDGAR company facts mix annual, quarterly and year-to-date figures from 10-K, 10-Q and 8-K filings. Each fact carries `fy`/`fp` fields, but they describe the *filing*, not the period: the prior-year comparative inside a FY2025 10-K also says `fy=2025`.
**Decision:** Keep only facts from form 10-K or 10-K/A. Duration facts must span 350–380 days (covers 52/53-week years); balance-sheet (instant) facts must fall within 7 days of the fiscal year end from `submissions.json` (`fiscalYearEnd`, MMDD). Each value is labelled by its period **end date**; `fy` and `fp` are never used (a test proves a comparative lands in the right year). All available years are kept; each scorer picks its own 10- or 15-year window.
**Trade-off:** Ignores 10-Q-only data (the latest quarter) and transition periods, so the series is annual and slightly behind. Gains: one unambiguous year label that cannot be shifted by how a company files comparatives.

### ADR-027 — Restatements: latest filed value, flagged, original kept
**Status:** Accepted · 2026-10-08
**Context:** The same period appears in several 10-Ks (as a comparative), and companies sometimes restate or recast it.
**Decision:** Use the value from the most recently filed 10-K for that period. If it differs from the earliest filed value by more than 0.5%, set `restated=true` and keep the original in `original_value`. Both values keep their accession, so either can be traced.
**Trade-off:** Scores use today's best-known number, not what investors saw at the time (no point-in-time view). Gains: consistent series, and restatements are visible instead of silent.

### ADR-028 — Concept map as reviewable config; per-year fallback; explicit derived values; never guess
**Status:** Accepted · 2026-10-08
**Context:** Companies tag the same measure with different XBRL concepts and change tags over time (GOOGL, TSLA and DUK all do). Hard-coding this in Python hides the judgement calls.
**Decision:** `config/concept_map.json` lists, per measure, the unit, period type and an ordered priority list of concepts, with a short reason per measure. For each fiscal year the first concept with a value wins, and the concept used is recorded on every value. If another listed concept disagrees by more than 1%, a note is added (no failure). Sums (e.g. D&A = depreciation + amortisation of intangibles) exist only where the map says so, need every part, and are marked `derived` with their source concepts. A measure/year with no match becomes a `Gap` with a reason (no listed concept reported, only non-annual data, unit mismatch). The normaliser reports gaps; whether a gap matters (e.g. a bank has no current assets, ADR-013) is the scorers' decision.
**Trade-off:** The map needs a human review per new company type, and fallback tags can mean slightly different things (e.g. net income including noncontrolling interests); the disagreement notes and the coverage report (`docs/coverage_report.md`) make that visible. Gains: no silent substitutions, and the judgement calls are in one reviewable file.

### ADR-029 — Pydantic v2 as the first dependency
**Status:** Accepted · 2026-10-08
**Context:** ADR-020 requires typed hand-off contracts validated before anything is written. Everything so far was standard library only.
**Decision:** Add Pydantic v2 (pinned exactly in `requirements.txt`, installed in a git-ignored `.venv`) for the contracts in `engine/contracts.py`. Everything else stays standard library.
**Trade-off:** One dependency and a venv step before running tests. Gains: validated, self-documenting contracts and JSON (de)serialisation with almost no code, reused by the results schema and trace replay.

### ADR-030 — Depreciation alone as a flagged, conservative D&A fallback
**Status:** Accepted · 2026-10-08
**Context:** B4 owner earnings = net income + D&A − capex. Some companies stop tagging amortisation: Tesla reports only `Depreciation` from 2022, so the derived sum (ADR-028) is incomplete and B4 became a data gap for its four latest years.
**Decision:** When no listed D&A concept and no complete derived sum exists for a year, `Depreciation` alone is used, marked `derived` with a note "excludes amortisation (understates D&A)". Understating D&A lowers owner earnings, so the fallback errs on the conservative side, the same reasoning as using total capex as a proxy for maintenance capex (PROCESS §5, B4). Alphabet remains a gap for most years because it has no D&A or depreciation tags before 2021.
**Trade-off:** Mixes slightly different definitions within one series; mitigated by the per-value flag and the coverage report. Gains: Tesla is scored on real data instead of a gap, without ever overstating owner earnings.

### ADR-031 — Scoring windows and the as-of year
**Status:** Accepted · 2026-10-08
**Context:** Criteria are defined over "the last 10 years" (G4: 15), but companies report different numbers of years, and the normaliser reports gaps only after a series' first value.
**Decision:** The as-of year is the latest fiscal year with net income. The window is the 10 fiscal years ending there (G4: 15). Fiscal years are keyed by the year of the period end date (a 52/53-week year ending in the first days of January counts in the year before). "Years on record" are window years with a net income value (ADR-012 correction); G3 and G4 judge those years and label a short record "N yrs on record", but a net income hole *after* the first record year is a data gap. Every other multi-year test (G5, B1, B3, B4) needs every window year; a missing year is a data gap that names the years, wherever the series starts. B1 also needs the opening equity of the first year. Percent met = met / decided (pass, partial pass, fail); data gaps, not meaningful and not applicable are counted separately (ADR-013).
**Trade-off:** One missing year makes a test a gap instead of a judgement on nine years: stricter, but never a guess. Gains: one rule for all windows and gaps that tell the reader exactly which years are missing.

### ADR-032 — Stock-split adjustment of per-share values
**Status:** Accepted · 2026-10-08
**Context:** EDGAR keeps older per-share figures on the share basis of the filing that reported them. Alphabet's 2016 EPS is 27.85 and its 2020 EPS 2.93, because of the 2022 20:1 split; Tesla mixes three bases (5:1 in 2020, 3:1 in 2022). Unadjusted, G5 (EPS growth) and G6/G7 would be wrong by large factors.
**Decision:** `engine/splits.py` reads the split-ratio facts a company tagged (`StockholdersEquityNoteStockSplitConversionRatio` and `...Ratio1`) and keeps only splits that the normalised series confirms: some value was restated by the same ratio (or a product of consecutive ratios). Duke's 0.8708 merger exchange ratio has no such evidence and is rejected with a note; Alphabet's 2014 class C dividend likewise. EPS and dividends per share are divided, share counts multiplied, by the cumulative ratio of confirmed splits dated after the filing the value comes from. Each adjusted value records `split_factor` and `value_before_split`, and appears as `split_adjusted` in the scorers' flags. Split dates are approximate (the latest announcement/effective instant, else the earliest period end) because they are only compared with 10-K filing dates. Disagreement between ratio facts and restatements becomes a series note; nothing is guessed.
**Trade-off:** A split that no 10-K ever restated would go unadjusted (and noted). Gains: all per-share history on today's basis with the evidence in the trace, no external split table to maintain.

### ADR-033 — Sector class from the SIC code until GICS is available
**Status:** Accepted · 2026-10-08
**Context:** ADR-013's exceptions need to know whether a company is a bank, insurer or utility. The GICS sector from the S&P 500 snapshot (ADR-014) is not built yet; the SEC SIC code is in every `submissions.json`.
**Decision:** `config/sector_rules.json` maps SIC ranges to bank (6021, 6022, 6029, 6035, 6036), insurer (6311-6411) and utility (4911, 4931, 4932, 4991), with a reason per rule; everything else is "other". The GICS sector will confirm or override this when the constituents snapshot is added.
**Trade-off:** SIC codes are coarse and company-chosen (a few insurers or utilities will be classed "other"). Gains: no dependency on a source we do not have yet, and the rule is reviewable data.

### ADR-034 — Edge-case rules in the scorers
**Status:** Accepted · 2026-10-08
**Decision:**
- **G4:** per-share dividends decide a year when the fact exists (a reported zero means unpaid); cash dividends paid are used only when per-share data is missing; neither means unpaid. This follows ADR-012's correction, where a one-off cash payment such as Alphabet's $47M in 2015 is not a dividend. A pass is a `partial_pass`, labelled "partial (15 of 20 yrs)" when the record covers all 15 years, else "N yrs on record". The source that decided each year is in the result.
- **G5:** a starting 3-year average EPS of zero or below is `not_meaningful` (averages shown, ratio withheld).
- **G6, G7:** with no price they are data gaps ("price not available (Finnhub, ADR-007)"). With a price, average EPS or book value per share of zero or below is a fail (no positive earnings or assets behind the price). P/E uses the 3-year average EPS in both. Book value per share is equity divided by split-adjusted diluted shares: a proxy, since EDGAR has no standard shares-outstanding concept in the map.
- **G2:** missing debt is a data gap, never "no debt". Utilities replace both tests with debt <= 2x equity.
- **B1:** ROE uses the average of opening and closing equity; any non-positive equity in the window is `not_meaningful`.
- **B2:** average net income of zero or below is a fail, with the figures shown.
- **B3:** the 10-year and 3-year margins are simple averages of yearly operating margins.
- **B4:** needs all 10 years of net income, D&A and capex, else a data gap listing the missing years. Years that use the depreciation-only fallback (ADR-030) are flagged.
**Trade-off:** Some choices are conservative (a gap rather than a guess; a fail for non-positive earnings). Gains: every label can be explained from the figures in the result without further assumptions.

### ADR-035 — 10-K text normalisation is the citation text
**Status:** Accepted · 2026-10-09
**Context:** The qualitative agent must quote the filing, and the Critic checks each quote verbatim against it (ADR-019). A raw 10-K is inline-XBRL HTML (2–16 MB) whose markup, hidden XBRL header, non-breaking spaces and curly quotes would make "verbatim" depend on the parser.
**Decision:** `engine/filing_text.py` converts the HTML to plain text with the standard library's `html.parser`, deterministically: script, style and hidden inline-XBRL blocks (`ix:header`, `display:none`) are dropped; block elements become line breaks; a table row becomes one line with its non-empty cells joined by " | "; whitespace is collapsed; non-breaking spaces and curly quotes become plain ones. This text is THE citation text: every section and passage offset, and every quote, refers to it. It is cached under `data/cache/sections/` keyed by the document's SHA-256 and a text-format version (git-ignored, rebuilt on demand). The largest filing (Duke, 16 MB) converts in about a second.
**Trade-off:** Quotes are of the normalised text, so a quote differs from the printed filing in whitespace, quote marks and table layout; the passage id, accession and offsets still locate it exactly. Gains: one reproducible text for retrieval, citation and verification.

### ADR-036 — Section extraction: longest candidate, title fallback, explicit not_found
**Status:** Accepted · 2026-10-09
**Context:** Items 1 (Business), 1A (Risk Factors) and 7 (MD&A) are the qualitative agent's evidence. Their headings appear twice (table of contents and body), differ in format (`ITEM 1A.RISK FACTORS`, `Item 1. | Business | 2`, `Items 1 and 2`) and some banks keep a cross-reference stub in Item 7 with the real MD&A elsewhere (JPMorgan: a 396-character stub; the MD&A follows the Item 15 index under repeating page headers).
**Decision:** `engine/sections.py` finds heading lines (`Item N`, including combined `Items 1 and 2`) and ends each section at the next heading of the following items (1: 1A/1B/1C/2; 1A: 1B/1C/2; 7: 7A/8). The candidate with the longest section wins (a table of contents entry is a few characters long) and must be at least 2,000 characters. Failing that, the section title alone on a line is tried the same way, ending at the next item heading or the auditor's report, and recorded as `method: title_fallback`. If nothing qualifies the section is `not_found` with a reason that states the longest candidates; nothing is guessed. Each section records status, method, offsets, length, accession and the document's SHA-256. All 15 test sections are found (JPMorgan's Item 7 by the fallback).
**Alternative considered:** the `edgartools` library already extracts sections. Rejected: a large dependency, heading rules we could not explain line by line, and no citation offsets into our own normalised text.
**Trade-off:** Heuristics tuned on five filings will meet layouts they cannot parse; the explicit `not_found` (and the sections report) make that visible instead of silently returning a table of contents. A long candidate that is really a different part (e.g. JPMorgan's 405,000-character MD&A) is accepted as the filing presents it.

### ADR-037 — Passages, BM25 retrieval and search terms as config
**Status:** Accepted · 2026-10-09
**Context:** ADR-022 chose keyword search over three sections; it needs citable units and a ranking.
**Decision:** Each section is cut at paragraph boundaries into passages: short paragraphs are merged up to about 200 words, paragraphs over 350 words are split at sentence ends, tables count as paragraphs. `passage_id = "{accession}:{item}:{n}"`, and each passage stores its offsets so `document_text[start:end] == passage.text` exactly. `engine/retrieve.py` ranks passages with a small pure-Python BM25 (k1 = 1.5, b = 0.75; lowercase alphanumeric tokens, a short stopword list, a trailing plural "s" stripped, no stemming library). The agent's tools are `search(cik, query, items, k)` and `get_passage(passage_id)`, returning plain Pydantic objects with scores and matched terms for the trace. `config/search_terms.json` gives, per qualitative Buffett criterion, the items to search first and starting queries, with a reason each; the agent may rephrase.
**Trade-off:** Keyword search misses synonyms and rewards passages that mention many generic terms (see `docs/sections_report.md`: e.g. a receivables-factoring paragraph tops Coca-Cola's capital-allocation search). The starting queries are a baseline to evaluate, not tuned to make particular companies look good. ADR-022's upgrade path (a small local embedding model) stays open if the evaluation shows missed evidence.

### ADR-038 — LLM record/replay, the same pattern as the SEC data
**Status:** Accepted · 2026-10-09
**Context:** Development, tests and the evaluation harness must not spend quota or depend on the network (ADR-025 for SEC data), and LLM output must be reproducible for the trace replay.
**Decision:** Every request is canonicalised (profile, model, messages, tools, response format, temperature, max tokens; never the API key or headers), hashed with SHA-256 and stored through `ResponseStore` as the provider's response plus the request and original latency: in `fixtures/llm/` (committed) for `record`, in `data/cache/llm/` (git-ignored) for `live`. `replay` (the default for tests) serves fixtures only and raises `LLMFixtureMissing` on a miss; it never touches the network and never writes the ledger. Temperature defaults to 0. The key is read from the environment only and redacted from errors; tests scan fixtures, traces and the ledger for it. Every call yields an `LLMCall` (tokens including thinking tokens, latency, actual and notional cost, replayed flag, the raw assistant message) and an automatic `llm_call` trace event. `complete_json` asks for JSON mode, validates against a Pydantic model and makes one repair attempt with the error; tool calls are returned in a provider-neutral shape.
**Trade-off:** A fixture only matches the exact same request, so changing a prompt means re-recording (a few free-tier requests). Gains: free, deterministic, offline tests of everything that uses the model. Found while recording: Gemini attaches `extra_content` (thought signatures) to tool calls and messages; the client keeps the raw assistant message so the agent loop can append it unchanged.

### ADR-039 — Budget guard and run ledger: Pacific-day quota, safety margin, paid-mode switch, caps
**Status:** Accepted · 2026-10-09
**Context:** ADR-023 caps spending at $4 under a $5 Google cap and uses the free tier first. The free tier limits requests per minute and per day, and Google resets the daily count at midnight Pacific time.
**Decision:** `data/ledger/usage.json` (git-ignored) holds requests per profile per Pacific day, the last request time, total spend, notional spend and spend per company, so separate runs share them. Before every request (including retries, since every attempt counts against the quota) the guard (a) sleeps to stay under the profile's requests per minute, (b) refuses with `QuotaReached` ("resume after midnight Pacific") once today's count reaches the daily limit minus a margin of 10, and (c) allows a paid call beyond that only if `PAID_MODE_ENABLED=true` and the projected cost (prompt characters / 4 at the input price plus max tokens at the output price) keeps total spend under the $4.00 engine cap and the company under its $0.05 cap (all in `config/models.json`); otherwise `BudgetExceeded`. Calls inside the free quota are free even in paid mode. A 429 whose body names a daily quota stops the batch cleanly and marks the day exhausted in the ledger; per-minute 429s and 5xx errors retry with backoff (2, 4, 8 s; `Retry-After` honoured); a 400 is not retried. Each call records two costs: **actual** (money spent: zero on the free tier and for replays) and **notional** (tokens x the paid price), both shown in the demo.
**Trade-off:** Tokens per minute are not paced (requests per minute is the binding limit at our prompt sizes) and the cost projection is rough, so a paid call can overshoot its projection slightly; the $4 cap sits under Google's $5 cap for that reason. Gains: a hard, explainable ceiling and a batch that stops and resumes cleanly.

### ADR-040 — Provider-agnostic client over OpenAI-compatible HTTP, with model profiles
**Status:** Accepted · 2026-10-09
**Context:** ADR-015 wants the model to be one config setting, with Gemini for runs, hosted Gemma for comparison and a local model for smoke tests.
**Decision:** `config/models.json` defines named profiles (base URL, model id, key variable name, paid prices, free-tier limits, and a source-and-date note); `LLM_PROFILE` in `.env` selects one, default `gemini-3.1-flash-lite`. The client speaks the OpenAI chat-completions protocol with `urllib` (no SDK), which Gemini, Ollama and most hosts accept. Model ids were checked against the provider's `/models` endpoint on 2026-10-09 (`gemini-3.1-flash-lite`, `gemma-4-31b-it`); JSON mode and tool calling (including the tool-result round trip) were confirmed on the free tier. Profiles `gemma-4-31b` and `ollama-local` are configuration only for now.
**Trade-off:** We re-implement a thin slice of what an SDK provides (retries, usage parsing) and depend on each provider's OpenAI-compatibility being faithful, e.g. Gemini's thought signatures. Gains: no new dependency, the whole client is readable in one sitting, and swapping models is a config change.

---

## Open questions
- Which companies form the featured set for the demo script (test tickers in ADR-024 are candidates).
- Whether to include a neutral scatter view of both rankings.
