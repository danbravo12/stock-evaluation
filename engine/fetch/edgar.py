"""SEC EDGAR client (Data fetcher tools: `edgar_facts`, `edgar_filing`).

Three modes, chosen per run:

* ``replay`` — read recorded fixtures only. Never touches the network. Used by
  tests, development and the evaluation harness (project rule: no live calls
  while developing).
* ``live``   — read the HTTP cache; on a miss, fetch from SEC and cache it.
* ``record`` — fetch from SEC and (over)write the fixture. Used once by
  ``scripts/record_fixtures.py``.

SEC fair-access rules are built in: a declared User-Agent ("Name email") on every
request, and a minimum interval between requests (well under 10 per second).
Data source: U.S. Securities and Exchange Commission, EDGAR (public domain).
"""
from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Literal

from engine.fetch.store import ResponseStore, StoredResponse
from engine.successors import NoAnnualReport, has_annual_report, load_successors
from engine.settings import Settings
from engine.universe import cik10, normalise_ticker

Mode = Literal["replay", "live", "record"]
# transport(url, headers, timeout) -> (status, response headers, body bytes)
Transport = Callable[[str, dict, float], "tuple[int, dict, bytes]"]

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{document}"

RETRY_STATUSES = {429, 500, 502, 503, 504}
BACKOFF_S = (1.0, 2.0, 4.0)


class EdgarError(RuntimeError):
    pass


class FixtureMissing(EdgarError):
    """Replay mode asked for something that was never recorded."""


class EdgarNotFound(EdgarError):
    pass


class NoAnnualReportError(EdgarNotFound, NoAnnualReport):
    """The registrant (and its predecessor, if any) has never filed a 10-K: a new listing or spin-off (ADR-063)."""


@dataclass(frozen=True)
class FilingRef:
    cik: str  # 10-digit
    form: str
    accession: str  # e.g. 0000021344-25-000011
    filing_date: str
    report_date: str
    primary_document: str

    @property
    def url(self) -> str:
        return ARCHIVES_URL.format(
            cik=int(self.cik),
            accession_nodash=self.accession.replace("-", ""),
            document=self.primary_document,
        )


def urllib_transport(url: str, headers: dict, timeout: float) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            status = resp.status
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""
    if resp_headers.get("content-encoding") == "gzip":
        body = gzip.decompress(body)
    return status, resp_headers, body


def _retry_delay(resp_headers: dict, default: float) -> float:
    """Honour a numeric Retry-After header if the server sent one."""
    try:
        return max(default, float(resp_headers.get("retry-after", "")))
    except ValueError:
        return default


