#!/usr/bin/env python3
"""Per-site coverage distributions, ONT and PacBio, from the per-coverage site counts that
suppfig2/41_coverage_histogram.sbatch wrote (one row per integer coverage). 7 pt, 2.35 x 1.7 in.
The medians and the share of sites at coverage five or more are computed here from the same
counts and written next to the panel.

Usage: 12_coverage_hist_nm.py <source_data dir> <out_stem>          (env: conda/envs/py39_v2)
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


def load(p):
    a = np.loadtxt(p, dtype="int64", ndmin=2)
    return a[:, 0], a[:, 1]


def stats(x, y):
    n = y.sum(); cs = np.cumsum(y)
    return n, (x * y).sum() / n, x[np.searchsorted(cs, n / 2)], y[x >= 5].sum()


def main() -> int:
    src, stem = sys.argv[1], sys.argv[2]
    XMAX = 100
    fig, ax = plt.subplots(figsize=(2.35, 1.7), constrained_layout=True)
    lines = ["platform\tsites\tmean_cov\tmedian_cov\tsites_cov_ge5\tpct_cov_ge5"]
    for lab, fn, col in (("ONT", "B_coverage_hist_ont.tsv", "#1f78b4"), ("PacBio", "B_coverage_hist_pacbio.tsv", "#e31a1c")):
        x, y = load(os.path.join(src, fn))
        n, mean, med, ge5 = stats(x, y)
        m = x <= XMAX
        ax.plot(x[m], y[m] / n * 100.0, lw=1.0, color=col, label=f"{lab}, median {med}, {ge5 / n * 100:.1f}% ≥ 5")
        lines.append(f"{lab}\t{n}\t{mean:.2f}\t{med}\t{ge5}\t{ge5 / n * 100:.2f}")
    ax.axvline(5, color="#444444", lw=0.6, ls="--")
    ax.set_xlim(0, XMAX); ax.set_ylim(bottom=0)
    ax.set_xlabel("Read coverage per CpG site"); ax.set_ylabel("Sites (%)")
    ax.legend(frameon=False, loc="upper right", handlelength=1.2)
    fig.savefig(stem + ".pdf"); fig.savefig(stem + ".png", dpi=300)
    open(stem + "_stats.tsv", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines)); print(f"wrote {stem}.pdf/.png  {PT} pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
