"""Which prompt version each agent uses (config/prompt_versions.json). v1 and v2 match recorded fixtures; v2.1 (build 4a) adds the latest-fiscal-year rule,
the per-sentence word counts in the citation cap error and the Critic's year rule, and is switched on by the refresh run (ADR-069 amendment)."""
from __future__ import annotations

import json

from engine.settings import REPO_ROOT

PATH = REPO_ROOT / "config" / "prompt_versions.json"
ORDER = ["v1", "v2", "v2.1"]


def active(agent: str) -> str:
    return json.loads(PATH.read_text(encoding="utf-8"))["active"][agent]


def at_least(agent: str, version: str) -> bool:
    """True if the active version of `agent` is `version` or later."""
    return ORDER.index(active(agent)) >= ORDER.index(version)
