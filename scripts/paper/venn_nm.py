#!/usr/bin/env python3
"""Two-set Venn of CpG sites covered at five or more reads, ONT and PacBio, from the counts in
the stats table (plot_perSite_venn.R wrote it). 7 pt, 2.2 x 1.7 in. Circle areas are
proportional to the set sizes and the overlap is placed by the overlap count, so the picture
is read off the same five numbers it prints.

Usage: 11_venn_nm.py <venn_stats.tsv> <out_stem>          (env: conda/envs/py39_v2)
"""
from __future__ import annotations

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.optimize import brentq

PT = float(os.environ.get("PANEL_MIN_PT", 7))
FD = os.environ.get("LONGVERSE_FONT_DIR", "/project2/sli68423_1316/users/yang/software/fonts")
fam = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf"):
    if os.path.isfile(os.path.join(FD, t)):
        matplotlib.font_manager.fontManager.addfont(os.path.join(FD, t))
if os.path.isfile(os.path.join(FD, "arial.ttf")):
    fam = "Arial"
plt.rcParams.update({"font.family": fam, "font.size": PT, "pdf.fonttype": 42, "ps.fonttype": 42})
ONT_C, PB_C = "#1f78b4", "#e31a1c"


def lens_area(d, r1, r2):
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2
    a1 = r1 * r1 * math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1))
    a2 = r2 * r2 * math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    return a1 + a2 - 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def main() -> int:
    stats, stem = sys.argv[1], sys.argv[2]
    kv = dict(l.rstrip("\n").split("\t") for l in open(stats) if "\t" in l and not l.startswith("metric"))
    tot1, tot2, both = int(kv["ONT_total"]), int(kv["PacBio_total"]), int(kv["overlap"])
    only1, only2 = int(kv["ONT_only"]), int(kv["PacBio_only"])
    assert tot1 == both + only1 and tot2 == both + only2, "the five counts do not add up"
    r1, r2 = math.sqrt(tot1 / math.pi), math.sqrt(tot2 / math.pi)
    d = brentq(lambda x: lens_area(x, r1, r2) - both, abs(r1 - r2) + 1e-9, r1 + r2 - 1e-9)
    scale = 1.0 / (r1 + r2 + d)
    r1, r2, d = r1 * scale, r2 * scale, d * scale
    fig, ax = plt.subplots(figsize=(2.2, 1.7), constrained_layout=True)
    c1, c2 = (-d / 2, 0), (d / 2, 0)
    ax.add_patch(Circle(c1, r1, fc=ONT_C, ec="none", alpha=0.45))
    ax.add_patch(Circle(c2, r2, fc=PB_C, ec="none", alpha=0.45))
    ax.add_patch(Circle(c1, r1, fc="none", ec=ONT_C, lw=0.6))
    ax.add_patch(Circle(c2, r2, fc="none", ec=PB_C, lw=0.6))
    # labels: the two crescents hold almost nothing, so their counts sit outside with a leader
    ax.text(0, 0, f"{both:,}", ha="center", va="center", fontsize=PT)
    # the sets overlap by 98%, so the two circles nearly coincide: the set labels go to the
    # upper left and upper right, clear of each other, rather than over each circle's centre
    top = max(r1, r2) + 0.04
    ax.text(-0.50, top, f"ONT\n{tot1:,}", ha="center", va="bottom", fontsize=PT, color=ONT_C)
    ax.text(0.50, top, f"PacBio\n{tot2:,}", ha="center", va="bottom", fontsize=PT, color=PB_C)
    ax.annotate(f"ONT only\n{only1:,}", xy=(c1[0] - r1 * 0.93, 0), xytext=(c1[0] - r1 - 0.06, -r1 - 0.10),
                ha="right", va="top", fontsize=PT, arrowprops=dict(arrowstyle="-", lw=0.5, color="#444444"))
    ax.annotate(f"PacBio only\n{only2:,}", xy=(c2[0] + r2 * 0.93, 0), xytext=(c2[0] + r2 + 0.06, -r2 - 0.10),
                ha="left", va="top", fontsize=PT, arrowprops=dict(arrowstyle="-", lw=0.5, color="#444444"))
    ax.set_xlim(-0.98, 0.98); ax.set_ylim(-0.85, 0.90); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(stem + ".pdf"); fig.savefig(stem + ".png", dpi=300)
    print(f"wrote {stem}.pdf/.png  ONT {tot1:,} PacBio {tot2:,} both {both:,}  {PT} pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
