"""Write docs/stability_report.md from the main results and results/stability/{a,b}/ (build 4a, ADR-072). Offline; --attach also writes `stability` onto the main results.

    .venv/bin/python scripts/stability_report.py [--attach]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.agreement import load_human_dev  # noqa: E402
from engine.agents.qualitative import load_criteria  # noqa: E402
from engine.contracts import QUAL_CRITERIA  # noqa: E402
from engine.settings import REPO_ROOT  # noqa: E402
from engine.stability import FIELDS, STABILITY_DIR, attach, collect, dev_correlation, flip_stats, load_paraphrases, load_threshold, criterion_stats, stability_for, pair_flips  # noqa: E402
from engine.universe import load_universe  # noqa: E402

OUT = REPO_ROOT / "docs" / "stability_report.md"
SHORT = {"evidence found": "found", "evidence weak": "weak", "insufficient evidence": "insufficient", "not assessed": "not assessed"}
TITLE = {"understandable_business": "Understandable business", "durable_competitive_advantage": "Durable competitive advantage", "candid_management": "Candid management",
         "rational_capital_allocation": "Rational capital allocation"}
FIELD = {"question": "Question", "found_means": "Found means", "weak_means": "Weak means", "insufficient_means": "Insufficient means"}


PAIR = {"main_vs_a": "main vs A", "main_vs_b": "main vs B", "a_vs_b": "A vs B"}
# the six differences between the agent and the human labels under prompt v2 (ADR-069): the question asked of build 4a is whether they are the borderline findings
V2_DISAGREEMENTS = [("KO", "durable_competitive_advantage"), ("JPM", "candid_management"), ("GOOGL", "durable_competitive_advantage"), ("GOOGL", "candid_management"),
                    ("TSLA", "rational_capital_allocation"), ("DUK", "candid_management")]


def pct(x) -> str:
    return "n/a" if x is None else f"{x:.0%}"


def runs_table(companies) -> list[str]:
    rows = []
    for label, base in (("main (v2.1)", REPO_ROOT / "results"), ("paraphrase A", STABILITY_DIR / "a"), ("paraphrase B", STABILITY_DIR / "b")):
        n = calls = tin = tout = 0
        notional = 0.0
        for _, cik in companies:
            p = base / f"{cik}.json"
            if p.exists():
                c = json.loads(p.read_text())["cost"]
                n, calls, tin, tout, notional = n + 1, calls + c["llm_calls"], tin + c["input_tokens"], tout + c["output_tokens"], notional + c["notional_cost_usd"]
        rows.append(f"| {label} | {n} | {calls} | {tin:,} | {tout:,} | ${notional:.3f} |")
    return ["| Run | Companies | Model calls | Input tokens | Output tokens | Notional cost |", "|---|---|---|---|---|---|"] + rows


def render(companies) -> str:
    rows = collect(companies)
    st = flip_stats(rows)
    human = load_human_dev()
    dev_rows = [r for r in rows if r["ticker"] in human]
    corr = dev_correlation(dev_rows, human)
    phi = "n/a" if corr["phi"] is None else format(corr["phi"], ".2f")
    main_c, para = load_criteria(), load_paraphrases()
    L = ["# Prompt-perturbation stability (build 4a, ADR-072)", "",
         "Research output, not financial advice. The qualitative agent and the Critic were run three times on the same 10-K: with the rubric as written (main, prompt v2.1) and with the question and the "
         "three verdict definitions reworded twice, keeping their meaning (`config/qualitative_paraphrases.json`, variants A and B). A finding is **stable** when the assessed verdicts "
         "of the three runs are equal and **borderline** when any differ. A verdict of \"not assessed\" is kept in the record but is not a judgement, so it does not count towards the status; "
         "a finding with fewer than two assessed verdicts has no status. Items, search queries, the year rule and the rationale note are identical in all three runs. Variant runs reuse the main "
         "run's numeric explanations and run live (their results are in `results/stability/{a,b}/`, run ids `<SYMBOL>-live-a` and `-b`); they do not replace the main results.", "",
         "## Runs", ""] + runs_table(companies) + [""]
    covered = sorted({r["ticker"] for r in rows}, key=lambda t: [x for x, _ in companies].index(t))
    L += ["## Flip rate", "",
          f"{len(covered)} of {len(companies)} companies have all three runs ({', '.join(covered)})"
          + ("" if len(covered) == len(companies) else "; variant B stops at the free-tier daily limit and continues after midnight Pacific with `scripts/stability_run.py b`, after which this report is regenerated") + ". "
          f"{st['findings']} findings from them; {st['judged']} have a status ({st['not_judged']} do not: fewer than two assessed verdicts). "
          f"**{st['overall']['borderline']} of {st['overall']['n']} are borderline ({pct(st['overall']['rate'])}).** Of the borderline findings, {st['spread']['one_level']} move one level "
          f"(found, weak and insufficient are the levels) and {st['spread']['two_levels']} move two levels between runs.", "",
          "| Criterion | Findings | Borderline | Flip rate |", "|---|---|---|---|"]
    L += [f"| {TITLE[c]} | {v['n']} | {v['borderline']} | {pct(v['rate'])} |" for c, v in st["per_criterion"].items()]
    L += ["", "Pairwise: how often two runs give different verdicts for the same finding (findings both assessed).", "", "| Pair | Compared | Different |", "|---|---|---|"]
    L += [f"| {PAIR[k]} | {v['n']} | {v['differ']} ({pct(v['differ'] / v['n'] if v['n'] else None)}) |" for k, v in st["pairs"].items()]
    ma = pair_flips(companies, "main", "a")
    L += ["", f"**Main against paraphrase A over all {ma['companies']} companies** (the two runs that exist everywhere): {ma['differ']} of {ma['n']} findings differ ({pct(ma['differ'] / ma['n'] if ma['n'] else None)}).", "",
          "| Criterion | Compared | Different |", "|---|---|---|"]
    L += [f"| {TITLE[c]} | {v['n']} | {v['differ']} ({pct(v['differ'] / v['n'] if v['n'] else None)}) |" for c, v in ma["per_criterion"].items()]
    L += ["", f"Verdicts of \"not assessed\" across the three runs: {st['not_assessed_verdicts']} of {st['findings'] * 3}.", ""]
    L += ["## Borderline findings", "", "| Company | Criterion | Main | A | B |", "|---|---|---|---|---|"]
    L += [f"| {r['ticker']} | {TITLE[r['criterion']]} | " + " | ".join(SHORT[r["verdicts"][k]] for k in ("main", "a", "b")) + " |" for r in rows if r["status"] == "borderline"]
    L += ["", "## Are the dev-set disagreements the borderline findings?", "",
          "The 20 dev findings (KO, JPM, GOOGL, TSLA, DUK) against the human labels (final main verdict, after the Critic's repairs). Small numbers: read the counts, not the p-value.", "",
          "| | Disagrees with the human label | Agrees |", "|---|---|---|",
          f"| Borderline | {corr['cells']['borderline']['disagree']} | {corr['cells']['borderline']['agree']} |",
          f"| Stable | {corr['cells']['stable']['disagree']} | {corr['cells']['stable']['agree']} |", "",
          f"- Disagreement rate among borderline findings: {pct(corr['disagree_rate_borderline'])}; among stable findings: {pct(corr['disagree_rate_stable'])}.",
          f"- Share of the disagreements that are borderline: {pct(corr['share_of_disagreements_that_are_borderline'])}.",
          f"- Phi coefficient: {phi}; one-sided Fisher exact p = {corr['fisher_p_one_sided']:.3f}. Findings without a status: {corr['unjudged']}.", "",
          "| Dev disagreement | Main | A | B | Status |", "|---|---|---|---|---|"]
    for r in dev_rows:
        if r["verdicts"]["main"] != human[r["ticker"]][r["criterion"]]:
            L.append(f"| {r['ticker']} {TITLE[r['criterion']]} (human: {SHORT[human[r['ticker']][r['criterion']]]}) | " + " | ".join(SHORT[r["verdicts"][k]] for k in ("main", "a", "b")) + f" | {r['status'] or 'no status'} |")
    per_company = [stability_for(cik) for _, cik in companies]
    rel = criterion_stats([p for p in per_company if p is not None])
    L += ["", "## Criterion reliability", "",
          f"A criterion whose flip rate (findings whose verdict changed, of those with at least two assessed verdicts) is at or above {pct(load_threshold())} (`config/reliability.json`) is marked "
          "reliability low in every result and on the company page.", "", "| Criterion | Compared | Changed | Flip rate | Marked |", "|---|---|---|---|---|"]
    L += [f"| {TITLE[c]} | {v['compared']} | {v['changed']} | {pct(v['rate'])} | {'low reliability' if v['low'] else 'no'} |" for c, v in rel.items()]
    by = {(r["ticker"], r["criterion"]): r for r in rows}
    L += ["", "The six differences under prompt v2 (ADR-069), looked up in these runs:", "", "| v2 difference | Main (v2.1) | A | B | Status |", "|---|---|---|---|---|"]
    for t, c in V2_DISAGREEMENTS:
        r = by.get((t, c))
        L.append(f"| {t} {TITLE[c]} | " + (" | ".join(SHORT[r["verdicts"][k]] for k in ("main", "a", "b")) + f" | {r['status'] or 'no status'} |" if r else "not run | | | |"))
    L += ["", "## The paraphrases", "", "Main wording is `config/search_terms.json`. Review that the meaning is the same in all three.", ""]
    for c in QUAL_CRITERIA:
        L += [f"### {TITLE[c]}", ""]
        for f in FIELDS:
            L += [f"**{FIELD[f]}**", "", f"- Main: {main_c[c][f]}", f"- A: {para['a'][c][f]}", f"- B: {para['b'][c][f]}", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attach", action="store_true")
    a = ap.parse_args()
    universe = load_universe()
    tickers = json.loads((REPO_ROOT / "config" / "test_tickers.json").read_text())["tickers"] + [e["symbol"] for e in json.loads((REPO_ROOT / "config" / "showcase.json").read_text())["showcase"]]
    companies = [(t, universe.primary_of(universe.row_for(t)).cik) for t in tickers]
    if a.attach:
        agreement = json.loads((REPO_ROOT / "eval" / "agreement_results.json").read_text())["heldout"]["per_criterion"]
        done = attach([c for _, c in companies], human={c: (v["exact"], v["n"]) for c, v in agreement.items()})
        print(f"stability attached to {len(done)} results")
    OUT.write_text(render(companies), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
