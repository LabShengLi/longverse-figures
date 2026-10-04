#!/usr/bin/env python3
"""Mean CpG methylation around a set of reference points (TSS or CTCF), three tracks, from the
deepTools plotProfile data table. 7 pt, 2.9 x 2.0 in: the first version at 3.5 x 1.7 was too flat to
read the dip at the reference point. Same parsing as suppfig2/42_plot_profile_12pt.py: a sample row
has a non-empty group column, the two header rows do not.

The bin width is printed on the x axis, because the two profiles do not share one. CTCF has fewer and
shorter regions than TSS, so a 50 bp bin there is a saw edge rather than a signal.

Usage: 13_profile_nm.py <profile_data.tsv> <out_stem> <centre> <flank_bp> [bin_bp]   (env: conda/envs/py39_v2)
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
import numpy as np

PT = float(os.environ.get("PANEL_MIN_PT", 7))
COLORS = {"ONT": "#1f78b4", "PacBio": "#e31a1c", "WGBS": "#33a02c"}
FD = os.environ.get("LONGVERSE_FONT_DIR", "/project2/sli68423_1316/users/yang/software/fonts")
fam = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf"):
    if os.path.isfile(os.path.join(FD, t)):
        matplotlib.font_manager.fontManager.addfont(os.path.join(FD, t))
if os.path.isfile(os.path.join(FD, "arial.ttf")):
    fam = "Arial"
plt.rcParams.update({"font.family": fam, "font.size": PT, "axes.labelsize": PT, "xtick.labelsize": PT,
                     "ytick.labelsize": PT, "legend.fontsize": PT, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2, "ytick.major.size": 2})


def main() -> int:
    data, stem, centre, flank = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    binbp = int(sys.argv[5]) if len(sys.argv) > 5 else 50
    series = []
    for r in (l.rstrip("\n").split("\t") for l in open(data) if l.strip()):
        if len(r) < 3 or not r[1].strip():
            continue
        vals = np.array([float(v) if v not in ("", "nan") else np.nan for v in r[2:]])
        if not np.all(np.isnan(vals)):
            series.append((r[0].strip(), vals))
    if not series:
        raise SystemExit(f"no plottable rows in {data}")
    fig, ax = plt.subplots(figsize=(2.9, 2.0), constrained_layout=True)
    for name, y in series:
        ax.plot(np.linspace(-flank, flank, len(y)), y, lw=1.0, label=name, color=COLORS.get(name))
    ax.axvline(0, color="#444444", lw=0.6, ls="--")
    ax.set_xlim(-flank, flank); ax.set_ylim(0, 1)
    ax.set_xticks([-flank, -flank // 2, 0, flank // 2, flank])
    ax.set_xticklabels([f"-{flank // 1000} kb", f"-{flank // 2000} kb", centre, f"+{flank // 2000} kb", f"+{flank // 1000} kb"])
    ax.set_xlabel(f"Distance from {centre} ({binbp} bp bins)")
    ax.set_ylabel("Methylation frequency")
    ax.legend(frameon=False, loc="lower right", handlelength=1.2)
    fig.savefig(stem + ".pdf"); fig.savefig(stem + ".png", dpi=300)
    print(f"wrote {stem}.pdf/.png from {len(series)} tracks x {len(series[0][1])} bins of {binbp} bp  {PT} pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
