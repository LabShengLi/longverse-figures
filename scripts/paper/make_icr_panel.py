#!/usr/bin/env python3
"""New Figure 3, the per-region panel: every imprinted control region on chromosome 20.

One row per region, the two haplotypes as a pair of points joined by a line. An imprinted
region should show one haplotype near fully methylated and the other near unmethylated; a
failed haplotype split shows both near the middle.

The two arms are drawn on the same axes rather than as two subplots. They produced
identical values, so side-by-side panels would be two copies of one picture; overlaying the
agent as open markers on the person's filled ones shows the agreement instead of asserting
it, and any disagreement would be visible as a marker that misses its point.

Usage: 57_make_icr_panel.py <human.csv> <agent.csv> <outdir>
"""
from __future__ import annotations

import csv
import sys
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_style

FONT_DIR = Path(os.environ.get("LV_FONTS", "/project2/sli68423_1316/users/yang/software/fonts"))
FONT_USED = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf", "ariali.ttf"):
    if (FONT_DIR / t).is_file():
        font_manager.fontManager.addfont(str(FONT_DIR / t))
if (FONT_DIR / "arial.ttf").is_file():
    FONT_USED = "Arial"
panel_style.apply(plt, FONT_USED)
HP1_C, HP2_C = "#D55E00", "#0072B2"


def short_name(name: str) -> str:
    """Region names that fit a 12 pt y axis on a 3.6 inch panel.

    The full names carry two gene symbols joined by a comma, which at 12 pt is wider than
    the plotting area it labels. The first symbol identifies the region unambiguously
    within chromosome 20 and the full names are in the source data CSV.
    """
    return name.split(",")[0].strip()


def load(path: Path) -> list[dict]:
    """Read the per-region CSV, keeping regions that actually have a value."""
    out = []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("Name") or "").strip().strip('"').replace("\t", ", ")
            try:
                hp1, hp2 = float(r["HP1_avg"]), float(r["HP2_avg"])
            except (TypeError, ValueError):
                out.append({"name": name, "hp1": None, "hp2": None,
                            "n1": r.get("HP1_ncpg"), "n2": r.get("HP2_ncpg")})
                continue
            out.append({"name": name, "hp1": hp1 * 100, "hp2": hp2 * 100,
                        "n1": r.get("HP1_ncpg"), "n2": r.get("HP2_ncpg")})
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    hp, ap, outdir = (Path(a) for a in sys.argv[1:4])
    outdir.mkdir(parents=True, exist_ok=True)
    human, agent = load(hp), load(ap)
    assert [r["name"] for r in human] == [r["name"] for r in agent], "region lists differ"

    fig, ax = plt.subplots(figsize=(9.6, 2.45))
    ys = list(range(len(human)))[::-1]
    n_missing = 0
    for y, h, a in zip(ys, human, agent):
        if h["hp1"] is None:
            n_missing += 1
            ax.text(50, y, "no CpG at coverage 5 or more", ha="center", va="center",
                    fontsize=6.5, color="0.55", style="italic")
            continue
        ax.plot([h["hp1"], h["hp2"]], [y, y], color="0.75", lw=1.0, zorder=1)
        ax.scatter([h["hp1"]], [y], s=42, color=HP1_C, zorder=3)
        ax.scatter([h["hp2"]], [y], s=42, color=HP2_C, zorder=3)
        # the agent's values, drawn on top; a mismatch would show as a ring off its dot
        ax.scatter([a["hp1"]], [y], s=90, facecolors="none", edgecolors=HP1_C,
                   lw=0.9, zorder=4)
        ax.scatter([a["hp2"]], [y], s=90, facecolors="none", edgecolors=HP2_C,
                   lw=0.9, zorder=4)
        ax.text(101.5, y, f"{h['n1']} / {h['n2']} CpG", ha="left", va="center",
                fontsize=6, color="0.45")

    ax.set_yticks(ys)
    ax.set_yticklabels([r["name"] for r in human], fontsize=7)
    ax.set_xlim(-3, 103)
    # headroom at the top for the legend, which used to sit below the axes and added
    # half an inch to a figure that is already tall
    ax.set_ylim(-0.6, len(human) + 0.35)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Average methylation in the region (%)")
    ax.axvline(50, color="0.88", lw=0.8, zorder=0)
    ax.set_title("Imprinted control regions on chromosome 20, by haplotype", pad=6)

    handles = [
        Line2D([], [], marker="o", ls="", color=HP1_C, markersize=6, label="HP1"),
        Line2D([], [], marker="o", ls="", color=HP2_C, markersize=6, label="HP2"),
        Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor="0.3",
               markersize=9, label="agent (open), person (filled)"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, 1.02), ncol=3, fontsize=6.5,
              handletextpad=0.4, columnspacing=1.6)

    for ext in ("pdf", "png"):
        fig.savefig(outdir / f"panel_icr_by_region.{ext}")
    plt.close(fig)

    # One plot per arm as well, so the deck can put the person on the left and the agent on
    # the right. Drawn on the same x axis and the same row order, so a difference between
    # the two sides would be a difference in the data.
    for tag, rowset in (("human", human), ("agent", agent)):
        f1, a1 = plt.subplots(figsize=(2.88, 2.55))
        for y, r in zip(ys, rowset):
            if r["hp1"] is None:
                a1.text(50, y, "no coverage", ha="center", va="center",
                        color="0.55", style="italic")
                continue
            a1.plot([r["hp1"], r["hp2"]], [y, y], color="0.75", lw=1.0, zorder=1)
            a1.scatter([r["hp1"]], [y], s=34, color=HP1_C, zorder=3)
            a1.scatter([r["hp2"]], [y], s=34, color=HP2_C, zorder=3)
        a1.set_yticks(ys)
        a1.set_yticklabels([short_name(r["name"]) for r in rowset])
        a1.set_xlim(-3, 103)
        a1.set_ylim(-0.6, len(rowset) + 0.35)
        a1.set_xticks([0, 25, 50, 75, 100])
        a1.set_xlabel("Methylation (%)")
        a1.axvline(50, color="0.88", lw=0.8, zorder=0)
        a1.set_title("Imprinted regions", pad=4)
        a1.legend(handles=[
            Line2D([], [], marker="o", ls="", color=HP1_C, markersize=5, label="HP1"),
            Line2D([], [], marker="o", ls="", color=HP2_C, markersize=6, label="HP2")],
            frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)
        for ext in ("pdf", "png"):
            f1.savefig(outdir / f"panel_icr_{tag}.{ext}")
        plt.close(f1)
        print(f"  wrote panel_icr_{tag}")

    csv_out = outdir.parent / "source_data" / "panel_icr_by_region.csv"
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["region", "human_HP1_pct", "human_HP2_pct", "agent_HP1_pct",
                    "agent_HP2_pct", "HP1_ncpg", "HP2_ncpg", "identical"])
        for h, a in zip(human, agent):
            same = (h["hp1"] == a["hp1"] and h["hp2"] == a["hp2"])
            w.writerow([h["name"], h["hp1"], h["hp2"], a["hp1"], a["hp2"],
                        h["n1"], h["n2"], same])
    print(f"  {len(human)} regions, {n_missing} without coverage")
    print(f"  wrote {outdir / 'panel_icr_by_region.pdf'} and {csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
