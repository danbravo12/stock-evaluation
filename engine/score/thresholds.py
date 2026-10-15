"""The numeric thresholds of the scorers in one place (ADR-011, ADR-074), so the sensitivity test can move each one by a stated fraction.

`CURRENT` holds the values the scorers read. The defaults are the published thresholds; nothing else changes them except `override`, a context
manager used by `eval/sensitivity.py` and the tests. Count thresholds (years out of ten) are whole numbers: `scaled` rounds them to the nearest year.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, fields, replace


@dataclass(frozen=True)
class Thresholds:
    g1_min_revenue: float = 1e9              # G1: revenue >= $1B
    g2_current_ratio: float = 2.0            # G2: current ratio >= 2
    g2_debt_to_net_current: float = 1.0      # G2: long-term debt <= 1 x net current assets
    g2_utility_debt_equity: float = 2.0      # G2, utilities: long-term debt <= 2 x equity
    g5_growth_ratio: float = 1.33            # G5: 3-yr avg EPS at the end >= 1.33 x at the start
    g6_max_pe: float = 15.0                  # G6: price <= 15 x avg EPS (price data pending)
    g7_max_pe_x_pb: float = 22.5             # G7: P/E x P/B <= 22.5 (price data pending)
    b1_roe: float = 0.15                     # B1: ROE >= 15% ...
    b1_min_years: int = 7                    # ... in at least 7 of the last 10 years
    b2_debt_multiple: float = 4.0            # B2: long-term debt <= 4 x 3-yr avg net income
    b3_margin_ratio: float = 0.9             # B3: last-3-yr avg margin >= 90% of the 10-yr avg
    b4_min_positive_years: int = 8           # B4: owner earnings positive in >= 8 of 10 years


DEFAULT = Thresholds()
CURRENT = DEFAULT
NAMES = [f.name for f in fields(Thresholds)]
COUNTS = {"b1_min_years", "b4_min_positive_years"}
CRITERION = {"g1_min_revenue": "G1", "g2_current_ratio": "G2", "g2_debt_to_net_current": "G2", "g2_utility_debt_equity": "G2", "g5_growth_ratio": "G5",
             "g6_max_pe": "G6", "g7_max_pe_x_pb": "G7", "b1_roe": "B1", "b1_min_years": "B1", "b2_debt_multiple": "B2", "b3_margin_ratio": "B3", "b4_min_positive_years": "B4"}


def T() -> Thresholds:
    return CURRENT


def scaled(name: str, factor: float) -> float | int:
    """The default of `name` times `factor`; a count of years is rounded to a whole year (half up)."""
    v = getattr(DEFAULT, name) * factor
    return int(v + 0.5) if name in COUNTS else round(v, 9)


@contextmanager
def override(**kw):
    """Run the scorers with some thresholds changed; the previous values come back on exit, also after an error."""
    global CURRENT
    prev = CURRENT
    CURRENT = replace(prev, **kw)
    try:
        yield CURRENT
    finally:
        CURRENT = prev
