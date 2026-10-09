Source data for this display item, one file per panel, named by the panel letter.
Collected by paper_figures/deliver/91_gather_source_data.sh. Paths use $RESULTS for
/project2/sli68423_1316/projects/long_verse/results. A sha256-verified copy of every upstream
file is in $RESULTS/2026_10_08_figure_source_archive/ (by_item/ed_fig1/). Rewritten 2026-10-08:
the previous README was the fig1 text copied unchanged and described the wrong figure.

Extended Data Fig. 1, the remaining ONT panels for the same two runs as Fig. 2.

  a  a_wgbs_by_coverage.csv (Supplementary Table S5)
     agreement with WGBS by read-depth bin, each arm, basecalling run
  b  b_calling_agent_cost.csv, b_phasing_agent_cost.csv, b_compute_minutes_detail.json
     the agent's tokens, cost and conversation time against the compute each run set off
  c  c_icr_by_region.csv
     the known chromosome 20 imprinting control regions per haplotype, each arm's own phasing
     run; 14 of 14 tasks, 95,576 and 95,190 reads per haplotype, identical read sets

  d_phasing_run_record.json, d_tss_after_phasing.csv
     NOT a panel of this figure. The legend declares a to c and PANEL_NAMES.tsv lists a to c.
     These two were a panel d in the earlier Article-form figure; 91_gather_source_data.sh
     lines 72-73 still collect them. Kept so the gather script stays reproducible; ignore
     for the Brief Communication.

Upstream: $RESULTS/2026_09_25_longverse_agent_benchmark/, as for Fig. 2.
