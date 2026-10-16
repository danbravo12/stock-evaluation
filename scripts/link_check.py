"""Link check of the live site (build 5).

    .venv/bin/python scripts/link_check.py https://<user>.github.io/stock-evaluation [site-dir]

Checks that (1) every file of the built site folder is served (every page, script, style, font, drawing and data file), (2) every internal link and every data path
named in a page or a script resolves, (3) every link to the code repository (header, footer, the document links) resolves, and (4) a sample of the SEC links answers.
Exit status 1 if anything fails. Uses only the standard library; requests run in parallel.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.settings import REPO_ROOT  # noqa: E402

HEADERS = {"User-Agent": "stock-evaluation-link-check (research project; contact via the repository)"}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.found.append(v)


def status(url: str) -> int:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in (403, 405):
                return e.code
        except Exception:
            if method == "GET":
                return 0
    return 0


def main() -> int:
    base = sys.argv[1].rstrip("/") + "/"
    site = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "site"
    manifest = json.loads((site / "data/manifest.json").read_text())
    repo = manifest["repo_url"]
    files = sorted(str(p.relative_to(site)) for p in site.rglob("*") if p.is_file())
    urls: dict[str, str] = {urljoin(base, f): "site file" for f in files}
    repo_links: dict[str, str] = {repo: "repository", f"{repo}/blob/{manifest['branch']}/LICENSE": "licence"}
    for name, rel in manifest["docs"].items():
        repo_links[f"{repo}/blob/{manifest['branch']}/{rel}"] = f"document link ({name})"
    sec: set[str] = set()
    for page in sorted(site.glob("*.html")):
        p = Links()
        p.feed(page.read_text(encoding="utf-8"))
        for ref in p.found:
            if ref.startswith(("#", "mailto:", "data:")):
                continue
            full = urljoin(base + page.name, ref)
            host = urlparse(full).netloc
            if full.startswith(base):
                urls.setdefault(full.split("#")[0], f"link on {page.name}")
            elif "github.com" in host:
                repo_links[full] = f"link on {page.name}"
            elif host.endswith("sec.gov"):
                sec.add(full)
    for js in sorted((site / "assets/js").glob("*.js")):
        for ref in set(re.findall(r'["`](data/[A-Za-z0-9_./-]+\.json)["`]', js.read_text(encoding="utf-8"))):
            urls.setdefault(urljoin(base, ref), f"data path in {js.name}")
    # the SEC links the data files carry: a sample, spread over the companies (the SEC asks for a modest request rate)
    sample = []
    for f in sorted((site / "data/results").glob("[0-9]*[0-9].json"))[::5]:
        r = json.loads(f.read_text())
        sample.append(r["data"]["filing"]["url"])
    sec |= set(sample)
    checks = {**urls, **repo_links}
    with ThreadPoolExecutor(16) as ex:
        results = dict(zip(checks, ex.map(status, checks)))
    with ThreadPoolExecutor(2) as ex:
        sec_results = dict(zip(sorted(sec), ex.map(status, sorted(sec))))
    bad = {u: (results[u], checks[u]) for u in results if results[u] != 200}
    bad_sec = {u: c for u, c in sec_results.items() if c not in (200, 403)}  # sec.gov answers 403 to some automated clients; a 404 is a real failure
    print(f"checked {len(urls)} site URLs ({len(files)} files), {len(repo_links)} repository links, {len(sec_results)} SEC links")
    for u, (c, why) in sorted(bad.items()):
        print(f"FAIL {c} {u}  [{why}]")
    for u, c in sorted(bad_sec.items()):
        print(f"FAIL {c} {u}  [SEC link]")
    forbidden = sum(1 for c in sec_results.values() if c == 403)
    if forbidden:
        print(f"note: {forbidden} SEC links answered 403 to this client (automated access is limited by the SEC); they were not counted as failures")
    print("all links resolve" if not bad and not bad_sec else f"{len(bad) + len(bad_sec)} failures")
    return 1 if bad or bad_sec else 0


if __name__ == "__main__":
    sys.exit(main())
