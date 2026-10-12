#!/usr/bin/env python3
"""Render the Supplementary Figure 4 matplotlib panels (PacBio chr20 phasing, agent vs human) at 7 pt.

Same scripts and sizes as Figure 4 (fig3/10_render_panels_nm.py): the cost chart from the
PacBio cost ledger (run_id pacbio_phasing) and the per-arm ICR dumbbells from the
evaluation records' per-region CSVs. The NanoMethViz region panels come from
fig_supp4/55_make_modbam_panels_nm.sbatch. Staging root nm_render_supp4/.

Usage: 10_render_panels_nm.py            (matplotlib env: conda/envs/py39_v2)
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

FIGS = Path(os.environ.get("LV_FIGS", "/project2/sli68423_1316/users/yang/workspace/longverse/hpc_test/analysis_claude/agent_benchmark/figures"))
AB = Path(os.environ.get("LV_RUN", "/project2/sli68423_1316/projects/long_verse/results/2026_09_25_longverse_agent_benchmark"))
OUT = Path(os.environ.get("LV_OUT", "/project2/sli68423_1316/projects/long_verse/results/2026_10_01_paper_figures"))
COST = Path(os.environ.get("LV_COST", "/project2/sli68423_1316/projects/long_verse/results/2026_10_02_pacbio_agent_cost/pacbio_agent_runs.csv"))
STAGE = OUT / "nm_render_supp4"
EVAL = AB / "evaluation"
DEST = OUT / "suppfig4"


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


def main() -> int:
    recs = {}
    for lab in ("supp4_human", "supp4_agent"):
        p = EVAL / f"{lab}.json"
        if not p.is_file():
            raise SystemExit(f"MISSING evaluation record {p}: run 41_evaluate_run.py first")
        recs[lab] = json.load(open(p))
    (STAGE / "figure3").mkdir(parents=True, exist_ok=True)
    (STAGE / "cost").mkdir(exist_ok=True)
    shutil.copy(COST, STAGE / "cost" / "agent_runs.csv")
    shutil.copy(DEST / "source_data" / "compute_minutes.json", STAGE / "figure3" / "compute_minutes.json")

    run("51_make_cost_panel", ["figure3", "pacbio_phasing"], 0.52, True)
    csvs = []
    for lab in ("supp4_human", "supp4_agent"):
        m = recs[lab]["measurements"]["icr_haplotypes"]
        if not m.get("ok"):
            raise SystemExit(f"{lab}: icr_haplotypes measurement failed: {m.get('error')}")
        csvs.append(m["payload"]["artifacts"][0]["path"])
    run("57_make_icr_panel", csvs + [str(STAGE / "figure3" / "panels")], 0.70, False)
    # the concordance numbers for the legend (ICR agent vs human) via 50_'s figure3 mode
    run("50_make_panels", ["figure3", "supp4_human", "supp4_agent"], 0.70, True)

    (DEST / "panels_nm").mkdir(parents=True, exist_ok=True)
    for f in sorted((STAGE / "figure3" / "panels").glob("panel_*")):
        shutil.copy(f, DEST / "panels_nm" / f.name)
    for f in sorted((STAGE / "figure3" / "source_data").glob("*")):
        shutil.copy(f, DEST / "source_data" / f.name)
    shutil.copy(STAGE / "figure3" / "concordance.json", DEST / "source_data" / "concordance.json")
    print(f"suppfig4/panels_nm: {len(list((DEST / 'panels_nm').glob('*.png')))} png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
