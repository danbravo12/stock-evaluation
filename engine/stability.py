"""Prompt-perturbation stability of the qualitative verdicts (build 4a, ADR-072).

The qualitative agent and the Critic are run again with the question and the verdict definitions reworded (config/qualitative_paraphrases.json,
variants "a" and "b"; the main run is the third). A finding whose verdict is not the same in all three is **borderline**: the verdict depends
on the wording, not only on the filing. Results of the variant runs live in `results/stability/<variant>/` and never replace the main results.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from engine.agents.qualitative import load_criteria
from engine.contracts import QUAL_CRITERIA
from engine.report import SCHEMA_VERSION, ReliabilityBasis, Result, Stability, result_json
from engine.settings import REPO_ROOT

PARAPHRASES_PATH = REPO_ROOT / "config" / "qualitative_paraphrases.json"
RELIABILITY_PATH = REPO_ROOT / "config" / "reliability.json"
STABILITY_DIR = REPO_ROOT / "results" / "stability"
VARIANTS = ("a", "b")
FIELDS = ("question", "found_means", "weak_means", "insufficient_means")
ASSESSED = ("evidence found", "evidence weak", "insufficient evidence")
LEVEL = {"insufficient evidence": 0, "evidence weak": 1, "evidence found": 2}


def load_paraphrases(path: Path = PARAPHRASES_PATH) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for v in VARIANTS:
        for c in QUAL_CRITERIA:
            missing = [f for f in FIELDS if not data[v][c].get(f)]
            if missing:
                raise ValueError(f"paraphrase {v}/{c} lacks {missing}")
    return data


def variant_criteria(variant: str, base: dict | None = None, paraphrases: dict | None = None) -> dict:
    """The main rubric with the question and the three verdict definitions replaced by variant `variant`; everything else is unchanged."""
    spec = copy.deepcopy(base or load_criteria())
    para = (paraphrases or load_paraphrases())[variant]
    for c in QUAL_CRITERIA:
        spec[c].update({f: para[c][f] for f in FIELDS})
    return spec


def classify(verdicts: dict[str, str]) -> Stability | None:
    """`verdicts` has the keys main, a, b. Stable if all assessed verdicts are equal, borderline if any differ. A verdict of "not assessed" is a system outcome,
    not a judgement, so it is kept in the record but does not count towards the status; with fewer than two assessed verdicts nothing can be said (None)."""
    assessed = [v for v in verdicts.values() if v in ASSESSED]
    if len(assessed) < 2:
        return None
    return Stability(status="stable" if len(set(assessed)) == 1 else "borderline", verdicts=dict(verdicts))


def result_path(cik: str, variant: str | None = None, root: Path | None = None) -> Path:
    if variant is None:
        return (root or REPO_ROOT / "results") / f"{cik}.json"
    return (root or STABILITY_DIR) / variant / f"{cik}.json"


def verdicts_of(path: Path) -> dict[str, str]:
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    return {q["finding"]["criterion"]: q["finding"]["verdict"] for q in r["qualitative"]}


def stability_for(cik: str, results_dir: Path | None = None, stability_dir: Path | None = None) -> dict[str, Stability | None] | None:
    """Per criterion, from the main result and the two variant results; None if a variant result is missing."""
    paths = {"main": result_path(cik, None, results_dir), "a": result_path(cik, "a", stability_dir), "b": result_path(cik, "b", stability_dir)}
    if not all(p.exists() for p in paths.values()):
        return None
    got = {k: verdicts_of(p) for k, p in paths.items()}
    return {c: classify({k: got[k].get(c, "not assessed") for k in ("main", "a", "b")}) for c in QUAL_CRITERIA}


def load_threshold(path: Path = RELIABILITY_PATH) -> float:
    return float(json.loads(Path(path).read_text(encoding="utf-8"))["low_flip_rate_threshold"])


def criterion_stats(per_company: list[dict], threshold: float | None = None) -> dict[str, dict]:
    """Per qualitative criterion over all companies: `compared` = findings with a stability status (at least two assessed verdicts), `changed` = those that are
    borderline, `rate` = changed / compared, `low` = rate at or above the threshold. `per_company` is a list of {criterion: Stability | dict | None}."""
    threshold = load_threshold() if threshold is None else threshold
    out = {}
    for c in QUAL_CRITERIA:
        statuses = []
        for company in per_company:
            st = company.get(c)
            status = st.get("status") if isinstance(st, dict) else (st.status if st is not None else None)
            if status:
                statuses.append(status)
        n, k = len(statuses), sum(x == "borderline" for x in statuses)
        rate = (k / n) if n else None
        out[c] = {"changed": k, "compared": n, "rate": rate, "low": rate is not None and rate >= threshold}
    return out


def attach(ciks: list[str], results_dir: Path | None = None, stability_dir: Path | None = None, threshold: float | None = None,
           human: dict[str, tuple[int, int]] | None = None) -> dict[str, dict]:
    """Write `stability` onto every qualitative item of each main result whose two variant results exist, then the criterion reliability (computed over all those
    companies) onto the items of every given result. Companies with a missing variant keep no stability record. `human` maps a criterion to
    (held-out findings the agent got right, held-out findings labelled) and is stored in the reliability basis. Returns the stability per company."""
    out = {cik: st for cik in ciks if (st := stability_for(cik, results_dir, stability_dir)) is not None}
    stats = criterion_stats(list(out.values()), threshold)
    for cik in ciks:
        path = result_path(cik, None, results_dir)
        if not path.exists():
            continue
        res = Result.model_validate_json(path.read_text(encoding="utf-8"))
        res.schema_version = SCHEMA_VERSION
        for q in res.qualitative:
            c = q.finding.criterion
            if cik in out:
                q.stability = out[cik].get(c)
            low = stats[c]["low"]
            q.reliability = "low" if low else None
            q.reliability_basis = ReliabilityBasis(changed=stats[c]["changed"], compared=stats[c]["compared"], human_agreed=(human or {}).get(c, (None, None))[0],
                                                   human_of=(human or {}).get(c, (None, None))[1]) if low else None
        path.write_text(result_json(res), encoding="utf-8")
    return out


# ---------- statistics over the runs ----------
def collect(companies: list[tuple[str, str]], results_dir: Path | None = None, stability_dir: Path | None = None) -> list[dict]:
    """One row per (company, criterion) with the three verdicts, for the companies whose two variant results exist. `companies` is [(ticker, cik)]."""
    rows = []
    for ticker, cik in companies:
        st = stability_for(cik, results_dir, stability_dir)
        if st is None:
            continue
        paths = {"main": result_path(cik, None, results_dir), "a": result_path(cik, "a", stability_dir), "b": result_path(cik, "b", stability_dir)}
        got = {k: verdicts_of(p) for k, p in paths.items()}
        for c in QUAL_CRITERIA:
            verdicts = {k: got[k].get(c, "not assessed") for k in ("main", "a", "b")}
            s = st[c]
            rows.append({"ticker": ticker, "cik": cik, "criterion": c, "verdicts": verdicts, "status": s.status if s else None})
    return rows


def flip_stats(rows: list[dict]) -> dict:
    """Flip rates. A finding "flips" when it is borderline (its assessed verdicts are not all equal). Pairwise rates compare two runs on the findings both assessed."""
    judged = [r for r in rows if r["status"] is not None]

    def share(rs):
        n, b = len(rs), sum(r["status"] == "borderline" for r in rs)
        return {"n": n, "borderline": b, "rate": (b / n) if n else None}

    def pair(x, y):
        both = [r for r in rows if r["verdicts"][x] in ASSESSED and r["verdicts"][y] in ASSESSED]
        return {"n": len(both), "differ": sum(r["verdicts"][x] != r["verdicts"][y] for r in both)}

    spreads = [max(LEVEL[v] for v in r["verdicts"].values() if v in LEVEL) - min(LEVEL[v] for v in r["verdicts"].values() if v in LEVEL) for r in judged if r["status"] == "borderline"]
    return {"findings": len(rows), "judged": len(judged), "not_judged": len(rows) - len(judged),
            "not_assessed_verdicts": sum(v == "not assessed" for r in rows for v in r["verdicts"].values()),
            "overall": share(judged), "per_criterion": {c: share([r for r in judged if r["criterion"] == c]) for c in QUAL_CRITERIA},
            "pairs": {"main_vs_a": pair("main", "a"), "main_vs_b": pair("main", "b"), "a_vs_b": pair("a", "b")},
            "spread": {"one_level": sum(s == 1 for s in spreads), "two_levels": sum(s == 2 for s in spreads)}}


def fisher_one_sided(a: int, b: int, c: int, d: int) -> float:
    """P(at least `a` in the top-left cell | margins) for the table [[a, b], [c, d]]: are the first row's members over-represented in the first column?"""
    from math import comb
    n1, m1, n = a + b, a + c, a + b + c + d
    denom = comb(n, m1)
    return sum(comb(n1, k) * comb(n - n1, m1 - k) for k in range(a, min(n1, m1) + 1)) / denom if denom else 1.0


