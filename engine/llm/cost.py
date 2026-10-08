"""Cost maths (ADR-039): what a call costs on the paid tier, and what we expect before sending it."""
from __future__ import annotations

from engine.contracts import Usage


def notional_cost(usage: Usage, profile: dict) -> float:
    """Tokens x the profile's paid price. 0.0 when the profile has no paid price."""
    price_in, price_out = profile.get("price_in_per_m"), profile.get("price_out_per_m")
    if price_in is None or price_out is None:
        return 0.0
    return (usage.prompt_tokens * price_in + usage.completion_tokens * price_out) / 1_000_000


def actual_cost(usage: Usage, profile: dict, paid: bool) -> float:
    """Money actually spent: only calls billed beyond the free quota cost anything."""
    return notional_cost(usage, profile) if paid else 0.0


def projected_cost(messages: list[dict], max_tokens: int, profile: dict) -> float | None:
    """Upper-ish estimate before sending: prompt characters / 4 for input, max_tokens for output.
    None when the profile has no paid price (so a paid call cannot be projected)."""
    price_in, price_out = profile.get("price_in_per_m"), profile.get("price_out_per_m")
    if price_in is None or price_out is None:
        return None
    chars = sum(len(str(m.get("content") or "")) for m in messages)
    return (chars / 4 * price_in + max_tokens * price_out) / 1_000_000
