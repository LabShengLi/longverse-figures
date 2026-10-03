"""Every panel of the LongVerse figures, redrawn from the numbers each one draws.

The point of this module is that nothing here reads a BAM, a per-site table or anything
else measured in gigabytes. Each function takes a small file out of ``data/`` and returns a
matplotlib figure. That is what makes the repository runnable in a browser on 2 GB of RAM.

Where the data came from, and why it is this small:

    profiles, costs, tables    already the drawn values: a TSS profile is 81 rows
    hexbins                    the hexagons matplotlib would have computed, exported once
                               from the 60-million-row point tables with the same
                               gridsize=100 and extent (0,100,0,100)
    ideograms                  the DMRs that clear |meth.diff| >= 50 and q <= 0.01, which
                               is 45,339 and 21,609 rows out of 13 million tiles
    heatmaps, Venn             the plotdf and the counts the original panels wrote out

The paper's ideograms and heatmaps were drawn in R. These are matplotlib redraws of the
identical numbers, so they are equivalent, not byte-identical. The R originals are in the
main repository under hpc_test/paper_scripts/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm

DATA = Path(__file__).resolve().parent.parent / "data"

# Nature Methods: 183 mm wide, 7 pt text. Kept here so every panel agrees.
MM = 1 / 25.4
PAGE_W_IN = 183 * MM
BASE_PT = 7
HYPER, HYPO = "#CC79A7", "#0072B2"
ONT_C, PB_C, WGBS_C = "#0072B2", "#D55E00", "#666666"


def style():
    plt.rcParams.update({
        "font.size": BASE_PT, "axes.labelsize": BASE_PT, "axes.titlesize": BASE_PT,
        "xtick.labelsize": BASE_PT, "ytick.labelsize": BASE_PT, "legend.fontsize": BASE_PT,
        "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "figure.dpi": 130, "savefig.dpi": 300, "pdf.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    })


# --------------------------------------------------------------------------- hexbins
def hexbin(key: str, xlabel: str, ylabel: str, stats: dict | None = None, ax=None):
    """Redraw an exported hexbin. The hexagons are the ones the original panel drew."""
    df = pd.read_csv(DATA / "plot_layer" / "hexbin" / f"{key}.csv.gz")
    if ax is None:
        _, ax = plt.subplots(figsize=(2.3, 1.9))

    # One hexagon per row, at the centres matplotlib computed. Drawing them directly, rather
    # than re-running hexbin on scattered points, is what keeps this exact.
    dx = 100.0 / 100 / 2          # gridsize=100 over extent 0-100
    dy = dx * 2 / np.sqrt(3)
    angles = np.arange(6) * np.pi / 3 + np.pi / 6
    unit = np.c_[np.cos(angles) * dx * 1.16, np.sin(angles) * dy * 1.16]
    verts = [unit + (x, y) for x, y in zip(df.hex_x, df.hex_y)]

    coll = PolyCollection(verts, array=df["count"].to_numpy(),
                          norm=LogNorm(vmin=max(df["count"].min(), 1), vmax=df["count"].max()),
                          cmap="inferno", linewidths=0)
    ax.add_collection(coll)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_aspect("equal")
    cb = ax.figure.colorbar(coll, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("CpG sites", size=BASE_PT)
    cb.ax.tick_params(labelsize=BASE_PT)
    if stats:
        # Inset far enough that the glyph does not sit on the spine, and on a panel so it
        # stays readable over the dark end of the colour map.
        ax.text(0.055, 0.945, f"r = {stats['r']:.3f}\nn = {stats['n']:,}",
                transform=ax.transAxes, va="top", ha="left", fontsize=BASE_PT,
                bbox=dict(facecolor="white", alpha=0.75, edgecolor="none",
                          boxstyle="round,pad=0.18"))
    return ax


def read_hexbin_stats(path: Path) -> dict:
    """Pull r and n out of one of the *_stats.txt files the original panels wrote.

    These files carry pearson_r TWICE, once under "# Methylation frequency (%)" and again
    under "# Coverage". Taking the last one labels a methylation panel with the coverage
    correlation: 0.18 where the panel shows 0.95. So the section header is tracked and only
    the methylation block is read. The count is called n_data_points, not n.
    """
    out: dict = {}
    section = None
    for line in Path(path).read_text().splitlines():
        if line.startswith("#"):
            section = line.lower()
            continue
        if "\t" not in line:
            continue
        k, v = line.split("\t", 1)
        if k == "pearson_r" and section and "methylation" in section:
            out["r"] = float(v)
        elif k in ("n_data_points", "n_sites", "n_shared_sites"):
            out["n"] = int(float(v))
    missing = {"r", "n"} - set(out)
    if missing:
        raise KeyError(f"{path.name}: no {sorted(missing)} found; "
                       f"is the methylation section still labelled '# Methylation'?")
    return out


# ------------------------------------------------------------------------- ideograms
# chm13v2.0 autosome lengths. The ideogram needs nothing else from the reference.
CHM13 = {
    "chr1": 248387328, "chr2": 242696752, "chr3": 201105948, "chr4": 193574945,
    "chr5": 182045439, "chr6": 172126628, "chr7": 160567428, "chr8": 146259331,
    "chr9": 150617247, "chr10": 134758134, "chr11": 135127769, "chr12": 133324548,
    "chr13": 113566686, "chr14": 101161492, "chr15": 99753195, "chr16": 96330374,
    "chr17": 84276897, "chr18": 80542538, "chr19": 61707364, "chr20": 66210255,
    "chr21": 45090682, "chr22": 51324926,
}


def ideogram(key: str, title: str, ax=None):
    """Haplotype DMRs along the autosomes: hyper above the line, hypo below."""
    df = pd.read_csv(DATA / "plot_layer" / "ideogram" / f"{key}.csv.gz")
    chroms = [c for c in CHM13 if c in set(df["chr"])]
    if ax is None:
        _, ax = plt.subplots(figsize=(3.5, 3.3))

    for i, chrom in enumerate(chroms):
        y0 = len(chroms) - i
        ax.add_patch(plt.Rectangle((0, y0 - 0.38), CHM13[chrom] / 1e6, 0.76,
                                   facecolor="#EEEEEE", edgecolor="none", zorder=0))
        sub = df[df["chr"] == chrom]
        mid = (sub["start"] + sub["end"]) / 2 / 1e6
        up = sub["direction"] == "hyper"
        ax.scatter(mid[up], np.full(up.sum(), y0 + 0.19), s=0.4, c=HYPER, lw=0, zorder=2)
        ax.scatter(mid[~up], np.full((~up).sum(), y0 - 0.19), s=0.4, c=HYPO, lw=0, zorder=2)

    ax.set_yticks(range(1, len(chroms) + 1))
    ax.set_yticklabels(reversed(chroms))
    ax.set_xlabel("Genomic coordinate (Mb)")
    ax.set_xlim(0, max(CHM13[c] for c in chroms) / 1e6)
    ax.set_ylim(0.4, len(chroms) + 0.7)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False)
    # The counts belong in the title, not floating beside it: placed as separate text they
    # overlapped the title whenever the panel got narrow.
    n_hy = int((df["direction"] == "hyper").sum())
    n_ho = int((df["direction"] == "hypo").sum())
    ax.set_title(f"{title}\nhyper {n_hy:,}   hypo {n_ho:,}", fontsize=BASE_PT)
    handles = [plt.Line2D([], [], marker="o", ls="", ms=3, color=HYPER, label="hyper"),
               plt.Line2D([], [], marker="o", ls="", ms=3, color=HYPO, label="hypo")]
    ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=BASE_PT)
    return ax


# --------------------------------------------------------------------------- curves
def profile(csv: Path, cols: dict[str, str], xlabel: str, ylabel: str,
            centre_label: str = "0", ax=None):
    """A mean-methylation profile around a feature. One line per column."""
    df = pd.read_csv(csv) if str(csv).endswith(".csv") else pd.read_csv(csv, sep="\t")
    xcol = df.columns[0]
    if ax is None:
        _, ax = plt.subplots(figsize=(2.3, 1.7))
    for col, (label, colour) in cols.items():
        if col in df.columns:
            ax.plot(df[xcol], df[col], label=label, color=colour, lw=1.0)
    ax.axvline(0, color="#999999", lw=0.5, ls=":")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, loc="best")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return ax


def bars(csv: Path, xcol: str, ycol: str, xlabel: str, ylabel: str,
         highlight: str | None = None, ax=None):
    """A simple bar chart; `highlight` names one row to colour differently."""
    df = pd.read_csv(csv)
    if "drawn_in_panel" in df.columns:
        # Source data carries series that were measured but not drawn. Respect the flag.
        df = df[df["drawn_in_panel"].astype(str).str.lower().isin(("yes", "true", "1"))]
    if ax is None:
        _, ax = plt.subplots(figsize=(2.3, 1.7))
    colours = ["#CC79A7" if (highlight and str(v) == highlight) else "#0072B2"
               for v in df[xcol]]
    ax.bar(df[xcol].astype(str), df[ycol], color=colours, width=0.68)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    for lab in ax.get_xticklabels():
        lab.set_ha("right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return ax


def heatmap(csv: Path, title: str, ax=None):
    """The imprinting-control-region heatmaps, from the plotdf the originals wrote."""
    df = pd.read_csv(csv)
    rowc, colc, valc = df.columns[0], df.columns[1], df.columns[2]
    mat = df.pivot(index=rowc, columns=colc, values=valc)
    if ax is None:
        _, ax = plt.subplots(figsize=(2.2, 3.0))
    im = ax.imshow(mat.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(mat.shape[1])); ax.set_xticklabels(mat.columns, rotation=30, ha="right")
    ax.set_yticks(range(mat.shape[0])); ax.set_yticklabels(mat.index)
    ax.set_title(title)
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("HP1 - HP2", size=BASE_PT)
    cb.ax.tick_params(labelsize=BASE_PT)
    return ax


def venn_counts(tsv: Path, ax=None):
    """ONT-only, PacBio-only and shared CpG counts, drawn as two circles."""
    from matplotlib_venn import venn2
    vals = {}
    for line in Path(tsv).read_text().splitlines():
        parts = line.replace(",", "\t").split("\t")
        if len(parts) >= 2 and parts[1].strip().replace("_", "").isdigit():
            vals[parts[0].strip()] = int(parts[1].strip())
    if ax is None:
        _, ax = plt.subplots(figsize=(2.3, 1.9))
    both = vals.get("both", vals.get("shared", 0))
    ont = vals.get("ont_only", vals.get("ONT_only", 0))
    pb = vals.get("pacbio_only", vals.get("PacBio_only", 0))
    venn2(subsets=(ont, pb, both), set_labels=("ONT", "PacBio"), ax=ax)
    return ax


def table_panel(rows: list[list[str]], header: list[str], ax=None):
    """A small table, used where the figure reports a run rather than a measurement."""
    if ax is None:
        _, ax = plt.subplots(figsize=(3.4, 1.2))
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=header, loc="center", cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(BASE_PT); t.scale(1, 1.3)
    for (r, _), cell in t.get_celld().items():
        cell.set_linewidth(0.3)
        if r == 0:
            cell.set_text_props(weight="bold")
    return ax


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


# ------------------------------------------------- deeptools and long-format readers
def profile_deeptools(tsv: Path, cols: dict, xlabel: str, ylabel: str,
                      span_kb: float = 2.0, ax=None):
    """A profile written by deeptools --outFileNameData, which is not a tidy table.

    Row 1 is 'bin labels', row 2 is 'bins', and each remaining row is one track: column 1
    the track name, column 2 the region set, columns 3 onward the binned means. The header
    rows are told apart by their SECOND column being empty, which is the only field that
    distinguishes them reliably - row 1 and row 3 both start with a word.
    """
    series, n_bins = {}, 0
    for line in Path(tsv).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or parts[1].strip() == "":
            continue                      # a header row, not a track
        name = parts[0].strip()
        vals = [float(v) for v in parts[2:] if v.strip() != ""]
        if vals:
            series[name] = np.asarray(vals)
            n_bins = max(n_bins, len(vals))
    if not series:
        raise ValueError(f"{Path(tsv).name}: no track rows found")

    x = np.linspace(-span_kb, span_kb, n_bins)
    if ax is None:
        _, ax = plt.subplots(figsize=(2.5, 1.9))
    for key, (label, colour) in cols.items():
        if key in series:
            ax.plot(x, series[key], label=label, color=colour, lw=1.0)
    ax.axvline(0, color="#999999", lw=0.5, ls=":")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return ax


def lines_by_series(csv: Path, xcol: str, ycol: str, series_col: str,
                    xlabel: str, ylabel: str, highlight: str | None = None, ax=None):
    """A long-format table drawn as one line per series, e.g. accuracy by read depth."""
    df = pd.read_csv(csv) if str(csv).endswith(".csv") else pd.read_csv(csv, sep="\t")
    if ax is None:
        _, ax = plt.subplots(figsize=(2.5, 1.8))
    order = list(dict.fromkeys(df[series_col]))
    palette = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#666666"]
    xs = list(dict.fromkeys(df[xcol].astype(str)))
    for i, name in enumerate(order):
        sub = df[df[series_col] == name]
        is_hi = highlight is not None and str(name) == highlight
        ax.plot([xs.index(str(v)) for v in sub[xcol].astype(str)], sub[ycol],
                marker="o", ms=2.5, lw=1.6 if is_hi else 1.0,
                color="#CC79A7" if is_hi else palette[i % len(palette)],
                label=str(name), zorder=3 if is_hi else 2)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs, rotation=0)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=BASE_PT - 1, loc="best")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return ax


def icr_haplotypes(csv: Path, arm: str = "human", ax=None):
    """HP1 against HP2 methylation at each imprinting control region, one pair of bars."""
    df = pd.read_csv(csv)
    hp1, hp2 = f"{arm}_HP1_pct", f"{arm}_HP2_pct"
    df = df.sort_values(hp1)
    y = np.arange(len(df))
    if ax is None:
        _, ax = plt.subplots(figsize=(2.6, max(1.6, 0.14 * len(df))))
    ax.barh(y - 0.19, df[hp1], height=0.36, color=HYPER, label="HP1")
    ax.barh(y + 0.19, df[hp2], height=0.36, color=HYPO, label="HP2")
    ax.set_yticks(y); ax.set_yticklabels(df["region"], fontsize=BASE_PT - 1)
    ax.set_xlabel("Methylation (%)")
    ax.legend(frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return ax
