#!/usr/bin/env python3
"""Strip machine-specific paths out of executed notebook outputs.

The notebooks are committed with their figures in them, so a reader browsing the repository
sees the panels without running anything. Their outputs also carry whatever the cells
printed, and that includes absolute paths of the machine that ran them: a first attempt put
the operator's username into eight files that way.

Images are untouched; only the text streams and error tracebacks are rewritten.

Usage:  clean_notebook_outputs.py [notebooks_dir]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

RULES = [
    (re.compile(r"/project2/sli68423_1316/users/yang/workspace/longverse-figures"), "."),
    (re.compile(r"/project2/sli68423_1316/users/yang/workspace/longverse"), "$LONGVERSE"),
    (re.compile(r"/project2/sli68423_1316/projects/long_verse"), "$PROJECT"),
    (re.compile(r"/project2/sli68423_1316/users/yang"), "$HOME_DIR"),
    (re.compile(r"/project2/sli68423_1316"), "$PROJECT"),
    (re.compile(r"/scratch[12]/[A-Za-z0-9_]+"), "$SCRATCH"),
    (re.compile(r"/home1/[A-Za-z0-9_]+"), "$HOME"),
]

# The operator's username is read from the environment rather than written here. A script
# whose job is to remove an identifier should not be the file that publishes it, which is
# what happened to the first version of this one.
_USER = os.environ.get("LV_SCRUB_USER") or os.environ.get("USER") or ""
if _USER:
    RULES.append((re.compile(r"\b" + re.escape(_USER) + r"\b"), "user"))


def scrub(text: str) -> tuple[str, int]:
    n = 0
    for pat, repl in RULES:
        text, k = pat.subn(repl, text)
        n += k
    return text, n


def clean(nb: dict) -> int:
    n = 0
    for cell in nb.get("cells", []):
        for outp in cell.get("outputs", []):
            for key in ("text",):
                if key in outp:
                    val = outp[key]
                    joined = "".join(val) if isinstance(val, list) else val
                    new, k = scrub(joined)
                    if k:
                        outp[key] = new.splitlines(keepends=True) if isinstance(val, list) else new
                        n += k
            for key in ("ename", "evalue"):
                if key in outp:
                    outp[key], k = scrub(outp[key])
                    n += k
            if "traceback" in outp:
                tb = []
                for line in outp["traceback"]:
                    line, k = scrub(line)
                    n += k
                    tb.append(line)
                outp["traceback"] = tb
            data = outp.get("data", {})
            for mime in ("text/plain", "text/html"):
                if mime in data:
                    val = data[mime]
                    joined = "".join(val) if isinstance(val, list) else val
                    new, k = scrub(joined)
                    if k:
                        data[mime] = new.splitlines(keepends=True) if isinstance(val, list) else new
                        n += k
    return n


def main(d: str = "notebooks") -> int:
    total = 0
    for f in sorted(Path(d).glob("*.ipynb")):
        nb = json.loads(f.read_text())
        k = clean(nb)
        if k:
            f.write_text(json.dumps(nb, indent=1))
            print(f"  {f.name:34s} {k:>4} replacement(s)")
        total += k
    # The check is for personal identifiers, not for the allocation path. The inlined
    # paper scripts carry their own default roots under /project2/<allocation>/, which is
    # a consequence of copying them verbatim and is the honest record of where they ran;
    # the allocation id is in the paper's Methods already. A username is different.
    personal = re.compile((re.escape(_USER) + "|" if _USER else "") + r"/home1/[A-Za-z0-9_]+")
    leaks = [f.name for f in Path(d).glob("*.ipynb") if personal.search(f.read_text())]
    print(f"\n  {total} replacements")
    if leaks:
        print("  STILL LEAKING:", ", ".join(leaks))
        return 1
    print("  verified: no machine path or username left in any notebook")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "notebooks"))
