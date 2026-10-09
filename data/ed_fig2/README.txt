Extended Data Fig. 2, PacBio calling, agent against expert, chr20.

Source data for this display item: what each panel reads, as the figure code reads it.
Panels were built in results/2026_10_01_paper_figures/suppfig3/; the numbers were computed from results/2026_10_02_suppfig34_pacbio_chr20/ (supp3_human, supp3_agent).
Paths below use $RESULTS for /project2/sli68423_1316/projects/long_verse/results, as the
records in this folder do. A sha256-verified copy of every upstream file is kept at
$RESULTS/2026_10_08_figure_source_archive/ (by_item/ed_fig2/), and each upstream directory
carries FIGURE_SOURCE_DO_NOT_DELETE.md. Written 2026-10-08.

Files here, and the upstream each one references:
  agent_argv.json
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/input/supp3_kinetics
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/tmp
  agent_cost_row.json   (self-contained: no upstream path inside it)
  agent_prompt.txt   (self-contained: no upstream path inside it)
  agent_record_pacbio_calling.json
      <- $RESULTS/2026_10_02_pacbio_agent_cost/agent_pacbio_calling/row.json
      <- $RESULTS/2026_10_02_pacbio_agent_cost/agent_pacbio_calling/session.json
  agent_trace.txt   (self-contained: no upstream path inside it)
  compute_minutes.json   (self-contained: no upstream path inside it)
  concordance.json   (self-contained: no upstream path inside it)
  human_command_as_run.txt
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/supp3_human/launch/nextflow.log
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/supp3_human/launch/trace.txt
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/supp3_human/results
  human_trace.txt   (self-contained: no upstream path inside it)
  panel_agent_cost.csv   (self-contained: no upstream path inside it)
  panel_hexbin_vs_wgbs.csv   (self-contained: no upstream path inside it)
  panel_tss_profile.csv   (self-contained: no upstream path inside it)
  panel_wgbs_by_coverage.csv   (self-contained: no upstream path inside it)
  suppfig3_human_vs_agent_stats.csv
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/supp3_agent/launch/results/supp3_agent-methylation-callings/Site_Level-supp3_agent_all/supp3_agent_all_PB_JASMINE-perSite-cov1.sort.bed.gz
      <- $RESULTS/2026_10_02_suppfig34_pacbio_chr20/supp3_human/results/supp3_human-methylation-callings/Site_Level-supp3_human_all/supp3_human_all_PB_JASMINE-perSite-cov1.sort.bed.gz

Note: suppfig3_human_vs_agent_stats.csv is the direct per-site comparison of the two
calling runs: 1,591,619 sites each, all shared, RMSE 0.0, so the two tables are identical.
