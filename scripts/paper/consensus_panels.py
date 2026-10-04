#!/usr/bin/env python3
"""Draw the data panels of New Figure 4 as standalone images.

Panel a  capability coverage, one row per nanopore analysis
Panel d  the term evidence: how often the concepts each system is built around appear in
         the NanoCortex preprint
Panel c  how the consensus is formed: three callers, the shared sites, two combinations
Panel f  three callers wrapped as agents by the same Paper2Agent route, and their site
         level consensus, against the whole genome bisulfite reference
Panel g  the same comparison split by read depth, which is where the consensus earns its
         keep

Panels b and c are comparison tables and are built as native PowerPoint elements instead,
so they stay editable.

Outputs: figure4/panels/*.{pdf,png} and figure4/source_data/*.csv
"""
from __future__ import annotations

import csv
import importlib.util
import os
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'figures'))
import panel_style

HERE = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location("d", HERE / "14_figure4_data.py")
D = importlib.util.module_from_spec(s); s.loader.exec_module(D)

RUN = Path(os.environ.get("LV_RUN", "/project2/sli68423_1316/projects/long_verse/results/2026_09_25_longverse_agent_benchmark"))
FIG = RUN / "figure4"
PANELS = FIG / "panels"; PANELS.mkdir(parents=True, exist_ok=True)

# Poster overrides. A poster is read from two metres away and its body text is 17 to 28 pt,
# so a panel drawn for the journal at 12 pt and 6.05 in, then placed at 4.7 in, carries
# 9.5 pt text and is the smallest thing on the wall. PANEL_OUT_DIR sends the output
# somewhere else and PANEL_FIG_W redraws at the width it will actually be placed at, so
# nothing is rescaled. Unset, both are inert and the journal panels are unchanged.
OUT_DIR = Path(os.environ.get("PANEL_OUT_DIR", str(PANELS)))
OUT_DIR.mkdir(parents=True, exist_ok=True)
_FIG_W = os.environ.get("PANEL_FIG_W")
# A poster panel is half a column wide and its labels are twice the size, so the sentences
# that fit a journal figure do not fit here. PANEL_SHORT_LABELS swaps in the short forms.
# Measured at 5.5 in and 16 pt: the long y labels of the depth panel collide with each
# other, its x label runs off the right edge, and the last two gain annotations overlap.
SHORT = bool(os.environ.get("PANEL_SHORT_LABELS"))
# Where the by-depth panel puts its legend. Inside the axes it sits on the curves: the lower
# right corner holds DeepMod2 rising from r = 0.45 and the upper left holds the consensus
# curves at 11 to 14x, so at journal size the key covers the lines it describes. The poster
# already moved it above the axes; PANEL_LEGEND_ABOVE lets the paper do the same without
# taking the poster's shortened axis labels with it.
LEGEND_ABOVE = SHORT or bool(os.environ.get("PANEL_LEGEND_ABOVE"))


def L(long_text: str, short_text: str) -> str:
    return short_text if SHORT else long_text


_FIG_H_SCALE = float(os.environ.get("PANEL_FIG_H_SCALE", "1"))
_FIG_H = os.environ.get("PANEL_FIG_H")
SPLIT_F = bool(os.environ.get("PANEL_SPLIT_F"))


def _fs(w: float, h: float) -> tuple[float, float]:
    """Figure size for a poster render.

    PANEL_FIG_W sets the width, aspect preserved. PANEL_FIG_H_SCALE multiplies the height;
    PANEL_FIG_H sets it outright, in inches, and wins when both are given. All three are
    inert when unset, so the journal figures are drawn exactly as before."""
    if _FIG_W:
        target = float(_FIG_W)
        w2, h2 = target, h * target / w * _FIG_H_SCALE
    else:
        w2, h2 = w, h * _FIG_H_SCALE
    if _FIG_H:
        h2 = float(_FIG_H)
    return (w2, h2)
SRC = FIG / "source_data"; SRC.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path("/project2/sli68423_1316/users/yang/software/fonts")

FONT_USED = "DejaVu Sans"
for ttf in ("arial.ttf", "arialbd.ttf", "ariali.ttf"):
    if (FONT_DIR / ttf).is_file():
        font_manager.fontManager.addfont(str(FONT_DIR / ttf))
