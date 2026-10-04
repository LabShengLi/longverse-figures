#!/usr/bin/env Rscript
## ONT against PacBio per-site methylation within each genomic region class, one small panel
## per class at 7 pt (1.75 x 1.5 in), from the ggplot objects that
## plot_perSite_cov_hexbin_by_region.sh saved (hg002_ont_pacbio_cov5_region_<class>_hexbin_compare.RData
## in results/2026_10_03_consensus_2platform_jasmine). The data are not recomputed; one
## RData is loaded at a time because the largest holds 56 million sites.
##
## Usage: 15_region_hexbin_nm.R <rdata dir> <outdir>      Env: ICR_BASE_PT (7)
suppressPackageStartupMessages({ library(ggplot2); library(readr); library(dplyr) })
argv <- commandArgs(trailingOnly = TRUE); stopifnot(length(argv) == 2)
rdir <- argv[1]; outdir <- argv[2]; dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
PT <- as.numeric(Sys.getenv("ICR_BASE_PT", "7"))
PREFIX <- "hg002_ont_pacbio_cov5"
regions <- c("Promoter", "5UTR", "3UTR", "Exon", "Intron", "Intergenic", "CpGIsland", "NonCpGIsland")
pretty <- c(Promoter = "Promoter", `5UTR` = "5' UTR", `3UTR` = "3' UTR", Exon = "Exon", Intron = "Intron",
            Intergenic = "Intergenic", CpGIsland = "CpG island", NonCpGIsland = "Non-island")
rows <- list()
for (label in regions) {
    fn <- file.path(rdir, sprintf("%s_region_%s_hexbin_compare.RData", PREFIX, label))
    stopifnot(file.exists(fn))
    e <- new.env(); load(fn, envir = e)
    if (label == regions[1]) { cat("mapping:\n"); print(e$p_meth$mapping); cat("labels:\n"); print(e$p_meth$labels[c("x", "y")]) }
    ## the saved plot keeps its own scales (replacing them moved every tick to the origin, the
    ## plot is in percent); the title is two lines because one does not fit 1.75 in at 7 pt
    p <- e$p_meth +
        ggtitle(sprintf("%s\nr = %.3f, n = %s", pretty[[label]], e$meth_cor, format(nrow(e$df), big.mark = ","))) +
        theme(plot.title = element_text(size = PT, hjust = 0.5, lineheight = 0.9), axis.title = element_text(size = PT),
              axis.text = element_text(size = PT), legend.position = "none",
              axis.line = element_line(linewidth = 0.3), axis.ticks = element_line(linewidth = 0.3),
              plot.margin = margin(t = 2, r = 4, b = 2, l = 2))
    stem <- file.path(outdir, sprintf("region_%02d_%s_nm", match(label, regions), label))
    ggsave(paste0(stem, ".pdf"), p, width = 1.75, height = 1.5, device = cairo_pdf)
    ggsave(paste0(stem, ".png"), p, width = 1.75, height = 1.5, dpi = 300, type = "cairo")
    rows[[label]] <- data.frame(region = label, n_cpg = nrow(e$df), PCC = e$meth_cor)
    cat(sprintf("wrote %s  n = %d  r = %.4f\n", stem, nrow(e$df), e$meth_cor))
    rm(e, p); invisible(gc())
}
write_tsv(bind_rows(rows), file.path(outdir, "region_stratified_nm_stats.tsv"))
