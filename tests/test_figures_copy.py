"""Figure lines on the company page: an empty list is a sentence, never a label followed by "none". Runs the page's own formatting code (site_src/assets/js/common.js) with node. Offline."""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest

from engine.settings import REPO_ROOT

NODE = shutil.which("node")
SCRIPT = """
import { figures, figureSummary } from "file://%s";
const criteria = JSON.parse(await new Promise((r) => { let s = ""; process.stdin.on("data", (d) => (s += d)); process.stdin.on("end", () => r(s)); }));
console.log(JSON.stringify(criteria.map((c) => ({ id: c.id, rows: figures(c), summary: figureSummary(c) }))));
"""


def run_node(criteria):
    p = subprocess.run([NODE, "--input-type=module", "-e", SCRIPT % (REPO_ROOT / "site_src/assets/js/common.js"), ], input=json.dumps(criteria), capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


@unittest.skipUnless(NODE, "node is not installed")
class TestFigureCopy(unittest.TestCase):
    def lines(self, out):
        for c in out:
            for r in c["rows"]:
                yield c["id"], " ".join(r)
            yield c["id"], c["summary"]

    def test_empty_lists_are_sentences(self):
        out = run_node([{"id": "B4", "figures": {"years_positive": 10, "years_with_depreciation_only": []}},
                        {"id": "G3", "figures": {"years_on_record": 10, "loss_years": []}},
                        {"id": "G4", "figures": {"years_on_record": 15, "unpaid_years": [], "unknown_years": []}},
                        {"id": "G3", "figures": {"years_on_record": 10, "loss_years": [2019, 2020]}}])
        self.assertEqual(out[0]["rows"], [["Years with positive owner earnings", "10"], ["No years where only depreciation was reported."]])
        self.assertEqual(out[1]["rows"][1], ["No loss years."])
        self.assertEqual(out[2]["rows"][1:], [["No years without a dividend."], ["No years with missing dividend data."]])
        self.assertEqual(out[3]["rows"][1], ["Loss years", "2019, 2020"])  # a list with years keeps its label and value
        for _, line in self.lines(out):
            self.assertFalse(line.endswith(" none"), line)

    def test_no_rendered_figure_line_of_any_recorded_result_ends_in_none(self):
        criteria = []
        for c in ("0000021344", "0000019617", "0001652044", "0001318605", "0001326160"):
            criteria += json.loads((REPO_ROOT / "results" / f"{c}.json").read_text())["scorecard"]["criteria"]
        out = run_node(criteria)
        self.assertEqual(len(out), 55)
        n = 0
        for cid, line in self.lines(out):
            self.assertFalse(line.endswith(" none") or " none;" in line or line.endswith("none."), f"{cid}: {line}")
            n += 1
        self.assertGreater(n, 100)

    def test_summary_line_for_a_row_without_an_explanation(self):
        out = run_node([{"id": "G3", "figures": {"years_on_record": 10, "loss_years": []}}, {"id": "G1", "figures": {"revenue": 8.79e9}}])
        self.assertEqual(out[0]["summary"], "No loss years")
        self.assertEqual(out[1]["summary"], "Revenue $8.79B")


if __name__ == "__main__":
    unittest.main()
