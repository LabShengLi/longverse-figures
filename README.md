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
    figures/       where a run of one notebook writes its PDFs and PNGs

| notebook | figure |
| --- | --- |
| `01_figure1` | Fig. 1e, f - three callers and their consensus |
| `02_figure2` | Fig. 2a, b - one sentence reproduces the expert, ONT |
| `03_extended_data_fig1` | ED Fig. 1a, b, c - the remaining ONT panels |
| `04_extended_data_fig2` | ED Fig. 2 - PacBio calling |
| `05_extended_data_fig3` | ED Fig. 3 - PacBio phasing |
| `06_extended_data_fig4` | ED Fig. 4a-e - ONT, PacBio and WGBS across the genome |
| `07_extended_data_fig5` | ED Fig. 5a-h - coverage, imprinting and regional agreement |
| `08_gnas_region` | Fig. 2c - GNAS, per haplotype |
| `00_all_figures` | draws everything in one go |

The notebooks are committed with their figures, so they can be read on GitHub without
running anything.

## The scripts

Each cell holds the script that drew that panel, taken from the paper's repository. Edit a
line and re-run and you get your edit.

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

## The location

A panel script names its output after what it draws, because that is all it knows:
`panel_f_consensus.png` is Figure 1e, and the novel imprinting heatmap is written by a script
under `fig_ed4` and is Extended Data Fig. 5d. Both names are useful and they are kept apart:

    figures/all/       named for the figure: fig1e_consensus_vs_wgbs, ed5d_icr_novel_heatmap
                       FIGURE_PANELS.tsv maps each one back to the name the script gave it
    figures/notebook/  named by the script, because the cell above it is that script and
                       the point of the notebook is that the two agree

`figures/all/other_renders/` holds what the scripts produce that no figure places: the
versions of a panel with both arms in one plot, where the paper draws one arm at a time.

## The data

Whole-genome inputs are not needed to draw a figure, so what is here is what each panel
reads.

| | |
| --- | --- |
| per-run evaluation records | 23 to 33 KB each |
| consensus and imprinting tables | 1 to 19 KB |
| phased reads at the imprinting regions | 116 MB |
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
