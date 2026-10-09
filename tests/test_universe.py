"""S&P 500 snapshot: parsing, validation, dual-class rule, the committed CSV against SEC's ticker file (offline)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.fetch.edgar import EdgarClient
from engine.settings import Settings
from engine.universe import (MAX_ROWS, MIN_ROWS, Constituent, Universe, load_universe, parse_constituents_html, validate_universe, write_csv)

HTML = """<table class="wikitable" id="constituents"><tbody>
<tr><th>Symbol</th><th>Security</th><th>GICS Sector</th><th>GICS Sub-Industry</th><th>Headquarters Location</th><th>Date added</th><th>CIK</th><th>Founded</th></tr>
<tr><td><a href="x">BRK.B</a>\n</td><td>Berkshire Hathaway</td><td>Financials</td><td>Multi-Sector Holdings</td><td>Omaha</td><td>2010-02-16</td><td>0001067983</td><td>1839</td></tr>
<tr><td>GOOGL</td><td>Alphabet Inc. (Class A)<sup>[1]</sup></td><td>Communication Services</td><td>Interactive Media</td><td>Mountain View</td><td>2014-04-03</td><td>1652044</td><td>1998</td></tr>
<tr><td>GOOG</td><td>Alphabet Inc. (Class C)</td><td>Communication Services</td><td>Interactive Media</td><td>Mountain View</td><td></td><td>0001652044</td><td>1998</td></tr>
</tbody></table><table><tr><td>other table</td></tr></table>"""


def row(sym, cik, **kw):
    return Constituent(symbol=sym, security=kw.get("security", sym), gics_sector="Industrials", gics_sub_industry="X", cik=cik, date_added="")


def sec(*pairs):
    return {str(i): {"cik_str": int(c), "ticker": t, "title": t} for i, (t, c) in enumerate(pairs)}


class TestParsing(unittest.TestCase):
    def test_table_is_parsed_with_normalised_symbols_footnotes_removed_and_ciks_padded(self):
        rows = parse_constituents_html(HTML)
        self.assertEqual([r.symbol for r in rows], ["BRK-B", "GOOGL", "GOOG"])
        self.assertEqual(rows[1].security, "Alphabet Inc. (Class A)")
        self.assertEqual(rows[1].cik, "0001652044")
        self.assertEqual(rows[2].date_added, "")

    def test_missing_table_is_an_error(self):
        with self.assertRaises(ValueError):
            parse_constituents_html("<table><tr><td>x</td></tr></table>")


class TestValidation(unittest.TestCase):
    PRIMARY = ["GOOGL", "FOXA", "NWSA"]

    def good(self, n=500):
        rows = [row(f"T{i}", str(1000 + i).zfill(10)) for i in range(n)]
        return rows, sec(*[(r.symbol, int(r.cik)) for r in rows])

    def test_a_valid_snapshot_has_no_problems(self):
        rows, s = self.good()
        self.assertEqual(validate_universe(rows, s, self.PRIMARY), [])

    def test_row_count_duplicates_and_missing_or_mismatched_ciks(self):
        rows, s = self.good()
        self.assertIn("rows; expected", validate_universe(rows[:100], s, self.PRIMARY)[0])
        dup = rows + [row("T1", "0000099999")]
        self.assertTrue(any("duplicate symbol T1" in p for p in validate_universe(dup, s, self.PRIMARY)))
        missing = rows[:-1] + [row("ZZZ", "0000777777")]
        self.assertTrue(any("ZZZ: CIK 0000777777 is not in SEC" in p for p in validate_universe(missing, s, self.PRIMARY)))
        wrong = rows[:-1] + [row("T7", "0000000001")]
        self.assertTrue(any("differs from SEC's" in p or "not in SEC" in p for p in validate_universe(wrong, s, self.PRIMARY)))
        self.assertTrue(MIN_ROWS < MAX_ROWS)

    def test_dual_class_needs_exactly_one_primary_symbol(self):
        rows, s = self.good()
        rows = rows[:-2] + [row("GOOGL", "0001652044"), row("GOOG", "0001652044")]
        s = sec(*[(r.symbol, int(r.cik)) for r in rows])
        self.assertEqual(validate_universe(rows, s, self.PRIMARY), [])
        self.assertTrue(any("not exactly one primary symbol" in p for p in validate_universe(rows, s, [])))
        self.assertTrue(any("not exactly one primary symbol" in p for p in validate_universe(rows, s, ["GOOGL", "GOOG"])))

    def test_primary_keeps_one_row_per_cik_in_snapshot_order(self):
        rows = [row("AAA", "0000000001"), row("GOOG", "0001652044"), row("GOOGL", "0001652044"), row("BBB", "0000000002")]
        u = Universe(rows, "2026-01-01", self.PRIMARY)
        self.assertEqual([r.symbol for r in u.primary], ["AAA", "GOOGL", "BBB"])
        self.assertEqual(u.dual_class_groups(), [["GOOG", "GOOGL"]])
        self.assertEqual(u.primary_of(u.row_for("goog")).symbol, "GOOGL")
        self.assertEqual(u.row_for("brk.b"), None)

    def test_csv_round_trip_and_attribution(self):
        rows, _ = self.good(3)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sp500_2026-01-02.csv"
            write_csv(rows, path)
            u = load_universe(path)
        self.assertEqual((u.rows, u.snapshot_date), (rows, "2026-01-02"))
        self.assertEqual(u.attribution, "Constituents: Wikipedia, as of 2026-01-02 (CC BY-SA)")


class TestCommittedSnapshot(unittest.TestCase):
    def test_the_committed_snapshot_is_valid_against_the_sec_fixture(self):
        u = load_universe(sec_tickers=EdgarClient("replay", Settings.from_env()).company_tickers())  # raises ValueError listing every problem
        self.assertTrue(MIN_ROWS <= len(u.rows) <= MAX_ROWS)
        self.assertEqual(len(u.primary), len({r.cik for r in u.rows}))
        self.assertEqual(sorted(g[0] for g in u.dual_class_groups()), ["FOXA", "GOOGL", "NWSA"])
        self.assertEqual({p.symbol for p in u.primary} & {"GOOG", "FOX", "NWS"}, set())
        for t in ("KO", "JPM", "GOOGL", "TSLA", "DUK", "MET", "PLD"):
            self.assertIsNotNone(u.row_for(t), t)


if __name__ == "__main__":
    unittest.main()
