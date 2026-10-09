"""Provider-agnostic LLM client over OpenAI-compatible HTTP, with record/replay (ADR-038, ADR-040).

Modes mirror the SEC fetcher (ADR-025):
* ``replay`` - fixtures only; a miss raises LLMFixtureMissing; never touches the network (default for tests).
* ``live``   - the git-ignored cache; on a miss call the provider and cache the response.
* ``record`` - always call the provider and write the response into fixtures/llm/.

A request is identified by the hash of its canonical form (profile, model, messages, tools, response
format, temperature, max_tokens). The API key and headers are never part of it, nor of any stored file,
trace or error message.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, TypeVar

from pydantic import BaseModel

from engine.contracts import LLMCall, ToolCall, Usage
from engine.fetch.store import ResponseStore
from engine.llm.budget import Budget, Ledger, LLMError, QuotaReached
from engine.llm.cost import actual_cost, notional_cost, projected_cost
from engine.settings import REPO_ROOT, Settings
from engine.trace import TraceRecorder

Mode = Literal["replay", "live", "record"]
# transport(url, headers, body, timeout) -> (status, response headers, body); body None means GET
Transport = Callable[[str, dict, "bytes | None", float], "tuple[int, dict, bytes]"]
M = TypeVar("M", bound=BaseModel)

MODELS_CONFIG_PATH = REPO_ROOT / "config" / "models.json"
BACKOFF_S = (2.0, 4.0, 8.0)  # 4 attempts in total
RATE_LIMIT_WAIT_S = 20.0  # per-minute 429 without a Retry-After header
DAILY_MARKERS = ("perday", "per day", "daily", "requests_per_day")


class LLMFixtureMissing(LLMError):
    """Replay mode was asked for a request that was never recorded."""


class LLMValidationError(LLMError):
    """The model did not return JSON matching the requested schema, even after one repair attempt."""


def load_models_config(path: Path = MODELS_CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def request_hash(request: dict) -> str:
    return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def urllib_transport(url: str, headers: dict, body: bytes | None, timeout: float) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


class LLMClient:
    def __init__(self, mode: Mode, settings: Settings | None = None, profile: str | None = None, transport: Transport | None = None,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), trace: TraceRecorder | None = None,
                 config: dict | None = None, timeout_s: float = 120.0, use_store: bool = True):
        if mode not in ("replay", "live", "record"):
            raise ValueError(f"Unknown mode {mode!r}")
        self.mode, self.settings = mode, settings or Settings.from_env()
        self.config = config or load_models_config()
        self.profile_name = profile or self.settings.llm_profile or self.config["default_profile"]
        if self.profile_name not in self.config["profiles"]:
            raise LLMError(f"Unknown LLM profile {self.profile_name!r}; known: {', '.join(self.config['profiles'])}")
        self.profile = self.config["profiles"][self.profile_name]
        self.transport, self._sleep, self._clock, self._now = transport or urllib_transport, sleep, clock, now
        self.trace, self.timeout_s, self.calls = trace, timeout_s, []
        self.use_store = use_store  # False (live only): never read or write the response store, so each call is a fresh request (variability runs)
        root = Path(self.settings.cache_dir if mode == "live" else self.settings.fixtures_dir) / "llm"
        self.store = ResponseStore(root)
        self._key = os.environ.get(self.profile["key_env"] or "") or None
        self.budget = None
        if mode != "replay":
            if self.profile["key_env"] and not self._key:
                raise LLMError(f"{self.profile['key_env']} is not set. Add it to .env to use mode {mode!r} (replay needs no key).")
            self.budget = Budget(self.profile_name, self.profile, self.config["budget"], Ledger(self.settings.ledger_path),
                                 self.settings.paid_mode_enabled, now, sleep)

    # ---------- public API ----------
    def chat(self, messages: list[dict], tools: list[dict] | None = None, response_format: dict | None = None,
             temperature: float = 0.0, max_tokens: int | None = None, *, company: str | None = None, agent: str = "llm") -> LLMCall:
        request = {"profile": self.profile_name, "model": self.profile["model"], "messages": messages, "tools": tools,
                   "response_format": response_format, "temperature": temperature, "max_tokens": max_tokens}
        digest = request_hash(request)
        key = f"{self.profile_name}/{digest}.json"
        call = None
        if self.mode in ("replay", "live") and (self.use_store or self.mode == "replay"):
            hit = self.store.get(key)
            if hit is not None:
                env = json.loads(hit.body)
                call = self._parse(env["response"], digest, env["latency_s"], replayed=True, paid=False)
            elif self.mode == "replay":
                raise LLMFixtureMissing(f"No recorded LLM response for request {digest[:12]} (profile {self.profile_name}). "
                                        "Record it with scripts/llm_smoke.py or LLMClient('record') on a machine with the key.")
        if call is None:
            response, latency, paid, url = self._send(request, company)
            envelope = {"request": request, "response": response, "latency_s": round(latency, 3)}
            if self.use_store or self.mode == "record":
                self.store.put(key, url, json.dumps(envelope, sort_keys=True).encode(), "application/json")
            call = self._parse(response, digest, round(latency, 3), replayed=False, paid=paid)
            self.budget.record_cost(call.actual_cost_usd, call.notional_cost_usd, company)
        self.calls.append(call)
        if self.trace:
            self.trace.llm_call(agent, messages, call)
        return call

    def complete_json(self, messages: list[dict], model_cls: type[M], *, agent: str = "llm", **kwargs) -> M:
        """Ask for JSON matching `model_cls`; one repair retry with the validation error, then raise."""
        schema = {"role": "system", "content": "Reply with only one JSON object matching this JSON schema, and no other text:\n"
                                                + json.dumps(model_cls.model_json_schema(), sort_keys=True)}
        history = [schema] + list(messages)
        call = self.chat(history, response_format={"type": "json_object"}, agent=agent, **kwargs)
        try:
            return model_cls.model_validate_json(_strip_fences(call.content or ""))
        except ValueError as first:
            history += [{"role": "assistant", "content": call.content or ""},
                        {"role": "user", "content": f"That reply was not valid: {str(first)[:500]}\nReply again with only the corrected JSON object."}]
            call = self.chat(history, response_format={"type": "json_object"}, agent=agent, **kwargs)
            try:
                return model_cls.model_validate_json(_strip_fences(call.content or ""))
            except ValueError as second:
                raise LLMValidationError(f"Model reply did not match {model_cls.__name__} after one repair attempt: {str(second)[:300]}") from None

    def list_models(self) -> list[str]:
        """Ids the provider offers (live check that a configured model id exists)."""
        if self.mode == "replay":
            raise LLMError("list_models needs the network: use mode 'live' or 'record'")
        self.budget.authorise(None, None)
        self.budget.pace()
        self.budget.record_request()
        status, _, body = self.transport(self.profile["base_url"].rstrip("/") + "/models", self._headers(), None, self.timeout_s)
        if status != 200:
            raise LLMError(f"HTTP {status} listing models: {self._error_text(body)}")
        return [m["id"] for m in json.loads(body)["data"]]

    # ---------- internals ----------
    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        return headers

    def _redact(self, text: str) -> str:
        return text.replace(self._key, "<redacted>") if self._key else text

    def _error_text(self, body: bytes) -> str:
        text = body.decode("utf-8", errors="replace")
        try:
            err = json.loads(text)
            err = err[0] if isinstance(err, list) and err else err
            text = err.get("error", {}).get("message") or text
        except (ValueError, AttributeError):
            pass
        return self._redact(" ".join(str(text).split())[:300])

    def _send(self, request: dict, company: str | None):
        url = self.profile["base_url"].rstrip("/") + "/chat/completions"
        payload = {k: v for k, v in request.items() if k != "profile" and v is not None}
        body = json.dumps(payload).encode()
        projected = projected_cost(request["messages"], request["max_tokens"] or self.config["budget"]["default_max_tokens"], self.profile)
        problem = ""
        for attempt in range(len(BACKOFF_S) + 1):
            paid = self.budget.authorise(projected, company)  # raises before anything is sent
            self.budget.pace()
            self.budget.record_request()  # every attempt counts against the daily quota
            started = self._clock()
            try:
                status, headers, resp = self.transport(url, self._headers(), body, self.timeout_s)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                status, headers, resp, problem = None, {}, b"", self._redact(str(e))
            latency = self._clock() - started
            if status == 200:
                return json.loads(resp), latency, paid, url
            wait = BACKOFF_S[attempt] if attempt < len(BACKOFF_S) else 0.0
            if status == 429:
                text = resp.decode("utf-8", errors="replace").lower()
                if any(marker in text for marker in DAILY_MARKERS):
                    self.budget.exhaust_today()
                    raise QuotaReached("quota reached; resume after midnight Pacific")
                wait = max(wait, RATE_LIMIT_WAIT_S, self._retry_after(headers))
                problem = "HTTP 429 (per-minute limit)"
            elif status is None or 500 <= status < 600:
                problem = problem or f"HTTP {status}"
                wait = max(wait, self._retry_after(headers))
            else:  # 400 and other client errors are not retried
                raise LLMError(f"HTTP {status} from {self.profile_name}: {self._error_text(resp)}")
            if attempt < len(BACKOFF_S):
                self._sleep(wait)
        raise LLMError(f"Giving up on {self.profile_name} after {len(BACKOFF_S) + 1} attempts ({problem})")

    @staticmethod
    def _retry_after(headers: dict) -> float:
        try:
            return float(headers.get("retry-after", ""))
        except ValueError:
            return 0.0

    def _parse(self, response: dict, digest: str, latency: float, replayed: bool, paid: bool) -> LLMCall:
        message = response["choices"][0]["message"]
        raw_usage = response.get("usage") or {}
        prompt, completion = raw_usage.get("prompt_tokens", 0), raw_usage.get("completion_tokens", 0)
        total = raw_usage.get("total_tokens", prompt + completion)
        details = raw_usage.get("completion_tokens_details") or {}
        # Thinking tokens are billed as output; some providers leave them out of completion_tokens, so
        # take the larger of completion_tokens and total - prompt.
        usage = Usage(prompt_tokens=prompt, completion_tokens=max(completion, total - prompt), total_tokens=total,
                      reasoning_tokens=details.get("reasoning_tokens", 0) or 0)
        tool_calls = []
        for tc in message.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except ValueError:
                args = {"_unparsed": tc["function"].get("arguments")}
            tool_calls.append(ToolCall(id=tc.get("id", ""), name=tc["function"]["name"], arguments=args))
        return LLMCall(profile=self.profile_name, model=self.profile["model"], request_hash=digest, replayed=replayed, paid=paid,
                       latency_s=latency, usage=usage, actual_cost_usd=0.0 if replayed else actual_cost(usage, self.profile, paid),
                       notional_cost_usd=notional_cost(usage, self.profile), finish_reason=response["choices"][0].get("finish_reason"),
                       content=message.get("content"), tool_calls=tool_calls, message=message)
