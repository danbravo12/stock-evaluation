"""Planner, orchestrator, reporter, batch and CLI: offline, on the 5 recorded companies (replay) and stubs."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import jsonschema

from engine import cli
from engine.batch import CompanyLedger, progress_markdown, run_batch
from engine.contracts import RunPlan
from engine.fetch.edgar import EdgarClient, EdgarError
from engine.llm.budget import BudgetExceeded, QuotaReached
from engine.llm.client import LLMFixtureMissing
from engine.orchestrator import analyse
from engine.planner import PRICE_GAP, plan_for
from engine.report import SCHEMA_PATH, Result, PublishGateError, finnhub_fields, write_result
from engine.score import score_ticker
from engine.settings import REPO_ROOT, Settings
from engine.universe import Constituent, Universe, load_universe

TICKERS = ["KO", "JPM", "GOOGL", "TSLA", "DUK"]
PRIMARY = ["GOOGL", "FOXA", "NWSA"]


def synthetic_universe():
    def c(sym, cik, name=None, sub="Y"):
        return Constituent(symbol=sym, security=name or sym, gics_sector="X", gics_sub_industry=sub, cik=cik, date_added="")
    return Universe([c("BNK", "0000000001", sub="Diversified Banks"), c("INS", "0000000002", sub="Multi-line Insurance"), c("UTL", "0000000003", sub="Electric Utilities"),
                     c("IND", "0000000004", sub="Industrial Conglomerates"), c("GOOG", "0001652044", "Alphabet C"), c("GOOGL", "0001652044", "Alphabet A")], "2026-01-01", PRIMARY)


class TestPlanner(unittest.TestCase):
    def test_sector_classes_decide_which_criteria_apply(self):
        u = synthetic_universe()
        for sym, sic, cls, na in [("BNK", 6021, "bank", ["G2", "B2", "B3", "B4"]), ("INS", 6311, "insurer", ["G2", "B2", "B3", "B4"]),
                                  ("UTL", 4911, "utility", []), ("IND", 3711, "other", []), ("IND", 6021, "other", []), ("IND", None, "other", [])]:
            p = plan_for(sym, u, sic)
            self.assertEqual((p.sector_class, [x.id for x in p.not_applicable]), (cls, na), sym)
            self.assertEqual(sorted(p.applicable + na), sorted([f"G{i}" for i in range(1, 8)] + [f"B{i}" for i in range(1, 5)]))
            self.assertTrue(p.in_scope and p.steps[0] == "fetch" and p.steps[-1] == "report")
        self.assertTrue(any("utility variant" in n for n in plan_for("UTL", u, 4911).notes))
        self.assertIn("(ADR-013)", plan_for("BNK", u, 6021).not_applicable[0].reason)

    def test_price_is_a_planned_gap(self):
        p = plan_for("IND", synthetic_universe(), 3711)
        self.assertIn(PRICE_GAP, [s.reason for s in p.skipped])

    def test_out_of_scope_ticker_gets_a_reason_and_no_steps(self):
        p = plan_for("ZZZZ", synthetic_universe())
        self.assertEqual((p.in_scope, p.steps, p.cik), (False, [], None))
        self.assertIn("not in the S&P 500 snapshot of 2026-01-01", p.out_of_scope_reason)

    def test_dual_class_second_symbol_is_planned_under_the_primary(self):
        u = synthetic_universe()
        self.assertEqual(plan_for("GOOG", u).cik, "0001652044")
        self.assertTrue(any("second share class" in n and "GOOGL" in n for n in plan_for("goog", u).notes))

    def test_plan_agrees_with_the_scorers_for_the_bank_fixture(self):
        edgar = EdgarClient("replay", Settings.from_env())
        u = load_universe(sec_tickers=edgar.company_tickers())
        for t in TICKERS:
            sic = edgar.submissions(u.row_for(t).cik).get("sic")
            plan = plan_for(t, u, sic)
            scored = score_ticker(edgar, t)
            self.assertEqual(plan.sector_class, scored.sector_class, t)
            self.assertEqual({x.id for x in plan.not_applicable}, {r.id for r in scored.results if r.label == "not_applicable"}, t)


class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = Settings.from_env()
        cls.edgar = EdgarClient("replay", cls.settings)
        cls.universe = load_universe(sec_tickers=cls.edgar.company_tickers())

    def run_analyse(self, ticker, directory, **kw):
        return analyse(ticker, mode="replay", settings=self.settings, universe=self.universe, edgar=self.edgar, results_dir=Path(directory), commit="test", **kw)


class TestOrchestrator(Replay):
    def test_out_of_scope_ticker_makes_a_plan_and_no_calls(self):
        class Boom:
            def __getattr__(self, name):
                raise AssertionError(f"edgar.{name} must not be called for an out-of-scope ticker")
        with tempfile.TemporaryDirectory() as d:
            r = analyse("ZZZZ", mode="replay", settings=self.settings, universe=self.universe, edgar=Boom(), results_dir=Path(d), commit="t")
            self.assertEqual(list(Path(d).iterdir()), [])
        self.assertFalse(r.plan.in_scope)
        self.assertEqual({s.status for s in r.steps if s.step != "report"}, {"skipped"})
        self.assertEqual((r.scorecard, r.qualitative, r.cost.llm_calls), (None, [], 0))
        self.assertIn("outside v1 scope", r.warnings[0].message)

    def test_a_full_run_has_every_step_done_and_the_expected_sections(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_analyse("KO", d)
        self.assertEqual([(s.step, s.status) for s in r.steps], [(s, "done") for s in ["fetch", "score", "qualitative", "explain_and_verify", "report"]])
        self.assertEqual(len(r.scorecard.criteria), 11)
        self.assertTrue(all(c.explanation for c in r.scorecard.criteria))
        self.assertEqual([q.finding.criterion for q in r.qualitative][:2], ["understandable_business", "durable_competitive_advantage"])
        self.assertEqual(set(r.cost.by_agent), {"critic", "explainer", "qualitative"})
        self.assertEqual(sum(a.calls for a in r.cost.by_agent.values()), r.cost.llm_calls)
        self.assertEqual(r.data.price, None)
        self.assertIn(PRICE_GAP, r.data.gaps)
        self.assertEqual((r.run.mode, r.run.generated_at, r.schema_version), ("replay", None, "1.4"))
        self.assertIn("not financial advice", r.disclaimer)
        self.assertTrue(any("Wikipedia" in a and "CC BY-SA" in a for a in r.attribution))
        self.assertTrue(any(s.kind == "sec_filing" and s.url for s in r.sources))

    def test_a_failing_score_step_degrades_and_skips_only_what_depends_on_it(self):
        with tempfile.TemporaryDirectory() as d, mock.patch("engine.orchestrator.score_company", side_effect=ValueError("no annual net income")):
            r = self.run_analyse("KO", d)
        status = {s.step: s for s in r.steps}
        self.assertEqual(status["score"].status, "failed")
        self.assertIn("no annual net income", status["score"].reason)
        self.assertEqual(status["qualitative"].status, "done")  # does not depend on the score
        self.assertEqual(status["explain_and_verify"].status, "skipped")
        self.assertIn("depends on score", status["explain_and_verify"].reason)
        self.assertEqual((r.scorecard, len(r.qualitative)), (None, 4))
        self.assertEqual({w.where for w in r.warnings}, {"score", "explain_and_verify"})

    def test_a_failing_qualitative_step_keeps_the_scorecard_without_explanations(self):
        with tempfile.TemporaryDirectory() as d, mock.patch("engine.orchestrator.assess_qualitative", side_effect=RuntimeError("model said no")):
            r = self.run_analyse("KO", d)
        self.assertEqual({s.step: s.status for s in r.steps}, {"fetch": "done", "score": "done", "qualitative": "failed", "explain_and_verify": "skipped", "report": "done"})
        self.assertEqual(len(r.scorecard.criteria), 11)
        self.assertTrue(all(c.explanation is None for c in r.scorecard.criteria))
        self.assertEqual((r.qualitative, r.critic), ([], None))

    def test_a_failing_fetch_skips_everything_after_it(self):
        with tempfile.TemporaryDirectory() as d, mock.patch("engine.orchestrator.normalise_from_store", side_effect=EdgarError("companyfacts unavailable")):
            r = self.run_analyse("KO", d)
        self.assertEqual({s.step: s.status for s in r.steps}, {"fetch": "failed", "score": "skipped", "qualitative": "skipped", "explain_and_verify": "skipped", "report": "done"})
        self.assertIsNone(r.scorecard)
        self.assertTrue(all("depends on" in s.reason for s in r.steps if s.status == "skipped"))

    def test_quota_budget_and_missing_fixture_errors_propagate_and_write_nothing(self):
        for exc in (QuotaReached("q"), BudgetExceeded("b"), LLMFixtureMissing("m")):
            with tempfile.TemporaryDirectory() as d, mock.patch("engine.orchestrator.assess_qualitative", side_effect=exc):
                with self.assertRaises(type(exc)):
                    self.run_analyse("KO", d)
                self.assertEqual([p.name for p in Path(d).glob("*.json")], [])

    def test_trace_tells_the_story_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            self.run_analyse("KO", d)
            events = [json.loads(l) for l in (Path(d) / "0000021344.trace.jsonl").read_text().splitlines()]
        agents = [e["agent"] for e in events]
        self.assertEqual(events[0]["agent"], "orchestrator")
        self.assertIn("plan:", events[0]["output"])
        first = {a.split("/")[0]: agents.index(a) for a in reversed(agents)}
        self.assertTrue(first["orchestrator"] < first["qualitative"] < first["explainer"] < first["critic"])
        self.assertEqual([e["step"] for e in events], list(range(1, len(events) + 1)))
        self.assertTrue(events[-1]["output"].startswith("report:"))


class TestReportAndDeterminism(Replay):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dirs = [tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()]
        cls.results = {}
        for d in cls.dirs:
            for t in TICKERS:
                cls.results[(d.name, t)] = analyse(t, mode="replay", settings=cls.settings, universe=cls.universe, edgar=cls.edgar, results_dir=Path(d.name), commit="test")

    @classmethod
    def tearDownClass(cls):
        for d in cls.dirs:
            d.cleanup()

    def test_two_replays_write_identical_files(self):
        a, b = (Path(d.name) for d in self.dirs)
        names = sorted(p.name for p in a.iterdir())
        self.assertEqual(len(names), 10)  # 5 results and 5 traces
        self.assertEqual(names, sorted(p.name for p in b.iterdir()))
        for n in names:
            self.assertEqual((a / n).read_bytes(), (b / n).read_bytes(), n)

    def test_results_validate_against_the_json_schema_and_round_trip(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(schema, json.loads(json.dumps(Result.model_json_schema(), sort_keys=True)), "schema/result.schema.json is stale: run python -m engine.cli schema")
        for p in Path(self.dirs[0].name).glob("*.json"):
            data = json.loads(p.read_text())
            jsonschema.validate(data, schema)
            self.assertEqual(json.loads(Result.model_validate(data).model_dump_json()), data)
            self.assertLess(p.stat().st_size, 150_000, p.name)

    def test_the_schema_rejects_a_broken_result(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        data = json.loads(next(Path(self.dirs[0].name).glob("*.json")).read_text())
        del data["plan"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(data, schema)

    def test_no_finnhub_field_in_any_result_and_the_gate_blocks_one(self):
        for p in Path(self.dirs[0].name).glob("*.json"):
            self.assertEqual(finnhub_fields(json.loads(p.read_text())), [], p.name)
        r = next(iter(self.results.values())).model_copy(deep=True)
        r.data.price = 123.4
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PublishGateError):
                write_result(r, Path(d))
            self.assertEqual(list(Path(d).iterdir()), [])
            write_result(r, Path(d), finnhub_public_ok=True)  # explicitly permitted
            self.assertEqual(len(list(Path(d).iterdir())), 1)

    def test_cost_by_agent_adds_up_and_the_free_tier_costs_nothing(self):
        for r in self.results.values():
            self.assertEqual(r.cost.actual_cost_usd, 0.0)
            self.assertAlmostEqual(sum(a.notional_cost_usd for a in r.cost.by_agent.values()), r.cost.notional_cost_usd, places=5)
            self.assertEqual(sum(a.input_tokens for a in r.cost.by_agent.values()), r.cost.input_tokens)

    def test_every_criterion_has_its_explanation_and_a_critic_status(self):
        for (_, t), r in self.results.items():
            for c in r.scorecard.criteria:
                self.assertTrue(c.explanation and c.critic_status, (t, c.id))
            keys = {f"{i.measure}:{i.fiscal_year}" for i in r.scorecard.inputs}
            self.assertTrue(all(k in keys for c in r.scorecard.criteria for k in c.input_keys), t)


class TestBatchAndCli(Replay):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = CompanyLedger(Path(self.tmp.name) / "companies.json")
        self.out = []

    def batch(self, symbols, analyse_fn=analyse, **kw):
        return run_batch(symbols, mode="replay", settings=self.settings, universe=self.universe, ledger=self.ledger, analyse_fn=analyse_fn, out=self.out.append,
                         edgar=self.edgar, results_dir=Path(self.tmp.name) / "results", commit="t", **kw)

    def test_quota_stops_the_batch_cleanly_and_a_resume_skips_finished_companies(self):
        calls = []

        def flaky(sym, **kw):
            calls.append(sym)
            if sym == "GOOGL":
                raise QuotaReached("quota reached: 490 of 500 requests used today")
            return analyse(sym, **kw)
        first = self.batch(["KO", "JPM", "GOOGL", "TSLA"], flaky)
        self.assertEqual((first.done, calls), (["KO", "JPM"], ["KO", "JPM", "GOOGL"]))
        self.assertIn("midnight Pacific", first.stopped)
        self.assertEqual({r["ticker"]: r["status"] for r in self.ledger.rows.values()}, {"KO": "done", "JPM": "warning"})  # JPM: the Critic still objects to one finding after its repair (a warning, not a failure)
        calls.clear()
        second = self.batch(["KO", "JPM", "GOOGL", "TSLA"], lambda s, **kw: (calls.append(s), analyse(s, **kw))[1])
        self.assertEqual((second.skipped, calls, second.stopped), (["KO", "JPM"], ["GOOGL", "TSLA"], None))
        third = self.batch(["KO", "JPM", "GOOGL", "TSLA"], lambda s, **kw: self.fail("everything is done"))
        self.assertEqual((third.done, third.skipped), ([], ["KO", "JPM", "GOOGL", "TSLA"]))

    def test_budget_error_stops_with_a_cap_message_and_force_re_runs(self):
        def over(sym, **kw):
            raise BudgetExceeded("projected $0.05 would take the total past the $6.00 cap")
        o = self.batch(["KO"], over)
        self.assertIn("cap", o.stopped)
        self.batch(["KO"])
        again = []
        self.batch(["KO"], lambda s, **kw: (again.append(s), analyse(s, **kw))[1], force=True)
        self.assertEqual(again, ["KO"])

    def test_limit_counts_analyses_not_skips(self):
        self.batch(["KO"])
        o = self.batch(["KO", "JPM", "GOOGL"], limit=1)
        self.assertEqual((o.skipped, o.done), (["KO"], ["JPM"]))

    def test_ledger_rows_and_progress_text(self):
        self.batch(["KO", "JPM"])
        row = next(r for r in self.ledger.rows.values() if r["ticker"] == "KO")
        self.assertEqual((row["model"], row["actual_cost_usd"]), ("gemini-3.1-flash-lite", 0.0))
        self.assertTrue(row["calls"] > 0 and row["input_tokens"] > 0 and row["finished_at"])
        text = progress_markdown(self.ledger, self.universe)
        self.assertIn("| Done |", text)
        self.assertIn("Remaining (not yet analysed) | 498", text)
        self.assertIn("Mean model calls", text)
        self.assertIn("days", text)
        self.assertIn("CC BY-SA", text)
        self.assertEqual(text, progress_markdown(CompanyLedger(self.ledger.path), self.universe))

    def test_progress_with_an_empty_ledger(self):
        text = progress_markdown(self.ledger, self.universe)
        self.assertIn("No company finished yet", text)
        self.assertIn("Not available until a company has finished", text)

    def test_cli_analyse_batch_and_status(self):
        env = {"LEDGER_PATH": str(Path(self.tmp.name) / "usage.json"), "RESULTS_DIR": str(Path(self.tmp.name) / "results")}
        with mock.patch.dict(os.environ, env), mock.patch.object(cli, "PROGRESS_PATH", Path(self.tmp.name) / "PROGRESS.md"):
            self.assertEqual(cli.main(["analyse", "KO", "--results-dir", self.tmp.name]), 0)
            self.assertTrue((Path(self.tmp.name) / "0000021344.json").exists())
            self.assertEqual(cli.main(["analyse", "ZZZZ", "--results-dir", self.tmp.name]), 1)
            self.assertEqual(cli.main(["batch", "--tickers", "JPM", "--results-dir", self.tmp.name]), 0)
            self.assertEqual(cli.main(["status"]), 0)
            self.assertIn("| Done |", (Path(self.tmp.name) / "PROGRESS.md").read_text())
            self.assertEqual(cli.main(["batch", "--results-dir", self.tmp.name]), 2)  # needs --tickers or --universe


class TestSampleResults(unittest.TestCase):
    def test_committed_sample_results_are_valid_and_gate_clean(self):
        files = sorted((REPO_ROOT / "results").glob("*.json"))
        if not files:
            self.skipTest("sample results not generated yet")
        schema = json.loads(SCHEMA_PATH.read_text())
        showcase = json.loads((REPO_ROOT / "config" / "showcase.json").read_text())  # the 5 test companies and the 20 showcase companies are committed (ADR-070)
        from engine.universe import load_universe
        u = load_universe()
        expected = {u.row_for(s).cik for s in [e["symbol"] for e in showcase["showcase"]] + [e["symbol"] for e in showcase["test_companies"]]}
        self.assertEqual({p.stem for p in files}, expected)
        self.assertEqual(len(files), 25)
        for p in files:
            data = json.loads(p.read_text())
            jsonschema.validate(data, schema)
            self.assertEqual(finnhub_fields(data), [])
            self.assertTrue((REPO_ROOT / data["trace_path"]).exists())


if __name__ == "__main__":
    unittest.main()
