#!/usr/bin/env Rscript
## Absolute haplotype methylation difference at the imprinting control regions covered by both
## platforms, by region set, ONT against PacBio, with the paired Wilcoxon test per set.
## 7 pt, 2.4 x 1.7 in. Parameterised copy of results/2026_10_03_2platform_phasing_jasmine/
## _compare_ont_pacbio_boxplot_for_region.R; the region counts and tests are recomputed and
## written next to the panel, and checked against that script's txt.
##
## Usage: 14_boxplot_nm.R <merged annotation csv> <outdir>      Env: ICR_BASE_PT (7)
suppressPackageStartupMessages({ library(tidyverse); library(ggpubr) })
argv <- commandArgs(trailingOnly = TRUE); stopifnot(length(argv) == 2)
input <- argv[1]; outdir <- argv[2]; dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
PT <- as.numeric(Sys.getenv("ICR_BASE_PT", "7"))

df2 <- read_csv(input, show_col_types = FALSE) %>%
    mutate(Region = case_when(Status == "Known" ~ "Known",
                              Status == "Novel" & Study == "Court-etal" ~ "Novel Court",
                              Status == "Novel" & Study == "Joshi-etal" ~ "Novel Joshi",
                              TRUE ~ "Other"),
           Region = factor(Region, levels = c("Known", "Novel Court", "Novel Joshi")))
stopifnot(!any(is.na(df2$Region)))
df_long <- df2 %>% select(Name, Region, ONT_HP_diff, Pacbio_HP_diff) %>%
    pivot_longer(c(ONT_HP_diff, Pacbio_HP_diff), names_to = "Platform", values_to = "HP_diff") %>%
    mutate(Platform = recode(Platform, ONT_HP_diff = "ONT", Pacbio_HP_diff = "PacBio"))

wilcox_df <- df2 %>% group_by(Region) %>%
    summarise(n = n(),
              statistic = wilcox.test(ONT_HP_diff, Pacbio_HP_diff, paired = TRUE)$statistic,
              p_value = wilcox.test(ONT_HP_diff, Pacbio_HP_diff, paired = TRUE)$p.value,
              median_ONT = median(ONT_HP_diff, na.rm = TRUE), median_PacBio = median(Pacbio_HP_diff, na.rm = TRUE),
              n_pairs_tested = sum(!is.na(ONT_HP_diff) & !is.na(Pacbio_HP_diff)), .groups = "drop")
write_tsv(wilcox_df, file.path(outdir, "hp_diff_by_region_nm_wilcoxon.tsv"))
print(wilcox_df)

labels <- wilcox_df %>% mutate(lab = sprintf("n = %d\nP = %s", n, formatC(p_value, digits = 2, format = "g")))
p <- ggplot(df_long, aes(x = Platform, y = HP_diff, fill = Platform)) +
    geom_boxplot(width = 0.6, outlier.size = 0.4, outlier.stroke = 0, alpha = 0.85, color = "grey25", lwd = 0.3) +
    scale_fill_manual(values = c("ONT" = "#1f78b4", "PacBio" = "#e31a1c")) +
    geom_text(data = labels, aes(x = 1.5, y = 1.04, label = lab), inherit.aes = FALSE, size = PT / ggplot2::.pt, vjust = 0, lineheight = 0.9) +
    facet_wrap(~Region, nrow = 1) +
    scale_y_continuous(breaks = seq(0, 1, 0.25)) +
    coord_cartesian(ylim = c(0, 1.22), clip = "off") +
    labs(x = NULL, y = "|HP1 - HP2| methylation") +
    theme_classic(base_size = PT) +
    theme(legend.position = "none",
          axis.text = element_text(color = "black", size = PT), axis.title = element_text(size = PT),
          strip.background = element_blank(), strip.text = element_text(size = PT),
          axis.line = element_line(linewidth = 0.3), axis.ticks = element_line(linewidth = 0.3),
          plot.margin = margin(t = 2, r = 2, b = 2, l = 2))
stem <- file.path(outdir, "hp_diff_by_region_nm")
ggsave(paste0(stem, ".pdf"), p, width = 2.4, height = 1.7, device = cairo_pdf)
ggsave(paste0(stem, ".png"), p, width = 2.4, height = 1.7, dpi = 300, type = "cairo")
cat("wrote", stem, ".pdf/.png\n")
