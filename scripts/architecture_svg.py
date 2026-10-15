"""Write site_src/assets/img/architecture.svg, the architecture drawing used by the README, the how-it-works page and the documents (build 5).

    .venv/bin/python scripts/architecture_svg.py

The file carries its own style with fallbacks, so it also reads correctly on its own (GitHub renders it as an image) and follows light and dark mode; inside the site
the page's colour variables take over. `publish` inlines this file into how-it-works.html in place of `__ARCHITECTURE_SVG__`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.settings import REPO_ROOT  # noqa: E402

OUT = REPO_ROOT / "site_src" / "assets" / "img" / "architecture.svg"
W, H = 960, 472
STYLE = ("<style>svg.arch{--a-paper:#FFFFFF;--a-ink:#1D2733;--a-muted:#5B6673;--a-blue:#2F5D8A}"
         "@media(prefers-color-scheme:dark){svg.arch{--a-paper:#1B232C;--a-ink:#E4E9EE;--a-muted:#9AA6B3;--a-blue:#8DB4DB}}"
         "svg.arch .box{fill:var(--surface,var(--a-paper));stroke:var(--ink,var(--a-ink));stroke-width:1}svg.arch .agent{stroke:var(--blue,var(--a-blue));stroke-width:2}"
         "svg.arch .arrow{stroke:var(--ink,var(--a-ink));stroke-width:1.2;fill:none}svg.arch text{fill:var(--ink,var(--a-ink));font:400 13px system-ui,sans-serif}"
         "svg.arch .sub{fill:var(--muted,var(--a-muted));font-size:11.5px}</style>")
parts: list[str] = []


def box(x, y, w, h, title, sub=None, agent=False):
    parts.append(f'<rect class="box{" agent" if agent else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>')
    parts.append(f'<text x="{x + 10}" y="{y + (h / 2 + 4 if sub is None else 23)}">{title}</text>')
    if sub:
        parts.append(f'<text class="sub" x="{x + 10}" y="{y + 41}">{sub}</text>')


def arrow(d, head, dashed=False):
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    parts.append(f'<path class="arrow" d="{d}"{dash}/>')
    parts.append(f'<path class="arrow" d="{head}"/>')


def right(x1, x2, y):
    arrow(f"M{x1} {y} H{x2}", f"M{x2 - 7} {y - 4} L{x2} {y} L{x2 - 7} {y + 4}")


def down(x, y1, y2, dashed=False):
    arrow(f"M{x} {y1} L{x} {y2}", f"M{x - 4} {y2 - 7} L{x} {y2} L{x + 4} {y2 - 7}", dashed)


def up(x, y1, y2, dashed=False):
    arrow(f"M{x} {y1} L{x} {y2}", f"M{x - 4} {y2 + 7} L{x} {y2} L{x + 4} {y2 + 7}", dashed)


box(20, 14, 920, 40, "Planner and orchestrator: decides scope, sector class and which tests apply; times and records every step in the trace")
box(20, 86, 150, 56, "SEC company facts", "XBRL figures, all years")
box(210, 86, 150, 56, "Normaliser", "one series per measure")
box(400, 86, 170, 56, "Scorers G1–G7, B1–B4", "plain arithmetic, no model")
box(610, 86, 150, 56, "Explainer", "one plain line per score", agent=True)
box(20, 196, 150, 56, "Latest 10-K", "Items 1, 1A and 7")
box(210, 196, 150, 56, "Retriever", "keyword search")
box(400, 196, 170, 56, "Qualitative agent", "one loop per question", agent=True)
box(610, 196, 150, 56, "Critic", "rules first, then a model", agent=True)
box(800, 140, 140, 56, "Reporter", "checks, publish gate")
for x1, x2, y in ((170, 210, 114), (360, 400, 114), (570, 610, 114), (170, 210, 224), (360, 400, 224), (570, 610, 224)):
    right(x1, x2, y)
down(685, 142, 196)
arrow("M760 114 H870 V140", "M866 133 L870 140 L874 133")
arrow("M760 224 H870 V196", "M866 203 L870 196 L874 203")
# the Critic's one repair: a rationale rewrite or a constrained retry, then a re-check
arrow("M610 235 H585 V268 H485 V252", "M481 259 L485 252 L489 259", dashed=True)
parts.append('<text class="sub" x="500" y="284">One repair per failed item</text>')
# stability runs and the evaluation harness
box(400, 292, 440, 50, "Stability runs: each question reworded twice", "agent and Critic rerun; sets the Borderline and Low reliability marks")
up(735, 292, 252, dashed=True)
box(20, 292, 360, 50, "Evaluation harness", "human labels, agreement, threshold sensitivity")
box(20, 366, 920, 36, "Results files and recorded trace, one per company, read by the static site (no model runs there)")
arrow("M870 196 V366", "M866 359 L870 366 L874 359")
down(620, 342, 366)
down(200, 342, 366, dashed=True)
box(20, 424, 620, 36, "Publish gates, then a secret scan of the site and every commit")
box(680, 424, 260, 36, "Static site (GitHub Pages)")
down(330, 402, 424)
right(640, 680, 442)
svg = (f'<svg class="arch" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d"><title id="t">Architecture of the analysis pipeline</title>'
       '<desc id="d">A planner controls two lanes. Numbers: SEC company facts, normaliser, scorers, Explainer. Text: latest 10-K, retriever, qualitative agent, Critic. The Critic can send a failed '
       'finding back once, by a rationale rewrite or a constrained retry. A reporter writes the results files. Stability runs reword each question twice and run the agent and the Critic again; '
       'the evaluation harness compares with human labels. Publish gates and a secret scan stand between the results files and the static site.</desc>' + STYLE + "".join(parts) + "</svg>\n")
if __name__ == "__main__":
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(svg)} bytes)")
