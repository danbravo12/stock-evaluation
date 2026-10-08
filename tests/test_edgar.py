"""Offline tests for the EDGAR client and response store. Run: python3 -m unittest -v"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.fetch.edgar import EdgarClient, EdgarError, EdgarNotFound, FixtureMissing
from engine.fetch.store import ResponseStore
from engine.settings import Settings
from engine.universe import cik10, normalise_ticker

UA = "StockEvaluation tests test@example.com"

TICKERS = {
    "0": {"cik_str": 21344, "ticker": "KO", "title": "COCA COLA CO"},
    "1": {"cik_str": 1067983, "ticker": "BRK-B", "title": "BERKSHIRE HATHAWAY INC"},
}
SUBMISSIONS = {
    "cik": "21344",
    "filings": {
        "recent": {
            "form": ["8-K", "10-K/A", "10-K", "10-Q", "10-K"],
            "accessionNumber": ["a-1", "a-2", "0000021344-25-000011", "a-4", "a-5"],
            "filingDate": ["2025-04-01", "2025-03-01", "2025-02-20", "2024-10-25", "2024-02-20"],
            "reportDate": ["", "2024-12-31", "2024-12-31", "2024-09-27", "2023-12-31"],
            "primaryDocument": ["x.htm", "y.htm", "ko-20241231.htm", "z.htm", "w.htm"],
        }
    },
}


class FakeTransport:
    """Scripted responses per URL substring; records every call."""

    def __init__(self, routes: dict[str, list[tuple[int, bytes]]], extra_headers: dict | None = None):
        self.extra_headers = extra_headers or {}
        self.routes = {k: list(v) for k, v in routes.items()}
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url, headers, timeout):
        self.calls.append((url, headers))
        for fragment, queue in self.routes.items():
            if fragment in url:
                status, body = queue.pop(0) if len(queue) > 1 else queue[0]
                return status, {"content-type": "application/json", **self.extra_headers}, body
        return 404, {}, b""


def js(obj) -> bytes:
    return json.dumps(obj).encode()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.settings = Settings(
            sec_user_agent=UA, fixtures_dir=root / "fixtures", cache_dir=root / "cache"
        )
        self.sleeps: list[float] = []

    def tearDown(self):
        self.tmp.cleanup()

    def client(self, mode, transport=None, settings=None):
        return EdgarClient(
            mode,
            settings or self.settings,
            transport=transport or FakeTransport({}),
            sleep=self.sleeps.append,
            clock=lambda: 0.0,  # frozen clock: every request after the first must wait
        )


class TestHelpers(unittest.TestCase):
    def test_normalise_ticker(self):
        for raw in ("brk.b", "BRK/B", " BRK-B ", "brk b"):
            self.assertEqual(normalise_ticker(raw), "BRK-B")

    def test_cik10(self):
        self.assertEqual(cik10(21344), "0000021344")
        self.assertEqual(cik10("0000021344"), "0000021344")


class TestStore(Base):
    def test_roundtrip_and_checksum(self):
        store = ResponseStore(self.settings.fixtures_dir)
        store.put("edgar/x/a.json", "https://example/a", b'{"a":1}', "application/json")
        got = store.get("edgar/x/a.json")
        self.assertEqual(got.body, b'{"a":1}')
        self.assertEqual(got.url, "https://example/a")

    def test_tampered_body_is_rejected(self):
        import gzip

        store = ResponseStore(self.settings.fixtures_dir)
        store.put("k.json", "u", b"original")
        (self.settings.fixtures_dir / "k.json.gz").write_bytes(gzip.compress(b"changed"))
        with self.assertRaises(ValueError):
            store.get("k.json")


class TestModes(Base):
    def test_replay_never_uses_network(self):
        transport = FakeTransport({"company_tickers": [(200, js(TICKERS))]})
        with self.assertRaises(FixtureMissing):
            self.client("replay", transport).company_tickers()
        self.assertEqual(transport.calls, [])

    def test_record_then_replay(self):
        transport = FakeTransport({"company_tickers": [(200, js(TICKERS))]})
        self.client("record", transport).company_tickers()
        replay_transport = FakeTransport({})
        data = self.client("replay", replay_transport).company_tickers()
        self.assertEqual(data["0"]["ticker"], "KO")
        self.assertEqual(replay_transport.calls, [])

    def test_live_caches_after_first_fetch(self):
        transport = FakeTransport({"company_tickers": [(200, js(TICKERS))]})
        c = self.client("live", transport)
        c.company_tickers()
        c.company_tickers()
        self.assertEqual(len(transport.calls), 1)
        self.assertTrue((self.settings.cache_dir / "edgar/company_tickers.json.gz").exists())

    def test_user_agent_required_for_network_modes(self):
        no_ua = Settings(None, self.settings.fixtures_dir, self.settings.cache_dir)
        for mode in ("live", "record"):
            with self.assertRaises(EdgarError):
                self.client(mode, settings=no_ua)
        self.client("replay", settings=no_ua)  # replay needs no network, so no UA

    def test_user_agent_sent(self):
        transport = FakeTransport({"company_tickers": [(200, js(TICKERS))]})
        self.client("record", transport).company_tickers()
        self.assertEqual(transport.calls[0][1]["User-Agent"], UA)


class TestNetworkBehaviour(Base):
    def test_retries_transient_errors_then_succeeds(self):
        transport = FakeTransport(
            {"company_tickers": [(503, b""), (429, b""), (200, js(TICKERS))]}
        )
        self.client("record", transport).company_tickers()
        self.assertEqual(len(transport.calls), 3)
        self.assertIn(1.0, self.sleeps)
        self.assertIn(2.0, self.sleeps)

    def test_honours_retry_after(self):
        transport = FakeTransport(
            {"company_tickers": [(429, b""), (200, js(TICKERS))]}, {"retry-after": "7"}
        )
        self.client("record", transport).company_tickers()
        self.assertIn(7.0, self.sleeps)

    def test_retries_connection_errors(self):
        calls = []

        def flaky(url, headers, timeout):
            calls.append(url)
            if len(calls) == 1:
                raise ConnectionResetError("boom")
            return 200, {}, js(TICKERS)

        self.client("record", flaky).company_tickers()
        self.assertEqual(len(calls), 2)

    def test_gives_up_after_four_attempts(self):
        transport = FakeTransport({"company_tickers": [(503, b"")]})
        with self.assertRaises(EdgarError):
            self.client("record", transport).company_tickers()
        self.assertEqual(len(transport.calls), 4)

    def test_403_and_404_do_not_retry(self):
        for status, exc in ((403, EdgarError), (404, EdgarNotFound)):
            transport = FakeTransport({"company_tickers": [(status, b"")]})
            with self.assertRaises(exc):
                self.client("record", transport).company_tickers()
            self.assertEqual(len(transport.calls), 1)

    def test_throttle_between_requests(self):
        transport = FakeTransport({"company_tickers": [(200, js(TICKERS))]})
        c = self.client("record", transport)
        c.company_tickers()
        c.company_tickers()
        self.assertIn(self.settings.sec_min_interval_s, self.sleeps)


class TestFilings(Base):
    def setUp(self):
        super().setUp()
        self.transport = FakeTransport(
            {
                "company_tickers": [(200, js(TICKERS))],
                "submissions/CIK0000021344": [(200, js(SUBMISSIONS))],
                "Archives/edgar/data/21344/000002134425000011/ko-20241231.htm": [
                    (200, b"<html>Item 1. Business</html>")
                ],
            }
        )

    def test_lookup_cik_normalises(self):
        c = self.client("record", self.transport)
        self.assertEqual(c.lookup_cik("brk.b")[0], "0001067983")
        with self.assertRaises(EdgarNotFound):
            c.lookup_cik("NOPE")

    def test_latest_10k_skips_amendments(self):
        ref = self.client("record", self.transport).latest_filing(21344)
        self.assertEqual(ref.accession, "0000021344-25-000011")
        self.assertEqual(ref.report_date, "2024-12-31")
        self.assertEqual(
            ref.url,
            "https://www.sec.gov/Archives/edgar/data/21344/000002134425000011/ko-20241231.htm",
        )

    def test_filing_document_recorded_with_provenance(self):
        c = self.client("record", self.transport)
        doc = c.filing_document(c.latest_filing(21344))
        self.assertIn(b"Item 1", doc.body)
        replay = self.client("replay")
        again = replay.filing_document(replay.latest_filing(21344))
        self.assertEqual(again.sha256, doc.sha256)
        self.assertTrue(again.url.startswith("https://www.sec.gov/Archives/"))


if __name__ == "__main__":
    unittest.main()
