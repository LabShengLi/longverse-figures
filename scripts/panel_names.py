"""The name a script gives a panel, and the name the paper gives it.

Shared by render_all.py (the batch render) and nbkit.py (the notebooks), so both write
the figure name: fig1e_consensus_vs_wgbs, ed5c_hp_diff_by_region. The script name a panel
was produced under is the key; FIGURE_PANELS.tsv beside the renders keeps both.
"""
from __future__ import annotations

# produced stem -> (figure, panel, new stem)
FIGURE_PANELS: dict[str, tuple[str, str, str]] = {
    "panel_f_consensus":                 ("Fig. 1", "e", "fig1e_consensus_vs_wgbs"),
    "panel_g_by_coverage":               ("Fig. 1", "f", "fig1f_consensus_by_coverage"),

    "fig2_ont_panel_tss_human":          ("Fig. 2", "b", "fig2b_human_tss_profile"),
    "fig2_ont_panel_tss_agent":          ("Fig. 2", "b", "fig2b_agent_tss_profile"),
    "fig2_ont_panel_hexbin_human_vs_wgbs": ("Fig. 2", "b", "fig2b_human_hexbin_vs_wgbs"),
    "fig2_ont_panel_hexbin_agent_vs_wgbs": ("Fig. 2", "b", "fig2b_agent_hexbin_vs_wgbs"),
    "fig2c_human_GNAS":                  ("Fig. 2", "c", "fig2c_human_gnas_modbam"),
    "fig2c_agent_GNAS":                  ("Fig. 2", "c", "fig2c_agent_gnas_modbam"),
    # Not Figure 2c. Figure 2c is the two ONT chromosome 20 arms, each drawn from its own
    # phasing run; Extended Data Fig. 3b is the same for PacBio. data/icr_bam holds the
    # whole-genome phased reads of the sample, so what these two draw is the region plot
    # the paper's two panels use, on the sample rather than on an arm. The arms' own BAMs
    # are not here. Named for what they are.
    "gnas_ont_20_60617123_60644527":     ("-", "-", "gnas_ont_whole_sample"),
    "gnas_pacbio_20_60617123_60644527":  ("-", "-", "gnas_pacbio_whole_sample"),
    # only written when NanoMethViz is absent and the paper's own output is copied in
    "panel_modbam_human_GNAS":           ("Fig. 2", "c", "fig2c_human_gnas_from_the_paper"),
    "panel_modbam_agent_GNAS":           ("Fig. 2", "c", "fig2c_agent_gnas_from_the_paper"),

    "fig2_ont_panel_wgbs_cov_human":     ("ED Fig. 1", "a", "ed1a_human_wgbs_by_coverage"),
    "fig2_ont_panel_wgbs_cov_agent":     ("ED Fig. 1", "a", "ed1a_agent_wgbs_by_coverage"),
    "ed1_cost_calling_panel_agent_cost": ("ED Fig. 1", "b", "ed1b_calling_agent_cost"),
    "ed1_cost_phasing_panel_agent_cost": ("ED Fig. 1", "b", "ed1b_phasing_agent_cost"),
    "panel_icr_human":                   ("ED Fig. 1", "c", "ed1c_human_icr_chr20"),
    "panel_icr_agent":                   ("ED Fig. 1", "c", "ed1c_agent_icr_chr20"),

    "ed2_pacbio_panel_hexbin_human_vs_wgbs": ("ED Fig. 2", "b", "ed2b_human_hexbin_vs_wgbs"),
    "ed2_pacbio_panel_hexbin_agent_vs_wgbs": ("ED Fig. 2", "b", "ed2b_agent_hexbin_vs_wgbs"),
    "ed2_pacbio_panel_wgbs_cov_human":   ("ED Fig. 2", "b", "ed2b_human_wgbs_by_coverage"),
    "ed2_pacbio_panel_wgbs_cov_agent":   ("ED Fig. 2", "b", "ed2b_agent_wgbs_by_coverage"),
    "ed2_pacbio_panel_tss_human":        ("ED Fig. 2", "b", "ed2b_human_tss_profile"),
    "ed2_pacbio_panel_tss_agent":        ("ED Fig. 2", "b", "ed2b_agent_tss_profile"),
    "ed2_pacbio_cost_panel_agent_cost":  ("ED Fig. 2", "a", "ed2a_agent_cost"),

    "ed3_pacbio_cost_panel_agent_cost":  ("ED Fig. 3", "a", "ed3a_agent_cost"),
    "ed3b_human_GNAS":                   ("ED Fig. 3", "b", "ed3b_human_gnas_modbam"),
    "ed3b_agent_GNAS":                   ("ED Fig. 3", "b", "ed3b_agent_gnas_modbam"),
    "ed3_pacbio_panel_icr_human":        ("ED Fig. 3", "b", "ed3b_human_icr_chr20"),
    "ed3_pacbio_panel_icr_agent":        ("ED Fig. 3", "b", "ed3b_agent_icr_chr20"),

    # The notebooks harvest the same panels under shorter prefixes than the batch render
    # (ed1 for fig2_ont's ED Fig. 1 panels, ed1_calling for ed1_cost_calling, and so on).
    # Both spellings name the same figure file, so both are listed.
    "ed1_panel_wgbs_cov_human":          ("ED Fig. 1", "a", "ed1a_human_wgbs_by_coverage"),
    "ed1_panel_wgbs_cov_agent":          ("ED Fig. 1", "a", "ed1a_agent_wgbs_by_coverage"),
    "ed1_calling_panel_agent_cost":      ("ED Fig. 1", "b", "ed1b_calling_agent_cost"),
    "ed1_phasing_panel_agent_cost":      ("ED Fig. 1", "b", "ed1b_phasing_agent_cost"),
    "ed2_cost_panel_agent_cost":         ("ED Fig. 2", "a", "ed2a_agent_cost"),
    "ed2_panel_tss_human":               ("ED Fig. 2", "b", "ed2b_human_tss_profile"),
    "ed2_panel_tss_agent":               ("ED Fig. 2", "b", "ed2b_agent_tss_profile"),
    "ed2_panel_wgbs_cov_human":          ("ED Fig. 2", "b", "ed2b_human_wgbs_by_coverage"),
    "ed2_panel_wgbs_cov_agent":          ("ED Fig. 2", "b", "ed2b_agent_wgbs_by_coverage"),
    "ed3_cost_panel_agent_cost":         ("ED Fig. 3", "a", "ed3a_agent_cost"),
    "ed3_panel_icr_human":               ("ED Fig. 3", "b", "ed3b_human_icr_chr20"),
    "ed3_panel_icr_agent":               ("ED Fig. 3", "b", "ed3b_agent_icr_chr20"),

    "ed4abc_hexbins":                    ("ED Fig. 4", "a-c", "ed4abc_hexbins"),
    "Ideogram_dmr_t2t_hg002_ont_blue":   ("ED Fig. 4", "d", "ed4d_ont_haplotype_dmr_ideogram"),
    "Ideogram_dmr_t2t_hg002_pacbio_blue":("ED Fig. 4", "e", "ed4e_pacbio_haplotype_dmr_ideogram"),

    "venn_cov5_nm":                      ("ED Fig. 5", "a", "ed5a_cpg_sites_venn"),
    "coverage_hist_nm":                  ("ED Fig. 5", "b", "ed5b_coverage_hist"),
    "hp_diff_by_region_nm":              ("ED Fig. 5", "c", "ed5c_hp_diff_by_region"),
    "icr_heatmap_novel_nm":              ("ED Fig. 5", "d", "ed5d_icr_novel_heatmap"),
    "icr_heatmap_known_nm":              ("ED Fig. 5", "e", "ed5e_icr_known_heatmap"),
    "tss_profile_nm":                    ("ED Fig. 5", "f", "ed5f_tss_profile"),
    "ctcf_profile_nm":                   ("ED Fig. 5", "g", "ed5g_ctcf_profile"),
    "ed5h_region_hexbins":               ("ED Fig. 5", "h", "ed5h_region_hexbins"),
}

