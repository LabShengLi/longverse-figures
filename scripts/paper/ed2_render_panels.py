#!/usr/bin/env python3
"""Render the Supplementary Figure 3 data panels (PacBio chr20 calling, agent vs human) at 7 pt.

Same panel scripts and the same sizes as Figure 3 (fig3/10_render_panels_nm.py), on the
PacBio arms of results/2026_10_02_suppfig34_pacbio_chr20:

  evaluation records   results/2026_09_25_longverse_agent_benchmark/evaluation/supp3_{human,agent}.json
                       (41_evaluate_run.py; the PacBio per-site table goes in as the tool's
                       "ont_bed" argument, so its rows carry tool = "ont" and the per-arm
                       panels pick them up unchanged; PANEL_PLATFORM relabels the axes PacBio)
  cost ledger          results/2026_10_02_pacbio_agent_cost/pacbio_agent_runs.csv, run_id pacbio_calling
  compute minutes      the agent arm's Nextflow run, 36 min 1 s (stdout.log "Duration")

Staging root nm_render_supp3/ so nothing under the ONT figure directories is touched.

Usage: 10_render_panels_nm.py            (matplotlib env: conda/envs/py39_v2)
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

FIGS = Path(os.environ.get("LV_FIGS", "/project2/sli68423_1316/users/yang/workspace/longverse/hpc_test/analysis_claude/agent_benchmark/figures"))
AB = Path(os.environ.get("LV_RUN", "/project2/sli68423_1316/projects/long_verse/results/2026_09_25_longverse_agent_benchmark"))
OUT = Path(os.environ.get("LV_OUT", "/project2/sli68423_1316/projects/long_verse/results/2026_10_01_paper_figures"))
SUPP = Path(os.environ.get("LV_SUPP", "/project2/sli68423_1316/projects/long_verse/results/2026_10_02_suppfig34_pacbio_chr20"))
COST = Path(os.environ.get("LV_COST", "/project2/sli68423_1316/projects/long_verse/results/2026_10_02_pacbio_agent_cost/pacbio_agent_runs.csv"))
STAGE = OUT / "nm_render_supp3"
EVAL = AB / "evaluation"
WGBS = Path(os.environ.get("LV_WGBS", "/project2/sli68423_1316/projects/long_verse/results/2026_06_08_hg002_bsseq/run_t2t/cpg/CpG.gz.bismark.cov.gz"))
DEST = OUT / "suppfig3"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, FIGS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(name: str, argv: list[str], scale: float, patch_run: bool) -> None:
    os.environ["PANEL_MIN_PT"] = "7"
    os.environ["PANEL_FIG_SCALE"] = str(scale)
    os.environ["PANEL_PLATFORM"] = "PacBio"
    sys.modules.pop("panel_style", None)
    mod = load_module(name)
    if patch_run:
        mod.RUN = STAGE
    sys.argv = [name] + argv
    rc = mod.main()
    if rc:
        raise SystemExit(f"{name} failed with {rc}")
    print(f"--- {name} done (scale {scale})")


def minutes_from_stdout(p: Path) -> float:
    import re
    m = re.search(r"Duration\s*:\s*(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?", p.read_text())
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return round(h * 60 + mi + s / 60, 1)


def main() -> int:
    for lab in ("supp3_human", "supp3_agent"):
        if not (EVAL / f"{lab}.json").is_file():
            raise SystemExit(f"MISSING evaluation record {EVAL / (lab + '.json')}: run 41_evaluate_run.py first")
    (STAGE / "figure2").mkdir(parents=True, exist_ok=True)
    (STAGE / "cost").mkdir(exist_ok=True)
    # 51_ reads RUN/cost/agent_runs.csv and RUN/figure2/compute_minutes.json by run_id
    shutil.copy(COST, STAGE / "cost" / "agent_runs.csv")
    comp = {"pacbio_calling": minutes_from_stdout(SUPP / "supp3_agent" / "launch" / "stdout.log")}
    (STAGE / "figure2" / "compute_minutes.json").write_text(json.dumps(comp, indent=1))
    print("compute minutes:", comp)

    run("50_make_panels", ["figure2", "supp3_human", "supp3_agent"], 0.60, True)
    run("51_make_cost_panel", ["figure2", "pacbio_calling"], 0.52, True)
    hu = json.load(open(EVAL / "supp3_human.json"))["inputs"]["persite_all"]
    ag = json.load(open(EVAL / "supp3_agent.json"))["inputs"]["persite_all"]
    run("53_make_hexbin_panel", [hu, ag, str(WGBS), str(STAGE / "figure2" / "panels")], 0.60, False)

    (DEST / "panels_nm").mkdir(parents=True, exist_ok=True)
    (DEST / "source_data").mkdir(exist_ok=True)
    for f in sorted((STAGE / "figure2" / "panels").glob("panel_*")):
        shutil.copy(f, DEST / "panels_nm" / f.name)
    for f in sorted((STAGE / "figure2" / "source_data").glob("*")):
        shutil.copy(f, DEST / "source_data" / f.name)
    shutil.copy(STAGE / "figure2" / "concordance.json", DEST / "source_data" / "concordance.json")
    shutil.copy(STAGE / "figure2" / "compute_minutes.json", DEST / "source_data" / "compute_minutes.json")
    print(f"suppfig3/panels_nm: {len(list((DEST / 'panels_nm').glob('*.png')))} png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
