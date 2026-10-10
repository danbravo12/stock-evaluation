"""Publish command: build the static site into `site/` (ADR-065). No model, no network at build time (the cited passages come from the recorded 10-Ks).

Reads `site_src/` (pages, styles, scripts, fonts), `site_data/rankings.json`, `results/scores/` and `results/<CIK>.json` (+ traces). Every JSON file it writes goes
through the Finnhub gate (ADR-021), all site copy and model-written text through the banned-phrase list (ADR-049), and every SEC link must be an https sec.gov URL.
A failed check removes the half-built folder and raises: nothing is served from a build that did not pass.
"""
from __future__ import annotations

import http.server
import json
import re
import shutil
import socketserver
import subprocess
from functools import partial
from pathlib import Path

from engine.agents.critic import banned_hits, load_banned
from engine.rankings import OUTPUT_PATH, Rankings
from engine.report import PublishGateError, finnhub_fields
from engine.settings import REPO_ROOT, Settings

SITE_SRC = REPO_ROOT / "site_src"
SITE_OUT = REPO_ROOT / "site"
DOCS = {"evaluation_notes": "docs/evaluation_notes.md", "DECISIONS": "DECISIONS.md", "PROCESS": "PROCESS.md", "ARCHITECTURE": "ARCHITECTURE.md",
        "universe_scorecard_report": "docs/universe_scorecard_report.md", "qualitative_report": "docs/qualitative_report.md", "critic_report": "docs/critic_report.md",
        "coverage_report": "docs/coverage_report.md"}
SCORE_KEYS = ("ticker", "cik", "name", "gics_sector", "gics_sub_industry", "sector_class", "sector_notes", "source_notes", "fetched_at", "score")
PAGES = ["index.html", "company.html", "trace.html", "how-it-works.html", "doc.html"]
SEC_URL = re.compile(r"^https://([a-z]+\.)?sec\.gov/")


class BannedPhraseError(RuntimeError):
    pass


class LinkError(RuntimeError):
    pass


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=True).stdout.strip() or None
    except Exception:
        return None


