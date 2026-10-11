// Shared helpers for every page. Plain ES module, no dependencies. All URLs are relative so the site works from a subpath.

export function el(tag, attrs, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return n;
}

export async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

export async function tryJSON(path) {
  try { return await getJSON(path); } catch { return null; }
}

export function fail(message, hint) {
  const main = document.querySelector("main");
  main.replaceChildren(el("h1", { text: "This page could not load" }), el("p", { text: message }), hint ? el("p", { text: hint }) : null,
    el("p", {}, el("a", { href: "index.html", text: "Back to the rankings" })));
}

// ---------- status marks: a shape and a word, never colour alone ----------
const NS = "http://www.w3.org/2000/svg";
const KIND = { pending: "pending", pass: "pass", partial_pass: "partial", fail: "fail", data_gap: "gap", not_applicable: "na", not_meaningful: "nm",
  "evidence found": "pass", "evidence weak": "partial", "insufficient evidence": "gap", "not assessed": "na" };
export const WORD = { pending: "Pending", pass: "Pass", partial_pass: "Partial pass", fail: "Fail", data_gap: "Data gap", not_applicable: "Not applicable", not_meaningful: "Not meaningful",
  "evidence found": "Evidence found", "evidence weak": "Evidence weak", "insufficient evidence": "Insufficient evidence", "not assessed": "Not assessed" };

function defs() {
  if (document.getElementById("mark-defs")) return;
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("id", "mark-defs"); svg.setAttribute("width", "0"); svg.setAttribute("height", "0"); svg.setAttribute("aria-hidden", "true");
  svg.style.position = "absolute";
  svg.innerHTML = `
    <pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" fill="none"/><line x1="0" y1="0" x2="0" y2="4" stroke="var(--muted)" stroke-width="1.6"/></pattern>
    <symbol id="m-pass" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="var(--pass)"/></symbol>
    <symbol id="m-partial" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="var(--pass)" stroke-width="1.6"/><path d="M8 1.5a6.5 6.5 0 0 0 0 13z" fill="var(--pass)"/></symbol>
    <symbol id="m-fail" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="var(--fail)" stroke-width="1.6"/><path d="M5.4 5.4l5.2 5.2M10.6 5.4l-5.2 5.2" stroke="var(--fail)" stroke-width="1.6" stroke-linecap="round"/></symbol>
    <symbol id="m-gap" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="url(#hatch)" stroke="var(--muted)" stroke-width="1.2"/></symbol>
    <symbol id="m-na" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="var(--muted)" stroke-width="1.4" stroke-dasharray="2.6 2.2"/></symbol>
    <symbol id="m-pending" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="var(--muted)" stroke-width="1.4"/><circle cx="8" cy="8" r="2.4" fill="var(--muted)"/></symbol>
    <symbol id="m-nm" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="var(--muted)" stroke-width="1.4" stroke-dasharray="2.6 2.2"/><path d="M5 8h6" stroke="var(--muted)" stroke-width="1.4" stroke-linecap="round"/></symbol>`;
  document.body.prepend(svg);
}

export function mark(label, { small = false, named = false } = {}) {
  defs();
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("class", "mark" + (small ? " sm" : ""));
  s.setAttribute("viewBox", "0 0 16 16");
  if (named) { s.setAttribute("role", "img"); s.setAttribute("aria-label", WORD[label] || label); } else s.setAttribute("aria-hidden", "true");
  const u = document.createElementNS(NS, "use");
  u.setAttribute("href", "#m-" + (KIND[label] || "na"));
  s.append(u);
  return s;
}

export function status(label) {
  return el("span", { class: "status" }, mark(label), el("span", { text: WORD[label] || label }));
}

export const CRITERIA = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "B1", "B2", "B3", "B4"];
export const NAMES = { G1: "Size", G2: "Financial strength", G3: "Earnings stability", G4: "Dividend record", G5: "Earnings growth", G6: "Moderate P/E", G7: "Price vs assets",
  B1: "Return on equity", B2: "Conservative debt", B3: "Stable margins", B4: "Owner earnings" };
