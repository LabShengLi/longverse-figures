#!/usr/bin/env python3
"""Generate one notebook per figure: the paper's own code in the cell, the panel underneath.

The code in every cell is read out of scripts/paper/ at generation time, not retyped. That
is the whole design constraint. An earlier version of this repository had notebook cells
written by hand from a description of each panel, and they were wrong in ways that only
showed on comparison: Figure 1e came back without its error half and without the value
labels on its bars, Figure 1f without its gain panel.

So the cells are generated, and `--check` verifies that what is in the notebooks still
matches what is in scripts/paper/. Edit a cell in a running session and it runs your
edit, which is the point of a notebook; commit a notebook whose code has drifted from the
source and the check fails.

Three kinds of cell:

    func     a function's source, inlined, then a call. Used where the paper draws one
             panel in one function.
    script   a whole script's source, inlined, with sys.argv set. Used where the paper's
             unit is a command-line program. Pasted once per notebook, not once per panel.
    rsource  an R script's source, inlined as a string, written out and run. R cannot run
             in a Python kernel, so the cell writes the file it runs; editing the string
             and re-running the cell runs the edit.

Usage:  build_notebooks.py [outdir]
        build_notebooks.py --check [outdir]
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE / "paper"

SETUP = '''import sys; sys.path.insert(0, "../scripts"); sys.path.insert(0, "../scripts/paper")
from pathlib import Path
from nbkit import setup, paper_py, paper_r, run_r_source, harvest, show, have_r_package, DATA

OUT = setup("../figures/notebook")
print("panels will be written to", OUT)

# %%R cells below run R natively in this kernel through rpy2, so the R panels are R code
# in the notebook rather than a string that gets written to a file.
%load_ext rpy2.ipython'''



def _arg(a: str) -> str:
    """Serialise one argument for a generated cell.

    Arguments that mention DATA or OUT become f-strings, so Python evaluates them when the
    cell runs. Substituting into a repr() does not work: repr quotes with single quotes and
    the substituted text uses double ones, so the result is a literal rather than an
    expression. That shipped once, and the empty path it produced reached R as setwd(""),
    which cairo then reported as a write failure.
    """
    return f'f{a!r}' if ("{DATA}" in a or "{OUT}" in a) else repr(a)


def func_source(module: str, func: str) -> str:
    """The source of one function, taken from the file rather than from memory."""
    tree = ast.parse((PAPER / module).read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func:
            return ast.get_source_segment((PAPER / module).read_text(), node)
    raise KeyError(f"{module}: no function {func}")


def script_source(script: str) -> str:
    """A whole script, minus its shebang and its __main__ guard.

    The guard is dropped because the cell calls main() itself with sys.argv already set;
    leaving it in would make the cell run twice.
    """
    text = (PAPER / script).read_text()
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    out, skip = [], False
    for ln in lines:
        if ln.startswith('if __name__ =='):
            skip = True
            continue
        if skip and (ln.startswith("    ") or not ln.strip()):
            continue
        skip = False
        out.append(ln)
    return "\n".join(out).rstrip()


def r_source(script: str) -> str:
    return (PAPER / script).read_text().rstrip()


def cell_func(module: str, func: str, call: str, shows: list[str], prefix=None) -> str:
    mod = module[:-3]
    head = (f'# From scripts/paper/{module}, the paper\'s own code. Edit and re-run freely;\n'
            f'# the file on disk is unchanged.\n'
            f'import importlib.util\n'
            f'_s = importlib.util.spec_from_file_location("{mod}", "../scripts/paper/{module}")\n'
            f'{mod} = importlib.util.module_from_spec(_s); _s.loader.exec_module({mod})\n'
            f'globals().update({{k: v for k, v in vars({mod}).items() if not k.startswith("__")}})\n\n')
    show = ", ".join(f'"{s}"' for s in shows)
    tail = f'\n\n{call}\nshow({show}{", prefix=" + repr(prefix) if prefix else ""})'
    return head + func_source(module, func) + tail


def cell_script(script: str, argv: list[str], shows: list[str], prefix=None,
                harvest_as: str | None = None) -> str:
    args = ", ".join(_arg(a) for a in argv)
    # The scripts use __file__ to find their siblings. A notebook cell has no __file__,
    # so it is defined to the path the code was copied from: the same value it would have
    # had if the script were run from scripts/paper/.
    head = (f'# scripts/paper/{script}, inlined. sys.argv is what the paper passes it.\n'
            f'import sys\n'
            f'sys.argv = [{repr(script)}, {args}]\n'
            f'__file__ = "../scripts/paper/{script}"\n\n')
    body = script_source(script)
    tail = "\n\nmain()"
    if harvest_as:
        tail += f'\nprint(harvest({harvest_as!r}), "panels collected")'
    show = ", ".join(f'"{s}"' for s in shows)
    tail += f'\nshow({show}{", prefix=" + repr(prefix) if prefix else ""})'
    return head + body + tail



def cell_rsource_argparser(script: str, argv: list[str], env: dict, shows: list[str]) -> str:
    """An R cell for a script that parses with argparser instead of commandArgs.

    argparser's parse_args(parser) reads the command line, and a notebook has no command
    line, so the call is given the vector explicitly. One line, marked, as everywhere else.
    """
    src = r_source(script)
    def rv(v):
        if v.startswith("../data/"):
            return f'file.path(Sys.getenv("LV_DATA"), "{v[len("../data/"):]}")'
        if v.startswith("../figures/notebook"):
            return 'Sys.getenv("LV_OUT")'
        return f'"{v}"'
    args = ", ".join(rv(a) for a in argv)
    marker = "args <- parse_args(parser)"
    if marker not in src:
        raise KeyError(f"{script}: no parse_args line to substitute")
    src = src.replace(
        marker,
        "## parse_args given its arguments directly; a notebook has no command line.\n"
        f"args <- parse_args(parser, c({args}))", 1)
    setenv = "\n".join(f'Sys.setenv({k} = {rv(v)})' for k, v in env.items()) if env else ""
    head = (f"%%R\n## scripts/paper/{script}, run as R. Edit any line and re-run the cell.\n"
            + (setenv + "\n\n" if setenv else "\n"))
    # The script saves by opening a device, printing, and calling graphics.off(). That
    # closes the device the %%R magic opened for the cell, and the magic's own dev.off()
    # afterwards then fails on the null device. Reopening one costs nothing and is not
    # part of the drawing: everything above has already been written to disk.
    tail = ("\n\n## The magic closes a device when the cell ends, and the script's\n"
            "## graphics.off() already closed it. Give it one to close.\n"
            "grDevices::pdf(NULL)\n")
    return head + src + tail, list(shows)


def cell_rsource(script: str, argv: list[str], env: dict, shows: list[str]) -> str:
    """An R cell: the paper's R source, run natively by rpy2's %%R magic.

    One line changes. The paper's scripts read their arguments with
    commandArgs(trailingOnly = TRUE), and a notebook has no command line, so that line is
    replaced with the vector it would have produced. The replacement is marked in the cell.
    Everything else is the file in scripts/paper/, character for character.

    The environment variables the script reads become Sys.setenv at the top, which is what
    passing them to Rscript would have done.
    """
    src = r_source(script)
    def rval0(v: str) -> str:
        if v.startswith("../data/"):
            return f'file.path(Sys.getenv("LV_DATA"), "{v[len("../data/"):]}")'
        if v.startswith("../figures/notebook"):
            return 'Sys.getenv("LV_OUT")'
        return f'"{v}"'
    args = ", ".join(rval0(a) for a in argv)
    marker = "argv <- commandArgs(trailingOnly = TRUE)"
    if marker not in src:
        raise KeyError(f"{script}: no commandArgs line to substitute")
    src = src.replace(
        marker,
        f"## commandArgs replaced for the notebook; everything else is the paper's file\n"
        f"argv <- c({args})", 1)
    def rval(v: str) -> str:
        # A path under data/ or figures/ becomes an expression over the environment
        # variables setup() exported, because the R working directory under rpy2 is not
        # the notebook's directory and a relative path would resolve elsewhere.
        if v.startswith("../data/"):
            return f'file.path(Sys.getenv("LV_DATA"), "{v[len("../data/"):]}")'
        if v.startswith("../figures/notebook"):
            return 'Sys.getenv("LV_OUT")'
        return f'"{v}"'

    setenv = "\n".join(f'Sys.setenv({k} = {rval(v)})' for k, v in env.items())
    head = (f"%%R\n"
            f"## scripts/paper/{script}, run as R. Edit any line and re-run the cell.\n"
            f"{setenv}\n\n")
    return head + src, list(shows)


def cell_r_rerun(script: str, argv: list[str], env: dict, shows: list[str]) -> str:
    """Re-run an R script already inlined in an earlier cell, with different arguments."""
    args = ", ".join(f'"{a}"' for a in argv)
    setenv = "\n".join(f'Sys.setenv({k} = "{v}")' for k, v in env.items())
    return (f"%%R\n## the same script as above, with the other platform's input\n"
            f"{setenv}\nargv <- c({args})\n"
            f"source(file.path(Sys.getenv('LV_PAPER'), '{script}'), local = FALSE)")


# notebook -> (intro markdown, [(heading, cell source)])
def books() -> dict:
    # The paper's own settings for these two panels, from fig_ed4/15_ideograms_wide.sbatch.
    # Three of them are not cosmetic. The legend moves under the plot, which gives the
    # karyogram about 3.3 in of a 3.52 in canvas instead of 2.34 in. The panels are 6.5 in
    # tall because the imprinting heatmaps left this figure on 2026-10-03 and freed the page.
    # And the point size carries the canvas ratio, 3.52/8: a ggplot point is absolute
    # millimetres, so the poster's 0.01 draws 45,329 DMRs as a solid band at paper size.
    IDEO = {"IDEOGRAM_METHDIFF": "50", "IDEOGRAM_QVALUE": "0.01", "IDEOGRAM_BASE_PT": "7",
            "IDEOGRAM_TITLE_PT": "7", "IDEOGRAM_WIDTH_IN": "3.52", "IDEOGRAM_HEIGHT_IN": "6.5",
            "IDEOGRAM_LEGEND_KEY": "2", "IDEOGRAM_TITLE": "",
            "IDEOGRAM_LEGEND_POS": "bottom", "IDEOGRAM_POINT_SIZE": "0.0044"}
    MERGED = "../data/ed_fig4/hg002_ONT_Pacbio_merged_with_annotation.mincov5.inner.csv"
    # Figure 1 e and f, from fig1_bc/10_render_ef_panels.sbatch. consensus_panels.py reads
    # all three when it is imported, so they are set before the cell loads it. The width is
    # 3.35 and not 3.5 because the tight crop counts the legend above the axes into the
    # width, and at 3.5 the pair no longer fits the 183 mm page side by side.
    FIG1_ENV = ('import os\n'
                'os.environ["PANEL_FIG_W"] = "3.35"\n'
                'os.environ["PANEL_FIG_H_SCALE"] = "1.15"\n'
                'os.environ["PANEL_LEGEND_ABOVE"] = "1"\n\n')

    return {
"01_figure1": ("""# Figure 1

