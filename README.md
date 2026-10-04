# LongVerse figures

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/LabShengLi/longverse-figures/main?urlpath=lab/tree/notebooks/00_all_figures.ipynb)

Click the badge. A JupyterLab opens in your browser, already set up. Choose
**Run -> Run All Cells** and every figure in the paper is drawn in front of you, by the
code that drew it for the paper.

No download, no install, no account. The first launch builds the image and takes ten to
fifteen minutes, because the four R panels need real Bioconductor packages; after that it
starts in about half a minute.

Figures for *LongVerse: one sentence to the allele-specific methylome, verified multi-agent
AI for Nanopore and PacBio long-read sequencing.*

---

## This runs the paper's code, not a lookalike

`scripts/paper/` holds twenty-one scripts copied from the paper's repository **verbatim**,
with one edit each: a hard-coded cluster path becomes an environment variable.

    ENS = Path("/project2/.../2026_09_28_ensemble_chr22")
    ENS = Path(os.environ.get("LV_ENS", "/project2/.../2026_09_28_ensemble_chr22"))

That is the whole change, and it is checked: the vendoring script diffs each copy against
its source and refuses any line that differs for another reason.

This matters because the first version of this repository did not do it. The panels were
redrawn by eye from the exported numbers, and Figure 1e came back without its error half
and without the value labels on its bars, Figure 1f without its gain panel. Redrawing from
a description does not converge on the original.

`figures/RENDER_LOG.tsv` names, for every panel, which script drew it.

## One notebook per figure, the code in the cell

`notebooks/01_figure1.ipynb` through `08_gnas_region.ipynb`: one per figure, a cell per
panel. The cell holds the paper's code and the panel appears underneath it. Edit a line and
re-run and you get your edit, which is the point of opening a notebook rather than a PDF.

The four R panels are R cells, not Python strings holding R. `rpy2`'s `%%R` magic runs them
natively in the same kernel, so the code is highlighted, editable and runs as R. One line in
each differs from the file on disk: the paper's scripts read their arguments with
`commandArgs(trailingOnly = TRUE)` and a notebook has no command line, so that line becomes
the vector it would have produced. The substitution is marked in the cell.

The cells are generated from `scripts/paper/`, never typed. `python scripts/build_notebooks.py
--check` verifies they still agree with it, which is how the first version's drift would
have been caught.

`00_all_figures.ipynb` is different: it calls `scripts/render_all.py` instead of re-running
every cell. Under rpy2 all the R cells share one R session, while the paper's scripts each
run in a fresh R process; running them together in one session let one leave a variable the
next tripped over. The driver starts a process per script, so it is the faithful way to draw
everything at once.

## Why the repository is small

The figures are computed from whole-genome data: 60 million CpG sites per platform, BAMs in
the hundreds of gigabytes. Almost none of that is needed to *draw* them.

| what a panel needs | size |
| --- | --- |
| per-run evaluation records, which hold the profiles and the costs | 23 to 33 KB each |
| the three-caller consensus tables | 1 to 2 KB |
| the imprinting tables | 19 KB |
| phased reads at the imprinting regions, for the region plots | 116 MB |
| the T2T annotation over those regions | 777 KB of 753 MB |

The read slice is the one piece that had to be made rather than found. The ninety
imprinting control regions span 1.02 Mb once padded, which is 0.005 percent of the genome,
so the phased BAMs go from 85 GB and 53 GB to 38 and 19 MB per haplotype. Base quality
strings are dropped: NanoMethViz reads the MM and ML tags, and keeping the qualities
doubled the size for nothing.

## The GNAS region plots depend on a source build

Figure 2c and Extended Data Fig. 1c are drawn by NanoMethViz. bioconda carries only 2.4.0,
a major version behind the 3.2.0 the paper used, so `postBuild` installs it from
Bioconductor instead. That is a source build with compiled dependencies, and it is the one
step here that can fail on a machine this was not tested on: it did not complete on the
cluster it was prepared on, where the conda compiler wrapper could not find its own
backend.

So the notebook does not assume it. If NanoMethViz is present the panel is regenerated from
the reads in `data/icr_bam/`; if it is not, the figure the paper's own run produced is
shown instead, and `figures/RENDER_LOG.tsv` records which of the two happened on that run.

## The two panels that are not the paper's code

Everything else runs the paper's script. These two cannot, and the render log says so on
their rows.

| panel | why | what is drawn instead |
| --- | --- | --- |
| ED Fig. 4a-c, whole-genome hexbins | the paper's script reads three 450 MB point tables | the ~11,000 hexagons its own `hexbin()` computed, exported once |
| ED Fig. 5f, region hexbins | the paper's script loads RData objects up to 890 MB | the same, per region |

The reduction is exact, not a sample: binning 202,270 sites returns hexagons whose counts
sum to 202,270. What differs is the twenty lines that turn hexagons into a picture.

## What is here

    data/          every number each panel draws, plus the imprinting-region reads
    notebooks/     00_all_figures.ipynb
    scripts/paper/ the paper's scripts, verbatim but for their roots
    scripts/       render_all.py, which runs them; panels.py, for the two exported panels
    figures/       where the PDFs and PNGs are written

## Running it elsewhere

```bash
git clone https://github.com/LabShengLi/longverse-figures
cd longverse-figures
conda env create -f environment.yml
conda activate longverse-figures
bash postBuild                      # installs NanoMethViz from Bioconductor
python scripts/render_all.py figures
```

`render_all.py` runs R with `--vanilla` and pins `R_LIBS` to the environment's own library.
That is deliberate: on the machine this was built on, a personal R library held a `stringi`
compiled against a different ICU, and three of the four R panels failed to load. A reader's
own R settings must not be able to change the paper's figures.

## Reproducing from reads instead

This repository starts from what each panel draws. To start from raw signal, the published
chromosome 20 GNAS test set is 33 MB and runs the whole pipeline in minutes:

- data: Zenodo record 23090404
- pipeline: <https://github.com/LabShengLi/longverse>

## Notes on the data

Command lines shown in Figure 2a have had their paths rewritten to `$LONGVERSE`, `$RESULTS`
and similar. They were absolute paths on a shared HPC filesystem; the shape of the
invocation is what the panel is about. Figure 2a itself is native PowerPoint text in the
paper rather than an image, so the notebook prints its content instead of redrawing it.

`data/plot_layer/MANIFEST.tsv` records, for each exported file, how many rows it draws and
how many it was reduced from. `data/icr_bam/README.txt` records how the read slice was cut.
