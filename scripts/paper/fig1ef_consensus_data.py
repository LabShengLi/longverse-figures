#!/usr/bin/env python3
"""The evidence behind New Figure 4: LongVerse agent against NanoCortex.

Every cell carries its source. NanoCortex facts come from the preprint at
manuscript/paper2agent/2026.05.19.726254v1.full.pdf, read directly; the term counts in
`term_evidence` were produced by scanning that PDF's extracted text and can be
reproduced with 15_verify_nanocortex_terms.py. LongVerse facts come from this session's
own measurements and from the pipeline source.

The honest starting point, which the figure states rather than hides: the two systems do
not overlap. NanoCortex is a direct-RNA epitranscriptomics agent. The LongVerse agent is a
DNA methylation agent with haplotype resolution. Neither can run the other's analysis, so
there is no like-for-like result to compare. What can be compared is what each covers, how
each is built, and how each is validated.
"""
from __future__ import annotations

# 2 = the system performs this, 1 = adjacent or partial, 0 = not addressed by the paper
# Focused on the two things the comparison is about: methylation calling and phasing.
# 2 = the system performs it, 0 = the paper does not address it. Every row carries its
# source. NanoCortex rows are the term counts in its preprint, reproducible with
# 15_verify_nanocortex_terms.py; LongVerse rows are runs in this benchmark.
CAPABILITIES = [
    # (capability, nanocortex, longverse, source note)
    ("Basecalling from raw signal on THIS data", 0, 2, "measured: Dorado 1.4.0 in their image dropped the 4 kHz chemistry"),
    ("Alignment to a reference",                2, 2, "minimap2; LongVerse aligns inside dorado basecaller"),
    ("Reference build stated in the paper",     0, 2, "NanoCortex: GRCh38/hg38/T2T appear 0 times"),
    ("DNA 5mC CpG calling",                     0, 2, "measured: their container cannot basecall 4 kHz data at all, job 6080345"),
    ("Per-site DNA methylation table",          0, 2, "LongVerse UNIFY, measured here: 1,594,304 chr20 sites"),
    ("Agreement with a bisulfite reference",    0, 2, "measured here: 1,552,623 CpGs against WGBS"),
    ("Small variant calling",                   0, 2, "'Clair3' appears 0 times; LongVerse LV_CLAIR3, 14-22 min"),
    ("Read phasing into haplotypes",            0, 2, "'phasing' and 'haplotype' appear 0 times; LongVerse WhatsHap"),
    ("Haplotype-resolved methylation",          0, 2, "measured here: HP1 and HP2 tables over 7 chr20 ICRs"),
    ("Imprinting, allele-specific methylation", 0, 2, "'imprint' and 'GNAS' appear 0 times"),
    ("Submitting and polling HPC jobs",         0, 2, "'Slurm' appears 0 times; LongVerse launch and status tools"),
    ("RNA modification detection",              2, 0, "NanoCortex: m6A, pseudouridine, inosine, m5C, 2-Ome-A"),
    ("Isoform assembly and quantification",     2, 0, "StringTie and FLAIR"),
    ("Gene fusion detection",                   2, 0, "FLAIR"),
    ("RNA secondary structure",                 2, 0, "RNA-FM and RiboSketch"),
    ("Literature and database integration",     2, 0, "BLAST, PubMed, GTEx, MODOMICS"),
    ("Writes its own analysis code",            2, 0, "NanoCortex generates Bash, Python or R"),
    ("Autonomous execution, no human approval", 2, 0, "NanoCortex runs unattended; ours is blocked by cluster policy"),
]

