"""The static site and the publish command (ADR-065, ADR-066): determinism, disclaimer, the Finnhub gate, banned phrases, links, schemas, size. Offline."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import jsonschema

from engine.publish import DOCS, PAGES, BannedPhraseError, LinkError, SITE_SRC, build_site
from engine.report import PublishGateError, SCHEMA_PATH as RESULT_SCHEMA
from engine.settings import REPO_ROOT, Settings
from engine.rankings import SCHEMA_PATH as RANKINGS_SCHEMA

SAMPLES = ["0000021344", "0000019617", "0001652044", "0001318605", "0001326160"]


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def sample_rankings(dest: Path) -> Path:
    """The committed rankings with only the five test companies marked as fully analysed, to go with `sample_results` (the 20 showcase results are not copied)."""
    rk = json.loads((REPO_ROOT / "site_data" / "rankings.json").read_text())
    for group in ("ranked", "ranked_financials", "insufficient_data"):
        for row in rk["criteria_ranking"][group]:
            if row["cik"] not in SAMPLES:
                row["has_full_analysis"], row["analysis_path"] = False, None
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "rankings.json"
    path.write_text(json.dumps(rk), encoding="utf-8")
    return path


def sample_results(dest: Path) -> Path:
    """The five committed full results and traces, in a temporary results folder (no score files: those are local)."""
    dest.mkdir(parents=True, exist_ok=True)
    for c in SAMPLES:
        for suffix in (".json", ".trace.jsonl"):
            shutil.copy(REPO_ROOT / "results" / f"{c}{suffix}", dest / f"{c}{suffix}")
    return dest


class SiteCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.results = sample_results(cls.tmp / "results")
        cls.settings = Settings.from_env()
        cls.out = cls.tmp / "site"
        cls.rankings = sample_rankings(cls.tmp / "rk")
        cls.manifest = build_site(cls.out, results_dir=cls.results, rankings_path=cls.rankings, settings=cls.settings, commit="test")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()


class TestBuild(SiteCase):
    def test_deterministic(self):
        again = build_site(self.tmp / "site2", results_dir=self.results, rankings_path=self.rankings, settings=self.settings, commit="test")
        self.assertEqual(tree_hash(self.out), tree_hash(self.tmp / "site2"))
        self.assertEqual(again, self.manifest)

    def test_showcase_list_is_resolved_from_the_config(self):
        sc = json.loads((self.out / "data/showcase.json").read_text())
        # this build has only the five test companies' results, so the 20 showcase companies are named as missing and the five are listed
        self.assertEqual([g["title"] for g in sc["groups"]], ["The five test companies"])
        self.assertEqual([i["symbol"] for i in sc["groups"][0]["items"]], ["KO", "JPM", "GOOGL", "TSLA", "DUK"])
        self.assertEqual(len(sc["missing"]), 20)
        self.assertEqual(self.manifest["showcase_missing"], sc["missing"])
        first = sc["groups"][0]["items"][0]
        self.assertEqual((first["name"], first["cik"]), ("The Coca-Cola Company", "0000021344"))

    def test_outputs_exist(self):
        for page in PAGES:
            self.assertTrue((self.out / page).exists(), page)
        d = self.out / "data"
        self.assertTrue((d / "rankings.json").exists() and (d / "manifest.json").exists())
        for c in SAMPLES:
            for f in (f"{c}.json", f"{c}.trace.json", f"{c}.passages.json", f"{c}.explain.json"):
                self.assertTrue((d / "results" / f).exists(), f)
        for name in DOCS:
            self.assertTrue((d / "docs" / f"{name}.md").exists(), name)
        self.assertEqual(self.manifest["counts"]["full_analysis"], 5)
        self.assertEqual(self.manifest["build_commit"], "test")

    def test_every_page_has_the_disclaimer_near_the_top(self):
        for page in PAGES:
            html = (self.out / page).read_text(encoding="utf-8")
            body = html[html.index("<body"):]
            self.assertIn("not financial advice", body[:2500].lower(), page)
            self.assertIn('lang="en"', html[:200])
            self.assertIn("<title>", html)

    def test_cited_passages_contain_the_cited_quotes(self):
        res = json.loads((self.out / "data/results/0000021344.json").read_text())
        passages = json.loads((self.out / "data/results/0000021344.passages.json").read_text())
        n = 0
        for q in res["qualitative"]:
            for c in q["finding"]["citations"]:
                p = passages[c["passage_id"]]
                self.assertEqual(p["text"][c["char_start"] - p["char_start"]:c["char_end"] - p["char_start"]], c["quote"])
                n += 1
        self.assertGreater(n, 3)

    def test_trace_is_the_recorded_run(self):
        trace = json.loads((self.out / "data/results/0000021344.trace.json").read_text())
        lines = (self.results / "0000021344.trace.jsonl").read_text().splitlines()
        self.assertEqual(len(trace["steps"]), len(lines))
        self.assertEqual([s["raw_step"] for s in trace["steps"]], list(range(1, len(lines) + 1)))
        self.assertEqual([l["id"] for l in trace["lanes"]], ["orchestrator", "scorers", "qualitative", "explainer", "critic", "reporter"])
        text = json.dumps(trace)
        self.assertIn("Passage 1:8: Our finished product operations", text)  # the searches list the passages they found, from the recorded 10-K
        ex = json.loads((self.out / "data/results/0000021344.explain.json").read_text())
        self.assertEqual(ex["name"], "The Coca-Cola Company")

    def test_size_of_the_index_page(self):
        total = sum(p.stat().st_size for p in [self.out / "index.html", self.out / "assets/site.css", self.out / "data/rankings.json", self.out / "data/manifest.json",
                                               *(self.out / "assets/js").glob("*.js"), self.out / "assets/fonts/public-sans-latin-400-normal.woff2",
                                               self.out / "assets/fonts/public-sans-latin-600-normal.woff2"])
        self.assertLess(total, 1_500_000, total)


class TestGates(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.results = sample_results(self.tmp / "results")
        self.sample_rankings = sample_rankings(self.tmp / "rk0")
        self.settings = Settings.from_env()

    def build(self, **kw):
        kw.setdefault("rankings_path", self.sample_rankings)
        return build_site(self.tmp / "site", results_dir=kw.pop("results", self.results), settings=self.settings, commit="t", **kw)

    def test_a_planted_finnhub_field_fails_the_build_and_leaves_no_site(self):
        rk = json.loads(self.sample_rankings.read_text())
        rk["criteria_ranking"]["ranked"][0]["labels"]["price"] = "12.3"
        path = self.tmp / "rk.json"
        path.write_text(json.dumps(rk))
        with self.assertRaises(PublishGateError):
            self.build(rankings_path=path, finnhub_public_ok=False)
        self.assertFalse((self.tmp / "site").exists() or (self.tmp / "site.building").exists())
        self.build(rankings_path=path, finnhub_public_ok=True)  # with permission the same data goes through
        self.assertTrue((self.tmp / "site" / "index.html").exists())

    def test_a_planted_field_in_a_result_fails_too(self):
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["data"]["analyst_buy"] = 12
        f.write_text(json.dumps(d))
        with self.assertRaises(PublishGateError):
            self.build(finnhub_public_ok=False)

    def test_a_banned_word_in_the_site_copy_fails_the_build(self):
        src = self.tmp / "src"
        shutil.copytree(SITE_SRC, src)
        p = src / "how-it-works.html"
        p.write_text(p.read_text().replace("<h1>How it works</h1>", "<h1>How it works</h1><p>This stock is undervalued.</p>"))
        with self.assertRaises(BannedPhraseError):
            self.build(site_src=src)
        self.assertFalse((self.tmp / "site").exists())

    def test_a_banned_phrase_in_a_model_written_line_fails_the_build(self):
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["qualitative"][0]["finding"]["rationale"] = "Investors should buy this."
        f.write_text(json.dumps(d))
        with self.assertRaises(BannedPhraseError):
            self.build()

    def test_a_non_sec_link_fails_the_build(self):
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["data"]["filing"]["url"] = "http://example.com/ko-10k.htm"
        f.write_text(json.dumps(d))
        with self.assertRaises(LinkError):
            self.build()

    def test_verbatim_filing_quotes_are_not_scanned_as_advice(self):  # a 10-K may use any word; only the project's and the model's own text is checked
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["qualitative"][0]["finding"]["citations"][0]["quote"] = "Analysts say shares are undervalued."
        f.write_text(json.dumps(d))
        self.build()


class TestLinksAndSchemas(SiteCase):
    def test_static_links_and_assets_resolve(self):
        for page in PAGES:
            html = (self.out / page).read_text(encoding="utf-8")
            for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
                if ref.startswith(("http", "#", "mailto:", "data:")):
                    continue
                target = ref.split("#")[0].split("?")[0]
                self.assertTrue((self.out / target).exists(), f"{page} -> {ref}")

    def test_links_and_data_paths_built_by_the_scripts_resolve(self):
        for js in (self.out / "assets/js").glob("*.js"):
            text = js.read_text(encoding="utf-8")
            for page in set(re.findall(r'["`]((?:index|company|trace|how-it-works|doc)\.html)', text)):
                self.assertTrue((self.out / page).exists(), f"{js.name} -> {page}")
            for ref in set(re.findall(r'["`](data/[A-Za-z0-9_./-]+\.json)["`]', text)):
                self.assertTrue((self.out / ref).exists(), f"{js.name} -> {ref}")
            for d in set(re.findall(r'`(data/[a-z]+)/\$\{', text)):
                if d != "data/scores":  # score files come from the local numeric run, which a clean checkout does not have
                    self.assertTrue((self.out / d).is_dir(), f"{js.name} -> {d}")
        doc_js = (self.out / "assets/js/doc.js").read_text()
        for name in re.search(r"ALLOWED = \[(.*?)\]", doc_js).group(1).replace('"', "").split(", "):
            self.assertTrue((self.out / "data/docs" / f"{name}.md").exists(), name)
        for page in PAGES:  # links to documents and to company pages from the static pages
            for ref in re.findall(r'href="(doc\.html\?f=(\w+))"', (self.out / page).read_text()):
                self.assertTrue((self.out / "data/docs" / f"{ref[1]}.md").exists(), ref[0])

    def test_every_company_in_the_rankings_with_a_full_analysis_has_its_files(self):
        rk = json.loads((self.out / "data/rankings.json").read_text())
        rows = rk["criteria_ranking"]["ranked"] + rk["criteria_ranking"]["ranked_financials"] + rk["criteria_ranking"]["insufficient_data"]
        full = [r for r in rows if r["has_full_analysis"]]
        self.assertEqual(sorted(r["cik"] for r in full), sorted(SAMPLES))
        for r in full:
            self.assertTrue((self.out / "data/results" / f"{r['cik']}.trace.json").exists())

    def test_every_sec_link_in_the_data_is_https_sec_gov(self):
        n = 0
        for p in (self.out / "data").rglob("*.json"):
            for url in re.findall(r'"(?:source_url|url)":"([^"]+)"', p.read_text(encoding="utf-8")):
                self.assertRegex(url, r"^https://([a-z]+\.)?sec\.gov/", p.name)
                n += 1
        self.assertGreater(n, 50)

    def test_json_validates_against_the_schemas(self):
        rk = json.loads((self.out / "data/rankings.json").read_text())
        jsonschema.validate(rk, json.loads(RANKINGS_SCHEMA.read_text()))
        schema = json.loads(RESULT_SCHEMA.read_text())
        for c in SAMPLES:
            jsonschema.validate(json.loads((self.out / "data/results" / f"{c}.json").read_text()), schema)
        m = self.manifest
        self.assertEqual(set(m), {"build_commit", "data_as_of", "attribution", "counts", "full_analysis", "caveats", "repo_url", "branch", "docs", "showcase_missing"})

    def test_the_scripts_set_no_inner_html_from_data(self):  # data is always inserted as text nodes
        for js in (self.out / "assets/js").glob("*.js"):
            body = js.read_text(encoding="utf-8")
            for m in re.finditer(r"innerHTML", body):
                line = body[body.rfind("\n", 0, m.start()) + 1:body.find("\n", m.start())]
                self.assertIn("svg.innerHTML", line, f"{js.name}: {line.strip()[:80]}")  # only the fixed SVG symbol definitions

    def test_rankings_page_has_the_pending_mark_the_second_table_and_unbroken_dates(self):
        js = (self.out / "assets/js/common.js").read_text() + (self.out / "assets/js/index.js").read_text()
        self.assertIn('id="m-pending"', js)
        self.assertIn("Pending: waiting for licensed price data", js)
        self.assertIn("Banks and insurers (fewer tests apply)", (self.out / "index.html").read_text())
        self.assertIn('class: "nowrap"', js)
        self.assertRegex((self.out / "assets/site.css").read_text(), r"\.nowrap \{ white-space: nowrap; \}")
        self.assertIn('id="ranking"', (self.out / "how-it-works.html").read_text())  # the long explanation of the score lives there, not on the rankings page

    def test_the_repository_link_comes_from_one_config_value(self):
        cfg = json.loads((REPO_ROOT / "config" / "site.json").read_text())
        self.assertEqual(self.manifest["repo_url"], cfg["repo_url"])
        self.assertEqual(self.manifest["docs"], DOCS)
        for page in PAGES:
            html = (self.out / page).read_text()
            self.assertNotIn("__REPO_URL__", html, page)
            nav = html[html.index('<nav aria-label="Main">'):html.index("</nav>")]
            self.assertIn(f'<a href="{cfg["repo_url"]}" rel="noopener">Code on GitHub</a>', nav, page)
            self.assertIn(f'href="{cfg["repo_url"]}"', html[html.index("<footer"):], page)
        self.assertIn(f'href="{cfg["repo_url"]}"', (self.out / "how-it-works.html").read_text().split("<h2>Project documents</h2>")[1])
        for p in list((SITE_SRC).glob("*.html")) + list((SITE_SRC / "assets/js").glob("*.js")):  # no address is written into a page or a script
            self.assertNotIn("github.com", p.read_text(), p.name)
        doc_js = (self.out / "assets/js/doc.js").read_text()
        self.assertIn("View this file on GitHub", doc_js)
        self.assertIn("m.repo_url", doc_js)

    def test_no_third_party_requests(self):
        for p in list(self.out.glob("*.html")) + list((self.out / "assets").rglob("*.js")) + [self.out / "assets/site.css"]:
            text = p.read_text(encoding="utf-8")
            hosts = set(re.findall(r'(?:src|href)="(https?://[^"/]+)', text)) | set(re.findall(r'url\((https?://[^)/]+)', text))
            hosts = {h for h in hosts if "sec.gov" not in h and "w3.org" not in h and h != "https://github.com"}  # the one link to the repository (config/site.json)
            self.assertEqual(hosts, set(), p.name)
            self.assertNotIn("fetch(\"http", text)


if __name__ == "__main__":
    unittest.main()
