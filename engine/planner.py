"""Rule-based planner (ADR-018): scope check, then which steps and criteria apply. No model, no network except the SIC lookup."""
from __future__ import annotations

from engine.contracts import NotApplicable, RunPlan, SkippedStep
from engine.score.common import FINANCIAL_CLASSES, load_sector_rules, resolve_sector, sector_notes
from engine.universe import Universe, normalise_ticker

STEPS = ["fetch", "score", "qualitative", "explain_and_verify", "report"]
GRAHAM = [f"G{i}" for i in range(1, 8)]
BUFFETT_QUANT = [f"B{i}" for i in range(1, 5)]
FINANCIAL_NOT_APPLICABLE = ["G2", "B2", "B3", "B4"]  # ADR-013 (the scorers apply the same rule)
PRICE_GAP = "price: Finnhub not yet integrated (publish gate, ADR-021)"


def plan_for(ticker: str, universe: Universe, sic: str | int | None = None, rules: dict | None = None) -> RunPlan:
    """Plan one analysis. `sic` is the company's SIC code (from its submissions); without it the sector class is "other" (ADR-033)."""
    t = normalise_ticker(ticker)
    row = universe.row_for(t)
    if row is None:
        return RunPlan(ticker=t, in_scope=False, out_of_scope_reason=f"{t} is not in the S&P 500 snapshot of {universe.snapshot_date} (outside v1 scope, ADR-002)",
                       universe_snapshot=universe.snapshot_date)
    primary = universe.primary_of(row)
    notes = []
    if primary is not None and primary.symbol != row.symbol:
        notes.append(f"{row.symbol} is a second share class of {primary.security}; analysed once per company under {primary.symbol} (ADR-053)")
    rules = rules or load_sector_rules()
    sector, basis, _ = resolve_sector(rules, sic=sic, gics_sub_industry=row.gics_sub_industry, cik=row.cik)
    na = [NotApplicable(id=i, reason=f"{sector} (ADR-013)") for i in FINANCIAL_NOT_APPLICABLE] if sector in FINANCIAL_CLASSES else []
    na_ids = {x.id for x in na}
    if sector == "utility":
        notes.append("G2 uses the utility variant: long-term debt <= 2x equity (ADR-013)")
    applicable = [i for i in GRAHAM + BUFFETT_QUANT if i not in na_ids]
    skipped = [SkippedStep(step="price", reason=PRICE_GAP), SkippedStep(step="criteria G6, G7", reason="need a price (Finnhub not yet integrated)")]
    return RunPlan(ticker=t, cik=row.cik, name=row.security, gics_sector=row.gics_sector, sector_class=sector, sector_basis=basis, sector_notes=sector_notes(sector, rules, gics_sub_industry=row.gics_sub_industry, cik=row.cik), in_scope=True,
                   universe_snapshot=universe.snapshot_date, steps=list(STEPS), skipped=skipped, applicable=applicable, not_applicable=na, notes=notes)
