"""Read the two arms' run records for the agent-versus-human figures (Fig 3, Fig 4).

  human_command_lines   the nextflow command the person typed, abbreviated for display and
                        wrapped by argument; the command as submitted stays in source_data
  trace_row             tasks completed, longest stage (realtime, not queue wait), failures
  tool_chain            the distinct tools the agent called, in order
"""
from __future__ import annotations

import csv
import re
import os
from pathlib import Path

WRAP_COLS = 50


def strip_paths(cmd: str) -> str:
    return re.sub(r"(/[\w.@+-]+)+/([\w.@+-]+)", r"\2", cmd)


def human_command_lines(path: Path, wrap_cols: int = WRAP_COLS) -> list[str]:
    """Site account and queue names, bind mounts, model prefixes and the -with-* provenance
    flags become placeholders. Quote state is tracked so --containerOptions '...' stays whole."""
    txt = path.read_text()
    cmd = " ".join(l.strip().rstrip("\\").strip() for l in txt.splitlines())
    cmd = re.sub(r'"\$ROOT[^"]*"', "<launch>", cmd)
    cmd = re.sub(r'"?\$REPO"?', "<repo>", cmd)
    cmd = re.sub(r"\s+", " ", cmd)
    args, cur, in_quote, skip = [], [], False, False
    for tok in cmd.split():
        if skip:
            skip = False; continue
        if tok == "-log":
            skip = True; continue
        if tok in ("nextflow", "run", "<repo>") or tok.startswith("$"):
            continue
        tok = strip_paths(tok)
        if in_quote:
            cur.append(tok)
            if tok.count("'") % 2 == 1:
                in_quote = False
            continue
        if tok.startswith("-") and cur:
            args.append(" ".join(cur)); cur = [tok]
        else:
            cur.append(tok)
        if tok.count("'") % 2 == 1:
            in_quote = True
    if cur:
        args.append(" ".join(cur))
    keep = []
    for a in args:
        flag = a.split(" ", 1)[0]
        if flag.startswith("-with-"):
            continue
        if flag == "--account":
            keep.append("--account <account>")
        elif flag in ("--gpu_queue", "--cpu_queue"):
            keep.append(f"{flag} <queue>")
        elif flag == "--containerOptions":
            keep.append("--containerOptions '--nv -B <binds>'")
        elif flag in ("--dorado_basecall_model", "--dorado_methcall_model") and "_400bps_" in a:
            keep.append(f"{flag} ...{a.split('_400bps_', 1)[-1]}")
        else:
            keep.append(a)
    lines, cur_line = ["nextflow run <repo> \\"], ""
    for a in keep:
        cand = (cur_line + " " + a).strip()
        if cur_line and len(cand) > wrap_cols:
            lines.append("    " + cur_line + " \\"); cur_line = a
        else:
            cur_line = cand
    if cur_line:
        lines.append("    " + cur_line)
    return lines


def dur_s(s: str) -> float:
    tot = 0.0
    for num, unit in re.findall(r"([\d.]+)\s*(ms|h|m|s)", s):
        tot += float(num) * {"h": 3600, "m": 60, "s": 1, "ms": 0.001}[unit]
    return tot


def fmt_s(sec: float) -> str:
    h, rem = divmod(int(round(sec)), 3600); m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def trace_row(path: Path) -> tuple[str, str, str]:
    """(tasks completed, longest stage with its name, failed tasks) from a Nextflow trace."""
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    done = sum(1 for r in rows if r["status"] in ("COMPLETED", "CACHED"))
    failed = [r["name"].split(" ")[0] for r in rows if r["status"] == "FAILED"]
    # realtime, not duration: duration counts the time the task waited in the Slurm queue
    longest = max(rows, key=lambda r: dur_s(r["realtime"]))
    return (f"{done}/{len(rows)}",
            f"{fmt_s(dur_s(longest['realtime']))} ({longest['name'].split(' ')[0]})",
            ", ".join(failed) or "none")


def tool_chain(rec: dict) -> list[str]:
    chain, seen = [], set()
    for s in rec["steps"]:
        for p in s["proposed"]:
            t = p["tool"].replace("longverse_", "")
            if t not in seen:
                chain.append(t); seen.add(t)
    return chain
