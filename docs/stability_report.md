# Prompt-perturbation stability (build 4a, ADR-072)

Research output, not financial advice. The qualitative agent and the Critic were run three times on the same 10-K: with the rubric as written (main, prompt v2.1) and with the question and the three verdict definitions reworded twice, keeping their meaning (`config/qualitative_paraphrases.json`, variants A and B). A finding is **stable** when the assessed verdicts of the three runs are equal and **borderline** when any differ. A verdict of "not assessed" is kept in the record but is not a judgement, so it does not count towards the status; a finding with fewer than two assessed verdicts has no status. Items, search queries, the year rule and the rationale note are identical in all three runs. Variant runs reuse the main run's numeric explanations and run live (their results are in `results/stability/{a,b}/`, run ids `<SYMBOL>-live-a` and `-b`); they do not replace the main results.

## Runs

| Run | Companies | Model calls | Input tokens | Output tokens | Notional cost |
|---|---|---|---|---|---|
| main (v2.1) | 25 | 274 | 703,974 | 59,136 | $0.265 |
| paraphrase A | 25 | 227 | 571,773 | 44,728 | $0.210 |
| paraphrase B | 5 | 47 | 126,111 | 8,704 | $0.045 |

## Flip rate

5 of 25 companies have all three runs (KO, JPM, GOOGL, TSLA, DUK); variant B stops at the free-tier daily limit and continues after midnight Pacific with `scripts/stability_run.py b`, after which this report is regenerated. 20 findings from them; 20 have a status (0 do not: fewer than two assessed verdicts). **8 of 20 are borderline (40%).** Of the borderline findings, 6 move one level (found, weak and insufficient are the levels) and 2 move two levels between runs.

| Criterion | Findings | Borderline | Flip rate |
|---|---|---|---|
| Understandable business | 5 | 0 | 0% |
| Durable competitive advantage | 5 | 2 | 40% |
| Candid management | 5 | 5 | 100% |
| Rational capital allocation | 5 | 1 | 20% |

Pairwise: how often two runs give different verdicts for the same finding (findings both assessed).

| Pair | Compared | Different |
|---|---|---|
| main vs A | 20 | 5 (25%) |
| main vs B | 20 | 5 (25%) |
| A vs B | 20 | 6 (30%) |

**Main against paraphrase A over all 25 companies** (the two runs that exist everywhere): 22 of 94 findings differ (23%).

| Criterion | Compared | Different |
|---|---|---|
| Understandable business | 22 | 0 (0%) |
| Durable competitive advantage | 25 | 7 (28%) |
| Candid management | 25 | 13 (52%) |
| Rational capital allocation | 22 | 2 (9%) |

Verdicts of "not assessed" across the three runs: 0 of 60.

## Borderline findings

| Company | Criterion | Main | A | B |
|---|---|---|---|---|
| KO | Durable competitive advantage | weak | found | found |
| KO | Candid management | found | insufficient | found |
| JPM | Candid management | insufficient | insufficient | weak |
| GOOGL | Durable competitive advantage | weak | insufficient | weak |
| GOOGL | Candid management | weak | insufficient | insufficient |
| TSLA | Candid management | weak | found | weak |
| TSLA | Rational capital allocation | found | found | insufficient |
| DUK | Candid management | weak | weak | insufficient |

## Are the dev-set disagreements the borderline findings?

