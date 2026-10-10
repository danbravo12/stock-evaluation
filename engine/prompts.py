"""Which prompt version each agent uses (config/prompt_versions.json). v1 matches the recorded fixtures; v2 waits for a re-record."""
from __future__ import annotations

import json

from engine.settings import REPO_ROOT

PATH = REPO_ROOT / "config" / "prompt_versions.json"


def active(agent: str) -> str:
    return json.loads(PATH.read_text(encoding="utf-8"))["active"][agent]
