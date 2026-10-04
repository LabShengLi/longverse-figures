# LongVerse figures

One notebook per figure. In each cell the paper's own code is there to read and to edit,
and the panel it drew appears underneath.

| notebook | figure |
| --- | --- |
| `01_figure1.ipynb` | Figure 1e, f |
| `02_figure2.ipynb` | Figure 2a, b |
| `03_extended_data_fig1.ipynb` | ED Fig. 1a, b, c |
| `04_extended_data_fig2.ipynb` | ED Fig. 2, PacBio calling |
| `05_extended_data_fig3.ipynb` | ED Fig. 3, PacBio phasing |
| `06_extended_data_fig4.ipynb` | ED Fig. 4, across the genome |
| `07_extended_data_fig5.ipynb` | ED Fig. 5, coverage and regions |
| `08_gnas_region.ipynb` | Figure 2c, the GNAS region plots |
| `00_all_figures.ipynb` | every cell above, in one run |

The code in the cells is generated from `../scripts/paper/`, which holds the paper's own
scripts copied verbatim. `python ../scripts/build_notebooks.py --check` verifies that the
two still agree.
