"""Runtime settings.

Secrets and personal details come from environment variables or a local `.env`
file (git-ignored). Nothing secret is ever written in code. See `.env.example`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (KEY=VALUE lines). Existing environment variables win."""
    path = path or REPO_ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    sec_user_agent: str | None
    fixtures_dir: Path
    cache_dir: Path
    # SEC fair-access policy: at most 10 requests/second. We stay well under.
    sec_min_interval_s: float = 0.15
    # LLM settings (the API key itself is read from the environment at call time, never stored here)
    llm_profile: str = "gemini-3.1-flash-lite"
    paid_mode_enabled: bool = False
    ledger_path: Path = REPO_ROOT / "data" / "ledger" / "usage.json"
    results_dir: Path = REPO_ROOT / "results"
    finnhub_public_ok: bool = False  # ADR-021: Finnhub-sourced fields may appear in published results only when true

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            sec_user_agent=os.environ.get("SEC_USER_AGENT") or None,
            fixtures_dir=Path(os.environ.get("FIXTURES_DIR", REPO_ROOT / "fixtures")),
            cache_dir=Path(os.environ.get("CACHE_DIR", REPO_ROOT / "data" / "cache")),
            llm_profile=os.environ.get("LLM_PROFILE") or "gemini-3.1-flash-lite",
            paid_mode_enabled=os.environ.get("PAID_MODE_ENABLED", "").strip().lower() == "true",
            ledger_path=Path(os.environ.get("LEDGER_PATH", REPO_ROOT / "data" / "ledger" / "usage.json")),
            results_dir=Path(os.environ.get("RESULTS_DIR", REPO_ROOT / "results")),
            finnhub_public_ok=os.environ.get("FINNHUB_PUBLIC_OK", "").strip().lower() == "true",
        )
