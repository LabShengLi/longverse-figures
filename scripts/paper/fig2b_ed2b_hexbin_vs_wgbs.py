#!/usr/bin/env python3
"""Panel C of New Figure 2: per-site methylation agreement, as hexbin scatter.

This replaces the earlier "agreement by coverage" curve. That curve reported one
correlation per coverage bin, which compressed 1.6 million sites into seven numbers and
hid both the shape of the agreement and the sites that disagree. A hexbin scatter shows
every site and still reads at figure size, and a single Pearson r per panel is the number
the reader wants.

Three panels, drawn by one function so that anything visible is a difference in the data
and not in the drawing:

    human command line  vs WGBS      does the person's run agree with the orthogonal assay
    agent               vs WGBS      does the agent's run agree with it equally well
    human               vs agent     do the two arms agree with each other

The third is the one that answers "did the agent drive the pipeline correctly", and it is
the strictest of the three: WGBS is a different assay on different molecules, so perfect
agreement with it is not expected from anyone, while the two arms ran the same pipeline on
the same reads with the same model and should be identical.

Frozen parameters, as agreed for the manuscript:
    WGBS            no coverage filter
    long read       min coverage 5
    strands         not merged; each strand-specific CpG is its own point

Joining on position alone is unambiguous here precisely because strands are not merged:
the + and - site of a CpG sit at different coordinates in both file types.

Usage:
    53_make_hexbin_panel.py <human_perSite.bed.gz> <agent_perSite.bed.gz> <wgbs.cov.gz> <outdir>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_style
from matplotlib.colors import LogNorm
from scipy import stats

FONT_DIR = Path(os.environ.get("LV_FONTS", "/project2/sli68423_1316/users/yang/software/fonts"))
FONT_USED = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf", "ariali.ttf"):
    if (FONT_DIR / t).is_file():
        font_manager.fontManager.addfont(str(FONT_DIR / t))
if (FONT_DIR / "arial.ttf").is_file():
    FONT_USED = "Arial"
panel_style.apply(plt, FONT_USED)

MIN_COV_LONGREAD = 5
GRIDSIZE = 60


def load_persite(path: Path, name: str) -> pd.DataFrame:
    """nanome per-site BED: chrom, start0, end, ., ., strand, methfreq(0-1), coverage."""
    df = pd.read_csv(path, sep="\t", header=None, compression="gzip",
                     usecols=[0, 1, 5, 6, 7],
                     names=["chrom", "start0", "strand", "freq", "cov"])
    df["pos"] = df["start0"] + 1              # to 1-based, matching the WGBS file
    df = df[df["cov"] >= MIN_COV_LONGREAD]
    df[name] = df["freq"] * 100.0             # to percent, matching the WGBS file
    return df[["chrom", "pos", name]]


def load_wgbs(path: Path, name: str) -> pd.DataFrame:
    """Bismark coverage: chrom, start1, end1, percent, n_methylated, n_unmethylated.

    No coverage filter is applied, by agreement. Column 4 is already a percentage, so it
    is used as it stands rather than recomputed from columns 5 and 6.
    """
    df = pd.read_csv(path, sep="\t", header=None, compression="gzip",
                     usecols=[0, 1, 3], names=["chrom", "pos", name])
    return df


def panel(ax, x, y, xlabel, ylabel, title, norm=None):
    """Draw one hexbin. `norm` is passed in so panels that share a colour bar share a scale.

    Each hexbin would otherwise build its own LogNorm from its own counts, and a single
    colour bar next to three such panels would describe only the first of them. The two
    WGBS panels are the ones a reader compares directly, so they are given one shared norm
    and one colour bar; the human-vs-agent panel concentrates the same number of sites onto
    a diagonal, reaching per-bin counts an order of magnitude higher, so forcing it onto
    that scale would saturate it. It gets its own colour bar instead.
    """
    r, p = stats.pearsonr(x, y)
    hb = ax.hexbin(x, y, gridsize=GRIDSIZE, bins=None, norm=norm or LogNorm(),
                   cmap="viridis", mincnt=1, linewidths=0)
    ax.plot([0, 100], [0, 100], color="0.35", lw=0.6, ls="--", zorder=3)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-2, 102)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    # The correlation goes in the title rather than in a box inside the axes. A boxed
    # annotation was tried first and placed bottom right, but in the two WGBS panels that
    # corner is not empty: it holds the sites WGBS calls methylated and the long reads do
    # not, which are exactly the sites a reader looks for. Covering them to display a
    # number that has no position on the axes was the wrong trade.
    ax.set_title(f"{title}\nr = {r:.4f}, n = {len(x):,}", pad=4, fontsize=8)
    return hb, r, p, len(x)


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    human_p, agent_p, wgbs_p, outdir = (Path(a) for a in sys.argv[1:5])
    # The two arms used different basecalling models, and that is the whole reason the
    # third panel is a cloud rather than a line. Naming the model on the axis keeps a
    # reader from reading the spread as agent error.
    hlab = os.environ.get("HUMAN_LABEL", "Human command line")
    alab = os.environ.get("AGENT_LABEL", "Agent")
    outdir.mkdir(parents=True, exist_ok=True)

    human = load_persite(human_p, "human")
    agent = load_persite(agent_p, "agent")
    wgbs = load_wgbs(wgbs_p, "wgbs")
    print(f"sites after filtering: human {len(human):,}  agent {len(agent):,}  wgbs {len(wgbs):,}")

    hw = human.merge(wgbs, on=["chrom", "pos"], how="inner")
    aw = agent.merge(wgbs, on=["chrom", "pos"], how="inner")
    ha = human.merge(agent, on=["chrom", "pos"], how="inner")
    print(f"overlaps: human-wgbs {len(hw):,}  agent-wgbs {len(aw):,}  human-agent {len(ha):,}")

    # One shared colour scale for the two WGBS panels, found by drawing them once on a
    # throwaway figure and taking the larger of the two maxima.
    probe_fig, probe_ax = plt.subplots(1, 2)
    hi = 1
    for ax_p, (xv, yv) in zip(probe_ax, ((hw["wgbs"], hw["human"]), (aw["wgbs"], aw["agent"]))):
        counts = ax_p.hexbin(xv.values, yv.values, gridsize=GRIDSIZE,
                             mincnt=1, linewidths=0).get_array()
        hi = max(hi, float(counts.max()))
    plt.close(probe_fig)
    wgbs_norm = LogNorm(vmin=1, vmax=hi)

    # Drawn at the size it is placed at in the deck, 6.54 x 2.30 inches. Drawing it larger
    # and letting PowerPoint shrink it scaled the 8 pt axis labels below 5 pt.
    fig, axes = plt.subplots(1, 3, figsize=(6.54, 2.30), constrained_layout=True)
    out = []
    hb1, r1, p1, n1 = panel(axes[0], hw["wgbs"].values, hw["human"].values,
                            f"WGBS methylation (%)", f"{hlab} (%)",
                            "Human vs WGBS", norm=wgbs_norm)
    out.append(("human_vs_wgbs", r1, p1, n1))
    _, r2, p2, n2 = panel(axes[1], aw["wgbs"].values, aw["agent"].values,
                          f"WGBS methylation (%)", f"{alab} (%)", "Agent vs WGBS",
                          norm=wgbs_norm)
    out.append(("agent_vs_wgbs", r2, p2, n2))
    hb3, r3, p3, n3 = panel(axes[2], ha["human"].values, ha["agent"].values,
                            f"{hlab} (%)", f"{alab} (%)", "Human vs agent")
    out.append(("human_vs_agent", r3, p3, n3))

    cb = fig.colorbar(hb1, ax=[axes[0], axes[1]], location="right",
                      fraction=0.030, pad=0.01)
    cb.set_label("CpG sites per bin", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    cb3 = fig.colorbar(hb3, ax=axes[2], location="right", fraction=0.060, pad=0.01)
    cb3.set_label("CpG sites per bin", fontsize=7)
    cb3.ax.tick_params(labelsize=6)

    for ext in ("pdf", "png"):
        fig.savefig(outdir / f"panel_hexbin_vs_wgbs.{ext}")
    plt.close(fig)

    # The same three comparisons again, one file each, so the deck can put the person's
    # plot on the left and the agent's on the right instead of in one strip. Each is drawn
    # at the size it is placed at, and the two WGBS panels keep the shared colour scale so
    # that a colour means the same number on both sides of the figure.
    # Short axis labels and no colour bar. At 12 pt neither "WGBS methylation (%)" nor a
    # colour bar fits beside a 2.3 inch axis in a 3 inch panel, and the density scale is
    # the same in every one of them, so it is stated once in the figure caption instead.
    # The correlation moves into the title, where it needs no space of its own.
    singles = [
        ("panel_hexbin_human_vs_wgbs", hw["wgbs"].values, hw["human"].values,
         "WGBS (%)", "ONT (%)", wgbs_norm),
        ("panel_hexbin_agent_vs_wgbs", aw["wgbs"].values, aw["agent"].values,
         "WGBS (%)", "ONT (%)", wgbs_norm),
        ("panel_hexbin_human_vs_agent", ha["human"].values, ha["agent"].values,
         "Human (%)", "Agent (%)", None),
    ]
    for name, xv, yv, xl, yl, nrm in singles:
        f1, a1 = plt.subplots(figsize=(3.05, 2.95), constrained_layout=True)
        r1, p1 = stats.pearsonr(xv, yv)
        a1.hexbin(xv, yv, gridsize=GRIDSIZE, norm=nrm or LogNorm(), cmap="viridis",
                  mincnt=1, linewidths=0)
        a1.plot([0, 100], [0, 100], color="0.35", lw=0.9, ls="--", zorder=3)
        a1.set_xlim(-2, 102); a1.set_ylim(-2, 102)
        a1.set_xticks([0, 50, 100]); a1.set_yticks([0, 50, 100])
        a1.set_xlabel(xl); a1.set_ylabel(yl)
        a1.set_title(f"r = {r1:.4f}")
        for ext in ("pdf", "png"):
            f1.savefig(outdir / f"{name}.{ext}")
        plt.close(f1)
        print(f"  wrote {name}")

    csv = outdir.parent / "source_data" / "panel_hexbin_vs_wgbs.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    with open(csv, "w") as f:
        f.write("comparison,pearson_r,p_value,n_sites,min_cov_longread,wgbs_filter,strands\n")
        for name, r, p, n in out:
            f.write(f"{name},{r:.6f},{p:.3e},{n},{MIN_COV_LONGREAD},none,not_merged\n")
    print(f"wrote {outdir / 'panel_hexbin_vs_wgbs.pdf'}")
    print(f"wrote {csv}")
    for name, r, p, n in out:
        print(f"  {name:18s} r={r:.6f}  n={n:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
