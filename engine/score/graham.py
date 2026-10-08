"""Graham's defensive-investor criteria G1-G7 (PROCESS.md section 5). Pure functions."""
from __future__ import annotations

from engine.contracts import CriterionResult
from engine.score.common import (DIVIDEND_WINDOW_YEARS, Facts, avg, gap, missing_text, not_applicable, result, window)

FINANCIAL = ("bank", "insurer")
MIN_REVENUE = 1e9


def g1_size(f: Facts, as_of: int) -> CriterionResult:
    name, thr = "Size", "revenue >= $1B"
    v = f.get("revenue", as_of)
    if v is None:
        return gap("G1", name, thr, f"no revenue for {as_of}", [as_of])
    return result("G1", name, "pass" if v.value >= MIN_REVENUE else "fail", thr,
                  figures={"revenue": v.value}, years=[as_of], inputs=[("revenue", v)])


def g2_financial_strength(f: Facts, as_of: int, sector: str) -> CriterionResult:
    name = "Financial strength"
    if sector in FINANCIAL:
        return not_applicable("G2", name, "current ratio >= 2 and long-term debt <= net current assets", sector)
    debt = f.get("long_term_debt", as_of)  # never assume zero: missing debt is a gap
    if sector == "utility":
        thr = "long-term debt <= 2 x stockholders' equity (utility variant)"
        equity = f.get("stockholders_equity", as_of)
        if debt is None or equity is None:
            return gap("G2", name, thr, missing_text({"long_term_debt": [] if debt else [as_of], "stockholders_equity": [] if equity else [as_of]}), [as_of])
        ok = debt.value <= 2 * equity.value
        return result("G2", name, "pass" if ok else "fail", thr,
                      figures={"long_term_debt": debt.value, "stockholders_equity": equity.value, "debt_to_equity": debt.value / equity.value if equity.value else None},
                      years=[as_of], inputs=[("long_term_debt", debt), ("stockholders_equity", equity)])
    thr = "current ratio >= 2 and long-term debt <= net current assets"
    ca, cl = f.get("current_assets", as_of), f.get("current_liabilities", as_of)
    if None in (ca, cl, debt):
        return gap("G2", name, thr, missing_text({"current_assets": [] if ca else [as_of], "current_liabilities": [] if cl else [as_of],
                                                  "long_term_debt": [] if debt else [as_of]}), [as_of])
    net_current = ca.value - cl.value
    ratio = ca.value / cl.value if cl.value else None
    ok = ratio is not None and ratio >= 2 and debt.value <= net_current
    return result("G2", name, "pass" if ok else "fail", thr,
                  figures={"current_ratio": ratio, "long_term_debt": debt.value, "net_current_assets": net_current},
                  years=[as_of], inputs=[("current_assets", ca), ("current_liabilities", cl), ("long_term_debt", debt)])


def g3_earnings_stability(f: Facts, as_of: int) -> CriterionResult:
    name, thr = "Earnings stability", "net income > 0 in every year of the last 10"
    ni, _ = f.collect("net_income", window(as_of))
    years = sorted(ni)
    holes = [y for y in range(years[0], as_of + 1) if y not in ni]
    if holes:
        return gap("G3", name, thr, f"net_income missing inside the record: {holes}", holes)
    ok = all(v.value > 0 for v in ni.values())
    return result("G3", name, "pass" if ok else "fail", thr,
                  figures={"years_on_record": len(years), "loss_years": [y for y in years if ni[y].value <= 0]},
                  by_year={y: ni[y].value for y in years}, years=years,
                  year_label=None if len(years) == 10 else f"{len(years)} yrs on record",
                  inputs=[("net_income", ni[y]) for y in years])


def g4_dividend_record(f: Facts, as_of: int) -> CriterionResult:
    """ADR-012 (with its 2026-10-08 correction): years on record = years with net income."""
    name, thr = "Dividend record", "dividend paid in every year on record in the last 15"
    ni, _ = f.collect("net_income", window(as_of, DIVIDEND_WINDOW_YEARS))
    record = sorted(ni)
    holes = [y for y in range(record[0], as_of + 1) if y not in ni]
    if holes:
        return gap("G4", name, thr, f"net_income missing inside the record: {holes}", holes)
    by_year, inputs = {}, []
    for y in record:
        dps, paid = f.get("dividends_per_share", y), f.get("dividends_paid", y)
        # Per-share data decides when present (even a reported zero: a one-off cash payment is not a dividend);
        # cash paid is the fallback only when per-share data is missing (ADR-012 correction).
        used = dps if dps is not None else paid
        source = "dividends_per_share" if dps is not None else "dividends_paid" if paid is not None else "none"
        by_year[y] = {"paid": used is not None and used.value > 0, "source": source, "value": used.value if used else None}
        if used is not None:
            inputs.append((source, used))
    if not all(d["paid"] for d in by_year.values()):
        return result("G4", name, "fail", thr, figures={"years_on_record": len(record), "unpaid_years": [y for y in record if not by_year[y]["paid"]]},
                      by_year=by_year, years=record, inputs=inputs)
    full = len(record) == DIVIDEND_WINDOW_YEARS
    return result("G4", name, "partial_pass", thr, figures={"years_on_record": len(record)}, by_year=by_year, years=record,
                  year_label="partial (15 of 20 yrs)" if full else f"{len(record)} yrs on record", inputs=inputs)


