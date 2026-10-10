"""Secret scan over the built site and over the whole git history (ADR-068).

Looks for Google API keys ("AIza…"), Finnhub keys, other well-known token shapes, private keys, any 32+ character string assigned to a name containing key, token, secret or
password, and the exact non-empty values of the local `.env`. History means every blob ever committed (gzip files are unpacked first, because the recorded SEC and model
responses are stored compressed) plus every commit message. A finding is reported redacted (first four characters), never in full.
"""
from __future__ import annotations

import gzip
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from engine.settings import REPO_ROOT

PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "finnhub_key": re.compile(r"(?i)finnhub[\w\-]{0,24}\s*[=:]\s*[\"']?[a-z0-9]{20,}\b"),
    "finnhub_url_token": re.compile(r"(?i)finnhub\.io[^\s\"']*[?&]token=[A-Za-z0-9]{16,}"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{30,}"),
    "long_secret_assignment": re.compile(r"(?i)\b[\w\-]*(?:api[_-]?key|secret|token|passwd|password)[\w\-]*[\"']?\s*[=:]\s*[\"']?[A-Za-z0-9+/_\-]{32,}={0,2}"),
}
ALLOW_PATH = REPO_ROOT / "config" / "secret_scan_allow.json"
TEXT_SUFFIXES = {".html", ".js", ".css", ".json", ".md", ".txt", ".svg", ".csv", ".jsonl", ".py", ".toml", ".cfg", ".yml", ".yaml", ""}
MAX_BLOB = 40_000_000


@dataclass(frozen=True)
class Finding:
    where: str
    kind: str
    sample: str  # redacted

    def __str__(self) -> str:
        return f"{self.where}: {self.kind} ({self.sample})"


def redact(text: str) -> str:
    return text[:4] + "…" + f"[{len(text)} chars]"


def load_allow(path: Path = ALLOW_PATH) -> list[re.Pattern]:
    return [re.compile(p) for p in json.loads(path.read_text(encoding="utf-8")).get("allow", [])] if path.exists() else []


def env_values(env_path: Path | None = None) -> dict[str, str]:
    """Non-empty values of the local .env that are long enough to be a secret or a personal detail."""
    path = env_path or REPO_ROOT / ".env"
    out = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if len(v) >= 8:
                    out[k.strip()] = v
    return out


def scan_text(where: str, text: str, env: dict[str, str], allow: list[re.Pattern]) -> list[Finding]:
    found = []
    for kind, pat in PATTERNS.items():
        for m in pat.finditer(text):
            if any(a.search(m.group(0)) for a in allow):
                continue
            found.append(Finding(where, kind, redact(m.group(0))))
            break  # one finding per kind per file is enough to act on
    for key, value in env.items():
        if value in text:
            found.append(Finding(where, f"value of {key} from .env", redact(value)))
    return found


def scan_tree(root: Path, env: dict[str, str] | None = None, allow: list[re.Pattern] | None = None) -> list[Finding]:
    env = env_values() if env is None else env
    allow = load_allow() if allow is None else allow
    out = []
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
            out += scan_text(str(p.relative_to(root)), p.read_text(encoding="utf-8", errors="ignore"), env, allow)
    return out


def _git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=text, check=True)


def scan_history(repo: Path = REPO_ROOT, env: dict[str, str] | None = None, allow: list[re.Pattern] | None = None) -> tuple[list[Finding], dict]:
    """(findings, stats) over every blob in every commit of every ref, and over the commit messages."""
    env = env_values() if env is None else env
    allow = load_allow() if allow is None else allow
    findings: list[Finding] = []
    listing = _git(repo, "rev-list", "--objects", "--all").stdout.splitlines()
    seen: dict[str, str] = {}
    for line in listing:
        sha, _, path = line.partition(" ")
        if path and sha not in seen:
            seen[sha] = path
    types = dict(l.split(" ", 1)[::-1] for l in _git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objecttype) %(objectname)").stdout.splitlines())
    scanned = skipped = 0
    for sha, path in seen.items():
        if types.get(sha) != "blob" or Path(path).suffix.lower() not in TEXT_SUFFIXES | {".gz"}:
            continue
        data = _git(repo, "cat-file", "blob", sha, text=False).stdout
        if len(data) > MAX_BLOB:
            skipped += 1
            continue
        if path.endswith(".gz"):
            try:
                data = gzip.decompress(data)
            except OSError:
                skipped += 1
                continue
        scanned += 1
        findings += scan_text(f"history blob {sha[:10]} ({path})", data.decode("utf-8", errors="ignore"), env, allow)
    messages = _git(repo, "log", "--all", "--format=%H%n%an <%ae>%n%B%n----").stdout
    for chunk in messages.split("\n----"):
        if chunk.strip():
            head = chunk.strip().splitlines()[0][:10]
            findings += scan_text(f"commit message {head}", chunk, env, allow)
    return findings, {"commits": len(_git(repo, "rev-list", "--all").stdout.split()), "blobs_scanned": scanned, "blobs_skipped": skipped}
