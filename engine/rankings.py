"""Rankings builder (ADR-004, ADR-062): `results/scores/*.json` (+ full results) -> `site_data/rankings.json`.

The criteria ranking orders companies by the Wilson lower bound of the share of decided criteria they meet. The analyst ranking is an empty section until Finnhub gives
written permission (ADR-007, ADR-021). There is no text that compares the two (ADR-004), and the output has no wall-clock time: the same inputs
write the same bytes.
"""
from __future__ import annotations

import json
import re
from math import sqrt
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from engine.report import DISCLAIMER, PublishGateError, finnhub_fields
from engine.settings import REPO_ROOT
from engine.successors import NO_ANNUAL_REPORT
from engine.universe import Universe, display_name

SCHEMA_VERSION = "1.0"
SCHEMA_PATH = REPO_ROOT / "schema" / "rankings.schema.json"
OUTPUT_PATH = REPO_ROOT / "site_data" / "rankings.json"
CRITERIA = [f"G{i}" for i in range(1, 8)] + [f"B{i}" for i in range(1, 5)]
PENDING = "pending"  # a valuation test (G6, G7) that waits for price data: not a data gap, not counted in decided
MET = ("pass", "partial_pass")
DECIDED = MET + ("fail",)
MIN_DECIDED = 7  # main ranking
FINANCIAL_MIN_DECIDED = 4  # banks and insurers: G2 and B2 to B4 do not apply and valuation is pending, so at most 5 tests can be decided
FINANCIAL_CLASSES = ("bank", "insurer")
Z = 1.96  # 95% Wilson score interval
VALUATION_CAVEAT = "Valuation criteria (G6, G7) pending price data."
ANALYSTS_PENDING = "pending Finnhub permission (ADR-007, ADR-021)"
SEC_ATTRIBUTION = "Filings and XBRL data: U.S. Securities and Exchange Commission, EDGAR (public domain)"


def wilson_lower_bound(met: int, decided: int, z: float = Z) -> float:
    """Lower bound of the Wilson score interval for the share `met / decided` (ADR-062 amendment). A short list of passes earns less than a long one."""
    if decided == 0:
        return 0.0
    p = met / decided
    centre = p + z * z / (2 * decided)
    spread = z * sqrt(p * (1 - p) / decided + z * z / (4 * decided * decided))
    return max(0.0, (centre - spread) / (1 + z * z / decided))


METHOD = {
    "score": "lower bound of the 95% Wilson score interval for met / decided (z = 1.96), to 3 decimals; percent_met is the plain share",
    "met": "criteria with the label pass or partial_pass",
    "decided": "criteria with the label pass, partial_pass or fail, over G1 to G7 and B1 to B4; not_applicable, not_meaningful and data_gap are left out",
    "pending": "G6 and G7 wait for licensed price data: they are shown as pending, are not data gaps and are not counted as decided",
    "minimum_decided": f"the main ranking needs at least {MIN_DECIDED} decided criteria; banks and insurers (fewer tests apply) are ranked in their own section from {FINANCIAL_MIN_DECIDED}; the others are listed as insufficient data with their counts",
    "ties": "higher met, then fewer data gaps, then symbol",
}


class RankingRow(BaseModel):
    symbol: str
    cik: str
    name: str
    gics_sector: str
    gics_sub_industry: str | None = None
    sector_class: str
    notes: list[str] = Field(default_factory=list)  # sector notes (REIT, broker, ...) and registrant notes (successor)
    caveats: list[str] = Field(default_factory=list)  # e.g. VALUATION_CAVEAT
    group: str = "main"  # main, financials or insufficient_data
    rank: int | None = None  # within its group; None in the insufficient-data group
    score: float | None = None  # Wilson lower bound of met / decided, 3 dp; None in the insufficient-data group
    met: int
    decided: int
    percent_met: float | None = None  # met / decided as a percentage, 1 dp; None when nothing is decided
    data_gaps: int
    labels: dict[str, str]  # criterion id -> label, G1..G7 then B1..B4
    has_full_analysis: bool  # the agent analysis (results/<CIK>.json) exists
    analysis_path: str | None = None
    as_of_fiscal_year: int


