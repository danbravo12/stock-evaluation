"""Buffett's quantitative criteria B1-B4 (PROCESS.md section 5, ADR-011). Pure functions."""
from __future__ import annotations

from engine.contracts import CriterionResult
from engine.score.common import Facts, avg, gap, missing_text, not_applicable, result, window
from engine.score.graham import FINANCIAL


def b1_return_on_equity(f: Facts, as_of: int) -> CriterionResult:
    name, thr = "Return on equity", "ROE >= 15% in at least 7 of the last 10 years"
    w = window(as_of)
    ni, miss_ni = f.collect("net_income", w)
    equity, miss_eq = f.collect("stockholders_equity", [w[0] - 1] + w)  # opening equity of the first year
    if miss_ni or miss_eq:
        return gap("B1", name, thr, missing_text({"net_income": miss_ni, "stockholders_equity": miss_eq}), miss_ni + miss_eq)
    inputs = [("net_income", ni[y]) for y in w] + [("stockholders_equity", v) for v in equity.values()]
    if any(v.value <= 0 for v in equity.values()):
        return result("B1", name, "not_meaningful", thr, years=w, reason="stockholders' equity is zero or negative in the window", inputs=inputs)
    roe = {y: ni[y].value / avg([equity[y - 1].value, equity[y].value]) for y in w}  # on average equity
    years_ok = [y for y in w if roe[y] >= 0.15]
    return result("B1", name, "pass" if len(years_ok) >= 7 else "fail", thr, figures={"years_at_or_above_15pct": len(years_ok)},
                  by_year=roe, years=w, inputs=inputs)


def b2_conservative_debt(f: Facts, as_of: int, sector: str) -> CriterionResult:
    name, thr = "Conservative debt", "long-term debt <= 4 x avg net income of the last 3 years"
    if sector in FINANCIAL:
        return not_applicable("B2", name, thr, sector)
    last3 = window(as_of)[-3:]
    debt, ni = f.get("long_term_debt", as_of), f.collect("net_income", last3)[0]
    if debt is None or len(ni) < 3:
        return gap("B2", name, thr, missing_text({"long_term_debt": [] if debt else [as_of], "net_income": [y for y in last3 if y not in ni]}), [as_of])
    avg_ni = avg(v.value for v in ni.values())
    ok = avg_ni > 0 and debt.value <= 4 * avg_ni  # no positive earnings: fail, figures shown
    return result("B2", name, "pass" if ok else "fail", thr, figures={"long_term_debt": debt.value, "avg_net_income_3y": avg_ni, "max_debt": 4 * avg_ni},
                  years=last3, inputs=[("long_term_debt", debt)] + [("net_income", ni[y]) for y in last3])


def b3_stable_margins(f: Facts, as_of: int, sector: str) -> CriterionResult:
    name, thr = "Stable margins", "operating margin > 0 every year and last-3-yr avg >= 90% of the 10-yr avg"
    if sector in FINANCIAL:
        return not_applicable("B3", name, thr, sector)
    w = window(as_of)
    op, miss_op = f.collect("operating_income", w)
    rev, miss_rev = f.collect("revenue", w)
    if miss_op or miss_rev:
        return gap("B3", name, thr, missing_text({"operating_income": miss_op, "revenue": miss_rev}), sorted(set(miss_op + miss_rev)))
    margin = {y: op[y].value / rev[y].value for y in w}
    avg10, avg3 = avg(margin.values()), avg(margin[y] for y in w[-3:])
    ok = all(m > 0 for m in margin.values()) and avg3 >= 0.9 * avg10
    return result("B3", name, "pass" if ok else "fail", thr, figures={"avg_margin_10y": avg10, "avg_margin_3y": avg3, "ratio": avg3 / avg10 if avg10 else None},
                  by_year=margin, years=w, inputs=[(m, d[y]) for y in w for m, d in (("operating_income", op), ("revenue", rev))])


def b4_owner_earnings(f: Facts, as_of: int, sector: str) -> CriterionResult:
    name, thr = "Owner earnings", "net income + D&A - capex > 0 in >= 8 of 10 years and last-3-yr avg > first-3-yr avg"
    if sector in FINANCIAL:
        return not_applicable("B4", name, thr, sector)
    w = window(as_of)
    parts = {m: f.collect(m, w) for m in ("net_income", "depreciation_amortization", "capex")}
    missing = {m: miss for m, (_, miss) in parts.items() if miss}
    if missing:  # needs all 10 years (ADR-034)
        return gap("B4", name, thr, missing_text(missing), sorted({y for ys in missing.values() for y in ys}))
    oe = {y: parts["net_income"][0][y].value + parts["depreciation_amortization"][0][y].value - parts["capex"][0][y].value for y in w}
    positive = sum(v > 0 for v in oe.values())
    first3, last3 = avg(oe[y] for y in w[:3]), avg(oe[y] for y in w[-3:])
    dep_only = [y for y in w if parts["depreciation_amortization"][0][y].source_concepts == ["us-gaap:Depreciation"]]
    r = result("B4", name, "pass" if positive >= 8 and last3 > first3 else "fail", thr,
               figures={"years_positive": positive, "avg_first_3y": first3, "avg_last_3y": last3, "years_with_depreciation_only": dep_only},
               by_year=oe, years=w, inputs=[(m, p[0][y]) for y in w for m, p in parts.items()])
    if dep_only:
        r.flags.append("depreciation_only")  # ADR-030: D&A understated in those years
    return r


def score_buffett(f: Facts, as_of: int, sector: str) -> list[CriterionResult]:
    return [b1_return_on_equity(f, as_of), b2_conservative_debt(f, as_of, sector), b3_stable_margins(f, as_of, sector),
            b4_owner_earnings(f, as_of, sector)]