Panels e and f: three methylation callers wrapped as agents by the same route, and their
site-level consensus, against the whole-genome bisulfite reference on chromosome 22.

The code in each cell is `scripts/paper/consensus_panels.py`, which is the paper's
`16_make_figure4_panels.py` copied verbatim.""", [

("## Figure 1e - three callers and their consensus\n\n"
 "Correlation on top, error below. The two do not rank the callers the same way: Rockfish "
 "edges LongVerse on r and loses to it on error, which is why the panel shows both.",
 FIG1_ENV + cell_func("consensus_panels.py", "panel_f_consensus",
           "panel_f_consensus()", ["panel_f_consensus.png"])),

("## Figure 1f - the same comparison by read depth\n\n"
 "The lower axis is where the consensus earns its keep.",
 FIG1_ENV + cell_func("consensus_panels.py", "panel_g_by_coverage",
           "panel_g_by_coverage()", ["panel_g_by_coverage.png"])),
]),

"02_figure2": ("""# Figure 2

One sentence reproduces the expert, ONT chromosome 20.

The cell below is `scripts/paper/make_panels.py` in full. It reads the per-run evaluation
records and writes several panels in one pass, so it is inlined once and the cells after it
show different panels from that run.""", [

("## Figure 2b - the same evaluation applied to each arm\n\n"
 "`human_upstream` is the expert's run, `agent_mcp_prompt` the agent's. In the paper each "
 "arm sits in its own dashed frame holding two plots; these are the right-hand one of each.",
 cell_script("make_panels.py", ["figure2", "human_upstream", "agent_mcp_prompt"],
             ["panel_tss_human.png", "panel_tss_agent.png"],
             prefix="fig2_ont", harvest_as="fig2_ont")),

("## The other half of Figure 2b, and what it is not\n\n"
 "The left-hand plot in each frame is a per-site hexbin against the bisulfite reference. "
 "Its script, `scripts/paper/make_hexbin_panel.py`, reads both arms' whole chromosome-20 "
 "per-site tables and the 540 MB bisulfite table, which this repository does not carry, so "
 "that half is not drawn here. What is below comes from the same pass as the cell above and "
 "is the measurement Extended Data Fig. 1a makes, both arms in one plot.",
 'show("panel_wgbs_by_coverage.png", prefix="fig2_ont")'),

("## Figure 2a - what the two arms were given\n\n"
 "In the paper this panel is native PowerPoint text, so the commands stay selectable. "
 "There is no image to regenerate; its content is below, from the same records.",
 '''import json
from IPython.display import Markdown, display

rec = json.load(open("../data/fig2/a_calling_run_record.json"))
cmd = open("../data/fig2/a_calling_human_command.txt").read().strip()

display(Markdown(f"**What the expert ran**\\n\\n```bash\\n{cmd}\\n```"))
display(Markdown(f"**What the agent was asked**\\n\\n> {rec.get('prompt') or rec.get('sentence') or '(see the record)'}"))
chain = rec.get("tool_chain") or [s.get("tool") for s in rec.get("steps", []) if s.get("tool")]
if chain:
    display(Markdown("**The tools it chose**\\n\\n" + "\\n".join(f"{i}. `{t}`" for i, t in enumerate(chain, 1))))'''),
]),

"03_extended_data_fig1": ("""# Extended Data Fig. 1

