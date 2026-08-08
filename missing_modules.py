#!/usr/bin/env python3
"""List every local module one tree needs and the other does not have.

Written 6 August 2026, after the merged `cortex_app.py` was placed in the working
copy and failed on `import cortex_entry`: a module that arrived with the site's
sign-in layer and had never been copied across. Finding those one traceback at a
time wastes a run each. This walks the import graph from a starting module and
reports the whole list in one pass.

It reads both trees and writes nothing. Pair it with reconcile_split.py, which
does the copying.

    py -3.12 missing_modules.py --from "C:\\AviaDev\\app" --to "...\\Avia QSI Tool\\app" ^
        --start cortex_app

Avia Solutions Limited. All rights reserved.
"""

import argparse
import ast
import os
import sys

# Anything importable from the interpreter itself is not our problem.
def _is_stdlib_or_installed(name):
    if name in getattr(sys, "stdlib_module_names", ()):
        return True
    try:
        import importlib.util
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _imports(path):
    """Top-level module names imported by one file. Unparseable files return nothing."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
            out.add(n.module.split(".")[0])
    return out


def _module_path(root, name):
    p = os.path.join(root, name + ".py")
    if os.path.isfile(p):
        return p
    p = os.path.join(root, name, "__init__.py")
    return p if os.path.isfile(p) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", required=True, help="the tree that has the modules")
    ap.add_argument("--to", dest="dst", required=True, help="the tree that may be missing them")
    ap.add_argument("--start", default="cortex_app",
                    help="module to walk out from (default cortex_app)")
    args = ap.parse_args()

    for p in (args.src, args.dst):
        if not os.path.isdir(p):
            sys.exit("not a directory: %s" % p)

    seen, queue, missing, unresolved = set(), [args.start], [], []
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        src_path = _module_path(args.src, name)
        dst_path = _module_path(args.dst, name)
        if src_path is None and dst_path is None:
            if not _is_stdlib_or_installed(name):
                unresolved.append(name)
            continue
        if dst_path is None:
            missing.append(name)
        # walk on from whichever copy we can read, preferring the source tree
        for dep in _imports(src_path or dst_path):
            if dep not in seen and not _is_stdlib_or_installed(dep):
                queue.append(dep)

    print("=" * 72)
    print("FROM  %s" % args.src)
    print("TO    %s" % args.dst)
    print("START %s   (%d local modules reached)" % (args.start, len(seen)))
    print("=" * 72)
    if missing:
        print("\nPRESENT IN FROM, MISSING FROM TO  (%d)" % len(missing))
        for m in sorted(missing):
            print("   %s.py" % m)
        print("\nAdd these to the reconciler manifest, or copy them, before running again.")
    else:
        print("\nNothing missing: every local module the import graph reaches exists on both sides.")
    if unresolved:
        print("\nNOT FOUND IN EITHER TREE, and not importable here  (%d)" % len(unresolved))
        for m in sorted(unresolved):
            print("   %s" % m)
        print("These are third-party packages that need installing, or a genuine gap.")
    print("=" * 72)


if __name__ == "__main__":
    main()
