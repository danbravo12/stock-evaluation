"""Content store for raw HTTP responses.

One store class serves two roles (ARCHITECTURE.md §1, "the cache is the only door
to the outside world"):

* the **HTTP cache** (`data/cache/`, git-ignored) used by live runs, and
* the **recorded fixtures** (`fixtures/`, committed) used by tests and development.

Each response is saved as a gzip body plus a small JSON metadata file recording
the source URL, fetch time and a SHA-256 of the body. That metadata is what lets
every figure later cite where and when its raw data came from.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class StoredResponse:
    url: str
    body: bytes
    fetched_at: str  # ISO 8601, UTC
    sha256: str
    content_type: str | None = None


class ResponseStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    # Readable layout: <root>/<logical key>.gz and <root>/<logical key>.meta.json
    # e.g. edgar/0000021344/companyfacts.json.gz
    def _paths(self, key: str) -> tuple[Path, Path]:
        base = self.root / key
        return base.with_name(base.name + ".gz"), base.with_name(base.name + ".meta.json")

    def has(self, key: str) -> bool:
        body_path, meta_path = self._paths(key)
        return body_path.exists() and meta_path.exists()

    def get(self, key: str) -> StoredResponse | None:
        if not self.has(key):
            return None
        body_path, meta_path = self._paths(key)
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        body = gzip.decompress(body_path.read_bytes())
        digest = hashlib.sha256(body).hexdigest()
        if digest != meta["sha256"]:
            raise ValueError(f"Stored body for {key!r} does not match its recorded checksum")
        return StoredResponse(
            url=meta["url"],
            body=body,
            fetched_at=meta["fetched_at"],
            sha256=digest,
            content_type=meta.get("content_type"),
        )

    def put(self, key: str, url: str, body: bytes, content_type: str | None = None) -> StoredResponse:
        body_path, meta_path = self._paths(key)
        body_path.parent.mkdir(parents=True, exist_ok=True)
        stored = StoredResponse(
            url=url,
            body=body,
            fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            sha256=hashlib.sha256(body).hexdigest(),
            content_type=content_type,
        )
        # mtime=0 keeps the gzip bytes identical for identical content (clean git diffs)
        body_path.write_bytes(gzip.compress(body, mtime=0))
        meta_path.write_text(
            json.dumps(
                {
                    "url": stored.url,
                    "fetched_at": stored.fetched_at,
                    "sha256": stored.sha256,
                    "bytes": len(body),
                    "content_type": content_type,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return stored