# ---------------------------------------------------------------------------- #
# NanoCortex run on this data, 2026-09-28. Measured, not inferred.
# ---------------------------------------------------------------------------- #
# The capability table above argues from absence: a term does not appear in the preprint,
# so the system is taken not to do that thing. That is weak on its own, because a paper can
# omit what its software supports, and NanoCortex's own agent said as much when asked: DNA
# 5mC is "within my claimed scope" but "my paper does not demonstrate it".
#
# So it was run. Their container was built from their own recipe, unmodified
# (singularity/bot.def, sha256 69535b1d..., commit f9b74d3), and given the identical chr20
# POD5 the LongVerse arms received. Job 6080345, on an H200.
#
# The command is theirs, not ours: ont_plus/dorado_agent.py lines 132-134 instruct the
# model to pick from fast, hac or sup and to "ALWAYS do not indicate the chemistry type",
# and line 154 fixes the form as
#     dorado basecaller MODEL INPUT_PATH --modified-bases MODS > OUTPUT_BAM
NANOCORTEX_ATTEMPT = {
    "container_sha256": "1030aa8a514b2f9314b54713e5de0b4cbd0edaba1dce372c537b41b1a7de9773",
    "recipe_sha256": "69535b1df686b1ed57e3c22073415825bfc9b0948ef2c65a31f0450277109916",
    "commit": "f9b74d3",
    "job_id": 6080345,
    "dorado": "1.4.0+ba44a013",
    "modkit": "0.6.1",
    "input": "hg002_ont_chr20.pod5, 295,225 reads, sample_rate 4000",
    "attempts": [
        ("A1", "dorado basecaller hac <pod5> --modified-bases 5mCG_5hmCG", 1, "1s",
         "chemistry deprecated"),
        ("A2", "dorado basecaller hac <pod5>  (no modifications)", 1, "1s",
         "same error, so it is not about 5mC"),
        ("A3", "list the models present in the image", 0, "0s",
         "none; the recipe installs no model"),
        ("A4", "dorado download --model dna_r10.4.1_e8.2_400bps_hac@v4.1.0", 1, "1s",
         "not a valid model name in Dorado 1.4.0"),
        ("A5", "the NanoCortex command again, models directory supplied", 1, "1s",
         "chemistry deprecated"),
    ],
    "error": ("Failed to resolve basecaller models: The 'DNA r10.4.1 e8.2 4kHz' chemistry "
              "has been deprecated since Dorado v1.0.0. Please use a previous version "
              "which can be found at .../dorado/releases/tag/v0.9.6."),
    "root_cause": ("singularity/bot.def pins Dorado 1.4.0, and Dorado removed the R10.4.1 "
                   "4 kHz chemistry in v1.0.0. This data is 4 kHz."),
    "catalogue_v410_entries": 0,
    "catalogue_earliest_dna_model": "dna_r10.4.1_e8.2_400bps_fast@v4.2.0 (5 kHz)",
    "bams_produced": 0,
    # stated so the comparison cannot be read as a stacked deck
    "fairness": [
        "Their recipe was built unmodified and its sha256 is in the job log.",
        "Their prompt rules chose the command, not our judgement of what it should be.",
        "A first build failed on our flag, --ignore-fakeroot-command, which left apt unable "
        "to drop privileges. That failure is ours and is excluded; plain --fakeroot on a "
        "compute node builds their recipe cleanly and their own %test section passes.",
        "The remedy is theirs to take and is named by Dorado itself: pin Dorado 0.9.6 or "
        "earlier. That is a change to their recipe, so it was not made here.",
    ],
}

ARCHITECTURE = [
    # (aspect, nanocortex, longverse)
    ("Model", "Gemini 3 Pro, 2.5 Pro, 2.5 Flash", "any MCP client; measured with Claude Sonnet 4.5"),
    ("Interface", "Gemini ADK, root agent plus sub-agents", "MCP server, 13 tools and 2 prompts"),
    ("How analysis runs", "the model writes Bash, Python or R,\naudited by a Reviewer Agent, then executed",
     "fixed typed wrappers that call a pinned\npipeline; the model supplies arguments only"),
    ("Reproducibility anchor", "none stated", "pinned source tree sha256, pinned containers"),
    ("Long jobs", "not addressed; no scheduler",
     "Slurm job id returned, status polled,\nresults read when finished"),
    ("Execution autonomy", "autonomous, with error self-correction",
     "blocked here by cluster permission policy;\nthe agent proposes, the client executes"),
    ("Code availability", "github.com/wanunulab/NanoCortex", "packaged server, 302 files, sha256 recorded"),
]

