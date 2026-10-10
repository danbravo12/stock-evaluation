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


# ---------- S&P 500 constituents (ADR-014, ADR-053) ----------
import csv  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from html.parser import HTMLParser  # noqa: E402
from pathlib import Path  # noqa: E402

from pydantic import BaseModel  # noqa: E402

from engine.settings import REPO_ROOT  # noqa: E402

UNIVERSE_DIR = REPO_ROOT / "data" / "universe"
PRIMARY_CONFIG = REPO_ROOT / "config" / "universe_primary.json"
CSV_FIELDS = ["symbol", "security", "gics_sector", "gics_sub_industry", "cik", "date_added"]
MIN_ROWS, MAX_ROWS = 495, 510


def display_name(security: str) -> str:
    """Wikipedia lists "Coca-Cola Company (The)"; people say "The Coca-Cola Company". The raw value stays in the CSV."""
    m = re.match(r"^(.*?)\s*\(The\)$", security)
    return f"The {m.group(1)}" if m else security


class Constituent(BaseModel):
    symbol: str  # normalised (BRK-B)
    security: str
    gics_sector: str
    gics_sub_industry: str
    cik: str  # 10 digits
    date_added: str  # as listed; may be empty

    @property
    def display_name(self) -> str:
        return display_name(self.security)


class _TableParser(HTMLParser):
    """Rows of the table with id="constituents": a list of cell-text lists."""

    def __init__(self):
        super().__init__()
        self.depth, self.rows, self._row, self._cell = 0, [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.depth or dict(attrs).get("id") == "constituents":
                self.depth += 1
        elif self.depth and tag == "tr":
            self._row = []
        elif self.depth and tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self.depth:
            self.depth -= 1
        elif self.depth and tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\[[^\]]*\]", "", " ".join("".join(self._cell).split()))
            self._row.append(text)
            self._cell = None
        elif self.depth and tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_constituents_html(html: str) -> list[Constituent]:
    """The Wikipedia constituents table as Constituent rows (header matched by name, so a column move does not shift fields)."""
    p = _TableParser()
    p.feed(html)
    if not p.rows:
        raise ValueError("no table with id 'constituents' in the page")
    header = [h.lower() for h in p.rows[0]]
    col = {name: next(i for i, h in enumerate(header) if name in h) for name in ("symbol", "security", "gics sector", "gics sub-industry", "cik", "date added")}
    out = []
    for r in p.rows[1:]:
        if len(r) < len(header):
            continue
        out.append(Constituent(symbol=normalise_ticker(r[col["symbol"]]), security=r[col["security"]], gics_sector=r[col["gics sector"]],
                               gics_sub_industry=r[col["gics sub-industry"]], cik=cik10(r[col["cik"]]), date_added=r[col["date added"]]))
    return out


def write_csv(rows: list[Constituent], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r.model_dump())


class Universe:
    """A dated constituents snapshot. Several rows can share a CIK (dual share classes); `primary` has one row per CIK (ADR-053)."""

    def __init__(self, rows: list[Constituent], snapshot_date: str, primary_symbols: list[str] | None = None, path: Path | None = None):
        self.rows, self.snapshot_date, self.path = rows, snapshot_date, path
        self.primary_symbols = set(primary_symbols if primary_symbols is not None else load_primary_symbols())
        self.by_symbol = {r.symbol: r for r in rows}

    @property
    def attribution(self) -> str:
        return f"Constituents: Wikipedia, as of {self.snapshot_date} (CC BY-SA)"

    @property
    def primary(self) -> list[Constituent]:
        """One row per CIK: the row whose symbol is in the primary list, else the only row; order of the snapshot."""
        by_cik: dict[str, list[Constituent]] = {}
        for r in self.rows:
            by_cik.setdefault(r.cik, []).append(r)
        out = []
        for cik, rs in by_cik.items():
            pick = rs[0] if len(rs) == 1 else next((r for r in rs if r.symbol in self.primary_symbols), None)
            if pick is not None:
                out.append(pick)
        return out

    def row_for(self, ticker: str) -> Constituent | None:
        return self.by_symbol.get(normalise_ticker(ticker))

    def primary_of(self, row: Constituent) -> Constituent | None:
        return next((p for p in self.primary if p.cik == row.cik), None)

    def dual_class_groups(self) -> list[list[str]]:
        by_cik: dict[str, list[str]] = {}
        for r in self.rows:
            by_cik.setdefault(r.cik, []).append(r.symbol)
        return [s for s in by_cik.values() if len(s) > 1]


def load_primary_symbols(path: Path = PRIMARY_CONFIG) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))["primary_symbols"]


def validate_universe(rows: list[Constituent], sec_tickers: dict, primary_symbols: list[str] | None = None) -> list[str]:
    """Problems found (ADR-014): row count, duplicate symbols, CIKs missing from or inconsistent with SEC's ticker file, dual classes
    with no primary symbol. An empty list means the snapshot is valid."""
    primary_symbols = set(primary_symbols if primary_symbols is not None else load_primary_symbols())
    problems = []
    if not MIN_ROWS <= len(rows) <= MAX_ROWS:
        problems.append(f"{len(rows)} rows; expected {MIN_ROWS}-{MAX_ROWS}")
    seen = set()
    for r in rows:
        if r.symbol in seen:
            problems.append(f"duplicate symbol {r.symbol}")
        seen.add(r.symbol)
    sec_ciks = {cik10(v["cik_str"]) for v in sec_tickers.values()}
    sec_by_ticker = {normalise_ticker(v["ticker"]): cik10(v["cik_str"]) for v in sec_tickers.values()}
    for r in rows:
        if r.cik not in sec_ciks:
            problems.append(f"{r.symbol}: CIK {r.cik} is not in SEC company_tickers")
        elif r.symbol in sec_by_ticker and sec_by_ticker[r.symbol] != r.cik:
            problems.append(f"{r.symbol}: CIK {r.cik} differs from SEC's {sec_by_ticker[r.symbol]} for that ticker")
    by_cik: dict[str, list[str]] = {}
    for r in rows:
        by_cik.setdefault(r.cik, []).append(r.symbol)
    for cik, syms in by_cik.items():
        if len(syms) > 1 and len([s for s in syms if s in primary_symbols]) != 1:
            problems.append(f"CIK {cik} has several symbols {syms} but not exactly one primary symbol in config/universe_primary.json")
    return problems


def load_universe(path: Path | None = None, sec_tickers: dict | None = None) -> Universe:
    """Load the latest (or the given) snapshot CSV; with `sec_tickers` also validate it and raise ValueError listing every problem."""
    path = Path(path) if path else latest_snapshot_path()
    with path.open(newline="", encoding="utf-8") as f:
        rows = [Constituent(**r) for r in csv.DictReader(f)]
    if sec_tickers is not None:
        problems = validate_universe(rows, sec_tickers)
        if problems:
            raise ValueError("invalid constituents snapshot: " + "; ".join(problems))
    m = re.search(r"sp500_(\d{4}-\d{2}-\d{2})\.csv$", path.name)
    return Universe(rows, m.group(1) if m else "unknown", path=path)


def latest_snapshot_path() -> Path:
    files = sorted(UNIVERSE_DIR.glob("sp500_*.csv"))
    if not files:
        raise FileNotFoundError("no data/universe/sp500_<date>.csv; run scripts/snapshot_universe.py")
    return files[-1]
