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
