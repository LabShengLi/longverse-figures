"""Panel a of the agent-versus-human figures: the same run, asked in two ways.

Left, the person's nextflow command as one block with a note; right, the sentence the
person typed to the agent, the tools the agent chose, and the turns, seconds and job id.
Under both, the two runs' task counts, longest stage and failures, and the agent's cost
chart. Returns the y where the next panel starts.

Laid out for the Nature Methods page: 183 mm wide, 7 pt text. The lengths were tuned on
the 13.33 in canvas and are mapped through nm_style.s().
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image
from pptx.util import Pt

from arm_records import human_command_lines, tool_chain, trace_row
from nm_style import s
from pptx_helpers import (AGENT, GREY, HUMAN, MIN_PT, SANS, E, box, hline, label, line,
                          para, picture, prompt_box, textbox)

WRAP_COLS = 52      # 7 pt Consolas is 0.058 in per character; the block is 3.4 in wide, 4 of it indent
LINE_IN = 0.13      # one 7 pt monospace line in the command block


def panel_a(slide, *, y, W, M, sd: Path, panels: Path, rec: dict, human_note: str,
            cost_note: str) -> tuple[float, list[tuple]]:
    colw = (W - 2 * M - s(0.35)) / 2
    RIGHT = M + colw + s(0.35)
    label(slide, M, y, "a", "The same run, asked in two ways", w=W - 2 * M)
    hline(slide, M, y + s(0.30), W - 2 * M)
    ytop = y + s(0.40)
    tb, tf = textbox(slide, M, ytop, colw, s(0.34))
    para(tf, "HUMAN COMMAND LINE", bold=True, color=HUMAN, first=True)
    tb, tf = textbox(slide, RIGHT, ytop, colw, s(0.34))
    para(tf, "AGENT", bold=True, color=AGENT, first=True)
    yb = ytop + s(0.42)
    bw = colw * 0.98

    hlines = human_command_lines(sd / "human_command_as_run.txt", WRAP_COLS)
    # height from the lines as PowerPoint will wrap them, not from the count: a quoted value
    # longer than the box (Supp Fig 4's containerOptions) wraps once more inside the box
    import math
    cols_fit = max(1, int((bw - 0.06) / (0.60 * MIN_PT / 72)))
    n_wrapped = sum(max(1, math.ceil(len(l) / cols_fit)) for l in hlines)
    hbox_h = s(0.30) + LINE_IN * n_wrapped
    box(slide, M, yb, bw, hbox_h, hlines, HUMAN, mono=True)
    tb, tf = textbox(slide, M, yb + hbox_h + s(0.06), bw, s(0.72))
    para(tf, human_note, color=GREY, first=True)
    human_bottom = yb + hbox_h + s(0.06) + s(0.72)

    # the sentence box grows with the sentence: 7 pt Arial is about 0.05 in per character,
    # 0.12 in per line; Fig 3's six words fit one line, Supp Fig 3's two sentences take three
    import math
    n_lines = max(1, math.ceil(len(rec["request"]) * 0.0506 / (bw - 0.06)))
    ph = max(s(0.46), 0.12 * n_lines + 0.08)
    prompt_box(slide, RIGHT, yb, bw, ph, f"“{rec['request']}”")
    tb, tf = textbox(slide, RIGHT, yb + ph + s(0.02), bw, s(0.30))
    para(tf, "what the person typed", color=GREY, first=True)
    tb, tf = textbox(slide, RIGHT, yb + ph + s(0.42), bw, s(0.30))
    para(tf, "what the agent did on its own", color=GREY, first=True)
    chain = tool_chain(rec)
    ya, bh, gap = yb + ph + s(0.74), s(0.34), s(0.10)
    line(slide, RIGHT + bw / 2, yb + ph + s(0.23), RIGHT + bw / 2, yb + ph + s(0.35), AGENT,
         width=0.75, arrow=True)
    for i, t in enumerate(chain):
        if i:
            line(slide, RIGHT + bw / 2, ya + i * (bh + gap) - gap, RIGHT + bw / 2,
                 ya + i * (bh + gap), AGENT, width=0.75, arrow=True)
        box(slide, RIGHT, ya + i * (bh + gap), bw, bh, t, AGENT, mono=True, line_width=0.75)
    ysum = ya + len(chain) * (bh + gap)
    tb, tf = textbox(slide, RIGHT, ysum, bw, s(0.56))
    para(tf, f"{rec['totals']['steps']} turns, {rec['totals']['wall_seconds']:.0f} s of "
             f"conversation, then Slurm job {rec['launched']['job_id']}", color=GREY, first=True)
    a_bottom = max(human_bottom, ysum + s(0.56))

    # the two runs and the agent's cost
    y2 = a_bottom + s(0.10)
    rows = [("Human command line",) + trace_row(sd / "human_trace.txt"),
            ("Agent",) + trace_row(sd / "agent_trace.txt")]
    cost_png = panels / "panel_agent_cost.png"
    with Image.open(cost_png) as im:
        d = im.info.get("dpi", (300, 300))[0] or 300
        cost_w, cost_h = im.width / d, im.height / d
    tbl_w = W - 2 * M - cost_w - s(0.25)
    picture(slide, cost_png, W - M - cost_w, y2)
    row_h = s(0.32)
    tbl = slide.shapes.add_table(3, 4, E(M), E(y2 + s(0.10)), E(tbl_w), E(3 * row_h)).table
    for r in tbl.rows:
        r.height = E(row_h)
    tbl.columns[0].width = E(s(2.0))
    for i in range(1, 4):
        tbl.columns[i].width = E((tbl_w - s(2.0)) / 3)
    for j, h in enumerate(["", "tasks completed", "longest stage", "failed"]):
        c = tbl.cell(0, j); c.text = h
        c.margin_left = c.margin_right = E(0.03); c.margin_top = c.margin_bottom = E(0.01)
        for r in c.text_frame.paragraphs[0].runs:
            r.font.size = Pt(MIN_PT); r.font.bold = True; r.font.name = SANS
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = tbl.cell(i, j); c.text = str(v)
            c.margin_left = c.margin_right = E(0.03); c.margin_top = c.margin_bottom = E(0.01)
            for r in c.text_frame.paragraphs[0].runs:
                r.font.size = Pt(MIN_PT); r.font.name = SANS
                r.font.color.rgb = HUMAN if i == 1 else AGENT; r.font.bold = (j == 0)
    tb, tf = textbox(slide, M, y2 + s(0.10) + 3 * row_h + s(0.08), tbl_w, s(0.72))
    para(tf, cost_note, color=GREY, first=True)
    y_next = y2 + max(cost_h, s(0.10) + 3 * row_h + s(0.08) + s(0.72)) + s(0.16)
    return y_next, rows