The remaining ONT panels: agreement by read depth for each arm on its own, and what the
agent consumed against the compute it set off.

The cost chart is `scripts/paper/make_cost_panel.py`, inlined below.""", [

("## a - agreement with the bisulfite reference, each arm separately",
 cell_script("make_panels.py", ["figure2", "human_upstream", "agent_mcp_prompt"],
             ["panel_wgbs_cov_human.png", "panel_wgbs_cov_agent.png"],
             prefix="ed1", harvest_as="ed1")),

("## b - tokens, cost and time against compute, the calling run",
 cell_script("make_cost_panel.py", ["figure2", "upstream_mcp_prompt"],
             ["panel_agent_cost.png"], prefix="ed1_calling", harvest_as="ed1_calling")),

("## b - the same for the phasing run",
 cell_script("make_cost_panel.py", ["figure3", "phasing_mcp_prompt"],
             ["panel_agent_cost.png"], prefix="ed1_phasing", harvest_as="ed1_phasing")),
]),

"04_extended_data_fig2": ("""# Extended Data Fig. 2

PacBio methylation calling, agent against expert, chromosome 20.

The paper runs this through an orchestrator that stages a run tree and a 540 MB bisulfite
table first. What draws is `make_panels.py`, the same script as Figure 2, so it is called
here with the PacBio labels.""", [

("## The two PacBio calling arms\n\n"
 "The same script as Figure 2, inlined again here so this notebook reads on its own, "
 "with the PacBio labels and PANEL_PLATFORM set so the axes say PacBio.",
 'import os\nos.environ["PANEL_PLATFORM"] = "PacBio"\n\n'
 + cell_script("make_panels.py", ["figure2", "supp3_human", "supp3_agent"],
               ["panel_tss_profile.png"], prefix="ed2", harvest_as="ed2")),

("## b - agreement with the bisulfite reference by read depth\n\n"
 "Another panel from the same pass as the cell above.",
 'show("panel_wgbs_by_coverage.png", prefix="ed2")'),
]),

"05_extended_data_fig3": ("""# Extended Data Fig. 3

