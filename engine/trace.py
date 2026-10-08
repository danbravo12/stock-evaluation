"""Trace recorder (ADR-020): one JSON line per step, the data behind the website's trace replay.

LLM calls are recorded automatically by the LLM client; agents add tool calls and notes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from engine.contracts import LLMCall, TraceEvent

SUMMARY_CHARS = 300


def summarise(text: Any, limit: int = SUMMARY_CHARS) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


class TraceRecorder:
    def __init__(self, run_id: str, path: Path | None = None, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.run_id, self.path, self._now = run_id, Path(path) if path else None, now
        self.events: list[TraceEvent] = []
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def _add(self, event: TraceEvent) -> TraceEvent:
        self.events.append(event)
        if self.path:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
        return event

    def _event(self, agent: str, type_: str, **fields) -> TraceEvent:
        return self._add(TraceEvent(run_id=self.run_id, step=len(self.events) + 1, agent=agent, type=type_,
                                    ts=self._now().replace(microsecond=0).isoformat(), **fields))

    def llm_call(self, agent: str, messages: list[dict], call: LLMCall) -> TraceEvent:
        last = next((m for m in reversed(messages) if m.get("role") in ("user", "tool")), messages[-1] if messages else {})
        output = summarise(call.content) if call.content else [{"tool": t.name, "arguments": t.arguments} for t in call.tool_calls]
        return self._event(agent, "llm_call", input_summary=f"{len(messages)} messages; last {last.get('role')}: {summarise(last.get('content'), 200)}",
                           output=output, usage=call.usage, latency_s=call.latency_s, actual_cost_usd=call.actual_cost_usd,
                           notional_cost_usd=call.notional_cost_usd, replayed=call.replayed)

    def tool_call(self, agent: str, name: str, arguments: dict, result: Any) -> TraceEvent:
        return self._event(agent, "tool_call", input_summary=f"{name}({summarise(json.dumps(arguments, sort_keys=True), 200)})", output=summarise(result, 500))

    def note(self, agent: str, text: str) -> TraceEvent:
        return self._event(agent, "note", output=text)
