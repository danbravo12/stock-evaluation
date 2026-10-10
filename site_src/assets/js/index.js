import { el, getJSON, manifest, footer, strip, mark, WORD } from "./common.js";

const $ = (id) => document.getElementById(id);
const SHOWCASE = ["KO", "JPM", "DUK"];

function companyHref(row) { return `company.html?cik=${row.cik}`; }
function rowCells(r, withRank) {
  const tds = [];
  if (withRank) tds.push(el("td", { class: "num", text: r.rank }));
  tds.push(el("td", { class: "co" }, el("a", { href: companyHref(r), text: r.name }), el("span", { class: "sym", text: r.symbol }),
    r.notes.length ? el("div", { class: "small muted", text: r.notes[0].split(":")[0].replace(/^Figures from predecessor registrant.*/, "Figures from predecessor registrant"), title: r.notes.join(" ") }) : null));
  tds.push(el("td", { text: r.gics_sector }));
  tds.push(el("td", { class: "num", text: `${r.met} of ${r.decided}` }));
  if (withRank) tds.push(el("td", { class: "num", text: r.percent_met == null ? "–" : `${r.percent_met.toFixed(0)}%` }));
  tds.push(el("td", { class: "num", text: r.data_gaps }));
  tds.push(el("td", {}, strip(r.labels)));
  if (withRank) tds.push(el("td", {}, r.has_full_analysis ? el("a", { href: companyHref(r) + "#analysis", text: "Yes, with agent analysis" }) : el("span", { class: "muted", text: "Scores only" })));
  return tds;
}

async function main() {
  const [data, m] = await Promise.all([getJSON("data/rankings.json"), manifest()]);
  footer(m);
  const cr = data.criteria_ranking, ranked = cr.ranked, insuf = cr.insufficient_data;
  const all = [...ranked, ...insuf];
  const full = all.filter((r) => r.has_full_analysis);
  const d = data.data_as_of;
  $("asof").textContent = `Data as of ${d.sec_fetched_from}${d.sec_fetched_to !== d.sec_fetched_from ? " to " + d.sec_fetched_to : ""} for SEC filings. Constituents list from ${d.constituents_snapshot}.`;
  $("coverage").textContent = `${all.length} companies scored on SEC filings. Full agent analysis, with quoted filing text and a replayable run, for ${full.length}: ${full.map((r) => r.symbol).join(", ")}.`;
  const show = [...SHOWCASE, ...full.map((r) => r.symbol)].filter((s, i, a) => a.indexOf(s) === i).map((s) => all.find((r) => r.symbol === s)).filter(Boolean);
  const sc = $("showcase");
  sc.append("Start with a full analysis: ");
  show.forEach((r, i) => { if (i) sc.append(i === show.length - 1 ? " and " : ", "); sc.append(el("a", { href: companyHref(r), text: `${r.name} (${r.symbol})` })); });
  sc.append(". Each score opens the SEC filing and the figures behind it; each judgement opens the quoted sentence from the annual report.");
  if (data.caveats.length) {
    const c = $("caveat"); c.hidden = false; c.className = "notebox";
    c.textContent = "Valuation criteria (G6 P/E, G7 P/E × P/B) are pending licensed price data. Until then they are data gaps for every company, so no one is scored on valuation.";
  }

  // sector filter
  const sectors = [...new Set(all.map((r) => r.gics_sector))].sort();
  for (const s of sectors) $("sector").append(el("option", { value: s, text: s }));

  const tbody = document.querySelector("#rank tbody");
  const rows = ranked.map((r) => ({ r, tr: el("tr", {}, rowCells(r, true)), name: r.name.toLowerCase(), sym: r.symbol.toLowerCase() }));
  tbody.append(...rows.map((x) => x.tr));
  const apply = () => {
    const q = $("q").value.trim().toLowerCase(), sec = $("sector").value, sort = $("sort").value;
    const order = [...rows].sort((a, b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "pct" ? (b.r.percent_met - a.r.percent_met) || (a.r.rank - b.r.rank) : a.r.rank - b.r.rank);
    let shown = 0;
    for (const x of order) {
      const ok = (!q || x.name.includes(q) || x.sym.includes(q)) && (!sec || x.r.gics_sector === sec);
      x.tr.hidden = !ok; if (ok) shown++;
      tbody.append(x.tr);
    }
    $("count").textContent = shown === rows.length ? `${shown} companies ranked` : `${shown} of ${rows.length} companies shown`;
    if (shown === 0) $("count").textContent = "No company matches. Clear the search or choose all sectors.";
  };
  for (const id of ["q", "sector", "sort"]) $(id).addEventListener("input", apply);
  apply();

  // legend
  $("legend").replaceChildren(...["pass", "partial_pass", "fail", "data_gap", "not_applicable"].map((l) => el("li", {}, mark(l, { small: true }), " ", WORD[l])));
  $("scorenote").textContent = "How companies are ordered: for each company, the score is the lower end of a 95% confidence range for the share of decided tests it meets (the Wilson score interval). A test is decided when it is a pass, partial pass or fail; data gaps and tests that do not apply are left out. A company with 6 of 6 therefore ranks below one with 9 of 9, because there is less evidence behind it. Ties go to more tests met, then fewer data gaps, then the symbol. The G4 dividend test can only ever be a partial pass, because SEC data covers about 15 years, not the 20 Graham asked for. Notes under a company name explain how its sector affects the tests.";

  // insufficient data
  $("insuf-sum").textContent = `${insuf.length} companies with fewer than ${cr.minimum_decided} decided tests`;
  $("insuf-why").textContent = "These are not ranked. Most were listed recently, so SEC filings give fewer than ten years of figures, or they do not report an item a test needs.";
  document.querySelector("#insuf tbody").append(...insuf.map((r) => el("tr", {}, rowCells(r, false))));

  // excluded
  $("excluded").hidden = data.excluded.length === 0;
  $("excl-sum").textContent = `${data.excluded.length} companies left out`;
  $("excl-list").append(...data.excluded.map((e) => el("li", {}, el("b", { text: `${e.name} (${e.symbol})` }), `: ${e.reason}`)));

  const a = data.ranking_by_analysts;
  $("analysts-text").textContent = `Not available yet. The analyst ranking needs a data licence that has not been granted (${a.reason}). Nothing is shown in its place, and this site does not compare the two rankings.`;
}
main().catch((e) => { document.querySelector("main").replaceChildren(el("h1", { text: "The rankings could not load" }), el("p", { text: `${e.message}. If you opened this file directly from disk, serve the folder instead: run "python -m engine.cli publish --serve".` })); });
