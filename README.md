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
    figures/       where a run writes its PDFs and PNGs

| notebook | figure |
| --- | --- |
| `01_figure1` | Fig. 1e, f - three callers and their consensus |
| `02_figure2` | Fig. 2a, b - one sentence reproduces the expert, ONT |
| `03_extended_data_fig1` | ED Fig. 1a, b - the remaining ONT panels |
| `04_extended_data_fig2` | ED Fig. 2 - PacBio calling |
| `05_extended_data_fig3` | ED Fig. 3 - PacBio phasing |
| `06_extended_data_fig4` | ED Fig. 4a-e - ONT, PacBio and WGBS across the genome |
| `07_extended_data_fig5` | ED Fig. 5a-h - coverage, imprinting and regional agreement |
| `08_gnas_region` | Fig. 2c - GNAS, per haplotype |
| `00_all_figures` | draws everything in one go |

The notebooks are committed with their figures, so they can be read on GitHub without
running anything.

## The code in the cells

Each cell holds the script that drew that panel, taken from the paper's repository. Edit a
line and re-run and you get your edit.

The four R panels are R cells: `rpy2`'s `%%R` magic runs them in the same kernel as the
Python ones. Each differs from its file by one line, marked where it happens, because the
scripts read their arguments from a command line and a notebook has none.

Cells are generated from `scripts/paper/`, and `python scripts/build_notebooks.py --check`
confirms they still match it.

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

## Two panels drawn from exported values

ED Fig. 4a-c and ED Fig. 5h are redrawn from the hexagons their own `hexbin()` call
produced, exported once, because the scripts for them read 450 MB and 890 MB inputs. The
binning is exact: 202,270 sites give hexagons whose counts sum to 202,270. Every other panel
drawn here runs its script. `figures/RENDER_LOG.tsv` lists which is which. The eight exported
region files are named `ed5_f_<region>`, the panel letter they carried when the export ran;
the panel is h.

## Two panels that are not here

Fig. 2b puts two plots in each arm's frame and this repository draws the right-hand one. The
left-hand one is a per-site hexbin whose script reads both arms' whole chromosome 20 per-site
tables and the 540 MB bisulfite table. ED Fig. 1c, the chromosome 20 imprinting control
regions, needs each arm's own per-region table from its pipeline run. Neither input is
carried here, so `scripts/paper/make_hexbin_panel.py` and `scripts/paper/make_icr_panel.py`
ship as the paper's code without a cell that calls them.

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

## Notes

Command lines shown in Figure 2a have their paths rewritten to `$LONGVERSE` and `$RESULTS`;
they were absolute paths on a shared filesystem. Figure 2a is native PowerPoint text in the
paper, so the notebook prints its content rather than redrawing it.

`data/plot_layer/MANIFEST.tsv` records how many rows each exported file draws and how many
it came from. `data/icr_bam/README.txt` records how the read slice was cut.
