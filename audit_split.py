#!/usr/bin/env python3
"""Compare two copies of the same tool and say exactly how they diverged.

Written 6 August 2026, after a day in which the running site and the working copy
each held half of the current tool: this folder had the new evidence file and the
old airport_capture, C:\\AviaDev\\app had the reverse. The engine raised
AttributeError on a function that exists in the other copy, and the site served an
older back-test than the one that had been wired.

This does not move, copy or change anything. It reads both trees and prints:

  1. files on one side only
  2. files on both sides that differ, and which side is newer
  3. for differing Python files, the top-level functions and classes that exist on
     one side and not the other, which is what a missing attribute looks like
  4. the track record evidence files, by name and date, on each side

Run it before deciding what to keep. Every line is a fact about the two trees; the
decision about which side wins stays with the person reading it.

    py -3.12 audit_split.py "C:\\AviaDev\\app" "C:\\Users\\...\\Avia QSI Tool\\app"

Avia Solutions Limited. All rights reserved.
"""

import argparse
import ast
import hashlib
import os
import sys
from datetime import datetime

SKIP_DIRS = {"__pycache__", ".git", ".idea", ".vscode", "node_modules", ".pytest_cache"}
# The evidence files the track record page prefers, in its own order.
EVIDENCE = ["master_backtest_scored.csv", "bt_v2_6yr.csv", "bt_v1_6yr.csv",
            "bt_v1_baseline.csv"]


def walk(root, fast=False):
    """Relative path -> (size, mtime, digest) for every file under root.

    fast skips the hash and compares size only. A folder synced by OneDrive can be
    slow to read file by file, and size plus modified time answers the question in
    almost every case; use the full hash when two files are the same size and you
    need to know whether the contents match.
    """
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            try:
                st = os.stat(full)
                if fast:
                    out[rel] = (st.st_size, st.st_mtime, "size:%d" % st.st_size)
                    continue
                h = hashlib.sha1()
                with open(full, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                out[rel] = (st.st_size, st.st_mtime, h.hexdigest())
            except OSError as e:
                out[rel] = (None, None, "unreadable: %s" % e)
    return out


def top_level_names(path):
    """Functions and classes defined at module level. Empty set if it will not parse."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return set()
    return {n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def when(ts):
    return datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M") if ts else "-"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", help="first copy, e.g. the one the service runs")
    ap.add_argument("b", help="second copy, e.g. the working folder")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--full", action="store_true",
                    help="list every differing file, not just the first 40")
    ap.add_argument("--fast", action="store_true",
                    help="compare size and date only, no hashing. Much quicker on a "
                         "OneDrive folder; two files of identical size read as the same")
    args = ap.parse_args()

    for p in (args.a, args.b):
        if not os.path.isdir(p):
            sys.exit("not a directory: %s" % p)

    A, B = walk(args.a, args.fast), walk(args.b, args.fast)
    la, lb = args.label_a, args.label_b
    print("=" * 78)
    print("%s = %s   (%d files)" % (la, args.a, len(A)))
    print("%s = %s   (%d files)" % (lb, args.b, len(B)))
    print("=" * 78)

    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    both = sorted(set(A) & set(B))
    differ = [f for f in both if A[f][2] != B[f][2]]
    same = len(both) - len(differ)

    print("\nSAME on both sides: %d" % same)
    print("DIFFER            : %d" % len(differ))
    print("ONLY IN %-10s: %d" % (la, len(only_a)))
    print("ONLY IN %-10s: %d" % (lb, len(only_b)))

    def show(title, names, side):
        if not names:
            return
        print("\n--- %s ---" % title)
        src = A if side == "a" else B
        root = args.a if side == "a" else args.b
        for f in (names if args.full else names[:40]):
            print("  %-52s %s" % (f, when(src[f][1])))
        if not args.full and len(names) > 40:
            print("  ... %d more, run with --full" % (len(names) - 40))

    show("only in %s" % la, only_a, "a")
    show("only in %s" % lb, only_b, "b")

    if differ:
        print("\n--- differing files, newer side marked ---")
        newer_a = newer_b = 0
        rows = sorted(differ, key=lambda f: -max(A[f][1] or 0, B[f][1] or 0))
        for f in (rows if args.full else rows[:40]):
            ta, tb = A[f][1] or 0, B[f][1] or 0
            mark = ("%s newer" % la) if ta > tb else ("%s newer" % lb) if tb > ta else "same time"
            if ta > tb:
                newer_a += 1
            elif tb > ta:
                newer_b += 1
            print("  %-44s %-11s  %s | %s" % (f, mark, when(ta), when(tb)))
        if not args.full and len(rows) > 40:
            print("  ... %d more, run with --full" % (len(rows) - 40))
        print("\n  newer in %s: %d      newer in %s: %d" % (la, newer_a, lb, newer_b))
        print("  A split shows as a real count on BOTH lines. One side newer on")
        print("  everything is simply a stale copy, which is the easy case.")

    # 3. what a missing attribute looks like, before it is raised at runtime
    print("\n--- functions and classes present on one side only ---")
    found = False
    for f in differ:
        if not f.endswith(".py"):
            continue
        na = top_level_names(os.path.join(args.a, f))
        nb = top_level_names(os.path.join(args.b, f))
        miss_a, miss_b = sorted(nb - na), sorted(na - nb)
        if miss_a or miss_b:
            found = True
            print("  %s" % f)
            if miss_b:
                print("      only in %-10s %s" % (la, ", ".join(miss_b)))
            if miss_a:
                print("      only in %-10s %s" % (lb, ", ".join(miss_a)))
    if not found:
        print("  none: every differing Python file defines the same names on both sides")

    # 4. the evidence the track record page reads, in the page's own preference order
    print("\n--- track record evidence files, in SOURCES order ---")
    print("  the page serves the FIRST of these that exists beside the running")
    print("  track_record.py, so the top present row on each side is what it shows")
    for name in EVIDENCE:
        ra = A.get(name)
        rb = B.get(name)
        print("  %-30s %s%-22s   %s%s"
              % (name,
                 "%s " % la, when(ra[1]) if ra else "absent",
                 "%s " % lb, when(rb[1]) if rb else "absent"))
    print("=" * 78)


if __name__ == "__main__":
    main()
