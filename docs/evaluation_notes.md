# Evaluation notes: what the tool gets wrong

Start of the honest list of known weaknesses, found while reviewing the scores of the 5 test companies (`docs/scorecard_report.md`, frozen in `eval/expected_scores.json`). Each item: what, why, impact, planned handling. Research output, not financial advice.

## 1. Known false positive: Alphabet G4 counts 2015 as "paid"
- **What:** G4 marks GOOGL's 2015 as a dividend year.
- **Why:** There is no per-share fact for 2015, so ADR-012 falls back to cash dividends paid, and Alphabet's $47M in the cash tag was a one-off non-dividend payment.
- **Impact:** None on the result (G4 still fails; most other years are unpaid). The same pattern could flatter another company.
- **Handling:** Rule kept as written; the deciding source is shown per year in the result. Revisit with a plausibility check (cash paid vs. share count) if it shows up in the full S&P 500 run.

## 2. G5 is sensitive to one-off years
- **What:** The 3-year starting average includes the 2017 tax-reform charge (KO EPS 0.29 against 1.49 and 1.50 either side).
- **Why:** G5 compares 3-year averages at the two ends of the window, so one unusual year moves the start average.
- **Impact:** The averages show it does not change KO or GOOGL: excluding 2017, KO's ratio goes from 2.43 to 1.78 and GOOGL's from 5.51 to 4.59, both well above the 1.33 threshold. A company closer to 1.33 could flip.
- **Handling:** Rule kept as written. Show the three yearly EPS values in the result (`by_year`, planned); flag results within ~15% of the threshold in the evaluation.