export const QUAL = { understandable_business: "Understandable business", durable_competitive_advantage: "Durable competitive advantage", candid_management: "Candid management",
  rational_capital_allocation: "Rational capital allocation" };

export function strip(labels) {
  const parts = [], spans = [];
  CRITERIA.forEach((c, i) => {
    if (i === 7) spans.push(el("span", { class: "gap" }));
    const l = labels[c] || "data_gap";
    parts.push(`${c} ${NAMES[c].toLowerCase()}: ${WORD[l].toLowerCase()}`);
    const m = mark(l, { small: true });
    m.append(Object.assign(document.createElementNS(NS, "title"), { textContent: `${c} ${NAMES[c]}: ${WORD[l]}` }));
    spans.push(m);
  });
  return el("span", { class: "strip", role: "img", "aria-label": parts.join("; ") }, spans);
}

// ---------- formatting ----------
export function usd(v) {
  if (v == null) return "–";
  const a = Math.abs(v), sign = v < 0 ? "-" : "";
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(2)}B`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(1)}M`;
  return `${sign}$${a.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}
export const perShare = (v) => (v == null ? "–" : `$${v.toFixed(2)}`);
export const pct = (v, d = 1) => (v == null ? "–" : `${(v * 100).toFixed(d)}%`);
export const ratio = (v) => (v == null ? "–" : v.toFixed(2));
export const years = (ys) => (ys && ys.length ? ys.join(", ") : "none");
export const dateOf = (s) => s || "unknown";

const USD_KEYS = new Set(["revenue", "long_term_debt", "net_current_assets", "stockholders_equity", "avg_net_income_3y", "max_debt", "avg_first_3y", "avg_last_3y"]);
const FIG = {
  revenue: ["Revenue", usd], current_ratio: ["Current ratio", ratio], long_term_debt: ["Long-term debt", usd], net_current_assets: ["Net current assets", usd],
  stockholders_equity: ["Shareholders' equity", usd], debt_to_equity: ["Debt to equity", ratio], years_on_record: ["Years on record", String], loss_years: ["Loss years", years],
  unpaid_years: ["Years without a dividend", years], unknown_years: ["Years with no dividend data", years], avg_eps_start: ["Average earnings per share, first 3 years", perShare],
  avg_eps_end: ["Average earnings per share, last 3 years", perShare], ratio: ["Ratio", ratio], years_at_or_above_15pct: ["Years with return on equity of 15% or more", String],
  avg_net_income_3y: ["Average net income, last 3 years", usd], max_debt: ["Debt ceiling (4 × average net income)", usd], avg_margin_10y: ["Average operating margin, 10 years", (v) => pct(v)],
  avg_margin_3y: ["Average operating margin, last 3 years", (v) => pct(v)], avg_first_3y: ["Average owner earnings, first 3 years", usd], avg_last_3y: ["Average owner earnings, last 3 years", usd],
  years_positive: ["Years with positive owner earnings", String], years_with_depreciation_only: ["Years where only depreciation was reported (no amortisation)", years],
};
const EMPTY = { loss_years: "No loss years.", unpaid_years: "No years without a dividend.", unknown_years: "No years with missing dividend data.", years_with_depreciation_only: "No years where only depreciation was reported." };
// Rows for the evidence pane: [label, value] for a figure, [sentence] for a list that is empty (never a label followed by "none").
export function figures(c) {
  const out = [];
  for (const [k, v] of Object.entries(c.figures || {})) {
    if (Array.isArray(v) && v.length === 0) { out.push([EMPTY[k] || `No ${k.replaceAll("_", " ")}.`]); continue; }
    const [label, f] = FIG[k] || [k.replaceAll("_", " "), (x) => String(x)];
    out.push([label, v == null ? "not available" : f(v)]);
  }
  return out;
}

// One line of key figures for a row without an agent explanation.
export function figureSummary(c, limit = 3) {
  return figures(c).filter((r) => r.length === 1 || !/^Years (on record|without|with)/.test(r[0])).slice(0, limit)
    .map((r) => (r.length === 1 ? r[0].replace(/\.$/, "") : `${r[0].charAt(0).toUpperCase() + r[0].slice(1).toLowerCase()} ${r[1]}`)).join("; ");
}

const MEASURE = { operating_income: "operating income", revenue: "revenue", net_income: "net income", eps_diluted: "diluted earnings per share", current_assets: "current assets",
  current_liabilities: "current liabilities", long_term_debt: "long-term debt", stockholders_equity: "shareholders' equity", depreciation_amortization: "depreciation and amortisation",
  capex: "capital spending", dividends_per_share: "dividends per share", dividends_paid: "dividends paid", diluted_shares: "diluted share count" };
export const measureName = (m) => MEASURE[m] || m.replaceAll("_", " ");
const yearsText = (ys) => (ys.length > 4 ? `${ys.length} years (${ys[0]} to ${ys[ys.length - 1]})` : ys.join(", "));

// The scorers' reasons in plain words: what the SEC filings do or do not say.
export function effectiveLabel(c) { // a valuation test that only waits for a price is pending, not a data gap
  return c.label === "data_gap" && /^price not available/i.test(c.reason || "") ? "pending" : c.label;
}

export function plainReason(c, sectorClass) {
  const r = (c.reason || "").trim();
  if (c.label === "not_applicable") {
    const who = sectorClass === "insurer" ? "insurers" : "banks";
    if (c.id === "G2" || c.id === "B2") return `Not applicable to ${who}: their balance sheets are not split into current and long-term items.`;
    return `Not applicable to ${who}: they report no operating income or capital spending in the usual sense.`;
  }
  if (c.label === "data_gap" || c.label === "pending") {
    if (/^price not available/i.test(r)) return "Pending licensed price data. This test compares the share price with earnings or assets.";
    const dm = r.match(/^dividend data missing for (.+)$/);
    if (dm) return `Dividend data is missing for ${dm[1]} in the SEC filings, so the record cannot be judged.`;
    const nm = r.match(/^net_income missing inside the record: \[(.*)\]$/);
    if (nm) return `Net income is missing for ${nm[1].split(",").length} year(s) inside the record (${nm[1]}).`;
    const nr = r.match(/^no (\w+) for (\d{4})$/);
    if (nr) return `SEC filings don't report ${measureName(nr[1])} for ${nr[2]}.`;
    const miss = [...r.matchAll(/(\w+) \[([^\]]*)\]/g)];
    if (r.startsWith("missing:") && miss.length) {
      return "Data gap: SEC filings don't report " + miss.map(([, m, ys]) => `${measureName(m)}${ys ? " for " + yearsText(ys.split(",").map((y) => y.trim())) : ""}`).join(" or ") + " for this company.";
    }
    return r ? r[0].toUpperCase() + r.slice(1) + "." : "The SEC filings do not give the figures this test needs.";
  }
  if (r) return r[0].toUpperCase() + r.slice(1) + (/[.)]$/.test(r) ? "" : ".");
  return "";
}

export function secOk(url) { return typeof url === "string" && /^https:\/\/([a-z]+\.)?sec\.gov\//.test(url); }
export function secLink(url, text) { return secOk(url) ? el("a", { href: url, rel: "noopener", text }) : el("span", { text }); }

export async function manifest() { return tryJSON("data/manifest.json"); }

export function footer(m) {
  const f = document.querySelector("footer.site .wrap");
  if (!f || !m) return;
  f.replaceChildren(
    el("p", { text: `Data as of ${m.data_as_of.sec_fetched_from}${m.data_as_of.sec_fetched_to !== m.data_as_of.sec_fetched_from ? " to " + m.data_as_of.sec_fetched_to : ""} for SEC filings; constituents list from ${m.data_as_of.constituents_snapshot}.` }),
    ...m.attribution.map((a) => el("p", { text: a })),
    m.repo_url ? el("p", {}, el("a", { href: m.repo_url, rel: "noopener", text: "Code and recorded data on GitHub" })) : null,
    el("p", { text: `Built from commit ${m.build_commit || "unknown"}. Research tool, not financial advice.` }));
}
