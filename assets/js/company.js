import { el, getJSON, tryJSON, fail, manifest, footer, mark, status, effectiveLabel, WORD, CRITERIA, NAMES, QUAL, usd, perShare, pct, figures, plainReason, secLink, secOk, measureName } from "./common.js";

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const FLAG_WORD = { derived: "derived", restated: "restated", split_adjusted: "split-adjusted" };

let model; // { row, criteria, qual, result, passages }
let selected = null;

function inputsOf(c, card) {
  if (c.inputs) return c.inputs;
  const by = Object.fromEntries((card.inputs || []).map((i) => [`${i.measure}:${i.fiscal_year}`, i]));
  return (c.input_keys || []).map((k) => by[k]).filter(Boolean);
}

async function load() {
  const rk = await getJSON("data/rankings.json");
  const all = [...rk.criteria_ranking.ranked, ...rk.criteria_ranking.insufficient_data];
  let cik = params.get("cik");
  const t = params.get("t");
  if (!cik && t) { const hit = [...all, ...rk.excluded].find((r) => r.symbol.toLowerCase() === t.toLowerCase()); cik = hit && hit.cik; }
  if (!cik) throw new Error("No company was asked for. Open one from the rankings.");
  const row = all.find((r) => r.cik === cik);
  const excluded = rk.excluded.find((r) => r.cik === cik);
  if (!row) return { cik, excluded };
  const score = await tryJSON(`data/scores/${cik}.json`);
  const result = row.has_full_analysis ? await tryJSON(`data/results/${cik}.json`) : null;
  const passages = result ? await tryJSON(`data/results/${cik}.passages.json`) : null;
  const explain = result ? await tryJSON(`data/results/${cik}.explain.json`) : null;
  let criteria;
  if (result && result.scorecard) criteria = result.scorecard.criteria.map((c) => ({ ...c, inputs: inputsOf(c, result.scorecard) }));
  else if (score) criteria = score.score.results.map((c) => ({ ...c }));
  else throw new Error("No score file for this company.");
  criteria.forEach((c) => { c.label = effectiveLabel(c); });
  return { cik, row, score, result, passages, explain, criteria, qual: result ? result.qualitative : [] };
}

// ---------- the list of tests ----------
function lineOf(c, cls) {
  if (c.label === "data_gap" || c.label === "pending" || c.label === "not_applicable") return plainReason(c, cls);
  if (c.explanation && c.explanation.text) return c.explanation.text;
  const figs = figures(c).filter(([k]) => !/^Years (on record|without|with)/.test(k)).slice(0, 3).map(([k, v]) => `${k.charAt(0).toUpperCase() + k.slice(1).toLowerCase()} ${v}`);
  return (plainReason(c, cls) || `Test: ${c.threshold}.`) + (figs.length && !plainReason(c, cls) ? ` ${figs.join("; ")}.` : "");
}

function critRow(id, name, label, line, warn, qual) {
  const b = el("button", { class: "crit", "data-q": qual ? "1" : false, type: "button", "aria-expanded": "false", "aria-controls": "pane", "data-id": id, onclick: () => select(id, true) },
    el("span", {}, el("span", { class: "t" }, id.length <= 3 ? el("span", { class: "id", text: id }) : null, name), el("br"), status(label)),
    el("span", { class: "line", text: line }),
    warn ? el("span", { class: "warn", text: warn }) : null);
  return el("li", { id: `row-${id}` }, b);
}

function renderList() {
  const ul = $("crits");
  if (model.result) ul.before(el("p", { class: "small muted", text: "Each score and judgement below was re-checked by the Critic, a second reviewer that is partly code and partly a model." }));
  const cls = model.row.sector_class, status_ = model.result ? model.result.critic.final : {};
  const byId = Object.fromEntries(model.criteria.map((c) => [c.id, c]));
  const group = (title, ids) => {
    ul.append(el("li", {}, el("h3", { text: title })));
    for (const id of ids) {
      const c = byId[id]; if (!c) continue;
      const warn = status_[id] === "warning" ? "The Critic still objects to this explanation. Open it to see why." : null;
      ul.append(critRow(id, `${NAMES[id] || c.name}`, c.label, lineOf(c, cls), warn));
    }
  };
  group("Graham's seven tests", CRITERIA.slice(0, 7));
  group("Buffett's four numeric tests", CRITERIA.slice(7));
  if (model.qual.length) {
    ul.append(el("li", { id: "analysis" }, el("h3", { text: "Buffett's four judgement tests, read from the annual report by the agent" })));
    for (const q of model.qual) {
      const f = q.finding, st = q.critic_status;
      ul.append(critRow(f.criterion, QUAL[f.criterion] || f.criterion, f.verdict, f.rationale, st === "warning" ? "The Critic still objects to this rationale. Open it to see why." : null, true));
    }
  }
}

