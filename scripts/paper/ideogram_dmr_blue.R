#!/usr/bin/env Rscript
rm(list = ls())
require(GenomicRanges)
require(ggbio)

# Visualize Hyper/Hypo DMR for HG002 ONT on T2T genome with gap region annotations

## What the ideogram draws. These two numbers are the panel: a DMR is plotted only if it
## clears both. They are NOT the function defaults further down (25 and 0.01) - line ~196
## passes these in and overrides those, which is how the panels came to be drawn at 10 and
## 0.05 while every count quoted beside them was computed at 25 and 0.01. Anything that
## reports a DMR count must read these same variables, which is why they are overridable:
## the number in the log and the dots on the page then cannot drift apart.
##
## 2026-10-03: raised to 50 and 0.01 on the user's call. At 10 percent the ideogram is a
## solid band on every chromosome and says nothing; 50 percent leaves the haplotype
## differences that are actually worth looking at.
methDiffCutoff <- as.numeric(Sys.getenv("IDEOGRAM_METHDIFF", "50"))
methDiffQValue <- as.numeric(Sys.getenv("IDEOGRAM_QVALUE",   "0.01"))
## Typography and canvas. The defaults reproduce the 12 pt, 8 x 7 in panel exactly; the
## Nature Methods render (paper_figures/fig_ed4) sets IDEOGRAM_BASE_PT=7 and a 3.5 in
## canvas, and blanks the title because the deck carries the panel caption.
basePt   <- as.numeric(Sys.getenv("IDEOGRAM_BASE_PT", "12"))
titlePt  <- as.numeric(Sys.getenv("IDEOGRAM_TITLE_PT", as.character(basePt + 2)))
figW     <- as.numeric(Sys.getenv("IDEOGRAM_WIDTH_IN", "8"))
figH     <- as.numeric(Sys.getenv("IDEOGRAM_HEIGHT_IN", "7"))
legendKey <- as.numeric(Sys.getenv("IDEOGRAM_LEGEND_KEY", "4"))
titleText <- Sys.getenv("IDEOGRAM_TITLE", "__default__")
cat(sprintf("[CUTOFF] methdiff >= %g, qvalue <= %g\n", methDiffCutoff, methDiffQValue))

## Parameterised copy of hpc_test/analysis/Figure4/IdeomgramPlot_methykit_{ont,pacbio}_hg002.R.
## The two originals differ only in platform name, input path, title and output name, so they
## are one script here. The originals are left untouched.
##
## Usage: 02_ideogram_dmr_blue.R <ont|pacbio> <outdir>
argv <- commandArgs(trailingOnly = TRUE)
platform <- if (length(argv) >= 1) argv[1] else "ont"
outdir   <- if (length(argv) >= 2) argv[2] else "."
stopifnot(platform %in% c("ont", "pacbio"))
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
PLATFORM_LABEL <- if (platform == "ont") "ONT" else "PacBio"

## The default is the June 2026 run. Its PacBio branch is primrose, so the PacBio
## ideogram must be pointed at a jasmine DMR directory instead; the ONT branch there
## is unaffected and stays the default. IDEOGRAM_WDIR overrides, nothing else changes.
wdir <- Sys.getenv('IDEOGRAM_WDIR',
                   '/project2/sli68423_1316/projects/long_verse/results/2026_06_16_phasing_dmr')
dir.create(wdir, showWarnings = FALSE, recursive = TRUE)
setwd(wdir)

chm13_chrom_size_file <- '/project2/sli68423_1316/users/yang/reference/chm13v2.0/chm13v2.0.chrom.sizes'
chm13_df <- read.table(chm13_chrom_size_file, sep = "\t", header = FALSE)

chm13.chr.len <- chm13_df[[2]]
names(chm13.chr.len) <- chm13_df[[1]]

# keep autosomes chr1-chr22 only
autosomes <- paste0("chr", 1:22)
chm13.chr.len <- chm13.chr.len[autosomes[autosomes %in% names(chm13.chr.len)]]

# load the methylKit DMR table. The originals name a plain .tsv; the files on disk were
# gzipped after that run, so take whichever is present rather than failing on the name.
dmr_file <- file.path(wdir, sprintf('methylkit_call/%s/hg002_%s_HP1_vs_HP2_methylkit_DMR_all.tsv',
                                    platform, platform))