class ExcludedRow(BaseModel):
    symbol: str
    cik: str
    name: str
    gics_sector: str
    status: str
    reason: str


class CriteriaRanking(BaseModel):
    method: dict[str, str]
    minimum_decided: int
    financials_minimum_decided: int
    ranked: list[RankingRow]
    ranked_financials: list[RankingRow]  # banks and insurers, their own ranking with the same score
    insufficient_data: list[RankingRow]


class PendingSection(BaseModel):
    status: Literal["pending"] = "pending"
    reason: str
    rows: list[Any] = Field(default_factory=list)


class DataAsOf(BaseModel):
    sec_fetched_from: str | None
    sec_fetched_to: str | None
    constituents_snapshot: str


class Counts(BaseModel):
    universe: int
    ranked: int
    ranked_financials: int
    insufficient_data: int
    excluded: int


class Rankings(BaseModel):
    schema_version: str = SCHEMA_VERSION
    disclaimer: str = DISCLAIMER
    data_as_of: DataAsOf
    attribution: list[str]
    caveats: list[str]
    counts: Counts
    criteria_ranking: CriteriaRanking
    # not named "analyst*": the Finnhub publish gate (ADR-021) matches that key pattern and this section holds no Finnhub data yet
    ranking_by_analysts: PendingSection
    excluded: list[ExcludedRow]


