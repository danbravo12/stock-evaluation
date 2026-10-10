import { el, getJSON, tryJSON, fail, manifest, footer, secLink } from "./common.js";

const $ = (id) => document.getElementById(id);
const cik = new URLSearchParams(location.search).get("cik");
const AGENT_WORD = (a) => {
  if (a === "orchestrator") return "Planner and orchestrator";
  if (a === "explainer") return "Explainer";
  if (a === "critic") return "Critic (second reader)";
  const [base, crit, extra] = a.split("/");
  const names = { understandable_business: "understandable business", durable_competitive_advantage: "durable competitive advantage", candid_management: "candid management", rational_capital_allocation: "rational capital allocation" };
  return base === "qualitative" ? `Qualitative agent: ${names[crit] || crit}${extra ? " (rewrite)" : ""}` : a;
};
const TYPE_WORD = { llm_call: "Model call", tool_call: "Tool call", note: "Step" };
let events = [], at = 0, timer = null, cum = [];

function describe(out) {
  if (out == null) return "No output recorded.";
  if (typeof out === "string") return out;
  if (Array.isArray(out)) return out.map((o) => (o && o.tool ? `Calls ${o.tool}\n${Object.entries(o.arguments || {}).map(([k, v]) => `  ${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`).join("\n")}` : typeof o === "string" ? o : JSON.stringify(o, null, 1))).join("\n\n");
  if (typeof out === "object") return Object.entries(out).map(([k, v]) => `${k.replaceAll("_", " ")}: ${typeof v === "string" ? v : JSON.stringify(v)}`).join("\n");
  return String(out);
}
const shortOf = (e) => {
  const t = typeof e.output === "string" ? e.output : e.input_summary || (e.type === "llm_call" ? "Model call" : "Step");
  return t.length > 90 ? t.slice(0, 88) + "…" : t;
};

function renderSteps() {
  const ol = $("steps");
  let last = null;
  events.forEach((e, i) => {
    if (e.agent !== last) {
      if (last !== null) ol.append(el("li", { class: "handoff", text: `Hands over from ${AGENT_WORD(last)} to ${AGENT_WORD(e.agent)}` }));
      ol.append(el("li", { class: "group", text: AGENT_WORD(e.agent) }));
      last = e.agent;
    }
    ol.append(el("li", {}, el("button", { class: "step", type: "button", "data-i": i, onclick: () => go(i) },
      el("span", { class: "n", text: i + 1 }), el("span", { class: "what", text: `${TYPE_WORD[e.type]}: ${shortOf(e)}` }))));
  });
}

function go(i) {
  at = Math.max(0, Math.min(events.length - 1, i));
  document.querySelectorAll(".step").forEach((b) => {
    const on = Number(b.dataset.i) === at;
    if (on) { b.setAttribute("aria-current", "step"); const ol = $("steps"), top = b.offsetTop - ol.offsetTop; if (top < ol.scrollTop + 40 || top > ol.scrollTop + ol.clientHeight - 60) ol.scrollTop = Math.max(0, top - ol.clientHeight / 2); } else b.removeAttribute("aria-current");
  });
  const e = events[at], tot = cum[at];
  const d = $("detail");
  const rows = [];
  rows.push(el("h2", { text: `Step ${at + 1} of ${events.length}: ${TYPE_WORD[e.type]}` }), el("p", { class: "muted", text: AGENT_WORD(e.agent) }));
  if (e.input_summary) rows.push(el("h3", { text: "What it was given" }), el("p", { class: "out", text: e.input_summary }));
  rows.push(el("h3", { text: "What it produced" }), el("p", { class: "out", text: describe(e.output) }));
  if (e.usage || e.latency_s != null) {
    const bits = [];
    if (e.usage) bits.push(`${e.usage.prompt_tokens.toLocaleString("en-US")} tokens in, ${e.usage.completion_tokens.toLocaleString("en-US")} out`);
    if (e.latency_s != null) bits.push(`${e.latency_s.toFixed(1)} seconds as first recorded`);
    if (e.notional_cost_usd != null) bits.push(`about $${e.notional_cost_usd.toFixed(5)} at paid rates`);
    if (e.replayed) bits.push("replayed from the recorded response, no new spend");
    rows.push(el("h3", { text: "Cost" }), el("p", { text: bits.join("; ") + "." }));
  }
  d.replaceChildren(...rows);
  $("totals").textContent = `So far: ${tot.calls} model calls, ${tot.tokens.toLocaleString("en-US")} tokens, about $${tot.cost.toFixed(4)} at paid rates.`;
  $("back").disabled = at === 0; $("fwd").disabled = at === events.length - 1;
  history.replaceState(null, "", `#${at + 1}`);
}

function play(on) {
  clearInterval(timer); timer = null;
  $("play").setAttribute("aria-pressed", String(on));
  $("play").textContent = on ? "Pause" : "Play";
  if (on) {
    if (at >= events.length - 1) go(0);
    const slow = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1800 : 900;
    timer = setInterval(() => { if (at >= events.length - 1) play(false); else go(at + 1); }, slow);
  }
}

async function main() {
  footer(await manifest());
  if (!cik) throw new Error("No company was asked for. Open a replay from a company page.");
  const [trace, result] = await Promise.all([getJSON(`data/results/${cik}.trace.json`), tryJSON(`data/results/${cik}.json`)]);
  events = trace;
  let c = { calls: 0, tokens: 0, cost: 0 };
  cum = events.map((e) => { if (e.type === "llm_call" && e.usage) { c = { calls: c.calls + 1, tokens: c.tokens + e.usage.total_tokens, cost: c.cost + (e.notional_cost_usd || 0) }; } return c; });
  const name = result ? `${result.plan.name} (${result.plan.ticker})` : cik;
  document.title = `Agent run for ${name}`;
  $("title").textContent = `How the agents analysed ${name}`;
  $("crumbs").replaceChildren(el("a", { href: "index.html", text: "All rankings" }), " / ", el("a", { href: `company.html?cik=${cik}`, text: name }));
  const agents = [...new Set(events.map((e) => AGENT_WORD(e.agent.split("/")[0] === "qualitative" ? "qualitative/x" : e.agent)))];
  $("lede").textContent = "This is a recorded run, replayed from files: no model is called on this page. The planner decides what to run, the scorers do the arithmetic, one agent per Buffett question reads the 10-K, the Explainer writes the plain-English lines, and the Critic re-checks everything against the filing. Step through to see each hand-off.";
  $("bar").hidden = false; $("tr").hidden = false;
  renderSteps();
  $("back").onclick = () => go(at - 1); $("fwd").onclick = () => go(at + 1); $("play").onclick = () => play(!timer);
  document.addEventListener("keydown", (ev) => {
    if (ev.target.closest("input, select, textarea")) return;
    if (ev.key === "ArrowRight") { ev.preventDefault(); go(at + 1); }
    else if (ev.key === "ArrowLeft") { ev.preventDefault(); go(at - 1); }
  });
  const start = parseInt(location.hash.slice(1), 10);
  go(Number.isFinite(start) ? start - 1 : 0);
}
main().catch((e) => fail(e.message, "Replays exist only for companies with a full agent analysis."));
