"""Deterministic scorers G1-G7 and B1-B4 (ADR-005). No LLM, no network."""
from __future__ import annotations

from engine.contracts import ScoreSet, Summary
from engine.normalise import normalise_from_store
from engine.score.buffett import score_buffett
from engine.score.common import Facts, input_ref, load_sector_rules, resolve_sector, sector_notes
from engine.score.graham import score_graham
from engine.splits import adjust_for_splits

def gics_sub_industry_of(ticker: str) -> str | None:
    """The ticker's GICS sub-industry in the latest S&P 500 snapshot, or None (then the SIC fallback decides)."""
    try:
        from engine.universe import load_universe
        row = load_universe().row_for(ticker)
        return row.gics_sub_industry if row else None
    except FileNotFoundError:
        return None


DECIDED = ("pass", "partial_pass", "fail")


def summarise(results) -> Summary:
    def counts(prefix):
        rs = [r for r in results if r.id.startswith(prefix) and r.label in DECIDED]
        return sum(r.label != "fail" for r in rs), len(rs)

    (gm, ga), (bm, ba) = counts("G"), counts("B")
    count = lambda label: sum(r.label == label for r in results)
    return Summary(graham_met=gm, graham_applicable=ga, buffett_met=bm, buffett_applicable=ba, data_gaps=count("data_gap"),
                   not_meaningful=count("not_meaningful"), not_applicable=count("not_applicable"),
                   percent_met=(gm + bm) / (ga + ba) if ga + ba else None)


def score_company(nf, ticker: str, sic, rules: dict, price: float | None = None, *, sector: str | None = None,
                  gics_sub_industry: str | None = None) -> ScoreSet:
    """`nf` is split-adjusted NormalisedFacts. `price` is optional (Finnhub, later). `sector` fixes the class (the planner passes its own);
    otherwise it is resolved from the CIK, the GICS sub-industry and the SIC code (ADR-057)."""
    f = Facts(nf)
    as_of = f.as_of_year()
    if as_of is None:
        raise ValueError(f"{ticker}: no annual net income in EDGAR; cannot set an as-of year")
    sector = sector or resolve_sector(rules, sic=sic, gics_sub_industry=gics_sub_industry, cik=nf.cik)[0]
    results = score_graham(f, as_of, sector, price) + score_buffett(f, as_of, sector)
    seen = {}
    for r in results:
        for i in r.inputs:
            seen[(i.measure, i.fiscal_year)] = i
    return ScoreSet(cik=nf.cik, ticker=ticker, as_of_year=as_of, sector_class=sector, results=results,
                    summary=summarise(results), inputs=sorted(seen.values(), key=lambda i: (i.measure, i.fiscal_year)),
                    sector_notes=sector_notes(sector, rules))


def score_ticker(client, ticker: str, rules: dict | None = None, price: float | None = None) -> ScoreSet:
    """Normalise, split-adjust and score one company through an EdgarClient (replay in tests)."""
    cik, _ = client.lookup_cik(ticker)
    nf = adjust_for_splits(normalise_from_store(client, cik), client.companyfacts(cik))
    return score_company(nf, ticker, client.submissions(cik).get("sic"), rules or load_sector_rules(), price, gics_sub_industry=gics_sub_industry_of(ticker))