# Rendered, and not placed in any figure: the two-arms-in-one versions of panels the paper
# draws one arm at a time. Kept, because they are what the script produces, but out of the
# way so that what is left in figures/all is the figures.
NOT_PLACED = {
    "fig2_ont_panel_tss_profile", "fig2_ont_panel_wgbs_by_coverage",
    "ed2_pacbio_panel_tss_profile", "ed2_pacbio_panel_wgbs_by_coverage",
    "ed2_pacbio_panel_agent_cost", "ed3_pacbio_panel_agent_cost",
    # both arms on one axis; the paper puts one arm on each side instead
    "panel_icr_by_region", "ed3_pacbio_panel_icr_by_region", "ed3_pacbio_panel_icr_haplotype",
    # the three-panel hexbin sheet; the paper places the two singles from it
    "fig2_ont_panel_hexbin_vs_wgbs", "fig2_ont_panel_hexbin_human_vs_agent",
    "ed2_pacbio_panel_hexbin_vs_wgbs", "ed2_pacbio_panel_hexbin_human_vs_agent",
    # the same renders under the notebooks' prefixes
    "ed1_panel_tss_profile", "ed1_panel_wgbs_by_coverage", "ed1_panel_tss_human", "ed1_panel_tss_agent",
    "ed1_panel_hexbin_vs_wgbs", "ed1_panel_hexbin_human_vs_agent", "ed1_panel_hexbin_human_vs_wgbs", "ed1_panel_hexbin_agent_vs_wgbs",
    "ed2_panel_tss_profile", "ed2_panel_wgbs_by_coverage", "ed2_panel_agent_cost",
    "ed2_panel_hexbin_vs_wgbs", "ed2_panel_hexbin_human_vs_agent", "ed2_panel_hexbin_human_vs_wgbs", "ed2_panel_hexbin_agent_vs_wgbs",
    "ed3_panel_icr_haplotype", "ed3_panel_icr_by_region", "ed3_panel_agent_cost",
}


