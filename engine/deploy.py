"""Deploy to GitHub Pages (ADR-068): build the site, run every gate, scan for secrets, then publish `site/` to the `gh-pages` branch through a git worktree.

`dry_run` builds, checks and prints what would be pushed, and touches nothing else. A real deploy refuses when any gate fails, when the secret scan finds anything, or when
the repository has no remote; it never forces a push.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from engine.publish import SITE_OUT, build_site, check_site
from engine.secrets_scan import Finding, scan_history, scan_tree
from engine.settings import REPO_ROOT, Settings

BRANCH = "gh-pages"


class DeployRefused(RuntimeError):
    pass


@dataclass
class DeployReport:
    manifest: dict
    files: int
    megabytes: float
    findings: list[Finding] = field(default_factory=list)
    history: dict = field(default_factory=dict)
    remote: str | None = None
    pushed: bool = False


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


def remote_url(repo: Path, name: str = "origin") -> str | None:
    r = _run(repo, "remote", "get-url", name, check=False)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def gates(repo: Path = REPO_ROOT, out: Path = SITE_OUT, settings: Settings | None = None, *, build=build_site, **build_kwargs) -> DeployReport:
    """Build (Finnhub gate, banned phrases, SEC links inside `build_site`), validate the output, scan the site and the history. Raises on a failed gate."""
    manifest = build(out, settings=settings, **build_kwargs)
    check_site(out)
    findings = scan_tree(out)
    hist, stats = scan_history(repo)
    files = [p for p in Path(out).rglob("*") if p.is_file()]
    return DeployReport(manifest=manifest, files=len(files), megabytes=round(sum(p.stat().st_size for p in files) / 1e6, 1), findings=findings + hist, history=stats, remote=remote_url(repo))


def summary(rep: DeployReport, out: Path) -> str:
    lines = [f"Built {out.name}/: {rep.files} files, {rep.megabytes} MB, from commit {rep.manifest['build_commit']}; {rep.manifest['counts']['scored']} company score files, {rep.manifest['counts']['full_analysis']} full analyses.",
             f"Secret scan: {rep.history.get('commits', 0)} commits, {rep.history.get('blobs_scanned', 0)} stored files scanned ({rep.history.get('blobs_skipped', 0)} skipped), site folder scanned: "
             + ("NOTHING FOUND." if not rep.findings else f"{len(rep.findings)} FINDING(S).")]
    lines += [f"  {f}" for f in rep.findings]
    lines.append(f"Would push the contents of {out.name}/ (plus .nojekyll) to branch {BRANCH} of " + (rep.remote or "a remote that is not configured yet (add one with: git remote add origin <url>)") + ".")
    return "\n".join(lines)


def deploy(repo: Path = REPO_ROOT, out: Path = SITE_OUT, settings: Settings | None = None, *, dry_run: bool = False, remote: str = "origin", **kw) -> DeployReport:
    rep = gates(repo, out, settings, **kw)
    if rep.findings:
        raise DeployRefused("the secret scan found something; nothing was pushed:\n" + "\n".join(f"  {f}" for f in rep.findings))
    if dry_run:
        return rep
    url = remote_url(repo, remote)
    if not url:
        raise DeployRefused(f"this repository has no remote called {remote!r}. Create the GitHub repository, run `git remote add {remote} <url>`, push main, then deploy again.")
    rep.remote = url
    source = _run(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    work = Path(tempfile.mkdtemp(prefix="gh-pages-"))
    shutil.rmtree(work)  # `git worktree add` wants to create it
    try:
        exists = _run(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}", check=False).returncode == 0
        if exists:
            _run(repo, "worktree", "add", str(work), BRANCH)
        else:
            _run(repo, "worktree", "add", "--detach", str(work))
            _run(work, "checkout", "--orphan", BRANCH)
        _run(work, "rm", "-rf", "--quiet", "--ignore-unmatch", ".")
        for p in work.iterdir():
            if p.name != ".git":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        shutil.copytree(out, work, dirs_exist_ok=True)
        (work / ".nojekyll").write_text("", encoding="utf-8")
        _run(work, "add", "-A", "-f")
        _run(work, "-c", "user.name=" + (_run(repo, "config", "user.name", check=False).stdout.strip() or "deploy"), "-c", "user.email=" + (_run(repo, "config", "user.email", check=False).stdout.strip() or "deploy@localhost"),
             "commit", "--quiet", "--allow-empty", "-m", f"Publish site built from {source}")
        _run(work, "push", remote, BRANCH)
        rep.pushed = True
    finally:
        _run(repo, "worktree", "remove", "--force", str(work), check=False)
        _run(repo, "worktree", "prune", check=False)
    return rep
