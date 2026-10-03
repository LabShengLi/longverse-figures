#!/usr/bin/env python3
"""Generate the notebooks, so the code in them is never hand-edited out of step with
scripts/panels.py.

Each notebook is deliberately thin: a cell per panel, three or four lines each, calling a
function from panels.py. The reasoning lives in panels.py where it can be tested; the
notebook is the thing a reader scrolls through.

Usage:  build_notebooks.py [outdir]        default ./notebooks
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HEADER = """# LongVerse figures

Every panel below is drawn from a small file in `data/`. Nothing here reads a BAM or a
whole-genome table, which is why it runs in a browser.

Run all cells: **Run -> Run All Cells**. The figures appear inline and are also written to
`figures/` as PDF and PNG.
"""

SETUP = """import sys; sys.path.insert(0, "../scripts")
from pathlib import Path
import matplotlib.pyplot as plt
import panels as P

P.style()
D = Path("../data"); OUT = Path("../figures"); OUT.mkdir(exist_ok=True)

def save(ax, name):
    fig = ax.figure
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight")
    return fig
"""

# notebook -> [(markdown heading, code)]
FIGS: dict[str, list[tuple[str, str]]] = {
    "01_figure1": [
        ("## Figure 1e. Three callers and their consensus against whole-genome bisulfite sequencing",
         'ax = P.bars(D/"fig1/e_consensus_vs_wgbs.csv", "series", "pearson_r_vs_wgbs",\n'
         '            "", "Pearson r vs WGBS", highlight="Consensus")\n'
         'save(ax, "fig1e_consensus");'),
        ("## Figure 1f. The same comparison split by read depth",
         'ax = P.lines_by_series(D/"fig1/f_consensus_by_coverage.csv", "coverage_bin",\n'
         '                       "pearson_r_vs_wgbs", "series", "Read depth",\n'
         '                       "Pearson r vs WGBS", highlight="Consensus")\n'
         'save(ax, "fig1f_by_coverage");'),
    ],
    "02_figure2": [
        ("## Figure 2b. Mean methylation around transcription start sites, expert and agent",
         'ax = P.profile(D/"fig2/b_tss_profile.csv",\n'
         '               {"human": ("expert", P.ONT_C), "agent_mcp_prompt": ("agent", P.HYPER)},\n'
         '               "Distance from TSS (bp)", "Mean methylation")\n'
         'save(ax, "fig2b_tss");'),
        ("## Figure 2b. Per-site agreement with WGBS\\n"
         "The two arms agree with each other exactly: the agent reproduced the expert's run.",
         'import pandas as pd\n'
         'print(pd.read_csv(D/"fig2/b_persite_vs_wgbs.csv").to_string(index=False))'),
        ("## Figure 2c. Haplotype methylation at the chromosome 20 imprinting control regions",
         'ax = P.icr_haplotypes(D/"fig2/c_icr_by_region.csv", arm="human")\n'
         'save(ax, "fig2c_icr");'),
    ],
    "03_extended_data_fig1": [
        ("## Extended Data Fig. 1a. Agreement with WGBS by read depth, both arms",
         'ax = P.lines_by_series(D/"ed_fig1/a_wgbs_by_coverage.csv", "cov_bin", "PCC", "arm",\n'
         '                       "Read depth", "Pearson r vs WGBS")\n'
         'save(ax, "ed1a_by_coverage");'),
        ("## Extended Data Fig. 1d. Transcription start site profile after phasing",
         'ax = P.profile(D/"ed_fig1/d_tss_after_phasing.csv",\n'
         '               {"human_command_line": ("expert", P.ONT_C), "agent": ("agent", P.HYPER)},\n'
         '               "Distance from TSS (bp)", "Mean methylation")\n'
         'save(ax, "ed1d_tss");'),
        ("## Extended Data Fig. 1c. The agent arm at the same imprinting control regions",
         'ax = P.icr_haplotypes(D/"ed_fig1/c_icr_by_region.csv", arm="agent")\n'
         'save(ax, "ed1c_icr");'),
    ],
    "04_extended_data_fig4": [
        ("## Extended Data Fig. 4a-c. Per-site methylation, every pair of platforms\\n"
         "Each hexagon is one the original panel computed, exported from 56 to 62 million sites.",
         'specs = [("ed4_a_ont_vs_wgbs", "a_ont_vs_wgbs", "WGBS methylation (%)", "ONT methylation (%)"),\n'
         '         ("ed4_b_pacbio_vs_wgbs", "b_pacbio_vs_wgbs", "WGBS methylation (%)", "PacBio methylation (%)"),\n'
         '         ("ed4_c_ont_vs_pacbio", "c_ont_vs_pacbio", "PacBio methylation (%)", "ONT methylation (%)")]\n'
         'fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))\n'
         'for (key, stem, xl, yl), ax in zip(specs, axes):\n'
         '    st = P.read_hexbin_stats(D/f"ed_fig4/hexbin_{stem}_nm_stats.txt")\n'
         '    P.hexbin(key, xl, yl, st, ax=ax)\n'
         'save(axes[0], "ed4abc_hexbins");'),
        ("## Extended Data Fig. 4d,e. Haplotype DMRs along the autosomes\\n"
         "Drawn at |HP1 - HP2| >= 50 percentage points and q <= 0.01, the same cutoff as the paper.",
         'fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6))\n'
         'P.ideogram("ed4_d_ont", "ONT", ax=axes[0])\n'
         'P.ideogram("ed4_e_pacbio", "PacBio", ax=axes[1])\n'
         'save(axes[0], "ed4de_ideograms");'),
        ("## Extended Data Fig. 4f,g. Imprinting control regions, HP1 minus HP2",
         'fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))\n'
         'P.heatmap(D/"ed_fig4/icr_heatmap_novel_nm.plotdf.csv", "Novel ICRs", ax=axes[0])\n'
         'P.heatmap(D/"ed_fig4/icr_heatmap_known_nm.plotdf.csv", "Known ICRs", ax=axes[1])\n'
         'save(axes[0], "ed4fg_icr_heatmaps");'),
    ],
    "05_extended_data_fig5": [
        ("## Extended Data Fig. 5d,e. Methylation around TSS and CTCF sites, three platforms",
         'cols = {"ONT": ("ONT", P.ONT_C), "PacBio": ("PacBio", P.PB_C), "WGBS": ("WGBS", P.WGBS_C)}\n'
         'fig, axes = plt.subplots(1, 2, figsize=(5.2, 1.9))\n'
         'P.profile_deeptools(D/"ed_fig5/TSS_profile_3track_nozero_data.tsv", cols,\n'
         '                    "Distance from TSS (kb)", "Mean methylation", ax=axes[0])\n'
         'P.profile_deeptools(D/"ed_fig5/CTCF_profile_3track_nozero_data.tsv", cols,\n'
         '                    "Distance from CTCF site (kb)", "Mean methylation", ax=axes[1])\n'
         'save(axes[0], "ed5de_profiles");'),
        ("## Extended Data Fig. 5f. ONT against PacBio within eight genomic region classes",
         'regions = ["Promoter", "5UTR", "3UTR", "Exon", "Intron", "Intergenic", "Island", "NonIsland"]\n'
         'fig, axes = plt.subplots(2, 4, figsize=(7.2, 4.2))\n'
         'for reg, ax in zip(regions, axes.ravel()):\n'
         '    P.hexbin(f"ed5_f_{reg}", "PacBio (%)", "ONT (%)", ax=ax)\n'
         '    ax.set_title(reg)\n'
         'save(axes.ravel()[0], "ed5f_region_hexbins");'),
    ],
}


def nb(cells):
    return {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                    "name": "python3"},
                     "language_info": {"name": "python", "version": "3.11"}},
        "nbformat": 4, "nbformat_minor": 5,
    }


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": text.splitlines(keepends=True)}


def main(outdir="notebooks"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    everything = [md(HEADER), code(SETUP)]
    for name, panels in FIGS.items():
        cells = [md(f"# {name.split('_', 1)[1].replace('_', ' ').title()}"), code(SETUP)]
        for heading, body in panels:
            cells += [md(heading), code(body)]
            everything += [md(heading), code(body)]
        (out / f"{name}.ipynb").write_text(json.dumps(nb(cells), indent=1))
        print(f"  wrote {name}.ipynb  ({len(panels)} panels)")
    (out / "00_all_figures.ipynb").write_text(json.dumps(nb(everything), indent=1))
    print(f"  wrote 00_all_figures.ipynb  ({sum(len(v) for v in FIGS.values())} panels)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "notebooks")
