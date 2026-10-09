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

## 7. Qualitative: "candid management" is "found" for all five companies
- **What:** KO, JPM, GOOGL, TSLA and DUK all get "evidence found" (`docs/qualitative_report.md`). The evidence is routine MD&A variance text: KO's North America unit case volume down 1%, TSLA's automotive revenue down 9%, JPM's card income down.
- **Why:** The rubric (`found_means`) accepts "a named decline with a figure"; every company reports declines. That measures disclosure, not candour (no admitted mistake, missed target or responsibility).
- **Impact:** The criterion does not discriminate between companies, so a "found" says little. The strongest case is Alphabet (the EC fine and a legal accrual, quantified) and Duke (impairments it names), which the same label does not separate from KO.
- **Handling:** Tighten the rubric to require management's own account of a setback (impairment, charge, missed target, restructuring, a stated cause that is the company's own), then re-record and re-review. Not done here: verdicts are for Daniel to review first (ADR-043).

## 8. Qualitative: "durable competitive advantage" can be "found" on the company's own assertion
- **What:** KO is "found" on the statement that its formulas are important trade secrets. There is no figure, share or rank, and the rationale itself adds that the filing says competitors or changes in law could erode the position.
- **Why:** The rubric says marketing language is a claim, and the model still counted a confident statement as a specific. A small model applies the found/weak line loosely.
- **Impact:** At least one "found" that the rubric's own rule would call "weak". By contrast TSLA's "weak" (a "we believe ... give us a competitive advantage" sentence), JPM's "insufficient" and DUK's "found" (sole supplier within service territories, a regulated franchise) read as the rubric intends.
- **Handling:** Review with the other verdicts; the Critic's "does the quote support the verdict" check (ADR-010) is meant to catch this. Consider requiring that a "found" quote contain a number or a named asset.

## 9. Qualitative: rationales say more than the quotes show
- **What:** Several rationales add claims that are not in their quotes: JPM capital allocation ("factors management considers when determining share repurchases"), TSLA capital allocation ("may choose to repay debt early"), KO durable advantage ("could be eroded by competitors or changes in law"). TSLA's capital allocation "found" rests on one forward-looking capex statement and no past action.
- **Why:** The agent checks quotes, not rationales; the rationale is free text limited to under 80 words.
- **Impact:** A reader may take the rationale as supported by the citation when it is only partly.
- **Handling:** The Critic's LLM check should compare rationale and quote; consider asking for the rationale to restate only what the quotes contain.

## 10. Qualitative: findings lost to the citation check (mechanical, not about the company)
- **What:** 5 of 20 findings ended `invalid_citation` and show "insufficient evidence": KO and DUK capital allocation, and Alphabet understandable business, durable advantage and capital allocation. Alphabet is 3 of 4 insufficient.
- **Why:** The model's quotes splice non-adjacent sentences, drop bullet or table characters, or add a full stop the filing lacks, and after the rejection message it resubmitted the same text in several cases. Alphabet's text is bullet- and table-heavy. 13 submissions were rejected across 8 of the 20 loops.
- **Impact:** For these the label is "the agent could not cite", not "the filing shows nothing". `stop_reason` keeps the two apart, and the site must show it, not just the label.
- **Handling:** Rejected quotes and the model's intended verdict are in the trace (not in the report). Options: quote selection by sentence id instead of free text; a stronger model; compare with Gemma 4 31B (STATUS Next #6). More prompting is unlikely to help (three recordings: 5, 4, 5 such findings).

## 11. Qualitative: retrieval observations and what is not yet measured
- **Retrieval:** The seeded search for "understandable business" is limited to Item 1, and JPM's cited segment descriptions came from Item 7 after the model's own search. For banks, Item 1 is a general overview. The model rescued it; a fixed search would not have. `get_passage` was never used (full passage text arrives with every search). Retrieval has no recall measure yet (STATUS Next #2).
- **Variability not measured:** one recording per prompt. Three recordings with small prompt changes moved several verdicts (e.g. Duke capital allocation found, then insufficient; JPM durable advantage weak, then insufficient), so run-to-run noise is likely sizeable. A repeat run at temperature 0 on the same prompt would show how much comes from the API itself.
- **Handling:** Do not freeze verdicts in `eval/` until reviewed; measure repeat-run variability on the 5 tickers (free tier, about 35 requests) as part of the evaluation harness.

