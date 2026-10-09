"""A scripted model client for Explainer / Critic tests: complete_json returns the next prepared object and records the request."""
from __future__ import annotations

from engine.contracts import LLMCall, Usage


class StubLLM:
    def __init__(self, *replies):
        self.replies, self.calls, self.requests = list(replies), [], []

    def complete_json(self, messages, model_cls, **kwargs):
        reply = self.replies.pop(0)
        reply = reply(messages) if callable(reply) else reply
        assert isinstance(reply, model_cls), (type(reply), model_cls)
        self.requests.append({"model": model_cls.__name__, "messages": messages, "kwargs": kwargs})
        self.calls.append(LLMCall(profile="stub", model="stub", request_hash=f"h{len(self.calls)}", replayed=False, paid=False, latency_s=0.1,
                                  usage=Usage(prompt_tokens=100, completion_tokens=10, total_tokens=110), actual_cost_usd=0.0, notional_cost_usd=0.0001))
        return reply

    def chat(self, *a, **k):  # the qualitative retry is patched out in tests that route
        raise AssertionError("unexpected chat call")
