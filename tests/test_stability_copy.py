"""The company page's borderline mark and sentence (ADR-072). Runs the page's own code (site_src/assets/js/common.js) with node. Offline."""
from __future__ import annotations

import json
import shutil
import subprocess
import unittest

from engine.settings import REPO_ROOT

NODE = shutil.which("node")
SCRIPT = """
import { borderlineSentence, isBorderline, stabilityRows } from "file://%s";
const cases = JSON.parse(await new Promise((r) => { let s = ""; process.stdin.on("data", (d) => (s += d)); process.stdin.on("end", () => r(s)); }));
console.log(JSON.stringify(cases.map((st) => ({ border: isBorderline(st), sentence: borderlineSentence(st), rows: st ? stabilityRows(st) : null }))));
"""
F, W, I = "evidence found", "evidence weak", "insufficient evidence"


def run_node(cases):
    p = subprocess.run([NODE, "--input-type=module", "-e", SCRIPT % (REPO_ROOT / "site_src/assets/js/common.js")], input=json.dumps(cases), capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


@unittest.skipUnless(NODE, "node is not installed")
class TestBorderlineCopy(unittest.TestCase):
    def test_sentences(self):
        out = run_node([{"status": "borderline", "verdicts": {"main": W, "a": W, "b": I}},
                        {"status": "borderline", "verdicts": {"main": W, "a": F, "b": F}},
                        {"status": "stable", "verdicts": {"main": W, "a": W, "b": W}}, None])
        self.assertEqual(out[0]["sentence"], "When the question was reworded, the verdict came out as weak and insufficient in two other runs.")
        self.assertEqual(out[1]["sentence"], "When the question was reworded, the verdict came out as found in both other runs.")
        self.assertEqual([o["border"] for o in out], [True, True, False, False])
        self.assertIsNone(out[2]["sentence"])
        self.assertIsNone(out[3]["sentence"])

    def test_the_three_verdicts_are_listed_in_plain_words(self):
        rows = run_node([{"status": "borderline", "verdicts": {"main": F, "a": W, "b": I}}])[0]["rows"]
        self.assertEqual(rows, [["Main run", "Evidence found"], ["Question reworded, version A", "Evidence weak"], ["Question reworded, version B", "Insufficient evidence"]])

    def test_the_page_uses_the_helpers(self):
        js = (REPO_ROOT / "site_src/assets/js/company.js").read_text()
        for name in ("borderlineSentence", "isBorderline", "stabilityRows"):
            self.assertIn(name, js)
        self.assertIn('"Borderline"', js)


if __name__ == "__main__":
    unittest.main()
