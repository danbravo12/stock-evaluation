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
from engine.trace_render import critic_notes, render_trace
from engine.report import PublishGateError, finnhub_fields
from engine.settings import REPO_ROOT, Settings

SITE_SRC = REPO_ROOT / "site_src"
SITE_OUT = REPO_ROOT / "site"
DOCS = {"evaluation_notes": "docs/evaluation_notes.md", "DECISIONS": "DECISIONS.md", "PROCESS": "PROCESS.md", "ARCHITECTURE": "ARCHITECTURE.md",
        "universe_scorecard_report": "docs/universe_scorecard_report.md", "qualitative_report": "docs/qualitative_report.md", "critic_report": "docs/critic_report.md",
        "coverage_report": "docs/coverage_report.md"}
SITE_CONFIG = REPO_ROOT / "config" / "site.json"
SHOWCASE_CONFIG = REPO_ROOT / "config" / "showcase.json"
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


def _no_network(url, headers, timeout):
    raise RuntimeError("the network is not used while publishing")


def _indexed_retriever(cik: str, settings: Settings):
    """A retriever whose index for `cik` loads: the recorded fixtures first (the five test companies), then the local cache of 10-K documents fetched in live mode (the showcase
    companies), never the network. None when the filing is in neither: the page then shows the quote without its surrounding text and the trace lists passage ids only."""
    from engine.fetch.edgar import EdgarClient
    from engine.retrieve import Retriever
    for client in (EdgarClient("replay", settings), EdgarClient("live", settings, transport=_no_network)):
        retriever = Retriever(client)
        try:
            retriever.index(cik)
            return retriever
        except Exception:
            continue
    return None


class MissingPassageError(RuntimeError):
    pass


def passages_for(cik: str, result: dict) -> dict:
    """The cited passages with their text, read from the result itself (schema 1.2), so the page can show the sentences around each quote.

    A result is self-contained: publishing never reads the 10-K. A cited passage whose text is missing from the result fails the build."""
    ids = sorted({c["passage_id"] for q in result["qualitative"] for c in q["finding"]["citations"]})
    stored = result.get("passages") or {}
    missing = [i for i in ids if i not in stored or not stored[i].get("text")]
    if missing:
        raise MissingPassageError(f"{cik}: the result cites passages whose text it does not carry: {missing[:3]}"
                                  + (" ..." if len(missing) > 3 else "") + " (re-run the analysis or `scripts/backfill_passages.py`)")
    return {pid: {k: stored[pid][k] for k in ("text", "char_start", "char_end", "item", "accession")} for pid in ids}


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
        site_cfg = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
        for page in tmp.glob("*.html"):  # the repository address is set in config/site.json only
            page.write_text(page.read_text(encoding="utf-8").replace("__REPO_URL__", site_cfg["repo_url"]), encoding="utf-8")
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
        rows = rankings.criteria_ranking.ranked + rankings.criteria_ranking.ranked_financials + rankings.criteria_ranking.insufficient_data
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
                retriever = _indexed_retriever(r.cik, settings)
                put(f"results/{r.cik}.trace.json", render_trace(trace, res, retriever=retriever, cik=r.cik))
                notes = critic_notes(res)
                notes["name"] = r.name
                put(f"results/{r.cik}.explain.json", notes)
                for key, text in _strings(notes):
                    scan_text(f"{r.symbol}:explain", text, banned)
                put(f"results/{r.cik}.passages.json", passages_for(r.cik, res))
                scan_result(r.symbol, res, banned)
                full.append(r.symbol)
        for name, rel in DOCS.items():
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            (data / "docs").mkdir(parents=True, exist_ok=True)
            (data / "docs" / f"{name}.md").write_text(text, encoding="utf-8")
        for r in rows:
            for n in r.notes + r.caveats:
                scan_text(f"{r.symbol}:note", n, banned)
        showcase = showcase_data(rankings)
        put("showcase.json", showcase)
        manifest = {"build_commit": commit if commit is not None else git_commit(), "data_as_of": rankings.data_as_of.model_dump(), "attribution": rankings.attribution,
                    "counts": {**rankings.counts.model_dump(), "scored": n_scores, "full_analysis": len(full)}, "full_analysis": sorted(full), "caveats": rankings.caveats,
                    "repo_url": site_cfg["repo_url"], "branch": site_cfg["branch"], "docs": DOCS, "showcase_missing": showcase["missing"]}
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
        (tmp / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages must not process the folder with Jekyll
        check_site(tmp)
        if out.exists():
            shutil.rmtree(out)
        tmp.rename(out)
        return manifest
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def showcase_data(rankings: Rankings, config_path: Path = SHOWCASE_CONFIG) -> dict:
    """The showcase list for the rankings page: config/showcase.json resolved against the rankings (name, rank, group), in the configured order. A company without a full
    analysis is left out and named in `missing`."""
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    cr = rankings.criteria_ranking
    rows = {r.symbol: r for r in cr.ranked + cr.ranked_financials + cr.insufficient_data}
    groups: dict[str, list] = {title: [] for title in cfg["groups"]}
    missing: list[str] = []
    entries = [(e["symbol"], e["group"], e["why"]) for e in cfg["showcase"]] + [(e["symbol"], "The five test companies", e["why"]) for e in cfg["test_companies"]]
    for symbol, group, why in entries:
        r = rows.get(symbol)
        if r is None or not r.has_full_analysis:
            missing.append(symbol)
            continue
        title, _, tag = group.partition(": ")
        title = "Edge cases the rules handle" if title == "Edge case" else title
        groups[title].append({"symbol": symbol, "name": r.name, "cik": r.cik, "tag": tag or None, "why": why, "rank": r.rank, "rank_group": r.group})
    return {"groups": [{"title": t, "items": items} for t, items in groups.items() if items], "missing": missing}


def check_site(out: Path) -> None:
    """Checks on a finished site folder: every JSON file is valid, the rankings and the results satisfy their schemas, and every internal link and data path resolves."""
    import jsonschema
    from engine.rankings import SCHEMA_PATH as RANKINGS_SCHEMA
    from engine.report import SCHEMA_PATH as RESULT_SCHEMA
    out = Path(out)
    for p in out.rglob("*.json"):
        json.loads(p.read_text(encoding="utf-8"))
    jsonschema.validate(json.loads((out / "data/rankings.json").read_text(encoding="utf-8")), json.loads(RANKINGS_SCHEMA.read_text(encoding="utf-8")))
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    for p in sorted((out / "data/results").glob("*.json")):
        if p.name.count(".") == 1:
            jsonschema.validate(json.loads(p.read_text(encoding="utf-8")), schema)
    for page in sorted(out.glob("*.html")):
        for ref in re.findall(r'(?:href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
            if not ref.startswith(("http", "#", "mailto:", "data:")) and not (out / ref.split("#")[0].split("?")[0]).exists():
                raise LinkError(f"{page.name}: {ref} does not exist in the built site")
    for js in sorted((out / "assets/js").glob("*.js")):
        text = js.read_text(encoding="utf-8")
        for ref in set(re.findall(r'["`](data/[A-Za-z0-9_./-]+\.json)["`]', text)) | set(re.findall(r'["`]((?:index|company|trace|how-it-works|doc)\.html)', text)):
            if not (out / ref).exists():
                raise LinkError(f"{js.name}: {ref} does not exist in the built site")


def serve(directory: Path = SITE_OUT, port: int = 8000) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {directory} at http://127.0.0.1:{port}/ (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