// ---------- the evidence pane ----------
function chart(c) {
  const by = c.by_year || {};
  const ys = Object.keys(by).sort();
  if (!ys.length) return null;
  const val = (y) => (typeof by[y] === "object" && by[y] !== null ? by[y].value : by[y]);
  const nums = ys.map(val);
  const fmt = c.id === "B1" || c.id === "B3" ? (v) => pct(v) : c.id === "G4" ? perShare : usd;
  const W = 520, H = 150, pl = 8, pr = 8, pt = 14, pb = 26, n = ys.length, bw = (W - pl - pr) / n;
  const real = nums.filter((v) => v != null);
  const max = Math.max(0, ...real), min = Math.min(0, ...real), span = max - min || 1;
  const y0 = pt + ((max - 0) / span) * (H - pt - pb);
  const NS = "http://www.w3.org/2000/svg";
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", `0 0 ${W} ${H}`); s.setAttribute("class", "chart"); s.setAttribute("role", "img");
  s.setAttribute("aria-label", `${c.name} by year: ` + ys.map((y, i) => `${y} ${nums[i] == null ? "no data" : fmt(nums[i])}`).join(", "));
  const add = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text != null) e.textContent = text; s.append(e); return e; };
  add("line", { x1: pl, x2: W - pr, y1: y0, y2: y0, stroke: "var(--rule)" });
  ys.forEach((y, i) => {
    const v = nums[i], x = pl + i * bw + bw * 0.15, w = bw * 0.7;
    if (v == null) { add("rect", { x, y: y0 - 10, width: w, height: 10, class: "bar-un" }); }
    else { const h = (Math.abs(v) / span) * (H - pt - pb); add("rect", { x, y: v >= 0 ? y0 - h : y0, width: w, height: Math.max(h, 1), class: v >= 0 ? "bar-pos" : "bar-neg" }); }
    if (n <= 12 || i % 2 === 0) add("text", { x: x + w / 2, y: H - 8, "text-anchor": "middle" }, String(y).slice(-n > 12 ? 2 : 4));
  });
  add("text", { x: pl, y: 10 }, `highest ${fmt(max)}`);
  add("text", { x: W - pr, y: 10, "text-anchor": "end" }, min < 0 ? `lowest ${fmt(min)}` : "");
  return s;
}

function inputsTable(list) {
  if (!list.length) return null;
  const t = el("table", { class: "inputs" }, el("thead", {}, el("tr", {}, ["Figure", "Year", "Value", "Filing tag", "Notes", "Source"].map((h) => el("th", { scope: "col", text: h })))));
  const b = el("tbody");
  for (const i of list) {
    const v = i.unit === "USD" ? usd(i.value) : i.unit === "USD/shares" ? perShare(i.value) : Number(i.value).toLocaleString("en-US");
    b.append(el("tr", {}, el("td", { text: measureName(i.measure) }), el("td", { text: i.fiscal_year }), el("td", { class: "num", text: v }), el("td", { text: i.concept }),
      el("td", {}, (i.flags || []).map((f) => el("span", { class: "flag", text: FLAG_WORD[f] || f }))), el("td", {}, secLink(i.source_url, "SEC filing"))));
  }
  t.append(b);
  return el("div", { class: "tablewrap", tabindex: "0", role: "region", "aria-label": "Inputs" }, t);
}

