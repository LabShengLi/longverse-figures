#!/usr/bin/env python3
"""Generate the notebooks.

The notebook runs scripts/render_all.py and then shows what it produced. It does not
contain a second copy of the plotting code, because two copies drift: the first version of
this repository had notebook cells that redrew the panels by hand, and they quietly lost
Figure 1e's error half and Figure 1f's gain bars.

Usage:  build_notebooks.py [outdir]        default ./notebooks
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INTRO = """# LongVerse figures

Every panel below is drawn by the paper's own code. `scripts/paper/` holds those scripts
copied verbatim from the paper's repository, with one edit each: the directory they read
from is an environment variable instead of an absolute path on a cluster.

Run all cells: **Run -> Run All Cells**. It takes about a minute.

Two panels are the exception and say so where they appear: the whole-genome hexbins and the
region hexbins are drawn from exported hexagons, because the paper's scripts for them read
450 MB and 890 MB inputs. The hexagons are the ones the paper's own `hexbin()` computed.
"""

RENDER = '''import subprocess, sys
from pathlib import Path

out = Path("../figures/notebook")
r = subprocess.run([sys.executable, "../scripts/render_all.py", str(out)],
                   capture_output=True, text=True)
print(r.stdout[-3000:])
if r.returncode != 0:
    print("STDERR:", r.stderr[-2000:])
'''

SHOW = '''import pandas as pd
from IPython.display import Image, display, Markdown

log = pd.read_csv(out / "RENDER_LOG.tsv", sep="\\t")
display(Markdown("### What drew each panel"))
display(log)
'''

GALLERY = '''from IPython.display import Image, display, Markdown

GROUPS = {
    "Figure 1e, f  -  three callers and their consensus": [
        "panel_f_consensus.png", "panel_g_by_coverage.png"],
    "Figure 2b, c  -  one sentence reproduces the expert, ONT chr20": [
        "fig2_ont_panel_tss_profile.png", "fig2_ont_panel_wgbs_by_coverage.png"],
    "Extended Data Fig. 1  -  the remaining ONT panels": [
        "ed1_cost_calling_panel_agent_cost.png", "ed1_cost_phasing_panel_agent_cost.png",
        "fig2_ont_panel_wgbs_cov_human.png", "fig2_ont_panel_wgbs_cov_agent.png"],
    "Extended Data Fig. 2  -  PacBio methylation calling, agent against expert": [
        "ed2_pacbio_panel_tss_profile.png", "ed2_pacbio_panel_wgbs_by_coverage.png"],
    "Extended Data Fig. 3  -  PacBio phasing": [
        "ed3_pacbio_panel_icr_haplotype.png"],
    "Extended Data Fig. 4  -  ONT, PacBio and WGBS across the genome": [
        "ed4abc_hexbins.png",
        "Ideogram_dmr_t2t_hg002_ont_blue.png", "Ideogram_dmr_t2t_hg002_pacbio_blue.png",
        "icr_heatmap_novel_nm.png", "icr_heatmap_known_nm.png"],
    "Extended Data Fig. 5  -  coverage and regional agreement": [
        "venn_cov5_nm.png", "coverage_hist_nm.png", "hp_diff_by_region_nm.png",
        "tss_profile_nm.png", "ctcf_profile_nm.png", "ed5f_region_hexbins.png"],
}

for title, names in GROUPS.items():
    display(Markdown(f"## {title}"))
    for n in names:
        p = out / n
        if p.is_file():
            display(Image(filename=str(p)))
        else:
            display(Markdown(f"*{n} was not produced; see the table above*"))
'''

FIG2A = '''from IPython.display import Markdown, display
import json

# Figure 2a is not an image in the paper. It is built as native PowerPoint text so the
# commands stay selectable, which means there is no PNG to regenerate. What it shows is
# below, read from the same run records the panel is built from.
rec = json.load(open("../data/fig2/a_calling_run_record.json"))
cmd = open("../data/fig2/a_calling_human_command.txt").read()

display(Markdown("### What the expert ran"))
display(Markdown(f"```bash\\n{cmd.strip()}\\n```"))

display(Markdown("### What the agent was asked"))
display(Markdown(f"> {rec.get('prompt') or rec.get('sentence') or '(see the record)'}"))

chain = rec.get("tool_chain") or [s.get("tool") for s in rec.get("steps", []) if s.get("tool")]
if chain:
    display(Markdown("### The tools it chose, in order"))
    display(Markdown("\\n".join(f"{i}. `{t}`" for i, t in enumerate(chain, 1))))

cost = rec.get("cost") or rec.get("usage") or {}
if cost:
    display(Markdown("### What it consumed"))
    display(Markdown("\\n".join(f"- {k}: {v}" for k, v in cost.items())))
'''

GNAS = '''from IPython.display import Image, display, Markdown
from pathlib import Path

# The GNAS region plots are drawn by NanoMethViz from the per-haplotype BAMs, which are
# 1.2 GB each. They are not regenerated here; these are the figures the paper's own script
# produced, included so the repository shows every panel.
display(Markdown("## Figure 2c and Extended Data Fig. 1c  -  GNAS, per haplotype"
                 "\\n\\n*Not regenerated in this notebook: the paper's script reads two "
                 "1.2 GB haplotype BAMs. These are its output.*"))
for n in ("panel_modbam_human_GNAS.png", "panel_modbam_agent_GNAS.png"):
    p = Path("../data/reference_panels") / n
    if p.is_file():
        display(Image(filename=str(p)))
'''


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


def main(outdir="notebooks"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    cells = [
        md(INTRO),
        md("## Draw everything\n\nThis runs the paper's panel scripts."),
        code(RENDER),
        code(SHOW),
        code(GALLERY),
        md("---"),
        code(FIG2A),
        md("---"),
        code(GNAS),
    ]
    (out / "00_all_figures.ipynb").write_text(json.dumps(nb(cells), indent=1))
    print(f"  wrote 00_all_figures.ipynb  ({len(cells)} cells)")
    for stale in out.glob("0[1-9]_*.ipynb"):
        stale.unlink()
        print(f"  removed stale {stale.name}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "notebooks")