PacBio phasing and per-haplotype methylation.""", [

("## The two PacBio phasing arms\n\n"
 "The same script again, on the phasing arms.",
 'import os\nos.environ["PANEL_PLATFORM"] = "PacBio"\n\n'
 + cell_script("make_panels.py", ["figure3", "supp4_human", "supp4_agent"],
               ["panel_icr_haplotype.png"], prefix="ed3", harvest_as="ed3")),
]),

"06_extended_data_fig4": ("""# Extended Data Fig. 4

ONT, PacBio and whole-genome bisulfite sequencing across the genome.

Panels d and e are drawn in R, and the R source is in the cells. Panels a to c are the one
place in this figure where the paper's script cannot run here: it reads three 450 MB point
tables.

The imprinting heatmaps used to be f and g of this figure. They moved to Extended Data
Fig. 5 d, e on 2026-10-03, so they are in notebook 07. Their input still sits in
`data/ed_fig4/`, which is where the paper's own build reads it from as well.""", [

("## a-c - per-site methylation, every pair of platforms\n\n"
 "**Not the paper's drawing code.** The hexagons are the ones the paper's own `hexbin()` "
 "computed, exported once from 56 to 62 million sites. Everything else in this notebook "
 "is the paper's.",
 '''import panels as P
import matplotlib.pyplot as plt
P.style()

specs = [("ed4_a_ont_vs_wgbs", "hexbin_a_ont_vs_wgbs_nm_stats.txt", "WGBS methylation (%)", "ONT methylation (%)"),
         ("ed4_b_pacbio_vs_wgbs", "hexbin_b_pacbio_vs_wgbs_nm_stats.txt", "WGBS methylation (%)", "PacBio methylation (%)"),
         ("ed4_c_ont_vs_pacbio", "hexbin_c_ont_vs_pacbio_nm_stats.txt", "PacBio methylation (%)", "ONT methylation (%)")]

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))
for (key, statfile, xl, yl), ax in zip(specs, axes):
    P.hexbin(key, xl, yl, P.read_hexbin_stats(DATA / "ed_fig4" / statfile), ax=ax)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"ed4abc_hexbins.{ext}", bbox_inches="tight")
plt.close(fig)
show("ed4abc_hexbins.png")'''),

