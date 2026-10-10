"""Shared helpers for the scorers: fiscal-year keys, windows, sector class, result builders.

Everything here is a pure function over `NormalisedFacts`. Scorers return structured
facts (figures, years, flags, provenance); the Explainer writes prose later.
"""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from engine.contracts import AnnualValue, CriterionResult, InputRef, Label, NormalisedFacts
from engine.settings import REPO_ROOT

SECTOR_RULES_PATH = REPO_ROOT / "config" / "sector_rules.json"
WINDOW_YEARS = 10
DIVIDEND_WINDOW_YEARS = 15


def fiscal_year(v: AnnualValue) -> int:
    """Year label of a fiscal year: the year of its end date, with a 52/53-week year that
    ends in the first days of January counted in the year before."""
    return (v.fiscal_year_end - timedelta(days=15)).year


class Facts:
    """Year-keyed access to one company's normalised series."""

    def __init__(self, nf: NormalisedFacts):
        self.by = {m: {fiscal_year(v): v for v in s.values} for m, s in nf.series.items()}

    def get(self, measure: str, year: int) -> AnnualValue | None:
        return self.by[measure].get(year)

    def as_of_year(self) -> int | None:
        """Latest fiscal year with net income (ADR-031)."""
        years = self.by["net_income"]
        return max(years) if years else None

    def collect(self, measure: str, years: list[int]):
        """({year: value} for the years that exist, [years that are missing])."""
        found = {y: self.by[measure][y] for y in years if y in self.by[measure]}
        return found, [y for y in years if y not in found]


def window(as_of: int, length: int = WINDOW_YEARS) -> list[int]:
    return list(range(as_of - length + 1, as_of + 1))


def avg(values) -> float:
    values = list(values)
    return sum(values) / len(values)


FINANCIAL_CLASSES = ("bank", "insurer")  # ADR-013: G2, B2, B3 and B4 do not apply


def sector_class(sic: int | str | None, rules: dict) -> str:
    if sic:
        for rule in rules["rules"]:
            if any(lo <= int(sic) <= hi for lo, hi in rule["sic_ranges"]):
                return rule["class"]
    return rules["default"]


def resolve_sector(rules: dict, *, sic: int | str | None = None, gics_sub_industry: str | None = None, cik: str | None = None) -> tuple[str, str, str]:
    """(class, basis, reason): per-CIK override, then the GICS sub-industry (a company in the snapshot with no rule for it is 'other'), then SIC ranges for tickers outside the snapshot, then the default (ADR-057)."""
    if cik and cik in rules.get("cik_overrides", {}):
        o = rules["cik_overrides"][cik]
        return o["class"], f"override:{o.get('name', cik)}", o["why"]
    if gics_sub_industry and gics_sub_industry in rules.get("gics_sub_industries", {}):
        o = rules["gics_sub_industries"][gics_sub_industry]
        return o["class"], f"gics:{gics_sub_industry}", o["why"]
    if gics_sub_industry:  # a company in the snapshot with no exception rule for its sub-industry is an ordinary company: SIC is not consulted (ADR-057)
        return rules["default"], f"gics:{gics_sub_industry} (no exception rule)", "no ADR-013 exception applies to this sub-industry"
    cls = sector_class(sic, rules)  # not in the snapshot: SIC ranges are the fallback
    return cls, f"sic:{sic}" if sic else "default", "SIC fallback (ticker not in the snapshot)" if sic else "no classification available"


def sector_notes(cls: str, rules: dict) -> list[str]:
    note = rules.get("notes", {}).get(cls)
    return [note] if note else []


def load_sector_rules(path: Path = SECTOR_RULES_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def input_ref(measure: str, v: AnnualValue) -> InputRef:
    flags = [f for f, on in (("derived", v.derived), ("restated", v.restated), ("split_adjusted", v.split_factor != 1.0)) if on]
    return InputRef(
        measure=measure, fiscal_year=fiscal_year(v), fiscal_year_end=v.fiscal_year_end, value=v.value, unit=v.unit,
        concept=v.concept, accession=v.accession, source_url=v.source_url, flags=flags,
    )


def result(cid: str, name: str, label: Label, threshold: str, *, figures: dict | None = None, by_year: dict | None = None,
           years: list[int] | None = None, year_label: str | None = None, reason: str | None = None,
           inputs: list[tuple[str, AnnualValue]] = ()) -> CriterionResult:
    refs = [input_ref(m, v) for m, v in inputs]
    return CriterionResult(
        id=cid, name=name, label=label, threshold=threshold, figures=figures or {}, by_year={str(k): v for k, v in (by_year or {}).items()},
        years=years or [], year_label=year_label, reason=reason,
        flags=sorted({f for r in refs for f in r.flags}), inputs=refs,
    )


def gap(cid: str, name: str, threshold: str, reason: str, years: list[int] | None = None) -> CriterionResult:
    return result(cid, name, "data_gap", threshold, reason=reason, years=years)


def missing_text(missing: dict[str, list[int]]) -> str:
    return "missing: " + "; ".join(f"{m} {ys}" for m, ys in missing.items() if ys)


def not_applicable(cid: str, name: str, threshold: str, sector: str) -> CriterionResult:
    return result(cid, name, "not_applicable", threshold, reason=f"{sector} (ADR-013)")
