#!/usr/bin/env python3
"""Redraw a per-site hexbin from its saved point table at Nature Methods size: 7 pt text on
a canvas of the width the panel occupies on the 183 mm page.

Same data as fig2/41_replot_hexbin_12pt.py (the point tables written by
plot_perSite_cov_hexbin_compare.py), same hexbin and colour scale; only the typography and
the canvas change. Integer colour-bar ticks, so no mathtext superscript falls below the
floor. The panel reports the r and n read from the stats file next to the table and refuses
if the table length disagrees with that n.

Usage: 11_hexbin_nm.py <points.csv.gz> <stats.txt> <out_stem> [fig_w_in fig_h_in]
Env:   PANEL_MIN_PT (default 7)          (env: conda/envs/py39_v2)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogLocator

PT = float(os.environ.get("PANEL_MIN_PT", 7))
FONT_DIR = os.environ.get("LONGVERSE_FONT_DIR", "/project2/sli68423_1316/users/yang/software/fonts")
family = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"):
    fp = os.path.join(FONT_DIR, t)
    if os.path.isfile(fp):
        matplotlib.font_manager.fontManager.addfont(fp)
if os.path.isfile(os.path.join(FONT_DIR, "arial.ttf")):
    family = "Arial"
plt.rcParams.update({"font.family": family, "font.size": PT, "axes.labelsize": PT, "axes.titlesize": PT,
                     "xtick.labelsize": PT, "ytick.labelsize": PT, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "xtick.major.size": 2.0, "ytick.major.size": 2.0})


def read_stats(path: Path) -> dict:
    out, section = {}, None
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            section = line.lower(); continue
        if "\t" not in line:
            continue
        k, v = line.split("\t", 1)
        if k == "pearson_r" and section and "methylation" in section:
            out["meth_r"] = float(v)
        elif k not in ("pearson_r", "pearson_p_value"):
            out[k] = v
    return out


def main() -> int:
    if len(sys.argv) not in (4, 6):
        print(__doc__); return 2
    points, stats_path, stem = sys.argv[1:4]
    fw, fh = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) == 6 else (2.30, 1.55)
    st = read_stats(Path(stats_path))
    n, r = int(st["n_data_points"]), st["meth_r"]
    # column 0 is site_key; the table stores group1 (y axis, as drawn) then group2 (x axis)
    df = pd.read_csv(points, usecols=[1, 2], dtype="float32")
    if len(df) != n:
        raise SystemExit(f"REFUSED: stats says n = {n:,} but the table holds {len(df):,} rows")
    ycol, xcol = df.columns[0], df.columns[1]
    fig, ax = plt.subplots(figsize=(fw, fh), constrained_layout=True)
    # edges drawn in the face colour: with no edge the rasteriser leaves a white mesh between hexes
    hb = ax.hexbin(df[xcol].to_numpy(), df[ycol].to_numpy(), gridsize=100, cmap="inferno", norm=LogNorm(),
                   edgecolors="face", linewidths=0.3)
    cb = fig.colorbar(hb, ax=ax, pad=0.02, fraction=0.06)
    cb.set_label("Sites", fontsize=PT)
    cb.ax.yaxis.set_major_locator(LogLocator(base=10.0))
    # only decades inside the data range; the locator also proposes ticks far above the maximum
    vmin, vmax = hb.norm.vmin, hb.norm.vmax
    ticks = [t for t in cb.get_ticks() if 1 <= t <= vmax]
    if len(ticks) > 4:
        ticks = ticks[::2]
    cb.set_ticks(ticks); cb.set_ticklabels([f"{int(t):,}" for t in ticks])
    cb.ax.tick_params(labelsize=PT, width=0.6, length=2.0)
    cb.outline.set_linewidth(0.6)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.set_xticks([0, 50, 100]); ax.set_yticks([0, 50, 100])
    ax.set_xlabel(f"{xcol} methylation (%)"); ax.set_ylabel(f"{ycol} methylation (%)")
    ax.set_title(f"r = {r:.3f}, n = {n:,}", fontsize=PT)
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    print(f"wrote {stem}.pdf/.png  y={ycol} x={xcol} r={r:.4f} n={n:,}  {PT} pt, {fw} x {fh} in")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