("## d - haplotype DMRs along the autosomes, ONT\n\n"
 "Drawn at the published cutoff: |HP1 - HP2| at least 50 percentage points, q at most "
 "0.01. The input holds the DMRs that already clear it, 45,339 of 2.6 million tiles; the "
 "script filters again at the same threshold, so what it draws is unchanged.",
 cell_rsource("ideogram_dmr_blue.R",
              ["ont", "../figures/notebook"],
              {**IDEO, "IDEOGRAM_WDIR": "../data/ed_fig4/dmr/ont"},
              ["Ideogram_dmr_t2t_hg002_ont_blue.png"])),

("## e - the same for PacBio\n\n"
 "The same script, the other platform's DMR table.",
 cell_rsource("ideogram_dmr_blue.R",
              ["pacbio", "../figures/notebook"],
              {**IDEO, "IDEOGRAM_WDIR": "../data/ed_fig4/dmr/pacbio"},
              ["Ideogram_dmr_t2t_hg002_pacbio_blue.png"])),

]),

"07_extended_data_fig5": ("""# Extended Data Fig. 5

Coverage and regional agreement between ONT and PacBio.""", [

("## a - CpG sites covered at five or more reads by each platform",
 cell_script("venn_nm.py",
             ["{DATA}/ed_fig5/A_venn_covered_cpg_cov5_stats.tsv", "{OUT}/venn_cov5_nm"],
             ["venn_cov5_nm.png"])),

("## b - per-site coverage distributions\n\n"
 "Drawn over the whole distribution with the coverage-5 threshold marked. Truncating "
 "there would hide the left tail the panel is about.",
 cell_script("coverage_hist_nm.py", ["{DATA}/ed_fig5", "{OUT}/coverage_hist_nm"],
             ["coverage_hist_nm.png"])),

("## c - haplotype difference by region set, with paired Wilcoxon tests",
 cell_rsource("boxplot_nm.R", [MERGED, "../figures/notebook"], {"ICR_BASE_PT": "7"},
              ["hp_diff_by_region_nm.png"])),

("## d, e - imprinting control regions, HP1 minus HP2\n\n"
 "ComplexHeatmap, novel regions in d and known ones in e. The script checks its own output "
 "row by row against a reference table before it writes, so a silent change in the numbers "
 "stops it rather than producing a plausible figure. The input lives under `data/ed_fig4/` "
 "because these two panels were f and g of Extended Data Fig. 4 until 2026-10-03; the "
 "paper's own build reads them from that directory too.",
 cell_rsource("icr_heatmap_nm.R",
              [MERGED, "../data/ed_fig4", "../figures/notebook"],
              {"ICR_BASE_PT": "7"},
              ["icr_heatmap_novel_nm.png", "icr_heatmap_known_nm.png"])),

("## f - methylation around transcription start sites, three platforms",
 cell_script("profile_nm.py",
             ["{DATA}/ed_fig5/TSS_profile_3track_nozero_data.tsv",
              "{OUT}/tss_profile_nm", "TSS", "2000"],
             ["tss_profile_nm.png"])),

("## g - CTCF, the same script with the other input",
 cell_script("profile_nm.py",
             ["{DATA}/ed_fig5/CTCF_profile_3track_nozero_data.tsv",
              "{OUT}/ctcf_profile_nm", "CTCF site", "2000"],
             ["ctcf_profile_nm.png"])),

("## h - ONT against PacBio within eight genomic region classes\n\n"
 "**Not the paper's drawing code**, for the same reason as Extended Data Fig. 4a-c: the "
 "paper's script loads RData objects up to 890 MB.",
 '''import panels as P
import matplotlib.pyplot as plt
P.style()

regions = ["Promoter", "5UTR", "3UTR", "Exon", "Intron", "Intergenic", "Island", "NonIsland"]
fig, axes = plt.subplots(2, 4, figsize=(7.2, 4.2))
for reg, ax in zip(regions, axes.ravel()):
    P.hexbin(f"ed5_f_{reg}", "PacBio (%)", "ONT (%)", ax=ax)
    ax.set_title(reg)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"ed5h_region_hexbins.{ext}", bbox_inches="tight")
plt.close(fig)
show("ed5h_region_hexbins.png")'''),
]),