if (FONT_DIR / "arial.ttf").is_file():
    FONT_USED = "Arial"
panel_style.apply(plt, FONT_USED)

NC_C, LV_C, NONE_C = "#8E6FB0", "#0072B2", "#EDEDED"

# Ensemble experiment, chromosome 22. Produced by ensemble_chr22/14_ and 15_.
ENS = Path(os.environ.get("LV_ENS", "/project2/sli68423_1316/projects/long_verse/results/2026_09_28_ensemble_chr22"))
# One colour per caller, held across panels f and g so a reader learns them once. The two
# consensus series share a family so that "these are combinations" reads without a legend.
ENS_C = {
    "longverse": LV_C,
    "deepmod2": "#E69F00",
    "rockfish": "#009E73",
    "mean_longverse_deepmod2": "#7A5195",
    "mean_all": "#BC5090",
    "coverage_mean_all": "#D62728",
}
ENS_LABEL = {
    "longverse": "LongVerse",
    "deepmod2": "DeepMod2",
    "rockfish": "Rockfish",
    "mean_longverse_deepmod2": "Consensus, LongVerse + DeepMod2",
    "mean_all": "Consensus",
    "coverage_mean_all": "Weighted Consensus",
}


def _read_csv(path: Path) -> list[dict]:
    with open(path) as fh:
        return list(csv.DictReader(fh))


