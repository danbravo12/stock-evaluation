"""Smoke test for the LLM client: model id check, JSON mode, tool calling.

    .venv/bin/python scripts/llm_smoke.py record    # live: uses ~4 free-tier requests, writes fixtures/llm/
    .venv/bin/python scripts/llm_smoke.py replay    # offline: same calls from the fixtures, zero network

Stops and reports (does not work around) if the endpoint cannot do JSON mode or tool calling.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel  # noqa: E402

from engine.llm.budget import Ledger  # noqa: E402
from engine.llm.client import LLMClient, LLMError, urllib_transport  # noqa: E402
from engine.settings import REPO_ROOT, Settings  # noqa: E402
from engine.trace import TraceRecorder  # noqa: E402


class Answer(BaseModel):
    ok: bool
    word: str


GET_YEAR = {"type": "function", "function": {"name": "get_year", "description": "Returns the current year.",
                                             "parameters": {"type": "object", "properties": {}}}}


def show(label: str, call) -> None:
    u = call.usage
    print(f"  {label}: model={call.model} tokens in/out/total={u.prompt_tokens}/{u.completion_tokens}/{u.total_tokens} "
          f"(thinking {u.reasoning_tokens}) latency={call.latency_s:.2f}s actual=${call.actual_cost_usd:.4f} "
          f"notional=${call.notional_cost_usd:.6f} replayed={call.replayed}")


def main(mode: str) -> int:
    settings = Settings.from_env()
    network = []

    def counting_transport(url, headers, body, timeout):
        if mode == "replay":
            raise AssertionError("network call in replay mode")
        network.append(url)
        return urllib_transport(url, headers, body, timeout)

    trace_path = REPO_ROOT / "data" / "cache" / "trace" / f"llm_smoke_{mode}.jsonl"
    trace_path.unlink(missing_ok=True)
    client = LLMClient(mode, settings, transport=counting_transport, trace=TraceRecorder(f"smoke-{mode}", trace_path))
    print(f"profile {client.profile_name}, configured model {client.profile['model']}, mode {mode}")

    if mode != "replay":
        ids = client.list_models()
        found = [i for i in ids if i.removeprefix("models/") == client.profile["model"]]
        print(f"  (a) models endpoint: {len(ids)} models; configured id {'FOUND as ' + found[0] if found else 'NOT FOUND'}")
        if not found:
            return 1

    try:  # (b) JSON mode
        answer = client.complete_json([{"role": "user", "content": 'Return {"ok": true, "word": "graham"}'}], Answer, agent="smoke")
    except LLMError as e:
        print(f"  (b) STOP: JSON mode failed: {e}")
        return 1
    show("(b) json", client.calls[-1])
    print(f"      parsed: {answer}")

    # (c) tool calling, including the round trip with the tool result
    messages = [{"role": "user", "content": "What year is it? Use the get_year tool."}]
    try:
        first = client.chat(messages, tools=[GET_YEAR], agent="smoke")
    except LLMError as e:
        print(f"  (c) STOP: tool calling failed: {e}")
        return 1
    show("(c) tool request", first)
    if not first.tool_calls:
        print(f"  (c) STOP: no tool_calls came back (content: {first.content!r})")
        return 1
    tc = first.tool_calls[0]
    print(f"      tool call: {tc.name}({tc.arguments})")
    messages += [first.message, {"role": "tool", "tool_call_id": tc.id, "content": "2025"}]
    final = client.chat(messages, tools=[GET_YEAR], agent="smoke")
    show("(c) after tool result", final)
    print(f"      final answer: {final.content!r}")

    ledger = Ledger(settings.ledger_path)
    print(f"  network calls this run: {len(network)}")
    print(f"  ledger: requests {ledger.data['requests']} spend ${ledger.spend:.4f} notional ${ledger.data['notional_usd']:.6f}")
    print(f"  trace: {trace_path.relative_to(REPO_ROOT)} ({len(client.trace.events)} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "replay"))