"08_gnas_region": ('''# Figure 2c - GNAS, per haplotype

Drawn by NanoMethViz from the phased reads. The whole-genome BAMs are 85 GB and 53 GB;
cut to the ninety imprinting control regions they are 38 and 19 MB per haplotype, which
is what `data/icr_bam/` holds.

NanoMethViz is installed from Bioconductor at build time, because bioconda carries only
2.4.0 against the 3.2.0 the paper used. That is a source build and it can fail. The first
cell says which of the two you are looking at.''', [

("## Is NanoMethViz in this environment?", 'if have_r_package("NanoMethViz"):\n    print("yes: the cells below draw the panels from data/icr_bam/")\nelse:\n    print("no: the R cells below will stop. Use the last cell, which shows")\n    print("the figure the paper\'s own run produced.")'),

("## GNAS, ONT\n\n"
 "The paper's NanoMethViz script, inlined. `parse_args` is given its arguments "
 "directly because a notebook has no command line; that one line is marked in the code.",
 cell_rsource_argparser("modbam_region_plot.R", ['--hp1_bam', '../data/icr_bam/hg002_ont_icr_HP1.bam', '--hp2_bam', '../data/icr_bam/hg002_ont_icr_HP2.bam', '--chr', 'chr20', '--start', '60617123', '--end', '60644527', '--gtf_file', '../data/icr_bam/hs1.ncbiRefSeq.icr.gtf', '--outdir', '../figures/notebook', '--outfn_prefix', 'gnas_ont', '--fig_w', '7', '--fig_h', '6', '--png'], {}, ["gnas_ont_20_60617123_60644527.png"])),

("## GNAS, PacBio\n\n"
 "The same script, the other platform's reads.",
 cell_rsource_argparser("modbam_region_plot.R", ['--hp1_bam', '../data/icr_bam/hg002_pacbio_icr_HP1.bam', '--hp2_bam', '../data/icr_bam/hg002_pacbio_icr_HP2.bam', '--chr', 'chr20', '--start', '60617123', '--end', '60644527', '--gtf_file', '../data/icr_bam/hs1.ncbiRefSeq.icr.gtf', '--outdir', '../figures/notebook', '--outfn_prefix', 'gnas_pacbio', '--fig_w', '7', '--fig_h', '6', '--png'], {}, ["gnas_pacbio_20_60617123_60644527.png"])),

("## If NanoMethViz is not here\n\n"
 "The figures the paper's own run produced, included so the repository shows every "
 "panel. These are **not** a redraw.",
 'from IPython.display import Image, display\nfor n in ("panel_modbam_human_GNAS.png", "panel_modbam_agent_GNAS.png"):\n    display(Image(filename=f"../data/reference_panels/{n}"))'),
]),
}


