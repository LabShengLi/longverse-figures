#!/usr/bin/env python3
"""Draw the data panels of New Figure 2 and New Figure 3 from the evaluation records.

One plotting function per panel type serves every arm, so anything visible is a difference
in the data and not in the drawing. Human on the left, agent on the right, without
exception. Each panel is written as PDF and PNG, and the numbers behind it as CSV.

Usage: 50_make_panels.py figure2|figure3 <human_label> <agent_label> [more agent labels]
"""
from __future__ import annotations

import csv
import json
import sys
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_style

RUN = Path(os.environ.get("LV_RUN", "/project2/sli68423_1316/projects/long_verse/results/2026_09_25_longverse_agent_benchmark"))
EVAL = RUN / "evaluation"
FONT_DIR = Path(os.environ.get("LV_FONTS", "/project2/sli68423_1316/users/yang/software/fonts"))

FONT_USED = "DejaVu Sans"
for t in ("arial.ttf", "arialbd.ttf", "ariali.ttf"):
    if (FONT_DIR / t).is_file():
        font_manager.fontManager.addfont(str(FONT_DIR / t))
if (FONT_DIR / "arial.ttf").is_file():
    FONT_USED = "Arial"
panel_style.apply(plt, FONT_USED)
HUMAN_C, AGENT_C = "#D55E00", "#0072B2"
OTHER_C = ["#009E73", "#CC79A7", "#56B4E9"]


def load(label: str) -> dict:
    p = EVAL / f"{label}.json"
    if not p.is_file():
        raise SystemExit(f"missing evaluation record: {p}")
    return json.load(open(p))


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((v - mx) ** 2 for v in xs) ** 0.5
    sy = sum((v - my) ** 2 for v in ys) ** 0.5
    return (sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / (sx * sy)) if sx and sy else float("nan")


def prof(rec: dict) -> tuple[list, list]:
    m = rec["measurements"].get("tss_profile")
    if not m or not m.get("ok"):
        return [], []
    pts = m["payload"]["profile"]
    return [p["position_bp"] for p in pts], [p["mean_methylation"] for p in pts]


def draw_profile(ax, x, y, colour, title, compact: bool = False):
    """`compact` is for the single-arm panels, which are small and carry 12 pt type.

    Five tick labels and the words "mean CpG methylation" do not fit beside a 2.5 inch
    axis at 12 pt; three ticks and "CpG methylation" do. Nothing is shortened on the
    combined panel, which has the width for it.
    """
    ax.plot(x, y, color=colour, lw=2.0)
    ax.axvline(0, color="0.6", lw=0.8, ls="--")
    ax.set_xlim(min(x), max(x)); ax.set_ylim(0, 1)
    if compact:
        ax.set_xticks([-2000, 0, 2000])
        ax.set_xticklabels(["-2 kb", "TSS", "2 kb"])
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_xlabel("distance to TSS"); ax.set_ylabel("CpG methylation")
    else:
        ax.set_xticks([-2000, -1000, 0, 1000, 2000])
        ax.set_xticklabels(["-2 kb", "-1 kb", "TSS", "1 kb", "2 kb"])
        ax.set_xlabel("distance to TSS"); ax.set_ylabel("mean CpG methylation")
    ax.set_title(title)


