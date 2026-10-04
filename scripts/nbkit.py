"""The few lines a notebook cell needs to run one of the paper's panel scripts and show it.

This exists so a cell can be three lines long without any of those lines being plotting
code. The drawing lives in scripts/paper/, copied from the paper's repository; everything
here is plumbing: set the roots, run the script the way the paper runs it, display what it
wrote.

render_all.py imports the same functions, so the notebook and the batch render cannot
disagree about how a panel is produced.

    from nbkit import setup, paper_py, paper_r, show, exported
    OUT = setup()

    paper_py("make_panels.py", ["figure2", "human_upstream", "agent_mcp_prompt"])
    show("panel_tss_profile.png", harvest="fig2_ont")
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = REPO / "data"
PAPER = HERE / "paper"

_OUT: Path | None = None


def setup(outdir: str | Path | None = None) -> Path:
    """Point the paper's scripts at this repository and return the output directory."""
    global _OUT
    out = Path(outdir) if outdir else REPO / "figures"
    # Absolute, always: ideogram_dmr_blue.R does setwd() before it draws, so a relative
    # output path stops meaning what the caller meant and cairo reports it as a write
    # failure, which reads like a graphics fault rather than a path one.
    _OUT = out.resolve()
    _OUT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PANEL_MIN_PT", "7")
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ["PANEL_OUT_DIR"] = str(_OUT)
    os.environ["LV_RUN"] = str(DATA / "runs")
    os.environ["LV_ENS"] = str(DATA / "fig1" / "ens")
    os.environ["LV_FONTS"] = str(DATA / "fonts")
    for p in (str(PAPER), str(HERE)):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Pin R before rpy2 starts it. rpy2 has no --vanilla, so without this R reads the
    # reader's ~/.Renviron and puts their personal library ahead of this environment's.
    # On the machine this was prepared on that library held a stringi built against a
    # different ICU, and tidyverse would not attach, which took out the boxplot panel.
    # Setting these must happen before `%load_ext rpy2.ipython`, which is why it is here
    # and not in the cell that uses R.
    rhome = Path(sys.executable).parent.parent / "lib" / "R"
    if rhome.is_dir():
        os.environ["R_HOME"] = str(rhome)
        os.environ["R_LIBS"] = os.environ["R_LIBS_USER"] = str(rhome / "library")
        os.environ["R_ENVIRON_USER"] = os.devnull
        os.environ["R_PROFILE_USER"] = os.devnull
    # Absolute, and visible to R. Under rpy2 the R working directory is wherever the
    # kernel started, which is not the notebook's directory, so a relative path in an R
    # cell resolves differently than the same path in a Python cell.
    os.environ["LV_DATA"] = str(DATA)
    os.environ["LV_OUT"] = str(_OUT)
    return _OUT


def out() -> Path:
    if _OUT is None:
        raise RuntimeError("call setup() first")
    return _OUT


def _rlib() -> Path:
    return Path(sys.executable).parent.parent / "lib" / "R" / "library"


def paper_py(script: str, args: list[str], env: dict | None = None) -> None:
    """Run one of the paper's Python panel scripts, on the command line, as it is run there."""
    e = dict(os.environ)
    e.update(env or {})
    e["PYTHONPATH"] = str(PAPER) + os.pathsep + e.get("PYTHONPATH", "")
    p = subprocess.run([sys.executable, str(PAPER / script), *args],
                       capture_output=True, text=True, env=e)
    if p.returncode != 0:
        raise RuntimeError(f"{script}: " + " / ".join(
            (p.stderr or p.stdout).strip().splitlines()[-3:]))
    if p.stdout.strip():
        print(p.stdout.strip()[-800:])


def paper_r(script: str, args: list[str], env: dict | None = None) -> None:
    """Run one of the paper's R panel scripts.

    --vanilla, and R_LIBS pinned to this environment. Without both, R reads the reader's
    ~/.Renviron and puts their personal library first; on the machine this was prepared on
    that library held a stringi built against a different ICU and three of the four R
    panels would not load. A reader's R settings must not change the paper's figures.
    """
    e = dict(os.environ)
    e.update(env or {})
    rlib = _rlib()
    if rlib.is_dir():
        e["R_LIBS"] = e["R_LIBS_USER"] = str(rlib)
    rscript = Path(sys.executable).parent / "Rscript"
    cmd = [str(rscript) if rscript.exists() else "Rscript", "--vanilla",
           str(PAPER / script), *args]
    p = subprocess.run(cmd, capture_output=True, text=True, env=e)
    if p.returncode != 0:
        raise RuntimeError(f"{script}: " + " / ".join(
            (p.stderr or p.stdout).strip().splitlines()[-3:]))


