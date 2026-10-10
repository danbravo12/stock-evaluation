import { el, getJSON, tryJSON, fail, manifest, footer } from "./common.js";

const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const cik = new URLSearchParams(location.search).get("cik");
let data, at = 0, timer = null;

const plural = (n, one, many) => `${n.toLocaleString("en-US")} ${n === 1 ? one : many || one + "s"}`;
const laneName = (id) => data.lanes.find((l) => l.id === id).name;

// ---------- swimlane overview ----------
function swimlane() {
  const lanes = data.lanes, steps = data.steps;
  const dx = Math.max(11, Math.min(18, Math.floor(900 / steps.length))), left = 168, top = 16, rowH = 30;
  const W = left + steps.length * dx + 24, H = top + lanes.length * rowH + 10;
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("class", "swimsvg");
  const add = (parent, tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text != null) e.textContent = text; parent.append(e); return e; };
  const y = (lane) => top + lanes.findIndex((l) => l.id === lane) * rowH + rowH / 2;
  const x = (n) => left + (n - 1) * dx + dx / 2;
  lanes.forEach((l) => { add(svg, "line", { x1: left - 8, x2: W - 8, y1: y(l.id), y2: y(l.id), class: "lane" }); add(svg, "text", { x: 6, y: y(l.id) + 4, class: "lanelabel" }, l.name); });
  steps.forEach((s, i) => {
    if (i === 0) return;
    const p = steps[i - 1], hand = p.lane !== s.lane;
    add(svg, "path", { d: `M${x(p.n)} ${y(p.lane)} L${x(s.n)} ${y(s.lane)}`, class: hand ? "hand" : "run" });
  });
  steps.forEach((s) => {
    const g = add(svg, "g", { class: "tick", tabindex: "0", role: "button", "aria-label": `Step ${s.n}, ${laneName(s.lane)}: ${s.title}`, "data-n": s.n });
    add(g, "circle", { cx: x(s.n), cy: y(s.lane), r: 6 });
    add(g, "title", {}, `${s.n}. ${s.title}`);
    g.addEventListener("click", () => go(s.n - 1, true));
    g.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(s.n - 1, true); } });
  });
  $("swim").replaceChildren(svg);
}

// ---------- groups and steps ----------
function renderGroups() {
  const root = $("groups");
  for (const g of data.groups) {
    if (g.handoff) root.append(el("p", { class: "handoff", text: g.handoff }));
    const d = el("details", { class: "grp", "data-id": g.id },
      el("summary", {}, el("b", { text: g.title }), el("span", { class: "muted", text: `  ${g.summary}` })),
      el("ol", { class: "steps" }, g.steps.map((n) => {
        const s = data.steps[n - 1];
        return el("li", {}, el("button", { class: "step", type: "button", "data-i": n - 1, onclick: () => go(n - 1, true) }, el("span", { class: "n", text: n }), el("span", { class: "what", text: s.title })));
      })));
    root.append(d);
  }
}

function sentenceCost(s) {
  const bits = [];
  if (s.tokens) bits.push(`${s.tokens.in.toLocaleString("en-US")} tokens read, ${s.tokens.out.toLocaleString("en-US")} written`);
  if (s.latency_s != null) bits.push(`${s.latency_s.toFixed(1)} seconds when first recorded`);
  if (s.cost_usd != null) bits.push(s.cost_usd < 0.0001 ? "under $0.0001 at paid rates" : `about $${s.cost_usd.toFixed(4)} at paid rates`);
  return bits.length ? bits.join("; ") + (s.replayed ? ". Replayed from the recorded response, so nothing was spent now." : ".") : null;
}