def panel_a() -> None:
    rows = D.CAPABILITIES
    names = [r[0] for r in rows]
    n = len(rows)
    fig, ax = plt.subplots(figsize=(5.3, 0.205 * n + 0.85))
    for i, (_, nc, lv, _src) in enumerate(rows):
        y = n - 1 - i
        for x, val, colour in ((0, nc, NC_C), (1, lv, LV_C)):
            face = colour if val == 2 else (NONE_C if val == 0 else "#FFFFFF")
            ax.add_patch(plt.Rectangle((x - 0.42, y - 0.40), 0.84, 0.80,
                                       facecolor=face, edgecolor="white", lw=1.2))
            if val == 2:
                ax.text(x, y, "+", ha="center", va="center", color="white",
                        fontsize=12, fontweight="bold")
    ax.set_xlim(-0.6, 1.6); ax.set_ylim(-0.7, n - 0.3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["NanoCortex", "LongVerse agent"], fontsize=12, fontweight="bold")
    ax.xaxis.set_ticks_position("top"); ax.xaxis.set_label_position("top")
    ax.set_yticks(range(n)); ax.set_yticklabels(names[::-1], fontsize=12)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(handles=[Patch(facecolor=NC_C, label="performed by NanoCortex"),
                       Patch(facecolor=LV_C, label="performed by the LongVerse agent"),
                       Patch(facecolor=NONE_C, label="not addressed by that paper")],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=1, frameon=False, fontsize=12)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(PANELS / f"panel_a_capability_matrix.{ext}")
    plt.close(fig)
    with open(SRC / "panel_a_capability_matrix.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["capability", "nanocortex", "longverse_agent", "source"])
        for r in rows:
            w.writerow(r)


def panel_d() -> None:
    counts = json.load(open(FIG / "nanocortex_term_counts.json"))
    ours = list(counts["ours"].items())
    theirs = list(counts["theirs"].items())
    fig, axes = plt.subplots(1, 2, figsize=(5.3, 2.5))

    ax = axes[0]
    labels = [k for k, _ in ours][::-1]
    vals = [v for _, v in ours][::-1]
    ax.barh(range(len(vals)), [max(v, 0.02) for v in vals], color=LV_C, height=0.7)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlim(0, 1); ax.set_xticks([0, 1])
    ax.set_xlabel("occurrences in the NanoCortex preprint")
    ax.set_title("terms this benchmark is built on", fontsize=12)
    for i, v in enumerate(vals):
        ax.text(0.06, i, str(v), va="center", fontsize=12, color="white" if v else LV_C,
                fontweight="bold")

    ax = axes[1]
    labels = [k for k, _ in theirs][::-1]
    vals = [v for _, v in theirs][::-1]
    ax.barh(range(len(vals)), vals, color=NC_C, height=0.7)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlabel("occurrences in the NanoCortex preprint")
    ax.set_title("terms NanoCortex is built on", fontsize=12)
    for i, v in enumerate(vals):
        ax.text(v + 1, i, str(v), va="center", fontsize=12, color=NC_C)
    ax.set_xlim(0, max(vals) * 1.18)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(PANELS / f"panel_d_term_evidence.{ext}")
    plt.close(fig)
    with open(SRC / "panel_d_term_evidence.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["term", "group", "occurrences_in_nanocortex_preprint"])
        for k, v in ours:
            w.writerow([k, "central to this benchmark", v])
        for k, v in theirs:
            w.writerow([k, "central to NanoCortex", v])


def panel_e_same_data() -> None:
    """What happened when each system was given the identical chromosome 20 POD5.

    The capability matrix argues from what a preprint does not mention, which a reader can
    fairly discount. This panel does not argue at all: both systems were handed the same
    47.5 GB file and the outcome of every attempt is printed with its exit code.

    Laid out as two lines per row, the command above and the outcome below it. A first
    version put them side by side on one line, which at the 12 pt floor left the two texts
    overlapping in the middle of the panel at every width that still fit the page.
    """
    d = D.NANOCORTEX_ATTEMPT
    # One explanatory line per attempt. A first version printed the outcome recorded in
    # the data and a note beside it, and the two said the same thing: A3 came out as
    # "none; the recipe installs no model; none; the recipe installs no model".
    short = {
        "A1": ("dorado basecaller hac <pod5> --modified-bases 5mCG_5hmCG",
               "the command NanoCortex's template produces; chemistry deprecated"),
        "A2": ("dorado basecaller hac <pod5>",
               "no modifications asked for, and the same error, so it is not about 5mC"),
        "A3": ("list the models present in the image",
               "none; their recipe installs no basecalling model"),
        "A4": ("dorado download --model ...400bps_hac@v4.1.0",
               "not a valid model name in Dorado 1.4.0"),
        "A5": ("the same command with a models directory supplied",
               "chemistry deprecated, exactly as in A1"),
    }
    rows = []
    for tag, _cmd, rc, _t, _outcome in d["attempts"]:
        cmd, line = short[tag]
        rows.append((f"{tag}  {cmd}", rc, line, "nanocortex"))
    rows.append(("LongVerse agent: one request in English, pipeline launched", 0,
                 "8 tasks, none failed, 1,594,304 chromosome 20 sites", "longverse"))

    fig, ax = plt.subplots(figsize=(9.6, 0.62 * len(rows) + 2.10))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.95, len(rows))
    for i, (text, rc, outcome, who) in enumerate(rows):
        y = len(rows) - i - 0.5
        ok = rc == 0
        colour = LV_C if who == "longverse" else NC_C
        ax.add_patch(plt.Rectangle((0.0, y - 0.10), 0.055, 0.34,
                                   color=colour if ok else "#B8B8B8",
                                   transform=ax.transData, clip_on=False))
        ax.text(0.0275, y + 0.07, "ok" if ok else "fail", ha="center", va="center",
                fontsize=panel_style.MIN_PT, color="white", fontweight="bold")
        ax.text(0.075, y + 0.07, text, ha="left", va="center",
                fontsize=panel_style.MIN_PT, color="#1A1A1A")
        ax.text(0.075, y - 0.26, outcome, ha="left", va="center",
                fontsize=panel_style.MIN_PT, color="#595959")

    ax.set_title("The same chromosome 20 POD5, given to both systems",
                 fontsize=panel_style.MIN_PT, pad=10)
    fig.text(0.0, 0.015,
             "NanoCortex, run in their container built from their own recipe "
             "(sha256 69535b1d...), with their command, job 6080345:\n"
             "\"The 'DNA r10.4.1 e8.2 4kHz' chemistry has been deprecated since Dorado "
             "v1.0.0\". Their image pins Dorado 1.4.0, whose\ncatalogue holds no @v4.1.0 "
             "model at all. No BAM was produced by any attempt.",
             fontsize=panel_style.MIN_PT, color="#595959", ha="left", va="bottom",
             linespacing=1.45)
    for ext in ("pdf", "png"):
        fig.savefig(PANELS / f"panel_e_same_data.{ext}")
    plt.close(fig)
    print(f"  panel_e_same_data  {len(rows)} rows")


def panel_b_measured() -> None:
    """What LongVerse was measured to do on the two tasks, and where NanoCortex has no
    counterpart. The empty column is the finding, so it is drawn rather than omitted."""
    M = D.LONGVERSE_MEASURED
    tasks = [("Methylation calling", M["methylation_calling"], "tss_profile_pearson_r"),
             ("Phasing", M["phasing"], "icr_pearson_r")]

    fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.4))

    ax = axes[0]
    names = [t[0] for t in tasks]
    human = [t[1]["pipeline_minutes_human"] for t in tasks]
    agent = [t[1]["pipeline_minutes_agent"] for t in tasks]
    x = range(len(tasks)); w = 0.36
    ax.bar([i - w / 2 for i in x], human, width=w, color="#D55E00", label="human command line")
    ax.bar([i + w / 2 for i in x], agent, width=w, color=LV_C, label="LongVerse agent")
    ax.set_xticks(list(x)); ax.set_xticklabels(names, fontsize=12)
    ax.set_ylabel("pipeline minutes"); ax.set_title("Both arms ran the pipeline", fontsize=12)
    ax.legend(frameon=False, fontsize=12)

    ax = axes[1]
    rs = [t[1][t[2]] for t in tasks]
    b = ax.bar(list(x), rs, color=LV_C, width=0.5)
    ax.bar_label(b, fmt="%.6f", fontsize=12, padding=2)
    ax.set_ylim(0.99, 1.005)
    ax.set_xticks(list(x)); ax.set_xticklabels(names, fontsize=12)
    ax.set_ylabel("Pearson r against the person")
    ax.set_title("Agreement, computed from files", fontsize=12)
    ax.text(0.5, 0.06, "NanoCortex reports no such measurement",
            transform=ax.transAxes, ha="center", fontsize=12, color=NC_C, style="italic")

    ax = axes[2]
    talk = [t[1]["agent_conversation_minutes"] for t in tasks]
    cost = [t[1]["agent_cost_usd"] for t in tasks]
    ax.bar([i - w / 2 for i in x], talk, width=w, color=LV_C, label="conversation, min")
    ax2 = ax.twinx()
    ax2.bar([i + w / 2 for i in x], cost, width=w, color="#009E73", label="cost, US$")
    ax.set_xticks(list(x)); ax.set_xticklabels(names, fontsize=12)
    ax.set_ylabel("minutes of conversation"); ax2.set_ylabel("US dollars")
    ax.set_title("What the agent cost", fontsize=12)
    ax2.spines["top"].set_visible(False)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=12, loc="upper left")
    ax.text(0.5, -0.42, "NanoCortex reports response time only, no tokens and no cost",
            transform=ax.transAxes, ha="center", fontsize=12, color=NC_C, style="italic")

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(PANELS / f"panel_b_measured.{ext}")
    plt.close(fig)
    with open(SRC / "panel_b_measured.csv", "w", newline="") as fh:
        w2 = csv.writer(fh)
        w2.writerow(["task", "pipeline_minutes_human", "pipeline_minutes_agent",
                     "pearson_r_against_person", "agent_conversation_minutes",
                     "agent_cost_usd", "nanocortex_counterpart"])
        for name, m, rk in tasks:
            w2.writerow([name, m["pipeline_minutes_human"], m["pipeline_minutes_agent"],
                         m[rk], m["agent_conversation_minutes"], m["agent_cost_usd"],
                         "none reported"])


