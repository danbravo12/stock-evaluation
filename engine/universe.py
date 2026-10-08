"""Ticker and CIK helpers (ADR-014).

The constituents snapshot loader and validator will live here too; for now this
holds the single normalisation function every other module must use.
"""
from __future__ import annotations


def normalise_ticker(ticker: str) -> str:
    """Return the canonical form used across the engine and by SEC: upper case,
    class separator as '-'. 'brk.b', 'BRK/B' and ' BRK-B ' all become 'BRK-B'."""
    t = ticker.strip().upper()
    for sep in (".", "/", " "):
        t = t.replace(sep, "-")
    return t


def cik10(cik: int | str) -> str:
    """Zero-padded 10-digit CIK, as used in EDGAR API URLs."""
    return str(int(cik)).zfill(10)