if (!file.exists(dmr_file) && file.exists(paste0(dmr_file, '.gz'))) {
    dmr_file <- paste0(dmr_file, '.gz')
}
stopifnot(file.exists(dmr_file))
cat("DMR table:", dmr_file, "\n")
dmr_df <- read.table(gzfile(dmr_file), sep = "\t", header = TRUE,
                     stringsAsFactors = FALSE, check.names = FALSE)
dmr_df <- dmr_df[dmr_df$chr %in% names(chm13.chr.len),]

# gap regions (TSV with header: chrom, chromStart, chromEnd)
t2t_gap_bed_file <- file.path(wdir, 'AH107353_T2T_hgUnique.tsv')
t2t_gap_bed_df <- read.table(t2t_gap_bed_file, sep = "\t", header = TRUE, stringsAsFactors = FALSE)
t2t_gap_bed_df <- t2t_gap_bed_df[t2t_gap_bed_df$chrom %in% names(chm13.chr.len),]
t2t_gap_granges <- GRanges(
    seqnames = t2t_gap_bed_df$chrom,
    ranges = IRanges(start = t2t_gap_bed_df$chromStart, end = t2t_gap_bed_df$chromEnd)
)

filter_dmr <- function(dmr_df, difference, qvalue, type) {
    sig <- abs(dmr_df$meth.diff) >= difference & dmr_df$qvalue <= qvalue
    if (type == "hyper") {
        dmr_df[sig & dmr_df$meth.diff > 0,]
    } else {
        dmr_df[sig & dmr_df$meth.diff < 0,]
    }
}

dmr_to_granges <- function(dmr_df) {
    GRanges(
        seqnames = dmr_df$chr,
        ranges = IRanges(start = dmr_df$start, end = dmr_df$end),
        meth.diff = dmr_df$meth.diff
    )
}

gap_ylim <- c(-100, 100)

# colorblind-friendly palette (Wong): pink vs BLUE; gap stays red.
#
# The original used Wong yellow #F0E442 for hypo. Wong is colourblind safe, but yellow on
# white has almost no luminance contrast, and on a printed poster at viewing distance the
# hypo points disappear. Wong blue #0072B2 keeps the palette colourblind safe and is the
# darkest colour in it, so the two DMR classes separate by lightness as well as by hue,
# which is what survives printing and photocopying.
hyper_col <- "#CC79A7"  # pink
hypo_col <- "#0072B2"   # blue, was #F0E442 yellow
gap_col <- "red"

