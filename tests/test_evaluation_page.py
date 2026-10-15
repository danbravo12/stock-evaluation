"""The evaluation page (build 4b, ADR-073): every figure on it comes from the eval data, none is typed into the page source. Runs the page's own code with node. Offline."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from engine.evaluation import evaluation_data
from engine.settings import REPO_ROOT

NODE = shutil.which("node")
STUB = """
globalThis.document = { createElement: (tag) => ({ tag, kids: [], attrs: {}, nodeType: 1, append(...k) { this.kids.push(...k); }, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener() {},
  set textContent(t) { this.kids = [{ nodeType: 3, text: String(t) }]; } }), createTextNode: (t) => ({ nodeType: 3, text: t }) };
const { render } = await import("file://%s");
const data = JSON.parse(await new Promise((r) => { let s = ""; process.stdin.on("data", (d) => (s += d)); process.stdin.on("end", () => r(s)); }));
const text = (n) => n.nodeType === 3 ? n.text : n.kids.map(text).join(n.tag === "tr" ? " | " : n.tag === "td" || n.tag === "th" ? "" : "") + (["p", "li", "h2", "tr"].includes(n.tag) ? "\\n" : "");
console.log(render(data).map(text).join(""));
"""


def stability_rows() -> list[dict]:
    rows = []
    for f in sorted((REPO_ROOT / "results").glob("[0-9]*[0-9].json")):
        r = json.loads(f.read_text())
        rows.append({q["finding"]["criterion"]: q.get("stability") for q in r["qualitative"]})
    return rows


def render_text(data: dict) -> str:
    p = subprocess.run([NODE, "--input-type=module", "-e", STUB % (REPO_ROOT / "site_src/assets/js/evaluation.js")], input=json.dumps(data), capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[:1500])
    return p.stdout


@unittest.skipUnless(NODE, "node is not installed")
class TestEvaluationPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = evaluation_data(stability_rows())
        cls.text = render_text(cls.data)

    def test_the_headline_figures_are_the_frozen_ones(self):
        t = self.text
        self.assertIn("agreed with the human label on 11 of 12 judgements of criteria that are not marked low reliability, and on 2 of 12 of criteria that are", t)
        self.assertIn("agreed with the person on 12 of 17; findings whose verdict changed with the wording agreed on 1 of 6", t)
        self.assertIn("same level for 13 of 24 judgements (54%)", t)
        self.assertIn("within one level on 17 of 24 (71%)", t)
        self.assertIn("stricter than the person on 8 judgements and more generous on 2; 1 could not be assessed", t)
        self.assertIn("Weighted kappa, the agreement beyond chance, is 0.03 on 23 assessed judgements", t)
        self.assertIn("21 of 24 labels", t)

    def test_every_section_is_there_with_plain_language(self):
        for h in ("What we measured and how", "Headline: the tool's own warnings", "Overall agreement, honestly", "The dev-set lesson", "The Critic", "The numbers side", "What it gets wrong"):
            self.assertIn(h, self.text)
        self.assertIn("v1.1: 19 of 20", self.text)
        self.assertIn("v2: 14 of 20", self.text)
        self.assertIn("TSLA candid management went from found to weak although found was the human label", self.text)
        self.assertIn("cannot catch a false negative", self.text)
        self.assertIn("Threshold sensitivity", self.text)
        self.assertIn("G1 | Revenue at least | $1 billion | $0.8 billion: 0 | $1.2 billion: 0", self.text)
        self.assertIn("B1 | Years the return on equity must be met | 7 years | 6 years: 25 | 8 years: 30", self.text)

    def test_the_figures_follow_the_data(self):
        """Change the data and the page changes: nothing is typed in."""
        d = json.loads(json.dumps(self.data))
        d["heldout"]["exact"], d["heldout"]["within_one"] = 20, 22
        d["split"]["heldout"]["criterion_reliability"]["low"] = {"n": 12, "exact": 7}
        d["critic"]["flagged_first_pass"] = 31
        d["sensitivity"]["delta"] = 0.1
        t = render_text(d)
        self.assertIn("same level for 20 of 24 judgements (83%)", t)
        self.assertIn("and on 7 of 12 of criteria that are", t)
        self.assertIn("it flagged 31 on the first pass", t)
        self.assertIn("moved down and up by 10%", t)

    def test_the_sensitivity_headline_names_the_most_and_least_sensitive_tests(self):
        s = self.data["sensitivity"]
        self.assertEqual(s["ranking"][0], "B3")
        self.assertIn(f"{s['ranking'][-1]} ", self.text.split("the least sensitive is ")[1][:5])

    def test_the_page_source_has_no_hard_coded_figures(self):
        html = (REPO_ROOT / "site_src/evaluation.html").read_text()
        visible = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
        visible = re.sub(r"<[^>]+>", " ", visible)
        digit = re.search(r".{0,20}\d.{0,20}", visible)
        self.assertIsNone(digit, f"a digit in the page text: {digit and digit.group(0)}")
        js = (REPO_ROOT / "site_src/assets/js/evaluation.js").read_text()
        js = re.sub(r"//.*", "", js)
        strings = re.findall(r"`[^`]*`|\"[^\"\n]*\"", js)
        for s in strings:
            if s in ('"0"', '"h2"'):  # tabindex="0" and the heading tag
                continue
            outside = re.sub(r"\$\{[^}]*\}", "", s)  # a number written inside a text, outside any ${...}, is a typed figure
            self.assertIsNone(re.search(r"\d", outside), f"hard-coded figure in a text: {s[:90]}")
        code = re.sub(r"`[^`]*`|\"[^\"\n]*\"", "", js)
        literals = set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])", code))
        self.assertLessEqual(literals, {"0", "1", "2", "100"}, f"numeric literals in the page code: {literals}")

    def test_the_interval_is_the_wilson_interval(self):
        from engine.evaluation import wilson
        lo, hi = wilson(13, 24)
        self.assertAlmostEqual(lo, 0.3507, places=3)
        self.assertAlmostEqual(hi, 0.7211, places=3)
        self.assertEqual(self.data["heldout"]["interval"], {"low": lo, "high": hi, "level": 0.95})
        self.assertIn("a 95% interval for the exact figure runs from about 35% to 72%", self.text)

    def test_the_data_comes_from_eval_files_only(self):
        src = (REPO_ROOT / "engine/evaluation.py").read_text()
        for name in ("agreement_results.json", "agreement_history.json", "critic_summary.json", "universe_label_counts.json", "universe_diagnostics.json", "numeric_triage.json",
                     "sensitivity_results.json", "expected_scores.json"):
            self.assertIn(name, src)
        self.assertEqual(self.data["heldout"]["exact"], json.loads((REPO_ROOT / "eval/agreement_results.json").read_text())["heldout"]["exact"])

    def test_the_built_site_publishes_the_evaluation_data(self):
        from engine.publish import build_site
        from engine.settings import Settings
        from tests.test_site import sample_rankings, sample_results
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out = tmp / "site"
            build_site(out, results_dir=sample_results(tmp / "r"), rankings_path=sample_rankings(tmp / "k"), settings=Settings.from_env(), commit="test")
            self.assertTrue((out / "evaluation.html").exists())
            ev = json.loads((out / "data/evaluation.json").read_text())
            self.assertEqual(ev["heldout"]["exact"], 13)
            self.assertIn('href="evaluation.html"', (out / "index.html").read_text())  # linked in the header nav
            self.assertIn('href="evaluation.html"', (out / "company.html").read_text())


if __name__ == "__main__":
    unittest.main()
