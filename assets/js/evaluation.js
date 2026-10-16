// The evaluation page: lays out data/evaluation.json (built from the frozen files in eval/, ADR-073). Prose is written here, figures come from the data: no figure is typed in.
import { el, NAMES } from "./common.js";

const pct = (x) => (x === null || x === undefined ? "n/a" : `${Math.round(x * 100)}%`);
const frac = (a, b) => `${a} of ${b}`;
const word = { insufficient: "insufficient evidence", weak: "evidence weak", found: "evidence found" };
const levelWord = { "evidence found": "found", "evidence weak": "weak", "insufficient evidence": "insufficient", "not assessed": "not assessed" };
const ids = (xs) => xs.join(", ");
const table = (head, rows, caption) => el("div", { class: "tablewrap", tabindex: "0", role: "region", "aria-label": caption }, el("table", {}, el("thead", {}, el("tr", {}, head.map((h) => el("th", { text: h })))), el("tbody", {}, rows.map((r) => el("tr", {}, r.map((c) => el("td", { text: String(c) })))))));
const section = (title, ...kids) => [el("h2", { text: title }), ...kids];
const p = (text, cls) => el("p", cls ? { class: cls, text } : { text });
const crit = (c) => c.replace(/_/g, " ");

export function render(d) {
  const out = [];
  const nQ = d.criteria.length, devCo = d.dev.items / nQ, heldCo = d.heldout.items / nQ;
  const h = d.heldout, dv = d.dev, sp = d.split.heldout;

  out.push(...section("What we measured and how",
    p(`Three checks, each answering a different question. The dev set: ${devCo} companies and ${dv.items} judgements that a person labelled while reading the tool's answers. The rubric was written and tuned on these companies, so agreement here is optimistic. The held-out set: ${heldCo} other companies and ${h.items} judgements, labelled blind by one person from a packet that holds the question, the full rubric and passages from a fixed keyword search of the filing, and nothing the tool produced. The stability test: each of the ${nQ} questions was asked three ways (the question and the definitions of the verdicts reworded twice without changing their meaning) about every analysed company, to see how often the verdict changes with the wording.`),
    p("A judgement is one of three levels: evidence found, evidence weak, insufficient evidence. Agreement is exact when the tool and the person pick the same level, and within one level when they are at most one step apart. A judgement the tool could not make (not assessed) counts as a disagreement.", "small muted")));

  const rel = sp.criterion_reliability, stab = sp.finding_stability;
  out.push(...section("Headline: the tool's own warnings predicted where it disagrees with a person",
    p(`On the held-out set the tool agreed with the human label on ${frac(rel.normal.exact, rel.normal.n)} judgements of criteria that are not marked low reliability, and on ${frac(rel.low.exact, rel.low.n)} of criteria that are. Findings whose verdict stayed the same under rewording agreed with the person on ${frac(stab.stable.exact, stab.stable.n)}; findings whose verdict changed with the wording agreed on ${frac(stab.borderline.exact, stab.borderline.n)}. A criterion is marked low reliability when its verdict changed with the wording for at least ${pct(d.threshold)} of companies; the mark is computed from the stability test, not from the human labels.`),
    table(["Question", "Dev agreement", "Held-out agreement", "Verdict changed with wording", "Reliability"],
      d.criteria.map((c) => [c.name, frac(c.dev_exact, c.dev_n), frac(c.heldout_exact, c.heldout_n), `${frac(c.changed, c.compared)} (${pct(c.flip_rate)})`, c.low ? "Low reliability" : "No mark"]), "Agreement and wording sensitivity per question"),
    p(`Over both sets together: criteria without the mark agreed on ${frac(d.split.combined.criterion_reliability.normal.exact, d.split.combined.criterion_reliability.normal.n)}, marked criteria on ${frac(d.split.combined.criterion_reliability.low.exact, d.split.combined.criterion_reliability.low.n)}. The dev figures lean on the same companies the rubric was tuned on; the held-out figures are the fairer test.`, "small muted")));

  const lo = h.interval.low, hi = h.interval.high;
  const gen = h.direction.agent_more_generous, strict = h.direction.agent_stricter, na = h.direction.not_assessed;
  const labels = h.human_label_counts, found = labels["evidence found"];
  const durable = d.criteria.find((c) => c.criterion === "durable_competitive_advantage");
  out.push(...section("Overall agreement, honestly",
    p(`Held-out set: the tool and the person chose the same level for ${frac(h.exact, h.labelled)} judgements (${pct(h.exact / h.labelled)}) and were within one level on ${frac(h.within_one, h.labelled)} (${pct(h.within_one / h.labelled)}). With one labeller and ${h.labelled} judgements the uncertainty is wide: a ${pct(h.interval.level)} interval for the exact figure runs from about ${pct(lo)} to ${pct(hi)}.`),
    p(`Direction: the tool was stricter than the person on ${gen === 0 && strict === 0 ? "none" : strict} judgements and more generous on ${gen}${na ? `; ${na} could not be assessed` : ""}. The rubric asks for checkable evidence in the filing (a market share, a quantified position, a missed target the company admits) and treats claims and general statements as weak. The reviewer judged more broadly, and the gap is largest for durable competitive advantage, where the tool agreed on ${frac(durable.heldout_exact, durable.heldout_n)} held-out judgements: the person accepted an advantage the filing describes, the rubric wants one the filing measures. That is a difference between a strict rubric and a reasonable reader, not only an error of the tool, and it is listed as a limit below.`),
    p(`Weighted kappa, the agreement beyond chance, is ${h.kappa.weighted_linear === null ? "undefined" : h.kappa.weighted_linear.toFixed(2)} on ${h.kappa.n} assessed judgements. It is near zero largely because the person labelled almost everything as found (${frac(found, h.labelled)} labels): when one rater uses one level nearly all the time, kappa has little to measure, so read it together with the exact and within-one figures.`),
    p(`Dev set for comparison: ${frac(dv.exact, dv.labelled)} exact and ${frac(dv.within_one, dv.labelled)} within one level, weighted kappa ${dv.kappa.weighted_linear === null ? "undefined" : dv.kappa.weighted_linear.toFixed(2)}.`, "small muted")));

  out.push(...section("The dev-set lesson",
    p("The first agreement figure came from the same companies the rubric was tuned on. When the wording changed in ways unrelated to judgement, it fell:"),
    el("ul", {}, d.history.map((s) => el("li", { text: `${s.version}: ${frac(s.agree, s.of)} (${s.what})` }))),
    p("Verdicts on borderline questions depend on small differences in wording and in what is retrieved, so a tuning set overstates accuracy. We reacted in three ways: a held-out set labelled blind, the stability test that asks every question three ways, and visible marks on the company pages (a Borderline mark where a verdict changed with the wording, and a Low reliability note where a whole question does so often).")));

  const c = d.critic, rep = Object.entries(c.repairs);
  const accepted = rep.reduce((n, [, v]) => n + (v.accepted || 0), 0), rejected = rep.reduce((n, [, v]) => n + (v.rejected_by_recheck || 0), 0);
  out.push(...section("The Critic",
    p(`The Critic is a second reader that is partly code and partly a model. It re-opens the filing to check that every quote is really there, scans for advice language, checks the Explainer's lines, and asks a model whether the quoted sentences support each found or weak verdict. It never rewrites: a flagged item goes back to its author once, and if the repair still fails the original stays with a visible warning.`),
    p(`Over ${c.companies} companies and ${c.items} items it flagged ${c.flagged_first_pass} on the first pass (${c.flagged_by.finding} judgements, ${c.flagged_by.explanation} explanations). ${accepted} repairs were accepted and ${rejected} were not; ${c.final.warning} items end with a warning.`),
    p(c.dev_repair_made_worse.length ? `A repair can make things worse: on the dev set ${c.dev_repair_made_worse.map((m) => `${m.ticker} ${crit(m.criterion)} went from ${levelWord[m.before]} to ${levelWord[m.after]} although ${levelWord[m.human]} was the human label`).join("; ")}.` : "On the dev set no repair turned a correct verdict into a wrong one."),
    p(`The Critic never reviews a verdict of insufficient evidence (${frac(c.insufficient_evidence, c.findings)} judgements), so it cannot catch a false negative, and ${c.not_assessed} judgements were not assessed at all.`)));

  const n = d.numbers, labelRows = Object.entries(n.criteria).map(([id, v]) => [id, NAMES[id] || "", v.decided, v.decided ? pct(v.pass / v.decided) : "n/a", v.data_gap]);
  const s = d.sensitivity, byC = s.by_criterion;
  const srows = s.thresholds.map((t) => t.testable ? [t.criterion, t.label, t.default_display, `${t.minus_display}: ${t.minus.changed}`, `${t.plus_display}: ${t.plus.changed}`] : [t.criterion, t.label, t.default_display, "needs a share price", "needs a share price"]);
  const top = s.ranking.slice(0, 2), least = s.ranking[s.ranking.length - 1];
  const tr = n.triage.fixed, rs = n.restatements;
  out.push(...section("The numbers side (no language model)",
    p(`The scorers are plain arithmetic. Their results for ${n.frozen_companies} test companies on ${n.frozen_criteria} criteria (${n.frozen_labels} labels) were checked by hand against the filings and are frozen: a test fails if any label moves. The whole index was scored in one run: ${n.universe_scored} companies scored and ${n.universe_no_report} without an annual report yet. Label counts are frozen too, so a rule change that moves many results shows up.`),
    table(["Test", "Name", "Decided", "Share that pass", "Data gaps"], labelRows, "Label counts per test over the whole index"),
    p(`Anomaly checks on the run flag companies for review. Still flagged after the fixes: ${n.diagnostics.companies_with.revenue_jump} with a revenue jump of three times or more, ${n.diagnostics.companies_with.eps_sign_mismatch} whose diluted earnings per share have the opposite sign to net income, and ${n.diagnostics.companies_with.g4_fail_with_13_or_more_paid_years} dividend failures with most years paid (mostly genuine suspensions).`),
    el("ul", {}, tr.map((f) => el("li", { text: `Fixed (${f.adr}): ${f.what}; ${f.metric}: ${f.before} before, ${f.after} after.` }))),
    p(`Restatements. The restatement flag was checked fact by fact. ${rs.companies_with_true_restatement} companies have at least one true restatement: a later filing reports the same concept for the same fiscal year with a value that differs by more than ten percent (${rs.true_restatement_values} values; usually a recast for a discontinued operation, an acquisition or a changed presentation, so informational).`),
    p(`Concept switches. ${rs.companies_with_concept_switch} companies report the same measure under different tags in different years. That can move a margin or a growth rate, but it is not a restatement, and the flag does not count it: ${rs.flagged_values_that_are_not_true_restatements} of the flagged values were anything other than a true restatement.`),
    p(`Threshold sensitivity. Each numeric threshold was moved down and up by ${pct(s.delta)} on its own (a count of years is rounded to a whole year) and all ${s.companies} companies were scored again. The table shows how many labels change.`),
    table(["Test", "Threshold", "Published value", "Lower: new value, labels changed", "Higher: new value, labels changed"], srows, "Labels changed when each threshold moves"),
    p(`The most threshold-sensitive tests are ${top.map((id) => `${id} (${NAMES[id]}; at most ${pct(byC[id].worst_share)} of ${byC[id].decided} decided labels change)`).join(" and ")}; the least sensitive is ${least} (${NAMES[least]}; at most ${pct(byC[least].worst_share)}). A test with a high share is a judgement call about where to draw the line, and its pass or fail on a company near the line should not be over-read. The two price-based tests cannot be tested until share prices are available.`)));

  out.push(...section("What it gets wrong",
    el("ul", {}, [
      ["Durable competitive advantage and candid management are the weak questions: they are marked low reliability, and the tool and a person often differ.", "doc.html?f=evaluation_notes"],
      ["An annual report is a limited guide to candour: it is reviewed by lawyers, so polished text is not evidence of openness.", "doc.html?f=evaluation_notes"],
      ["The rubric is stricter than a reasonable reader on durable advantage; a second rater and a rubric review are the next step.", "doc.html?f=evaluation_notes"],
      ["Capital allocation is sometimes not assessed because the agent runs out of turns looking for a current-year sentence.", "doc.html?f=evaluation_notes"],
      ["The held-out set has one labeller and a few judgements; the dev set was used for tuning.", "doc.html?f=DECISIONS"],
      ["Data gaps: operating income and capital spending are untagged for many companies, so two tests are gaps for them; the price tests wait for licensed price data.", "doc.html?f=universe_scorecard_report"],
      ["Reading the full list of limits, one by one:", "doc.html?f=evaluation_notes"],
    ].map(([t, href]) => el("li", {}, t, " ", el("a", { href, text: "Details" }))))));
  return out;
}
