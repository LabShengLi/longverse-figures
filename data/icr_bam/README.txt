Phased reads at the imprinting control regions, both platforms.

Cut from the whole-genome phased BAMs (ONT 85 GB, PacBio 53 GB) to the 90 imprinting
control regions, padded 5 kb and merged into 85 intervals spanning 1.02 Mb. That is 0.005
percent of the genome and it is everything the region plots draw.

Base quality strings are replaced with "*". NanoMethViz reads the MM and ML tags, not the
qualities, and keeping them doubled the size: 306 MB with, 116 MB without. Read counts are
unchanged and every read still carries its modification tags.

    hg002_<platform>_icr_HP1.bam      haplotype 1
    hg002_<platform>_icr_HP2.bam      haplotype 2
    hs1.ncbiRefSeq.icr.gtf            the T2T annotation over these regions, 777 KB of 753 MB
    icr_regions_pad5000.bed           the intervals, with the gene names that selected them

Cut by hpc_test/analysis_claude/paper_figures/deliver/95_subset_phased_bams_to_icr.sbatch.