function checksFor(id) {
  const n = model.explain && model.explain.critic[id];
  if (!n) return null;
  return el("div", {}, el("h3", { text: "What the Critic found" }), el("p", {}, mark(n.objected ? "partial_pass" : "pass"), " ", n.status + "."),
    ...n.sentences.map((t) => el("p", { text: t })), n.ran ? el("p", { class: "small muted", text: n.ran }) : null);
}

function numericPane(c) {
  const pane = [];
  pane.push(el("h2", {}, `${c.id} ${NAMES[c.id] || c.name}`), el("p", {}, status(c.label)));
  const line = lineOf(c, model.row.sector_class);
  if (c.explanation || c.label === "data_gap" || c.label === "pending" || c.label === "not_applicable") pane.push(el("p", { text: line }));
  pane.push(el("p", { class: "small muted", text: `The test: ${c.threshold}.` + (c.year_label ? ` Record: ${c.year_label}.` : "") }));
  const figs = figures(c);
  if (figs.length) pane.push(el("h3", { text: "What the filings show" }), el("dl", { class: "fig" }, figs.flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])));
  const ch = chart(c);
  if (ch) pane.push(el("h3", { text: { G3: "Net income by year", G4: "Dividends per share by year", B1: "Return on average equity by year", B3: "Operating margin by year", B4: "Owner earnings by year" }[c.id] || "By year" }), ch);
  const ins = inputsTable(c.inputs || []);
  if (ins) pane.push(el("h3", { text: "Every input, with its filing" }), ins);
  else if (!["data_gap", "pending", "not_applicable"].includes(c.label)) pane.push(el("p", { class: "muted", text: "No filing figures are attached to this result." }));
  if (c.id === "G6" || c.id === "G7") pane.push(el("p", { class: "muted", text: "This test compares a share price with earnings and assets. Prices come from a licensed data feed that is not connected yet." }));
  const cc = checksFor(c.id); if (cc) pane.push(cc);
  return pane;
}

function passageView(cit) {
  const p = model.passages && model.passages[cit.passage_id];
  const q = el("blockquote", { class: "filing" });
  if (p) {
    const a = cit.char_start - p.char_start, b = cit.char_end - p.char_start;
    if (a >= 0 && b <= p.text.length && p.text.slice(a, b) === cit.quote) {
      q.append(el("span", { class: "ctx", text: (a > 400 ? "… " : "") + p.text.slice(Math.max(0, a - 400), a) }), el("mark", { class: "hl", text: cit.quote }), el("span", { class: "ctx", text: p.text.slice(b, b + 400) + (p.text.length - b > 400 ? " …" : "") }));
      return q;
    }
  }
  q.append(el("mark", { class: "hl", text: cit.quote }));
  return q;
}

function qualPane(q) {
  const f = q.finding, pane = [];
  pane.push(el("h2", { text: QUAL[f.criterion] || f.criterion }), el("p", {}, status(f.verdict)));
  pane.push(el("p", { text: f.rationale }));
  if (f.stop_reason && f.stop_reason !== "submitted") pane.push(el("p", { class: "muted", text: `The agent stopped early (${f.stop_reason.replaceAll("_", " ")}), so this is not a judgement about the company.` }));
  if (!f.citations.length) pane.push(el("p", { class: "muted", text: "No sentence in the annual report is cited for this verdict." }));
  pane.push(el("h3", { text: f.citations.length ? "The sentences it relies on, in the annual report" : "Evidence" }));
  f.citations.forEach((c) => {
    pane.push(passageView(c));
    const filing = model.result.data.filing;
    pane.push(el("p", { class: "src" }, `Item ${c.item}, filing ${c.accession}. `, secLink(filing.url, "Open the 10-K"), "."),
      el("p", { class: "src offs", text: `Characters ${c.char_start} to ${c.char_end} of the filing's normalised text.` }));
  });
  const qn = model.explain && model.explain.qualitative[f.criterion];
  if (qn) pane.push(el("p", { class: "small muted", text: qn }));
  const st = q.critic_status;
  const cc = checksFor(f.criterion);
  if (cc) pane.push(cc);
  return pane;
}

