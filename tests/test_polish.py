"""Build 5: README and documents, the decision index, the architecture drawing, the mobile swimlane and heading structure. Offline."""
from __future__ import annotations

import re
import runpy
import unittest

from engine.settings import REPO_ROOT

AUDIENCE = re.compile(r"interview|hiring|recruiter|portfolio piece|career|impress", re.I)


class TestReadme(unittest.TestCase):
    def test_structure_and_links(self):
        s = (REPO_ROOT / "README.md").read_text()
        for h in ("## A two-minute tour", "## Architecture in brief", "## Cost", "### With a production budget", "## Evaluation in three lines", "## Running it locally", "## Project documents", "## Data and licences"):
            self.assertIn(h, s)
        self.assertIsNone(AUDIENCE.search(s))
        tour = s.split("## A two-minute tour")[1].split("## Architecture")[0]
        self.assertEqual(len(re.findall(r"^\d\. ", tour, flags=re.M)), 5)
        for page in ("index.html", "company.html?cik=", "trace.html?cik=", "evaluation.html", "how-it-works.html"):
            self.assertIn(page, tour)
        self.assertIn("not financial advice", s.lower())
        self.assertIn("site_src/assets/img/architecture.svg", s)

    def test_no_audience_framing_in_the_documents(self):
        for f in ("README.md", "ARCHITECTURE.md", "STATUS.md", "DECISIONS.md", "PROCESS.md", "FILEMAP.md", "site_src/how-it-works.html", "site_src/evaluation.html"):
            self.assertIsNone(AUDIENCE.search((REPO_ROOT / f).read_text()), f)


class TestDecisionIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (REPO_ROOT / "DECISIONS.md").read_text()

    def test_every_entry_has_one_index_row_in_number_order(self):
        heads = re.findall(r"^### (ADR-\d+|V2-\d+) ", self.text, flags=re.M)
        rows = re.findall(r"^\| \[(ADR-\d+|V2-\d+)\]", self.text, flags=re.M)
        self.assertEqual(sorted(heads, key=lambda h: (h.startswith("V2"), int(h.split("-")[1]))), rows)
        self.assertEqual(len(set(rows)), len(rows))

    def test_index_links_resolve_to_headings(self):
        def slug(h):
            return re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
        slugs = {slug(h) for h in re.findall(r"^### (.+)$", self.text, flags=re.M)}
        for link in re.findall(r"\]\(#([^)]+)\)", self.text):
            self.assertIn(link, slugs, link)

    def test_superseded_entries_link_to_their_replacement(self):
        for a, b in (("ADR-045", "ADR-046"), ("ADR-033", "ADR-057")):
            row = next(r for r in self.text.split("\n") if r.startswith(f"| [{a}]"))
            self.assertIn(f"[{b}]", row)
        self.assertIn("Superseded by [ADR-046]", self.text.split("### ADR-045")[1].split("### ADR-046")[0])

    def test_every_amendment_is_dated(self):
        for m in re.finditer(r"\*\*Amend(?:ment|ed)\b[^*]*\*\*", self.text):
            self.assertRegex(m.group(0), r"\d{4}-\d{2}-\d{2}", m.group(0))


class TestDrawing(unittest.TestCase):
    def test_the_committed_svg_is_what_the_generator_writes(self):
        mod = runpy.run_path(str(REPO_ROOT / "scripts/architecture_svg.py"))
        self.assertEqual((REPO_ROOT / "site_src/assets/img/architecture.svg").read_text(), mod["svg"])

    def test_it_is_self_contained_and_covers_the_built_components(self):
        svg = (REPO_ROOT / "site_src/assets/img/architecture.svg").read_text()
        self.assertIn("prefers-color-scheme:dark", svg)
        for word in ("Planner and orchestrator", "Scorers", "Qualitative agent", "Explainer", "Critic", "Reporter", "Stability runs", "Evaluation harness", "Publish gates", "secret scan", "Static site"):
            self.assertIn(word, svg)

    def test_publish_inlines_it_into_how_it_works(self):
        html = (REPO_ROOT / "site_src/how-it-works.html").read_text()
        self.assertIn("__ARCHITECTURE_SVG__", html)
        self.assertNotIn("<svg", html)


class TestSwimlane(unittest.TestCase):
    def test_agent_names_are_outside_the_scrolling_plot(self):
        js = (REPO_ROOT / "site_src/assets/js/trace.js").read_text()
        self.assertIn("swimlabels", js)
        self.assertIn("labelW", js)
        css = (REPO_ROOT / "site_src/assets/site.css").read_text()
        self.assertRegex(css, r"figure\.swim \.swimwrap \{ display: flex")
        self.assertIn("svg.swimlabels", css)


class TestHeadings(unittest.TestCase):
    def test_lists_use_h2_under_the_page_h1_and_the_doc_viewer_maps_levels_exactly(self):
        for f in ("company.js", "index.js"):
            js = (REPO_ROOT / "site_src/assets/js" / f).read_text()
            self.assertNotIn('el("h3", { text: title })', js)
        self.assertIn("Math.min(h[1].length, 4)", (REPO_ROOT / "site_src/assets/js/doc.js").read_text())

    def test_the_audit_script_is_there(self):
        self.assertIn("lowContrast", (REPO_ROOT / "scripts/site_audit.mjs").read_text())


if __name__ == "__main__":
    unittest.main()
