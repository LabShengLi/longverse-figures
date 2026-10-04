#!/usr/bin/env Rscript
## Imprinting-control-region heatmaps (HP1 minus HP2 methylation, ONT and PacBio) at Nature
## Methods size: 7 pt text, cells sized so the 43-column novel heatmap spans the 183 mm page.
##
## Parameterised copy of results/2026_10_03_2platform_phasing_jasmine/
## _2025_06_17_figure5_ab_plot_heatmap_compare_icr.R (the 12 pt deck version). Same input,
## same ordering (ONT difference descending), same colour scale; the plot tables it writes
## are checked row for row against that script's plotdf.csv, so the two renders cannot
## drift apart in content.
##
## Usage: 12_icr_heatmap_nm.R <input merged csv> <reference dir with *.plotdf.csv> <outdir>
## Env:   ICR_BASE_PT (7), ICR_CELL_W_MM (3.3), ICR_CELL_H_MM (4), ICR_COL_LABEL_MM (22)
suppressPackageStartupMessages({
    library(tidyverse); library(ComplexHeatmap); library(circlize); library(RColorBrewer); library(grid)
})
argv <- commandArgs(trailingOnly = TRUE)
stopifnot(length(argv) == 3)
input_file <- argv[1]; ref_dir <- argv[2]; outdir <- argv[3]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

BASE_PT <- as.numeric(Sys.getenv("ICR_BASE_PT", "7"))
CELL_W_MM <- as.numeric(Sys.getenv("ICR_CELL_W_MM", "3.3"))
CELL_H_MM <- as.numeric(Sys.getenv("ICR_CELL_H_MM", "4"))
ROW_GAP_MM <- 1
LEGEND_W_MM <- 16
ROW_LABEL_W_MM <- 11
COL_LABEL_H_MM <- as.numeric(Sys.getenv("ICR_COL_LABEL_MM", "22"))
MARGIN_MM <- 2

df_all <- read_csv(input_file, show_col_types = FALSE) %>%
    transmute(Name = as.character(Name), Status = as.character(Status),
              ONT_diff = as.numeric(ONT_HP_diff), Pacbio_diff = as.numeric(Pacbio_HP_diff)) %>%
    drop_na(ONT_diff, Pacbio_diff) %>%
    arrange(desc(ONT_diff), desc(Pacbio_diff))
cat("rows:", nrow(df_all), " known:", sum(df_all$Status == "Known"), " novel:", sum(df_all$Status == "Novel"), "\n")

breaks <- seq(0, 1, length.out = 11)
col_fun <- colorRamp2(breaks, colorRampPalette(rev(brewer.pal(n = 7, name = "RdYlBu")))(length(breaks)))

plotdf_known <- df_all %>% filter(Status == "Known") %>% select(Name, ONT = ONT_diff, PacBio = Pacbio_diff)
plotdf_novel <- df_all %>% filter(Status == "Novel") %>% select(Name, ONT = ONT_diff, PacBio = Pacbio_diff) %>%
    mutate(Name = str_replace(Name, "intragenic_", "intra_"),
           Name = str_replace(Name, "PWARSN,SNORD107,PWARSN,PWAR5", "PWARSN,SNORD107"))

check_against_reference <- function(plotdf, ref_csv) {
    ref <- read_csv(ref_csv, show_col_types = FALSE)
    stopifnot(nrow(ref) == nrow(plotdf), all(ref$Name == plotdf$Name),
              max(abs(ref$ONT - plotdf$ONT)) < 1e-9, max(abs(ref$PacBio - plotdf$PacBio)) < 1e-9)
    cat("  matches", basename(ref_csv), "(", nrow(ref), "regions )\n")
}
check_against_reference(plotdf_known, file.path(ref_dir, "hg002_known_icr_hp_diff_heatmap.mincov5.plotdf.csv"))
check_against_reference(plotdf_novel, file.path(ref_dir, "hg002_novel_icr_hp_diff_heatmap.mincov5.plotdf.csv"))

draw_one <- function(plotdf, tag) {
    write_csv(plotdf, file.path(outdir, sprintf("icr_heatmap_%s_nm.plotdf.csv", tag)))
    mat <- plotdf %>% column_to_rownames("Name") %>% as.matrix() %>% t()
    n_col <- ncol(mat); n_row <- nrow(mat)
    italic_labels <- parse(text = paste0("italic('", plotdf$Name, "')"))
    ht <- Heatmap(mat, name = "HP1 - HP2", col = col_fun, na_col = "black",
                  width = unit(n_col * CELL_W_MM, "mm"),
                  height = unit(n_row * CELL_H_MM + (n_row - 1L) * ROW_GAP_MM, "mm"),
                  column_labels = italic_labels, column_title = character(0),
                  cluster_columns = FALSE, cluster_rows = FALSE, row_title = NULL,
                  column_names_gp = gpar(fontsize = BASE_PT), row_names_gp = gpar(fontsize = BASE_PT),
                  heatmap_legend_param = list(title_gp = gpar(fontsize = BASE_PT, fontface = "bold"),
                                              labels_gp = gpar(fontsize = BASE_PT),
                                              grid_width = unit(3, "mm"), legend_height = unit(14, "mm")),
                  row_split = factor(c("ONT", "PacBio"), levels = c("ONT", "PacBio")),
                  row_gap = unit(ROW_GAP_MM, "mm"), rect_gp = gpar(col = "#DDDDDD", lwd = 0.5))
    w_in <- (n_col * CELL_W_MM + LEGEND_W_MM + ROW_LABEL_W_MM + 2 * MARGIN_MM) / 25.4
    ## the legend is centred on the two heatmap rows and its title rises above them: 6 mm of
    ## headroom, or the title is clipped at the top of the device (seen 2026-10-03)
    TOP_MM <- MARGIN_MM + 6
    h_in <- (n_row * CELL_H_MM + (n_row - 1L) * ROW_GAP_MM + COL_LABEL_H_MM + MARGIN_MM + TOP_MM) / 25.4
    stem <- file.path(outdir, sprintf("icr_heatmap_%s_nm", tag))
    pad <- unit(c(MARGIN_MM, MARGIN_MM, TOP_MM, MARGIN_MM), "mm")   # bottom, left, top, right
    cairo_pdf(paste0(stem, ".pdf"), width = w_in, height = h_in); draw(ht, padding = pad); dev.off()
    png(paste0(stem, ".png"), width = w_in, height = h_in, units = "in", res = 300, type = "cairo")
    draw(ht, padding = pad); dev.off()
    cat(sprintf("wrote %s.pdf/.png  %d regions, %.2f x %.2f in, %g pt\n", stem, n_col, w_in, h_in, BASE_PT))
}
draw_one(plotdf_novel, "novel")
draw_one(plotdf_known, "known")
