"""Deploy dry run, the gates, the secret scan over files and git history, and the gh-pages push to a local bare remote (ADR-068). Offline."""
from __future__ import annotations

import gzip
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from engine.deploy import BRANCH, DeployRefused, deploy, gates, remote_url, summary
from engine.publish import LinkError, SITE_SRC, build_site, check_site
from engine.report import PublishGateError
from engine.secrets_scan import redact, scan_history, scan_text, scan_tree
from engine.settings import Settings
from tests.test_site import sample_results

GOOGLE = "AIza" + "SyD3x9Qk2LmN8vR4tUwY6zB1cE5fG7hJ0kA"[:35]
FINN = "cnk3gq9r01qk4f8h2d70cnk3gq9r01qk4f8h2d7g"[:20]


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@example.com")
    (path / "README.md").write_text("hello\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "first")
    return path


class TestScanner(unittest.TestCase):
    def test_patterns_catch_the_shapes_and_redact(self):
        env = {}
        for text, kind in [(f"key = '{GOOGLE}'", "google_api_key"), (f"FINNHUB_API_KEY={FINN}", "finnhub_key"), ("-----BEGIN " + "RSA PRIVATE KEY-----", "private_key"),
                           ('"api_key": "' + "a1B2c3D4" * 5 + '"', "long_secret_assignment"), ("token = " + "x9" * 20, "long_secret_assignment"),
                           ("Authorization: Bearer " + "abc.DEF-123_" * 4, "bearer_token"), ("ghp_" + "A1b2" * 10, "github_token")]:
            hits = scan_text("f", text, {}, [])
            self.assertIn(kind, [h.kind for h in hits], text)
            self.assertNotIn(text.split()[-1].strip("'\""), " ".join(str(h) for h in hits))  # redacted, never the full value
        self.assertEqual(redact("AIzaSecretSecretSecret"), "AIza…[22 chars]")

    def test_ordinary_hashes_and_names_are_not_findings(self):
        text = '{"sha256": "' + "ab12" * 16 + '", "request_hash": "' + "cd34" * 8 + '", "accession": "0000021344-26-010047", "url": "https://www.sec.gov/Archives/edgar/data/21344/"}\nSEC_USER_AGENT=\nFINNHUB_API_KEY=\n'
        self.assertEqual(scan_text("f", text, {}, []), [])

    def test_the_exact_values_of_the_local_env_are_searched_for(self):
        hits = scan_text("f", "some text with My-Private-Value-123 inside", {"SEC_USER_AGENT": "My-Private-Value-123"}, [])
        self.assertEqual([h.kind for h in hits], ["value of SEC_USER_AGENT from .env"])

    def test_the_allow_list_silences_a_documented_false_positive(self):
        import re
        self.assertEqual(scan_text("f", f"key = '{GOOGLE}'", {}, [re.compile("AIza")]), [])

    def test_tree_scan_finds_a_planted_key_in_the_site(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data").mkdir()
            (Path(d) / "data" / "x.json").write_text(json.dumps({"note": f"key {GOOGLE}"}))
            (Path(d) / "ok.html").write_text("<p>fine</p>")
            hits = scan_tree(Path(d), env={}, allow=[])
        self.assertEqual([(h.where, h.kind) for h in hits], [("data/x.json", "google_api_key")])


class TestHistoryScan(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = make_repo(Path(self._tmp.name) / "repo")

    def test_a_clean_repository_has_no_findings(self):
        findings, stats = scan_history(self.repo, env={}, allow=[])
        self.assertEqual((findings, stats["commits"], stats["blobs_scanned"]), ([], 1, 1))

    def test_a_secret_committed_and_deleted_is_still_found_in_history(self):
        (self.repo / "config.py").write_text(f"API = '{GOOGLE}'\n")
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", "oops")
        (self.repo / "config.py").unlink()
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", "remove it")
        findings, _ = scan_history(self.repo, env={}, allow=[])
        self.assertEqual([f.kind for f in findings], ["google_api_key"])
        self.assertIn("config.py", findings[0].where)
        self.assertNotIn(GOOGLE, str(findings[0]))

    def test_a_secret_inside_a_gzip_fixture_is_found(self):
        (self.repo / "fixtures").mkdir()
        (self.repo / "fixtures" / "response.json.gz").write_bytes(gzip.compress(json.dumps({"headers": {"x": f"AIza{'q' * 35}"}}).encode()))
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", "fixture")
        findings, _ = scan_history(self.repo, env={}, allow=[])
        self.assertEqual([f.kind for f in findings], ["google_api_key"])

    def test_a_secret_in_a_commit_message_or_an_env_value_is_found(self):
        (self.repo / "notes.md").write_text("The shared login is Hunter2-Hunter2 for now\n")
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", f"temporary key {GOOGLE}")
        findings, _ = scan_history(self.repo, env={"X_SECRET": "Hunter2-Hunter2"}, allow=[])
        kinds = sorted(f.kind for f in findings)
        self.assertEqual(kinds, ["google_api_key", "value of X_SECRET from .env"])

    def test_this_repository_s_history_and_env_are_clean(self):
        from engine.settings import REPO_ROOT
        findings, stats = scan_history(REPO_ROOT)
        self.assertEqual(findings, [], "\n".join(map(str, findings)))
        self.assertGreater(stats["blobs_scanned"], 100)


class DeployCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.repo = make_repo(self.tmp / "repo")
        self.results = sample_results(self.tmp / "results")
        self.out = self.tmp / "site"
        self.settings = Settings.from_env()

    def run_deploy(self, **kw):
        return deploy(self.repo, self.out, self.settings, results_dir=kw.pop("results_dir", self.results), commit="t", **kw)


class TestDryRun(DeployCase):
    def test_dry_run_builds_checks_and_changes_nothing(self):
        rep = self.run_deploy(dry_run=True)
        self.assertEqual((rep.findings, rep.remote, rep.pushed), ([], None, False))
        self.assertTrue((self.out / ".nojekyll").exists() and (self.out / "index.html").exists())
        self.assertEqual(git(self.repo, "branch", "--list", BRANCH), "")
        text = summary(rep, self.out)
        self.assertIn("NOTHING FOUND", text)
        self.assertIn("remote that is not configured yet", text)
        self.assertEqual(rep.manifest["counts"]["full_analysis"], 5)

    def test_a_secret_in_the_history_refuses_even_a_dry_run(self):
        (self.repo / "old.txt").write_text(f"{GOOGLE}\n")
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", "mistake")
        git(self.repo, "rm", "-q", "old.txt"); git(self.repo, "commit", "-q", "-m", "removed")
        with self.assertRaises(DeployRefused) as ctx:
            self.run_deploy(dry_run=True)
        self.assertIn("google_api_key", str(ctx.exception))
        self.assertNotIn(GOOGLE, str(ctx.exception))

    def test_a_secret_planted_in_the_published_data_is_caught(self):
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["plan"]["notes"].append(f"debug {GOOGLE}")
        f.write_text(json.dumps(d))
        with self.assertRaises(DeployRefused):
            self.run_deploy(dry_run=True)

    def test_a_failed_publish_gate_refuses(self):
        f = self.results / "0000021344.json"
        d = json.loads(f.read_text())
        d["data"]["analyst_buy"] = 3
        f.write_text(json.dumps(d))
        with self.assertRaises(PublishGateError):
            self.run_deploy(dry_run=True)

    def test_a_broken_link_in_the_built_site_fails_the_check(self):
        src = self.tmp / "src"
        shutil.copytree(SITE_SRC, src)
        p = src / "index.html"
        p.write_text(p.read_text().replace('href="how-it-works.html"', 'href="gone.html"', 1))
        with self.assertRaises(LinkError):
            build_site(self.out, results_dir=self.results, settings=self.settings, commit="t", site_src=src)


class TestPush(DeployCase):
    def test_without_a_remote_a_real_deploy_refuses(self):
        with self.assertRaises(DeployRefused) as ctx:
            self.run_deploy()
        self.assertIn("no remote", str(ctx.exception))
        self.assertEqual(git(self.repo, "branch", "--list", BRANCH), "")

    def test_deploy_pushes_the_site_to_gh_pages_and_never_touches_main(self):
        bare = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        git(self.repo, "remote", "add", "origin", str(bare))
        git(self.repo, "push", "-q", "origin", "main")
        main_before = git(bare, "rev-parse", "main").strip()
        rep = self.run_deploy()
        self.assertTrue(rep.pushed)
        self.assertEqual(remote_url(self.repo), str(bare))
        self.assertEqual(git(bare, "rev-parse", "main").strip(), main_before)
        files = git(bare, "ls-tree", "-r", "--name-only", BRANCH).splitlines()
        self.assertIn("index.html", files)
        self.assertIn(".nojekyll", files)
        self.assertIn("data/rankings.json", files)
        self.assertNotIn("README.md", files)  # the branch holds the site only
        self.assertIn("Publish site built from", git(bare, "log", "-1", "--format=%s", BRANCH))
        # a second deploy adds a commit on top (no force)
        first = git(bare, "rev-parse", BRANCH).strip()
        self.run_deploy()
        self.assertEqual(git(bare, "rev-list", "--count", BRANCH).strip(), "2")
        self.assertEqual(git(bare, "rev-parse", f"{BRANCH}~1").strip(), first)
        self.assertEqual(git(self.repo, "worktree", "list").count("\n"), 1)  # the temporary worktree is gone

    def test_a_secret_stops_the_push(self):
        bare = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        git(self.repo, "remote", "add", "origin", str(bare))
        (self.repo / "leak.txt").write_text(f"token = {'z9' * 20}\n")
        git(self.repo, "add", "-A"); git(self.repo, "commit", "-q", "-m", "leak")
        with self.assertRaises(DeployRefused):
            self.run_deploy()
        self.assertEqual(git(bare, "branch", "--list").strip(), "")


if __name__ == "__main__":
    unittest.main()