def panel_c_schematic() -> None:
    """The consensus agent, drawn as a design rather than as this one experiment.

    The three callers measured here are members, not the membership. Each is an MCP server
    built by the same Paper2Agent route, so the consensus agent's contract with a member is
    the protocol, not the caller: anything that speaks MCP and returns per site calls can
    join, and the user chooses how many members to run. Dashed outlines mark what is
    pluggable rather than fixed, solid ones what was actually run for panels d and e.

    Drawn with the measured r on each member so the diagram is not merely decorative, and
    with the open slots drawn rather than described, because a diagram that showed only the
    three members would argue for a fixed trio, which is the opposite of the design.
    """
    rows = {r["series"]: r for r in _read_csv(ENS / "consensus_three_tools.csv")}
    def r_of(k):
        return float(rows[k]["pearson_r_vs_wgbs"])
    n_sites = int(rows["longverse"]["n_sites"])

    fig, ax = plt.subplots(figsize=_fs(6.4, 3.35))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.05)
    ax.axis("off")
    PT = panel_style.MIN_PT
    OPEN = "#9A9A9A"

    def box(x, y, w, h, face, lines, *, ink="white", edge=None, hatch="", dashed=False):
        ax.add_patch(plt.Rectangle(
            (x, y), w, h, facecolor=face, alpha=0.30 if dashed else 0.93,
            edgecolor=edge or (OPEN if dashed else face), linewidth=1.4, hatch=hatch,
            linestyle=(0, (4, 3)) if dashed else "solid", zorder=2))
        step = h / (len(lines) + 1)
        for i, (txt, bold) in enumerate(lines, start=1):
            ax.text(x + w / 2, y + h - i * step, txt, ha="center", va="center", zorder=3,
                    fontsize=PT, color=ink, fontweight="bold" if bold else "normal")

    def arrow(x0, y0, x1, y1, dashed=False):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=1,
                    arrowprops=dict(arrowstyle="-|>", color=OPEN, linewidth=1.4,
                                    shrinkA=0, shrinkB=0,
                                    linestyle=(0, (4, 3)) if dashed else "solid"))

    # 2.75 wide, not 2.15: "intersect per site" at 12 pt needs 1.3 in and the narrow
    # box gave it 1.38 in including padding, so the line sat on the border
    HUB_X, HUB_Y, HUB_W, HUB_H = 3.05, 2.05, 2.75, 1.95
    hub_cx, hub_cy = HUB_X + HUB_W / 2, HUB_Y + HUB_H / 2

    members = [("longverse", "LongVerse", 4.55), ("deepmod2", "DeepMod2", 3.35),
               ("rockfish", "Rockfish", 2.15)]
    for key, name, y in members:
        box(0.05, y, 2.35, 1.02, ENS_C[key],
            [(name, True), (f"r = {r_of(key):.4f}", False)])
        arrow(2.46, y + 0.51, HUB_X - 0.08, hub_cy)
    box(0.05, 0.80, 2.35, 1.02, OPEN,
        [("any MCP caller", True), ("joins the same way", False)],
        ink="#4A4A4A", dashed=True)
    arrow(2.46, 1.31, HUB_X - 0.08, hub_cy, dashed=True)

    box(HUB_X, HUB_Y, HUB_W, HUB_H, "#FFFFFF",
        [("Consensus agent", True), ("run any k members", False),
         ("intersect per site", False), (f"{n_sites:,} here", False)],
        ink="#1A1A1A", edge="#707070")

    outs = [("mean_all", "Consensus", "equal weights", 4.35),
            ("coverage_mean_all", "Weighted Consensus", "weighted by coverage", 2.75)]
    for key, name, how, y in outs:
        arrow(HUB_X + HUB_W + 0.08, hub_cy, 6.02, y + 0.60)
        box(6.10, y, 3.85, 1.20, ENS_C[key],
            [(name, True), (how, False), (f"r = {r_of(key):.4f}", False)], hatch="//")
    arrow(HUB_X + HUB_W + 0.08, hub_cy, 6.02, 1.70, dashed=True)
    box(6.10, 1.10, 3.85, 1.20, OPEN,
        [("further rules", True), ("median, trimmed mean,", False),
         ("learned weights", False)], ink="#4A4A4A", dashed=True)

    ax.text(1.22, 5.82, "members, one MCP agent each", ha="center", va="center",
            fontsize=PT, color="#595959")
    ax.text(8.02, 5.82, "combination rules", ha="center", va="center",
            fontsize=PT, color="#595959")
    ax.text(5.00, 0.30, "solid, run for panels d and e      dashed, the design allows it",
            ha="center", va="center", fontsize=PT, color="#808080")
    fig.tight_layout(pad=0.15)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"panel_c_schematic.{ext}")
    plt.close(fig)
    print("  panel_c_schematic  3 members plus an open slot, 2 rules plus an open slot")


