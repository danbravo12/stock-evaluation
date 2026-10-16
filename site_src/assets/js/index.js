import { el, getJSON, tryJSON, manifest, footer, strip, mark, WORD } from "./common.js";

const $ = (id) => document.getElementById(id);
const date = (d) => el("span", { class: "nowrap", text: d });

function companyHref(row) { return `company.html?cik=${row.cik}`; }
function rowCells(r, withRank) {
  const tds = [];
  if (withRank) tds.push(el("td", { class: "num", text: r.rank }));
  tds.push(el("td", { class: "co" }, el("a", { href: companyHref(r), text: r.name }), el("span", { class: "sym", text: r.symbol }),
    r.notes.length ? el("div", { class: "small muted", text: r.notes[0].split(":")[0].replace(/^Figures from predecessor registrant.*/, "Figures from predecessor registrant"), title: r.notes.join(" ") }) : null));
  tds.push(el("td", { class: "sector", text: r.gics_sector }));
  tds.push(el("td", { class: "num", text: `${r.met} of ${r.decided}` }));
  if (withRank) tds.push(el("td", { class: "num", text: r.percent_met == null ? "–" : `${r.percent_met.toFixed(0)}%` }));
  tds.push(el("td", { class: "num", text: r.data_gaps }));
  tds.push(el("td", {}, strip(r.labels)));
  if (withRank) tds.push(el("td", {}, r.has_full_analysis ? el("a", { href: companyHref(r) + "#analysis", text: "Yes, with agent analysis" }) : el("span", { class: "muted", text: "Scores only" })));
  return tds;
}

function fill(tbody, list) {
  const rows = list.map((r) => ({ r, tr: el("tr", {}, rowCells(r, true)), name: r.name.toLowerCase(), sym: r.symbol.toLowerCase() }));
  tbody.append(...rows.map((x) => x.tr));
  return rows;
}

async function main() {
  const [data, m] = await Promise.all([getJSON("data/rankings.json"), manifest()]);
  footer(m);
  const cr = data.criteria_ranking, fin = cr.ranked_financials, insuf = cr.insufficient_data;
  const all = [...cr.ranked, ...fin, ...insuf];
  const full = all.filter((r) => r.has_full_analysis);
  const d = data.data_as_of;
  const asof = $("asof");
  asof.replaceChildren(...["Data as of ", date(d.sec_fetched_from), ...(d.sec_fetched_to !== d.sec_fetched_from ? [" to ", date(d.sec_fetched_to)] : []),
    `. ${all.length} companies scored on SEC filings; full agent analysis, with quoted filing text and a replayable run, for ${full.length}, listed in the showcase below.`]);
  const sc = await tryJSON("data/showcase.json");
  if (sc && sc.groups.length) {
    $("showcase").hidden = false;
    $("show-sum").textContent = `Showcase: ${sc.groups.reduce((n, g) => n + g.items.length, 0)} companies with a full agent analysis`;
    $("show-groups").replaceChildren(...sc.groups.flatMap((g) => [el("h2", { class: "grp", text: g.title }),
      el("ul", { class: "showlist" }, g.items.map((i) => el("li", {}, el("a", { href: `company.html?cik=${i.cik}`, text: `${i.name} (${i.symbol})` }), i.tag ? el("span", { class: "muted", text: `  ${i.tag}` }) : null,
        el("br"), i.why, i.rank ? el("span", { class: "muted", text: ` Rank ${i.rank}${i.rank_group === "financials" ? " among banks and insurers" : ""}.` }) : null)))]));
  }
  if (data.caveats.length) {
    const c = $("caveat"); c.hidden = false;
    c.textContent = "Valuation tests (G6 P/E, G7 P/E × P/B) are pending licensed price data. They are not counted as gaps or as decided tests.";
  }

  const sectors = [...new Set(all.map((r) => r.gics_sector))].sort();
  for (const s of sectors) $("sector").append(el("option", { value: s, text: s }));

  const groups = [{ rows: fill(document.querySelector("#rank tbody"), cr.ranked), label: "ranked" }];
  if (fin.length) {
    $("fin-section").hidden = false;
    $("fin-why").textContent = `Banks and insurers do not report current assets, operating income or capital spending in the usual way, so four tests do not apply to them. They are ranked here by the same score, from ${cr.financials_minimum_decided} decided tests, and are not compared with the companies above.`;
    groups.push({ rows: fill(document.querySelector("#fin tbody"), fin), label: "banks and insurers" });
  }
  const apply = () => {
    const q = $("q").value.trim().toLowerCase(), sec = $("sector").value, sort = $("sort").value;
    let shown = 0, total = 0;
    for (const g of groups) {
      const body = g.rows[0].tr.parentElement;
      const order = [...g.rows].sort((a, b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "pct" ? (b.r.percent_met - a.r.percent_met) || (a.r.rank - b.r.rank) : a.r.rank - b.r.rank);
      for (const x of order) {
        const ok = (!q || x.name.includes(q) || x.sym.includes(q)) && (!sec || x.r.gics_sector === sec);
        x.tr.hidden = !ok; if (ok) shown++;
        body.append(x.tr);
      }
      total += g.rows.length;
    }
    $("count").textContent = shown === total ? `${shown} companies ranked` : shown === 0 ? "No company matches. Clear the search or choose all sectors." : `${shown} of ${total} ranked companies shown`;
  };
  for (const id of ["q", "sector", "sort"]) $(id).addEventListener("input", apply);
  apply();

  const key = [["pass", "Pass"], ["partial_pass", "Partial pass (a test that can only be met in part)"], ["fail", "Fail"], ["data_gap", "Data gap (the filings do not give the figures)"],
    ["not_applicable", "Not applicable to this kind of company"], ["pending", "Pending: waiting for licensed price data, not counted as a gap"]];
  $("legend").replaceChildren(...key.map(([l, t]) => el("li", {}, mark(l, { small: true }), " ", t)));
  $("scorenote").append("The order is explained in ", el("a", { href: "how-it-works.html#ranking", text: "how companies are ranked" }), ".");

  $("insuf-sum").textContent = `${insuf.length} companies with too few decided tests to rank`;
  $("insuf-why").textContent = `A company needs ${cr.minimum_decided} decided tests to enter the main ranking (${cr.financials_minimum_decided} for banks and insurers). These have fewer: most were listed recently, so SEC filings give under ten years of figures, or they do not report an item a test needs. They are shown with their marks and are not ranked.`;
  document.querySelector("#insuf tbody").append(...insuf.map((r) => el("tr", {}, rowCells(r, false))));

  $("excluded").hidden = data.excluded.length === 0;
  $("excl-sum").textContent = `${data.excluded.length} companies left out`;
  $("excl-list").append(...data.excluded.map((e) => el("li", {}, el("b", { text: `${e.name} (${e.symbol})` }), `: ${e.reason}`)));

  $("analysts-text").textContent = `Not available yet: it needs a data licence that has not been granted (${data.ranking_by_analysts.reason}). This site does not compare the two rankings.`;
}
main().catch((e) => { document.querySelector("main").replaceChildren(el("h1", { text: "The rankings could not load" }), el("p", { text: `${e.message}. If you opened this file directly from disk, serve the folder instead: run "python -m engine.cli publish --serve".` })); });
