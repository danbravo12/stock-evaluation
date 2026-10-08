"""Run ledger and budget guard (ADR-023, ADR-039).

The ledger is a small JSON file shared by separate runs: requests per profile per Pacific day,
total and per-company spend. The guard runs before every live request: it paces to the free
tier's requests per minute, refuses when the day's quota (minus a safety margin) is used up, and
only allows paid calls when PAID_MODE_ENABLED=true and the projected cost fits the caps.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")  # Google resets daily quotas at midnight Pacific


class LLMError(RuntimeError):
    pass


class QuotaReached(LLMError):
    """The free daily quota is used up. The batch stops cleanly and resumes the next Pacific day."""


class BudgetExceeded(LLMError):
    """A paid call would break a spending cap, or paid mode is off."""


def pacific_day(now: datetime) -> date:
    return now.astimezone(PACIFIC).date()


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {"requests": {}, "last_request_ts": {}, "spend_usd": 0.0, "notional_usd": 0.0, "companies": {}}
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text(encoding="utf-8")))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def requests_today(self, profile: str, day: date) -> int:
        return self.data["requests"].get(profile, {}).get(day.isoformat(), 0)

    def add_request(self, profile: str, day: date, ts: float) -> None:
        by_day = self.data["requests"].setdefault(profile, {})
        by_day[day.isoformat()] = by_day.get(day.isoformat(), 0) + 1
        self.data["last_request_ts"][profile] = ts
        self._save()

    def mark_exhausted(self, profile: str, day: date, limit: int) -> None:
        by_day = self.data["requests"].setdefault(profile, {})
        by_day[day.isoformat()] = max(by_day.get(day.isoformat(), 0), limit)
        self._save()

    def add_cost(self, actual: float, notional: float, company: str | None) -> None:
        self.data["spend_usd"] += actual
        self.data["notional_usd"] += notional
        if company and actual:
            self.data["companies"][company] = self.data["companies"].get(company, 0.0) + actual
        self._save()

    @property
    def spend(self) -> float:
        return self.data["spend_usd"]

    def company_spend(self, company: str) -> float:
        return self.data["companies"].get(company, 0.0)


class Budget:
    def __init__(self, profile_name: str, profile: dict, config: dict, ledger: Ledger, paid_enabled: bool = False,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), sleep: Callable[[float], None] = time.sleep):
        self.name, self.profile, self.ledger = profile_name, profile, ledger
        self.free = profile.get("free_tier")  # None: unmetered (local model)
        self.margin = config["daily_safety_margin"]
        self.total_cap, self.company_cap = config["total_usd_cap"], config["per_company_usd_cap"]
        self.paid_enabled, self._now, self._sleep = paid_enabled, now, sleep

    def free_quota_left(self) -> int | None:
        if not self.free:
            return None
        return self.free["rpd"] - self.margin - self.ledger.requests_today(self.name, pacific_day(self._now()))

    def pace(self) -> None:
        """Sleep so requests stay under the free tier's requests per minute (also across runs)."""
        if not self.free:
            return
        last = self.ledger.data["last_request_ts"].get(self.name)
        if last is not None:
            wait = 60.0 / self.free["rpm"] - (self._now().timestamp() - last)
            if wait > 0:
                self._sleep(wait)

    def authorise(self, projected_usd: float | None, company: str | None) -> bool:
        """Check before every request. Returns True if the request will be billed (beyond the free quota).
        Raises QuotaReached or BudgetExceeded when it must not be sent."""
        left = self.free_quota_left()
        if left is None or left > 0:
            return False
        if not self.paid_enabled:
            used = self.ledger.requests_today(self.name, pacific_day(self._now()))
            raise QuotaReached(f"quota reached: {used} of {self.free['rpd']} requests used today "
                               f"(safety margin {self.margin}); resume after midnight Pacific")
        if projected_usd is None:
            raise BudgetExceeded(f"profile {self.name!r} has no paid price configured, so a paid call cannot be projected")
        if self.ledger.spend + projected_usd > self.total_cap:
            raise BudgetExceeded(f"projected ${projected_usd:.4f} would take total spend past the ${self.total_cap:.2f} cap "
                                 f"(spent ${self.ledger.spend:.4f})")
        if company and self.ledger.company_spend(company) + projected_usd > self.company_cap:
            raise BudgetExceeded(f"projected ${projected_usd:.4f} would take {company} past its ${self.company_cap:.2f} cap")
        return True

    def record_request(self) -> None:
        now = self._now()
        self.ledger.add_request(self.name, pacific_day(now), now.timestamp())

    def record_cost(self, actual: float, notional: float, company: str | None) -> None:
        self.ledger.add_cost(actual, notional, company)

    def exhaust_today(self) -> None:
        """A 429 said the daily quota is gone: remember it so other runs stop too."""
        if self.free:
            self.ledger.mark_exhausted(self.name, pacific_day(self._now()), self.free["rpd"])
