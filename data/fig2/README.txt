Source data for this display item, one file per panel, named by the panel letter.
Collected by paper_figures/deliver/91_gather_source_data.sh. Paths use $RESULTS for
/project2/sli68423_1316/projects/long_verse/results. A sha256-verified copy of every upstream
file is in $RESULTS/2026_10_08_figure_source_archive/ (by_item/fig2/). Rewritten 2026-10-08:
the previous README was the fig1 text copied unchanged and described the wrong figure.

Fig. 2, one sentence reproduces the expert, HG002 ONT chromosome 20.

  a  a_calling_run_record.json, a_phasing_run_record.json
     the expert's command and the agent's sentence, tool order, tasks, turns, tokens, cost;
     drawn straight from these records by arm_panel_a.py (prompt box + step table), so panel a
     has no CSV and is not listed in PANEL_NAMES.tsv, which lists rendered panel PDFs only
  b  b_persite_vs_wgbs.csv, b_tss_profile.csv (Supplementary Table S3)
     each arm's calls against WGBS at coverage >= 5, and mean methylation in 50 bp bins at TSS
  c  c_icr_*.csv (Supplementary Table S4); the GNAS region panels read the chr20 haplotype
     BAM subsets in data/icr_bam/, and the two arms' panels are byte-identical (md5 in the legend)

Upstream: $RESULTS/2026_09_25_longverse_agent_benchmark/ (pipeline_runs/{agent,human}/
upstream_chr20*, downstream_chr20*), which carries FIGURE_SOURCE_DO_NOT_DELETE.md.
