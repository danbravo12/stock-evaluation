"""Registrant successors and companies without an annual report (ADR-063).

A snapshot CIK can belong to a registrant that has not filed a 10-K yet. Two different cases:

* a **successor** after a reorganisation (ExxonMobil Holdings Corp, 8-K12B of 2026-07-01): the figures are read from the predecessor registrant
  until the successor files its own 10-K. Only `config/registrant_successors.json` entries, each with the succession filing as evidence;
* a **new registrant** (spin-offs such as Honeywell Aerospace and Vylor, Form 10-12B): there is no annual report yet, so the company is not scored.
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.settings import REPO_ROOT

SUCCESSORS_PATH = REPO_ROOT / "config" / "registrant_successors.json"
ANNUAL_REPORT_FORMS = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A", "10-K405"})
NO_ANNUAL_REPORT = "No annual report (10-K) filed yet"  # prefix of the message; ledger status "no_annual_report"


class NoAnnualReport(RuntimeError):
    """The company has not filed a 10-K (and no predecessor registrant did)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def no_annual_report_message(date_added: str | None) -> str:
    return f"{NO_ANNUAL_REPORT}; listed since {date_added}." if date_added else f"{NO_ANNUAL_REPORT}."


def load_successors(path: Path = SUCCESSORS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["successors"] if path.exists() else {}


def has_annual_report(submissions: dict) -> bool:
    """Whether the registrant's recent filings include a 10-K (a new registrant's history is short, so the recent list is enough)."""
    return any(f in ANNUAL_REPORT_FORMS for f in submissions.get("filings", {}).get("recent", {}).get("form", []))