def harvest(prefix: str) -> int:
    """Move what a run wrote beside the run directory into the output directory.

    make_panels.py writes to RUN/<figure2|figure3>/panels. The ONT arms and the PacBio arms
    both use those names, so one overwrites the other unless each is collected and cleared
    before the next runs: the ONT TSS profile once came back with a PacBio column.
    """
    n = 0
    for src in sorted((DATA / "runs").rglob("panels/*")):
        if src.suffix in (".png", ".pdf"):
            (out() / f"{prefix}_{src.name}").write_bytes(src.read_bytes())
            src.unlink()
            n += 1
    for src in sorted((DATA / "runs").rglob("source_data/panel_*")):
        (out() / "source_data").mkdir(exist_ok=True)
        (out() / "source_data" / f"{prefix}_{src.name}").write_bytes(src.read_bytes())
        src.unlink()
    return n


def show(*names: str, prefix: str | None = None, width: int | None = None) -> None:
    """Display panels the last call wrote. In a terminal, print where they are instead."""
    paths = [out() / (f"{prefix}_{n}" if prefix else n) for n in names]
    try:
        from IPython.display import Image, display
    except ImportError:
        for p in paths:
            print(f"  {'ok ' if p.is_file() else 'MISSING'} {p}")
        return
    for p in paths:
        if p.is_file():
            display(Image(filename=str(p), width=width))
        else:
            print(f"  not produced: {p.name}")


def have_r_package(name: str) -> bool:
    rscript = Path(sys.executable).parent / "Rscript"
    e = dict(os.environ)
    rlib = _rlib()
    if rlib.is_dir():
        e["R_LIBS"] = e["R_LIBS_USER"] = str(rlib)
    return subprocess.run(
        [str(rscript) if rscript.exists() else "Rscript", "--vanilla", "-e",
         f'quit(status = as.integer(!requireNamespace("{name}", quietly = TRUE)))'],
        capture_output=True, env=e).returncode == 0


def exported_hexbins(keys: list[tuple[str, str, str, str]], ncols: int, stem: str,
                     figsize: tuple[float, float], titles: bool = False):
    """The two panels whose paper script cannot run here: its inputs are 450 and 890 MB.

    The hexagons are the ones the paper's own hexbin() computed, exported once. Only the
    lines that turn hexagons into a picture are not the paper's.
    """
    import matplotlib.pyplot as plt
    import panels as P
    P.style()
    fig, axes = plt.subplots((len(keys) + ncols - 1) // ncols, ncols, figsize=figsize)
    axes = axes.ravel() if hasattr(axes, "ravel") else [axes]
    for (key, statfile, xl, yl), ax in zip(keys, axes):
        st = P.read_hexbin_stats(DATA / "ed_fig4" / statfile) if statfile else None
        P.hexbin(key, xl, yl, st, ax=ax)
        if titles:
            ax.set_title(key.rsplit("_", 1)[-1])
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out() / f"{stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


def run_r_source(source: str, name: str, args: list[str], env: dict | None = None) -> None:
    """Write an R script out of a notebook cell and run it.

    R does not run in a Python kernel, so a cell that wants to show R code has to hold it
    as text. Writing it to a scratch file and running that means the code in the cell is
    the code that runs: edit the string, re-run, and the edit takes effect. The file goes
    beside the output rather than over scripts/paper/, so the vendored copy stays the
    reference that build_notebooks.py --check compares against.
    """
    scratch = out() / "_edited_r"
    scratch.mkdir(exist_ok=True)
    path = scratch / name
    path.write_text(source.lstrip("\n"))
    e = dict(os.environ)
    e.update(env or {})
    rlib = _rlib()
    if rlib.is_dir():
        e["R_LIBS"] = e["R_LIBS_USER"] = str(rlib)
    rscript = Path(sys.executable).parent / "Rscript"
    cmd = [str(rscript) if rscript.exists() else "Rscript", "--vanilla", str(path), *args]
    p = subprocess.run(cmd, capture_output=True, text=True, env=e)
    if p.returncode != 0:
        raise RuntimeError(f"{name}: " + " / ".join(
            (p.stderr or p.stdout).strip().splitlines()[-3:]))