def dev_correlation(rows: list[dict], human: dict[str, dict[str, str]]) -> dict:
    """Are the dev-set disagreements (final main verdict against the human one) the borderline findings? 2x2 counts, rates, phi and a one-sided Fisher exact p."""
    cells = {"borderline": {"disagree": 0, "agree": 0}, "stable": {"disagree": 0, "agree": 0}}
    unjudged = 0
    for r in rows:
        h = human.get(r["ticker"], {}).get(r["criterion"])
        if h is None:
            continue
        if r["status"] is None:
            unjudged += 1
            continue
        cells[r["status"]]["agree" if r["verdicts"]["main"] == h else "disagree"] += 1
    a, b = cells["borderline"]["disagree"], cells["borderline"]["agree"]
    c, d = cells["stable"]["disagree"], cells["stable"]["agree"]
    den = ((a + b) * (c + d) * (a + c) * (b + d)) ** 0.5
    rate = lambda x, y: (x / (x + y)) if (x + y) else None  # noqa: E731
    return {"cells": cells, "unjudged": unjudged, "disagree_rate_borderline": rate(a, b), "disagree_rate_stable": rate(c, d),
            "share_of_disagreements_that_are_borderline": rate(a, c), "phi": ((a * d - b * c) / den) if den else None, "fisher_p_one_sided": fisher_one_sided(a, b, c, d)}


def pair_flips(companies: list[tuple[str, str]], x: str, y: str, results_dir: Path | None = None, stability_dir: Path | None = None) -> dict:
    """Main-vs-variant (or variant-vs-variant) flip counts per criterion over every company where both runs exist; findings assessed in both only."""
    def path(k, cik):
        return result_path(cik, None, results_dir) if k == "main" else result_path(cik, k, stability_dir)
    per = {c: {"n": 0, "differ": 0} for c in QUAL_CRITERIA}
    covered = 0
    for _, cik in companies:
        px, py = path(x, cik), path(y, cik)
        if not (px.exists() and py.exists()):
            continue
        covered += 1
        vx, vy = verdicts_of(px), verdicts_of(py)
        for c in QUAL_CRITERIA:
            if vx.get(c) in ASSESSED and vy.get(c) in ASSESSED:
                per[c]["n"] += 1
                per[c]["differ"] += vx[c] != vy[c]
    return {"companies": covered, "per_criterion": per, "n": sum(v["n"] for v in per.values()), "differ": sum(v["differ"] for v in per.values())}