def panel_f_consensus() -> None:
    """Three callers and their consensus against the bisulfite reference.

    All six series are scored on the same 1,381,961 chromosome 22 sites, the ones every
    caller and the truth share, so a bar can never be higher because that caller reached
    more of the chromosome. Chromosome 22 is held out from DeepMod2's training set, which
    is why the experiment is on chromosome 22 rather than on the chromosome 20 used
    elsewhere in this figure.

    The axis starts at 0.90 rather than 0, which exaggerates differences. That is the
    point of the panel, the differences are small, and the numbers are printed on the bars
    so the exaggeration cannot mislead anyone who reads them.
    """
    rows = {r["series"]: r for r in _read_csv(ENS / "consensus_three_tools.csv")}
    # The three callers and the two ways of combining all three. The pairwise means are
    # measured too and are kept in this panel's source data with a drawn_in_panel column,
    # so a reader can see that the drawn series are not the only ones that beat the singles.
    # LongVerse, Rockfish, DeepMod2, then the two rules: the same order the by-depth panel
    # draws its legend in, so e and f read down the same list (the author's call, 2026-10-04).
    order = ["longverse", "rockfish", "deepmod2", "mean_all", "coverage_mean_all"]
    vals = [float(rows[k]["pearson_r_vs_wgbs"]) for k in order]
    n_sites = int(rows["longverse"]["n_sites"])
    best_single = max(vals[:3])

    # Correlation on top, error below. A correlation alone can be read as a ranking of
    # agreement while saying nothing about how far off a call actually is, and the two do
    # not order the callers the same way here: Rockfish edges LongVerse on r and loses to
    # it on error. Showing one without the other would hide that.
    rmse = [float(rows[k]["rmse_vs_wgbs"]) for k in order]
    best_single_rmse = min(rmse[:3])

    # PANEL_SPLIT_F: the two metrics as two files, for a poster that places them apart.
    # Without it, one figure with the two axes stacked, exactly as the journal has it.
    if SPLIT_F:
        fig, ax = plt.subplots(figsize=_fs(6.4, 2.6))
        fig2, axe = plt.subplots(figsize=_fs(6.4, 2.6))
    else:
        fig, (ax, axe) = plt.subplots(2, 1, figsize=_fs(6.4, 5.05), sharey=True)
    y = list(range(len(order)))[::-1]
    colours = [ENS_C[k] for k in order]
    hatches = ["", "", "", "//", "//"]

    bars = ax.barh(y, vals, height=0.60, color=colours, hatch=hatches)
    for rect, v in zip(bars, vals):
        ax.text(v + 0.0012, rect.get_y() + rect.get_height() / 2, f"{v:.4f}",
                va="center", ha="left", fontsize=panel_style.MIN_PT)
    ax.axvline(best_single, color="#595959", lw=1.0, ls=":")
    # Above the top bar, not under the axis: at the 12 pt floor this label collided with
    # the x tick labels when it sat below the axis.
    ax.set_ylim(-0.62, len(order) - 0.02)
    ax.text(best_single - 0.0013, len(order) - 0.34, "best single caller",
            ha="right", va="center", fontsize=panel_style.MIN_PT, color="#595959")
    ax.set_yticks(y)
    ax.set_yticklabels([ENS_LABEL[k] for k in order], fontsize=panel_style.MIN_PT)
    ax.set_xlim(0.900, 0.952)
    ax.set_xlabel(L("Pearson r against WGBS, higher is better", "Pearson r vs WGBS"),
                  fontsize=panel_style.MIN_PT)
    # In poster mode the long title is wider than the 5.3 in canvas. matplotlib's tight
    # bounding box then grows to include it, the saved PNG comes out 6.6 in wide, and two
    # of them no longer fit side by side in a column. The short title is the fix at source.
    if not SPLIT_F:                      # split panels carry their own poster header
        ax.set_title(L(f"Chromosome 22, {n_sites:,} sites shared by all three callers",
                       f"chr22, {n_sites:,} shared sites"),
                     fontsize=panel_style.MIN_PT, pad=8)
    ax.tick_params(labelsize=panel_style.MIN_PT)

    ebars = axe.barh(y, rmse, height=0.60, color=colours, hatch=hatches)
    for rect, v in zip(ebars, rmse):
        axe.text(v + 0.0007, rect.get_y() + rect.get_height() / 2, f"{v:.4f}",
                 va="center", ha="left", fontsize=panel_style.MIN_PT)
    axe.axvline(best_single_rmse, color="#595959", lw=1.0, ls=":")
    if SPLIT_F:                          # no shared y axis to inherit these from
        axe.set_ylim(-0.62, len(order) - 0.02)
        axe.set_yticks(y)
        axe.set_yticklabels([ENS_LABEL[k] for k in order], fontsize=panel_style.MIN_PT)
    axe.set_xlim(0.120, 0.158)
    axe.set_xlabel(L("Root mean squared error against WGBS, lower is better",
                     "RMSE vs WGBS, lower is better"), fontsize=panel_style.MIN_PT)
    axe.tick_params(labelsize=panel_style.MIN_PT)

    for a in (ax, axe):
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    if SPLIT_F:
        for f_, stem in ((fig, "panel_f_pearson"), (fig2, "panel_f_rmse")):
            f_.tight_layout()
            for ext in ("pdf", "png"):
                f_.savefig(OUT_DIR / f"{stem}.{ext}")
            plt.close(f_)
    else:
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(OUT_DIR / f"panel_f_consensus.{ext}")
        plt.close(fig)

    with open(SRC / "panel_f_consensus.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["series", "pearson_r_vs_wgbs", "rmse_vs_wgbs", "n_sites",
                    "is_consensus", "drawn_in_panel"])
        for k in ["longverse", "deepmod2", "rockfish", "mean_longverse_deepmod2",
                  "mean_longverse_rockfish", "mean_deepmod2_rockfish", "mean_all",
                  "coverage_mean_all"]:
            if k not in rows:
                continue
            w.writerow([ENS_LABEL.get(k, k), rows[k]["pearson_r_vs_wgbs"],
                        rows[k]["rmse_vs_wgbs"], rows[k]["n_sites"],
                        "no" if k in ("longverse", "deepmod2", "rockfish") else "yes",
                        "yes" if k in order else "no"])
    print(f"  panel_f_consensus  {len(order)} series over {n_sites:,} sites, "
          f"r and RMSE")