class EdgarClient:
    def __init__(
        self,
        mode: Mode,
        settings: Settings | None = None,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        timeout_s: float = 30.0,
        successors: dict | None = None,
    ):
        if mode not in ("replay", "live", "record"):
            raise ValueError(f"Unknown mode {mode!r}")
        self.mode = mode
        self.settings = settings or Settings.from_env()
        self.transport = transport or urllib_transport
        self._sleep = sleep
        self._clock = clock
        self.timeout_s = timeout_s
        self.successors = load_successors() if successors is None else successors  # ADR-063
        self._last_request_at: float | None = None
        self.requests_made = 0
        self.store = ResponseStore(
            self.settings.cache_dir if mode == "live" else self.settings.fixtures_dir
        )
        if mode != "replay" and not self.settings.sec_user_agent:
            raise EdgarError(
                "SEC_USER_AGENT is not set. SEC requires a declared User-Agent such as "
                "'StockEvaluation research tool your.name@example.com'. Add it to .env."
            )

    # ---------- public tools ----------
    def company_tickers(self) -> dict:
        return self._get_json("edgar/company_tickers.json", TICKERS_URL)

    def lookup_cik(self, ticker: str) -> tuple[str, str]:
        """Return (10-digit CIK, company title) for a ticker, using SEC's ticker file."""
        wanted = normalise_ticker(ticker)
        for row in self.company_tickers().values():
            if normalise_ticker(row["ticker"]) == wanted:
                return cik10(row["cik_str"]), row["title"]
        raise EdgarNotFound(f"Ticker {ticker!r} not found in SEC company_tickers.json")

    def submissions(self, cik: int | str) -> dict:
        c = cik10(cik)
        return self._get_json(f"edgar/{c}/submissions.json", SUBMISSIONS_URL.format(cik10=c))

    def source_for(self, cik: int | str) -> tuple[str, str | None]:
        """(CIK whose companyfacts and 10-K stand in for `cik`, visible note). Normally the CIK itself. For a registrant successor (ADR-063) that has
        not filed a 10-K yet it is the predecessor registrant, with the note from `config/registrant_successors.json`."""
        c = cik10(cik)
        entry = self.successors.get(c)
        if entry is None or has_annual_report(self.submissions(c)):
            return c, None
        return cik10(entry["predecessors"][0]), entry["note"]

    def companyfacts(self, cik: int | str) -> dict:
        c = self.source_for(cik)[0]
        return self._get_json(f"edgar/{c}/companyfacts.json", COMPANYFACTS_URL.format(cik10=c))

    def latest_filing(self, cik: int | str, form: str = "10-K") -> FilingRef:
        """Most recent original filing of `form` (amendments such as 10-K/A excluded). A successor without a 10-K of its own gets its predecessor's (ADR-063)."""
        c = self.source_for(cik)[0]
        recent = self.submissions(c).get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        for i, f in enumerate(forms):  # SEC lists newest first
            if f == form:
                return FilingRef(
                    cik=c,
                    form=f,
                    accession=recent["accessionNumber"][i],
                    filing_date=recent["filingDate"][i],
                    report_date=recent.get("reportDate", [""] * len(forms))[i],
                    primary_document=recent["primaryDocument"][i],
                )
        message = f"No {form} found in recent filings for CIK {c}"
        if form == "10-K" and not has_annual_report(self.submissions(c)):
            raise NoAnnualReportError(message)
        raise EdgarNotFound(message)

    def filing_document(self, ref: FilingRef) -> StoredResponse:
        key = f"edgar/{ref.cik}/{ref.form}/{ref.accession}/{ref.primary_document}"
        return self._get(key, ref.url)

    # ---------- internals ----------
    def _get_json(self, key: str, url: str) -> dict:
        return json.loads(self._get(key, url).body)

    def _get(self, key: str, url: str) -> StoredResponse:
        if self.mode in ("replay", "live"):
            hit = self.store.get(key)
            if hit is not None:
                return hit
            if self.mode == "replay":
                raise FixtureMissing(
                    f"No recorded fixture for {key!r}. Run scripts/record_fixtures.py on a "
                    "machine with internet access."
                )
        body, content_type = self._fetch(url)
        return self.store.put(key, url, body, content_type)

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            wait = self.settings.sec_min_interval_s - (self._clock() - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._clock()

    def _fetch(self, url: str) -> tuple[bytes, str | None]:
        headers = {
            "User-Agent": self.settings.sec_user_agent or "",
            "Accept-Encoding": "gzip",
        }
        last_error = ""
        for attempt in range(len(BACKOFF_S) + 1):
            self._throttle()
            self.requests_made += 1
            try:
                status, resp_headers, body = self.transport(url, headers, self.timeout_s)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                status, resp_headers, body, last_error = None, {}, b"", str(e)
            if status == 200:
                return body, resp_headers.get("content-type")
            if status == 404:
                raise EdgarNotFound(f"SEC returned 404 for {url}")
            if status == 403:
                raise EdgarError(
                    f"SEC refused the request (403) for {url}. Check SEC_USER_AGENT is "
                    "'Name email' and that requests stay under 10 per second."
                )
            if status is not None and status not in RETRY_STATUSES:
                raise EdgarError(f"SEC returned HTTP {status} for {url}")
            last_error = last_error or f"HTTP {status}"
            if attempt < len(BACKOFF_S):
                self._sleep(_retry_delay(resp_headers, BACKOFF_S[attempt]))
        raise EdgarError(f"Giving up on {url} after {len(BACKOFF_S) + 1} attempts ({last_error})")
