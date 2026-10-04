#!/usr/bin/env python3
"""The agent's cost, as a chart rather than a table.

Requirement R4: cost is drawn, not tabulated. Three things a reader needs, side by side:
where the tokens went, what each run cost, and how the conversation time compares with the
compute it set off. The last one is the point: a minute of talking buys hours of GPU.

Usage: 51_make_cost_panel.py <figure2|figure3> <run_id> [run_id ...]
       run ids are the keys in cost/agent_runs.csv
"""
from __future__ import annotations

import csv
import json
import sys
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib import font_manager

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_style

RUN = Path(os.environ.get("LV_RUN", "/project2/sli68423_1316/projects/long_verse/results/2026_09_25_longverse_agent_benchmark"))
FONT_DIR = Path(os.environ.get("LV_FONTS", "/project2/sli68423_1316/users/yang/software/fonts"))
FONT_USED = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf"):
    if (FONT_DIR / t).is_file():
        font_manager.fontManager.addfont(str(FONT_DIR / t))
if (FONT_DIR / "arial.ttf").is_file():
    FONT_USED = "Arial"
panel_style.apply(plt, FONT_USED)
# "input" and "conversation" shared one blue in a single legend, which reads as the same
# category listed twice; input is now a darker navy that no other series uses
C_IN, C_OUT, C_THINK, C_CACHE = "#08306B", "#009E73", "#56B4E9", "#BBBBBB"
AGENT_C, HUMAN_C = "#0072B2", "#D55E00"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip().splitlines()[-2], file=sys.stderr)
        return 2
    which, want = sys.argv[1], sys.argv[2:]
    rows = {r["run_id"]: r for r in csv.DictReader(open(RUN / "cost" / "agent_runs.csv"))}
    runs = [rows[w] for w in want if w in rows]
    if not runs:
        print(f"none of {want} in cost/agent_runs.csv; run 32_agent_cost_ledger.py first",
              file=sys.stderr)
        return 1
    out = RUN / which / "panels"; out.mkdir(parents=True, exist_ok=True)
    src = RUN / which / "source_data"; src.mkdir(parents=True, exist_ok=True)
    # "tools_only" on its own was read as the command line arm, which it is not: all three
    # of these are the agent, differing only in how much it is told. The human arm types a
    # command and spends no tokens at all, so it has no bar here and is stated instead.
    # Named for what the agent was given, not for the switch in the harness. "Paper2Agent
    # MCP" was considered and rejected: Paper2Agent is another group's system, and labelling
    # an arm with it invites the reader to think that system was run here. What was run is
    # this project's own MCP server; only the prompt layer follows the Paper2Agent design,
    # and that belongs in the text rather than on an axis.
    # Two arms, two labels, both short enough for an axis:
    #   MCP           this project's MCP server, tools attached and nothing else said
    #   Paper2Agent   the same server with its own prompt surfaced, which is the pattern
    #                 the Paper2Agent paper describes
    # The label names a design, not a piece of software that was executed here. Nothing of
    # Paper2Agent's own code was run, so the figure caption says so in words; putting that
    # qualification on the axis would make the axis unreadable.
    PRETTY = {
        "tools_only":  "MCP",
        "with_prompt": "MCP\n+ inspect hint",
        "mcp_prompt":  "Paper2Agent",
    }
    names = [PRETTY.get(r["run_id"].replace("upstream_", "").replace("phasing_", ""),
                        r["run_id"]) for r in runs]
    x = range(len(runs))

    # Drawn at the size it is placed at in the deck, 5.9 x 1.85 inches, rather than at a
    # comfortable size and shrunk afterwards. Shrinking a 7.4 inch figure into 3.9 inches
    # of slide scaled its 8 pt labels down to about 4 pt, which is where the tick labels
    # started running into the bars.
    # Horizontal bars, because at 12 pt the arm names will not fit under a vertical bar:
    # "MCP" and "Paper2Agent" collided into each other at every width tried. On the y axis
    # they have the whole row. Only the leftmost panel carries the names, the legend sits
    # below all three in one line, and the tick labels are shortened, because a 12 pt floor
    # in a 5.4 inch strip pays for itself in removed content, not in smaller type.
    fig, axes = plt.subplots(1, 3, figsize=(5.4, 2.45), sharey=True)
    yy = list(range(len(runs)))[::-1]

    def short(v):
        return f"{v/1000:.0f}k" if v >= 1000 else f"{v:.0f}"

    ax = axes[0]
    ins = [int(r["input_tokens"]) for r in runs]
    outs = [int(r["output_tokens"]) for r in runs]
    thinks = [int(r["thinking_tokens"]) for r in runs]
    vis = [o - t for o, t in zip(outs, thinks)]
    ax.barh(yy, ins, color=C_IN, label="input")
    ax.barh(yy, vis, left=ins, color=C_OUT, label="output")
    ax.barh(yy, thinks, left=[i + v for i, v in zip(ins, vis)], color=C_THINK,
            label="thinking")
    ax.set_yticks(yy); ax.set_yticklabels(names)
    ax.set_title("Tokens")
    hi = max(i + o for i, o in zip(ins, outs))
    ax.set_xticks([0, hi / 2, hi])
    ax.set_xticklabels(["0", short(hi / 2), short(hi)])

    ax = axes[1]
    costs = [float(r["cost_usd"]) for r in runs]
    ax.barh(yy, costs, color=AGENT_C, height=0.55)
    for y_, c in zip(yy, costs):
        ax.text(c, y_, f" ${c:.2f}", va="center", ha="left", fontsize=panel_style.MIN_PT)
    ax.set_title("Cost, US$")
    ax.set_xlim(0, max(costs) * 1.55)
    ax.set_xticks([0, round(max(costs), 1)])

    ax = axes[2]
    talk = [float(r["wall_seconds"]) / 60 for r in runs]
    meta = json.loads((RUN / which / "compute_minutes.json").read_text()) \
        if (RUN / which / "compute_minutes.json").is_file() else {}
    comp = [meta.get(r["run_id"], 0) for r in runs]
    h = 0.34
    ax.barh([y_ + h / 2 for y_ in yy], talk, height=h, color=AGENT_C, label="conversation")
    if any(comp):
        ax.barh([y_ - h / 2 for y_ in yy], comp, height=h, color=HUMAN_C, label="compute")
    ax.set_xscale("log")
    ax.set_title("Minutes, log")
    ax.set_xticks([1, 100])
    ax.set_xticklabels(["1", "100"])

    handles = [Patch(color=C_IN, label="input"), Patch(color=C_OUT, label="output"),
               Patch(color=C_THINK, label="thinking"),
               Patch(color=AGENT_C, label="conversation"), Patch(color=HUMAN_C, label="compute")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
               fontsize=panel_style.MIN_PT, bbox_to_anchor=(0.5, -0.13),
               handlelength=1.0, handletextpad=0.4, columnspacing=1.0)
    fig.text(0.5, -0.24, "human command line: $0, no tokens", ha="center",
             fontsize=panel_style.MIN_PT, color="0.35")

    fig.tight_layout()
    for e in ("pdf", "png"):
        fig.savefig(out / f"panel_agent_cost.{e}")
    plt.close(fig)

    with open(src / "panel_agent_cost.csv", "w", newline="") as fh:
        w2 = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w2.writeheader(); w2.writerows(runs)
    print(f"font: {FONT_USED}")
    for r, c in zip(runs, comp):
        print(f"  {r['run_id']:<26} ${r['cost_usd']:>7}  talk {float(r['wall_seconds'])/60:5.1f} min"
              f"  compute {c:6.1f} min  in {r['input_tokens']:>5} out {r['output_tokens']:>6}")
    print(f"panel -> {out/'panel_agent_cost.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