def panel_g_by_coverage() -> None:
    """The same comparison split by read depth.

    Binned by the MINIMUM coverage across the three callers, because that is the depth
    actually available to a consensus and because one binning variable keeps every curve
    on the same rows.

    The lower axis is the finding. Averaging callers buys almost nothing where the data is
    already deep and buys a great deal where it is thin, which is what averaging noise is
    supposed to do. A panel showing only the upper axis would let a reader conclude the
    consensus is uniformly slightly better, which is not what was measured.
    """
    rows = _read_csv(ENS / "consensus_by_coverage.csv")
    bins = sorted({(int(r["bin_lo"]), r["bin"]) for r in rows})
    labels = [b[1] for b in bins]
    x = list(range(len(bins)))
    by = {}
    for r in rows:
        by.setdefault(r["series"], {})[r["bin"]] = float(r["pearson_r_vs_wgbs"])
    n_by_bin = {}
    for r in rows:
        n_by_bin[r["bin"]] = int(r["n_sites"])

    singles = ["longverse", "deepmod2", "rockfish"]
    shown = ["longverse", "rockfish", "deepmod2", "mean_all", "coverage_mean_all"]

    fig, (ax, axd) = plt.subplots(2, 1, figsize=_fs(6.4, 4.9), sharex=True,
                                  gridspec_kw={"height_ratios": [2.15, 1.0]})
    # LongVerse and Rockfish sit on top of each other at almost every depth, which is the
    # result, but a solid green line over a solid blue one just hides the blue. Rockfish is
    # dashed so both are readable where they coincide.
    for k in shown:
        thick = k in ("mean_all", "coverage_mean_all")
        ax.plot(x, [by[k][b] for b in labels], marker="o",
                ms=5.5 if thick else 4.0, lw=2.6 if thick else 1.6,
                ls="--" if k in ("rockfish", "mean_all") else "-",
                color=ENS_C[k], label=ENS_LABEL[k], zorder=3 if thick else 2)
    ax.set_ylabel(L("Pearson r vs WGBS", "Pearson r"), fontsize=panel_style.MIN_PT)
    # Poster: the legend goes ABOVE the axes, in a row. At double height there is no empty
    # corner inside the plot: lower right sat on DeepMod2's rise from r = 0.45, upper left
    # sat on the consensus curves at 11 to 14x. Outside the axes it can cover nothing. The
    # in-figure title is dropped in the same mode, the poster's panel header already names
    # the panel. The journal figure keeps its signed off layout.
    if LEGEND_ABOVE:
        # Two columns, always. matplotlib fills a column at a time, so five entries land as
        # three and two: the three callers on the left, the two consensus rules on the right,
        # which is the split the panel is about. One column was five rows of key above a plot
        # that needed the height for its curves (the author's call, 2026-10-04). Three columns
        # were tried earlier and the row holding Consensus and Weighted Consensus came out
        # wider than the axes.
        ax.legend(frameon=False, fontsize=panel_style.MIN_PT, loc="lower center",
                  bbox_to_anchor=(0.5, 1.0), ncol=2,
                  columnspacing=1.0, handlelength=1.4)
    else:
        ax.legend(frameon=False, fontsize=panel_style.MIN_PT, loc="lower right")
    ax.tick_params(labelsize=panel_style.MIN_PT)
    # The title lives where the legend now is, so one of them has to go: the deck's panel
    # header already says what this panel shows, and the legend cannot be read anywhere else.
    if not LEGEND_ABOVE:
        ax.set_title("Agreement by read depth, chromosome 22",
                     fontsize=panel_style.MIN_PT, pad=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

    gain = [by["coverage_mean_all"][b] - max(by[k][b] for k in singles) for b in labels]
    axd.bar(x, gain, width=0.55, color=ENS_C["coverage_mean_all"])
    # tick_pt is set below; on a narrow canvas the gain labels take that size too, since
    # at the floor size 0.008 and 0.005 touched at 4.2 in of width
    for xi, g in zip(x, gain):
        axd.text(xi, g + 0.0016, f"{g:.3f}" if SHORT else f"{g:+.3f}",
                 ha="center", va="bottom",
                 fontsize=panel_style.MIN_PT - 2 if (SHORT and fig.get_figwidth() < 5.5) else panel_style.MIN_PT)
    axd.axhline(0, color="#1A1A1A", lw=0.8)
    axd.set_ylim(0, max(gain) * 1.38)
    axd.set_ylabel(L("gain over\nbest single", "gain"), fontsize=panel_style.MIN_PT)
    axd.set_xticks(x)
    # Six bins in under 5 in of canvas: at the floor size "15-19" and "20-29" touch, so
    # the tick labels drop two points there and the size used is printed at build time.
    tick_pt = panel_style.MIN_PT - 2 if (SHORT and fig.get_figwidth() < 5.5) else panel_style.MIN_PT
    if tick_pt != panel_style.MIN_PT:
        print(f"  panel_g_by_coverage: x tick labels at {tick_pt:g} pt on a "
              f"{fig.get_figwidth():.2f} in canvas (floor {panel_style.MIN_PT:g})")
    axd.set_xticklabels([f"{l}\n{n_by_bin[l]/1000:.0f}k" for l in labels], fontsize=tick_pt)
    axd.set_xlabel(L("minimum coverage across the three callers, and sites per bin",
                     "minimum coverage, sites per bin"), fontsize=panel_style.MIN_PT)
    axd.tick_params(labelsize=panel_style.MIN_PT)
    for sp in ("top", "right"):
        axd.spines[sp].set_visible(False)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"panel_g_by_coverage.{ext}")
    plt.close(fig)

    with open(SRC / "panel_g_by_coverage.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["coverage_bin", "n_sites", "series", "pearson_r_vs_wgbs",
                    "gain_of_coverage_weighted_consensus_over_best_single"])
        for b in labels:
            g = by["coverage_mean_all"][b] - max(by[k][b] for k in singles)
            for k in by:
                w.writerow([b, n_by_bin[b], ENS_LABEL.get(k, k), f"{by[k][b]:.6f}",
                            f"{g:.6f}" if k == "coverage_mean_all" else ""])
    print(f"  panel_g_by_coverage  {len(labels)} depth bins, "
          f"gain {min(gain):+.4f} to {max(gain):+.4f}")


if __name__ == "__main__":
    panel_a()
    panel_b_measured()
    panel_e_same_data()
    panel_d()
    panel_c_schematic()
    panel_f_consensus()
    panel_g_by_coverage()
    print(f"font: {FONT_USED}")
    for p in sorted(PANELS.glob("*.png")):
        print(f"  {p.name:<38} {p.stat().st_size/1024:6.0f} KB")