function select(id, user) {
  selected = id;
  document.querySelectorAll(".crit").forEach((b) => b.setAttribute("aria-expanded", String(b.dataset.id === id)));
  const q = model.qual.find((x) => x.finding.criterion === id);
  const c = model.criteria.find((x) => x.id === id);
  const pane = $("pane");
  const fresh = pane.cloneNode(false); // re-create so the opening animation plays once per selection
  fresh.append(...(q ? qualPane(q) : c ? numericPane(c) : [el("p", { class: "empty", text: "Select a test to see the evidence behind it." })]));
  pane.replaceWith(fresh);
  place();
  if (user) history.replaceState(null, "", `#${id}`);
}

const narrow = window.matchMedia("(max-width: 900px)");
function place() { // on narrow screens the pane opens inline under the selected row
  const pane = $("pane"), row = selected && $(`row-${selected}`);
  if (narrow.matches && row) row.after(pane); else $("panehome").append(pane);
  if (narrow.matches && row && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) pane.scrollIntoView({ block: "nearest" });
}
narrow.addEventListener("change", place);
window.addEventListener("hashchange", () => { const id = location.hash.slice(1); if (id && (model.criteria.some((c) => c.id === id) || model.qual.some((x) => x.finding.criterion === id))) select(id, false); });

// ---------- page ----------
function costLine() {
  const r = model.result;
  if (!r) return el("div", { class: "cost" },
    el("p", { text: "Full agent analysis has not been run for this company. These scores come from the SEC's structured data alone." }),
    el("p", { text: "A full analysis would add a plain-English explanation of each score, four judgements on Buffett's qualitative questions (is the business understandable, does it have a lasting advantage, is management candid, is capital used sensibly), each backed by a quoted sentence from the annual report, a Critic (a second reviewer) that checks them, and a replayable record of every step the agents took." }));
  return el("div", { class: "cost", id: "cost" },
    el("p", { text: model.explain ? model.explain.cost : "" }),
    el("p", {}, el("a", { href: `trace.html?cik=${model.cik}`, text: "Replay the agent run step by step" }), ". Filing used: ", secLink(r.data.filing.url, `Form 10-K filed ${r.data.filing.filing_date}`), "."));
}

async function main() {
  const m = await manifest(); footer(m);
  model = await load();
  if (model.excluded) {
    $("head").replaceChildren(el("h1", { text: model.excluded.name }), el("p", { class: "lede", text: model.excluded.reason }), el("p", { text: "It is left out of the ranking until it files an annual report. This page will change after the next data refresh." }));
    return;
  }
  const r = model.row;
  document.title = `${r.name} (${r.symbol}) analysis`;
  const classWord = { bank: "bank rules (no current assets or operating income)", insurer: "insurer rules (no current assets or operating income)", utility: "utility variant of the debt test", reit: "standard rules with a REIT note", other: "standard" }[r.sector_class] || r.sector_class;
  $("head").replaceChildren(el("h1", { text: `${r.name} (${r.symbol})` }),
    el("ul", { class: "facts" },
      el("li", {}, el("b", { text: "Sector " }), r.gics_sector), el("li", {}, el("b", { text: "Rules applied " }), classWord),
      el("li", {}, el("b", { text: "Latest fiscal year " }), String(r.as_of_fiscal_year)),
      el("li", {}, el("b", { text: "Tests met " }), `${r.met} of ${r.decided} decided`), el("li", {}, el("b", { text: "Rank " }), r.rank ? `${r.rank}` : "not ranked (too few decided tests)")),
    ...r.notes.map((n) => el("p", { class: "notebox", text: n })),
    r.caveats.length ? el("p", { class: "notebox", text: "Valuation criteria (G6 P/E, G7 P/E × P/B) are pending licensed price data." }) : null,
    el("p", { class: "links" }, secLink(`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${model.cik}&type=10-K`, "All annual reports for this company on the SEC site"), model.result ? el("a", { href: `trace.html?cik=${model.cik}`, text: "Replay the agent run" }) : null));
  renderList();
  $("cols").hidden = false;
  $("foot").replaceChildren(costLine());
  const id = location.hash.slice(1);
  const first = model.criteria.find((c) => c.id === id) || model.qual.find((x) => x.finding.criterion === id) ? id : null;
  if (first) select(first, false);
}
main().catch((e) => fail(e.message, "Open a company from the rankings page, or check that the data folder was published."));