def _dump(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"


def _strings(obj, key=""):
    """(key, value) for every string in a JSON value."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v, key)
    elif isinstance(obj, str):
        yield key, obj


def check_sec_links(name: str, obj) -> None:
    for key, value in _strings(obj):
        if key in ("url", "source_url") and not SEC_URL.match(value):
            raise LinkError(f"{name}: {key} is not an https sec.gov URL: {value}")


# text a model wrote or the project wrote about a company; verbatim filing quotes, passages and the trace's raw model replies are not scanned
MODEL_TEXT_KEYS = {"rationale", "text", "reason", "message", "note", "notes", "sector_notes", "source_notes", "detail"}


def scan_text(name: str, text: str, banned: dict) -> None:
    hits = banned_hits(text, banned)
    if hits:
        raise BannedPhraseError(f"{name}: banned language: {hits[0]}")


def scan_result(name: str, result: dict, banned: dict) -> None:
    for key, value in _strings({"scorecard": result.get("scorecard"), "qualitative": [{"rationale": q["finding"]["rationale"]} for q in result.get("qualitative", [])],
                                "critic": result.get("critic"), "plan": result.get("plan")}):
        if key in MODEL_TEXT_KEYS:
            scan_text(f"{name}:{key}", value, banned)


def page_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    return text


def passages_for(cik: str, result: dict, settings: Settings) -> dict:
    """The cited passages with their text, from the recorded 10-K (replay), so the page can show the sentences around each quote."""
    from engine.fetch.edgar import EdgarClient
    from engine.retrieve import Retriever
    ids = sorted({c["passage_id"] for q in result["qualitative"] for c in q["finding"]["citations"]})
    if not ids:
        return {}
    retriever = Retriever(EdgarClient("replay", settings))
    retriever.index(cik)
    out = {}
    for pid in ids:
        p = retriever.get_passage(pid)
        out[pid] = {"text": p.text, "char_start": p.char_start, "char_end": p.char_end, "item": p.item, "accession": p.accession}
    return out


def build_site(out: Path = SITE_OUT, *, results_dir: Path | None = None, rankings_path: Path = OUTPUT_PATH, settings: Settings | None = None,
               commit: str | None = None, site_src: Path = SITE_SRC, finnhub_public_ok: bool | None = None) -> dict:
    """Build the site; returns the manifest. Deterministic for fixed inputs (no clock, the commit is a parameter)."""
    settings = settings or Settings.from_env()
    results_dir = Path(results_dir) if results_dir else settings.results_dir
    ok = settings.finnhub_public_ok if finnhub_public_ok is None else finnhub_public_ok
    banned = load_banned()
    out = Path(out)
    tmp = out.with_name(out.name + ".building")
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        shutil.copytree(site_src, tmp)
        data = tmp / "data"
        written: list[tuple[str, object]] = []

        def put(rel: str, obj=None, text: str | None = None):
            path = data / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text if text is not None else _dump(obj), encoding="utf-8")
            written.append((rel, obj if obj is not None else json.loads(text)))

        rk_text = Path(rankings_path).read_text(encoding="utf-8")
        rankings = Rankings.model_validate_json(rk_text)
        put("rankings.json", text=rk_text)
        rows = rankings.criteria_ranking.ranked + rankings.criteria_ranking.insufficient_data
        n_scores, full = 0, []
        for r in rows:
            sf = results_dir / "scores" / f"{r.cik}.json"
            if sf.exists():
                d = json.loads(sf.read_text(encoding="utf-8"))
                if d.get("score"):
                    put(f"scores/{r.cik}.json", {k: d.get(k) for k in SCORE_KEYS})
                    n_scores += 1
            if r.has_full_analysis:
                res = json.loads((results_dir / f"{r.cik}.json").read_text(encoding="utf-8"))
                put(f"results/{r.cik}.json", res)
                trace = [json.loads(l) for l in (results_dir / f"{r.cik}.trace.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
                put(f"results/{r.cik}.trace.json", trace)
                put(f"results/{r.cik}.passages.json", passages_for(r.cik, res, settings))
                scan_result(r.symbol, res, banned)
                full.append(r.symbol)
        for name, rel in DOCS.items():
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            (data / "docs").mkdir(parents=True, exist_ok=True)
            (data / "docs" / f"{name}.md").write_text(text, encoding="utf-8")
        for r in rows:
            for n in r.notes + r.caveats:
                scan_text(f"{r.symbol}:note", n, banned)
        manifest = {"build_commit": commit if commit is not None else git_commit(), "data_as_of": rankings.data_as_of.model_dump(), "attribution": rankings.attribution,
                    "counts": {**rankings.counts.model_dump(), "scored": n_scores, "full_analysis": len(full)}, "full_analysis": sorted(full), "caveats": rankings.caveats}
        put("manifest.json", manifest)

        # ---- the gates
        if not ok:
            for rel, obj in written:
                leaked = finnhub_fields(obj)
                if leaked:
                    raise PublishGateError(f"Finnhub-sourced fields in data/{rel} while FINNHUB_PUBLIC_OK is off (ADR-021): {leaked[:3]}")
        for rel, obj in written:
            check_sec_links(rel, obj)
        for p in sorted(tmp.rglob("*")):
            if p.suffix in (".html", ".js"):
                scan_text(str(p.relative_to(tmp)), page_text(p), banned)
        missing = [p for p in PAGES if not (tmp / p).exists()]
        if missing:
            raise LinkError(f"pages missing from site_src: {missing}")
        if out.exists():
            shutil.rmtree(out)
        tmp.rename(out)
        return manifest
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def serve(directory: Path = SITE_OUT, port: int = 8000) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {directory} at http://127.0.0.1:{port}/ (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
