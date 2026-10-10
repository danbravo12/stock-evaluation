import { el, fail, manifest, footer } from "./common.js";
// A small, safe Markdown viewer for the repository documents linked from "How it works". It builds DOM nodes and never parses HTML.
const ALLOWED = ["evaluation_notes", "DECISIONS", "PROCESS", "ARCHITECTURE", "universe_scorecard_report", "qualitative_report", "critic_report", "coverage_report"];
function inline(text) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    out.push(text.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) out.push(el("b", { text: t.slice(2, -2) }));
    else if (t.startsWith("`")) out.push(el("i", { text: t.slice(1, -1) }));
    else { const [, label, href] = t.match(/\[([^\]]+)\]\(([^)]+)\)/); out.push(/^https:\/\//.test(href) ? el("a", { href, rel: "noopener", text: label }) : label); }
    last = m.index + t.length;
  }
  out.push(text.slice(last));
  return out;
}
function render(md) {
  const root = document.createDocumentFragment(), lines = md.split("\n");
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    const h = l.match(/^(#{1,4})\s+(.*)$/);
    if (h) { root.append(el("h" + Math.min(h[1].length + 1, 4), { text: h[2].replace(/[`*]/g, "") })); i++; continue; }
    if (l.startsWith("|")) {
      const rows = []; while (i < lines.length && lines[i].startsWith("|")) { if (!/^\|[\s:|-]+\|?$/.test(lines[i])) rows.push(lines[i].replace(/^\||\|$/g, "").split("|")); i++; }
      const t = el("table", {}, el("tbody", {}, rows.map((r, ri) => el("tr", {}, r.map((c) => el(ri === 0 ? "th" : "td", {}, inline(c.trim())))))));
      root.append(el("div", { class: "tablewrap", tabindex: "0", role: "region", "aria-label": "Table" }, t)); continue;
    }
    if (/^\s*[-*]\s+/.test(l)) { const items = []; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) { items.push(el("li", {}, inline(lines[i].replace(/^\s*[-*]\s+/, "")))); i++; } root.append(el("ul", {}, items)); continue; }
    if (/^\s*\d+\.\s+/.test(l)) { const items = []; while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) { items.push(el("li", {}, inline(lines[i].replace(/^\s*\d+\.\s+/, "")))); i++; } root.append(el("ol", {}, items)); continue; }
    const para = []; while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|\||\s*[-*]\s|\s*\d+\.\s)/.test(lines[i])) para.push(lines[i++]);
    root.append(el("p", {}, inline(para.join(" "))));
  }
  return root;
}
async function main() {
  footer(await manifest());
  const f = new URLSearchParams(location.search).get("f");
  if (!ALLOWED.includes(f)) throw new Error("That document is not part of this site.");
  const r = await fetch(`data/docs/${f}.md`);
  if (!r.ok) throw new Error(`The document could not be loaded (HTTP ${r.status}).`);
  document.title = `${f.replaceAll("_", " ")} (repository document)`;
  $doc.replaceChildren(el("p", { class: "muted small", text: `Shown as plain text from the project repository: ${f}.md` }), render(await r.text()));
}
const $doc = document.getElementById("doc");
main().catch((e) => fail(e.message, "Go back to how it works and choose another link."));