ideoDMC <- function(dmr_df, chrom.length, difference = 25,
                    qvalue = 0.01, circos = FALSE, title = "Test title",
                    hyper.col = hyper_col,
                    hypo.col = hypo_col,
                    gap.col = gap_col) {
    myIdeo <- GRanges(seqnames = names(chrom.length),
                      ranges = IRanges(start = 1, width = chrom.length))
    seqlevels(myIdeo) <- names(chrom.length)
    seqlengths(myIdeo) <- chrom.length

    hyper <- filter_dmr(dmr_df, difference, qvalue, "hyper")
    hypo <- filter_dmr(dmr_df, difference, qvalue, "hypo")

    g.per <- dmr_to_granges(hyper)
    seqlevels(g.per) <- seqlevels(myIdeo)
    seqlengths(g.per) <- chrom.length

    g.po <- dmr_to_granges(hypo)
    seqlevels(g.po) <- seqlevels(myIdeo)
    seqlengths(g.po) <- chrom.length

    values(g.po)$id <- "Hypo"
    values(g.per)$id <- "Hyper"
    legend_levels <- c("Hyper", "Hypo", "Gap region")
    values(g.po)$id <- factor(values(g.po)$id, levels = legend_levels)
    values(g.per)$id <- factor(values(g.per)$id, levels = legend_levels)

    # invisible dummy point so "Gap region" appears in the color legend
    g.gap.legend <- GRanges(
        seqnames = names(chrom.length)[1],
        ranges = IRanges(start = 1, width = 1),
        meth.diff = gap_ylim[1] - 1,
        id = factor("Gap region", levels = legend_levels)
    )
    seqlevels(g.gap.legend) <- seqlevels(myIdeo)
    seqlengths(g.gap.legend) <- chrom.length
    g.dmr <- c(g.po, g.per, g.gap.legend)

    if (circos) {
        p <- ggplot() + layout_circle(myIdeo, geom = "ideo", fill = "gray70",
                                      radius = 39, trackWidth = 2)

        p <- p +
            layout_circle(c(g.po, g.per), geom = "point",
                          size = 1, aes(x = midpoint,
                                        y = meth.diff, color = id), radius = 25, trackWidth = 30) +
            scale_colour_manual(values = c("Hyper" = hyper.col, "Hypo" = hypo.col))
        p3 <- p +
            layout_circle(myIdeo, geom = "text", aes(label = seqnames),
                          vjust = 0, radius = 55, trackWidth = 7) +
            labs(title = title)

    } else {
        legend_shapes <- c("Hyper" = 16, "Hypo" = 16, "Gap region" = 22)
        legend_title <- "Annotation"
        p1 <- ggplot() + layout_karyogram(myIdeo)
        p2 <- p1 +
            layout_karyogram(g.dmr, geom = "point", size = 0.01,
                             aes(x = midpoint,
                                 y = meth.diff, color = id)) +
            scale_colour_manual(legend_title,
                                breaks = legend_levels,
                                values = c("Hyper" = hyper.col,
                                           "Hypo" = hypo.col,
                                           "Gap region" = gap.col)) +
            labs(title = title) +
            xlab("Genomic coordinates") +
            ylab("Methylation difference (%)") +
            ## ggplot's base_size is not a floor: axis.text defaults to rel(0.8), so a
            ## base of 11 puts the chromosome strip labels and both axes at 8.8 pt. Only
            ## plot.title was ever set here, which is why the panel sat at 9 pt while
            ## reading as finished. Every text element is named explicitly instead.
            theme(
                plot.title   = if (nzchar(title)) element_text(hjust = 0.5, size = titlePt) else element_blank(),
                axis.title   = element_text(size = basePt),
                axis.text    = element_text(size = basePt),
                strip.text   = element_text(size = basePt),
                legend.title = element_text(size = basePt),
                legend.text  = element_text(size = basePt),
                legend.key.size = unit(basePt * 1.2, "pt")
            ) +
            guides(color = guide_legend(
                title = legend_title,
                override.aes = list(
                    shape = unname(legend_shapes[legend_levels]),
                    fill = c(hyper.col, hypo.col, NA),
                    colour = c(hyper.col, hypo.col, gap.col),
                    alpha = c(1, 1, 1),
                    size = c(legendKey, legendKey, legendKey)
                )
            ))
        p3 <- p2 +
            layout_karyogram(t2t_gap_granges,
                             geom = "rect",
                             rect.height = abs(gap_ylim[2] - gap_ylim[1]) / 2,
                             ylim = gap_ylim,
                             color = gap.col, fill = NA) +
            coord_cartesian(ylim = gap_ylim)
    }

    return(p3)
}

ideoPlot <- ideoDMC(dmr_df, chrom.length = chm13.chr.len,
                    difference = methDiffCutoff, qvalue = methDiffQValue,
                    circos = FALSE,
                    title = if (identical(titleText, "__default__"))
                        sprintf("%s: DMRs of Haplotypes in HG002", PLATFORM_LABEL) else titleText)

ideoPlot

stem <- file.path(outdir, sprintf('Ideogram_dmr_t2t_hg002_%s_blue', platform))

## cairo_pdf, not pdf(): the base device does not embed fonts, so an Arial panel opens in
## whatever the reader substitutes. Same reason png() is given the cairo type. The size is
## 8 x 7 rather than 8 x 6: at 12 pt the 24 chromosome strip labels need the extra inch.
cairo_pdf(paste0(stem, '.pdf'), width = figW, height = figH)
print(ideoPlot)
dev.off()

png(paste0(stem, '.png'), width = figW, height = figH, units = "in", res = 400, type = "cairo")
print(ideoPlot)
dev.off()

cat("wrote", paste0(stem, c('.pdf', '.png')), "\n")
cat("hyper", hyper_col, " hypo", hypo_col, "\n")