INDEX = """# LongVerse figures

One notebook per figure. In each cell the paper's own code is there to read and to edit,
and the panel it drew appears underneath.

| notebook | figure |
| --- | --- |
| `01_figure1.ipynb` | Figure 1e, f |
| `02_figure2.ipynb` | Figure 2a, b |
| `03_extended_data_fig1.ipynb` | ED Fig. 1a, b |
| `04_extended_data_fig2.ipynb` | ED Fig. 2, PacBio calling |
| `05_extended_data_fig3.ipynb` | ED Fig. 3, PacBio phasing |
| `06_extended_data_fig4.ipynb` | ED Fig. 4, across the genome |
| `07_extended_data_fig5.ipynb` | ED Fig. 5, coverage and regions |
| `08_gnas_region.ipynb` | Figure 2c, the GNAS region plots |
| `00_all_figures.ipynb` | every cell above, in one run |

The code in the cells is generated from `../scripts/paper/`, which holds the paper's own
scripts copied verbatim. `python ../scripts/build_notebooks.py --check` verifies that the
two still agree.
"""


def nb(cells):
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                         "language_info": {"name": "python", "version": "3.11"}},
            "nbformat": 4, "nbformat_minor": 5}


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": t.splitlines(keepends=True)}


def main(outdir="notebooks", check=False):
    out = Path(outdir)
    B = books()
    if check:
        bad = 0
        for name, (_intro, panels) in B.items():
            p = out / f"{name}.ipynb"
            if not p.is_file():
                print(f"  MISSING {p.name}"); bad += 1; continue
            have = json.loads(p.read_text())
            want = []
            for _h, c in panels:
                if isinstance(c, tuple):
                    want += [code(c[0])["source"],
                             code("show(" + ", ".join(repr(x) for x in c[1]) + ")")["source"]]
                else:
                    want.append(code(c)["source"])
            got = [c["source"] for c in have["cells"] if c["cell_type"] == "code"][1:]
            if got != want:
                print(f"  DRIFTED {p.name}: a cell no longer matches scripts/paper/")
                bad += 1
        print(f"\n  {len(B) - bad} of {len(B)} notebooks match the vendored source")
        return 1 if bad else 0

    out.mkdir(parents=True, exist_ok=True)
    # The combined notebook runs the batch driver instead of re-executing every cell.
    # Under rpy2 all %%R cells share one R session while the paper's scripts each run in
    # a fresh R process. Run them together in one session and one leaves a variable the
    # next trips over, which is what happened here: ggsave's `units` was still bound from
    # an earlier panel. render_all.py starts a process per script, so it is the faithful
    # way to draw everything at once.
    everything = [md("# Every figure, in one run\n\nThis runs `scripts/render_all.py`, which starts a fresh process per script, exactly as\nthe paper does. To read the code that draws a figure, open that figure's own notebook:\nthe code is in the cells there.\n"), code('import subprocess, sys\nr = subprocess.run([sys.executable, "../scripts/render_all.py", "../figures/notebook"],\n                   capture_output=True, text=True)\nprint(r.stdout[-4000:])\nif r.returncode != 0:\n    print("STDERR:", r.stderr[-1500:])'), code('import pandas as pd\nfrom IPython.display import display, Markdown\nlog = pd.read_csv("../figures/notebook/RENDER_LOG.tsv", sep="\\t")\ndisplay(Markdown("### What drew each panel"))\ndisplay(log)'), code('from IPython.display import Image, display, Markdown\nfrom pathlib import Path\nfor p in sorted(Path("../figures/notebook").glob("*.png")):\n    display(Markdown(f"**{p.name}**"))\n    display(Image(filename=str(p)))')]
    for name, (intro, panels) in B.items():
        cells = [md(intro), code(SETUP)]
    # A %%R cell is R all the way down, so the panel it wrote is displayed by a Python
    # cell after it. Dropping that when the R cells were converted to %%R is why Extended
    # Data Fig. 4 came back with one embedded image instead of five: the scripts had run
    # and written their files, and nothing showed them.
        for heading, body in panels:
            if isinstance(body, tuple):
                rcode, shows = body
                cells += [md(heading), code(rcode),
                          code("show(" + ", ".join(repr(x) for x in shows) + ")")]
            else:
                cells += [md(heading), code(body)]
        (out / f"{name}.ipynb").write_text(json.dumps(nb(cells), indent=1))
        n_lines = sum(len((c[0] if isinstance(c, tuple) else c).splitlines()) for _h, c in panels)
        print(f"  {name}.ipynb  {len(panels)} cells, {n_lines} lines of the paper's code")
    (out / "00_all_figures.ipynb").write_text(json.dumps(nb(everything), indent=1))
    (out / "README.md").write_text(INDEX)
    print("  00_all_figures.ipynb  runs render_all.py, one process per script")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--check"]
    sys.exit(main(args[0] if args else "notebooks", check="--check" in sys.argv))
