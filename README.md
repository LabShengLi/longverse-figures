# LongVerse figures

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/LabShengLi/longverse-figures/main?urlpath=lab/tree/notebooks)

The figures from *LongVerse: one sentence to the allele-specific methylome, verified
multi-agent AI for Nanopore and PacBio long-read sequencing*, with the code that draws them
and the numbers they are drawn from.

Click the badge and a JupyterLab opens in your browser with everything installed. Open a
notebook and run it. Nothing to download, no account. The first launch builds the image and
takes ten to fifteen minutes; after that it starts in about half a minute.

---

## Contents

    notebooks/     one per figure: the code in the cell, the panel underneath
    scripts/paper/ the panel scripts, as they are in the paper's repository
    data/          what each panel draws, 128 MB
    figures/all/   the batch render, each image named for the figure and panel it is
    figures/       where a run of one notebook writes its PDFs and PNGs, named for the figure

| notebook | figure |
| --- | --- |
| `01_figure1` | Fig. 1e, f - three callers and their consensus |
| `02_figure2` | Fig. 2a, b, c - one sentence reproduces the expert, ONT |
| `03_extended_data_fig1` | ED Fig. 1a, b, c - the remaining ONT panels |
| `04_extended_data_fig2` | ED Fig. 2a, b - PacBio calling |
| `05_extended_data_fig3` | ED Fig. 3a, b - PacBio phasing |
| `06_extended_data_fig4` | ED Fig. 4a-e - ONT, PacBio and WGBS across the genome |
| `07_extended_data_fig5` | ED Fig. 5a-h - coverage, imprinting and regional agreement |
| `08_gnas_region` | the region plot behind Fig. 2c - GNAS, per haplotype |
| `00_all_figures` | draws everything in one go |

The notebooks are committed with their figures, so they can be read on GitHub without
running anything.

## The scripts

Each cell holds the script that drew that panel, taken from the paper's repository and
named here for the display item it draws; a script that serves several items carries all
of them in its name. Edit a line and re-run and you get your edit.

| script (scripts/paper/) | draws |
|---|---|
| `fig1ef_consensus_panels.py` (+ `fig1ef_consensus_data.py`) | Fig. 1e, f |
| `fig2_ed1_ed2_ed3_make_panels.py` (+ `fig2a_ed2a_ed3a_arm_panel.py`, `fig2a_ed2a_ed3a_arm_records.py`) | Fig. 2a, b; ED Fig. 1a; ED Fig. 2; ED Fig. 3 |
| `fig2b_ed2b_hexbin_vs_wgbs.py` | Fig. 2b, ED Fig. 2b hexbins |
| `fig2c_ed1c_ed3b_icr_panel.py` | Fig. 2c, ED Fig. 1c, ED Fig. 3b imprinting regions |
| `fig2c_ed3b_gnas_region_plot.R` | Fig. 2c, ED Fig. 3b GNAS per haplotype (NanoMethViz) |
| `ed1b_ed2a_ed3a_agent_cost.py` | ED Fig. 1b, ED Fig. 2a, ED Fig. 3a |
| `ed4abc_hexbin.py` | ED Fig. 4a-c (the paper's script; here the exported hexagons are drawn, see below) |
| `ed4de_dmr_ideogram.R` | ED Fig. 4d, e |
| `ed5a_cpg_venn.py`, `ed5b_coverage_hist.py` | ED Fig. 5a, b |
| `ed5c_hp_diff_by_region.R` | ED Fig. 5c |
| `ed5de_icr_heatmaps.R` | ED Fig. 5d, e |
| `ed5fg_tss_ctcf_profiles.py` | ED Fig. 5f, g |
| `ed5h_region_hexbins.R` | ED Fig. 5h (as ED Fig. 4a-c, from exported hexagons) |
| `nm_style.py`, `panel_style.py` | the journal's sizes and fonts, imported by the others |

The four R panels are R cells: `rpy2`'s `%%R` magic runs them in the same kernel as the
Python ones. Each differs from its file by one line, marked where it happens, because the
scripts read their arguments from a command line and a notebook has none.

Cells are generated from `scripts/paper/`, and `python scripts/build_notebooks.py --check`
confirms they still match it.

Two panels do not run their script: ED Fig. 4a-c and ED Fig. 5h are drawn from the hexagons
their own `hexbin()` call produced and exported, because the scripts for them read 450 MB and
890 MB inputs. `figures/all/RENDER_LOG.tsv` says which panel was drawn which way. Where a
command line is shown, absolute paths on the shared filesystem read `$LONGVERSE` and
`$RESULTS`.

## The names

Every image is named for the figure and the panel it is: `fig1e_consensus_vs_wgbs.png`,
`ed5c_hp_diff_by_region.png`. The paper's scripts name a file after what it draws, because
that is all they know (`panel_f_consensus.png` is Figure 1e), so `scripts/panel_names.py`
holds the table from the one name to the other, and both the notebooks and the batch
render apply it before anything is shown or kept.

    figures/           what a run of the notebooks writes, figure-named; not committed
    figures/all/       the same panels from the batch render on the paper's machine,
                       committed; FIGURE_PANELS.tsv beside them lists each one with the
                       name its script produced it under
    figures/all/other_renders/   what the scripts produce that no figure places: the
                       versions of a panel with both arms in one plot, where the paper
                       draws one arm at a time

## The data

Whole-genome inputs are not needed to draw a figure, so what is here is what each panel
reads, 196 MB in all.

| | |
| --- | --- |
| per-run evaluation records | 23 to 33 KB each |
| consensus and imprinting tables | 0.6 to 19 KB |
| phased reads at the imprinting regions | 116 MB |
| phased reads at GNAS, one pair per arm | 2.9 MB |
| chromosome 20 per-site calls, four arms, and the bisulfite slice | 66 MB |
| T2T annotation over those regions | 777 KB |
| exported hexagons and DMRs | 2.1 MB |

The read slice was cut for this repository. The ninety imprinting control regions span
1.02 Mb once padded, so the phased BAMs go from 85 GB and 53 GB to 38 and 19 MB per
haplotype. Base qualities are dropped, since NanoMethViz reads the MM and ML tags.

## Running it elsewhere

```bash
git clone https://github.com/LabShengLi/longverse-figures
cd longverse-figures
conda env create -f environment.yml
conda activate longverse-figures
bash postBuild
jupyter lab notebooks
```

R here is 4.4.3 and NanoMethViz is 3.2.0, the versions the paper's figures were drawn
on. `postBuild` compiles NanoMethViz rather than installing it prebuilt: the newest conda
build is 2.8.1, and 2.8.1's `plot_grange()` does not take the arguments the paper's script
passes.

R runs with `--vanilla` and `R_LIBS` pinned to the environment, so a personal R library
cannot change what the figures look like.

## From reads instead

The published chromosome 20 GNAS test set is 33 MB and runs the pipeline end to end in
minutes: Zenodo record 23090404, pipeline at <https://github.com/LabShengLi/longverse>.
