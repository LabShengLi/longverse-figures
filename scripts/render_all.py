#!/usr/bin/env python3
"""Render every panel, using the paper's own code wherever the paper's own inputs fit.

Two kinds of panel live here and the difference is worth stating plainly, because it is the
difference between reproducing a figure and redrawing one.

    PAPER CODE    scripts/paper/ holds the paper's rendering scripts, copied verbatim
                  except that their hard-coded roots read an environment variable. The
                  inputs they need are small enough to ship: per-run evaluation records are
                  23 to 33 KB, the consensus tables are 1 to 2 KB, the imprinting tables
                  are 19 KB. These panels are the paper's panels.

    EXPORTED      two panels cannot work that way. The whole-genome hexbins read 450 MB
                  point tables and the region hexbins read RData objects up to 890 MB. For
                  those, the hexagons the paper's own hexbin() computed were exported once
                  (data/plot_layer/) and are drawn here. The data is identical; the twenty
                  lines that turn hexagons into a picture are not the paper's.

Usage:  render_all.py [outdir]        default ../figures
        PANEL_MIN_PT=7 by default, the Nature Methods size.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = REPO / "data"
PAPER = HERE / "paper"

os.environ.setdefault("PANEL_MIN_PT", "7")
os.environ.setdefault("LV_RUN", str(DATA / "runs"))
os.environ.setdefault("LV_ENS", str(DATA / "fig1" / "ens"))
os.environ.setdefault("LV_FONTS", str(DATA / "fonts"))
os.environ.setdefault("MPLBACKEND", "Agg")

# The vendored scripts import their siblings by bare name (`import panel_style`),
# exactly as they do in the paper repository, so that directory has to be importable
# before any of them is loaded.
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(HERE))

results: list[tuple[str, str, str]] = []     # panel, how, outcome


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def record(panel: str, how: str, fn):
    try:
        fn()
        results.append((panel, how, "ok"))
        print(f"  ok    {panel:34s} {how}")
    except Exception as exc:                     # noqa: BLE001 - one panel must not stop the rest
        results.append((panel, how, f"{type(exc).__name__}: {exc}"))
        print(f"  FAIL  {panel:34s} {how}  {type(exc).__name__}: {exc}")


def pyrun(panel: str, script: str, args: list[str], env: dict | None = None):
    """Call a vendored script the way the paper calls it, on the command line.

    These modules read sys.argv and exit; importing and poking at their internals would be
    a different program. Running them as programs keeps them the paper's.
    """
    def run():
        e = dict(os.environ)
        e.update(env or {})
        e["PYTHONPATH"] = str(PAPER) + os.pathsep + e.get("PYTHONPATH", "")
        p = subprocess.run([sys.executable, str(PAPER / script), *args],
                           capture_output=True, text=True, env=e)
        if p.returncode != 0:
            tail = (p.stderr or p.stdout).strip().splitlines()[-3:]
            raise RuntimeError(" / ".join(tail) or f"exit {p.returncode}")
    record(panel, f"paper code: {script}", run)


def harvest(prefix: str, out: Path) -> int:
    """Move what a run just wrote beside the run directory into out/, under a prefix.

    make_panels.py writes to RUN/<which>/panels, where <which> is figure2 or figure3. The
    ONT arms and the PacBio arms both use those two names, so running one after the other
    overwrites the first: the ONT tss profile came back with a supp3_agent column. Harvest
    immediately, prefix by display item, and clear the directory so the next run cannot
    inherit a stale file either.
    """
    n = 0
    for src in sorted((DATA / "runs").rglob("panels/*")):
        if src.suffix in (".png", ".pdf"):
            (out / f"{prefix}_{src.name}").write_bytes(src.read_bytes())
            src.unlink()
            n += 1
    for src in sorted((DATA / "runs").rglob("source_data/panel_*")):
        (out / "source_data").mkdir(exist_ok=True)
        (out / "source_data" / f"{prefix}_{src.name}").write_bytes(src.read_bytes())
        src.unlink()
    return n


def rscript(panel: str, script: str, args: list[str], env: dict | None = None):
    def run():
        e = dict(os.environ)
        e.update(env or {})
        # --vanilla, and R_LIBS pinned to this environment's own library.
        #
        # Without both, R reads the user's ~/.Renviron and puts their personal library
        # first. On the machine this was built on that library held a stringi compiled
        # against a different ICU, and every package that depends on it - ggbio, tidyverse,
        # so three of the four R panels - failed to load with a missing libicui18n.so.67.
        # Nothing was wrong with the installed packages. A reader's own R settings must not
        # be able to change the paper's figures.
        rlib = Path(sys.executable).parent.parent / "lib" / "R" / "library"
        if rlib.is_dir():
            e["R_LIBS"] = str(rlib)
            e["R_LIBS_USER"] = str(rlib)
        cmd = [str(Path(sys.executable).parent / "Rscript"), "--vanilla",
               str(PAPER / script), *args]
        if not Path(cmd[0]).exists():
            cmd[0] = "Rscript"
        p = subprocess.run(cmd, capture_output=True, text=True, env=e)
        if p.returncode != 0:
            tail = (p.stderr or p.stdout).strip().splitlines()[-3:]
            raise RuntimeError(" / ".join(tail) or f"exit {p.returncode}")
    record(panel, f"paper code, R: {script}", run)


def main(outdir: str = None) -> int:
    # Absolute, always. ideogram_dmr_blue.R does setwd(IDEOGRAM_WDIR) before it draws, so a
    # relative output path stops pointing where the caller meant and cairo reports it as
    # "error while writing to output stream", which reads like a graphics fault rather than
    # a path one.
    out = (Path(outdir) if outdir else REPO / "figures").resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.environ["PANEL_OUT_DIR"] = str(out)

    print("== Figure 1 e,f  (paper code)")
    cp = load("consensus_panels", PAPER / "consensus_panels.py")
    record("Fig 1e consensus", "paper code", cp.panel_f_consensus)
    record("Fig 1f by coverage", "paper code", cp.panel_g_by_coverage)

    print("== Extended Data Fig. 4 f,g  imprinting heatmaps (paper code, R)")
    merged = DATA / "ed_fig4" / "hg002_ONT_Pacbio_merged_with_annotation.mincov5.inner.csv"
    rscript("ED4 f,g ICR heatmaps", "icr_heatmap_nm.R",
            [str(merged), str(DATA / "ed_fig4"), str(out)], {"ICR_BASE_PT": "7"})

    print("== Extended Data Fig. 5c  haplotype difference boxplot (paper code, R)")
    rscript("ED5 c HP difference", "boxplot_nm.R",
            [str(merged), str(out)], {"ICR_BASE_PT": "7"})

    print("== Extended Data Fig. 4 d,e  DMR ideograms (paper code, R)")
    for key, plat in (("ed4_d_ont", "ont"), ("ed4_e_pacbio", "pacbio")):
        wdir = DATA / "ed_fig4" / "dmr" / plat
        rscript(f"ED4 {'d' if plat == 'ont' else 'e'} ideogram {plat}",
                "ideogram_dmr_blue.R", [plat, str(out)],
                {"IDEOGRAM_WDIR": str(wdir), "IDEOGRAM_METHDIFF": "50",
                 "IDEOGRAM_QVALUE": "0.01", "IDEOGRAM_BASE_PT": "7",
                 "IDEOGRAM_TITLE_PT": "7", "IDEOGRAM_WIDTH_IN": "3.5",
                 "IDEOGRAM_HEIGHT_IN": "3.3", "IDEOGRAM_LEGEND_KEY": "2",
                 "IDEOGRAM_TITLE": ""})

    print("== Extended Data Fig. 5 a,b,d,e  (paper code)")
    pyrun("ED5 a Venn", "venn_nm.py",
          [str(DATA / "ed_fig5" / "A_venn_covered_cpg_cov5_stats.tsv"), str(out / "venn_cov5_nm")])
    pyrun("ED5 b coverage histogram", "coverage_hist_nm.py",
          [str(DATA / "ed_fig5"), str(out / "coverage_hist_nm")])
    pyrun("ED5 d TSS profile", "profile_nm.py",
          [str(DATA / "ed_fig5" / "TSS_profile_3track_nozero_data.tsv"),
           str(out / "tss_profile_nm"), "TSS", "2000"])
    pyrun("ED5 e CTCF profile", "profile_nm.py",
          [str(DATA / "ed_fig5" / "CTCF_profile_3track_nozero_data.tsv"),
           str(out / "ctcf_profile_nm"), "CTCF site", "2000"])

    print("== Figure 2 b,c and Extended Data Fig. 1  (paper code)")
    pyrun("Fig 2b,c + ED1 ONT panels", "make_panels.py",
          ["figure2", "human_upstream", "agent_mcp_prompt"])
    print(f"    harvested {harvest('fig2_ont', out)} files")
    pyrun("ED1 b cost, calling", "make_cost_panel.py", ["figure2", "upstream_mcp_prompt"])
    print(f"    harvested {harvest('ed1_cost_calling', out)} files")
    pyrun("ED1 b cost, phasing", "make_cost_panel.py", ["figure3", "phasing_mcp_prompt"])
    print(f"    harvested {harvest('ed1_cost_phasing', out)} files")

    print("== Extended Data Figs 2 and 3, the PacBio arms  (paper code)")
    # The paper runs these through fig_supp3/10_render_panels_nm.py, an orchestrator that
    # stages a run tree and a 540 MB bisulfite table before calling the panel modules. The
    # modules are what draw, and they read the per-run evaluation records, which are here.
    # So they are called directly, with the PacBio labels, rather than reproducing the
    # staging.
    pyrun("ED2 PacBio calling panels", "make_panels.py",
          ["figure2", "supp3_human", "supp3_agent"], {"PANEL_PLATFORM": "PacBio"})
    print(f"    harvested {harvest('ed2_pacbio', out)} files")
    pyrun("ED3 PacBio phasing panels", "make_panels.py",
          ["figure3", "supp4_human", "supp4_agent"], {"PANEL_PLATFORM": "PacBio"})
    print(f"    harvested {harvest('ed3_pacbio', out)} files")

    print("== Figure 2c and Extended Data Fig. 1c  GNAS region plots (paper code, R)")
    # The paper draws these with NanoMethViz from the per-haplotype BAMs. Those are 85 GB
    # and 53 GB whole-genome; cut to the imprinting control regions they are 38 and 19 MB,
    # which is what data/icr_bam holds. If NanoMethViz is not in the environment the panel
    # falls back to the figure the paper's own run produced, and the log says which.
    icr = DATA / "icr_bam"
    gnas = ("chr20", 60617123, 60644527)
    have_nmv = subprocess.run(
        [str(Path(sys.executable).parent / "Rscript"), "--vanilla", "-e",
         'quit(status = as.integer(!requireNamespace("NanoMethViz", quietly = TRUE)))'],
        capture_output=True, env={**os.environ,
                                  "R_LIBS": str(Path(sys.executable).parent.parent / "lib/R/library"),
                                  "R_LIBS_USER": str(Path(sys.executable).parent.parent / "lib/R/library")}
    ).returncode == 0
    if have_nmv:
        for plat in ("ont", "pacbio"):
            rscript(f"Fig 2c GNAS {plat}", "modbam_region_plot.R",
                    ["--hp1_bam", str(icr / f"hg002_{plat}_icr_HP1.bam"),
                     "--hp2_bam", str(icr / f"hg002_{plat}_icr_HP2.bam"),
                     "--chr", gnas[0], "--start", str(gnas[1]), "--end", str(gnas[2]),
                     "--gtf_file", str(icr / "hs1.ncbiRefSeq.icr.gtf"),
                     "--outdir", str(out), "--outfn_prefix", f"gnas_{plat}",
                     "--fig_w", "7", "--fig_h", "6", "--png"])
    else:
        def fallback():
            n = 0
            for f in sorted((DATA / "reference_panels").glob("*GNAS*.png")):
                (out / f.name).write_bytes(f.read_bytes())
                n += 1
            if not n:
                raise RuntimeError("NanoMethViz absent and no reference panel to fall back to")
        record("Fig 2c GNAS", "paper output, NOT regenerated (NanoMethViz absent)", fallback)

    print("== hexbins drawn from the exported hexagon layer")
    import panels as P                                           # noqa: E402
    P.style()
    def hexfig():
        import matplotlib.pyplot as plt
        specs = [("ed4_a_ont_vs_wgbs", "a_ont_vs_wgbs", "WGBS methylation (%)", "ONT methylation (%)"),
                 ("ed4_b_pacbio_vs_wgbs", "b_pacbio_vs_wgbs", "WGBS methylation (%)", "PacBio methylation (%)"),
                 ("ed4_c_ont_vs_pacbio", "c_ont_vs_pacbio", "PacBio methylation (%)", "ONT methylation (%)")]
        fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))
        for (key, stem, xl, yl), ax in zip(specs, axes):
            st = P.read_hexbin_stats(DATA / "ed_fig4" / f"hexbin_{stem}_nm_stats.txt")
            P.hexbin(key, xl, yl, st, ax=ax)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(out / f"ed4abc_hexbins.{ext}", bbox_inches="tight")
        plt.close(fig)
    record("ED4 a-c hexbins", "exported hexagons", hexfig)

    def regionfig():
        import matplotlib.pyplot as plt
        regions = ["Promoter", "5UTR", "3UTR", "Exon", "Intron", "Intergenic", "Island", "NonIsland"]
        fig, axes = plt.subplots(2, 4, figsize=(7.2, 4.2))
        for reg, ax in zip(regions, axes.ravel()):
            P.hexbin(f"ed5_f_{reg}", "PacBio (%)", "ONT (%)", ax=ax)
            ax.set_title(reg)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(out / f"ed5f_region_hexbins.{ext}", bbox_inches="tight")
        plt.close(fig)
    record("ED5 f region hexbins", "exported hexagons", regionfig)

    # make_panels.py and make_cost_panel.py write beside their run directory, as they do in
    # the paper repository; PANEL_OUT_DIR is only honoured by the panel scripts that were
    # written for the poster. Collect what they produced rather than patching where they
    # put it, which would be an edit to the paper's code.
    n_ok = sum(1 for _, _, r in results if r == "ok")
    print(f"\n  {n_ok} of {len(results)} panels rendered")
    for p, how, r in results:
        if r != "ok":
            print(f"    {p}: {r}")
    with open(out / "RENDER_LOG.tsv", "w") as fh:
        fh.write("panel\tdrawn_by\toutcome\n")
        for row in results:
            fh.write("\t".join(row) + "\n")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
