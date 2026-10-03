# LongVerse figures

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/LabShengLi/longverse-figures/main?urlpath=lab/tree/notebooks/00_all_figures.ipynb)

Click the badge. A JupyterLab opens in your browser, already set up. Choose
**Run -> Run All Cells** and every figure from the paper is redrawn in front of you, from
the numbers it was drawn from.

No download, no install, no account. The first launch builds the environment and takes a
few minutes; afterwards it starts in about half a minute.

Figures for *LongVerse: one sentence to the allele-specific methylome, verified multi-agent
AI for Nanopore and PacBio long-read sequencing.*

---

## What is here

    data/          every number each panel draws, 3.5 MB in total
    notebooks/     00_all_figures.ipynb, plus one notebook per figure
    scripts/       panels.py, one function per kind of panel
    figures/       where the PDFs and PNGs are written

## Why it is only 3.5 MB

The figures are computed from whole-genome data: 60 million CpG sites per platform, BAMs in
the hundreds of gigabytes. None of that is needed to *draw* them, and this repository ships
what is.

| panel | drawn from | reduced from |
| --- | --- | --- |
| hexbins | the ~11,000 hexagons matplotlib computes, 52 KB each | 56-62 million rows, 450 MB each |
| ideograms | the 45,339 and 21,609 DMRs that clear the cutoff | 2.6 million tiles, 73 MB |
| region hexbins | 8 x ~10,000 hexagons | per-region tables up to 276 MB |
| profiles, costs, tables | already the drawn values | unchanged |

The reduction is exact, not a sample. The hexagons are produced by the same `hexbin` call
the paper's panels use, `gridsize=100` over `extent=(0, 100, 0, 100)`, and the DMRs are
those passing the published cutoff of |HP1 - HP2| >= 50 percentage points and q <= 0.01.
Binning 202,270 sites returns hexagons whose counts sum to 202,270: no point is dropped.

That is also what makes the repository run on the 2 GB of memory a free Binder gets.

## These are redraws, not the submitted files

The paper's ideograms were drawn with karyoploteR and its heatmaps with ComplexHeatmap.
Installing those on Binder takes ten to twenty minutes and fails often enough to matter, so
every panel here is redrawn in matplotlib from the identical numbers. They are equivalent,
not byte-identical: colours and spacing differ slightly.

The R originals, and the whole pipeline, are in the main repository:
<https://github.com/LabShengLi/longverse>.

## Running it elsewhere

```bash
git clone https://github.com/LabShengLi/longverse-figures
cd longverse-figures
conda env create -f environment.yml
conda activate longverse-figures
jupyter lab notebooks/00_all_figures.ipynb
```

## Reproducing from the raw data instead

This repository starts from the drawn numbers. To start from reads, the published
chromosome 20 GNAS test set is 33 MB and runs the whole pipeline in minutes:

- data: Zenodo record 23090404
- pipeline: <https://github.com/LabShengLi/longverse>

## Notes on the data

Paths in the command lines shown in Figure 2a have been rewritten to `$LONGVERSE`,
`$RESULTS` and similar. They were absolute paths on a shared HPC filesystem; the shape of
the invocation is what the panel is about.

`data/plot_layer/MANIFEST.tsv` records, for each exported file, how many rows it draws and
how many rows it was reduced from.