# ---------- reading the inputs ----------
def _load(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _label(r: dict) -> str:
    """The label, with a valuation test that only waits for a price shown as pending instead of a data gap."""
    if r["label"] == "data_gap" and (r.get("reason") or "").startswith("price not available"):
        return PENDING
    return r["label"]


def _from_score_file(d: dict) -> dict | None:
    sc = d["score"]
    return {"labels": {r["id"]: _label(r) for r in sc["results"]}, "as_of": sc["as_of_year"], "sector_class": d["sector_class"], "name": d["name"], "gics_sector": d["gics_sector"],
            "gics_sub_industry": d.get("gics_sub_industry"), "notes": list(d.get("sector_notes") or []) + list(d.get("source_notes") or []), "fetched": d.get("fetched_at")}


def _from_full_result(d: dict) -> dict | None:
    card = d.get("scorecard")
    if not card:
        return None
    plan, data = d["plan"], d.get("data") or {}
    return {"labels": {c["id"]: _label(c) for c in card["criteria"]}, "as_of": card["as_of_year"], "sector_class": card["sector_class"], "name": plan.get("name") or plan["ticker"],
            "gics_sector": plan.get("gics_sector") or "", "gics_sub_industry": None, "notes": list(card.get("sector_notes") or []),
            "fetched": (data.get("as_of") or {}).get("companyfacts") or None}


def _row(symbol: str, cik: str, info: dict, full_path: str | None) -> RankingRow:
    labels = {c: info["labels"].get(c, "data_gap") for c in CRITERIA}
    met = sum(l in MET for l in labels.values())
    decided = sum(l in DECIDED for l in labels.values())
    caveats = [VALUATION_CAVEAT] if PENDING in (labels["G6"], labels["G7"]) else []
    return RankingRow(symbol=symbol, cik=cik, name=display_name(info["name"]), gics_sector=info["gics_sector"], gics_sub_industry=info["gics_sub_industry"], sector_class=info["sector_class"],
                      notes=info["notes"], caveats=caveats, met=met, decided=decided, percent_met=round(100 * met / decided, 1) if decided else None, data_gaps=sum(l == "data_gap" for l in labels.values()), labels=labels,
                      has_full_analysis=full_path is not None, analysis_path=full_path, as_of_fiscal_year=info["as_of"])


def build_rankings(universe: Universe, scores_dir: Path, results_dir: Path) -> Rankings:
    """One row per company of the snapshot (one per CIK). A company is scored from its score file, else from its full result; a company with neither, or with
    the status `no_annual_report`, is excluded with the reason."""
    scores_dir, results_dir = Path(scores_dir), Path(results_dir)
    rows: list[RankingRow] = []
    excluded: list[ExcludedRow] = []
    fetched: list[str] = []
    for c in universe.primary:
        score_file, full_file = _load(scores_dir / f"{c.cik}.json"), _load(results_dir / f"{c.cik}.json")
        full_path = f"results/{c.cik}.json" if full_file and full_file.get("scorecard") else None
        info = None
        if score_file and score_file.get("status") == "no_annual_report":
            excluded.append(ExcludedRow(symbol=c.symbol, cik=c.cik, name=c.display_name, gics_sector=c.gics_sector, status="no_annual_report", reason=score_file["message"]))
            continue
        if score_file and score_file.get("score"):
            info = _from_score_file(score_file)
        elif full_file:
            info = _from_full_result(full_file)
        if info is None:
            excluded.append(ExcludedRow(symbol=c.symbol, cik=c.cik, name=c.display_name, gics_sector=c.gics_sector, status="not_scored", reason="no result file: run the batch for this company"))
            continue
        if info["fetched"]:
            fetched.append(info["fetched"])
        rows.append(_row(c.symbol, c.cik, info, full_path))

    def order(rs):
        out = sorted(rs, key=lambda r: (-round(wilson_lower_bound(r.met, r.decided), 9), -r.met, r.data_gaps, r.symbol))
        for i, r in enumerate(out, 1):
            r.rank, r.score = i, round(wilson_lower_bound(r.met, r.decided), 3)
        return out

    fin = lambda r: r.sector_class in FINANCIAL_CLASSES  # noqa: E731
    ranked = order([r for r in rows if not fin(r) and r.decided >= MIN_DECIDED])
    ranked_fin = order([r for r in rows if fin(r) and r.decided >= FINANCIAL_MIN_DECIDED])
    for r in ranked_fin:
        r.group = "financials"
    in_group = {id(r) for r in ranked + ranked_fin}
    insufficient = sorted((r for r in rows if id(r) not in in_group), key=lambda r: r.symbol)
    for r in insufficient:
        r.group = "insufficient_data"
    caveats = [VALUATION_CAVEAT] if any(VALUATION_CAVEAT in r.caveats for r in rows) else []
    return Rankings(
        data_as_of=DataAsOf(sec_fetched_from=min(fetched) if fetched else None, sec_fetched_to=max(fetched) if fetched else None, constituents_snapshot=universe.snapshot_date),
        attribution=[universe.attribution, SEC_ATTRIBUTION], caveats=caveats,
        counts=Counts(universe=len(universe.primary), ranked=len(ranked), ranked_financials=len(ranked_fin), insufficient_data=len(insufficient), excluded=len(excluded)),
        criteria_ranking=CriteriaRanking(method=METHOD, minimum_decided=MIN_DECIDED, financials_minimum_decided=FINANCIAL_MIN_DECIDED, ranked=ranked, ranked_financials=ranked_fin, insufficient_data=insufficient),
        ranking_by_analysts=PendingSection(reason=ANALYSTS_PENDING), excluded=sorted(excluded, key=lambda e: e.symbol))


# ---------- writing ----------
def rankings_json(rankings: Rankings) -> str:
    return json.dumps(rankings.model_dump(mode="json"), indent=1, ensure_ascii=False) + "\n"


def write_rankings(rankings: Rankings, path: Path = OUTPUT_PATH, *, finnhub_public_ok: bool = False) -> Path:
    """Validate by a round trip, apply the Finnhub publish gate (ADR-021), write the file."""
    text = rankings_json(rankings)
    Rankings.model_validate_json(text)
    if not finnhub_public_ok:
        leaked = finnhub_fields(json.loads(text))
        if leaked:
            raise PublishGateError(f"Finnhub-sourced fields in the rankings while FINNHUB_PUBLIC_OK is off (ADR-021): {leaked}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def export_rankings_schema(path: Path = SCHEMA_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(Rankings.model_json_schema(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["Rankings", "RankingRow", "build_rankings", "write_rankings", "export_rankings_schema", "VALUATION_CAVEAT", "ANALYSTS_PENDING", "MIN_DECIDED", "FINANCIAL_MIN_DECIDED", "PENDING", "NO_ANNUAL_REPORT", "wilson_lower_bound"]