def panel_tss(out: Path, src: Path, human: dict, agents: list[dict]) -> dict:
    hx, hy = prof(human)
    if not hx:
        return {}
    cols = 1 + len(agents)
    fig, axes = plt.subplots(1, cols, figsize=(2.7 * cols, 2.3), sharey=True)
    axes = [axes] if cols == 1 else list(axes)
    draw_profile(axes[0], hx, hy, HUMAN_C, "Human command line")
    stats = {}
    for i, a in enumerate(agents):
        ax_, ay = prof(a)
        n = min(len(hy), len(ay))
        d = [ay[j] - hy[j] for j in range(n)]
        r = pearson(hy[:n], ay[:n])
        stats[a["arm"]] = {"n_bins": n, "pearson_r": round(r, 6),
                           "rms_difference": round((sum(v * v for v in d) / n) ** 0.5, 8),
                           "max_abs_difference": round(max(abs(v) for v in d), 8)}
        draw_profile(axes[i + 1], ax_, ay, AGENT_C if i == 0 else OTHER_C[i % 3],
                     f"Agent ({a['arm'].replace('agent_', '')})")
        axes[i + 1].set_ylabel("")
        axes[i + 1].text(0.97, 0.06,
                         f"r = {stats[a['arm']]['pearson_r']:.6f}\n"
                         f"RMS diff = {stats[a['arm']]['rms_difference']:.2e}",
                         transform=axes[i + 1].transAxes, ha="right", va="bottom", fontsize=6.5)
    fig.tight_layout()
    for e in ("pdf", "png"):
        fig.savefig(out / f"panel_tss_profile.{e}")
    plt.close(fig)

    # The same profiles again, one file per arm, so panel c can be laid out with the person
    # on the left and the agent on the right instead of as one strip. Same axes limits and
    # same drawing function, so a difference between the two files is a difference in data.
    for tag, xs, ys_, colour, title in (
            [("human", hx, hy, HUMAN_C, "TSS profile")]
            + [(f"agent", *prof(a), AGENT_C, "TSS profile") for a in agents[:1]]):
        f1, a1 = plt.subplots(figsize=(3.05, 2.95))
        draw_profile(a1, xs, ys_, colour, title, compact=True)
        f1.tight_layout()
        for e in ("pdf", "png"):
            f1.savefig(out / f"panel_tss_{tag}.{e}")
        plt.close(f1)
    with open(src / "panel_tss_profile.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["position_bp", "human"] + [a["arm"] for a in agents])
        series = [prof(a)[1] for a in agents]
        for j, x in enumerate(hx):
            w.writerow([x, f"{hy[j]:.6f}"] + [f"{s[j]:.6f}" if j < len(s) else "" for s in series])
    return stats


def panel_wgbs(out: Path, src: Path, human: dict, agents: list[dict]) -> dict:
    def rows(rec):
        m = rec["measurements"].get("wgbs_by_coverage")
        if not m or not m.get("ok"):
            return []
        return [r for r in m["payload"].get("results", []) if r.get("tool") == "ont"
                and r.get("PCC") is not None]
    hr = rows(human)
    if not hr:
        return {}
    fig, ax = plt.subplots(figsize=(3.1, 2.3))
    ax.plot([r["cov_bin_mid"] for r in hr], [r["PCC"] for r in hr], "o-",
            color=HUMAN_C, lw=1.4, ms=4, label="Human command line")
    stats = {}
    for i, a in enumerate(agents):
        ar = rows(a)
        if not ar:
            continue
        ax.plot([r["cov_bin_mid"] for r in ar], [r["PCC"] for r in ar], "s--",
                color=AGENT_C if i == 0 else OTHER_C[i % 3], lw=1.2, ms=3.5,
                label=f"Agent ({a['arm'].replace('agent_','')})")
        n = min(len(hr), len(ar))
        stats[a["arm"]] = {"bins": n,
                           "max_abs_PCC_difference": round(max(abs(ar[j]["PCC"] - hr[j]["PCC"])
                                                               for j in range(n)), 8)}
    ax.set_xlabel("ONT coverage bin (midpoint)"); ax.set_ylabel("Pearson r against WGBS")
    ax.set_ylim(0, 1); ax.legend(frameon=False, loc="lower right")
    ax.set_title("Agreement with WGBS by coverage")
    fig.tight_layout()
    for e in ("pdf", "png"):
        fig.savefig(out / f"panel_wgbs_by_coverage.{e}")
    plt.close(fig)

    # One file per arm, drawn at the width it is placed at, for the two-row panel c. The
    # axis label is shortened because at 12 pt "Pearson r against WGBS" is wider than the
    # 2.4 inch axis it labels; the caption says what the axis is.
    for tag, rec, colour, marker in (("human", human, HUMAN_C, "o-"),
                                     ("agent", agents[0] if agents else None, AGENT_C, "s-")):
        if rec is None:
            continue
        rr = rows(rec)
        if not rr:
            continue
        f1, a1 = plt.subplots(figsize=(3.05, 2.95))
        a1.plot([r["cov_bin_mid"] for r in rr], [r["PCC"] for r in rr], marker,
                color=colour, lw=2.0, ms=6)
        a1.set_xlabel("ONT coverage")
        a1.set_ylabel("r against WGBS")
        a1.set_ylim(0, 1)
        a1.set_yticks([0, 0.5, 1.0])
        a1.set_title("By coverage")
        f1.tight_layout()
        for e in ("pdf", "png"):
            f1.savefig(out / f"panel_wgbs_cov_{tag}.{e}")
        plt.close(f1)
    with open(src / "panel_wgbs_by_coverage.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["arm", "cov_bin", "cov_bin_mid", "n_cpg", "PCC", "MSE"])
        for lbl, rec in [("human", human)] + [(a["arm"], a) for a in agents]:
            for r in rows(rec):
                w.writerow([lbl, r["cov_bin"], r["cov_bin_mid"], r["n_cpg"], r["PCC"], r["MSE"]])
    return stats


def panel_icr(out: Path, src: Path, human: dict, agents: list[dict]) -> dict:
    def regions(rec):
        m = rec["measurements"].get("icr_haplotypes")
        if not m or not m.get("ok"):
            return {}
        return {r["name"]: (r["HP1_avg"], r["HP2_avg"], r["start"]) for r in m["payload"]["regions"]}
    hr = regions(human)
    if not hr:
        return {}
    order = sorted(hr, key=lambda k: int(hr[k][2]))
    cols = 1 + len(agents)
    fig, axes = plt.subplots(1, cols, figsize=(2.9 * cols, 2.5), sharey=True)
    axes = [axes] if cols == 1 else list(axes)
    stats = {}
    for i, (lbl, rec, colour) in enumerate(
            [("Human command line", human, HUMAN_C)] +
            [(f"Agent ({a['arm'].replace('agent_','')})", a,
              AGENT_C if k == 0 else OTHER_C[k % 3]) for k, a in enumerate(agents)]):
        rg = regions(rec)
        ax = axes[i]
        for j, n in enumerate(order):
            v = rg.get(n)
            if not v or v[0] is None or v[1] is None:
                continue
            ax.plot([v[0], v[1]], [j, j], color="0.75", lw=0.8, zorder=1)
            ax.scatter([v[0]], [j], s=26, facecolor="white", edgecolor=colour, lw=1.1, zorder=3)
            ax.scatter([v[1]], [j], s=26, color=colour, zorder=3)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=6.5)
        ax.set_xlim(-0.03, 1.03); ax.set_xlabel("mean CpG methylation")
        ax.set_title(lbl); ax.invert_yaxis()
        if i:
            ax.set_ylabel("")
            pairs = [(hr[n][k], rg[n][k]) for n in order if n in rg
                     for k in (0, 1) if hr[n][k] is not None and rg[n][k] is not None]
            if pairs:
                stats[agents[i - 1]["arm"]] = {
                    "values": len(pairs),
                    "pearson_r": round(pearson([p[0] for p in pairs], [p[1] for p in pairs]), 6),
                    "max_abs_difference": round(max(abs(p[1] - p[0]) for p in pairs), 8)}
    axes[0].scatter([], [], s=26, facecolor="white", edgecolor=HUMAN_C, lw=1.1, label="HP1")
    axes[0].scatter([], [], s=26, color=HUMAN_C, label="HP2")
    axes[0].legend(loc="lower right", frameon=False, fontsize=6.5)
    fig.tight_layout()
    for e in ("pdf", "png"):
        fig.savefig(out / f"panel_icr_haplotype.{e}")
    plt.close(fig)
    with open(src / "panel_icr_haplotype.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["region", "arm", "HP1", "HP2"])
        for lbl, rec in [("human", human)] + [(a["arm"], a) for a in agents]:
            rg = regions(rec)
            for n in order:
                v = rg.get(n)
                if v:
                    w.writerow([n, lbl, v[0], v[1]])
    return stats


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    which, hlabel, alabels = sys.argv[1], sys.argv[2], sys.argv[3:]
    out = RUN / which / "panels"; out.mkdir(parents=True, exist_ok=True)
    src = RUN / which / "source_data"; src.mkdir(parents=True, exist_ok=True)
    human = load(hlabel); agents = [load(a) for a in alabels]
    for r, lbl in [(human, hlabel)] + list(zip(agents, alabels)):
        r["arm"] = lbl
    summary = {"font_used": FONT_USED, "human": hlabel, "agents": alabels}
    if which == "figure2":
        summary["tss_profile"] = panel_tss(out, src, human, agents)
        summary["wgbs_by_coverage"] = panel_wgbs(out, src, human, agents)
    else:
        summary["icr_haplotype"] = panel_icr(out, src, human, agents)
    (RUN / which / "concordance.json").write_text(json.dumps(summary, indent=2))
    print(f"font: {FONT_USED}")
    print(json.dumps(summary, indent=2))
    print(f"panels -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
