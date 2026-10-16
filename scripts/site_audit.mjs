// Screenshots and an accessibility / layout audit of the built site, through headless Chrome (build 5).
//   node scripts/site_audit.mjs <base-url> [--shots] [--audit]
// Screenshots go to docs/screenshots/<page>-<width>.png at 1280 and 390 px. The audit reports, per page, width and colour scheme: horizontal overflow, heading order,
// images without alt text, controls without an accessible name, and text whose contrast with its background is below 4.5:1 (3:1 for large text).
import { spawn } from "node:child_process";
import fs from "node:fs";

const base = process.argv[2] || "http://localhost:8781";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PAGES = { index: "index.html", company: "company.html?cik=0000021344", "company-pane": "company.html?cik=0000021344#candid_management", trace: "trace.html?cik=0000021344", evaluation: "evaluation.html", "how-it-works": "how-it-works.html", doc: "doc.html?f=DECISIONS" };
const SHOT = ["index", "company-pane", "trace", "evaluation", "how-it-works"];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const port = 9333;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`, "--user-data-dir=/tmp/chrome-audit", "--no-first-run", "about:blank"], { stdio: "ignore" });
let ws, id = 0; const pending = new Map();
async function connect() {
  for (let i = 0; i < 50; i++) { try { const t = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); const page = t.find((x) => x.type === "page"); if (page) { ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; }); ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } }; return; } } catch {} await sleep(200); }
  throw new Error("no chrome");
}
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJS = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result.result.value;

const AUDIT = `(() => {
  const out = { overflow: document.documentElement.scrollWidth - window.innerWidth, headings: [], badHeadings: [], noAlt: 0, noName: [], lowContrast: [] };
  let prev = 0;
  for (const h of document.querySelectorAll("h1,h2,h3,h4")) { const l = +h.tagName[1]; out.headings.push(l); if (prev && l > prev + 1) out.badHeadings.push(h.textContent.trim().slice(0, 40) + " (h" + l + " after h" + prev + ")"); prev = l; }
  if (document.querySelectorAll("h1").length !== 1) out.badHeadings.push("h1 count " + document.querySelectorAll("h1").length);
  for (const i of document.querySelectorAll("img:not([alt])")) out.noAlt++;
  for (const c of document.querySelectorAll("a,button,input,select,textarea,[role=button],summary")) {
    const name = (c.getAttribute("aria-label") || c.textContent || c.getAttribute("title") || c.getAttribute("alt") || (c.labels && c.labels[0] && c.labels[0].textContent) || "").trim();
    if (!name && c.offsetParent !== null) out.noName.push(c.outerHTML.slice(0, 80));
  }
  const parse = (s) => { const m = s.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(",").map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = ({ r, g, b }) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const bgOf = (e) => { let layers = []; for (let n = e; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; } } let base = { r: 255, g: 255, b: 255 }; for (const c of layers.reverse()) base = { r: c.r * c.a + base.r * (1 - c.a), g: c.g * c.a + base.g * (1 - c.a), b: c.b * c.a + base.b * (1 - c.a) }; return base; };
  const seen = new Set(); const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t; (t = walker.nextNode()); ) {
    if (!t.textContent.trim()) continue; const e = t.parentElement; if (!e || seen.has(e) || e.closest("script,style,svg") || e.offsetParent === null && getComputedStyle(e).position !== "fixed") continue; seen.add(e);
    const cs = getComputedStyle(e); if (cs.visibility === "hidden" || cs.display === "none") continue;
    const fg = parse(cs.color), bg = bgOf(e); if (!fg) continue;
    const mix = { r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a) };
    const L1 = lum(mix), L2 = lum(bg), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700, large = size >= 24 || (size >= 18.66 && bold);
    if (ratio < (large ? 3 : 4.5)) out.lowContrast.push({ text: t.textContent.trim().slice(0, 40), ratio: +ratio.toFixed(2), tag: e.tagName.toLowerCase() + (e.className ? "." + String(e.className).split(" ")[0] : "") });
  }
  out.lowContrast = out.lowContrast.slice(0, 12); out.noName = out.noName.slice(0, 5);
  return out; })()`;

const ACTIVE = `(() => { const e = document.activeElement; if (!e || e === document.body) return null; const c = getComputedStyle(e);
  let ring = (c.outlineStyle !== "none" && parseFloat(c.outlineWidth) > 0) || c.boxShadow !== "none";
  if (e.tagName.toLowerCase() === "g") { const k = e.querySelector("circle"); ring = !!k && parseFloat(getComputedStyle(k).strokeWidth) >= 3; } // an SVG mark shows focus as a thicker ring
  return { name: e.tagName + " " + (e.getAttribute("aria-label") || e.textContent || "").trim().slice(0, 30), ring, visible: e.offsetParent !== null || c.position === "fixed" }; })()`;
async function tabThrough(n) { // real Tab presses, so :focus-visible applies; every focused control must show a ring
  const bad = []; let seen = 0;
  for (let i = 0; i < n; i++) {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 }); await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    const a = await evalJS(ACTIVE); if (!a) continue; seen++; if (a.visible && !a.ring) bad.push(a.name);
  }
  return { checked: seen, noVisibleFocus: [...new Set(bad)].slice(0, 8) };
}

await connect();
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable"); await send("Network.setCacheDisabled", { cacheDisabled: true });
if (process.argv.includes("--swimlane")) { // the agent names stay put while the overview scrolls sideways (mobile)
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 780, deviceScaleFactor: 1, mobile: true }); await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "dark" }] });
  await send("Page.navigate", { url: `${base}/trace.html?cik=0000021344` }); await sleep(2500);
  const info = await evalJS("(() => { const s = document.getElementById('swim'); s.scrollLeft = 250; const l = document.querySelector('.swimlabels'); const r = l.getBoundingClientRect(); return { scrollLeft: s.scrollLeft, scrollWidth: s.scrollWidth, clientWidth: s.clientWidth, labelsLeft: r.left, labelsWidth: r.width, labelsVisible: r.left >= 0 && r.right <= innerWidth }; })()");
  console.log("swimlane", JSON.stringify(info), JSON.stringify(await evalJS("(() => { const f = document.getElementById('swimfig'); document.getElementById('swimfig').scrollIntoView(); const r = f.getBoundingClientRect(); return { h: r.height, top: r.top, labelsH: document.querySelector('.swimlabels').getBoundingClientRect().height, plotH: document.querySelector('.swimsvg').getBoundingClientRect().height }; })()")));
  fs.writeFileSync("docs/screenshots/trace-swimlane-scrolled-390.png", Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));
  ws.close(); chrome.kill(); process.exit(0);
}
const shots = process.argv.includes("--shots"), audit = process.argv.includes("--audit");
const report = {};
for (const width of [1280, 390]) for (const scheme of ["light", "dark"]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 500 });
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: scheme }] });
  for (const [name, path] of Object.entries(PAGES)) {
    await send("Page.navigate", { url: `${base}/${path}` }); await sleep(2500);
    if (path.includes("#")) { await evalJS("location.reload()"); await sleep(2500); }
    if (audit) { const r = await evalJS(AUDIT); await evalJS('document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)'); r.focus = await tabThrough(30); report[`${name} ${width} ${scheme}`] = r; }
    if (shots && scheme === "dark" && SHOT.includes(name)) {
      const h = await evalJS("Math.ceil(document.documentElement.scrollHeight)");
      await send("Emulation.setDeviceMetricsOverride", { width, height: Math.min(h, 12000), deviceScaleFactor: 1, mobile: width < 500 }); await sleep(600);
      const r = await send("Page.captureScreenshot", { format: "png" });
      fs.writeFileSync(`docs/screenshots/${name}-${width}.png`, Buffer.from(r.result.data, "base64"));
    }
  }
}
if (audit) fs.writeFileSync("/tmp/audit.json", JSON.stringify(report, null, 1));
ws.close(); chrome.kill();
if (audit) {
  let bad = 0;
  for (const [k, r] of Object.entries(report)) {
    const issues = [r.overflow > 0 && `overflow ${r.overflow}px`, r.badHeadings.length && `headings: ${r.badHeadings.join("; ")}`, r.noAlt && `${r.noAlt} images without alt`, r.noName.length && `unnamed controls: ${r.noName.length}`, r.lowContrast.length && `low contrast: ${r.lowContrast.length} (${r.lowContrast.slice(0, 3).map((c) => c.text + " " + c.ratio).join("; ")})`, r.focus.noVisibleFocus.length && `no visible focus: ${r.focus.noVisibleFocus.slice(0, 3).join("; ")}`].filter(Boolean);
    if (issues.length) { bad++; console.log(k + ": " + issues.join(" | ")); }
  }
  console.log(bad ? `${bad} of ${Object.keys(report).length} page views have issues` : `no issues in ${Object.keys(report).length} page views`);
}