## 3. JPM B1 uses total equity, including preferred stock
- **What:** ROE is net income over average `StockholdersEquity`, which includes preferred shares.
- **Why:** The concept map has no common-equity measure, and preferred dividends are not deducted from net income here.
- **Impact:** ROE is understated for a bank with preferred stock. Rough estimate, not computed by the tool (preferred is about 7–10% of JPM's equity): about 5 of 10 years would reach 15% instead of 4, still below the 7 required, so the fail should stand.
- **Handling:** Documented limitation. A common-equity measure (equity minus preferred, net income available to common) is a candidate normaliser addition.

## 4. Borderline results: Alphabet G2
- **What:** GOOGL passes G2 with a current ratio of 2.005 against the threshold of 2.
- **Why:** The threshold is a hard cut-off; the figure is within 0.3% of it.
- **Impact:** A small restatement or a different long-term debt tag could flip the label.
- **Handling:** The figure is in the result so the margin is visible. Add a "within x% of threshold" flag to the evaluation harness.

## 5. DUK B4: negative owner earnings in every year
- **What:** Duke's net income + D&A − capex is negative in all 10 years (−$0.1B to −$3.7B).
- **Why:** A regulated utility invests more than it earns plus depreciates, funded by debt and rate-base recovery; B4 treats total capex as maintenance capex (PROCESS §5).
- **Impact:** The criterion measures a different thing for capital-heavy utilities, so the fail says little about business quality.
- **Handling:** Result stands (consistent with ADR-024's expectation). Consider a utility exception for B4 in a later ADR; for now the explanation must say it is an industry mismatch.

## 6. Risk: `SalesRevenueGoodsNet` can be partial revenue
- **What:** It is the last fallback in the revenue concept map. For some companies it is a component of revenue (Tesla's automotive sales are tagged this way).
- **Why:** It was added so KO's 2007–2017 revenue fills in; the map cannot tell a total from a component.
- **Impact:** None on the 5 test companies (it never wins a year there). For another company with a revenue gap it could fill the year with a partial figure and distort G1 and B3.
- **Handling:** Review before the full S&P 500 run: list every company and year where it is the chosen concept and compare with the total.

## 7. Qualitative: "candid management" was "found" for all five companies — partly fixed in v1.1
- **Before (7af5412):** KO, JPM, GOOGL, TSLA and DUK all "found", on routine MD&A variance text (KO's North America unit case volume down 1%, TSLA's automotive revenue down 9%, JPM's card income down). The rubric accepted "a named decline with a figure", which measures disclosure, not candour.
- **Change (ADR-047):** "found" now needs management's own account of a setback it attributes at least partly to its own decisions or execution, a missed target or guidance, or a plainly stated material weakness, restatement or write-down of something it chose; declines explained only by external factors are "weak". New queries; the rationale must say that a 10-K is a limited guide to candour.
- **After (v1.1 recording):** KO insufficient, JPM insufficient, GOOGL found, TSLA found, DUK weak. The criterion now discriminates (2 found, 1 weak, 2 insufficient), but I doubt both "found": GOOGL's rests on the Item 1A sentence that its devices "have had, and in the future may have, quality issues" (a risk-factor admission, not an account of a particular setback or its cause), and TSLA's on "our guidance ... has in the past been inaccurate in certain respects, such as the timing of new product manufacturing ramps" (a real admission of missed guidance, but one generic sentence in the risk factors). The rubric allows both; whether it should is for review. Duke's "weak" (progress toward net zero "will not be linear") is a hedge, not a setback.
- **Still open:** the strongest cases in the filings (Alphabet's quantified EC fine and legal accrual, Duke's named impairments) are external-cause or litigation items and so fall under "weak" by the new rule; the agent did not cite them. Candour is better judged from shareholder letters (outside v1).

## 8. Qualitative: "durable competitive advantage" could be "found" on the company's own assertion — fixed in v1.1
- **Before:** KO "found" on a statement that its formulas are important trade secrets; no figure, and the rationale itself said competitors could erode the position.
- **Change (ADR-047):** "found" needs a checkable specific (share or rank figure, regulated exclusive franchise, quantified scale or cost position, long-term contracts with terms, network size); an asset that exists or matters without a measure is "weak"; text that argues against the criterion is "insufficient evidence".
- **After:** KO found, now on a figure (its trademarked beverages account for 2.2 billion of the estimated 65 billion beverage servings consumed worldwide every day: a share-type measure); JPM insufficient (cites total assets and equity, calls "leading" promotional); GOOGL insufficient (cites trade secrets and the Item 1 statement that users are "one click away", i.e. argues against); TSLA weak ("we believe ... give us a competitive advantage"); DUK found (sole supplier within its service territories, rates set by commissions: a regulated franchise). All five read as the rubric intends.

## 9. Qualitative: rationales say more than the quotes show
- **What:** Several rationales add claims that are not in their quotes: JPM capital allocation ("factors management considers when determining share repurchases"), TSLA capital allocation ("may choose to repay debt early"), KO durable advantage ("could be eroded by competitors or changes in law"). TSLA's capital allocation "found" rests on one forward-looking capex statement and no past action.
- **Why:** The agent checks quotes, not rationales; the rationale is free text limited to under 80 words.
- **Impact:** A reader may take the rationale as supported by the citation when it is only partly.
- **Handling:** The Critic's LLM check should compare rationale and quote; consider asking for the rationale to restate only what the quotes contain.
- **Update (v1.1, kept open as the Critic's test case):** the new rule that the rationale may state only what the cited sentences show did not remove the pattern. JPM capital allocation is "found" although the cited sentences name repurchases and dividends without amounts, which the rubric calls weak (and the rationale adds the governance framework and decision factors); DUK capital allocation's rationale mentions "concrete figures" for capital expenditures and debt repayment while the citations show only dividends paid. No code guard has been added on purpose.

## 10. Qualitative: findings lost to the citation check (mechanical, not about the company) — fixed in v1.1
- **Before:** 5 of 20 findings ended `invalid_citation` and showed "insufficient evidence" (KO and DUK capital allocation; Alphabet understandable business, durable advantage and capital allocation). In the traces 4 of 5 rejected quotes ran past a bullet ("•") or line break inside the passage and one was 63 words; the model spliced non-adjacent sentences, dropped bullet or table characters, or added a full stop, and often resubmitted the same text after feedback. Three recordings with prompt tweaks gave 5, 4, 5 such findings.
- **Change (ADR-046):** the model no longer types quotes. Passages are shown as numbered sentences and it cites `{passage_id, first, last}`; code builds the quote and offsets. The "insufficient evidence" label was also split (ADR-047): code-assigned "not assessed" now marks "the system could not judge", leaving "insufficient evidence" to mean "the filing, as retrieved, does not show it".
- **After:** 0 of 20 findings `invalid_citation`, 0 "not assessed", mean 7.0 model calls and 938 output tokens per company (from 1,287). Cost of the approach: a cited span can carry bullet fragments or a clause the model did not choose (e.g. Alphabet's understandable-business citation opens with a "•Brand advertising helps ..." sentence that says little about how the company earns money).

## 11. Qualitative: retrieval observations and what is not yet measured
- **Retrieval:** The seeded search for "understandable business" is limited to Item 1, and JPM's cited segment descriptions came from Item 7 after the model's own search. For banks, Item 1 is a general overview. The model rescued it; a fixed search would not have. `get_passage` was never used (full passage text arrives with every search). Retrieval has no recall measure yet (STATUS Next #2).
- **Variability (history):** before v1.1, one recording per prompt. Three recordings with small prompt changes moved several verdicts (e.g. Duke capital allocation found, then insufficient; JPM durable advantage weak, then insufficient), so run-to-run noise is likely sizeable. A repeat run at temperature 0 on the same prompt would show how much comes from the API itself.
- **Handling:** Do not freeze verdicts in `eval/` until reviewed; measure repeat-run variability on the 5 tickers (free tier, about 35 requests) as part of the evaluation harness.
- **Variability measured (v1.1, `docs/qualitative_variability.md`):** two extra live runs of the 5 tickers at temperature 0 with the response store bypassed (70 requests, actual $0.00) gave verdicts identical to the recorded run in 20 of 20 findings, the same cited passages in all 20, and identical token counts. So the API is reproducible for identical prompts. This does not make the labels stable: small prompt or rubric changes did move verdicts (above), so the real sensitivity is to wording, not to API noise. A fair robustness test would rephrase the prompt or rubric slightly and compare.
- **New observation:** the segmenter over-splits bullets and table rows, so some citations are fragments ("•the impact of capital actions, including ...", "Dividends paid | (3,300) | ..."); legible but thin.

