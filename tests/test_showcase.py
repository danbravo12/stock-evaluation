"""The showcase list (config/showcase.json, ADR-070): valid, resolved against the rankings, and every reason checked against the committed scores. Offline."""
from __future__ import annotations

import json
import unittest

from engine.publish import showcase_data
from engine.rankings import Rankings
from engine.settings import REPO_ROOT
from engine.universe import load_universe

CONFIG = json.loads((REPO_ROOT / "config" / "showcase.json").read_text(encoding="utf-8"))
RANKINGS = Rankings.model_validate_json((REPO_ROOT / "site_data" / "rankings.json").read_text(encoding="utf-8"))
ROWS = {r.symbol: r for r in RANKINGS.criteria_ranking.ranked + RANKINGS.criteria_ranking.ranked_financials + RANKINGS.criteria_ranking.insufficient_data}


class TestConfig(unittest.TestCase):
    def test_twenty_distinct_companies_of_the_snapshot_each_with_a_reason(self):
        syms = [e["symbol"] for e in CONFIG["showcase"]]
        self.assertEqual(len(syms), 20)
        self.assertEqual(len(set(syms)), 20)
        universe = {r.symbol for r in load_universe().primary}
        self.assertTrue(set(syms) <= universe)
        tests = [e["symbol"] for e in CONFIG["test_companies"]]
        self.assertEqual(tests, ["KO", "JPM", "GOOGL", "TSLA", "DUK"])
        self.assertFalse(set(tests) & set(syms))
        for e in CONFIG["showcase"] + CONFIG["test_companies"]:
            self.assertTrue(e["why"].endswith("."), e)
            self.assertLess(len(e["why"]), 220, e)
        self.assertTrue(all(e["group"].split(": ")[0] in ("Top of the ranking", "Large and familiar", "Edge case") for e in CONFIG["showcase"]))

    def test_the_groups_match_the_brief(self):
        by = {}
        for e in CONFIG["showcase"]:
            by.setdefault(e["group"].split(": ")[0], []).append(e["symbol"])
        self.assertEqual(by["Top of the ranking"], ["AMAT", "FAST", "COST"])
        self.assertEqual(by["Large and familiar"], ["MSFT", "AAPL", "NVDA", "META", "JNJ", "PG", "MCD", "CAT"])
        self.assertEqual(by["Edge case"], ["XOM", "BRK-B", "UNH", "MET", "GS", "PLD", "O", "NEE", "VST"])


class TestReasonsAreTrue(unittest.TestCase):
    """Each line the site shows is a claim about the data; these fail if a rule change makes one untrue."""

    def L(self, s):
        return ROWS[s].labels

    def test_top_of_the_ranking(self):
        for s in ("AMAT", "FAST"):
            self.assertEqual((ROWS[s].met, ROWS[s].decided), (9, 9), s)
        self.assertEqual((ROWS["COST"].met, ROWS["COST"].decided, self.L("COST")["G2"]), (8, 9, "fail"))
        self.assertTrue(all(v in ("pass", "partial_pass") for k, v in self.L("COST").items() if k not in ("G2", "G6", "G7")))

    def test_large_and_familiar(self):
        self.assertEqual([k for k, v in self.L("MSFT").items() if v == "fail"], ["G2"])
        self.assertEqual([k for k, v in self.L("AAPL").items() if v == "fail"], ["G2", "G4"])
        self.assertEqual(self.L("NVDA")["G4"], "fail")
        self.assertEqual(self.L("NVDA")["B4"], "data_gap")
        self.assertEqual([k for k, v in self.L("META").items() if v == "fail"], ["G4"])
        self.assertEqual(self.L("JNJ")["B3"], "data_gap")
        self.assertEqual((self.L("MCD")["B1"], self.L("MCD")["B2"]), ("not_meaningful", "fail"))
        self.assertEqual(self.L("CAT")["G3"], "fail")

    def test_edge_cases(self):
        self.assertTrue(ROWS["XOM"].notes[0].startswith("Figures from predecessor registrant Exxon Mobil Corp"))
        self.assertTrue(ROWS["BRK-B"].notes[0].startswith("Conglomerate with large insurance operations"))
        self.assertEqual(ROWS["BRK-B"].group, "insufficient_data")
        self.assertEqual((ROWS["UNH"].sector_class, ROWS["UNH"].decided), ("other", 9))
        self.assertEqual((ROWS["MET"].sector_class, [k for k, v in self.L("MET").items() if v == "not_applicable"]), ("insurer", ["G2", "B2", "B3", "B4"]))
        self.assertEqual((ROWS["GS"].sector_class, ROWS["GS"].notes), ("bank", []))
        self.assertTrue(ROWS["PLD"].sector_class == "reit" and ROWS["PLD"].notes[0].startswith("REIT:") and self.L("PLD")["G4"] == "partial_pass")
        self.assertEqual((ROWS["O"].sector_class, ROWS["O"].group), ("reit", "insufficient_data"))
        self.assertEqual((ROWS["NEE"].sector_class, self.L("NEE")["G2"]), ("utility", "pass"))
        self.assertEqual(ROWS["VST"].notes, ["Not rate-regulated, so Graham's utility variant does not apply."])


class TestResolution(unittest.TestCase):
    def test_the_list_is_resolved_in_order_and_missing_companies_are_named(self):
        data = showcase_data(RANKINGS)
        titles = [g["title"] for g in data["groups"]]
        self.assertEqual(titles, [t for t in CONFIG["groups"] if t in titles])
        present = [i["symbol"] for g in data["groups"] for i in g["items"]]
        self.assertEqual(sorted(present + data["missing"]), sorted([e["symbol"] for e in CONFIG["showcase"]] + [e["symbol"] for e in CONFIG["test_companies"]]))
        first = data["groups"][0]["items"][0]
        self.assertEqual(set(first), {"symbol", "name", "cik", "tag", "why", "rank", "rank_group"})

    def test_after_the_batch_nobody_is_missing(self):
        """Needs the 20 showcase results committed under results/ (has_full_analysis in the committed rankings)."""
        self.assertEqual(showcase_data(RANKINGS)["missing"], [])


if __name__ == "__main__":
    unittest.main()