VALIDATION = [
    # (aspect, nanocortex, longverse)
    ("Who scores the result", "an LLM judge (Claude) on a 0 to 1 rubric",
     "nobody; every number is computed from the output files"),
    ("Judge independence", "the judge is Claude, the system is Gemini;\nthe preprint does not flag this",
     "not applicable"),
    ("Accuracy against ground truth", "none reported",
     "against a bisulfite reference and against a person\nrunning the same pipeline"),
    ("Human expert baseline", "none",
     "the same two tasks, run from the command line"),
    ("Reproducibility anchor", "none stated",
     "pinned source tree sha256, pinned container digests"),
    ("Token and cost accounting", "none; response time only",
     "per turn and per run, from the CLI result envelope"),
    ("Session recording", "not reported",
     "replayable capture, GIF and MP4 for every run"),
    ("Measured agreement with a person", "no such measurement exists",
     "methylation r = 1.000000; haplotypes r = 1.0,\nlargest difference 0.0"),
]

# measured in this session; see 15_verify_nanocortex_terms.py
TERM_EVIDENCE = {
    "note": "occurrences in the full text of the NanoCortex preprint, 20 pages, 49,581 characters",
    "ours": ["CpG", "5mC", "5hmC", "haplotype", "phasing", "allele-specific",
             "imprint", "GNAS", "Clair3", "whatshap", "HG002", "chr20",
             "GRCh38", "T2T", "Slurm", "MCP"],
    "theirs": ["RNA", "isoform", "fusion", "pseudouridine", "epitranscript",
               "m6A", "inosine", "Remora", "StringTie", "FLAIR"],
}

# Everything here was measured in this benchmark on HG002 ONT chr20; see
# claude_prompt/2026_09_27_new_figure2_and_figure3_results.md.
LONGVERSE_MEASURED = {
    "methylation_calling": {
        "task": "Basecall and call CpG methylation for ONT data.",
        "request_words": 8,
        "agent_turns": 5, "agent_conversation_minutes": 3.1, "agent_cost_usd": 0.6737,
        "pipeline_minutes_human": 157, "pipeline_minutes_agent": 159.5,
        "tss_profile_pearson_r": 1.000000, "tss_profile_rms_difference": 1.58e-06,
        "wgbs_max_pcc_difference": 3.5e-06,
        "sites": 1594304, "wgbs_overlap": 1552623,
    },
    "phasing": {
        "task": "Phase the reads and give me methylation per haplotype.",
        "request_words": 9,
        "agent_turns": 2, "agent_conversation_minutes": 0.9, "agent_cost_usd": 0.2615,
        "pipeline_minutes_human": 104, "pipeline_minutes_agent": 44.5,
        "icr_pearson_r": 1.0, "icr_max_abs_difference": 0.0, "icr_values_compared": 12,
        "top_region": "GNAS_Ex1A", "top_abs_diff": 0.975026,
    },
    "server": {"tools": 14, "prompts": 2, "pytest_cases": 50,
               "acceptance_cases": 37, "acceptance_runtimes": 3},
}

# What NanoCortex reports, for the same rows. Every value is what the preprint gives, and
# "not reported" is not a criticism: it is a different kind of paper.
NANOCORTEX_REPORTED = {
    "evaluation": "LLM-judged capability rubric over six dimensions, plus response time",
    "baselines": "ChatGPT 5.4 and Gemini 3.0 Pro",
    "response_time_seconds": "about 5 s for simple tasks to over 800 s for interactive ones",
    "latency_trials": "9 tasks x 3 backends x 20 trials",
    "accuracy_against_ground_truth": None,
    "human_baseline": None,
    "token_or_cost_accounting": None,
    "hardware": "not stated; HPC acknowledged but no spec, no scheduler",
}