The 20 dev findings (KO, JPM, GOOGL, TSLA, DUK) against the human labels (final main verdict, after the Critic's repairs). Small numbers: read the counts, not the p-value.

| | Disagrees with the human label | Agrees |
|---|---|---|
| Borderline | 5 | 3 |
| Stable | 0 | 12 |

- Disagreement rate among borderline findings: 62%; among stable findings: 0%.
- Share of the disagreements that are borderline: 100%.
- Phi coefficient: 0.71; one-sided Fisher exact p = 0.004. Findings without a status: 0.

| Dev disagreement | Main | A | B | Status |
|---|---|---|---|---|
| KO Durable competitive advantage (human: found) | weak | found | found | borderline |
| KO Candid management (human: insufficient) | found | insufficient | found | borderline |
| GOOGL Durable competitive advantage (human: insufficient) | weak | insufficient | weak | borderline |
| TSLA Candid management (human: found) | weak | found | weak | borderline |
| TSLA Rational capital allocation (human: weak) | found | found | insufficient | borderline |

## Criterion reliability

A criterion whose flip rate (findings whose verdict changed, of those with at least two assessed verdicts) is at or above 30% (`config/reliability.json`) is marked reliability low in every result and on the company page.

| Criterion | Compared | Changed | Flip rate | Marked |
|---|---|---|---|---|
| Understandable business | 5 | 0 | 0% | no |
| Durable competitive advantage | 5 | 2 | 40% | low reliability |
| Candid management | 5 | 5 | 100% | low reliability |
| Rational capital allocation | 5 | 1 | 20% | no |

The six differences under prompt v2 (ADR-069), looked up in these runs:

| v2 difference | Main (v2.1) | A | B | Status |
|---|---|---|---|---|
| KO Durable competitive advantage | weak | found | found | borderline |
| JPM Candid management | insufficient | insufficient | weak | borderline |
| GOOGL Durable competitive advantage | weak | insufficient | weak | borderline |
| GOOGL Candid management | weak | insufficient | insufficient | borderline |
| TSLA Rational capital allocation | found | found | insufficient | borderline |
| DUK Candid management | weak | weak | insufficient | borderline |

## The paraphrases

Main wording is `config/search_terms.json`. Review that the meaning is the same in all three.

### Understandable business

**Question**

- Main: Can the business be explained simply: what the company sells, to whom, and how it makes money?
- A: Is it possible to describe the company's business in plain words: what it sells, who buys it, and how it earns its money?
- B: Does the filing let a reader explain the business simply, covering what the company sells, who it sells to, and where its revenue comes from?

**Found means**

- Main: The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- A: The filing identifies particular products or services, says which customers or markets buy them, and explains how revenue arises (for instance segments with figures, or a pricing or sales model), in everyday language.
- B: Specific products or services are named, the customers or markets they serve are identified, and the way revenue is earned is described (for example segment figures, or a pricing or sales model), all in plain terms.

**Weak means**

- Main: The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- A: The business is described only in broad or promotional language (such as 'a leading provider of solutions'), or the filing says what the company sells but not who the buyers are or how the company makes money.
- B: The description is general or promotional ('a leading provider of solutions'), or the filing states what is sold without saying who buys it or how revenue is earned.

**Insufficient means**

- Main: The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- A: The retrieved text does not state what the company sells or how it makes money, or the Business section is missing. If the retrieved text points against the criterion, this is the verdict, and the rationale says so.
- B: Nothing in the retrieved text says what the company sells or how it earns revenue, or the Business section is absent. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

### Durable competitive advantage

**Question**

- Main: Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?
- A: Does the filing offer concrete evidence of an advantage that shields the company's profits from competitors for many years (such as a brand, a scale or cost position, switching costs, a network, patents or a regulated franchise)?
- B: Is there concrete evidence in the filing of a lasting advantage that keeps competitors from eroding the company's profits (for example a brand, a scale or cost position, switching costs, a network, patents, or a regulated franchise)?

**Found means**

- Main: The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- A: The filing names a source of advantage AND gives a checkable specific for it: a market share or ranking figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated size of network. Merely saying that an asset exists or is important (brand, trade secrets, patents, 'strong' distribution), with no measure, is not enough.
- B: A source of advantage is stated AND backed by a checkable specific: a market share or rank; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. Saying that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure does not count.

**Weak means**

- Main: The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- A: The advantage is merely claimed, or an asset such as a brand, trade secrets, patents or scale is called important without any measure; or the filing's own statements that competitors or customers can readily erode the position offset the specifics.
- B: The advantage is only asserted, or an asset (brand, trade secrets, patents, scale) is described as important but not measured; or the filing itself says competitors or customers can readily wear the position down, offsetting the specifics.

**Insufficient means**

- Main: The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- A: The retrieved text is silent on the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text points against the criterion, this is the verdict, and the rationale says so.
- B: The retrieved text does not discuss the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

### Candid management

**Question**

- Main: Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?
- A: Does management talk openly, in its own words, about setbacks, mistakes, declines and uncertainty, and not only about successes?
- B: Is management open, in its own words, about setbacks, mistakes, declines and uncertainty, rather than describing only successes?

**Found means**

- Main: Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- A: Management's own account of a setback that it blames at least in part on the company's own decisions or execution; or a target or guidance of the company's own that was missed; or an acknowledged material weakness, restatement or write-down of something management itself chose (an acquisition, investment or project), stated plainly.
- B: Management itself describes a setback and attributes it at least partly to the company's own decisions or execution; or reports a target or guidance of its own that was missed; or acknowledges a material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.

**Weak means**

- Main: Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- A: Declines or charges attributed solely to outside factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or general words of caution ('results may fluctuate', 'we face risks'); or a setback that is mentioned but not explained.
- B: Declines or charges are explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even if quantified; or the caution is generic ('results may fluctuate', 'we face risks'); or a setback is noted without any explanation.

**Insufficient means**

- Main: The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- A: The retrieved text is promotional or boilerplate and offers nothing from which to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text points against the criterion, this is the verdict, and the rationale says so.
- B: The retrieved text is promotional or boilerplate and gives no basis for judging candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

### Rational capital allocation

**Question**

- Main: Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.
- A: Does the filing show how management uses the cash the business produces (reinvestment, acquisitions, buybacks, dividends, repaying debt) and explain its approach? You judge whether this is documented concretely, not whether the prices paid were good.
- B: Does the filing document what management does with the cash the business generates (reinvesting, acquisitions, buybacks, dividends, repaying debt) and say why? The test is whether this is concretely documented, not whether the prices paid were good.

**Found means**

- Main: The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- A: The filing puts an amount on at least one action taken in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- B: At least one action in the fiscal year is quantified (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount), AND the filing states a policy, priority or rationale for how cash is used. Not every action needs an amount.

**Weak means**

- Main: Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- A: Only forward-looking plans; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- B: Forward-looking plans only; or actions without any amount; or amounts without a stated policy, priority or rationale.

**Insufficient means**

- Main: The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- A: The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text points against the criterion, this is the verdict, and the rationale says so.
- B: Nothing in the retrieved text says what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