function go(i, user) {
  at = Math.max(0, Math.min(data.steps.length - 1, i));
  const s = data.steps[at], g = data.groups.find((x) => x.id === s.group);
  document.querySelectorAll(".step").forEach((b) => (Number(b.dataset.i) === at ? b.setAttribute("aria-current", "step") : b.removeAttribute("aria-current")));
  document.querySelectorAll(".tick").forEach((t) => t.classList.toggle("active", Number(t.dataset.n) === s.n));
  const det = document.querySelector(`details.grp[data-id="${g.id}"]`);
  if (det && !det.open) det.open = true; // playing expands the group it enters
  const btn = document.querySelector(`.step[data-i="${at}"]`);
  if (btn && (timer || user)) { const r = btn.getBoundingClientRect(); if (r.top < 90 || r.bottom > window.innerHeight - 10) btn.scrollIntoView({ block: "center" }); }
  const rows = [el("h2", { text: `Step ${s.n} of ${data.steps.length}: ${s.title}` }), el("p", { class: "muted", text: `${laneName(s.lane)}${g.repair ? ", repair" : ""}` })];
  if (s.details.length) rows.push(...s.details.map((d) => el("p", { class: "out", text: d })));
  if (s.quote) rows.push(el("h3", { text: "The quote built from the filing" }), el("blockquote", { class: "filing" }, el("mark", { class: "hl", text: s.quote })));
  const c = sentenceCost(s);
  if (c) rows.push(el("h3", { text: "What it used" }), el("p", { text: c }));
  rows.push(el("p", { class: "small muted", text: `Recorded as event ${s.raw_step} of the trace file for this company.` }));
  $("detail").replaceChildren(...rows);
  $("totals").textContent = `So far: ${plural(s.total.calls, "model call")}, ${s.total.tokens.toLocaleString("en-US")} tokens, about $${s.total.cost_usd.toFixed(4)} at paid rates.`;
  $("back").disabled = at === 0; $("fwd").disabled = at === data.steps.length - 1;
  history.replaceState(null, "", `#${s.n}`);
}

function play(on) {
  clearInterval(timer); timer = null;
  $("play").setAttribute("aria-pressed", String(on));
  $("play").textContent = on ? "Pause" : "Play";
  if (on) {
    if (at >= data.steps.length - 1) go(0);
    const ms = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 1800 : 1000;
    timer = setInterval(() => { if (at >= data.steps.length - 1) play(false); else go(at + 1); }, ms);
  }
}

async function main() {
  footer(await manifest());
  if (!cik) throw new Error("No company was asked for. Open a replay from a company page.");
  const [trace, ex] = await Promise.all([getJSON(`data/results/${cik}.trace.json`), tryJSON(`data/results/${cik}.explain.json`)]);
  data = trace;
  const name = (ex && ex.name) || cik;
  document.title = `Agent run for ${name}`;
  $("title").textContent = `How the agents analysed ${name}`;
  $("crumbs").replaceChildren(el("a", { href: "index.html", text: "All rankings" }), " / ", el("a", { href: `company.html?cik=${cik}`, text: name }));
  $("lede").textContent = "This is a recorded run, replayed from files: no model is called on this page. The planner decides what to run, the scorers do the arithmetic, one qualitative agent per Buffett question reads the 10-K, the Explainer writes the plain-English lines, and the Critic, a second reviewer, re-checks everything against the filing. Step through to see each hand-off.";
  $("swimfig").hidden = false; $("bar").hidden = false; $("tr").hidden = false;
  swimlane(); renderGroups();
  $("back").onclick = () => go(at - 1, true); $("fwd").onclick = () => go(at + 1, true); $("play").onclick = () => play(!timer);
  document.addEventListener("keydown", (ev) => {
    if (ev.target.closest("input, select, textarea, summary, svg")) return;
    if (ev.key === "ArrowRight") { ev.preventDefault(); go(at + 1, true); }
    else if (ev.key === "ArrowLeft") { ev.preventDefault(); go(at - 1, true); }
  });
  const start = parseInt(location.hash.slice(1), 10);
  go(Number.isFinite(start) ? start - 1 : 0, false);
}
main().catch((e) => fail(e.message, "Replays exist only for companies with a full agent analysis."));