def _avg_eps(f: Facts, years: list[int]):
    eps, missing = f.collect("eps_diluted", years)
    return eps, missing


def g5_earnings_growth(f: Facts, as_of: int) -> CriterionResult:
    name, thr = "Earnings growth", "3-yr avg diluted EPS (end) >= 1.33 x 3-yr avg (start of the 10-yr window)"
    w = window(as_of)
    first, last = w[:3], w[-3:]
    eps, missing = _avg_eps(f, first + last)
    if missing:
        return gap("G5", name, thr, missing_text({"eps_diluted": missing}), missing)
    start, end = avg(eps[y].value for y in first), avg(eps[y].value for y in last)
    figures = {"avg_eps_start": start, "avg_eps_end": end, "ratio": end / start if start > 0 else None}
    inputs = [("eps_diluted", eps[y]) for y in first + last]
    if start <= 0:
        return result("G5", name, "not_meaningful", thr, figures=figures, years=first + last, reason="starting average EPS is not positive", inputs=inputs)
    return result("G5", name, "pass" if end >= 1.33 * start else "fail", thr, figures=figures, years=first + last, inputs=inputs)


def _price_test(cid, name, thr, f, as_of, price, build):
    if price is None:
        return gap(cid, name, thr, "price not available (Finnhub, ADR-007)")
    last3 = window(as_of)[-3:]
    eps, missing = _avg_eps(f, last3)
    if missing:
        return gap(cid, name, thr, missing_text({"eps_diluted": missing}), missing)
    return build(price, avg(eps[y].value for y in last3), [("eps_diluted", eps[y]) for y in last3], last3)


def g6_moderate_pe(f: Facts, as_of: int, price: float | None) -> CriterionResult:
    name, thr = "Moderate P/E", "price <= 15 x avg diluted EPS of the last 3 years"

    def build(price, avg_eps, inputs, years):
        ok = avg_eps > 0 and price <= 15 * avg_eps  # no positive earnings to support a price: fail
        return result("G6", name, "pass" if ok else "fail", thr,
                      figures={"price": price, "avg_eps_3y": avg_eps, "max_price": 15 * avg_eps}, years=years, inputs=inputs)
    return _price_test("G6", name, thr, f, as_of, price, build)


def g7_price_vs_assets(f: Facts, as_of: int, price: float | None) -> CriterionResult:
    name, thr = "Price vs assets", "P/E x P/B <= 22.5"

    def build(price, avg_eps, inputs, years):
        equity, shares = f.get("stockholders_equity", as_of), f.get("diluted_shares", as_of)
        if equity is None or shares is None:
            return gap("G7", name, thr, missing_text({"stockholders_equity": [] if equity else [as_of], "diluted_shares": [] if shares else [as_of]}), [as_of])
        bvps = equity.value / shares.value  # book value per share proxy (ADR-034)
        ok = avg_eps > 0 and bvps > 0 and (price / avg_eps) * (price / bvps) <= 22.5
        return result("G7", name, "pass" if ok else "fail", thr,
                      figures={"price": price, "avg_eps_3y": avg_eps, "book_value_per_share": bvps,
                               "pe": price / avg_eps if avg_eps else None, "pb": price / bvps if bvps else None,
                               "pe_x_pb": (price / avg_eps) * (price / bvps) if avg_eps and bvps else None},
                      years=years + [as_of], inputs=inputs + [("stockholders_equity", equity), ("diluted_shares", shares)])
    return _price_test("G7", name, thr, f, as_of, price, build)


def score_graham(f: Facts, as_of: int, sector: str, price: float | None) -> list[CriterionResult]:
    return [g1_size(f, as_of), g2_financial_strength(f, as_of, sector), g3_earnings_stability(f, as_of),
            g4_dividend_record(f, as_of), g5_earnings_growth(f, as_of), g6_moderate_pe(f, as_of, price),
            g7_price_vs_assets(f, as_of, price)]
