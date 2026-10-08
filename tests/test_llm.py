"""LLM client, cost meter, budget guard and trace recorder: fully offline with a fake transport."""
from __future__ import annotations

import gzip
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from pydantic import BaseModel

from engine.contracts import Usage
from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.llm.client import LLMClient, LLMError, LLMFixtureMissing, LLMValidationError, load_models_config, request_hash
from engine.llm.cost import notional_cost, projected_cost
from engine.settings import REPO_ROOT, Settings
from engine.trace import TraceRecorder

KEY = "SECRET-KEY-123"
MESSAGES = [{"role": "user", "content": "Say hello"}]


def ok(content="hello", usage=(10, 5, 15), tool_calls=None, extra=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    body = {"choices": [{"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": usage[0], "completion_tokens": usage[1], "total_tokens": usage[2], **(extra or {})}}
    return 200, {}, json.dumps(body).encode()


class FakeTransport:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def __call__(self, url, headers, body, timeout):
        self.calls.append((url, headers, body))
        if not self.responses:
            raise AssertionError("unexpected network call")
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


class Clock:
    """Wall clock that moves when the client sleeps."""

    def __init__(self, start="2026-10-09T12:00:00+00:00"):
        self.dt, self.sleeps = datetime.fromisoformat(start), []

    def now(self):
        return self.dt

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.dt += timedelta(seconds=seconds)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {"GEMINI_API_KEY": KEY})
        self.env.start()
        self.clock = Clock()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def settings(self, paid=False):
        return Settings(None, self.root / "fixtures", self.root / "cache", llm_profile="gemini-3.1-flash-lite",
                        paid_mode_enabled=paid, ledger_path=self.root / "ledger" / "usage.json")

    def client(self, mode="live", transport=None, paid=False, trace=None):
        return LLMClient(mode, self.settings(paid), transport=transport or FakeTransport(ok()), sleep=self.clock.sleep,
                         now=self.clock.now, clock=lambda: 0.0, trace=trace)

    def write_ledger(self, **data):
        path = self.root / "ledger" / "usage.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))


class TestRecordReplay(Base):
    def test_request_hash_is_stable_and_excludes_the_key(self):
        c = self.client()
        a, b = c.chat(MESSAGES), c.chat(MESSAGES)
        other = c.chat([{"role": "user", "content": "Say goodbye"}])
        self.assertEqual(a.request_hash, b.request_hash)
        self.assertNotEqual(a.request_hash, other.request_hash)
        request = {"profile": "p", "model": "m", "messages": MESSAGES, "tools": None, "response_format": None, "temperature": 0.0, "max_tokens": None}
        self.assertEqual(request_hash(request), request_hash(dict(reversed(list(request.items())))))  # key order does not matter
        self.assertNotIn(KEY, json.dumps(request))

    def test_record_then_replay_makes_no_network_call(self):
        self.client("record", FakeTransport(ok("recorded"))).chat(MESSAGES)
        replay_transport = FakeTransport()
        call = self.client("replay", replay_transport).chat(MESSAGES)
        self.assertEqual((call.content, call.replayed, call.actual_cost_usd), ("recorded", True, 0.0))
        self.assertEqual(replay_transport.calls, [])

    def test_replay_miss_raises_and_never_calls_the_network(self):
        transport = FakeTransport(ok())
        with self.assertRaises(LLMFixtureMissing):
            self.client("replay", transport).chat(MESSAGES)
        self.assertEqual(transport.calls, [])

    def test_live_mode_caches_after_the_first_call(self):
        transport = FakeTransport(ok())
        c = self.client("live", transport)
        first, second = c.chat(MESSAGES), c.chat(MESSAGES)
        self.assertEqual((len(transport.calls), first.replayed, second.replayed), (1, False, True))
        self.assertTrue(any((self.root / "cache" / "llm").rglob("*.gz")))
        self.assertFalse((self.root / "fixtures").exists())  # live never writes fixtures

    def test_key_required_for_live_and_record_but_not_replay(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            for mode in ("live", "record"):
                with self.assertRaises(LLMError):
                    self.client(mode)
            self.client("replay")

    def test_unknown_profile(self):
        with self.assertRaises(LLMError):
            LLMClient("replay", self.settings(), profile="nope")

    def test_request_uses_bearer_header_and_default_temperature_zero(self):
        t = FakeTransport(ok())
        self.client("record", t).chat(MESSAGES)
        url, headers, body = t.calls[0]
        self.assertTrue(url.endswith("/chat/completions"))
        self.assertEqual(headers["Authorization"], f"Bearer {KEY}")
        self.assertEqual(json.loads(body)["temperature"], 0.0)
        self.assertNotIn("profile", json.loads(body))


class TestCost(Base):
    def test_free_tier_actual_is_zero_and_notional_from_prices(self):
        call = self.client(transport=FakeTransport(ok(usage=(1000, 2000, 3000)))).chat(MESSAGES)
        self.assertEqual(call.actual_cost_usd, 0.0)
        self.assertAlmostEqual(call.notional_cost_usd, (1000 * 0.25 + 2000 * 1.5) / 1e6)
        self.assertFalse(call.paid)

    def test_thinking_tokens_count_as_output(self):  # total 5000 = 1000 prompt + 500 reported + 3500 thinking
        call = self.client(transport=FakeTransport(ok(usage=(1000, 500, 5000), extra={"completion_tokens_details": {"reasoning_tokens": 3500}}))).chat(MESSAGES)
        self.assertEqual((call.usage.completion_tokens, call.usage.reasoning_tokens), (4000, 3500))

    def test_profiles_without_a_price_cost_nothing_notionally(self):
        cfg = load_models_config()["profiles"]
        self.assertEqual(notional_cost(Usage(prompt_tokens=10, completion_tokens=10), cfg["gemma-4-31b"]), 0.0)
        self.assertIsNone(projected_cost(MESSAGES, 100, cfg["gemma-4-31b"]))

    def test_projection_is_chars_over_four_plus_max_tokens(self):
        profile = load_models_config()["profiles"]["gemini-3.1-flash-lite"]
        self.assertAlmostEqual(projected_cost([{"role": "user", "content": "x" * 400}], 1000, profile), (100 * 0.25 + 1000 * 1.5) / 1e6)


class TestBudgetGuard(Base):
    def test_rpm_pacing_sleeps_between_requests(self):
        c = self.client(transport=FakeTransport(ok()))
        c.chat(MESSAGES)
        self.assertEqual(self.clock.sleeps, [])
        c.chat([{"role": "user", "content": "again"}])
        self.assertEqual(self.clock.sleeps, [60 / 15])  # 15 requests per minute

    def test_rpd_guard_refuses_at_limit_minus_margin(self):
        today = "2026-10-09"
        self.write_ledger(requests={"gemini-3.1-flash-lite": {today: 489}})
        t = FakeTransport(ok())
        self.client(transport=t).chat(MESSAGES)  # request 490 of 490 allowed
        with self.assertRaises(QuotaReached) as ctx:
            self.client(transport=t).chat([{"role": "user", "content": "one more"}])
        self.assertIn("resume after midnight Pacific", str(ctx.exception))
        self.assertEqual(len(t.calls), 1)

    def test_daily_count_resets_at_midnight_pacific(self):
        # 06:59 UTC on 9 Oct is 23:59 on 8 Oct in Los Angeles (PDT); two minutes later it is the next day.
        self.clock.dt = datetime(2026, 10, 9, 6, 59, tzinfo=timezone.utc)
        self.write_ledger(requests={"gemini-3.1-flash-lite": {"2026-10-08": 490}})
        with self.assertRaises(QuotaReached):
            self.client().chat(MESSAGES)
        self.clock.dt = datetime(2026, 10, 9, 7, 1, tzinfo=timezone.utc)
        self.assertEqual(self.client().chat(MESSAGES).content, "hello")

    def test_ledger_is_shared_between_clients(self):
        self.client(transport=FakeTransport(ok())).chat(MESSAGES)
        self.client(transport=FakeTransport(ok())).chat([{"role": "user", "content": "b"}])
        ledger = json.loads((self.root / "ledger" / "usage.json").read_text())
        self.assertEqual(ledger["requests"]["gemini-3.1-flash-lite"]["2026-10-09"], 2)

    def test_paid_call_beyond_quota_is_refused_unless_enabled(self):
        self.write_ledger(requests={"gemini-3.1-flash-lite": {"2026-10-09": 490}})
        with self.assertRaises(QuotaReached):
            self.client(paid=False).chat(MESSAGES)
        call = self.client(transport=FakeTransport(ok(usage=(1000, 2000, 3000))), paid=True).chat(MESSAGES)
        self.assertTrue(call.paid)
        self.assertAlmostEqual(call.actual_cost_usd, call.notional_cost_usd)
        self.assertGreater(call.actual_cost_usd, 0)
        ledger = json.loads((self.root / "ledger" / "usage.json").read_text())
        self.assertAlmostEqual(ledger["spend_usd"], call.actual_cost_usd)

    def test_calls_inside_the_free_quota_stay_free_even_in_paid_mode(self):
        call = self.client(paid=True).chat(MESSAGES)
        self.assertEqual((call.paid, call.actual_cost_usd), (False, 0.0))

    def test_total_and_company_caps_block_projected_overspend(self):
        self.write_ledger(requests={"gemini-3.1-flash-lite": {"2026-10-09": 490}}, spend_usd=3.99999)
        t = FakeTransport(ok())
        with self.assertRaises(BudgetExceeded) as ctx:
            self.client(transport=t, paid=True).chat(MESSAGES, max_tokens=4000)
        self.assertIn("cap", str(ctx.exception))
        self.write_ledger(requests={"gemini-3.1-flash-lite": {"2026-10-09": 490}}, spend_usd=0.0, companies={"0000021344": 0.0499})
        with self.assertRaises(BudgetExceeded):
            self.client(transport=t, paid=True).chat(MESSAGES, max_tokens=4000, company="0000021344")
        self.assertEqual(t.calls, [])

    def test_daily_quota_429_stops_cleanly_and_is_remembered(self):
        body = json.dumps({"error": {"message": "Quota exceeded", "details": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}}).encode()
        t = FakeTransport((429, {}, body))
        with self.assertRaises(QuotaReached) as ctx:
            self.client(transport=t).chat(MESSAGES)
        self.assertIn("resume after midnight Pacific", str(ctx.exception))
        self.assertEqual(len(t.calls), 1)
        with self.assertRaises(QuotaReached):  # the next run stops before sending anything
            self.client(transport=t).chat([{"role": "user", "content": "other"}])
        self.assertEqual(len(t.calls), 1)

    def test_per_minute_429_is_retried_honouring_retry_after(self):
        body = json.dumps({"error": {"message": "Resource exhausted: requests per minute"}}).encode()
        t = FakeTransport((429, {"retry-after": "37"}, body), ok())
        self.assertEqual(self.client(transport=t).chat(MESSAGES).content, "hello")
        self.assertEqual(len(t.calls), 2)
        self.assertIn(37.0, self.clock.sleeps)

    def test_server_errors_retry_then_give_up_after_four_attempts(self):
        t = FakeTransport((503, {}, b""))
        with self.assertRaises(LLMError):
            self.client(transport=t).chat(MESSAGES)
        self.assertEqual(len(t.calls), 4)

    def test_400_is_not_retried_and_the_key_is_redacted(self):
        t = FakeTransport((400, {}, json.dumps({"error": {"message": f"bad request for key {KEY}"}}).encode()))
        with self.assertRaises(LLMError) as ctx:
            self.client(transport=t).chat(MESSAGES)
        self.assertEqual(len(t.calls), 1)
        self.assertNotIn(KEY, str(ctx.exception))

    def test_connection_errors_are_retried(self):
        calls = []

        def flaky(url, headers, body, timeout):
            calls.append(1)
            if len(calls) == 1:
                raise ConnectionResetError("boom")
            return ok()

        self.assertEqual(self.client(transport=flaky).chat(MESSAGES).content, "hello")


class Answer(BaseModel):
    ok: bool
    word: str


class TestStructuredOutput(Base):
    def test_json_happy_path_requests_json_mode(self):
        t = FakeTransport(ok('{"ok": true, "word": "graham"}'))
        result = self.client(transport=t).complete_json(MESSAGES, Answer)
        self.assertEqual(result, Answer(ok=True, word="graham"))
        sent = json.loads(t.calls[0][2])
        self.assertEqual(sent["response_format"], {"type": "json_object"})
        self.assertIn("JSON schema", sent["messages"][0]["content"])

    def test_fenced_json_is_accepted(self):
        t = FakeTransport(ok('```json\n{"ok": false, "word": "x"}\n```'))
        self.assertFalse(self.client(transport=t).complete_json(MESSAGES, Answer).ok)

    def test_one_repair_attempt_with_the_validation_error(self):
        t = FakeTransport(ok('{"ok": "maybe"}'), ok('{"ok": true, "word": "fixed"}'))
        result = self.client(transport=t).complete_json(MESSAGES, Answer)
        self.assertEqual(result.word, "fixed")
        repair = json.loads(t.calls[1][2])["messages"]
        self.assertIn("not valid", repair[-1]["content"])
        self.assertEqual(repair[-2]["role"], "assistant")

    def test_two_failures_raise(self):
        t = FakeTransport(ok("not json"), ok("still not json"))
        with self.assertRaises(LLMValidationError):
            self.client(transport=t).complete_json(MESSAGES, Answer)
        self.assertEqual(len(t.calls), 2)

    def test_tool_calls_are_parsed_and_the_raw_message_kept(self):
        tc = [{"id": "call_1", "type": "function", "function": {"name": "get_year", "arguments": "{\"x\": 1}"}, "extra_content": {"google": {"thought_signature": "sig"}}}]
        call = self.client(transport=FakeTransport(ok(content=None, tool_calls=tc))).chat(MESSAGES, tools=[{"type": "function", "function": {"name": "get_year"}}])
        self.assertEqual([(t.id, t.name, t.arguments) for t in call.tool_calls], [("call_1", "get_year", {"x": 1})])
        self.assertEqual(call.message["tool_calls"][0]["extra_content"]["google"]["thought_signature"], "sig")


class TestTraceAndSecrets(Base):
    def test_trace_events_are_written_as_jsonl(self):
        path = self.root / "trace" / "run.jsonl"
        trace = TraceRecorder("run-1", path, now=self.clock.now)
        c = self.client(transport=FakeTransport(ok("hi there")), trace=trace)
        c.chat(MESSAGES, agent="explainer")
        trace.tool_call("qualitative", "search", {"query": "brand"}, "3 hits")
        trace.note("orchestrator", "done")
        events = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([(e["step"], e["agent"], e["type"]) for e in events],
                         [(1, "explainer", "llm_call"), (2, "qualitative", "tool_call"), (3, "orchestrator", "note")])
        self.assertEqual(events[0]["usage"]["total_tokens"], 15)
        self.assertEqual((events[0]["output"], events[0]["replayed"], events[0]["actual_cost_usd"]), ("hi there", False, 0.0))
        self.assertTrue(all(e["run_id"] == "run-1" for e in events))

    def test_the_api_key_appears_in_no_stored_file(self):
        path = self.root / "trace.jsonl"
        trace = TraceRecorder("run-1", path)
        self.client("record", FakeTransport(ok()), trace=trace).chat(MESSAGES)
        with self.assertRaises(LLMError):
            self.client("record", FakeTransport((400, {}, f"echo {KEY}".encode())), trace=trace).chat([{"role": "user", "content": "other"}])
        for f in self.root.rglob("*"):
            if f.is_file():
                data = f.read_bytes()
                data = gzip.decompress(data) if f.suffix == ".gz" else data
                self.assertNotIn(KEY.encode(), data, str(f))

    def test_committed_llm_fixtures_and_sample_traces_do_not_contain_the_real_key(self):
        env_file = REPO_ROOT / ".env"  # read directly: setUp patches the environment variable
        key = next((line.split("=", 1)[1].strip().strip("\"'") for line in env_file.read_text().splitlines()
                    if line.startswith("GEMINI_API_KEY=")), "") if env_file.exists() else ""
        if not key:
            self.skipTest("no real key in .env")
        scanned = 0
        for root in (REPO_ROOT / "fixtures" / "llm", REPO_ROOT / "data" / "cache" / "trace", REPO_ROOT / "data" / "ledger"):
            for f in root.rglob("*") if root.exists() else []:
                if f.is_file():
                    data = gzip.decompress(f.read_bytes()) if f.suffix == ".gz" else f.read_bytes()
                    self.assertNotIn(key.encode(), data, str(f))
                    scanned += 1
        self.assertGreater(scanned, 0)


class TestListModels(Base):
    def test_list_models_reads_ids(self):
        t = FakeTransport((200, {}, json.dumps({"data": [{"id": "models/a"}, {"id": "models/b"}]}).encode()))
        self.assertEqual(self.client(transport=t).list_models(), ["models/a", "models/b"])
        self.assertTrue(t.calls[0][0].endswith("/models"))
        self.assertIsNone(t.calls[0][2])


if __name__ == "__main__":
    unittest.main()
