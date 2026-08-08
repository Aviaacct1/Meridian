#!/usr/bin/env python3
"""What in this tool is built, and what is built but nothing calls.

Written 7 August 2026. In one day four capabilities were found that had been
built, tested and then gone quiet without anything failing:

  * airport_capture_factors.json was not beside the module that loads it, and the
    loader returned a neutral 1.0 for every airport inside a bare except.
  * corrected_fc_over_out was empty on every row, so the track record page drew
    the same series twice under a heading that claimed a correction.
  * qsi_feed and dep_time_mins, the schedule-quality connecting feed, are set by
    backtest.py and by nothing else, so no live forecast has ever used them.
  * departure_time_grid.py searches departure times against hub waves and is
    imported by nothing the live engine runs.

None of those show up as an error. They show up as a tool that is quietly less
capable than the person using it believes. This finds them, by asking four
questions of the tree rather than of any one file:

  1. WHICH MODULES DOES NOTHING IMPORT. Split into command-line tools, which are
     meant to stand alone, and modules that are neither imported nor runnable.
  2. WHICH CONFIG KEYS ARE READ AND NEVER SET. A module that reads
     cfg["mct_banking"] and no file anywhere writes it is a switch with no hand
     on it.
  3. WHICH DATA FILES ARE LOADED BY PATH AND ARE NOT THERE. The 6 August failure.
  4. WHERE FAILURE IS SWALLOWED. Every `except: pass` and every except that
     returns a default, which is the shape all four of the above took.

It reads only. Run it before a git migration so the first commit lands with a
written record of what is live and what is orphaned, and again whenever a
capability seems to have gone missing.

    py -3.12 capability_audit.py --tree "C:\\AviaDev\\app"
    py -3.12 capability_audit.py --tree "C:\\AviaDev\\app" --out capability_audit.md

Avia Solutions Limited. All rights reserved.
"""

import argparse
import ast
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {"__pycache__", ".git", ".idea", ".vscode", "node_modules", "venv",
             ".venv", "_dt_cache", "site-packages", ".pytest_cache"}

# Names that hold configuration rather than data, so a string subscript on them
# is a switch rather than a row lookup.
CONFIG_NAMES = {"cfg", "config", "feed_cfg", "opts", "options", "params", "settings",
                "conf", "kw", "kwargs", "ctx", "meta"}

DATA_SUFFIX = (".json", ".csv", ".tsv", ".joblib", ".pkl", ".pickle", ".parquet",
               ".duckdb", ".xlsx", ".txt")


def walk_py(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def parse(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return ast.parse(fh.read()), fh
    except Exception:
        return None, None


def source(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
def scan(root):
    """Every module, keyed by the name an import would actually resolve to.

    This used to key on the bare filename, so a nested copy of a module silently
    replaced the top-level one: `app_avia_style/cortex_app.py`, the frozen July
    rollback, overwrote the live `cortex_app.py` and the audit then reported the
    frozen file's line numbers and environment variables as though they were the
    running tool's. A silent overwrite, in the tool written to find silent
    overwrites, and it produced a confident and wrong finding before it was caught
    by a file hash.

    Modules at the top of the tree win, because that is what `import x` resolves to
    with the tree on the path. Any shadowed copy is recorded and reported.
    """
    mods, shadowed = {}, []
    for path in sorted(walk_py(root), key=lambda p: (p.count(os.sep), p)):
        rel = os.path.relpath(path, root).replace("\\", "/")
        name = os.path.splitext(os.path.basename(path))[0]
        src = source(path)
        try:
            tree = ast.parse(src)
        except Exception:
            tree = None
        if name in mods:
            shadowed.append((rel, mods[name]["rel"]))
            continue
        mods[name] = {"path": path, "rel": rel, "src": src, "tree": tree}
    return mods, shadowed


def imports_of(tree):
    out = set()
    if tree is None:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
            out.add(n.module.split(".")[0])
    # __import__("name") is how cortex_app reached airport_capture, and an import
    # graph that misses it reports a live module as an orphan.
    return out


def dynamic_imports(src):
    return set(re.findall(r'__import__\(\s*["\']([A-Za-z_][\w]*)["\']', src)) | \
           set(re.findall(r'importlib\.import_module\(\s*["\']([A-Za-z_][\w]*)["\']', src))


def config_reads(tree):
    """Keys read off a config-looking mapping: cfg.get("k") or cfg["k"]."""
    out = set()
    if tree is None:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "get" and n.args:
            base = n.func.value
            if isinstance(base, ast.Name) and base.id in CONFIG_NAMES \
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                out.add(n.args[0].value)
        elif isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
                and n.value.id in CONFIG_NAMES:
            k = n.slice
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.add(k.value)
    return out


def config_writes(tree):
    """Keys assigned onto a config-looking mapping: cfg["k"] = ..."""
    out = set()
    if tree is None:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) \
                        and t.value.id in CONFIG_NAMES:
                    k = t.slice
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        out.add(k.value)
        # cfg.update({"k": ...}) and dict(cfg, k=...) are also writes
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "update" and isinstance(n.func.value, ast.Name) \
                and n.func.value.id in CONFIG_NAMES:
            for a in n.args:
                if isinstance(a, ast.Dict):
                    for k in a.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            out.add(k.value)
    return out


def kwarg_names(tree):
    """Keyword arguments any function in this module accepts.

    A config key often arrives as a named parameter rather than a dict write, and
    counting that as a write stops the report crying wolf on every option.
    """
    out = set()
    if tree is None:
        return out
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            out |= {x.arg for x in list(a.args) + list(a.kwonlyargs)}
        if isinstance(n, ast.Call):
            out |= {k.arg for k in n.keywords if k.arg}
    return out


def env_vars(src):
    return set(re.findall(r'environ\.get\(\s*["\']([A-Z][A-Z0-9_]*)["\']', src)) | \
           set(re.findall(r'environ\[\s*["\']([A-Z][A-Z0-9_]*)["\']', src))


def data_files(src):
    out = set()
    for m in re.finditer(r'["\']([\w\-./\\]+(?:%s))["\']' % "|".join(
            s.replace(".", r"\.") for s in DATA_SUFFIX), src):
        p = m.group(1)
        if not p.startswith(("http", "//")):
            out.add(p)
    return out


def swallows(tree):
    """except blocks that hide the failure: pass, or return a constant."""
    out = []
    if tree is None:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler):
            body = n.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                out.append((n.lineno, "pass"))
            elif len(body) == 1 and isinstance(body[0], ast.Return) \
                    and isinstance(body[0].value, ast.Constant):
                out.append((n.lineno, "return %r" % (body[0].value.value,)))
            elif len(body) == 1 and isinstance(body[0], ast.Assign) \
                    and isinstance(body[0].value, ast.Constant):
                out.append((n.lineno, "assign a default"))
    return out


def has_main(src):
    return "__main__" in src


# ---------------------------------------------------------------------------
def report(root, out_path=None):
    mods, shadowed = scan(root)
    names = set(mods)

    imported_by = defaultdict(set)
    for name, m in mods.items():
        for dep in imports_of(m["tree"]) | dynamic_imports(m["src"]):
            if dep in names and dep != name:
                imported_by[dep].add(name)

    reads, writes, kwargs = {}, {}, set()
    for name, m in mods.items():
        reads[name] = config_reads(m["tree"])
        writes[name] = config_writes(m["tree"])
        kwargs |= kwarg_names(m["tree"])

    all_writes = set()
    for w in writes.values():
        all_writes |= w

    L = []
    a = L.append
    a("# Capability audit")
    a("")
    a("Tree: `%s`" % root)
    a("")
    a("%d Python modules, by the name an import resolves to." % len(mods))
    a("")
    if shadowed:
        a("### Shadowed copies (%d)" % len(shadowed))
        a("")
        a("Same module name in more than one place. The shallower one wins on the "
          "import path and is the one audited; the other is listed here so it is "
          "never mistaken for the live file.")
        a("")
        for dup, kept in shadowed:
            a("- `%s` is shadowed by `%s`" % (dup, kept))
        a("")

    # 1. orphans -----------------------------------------------------------
    tools, orphans = [], []
    for name, m in sorted(mods.items()):
        if imported_by[name]:
            continue
        (tools if has_main(m["src"]) else orphans).append(name)
    a("## 1. Nothing imports these")
    a("")
    a("A module nothing imports is either a command-line tool, which is fine, or "
      "a capability with no way in, which is the `departure_time_grid.py` case.")
    a("")
    a("### Command-line tools (%d), expected to stand alone" % len(tools))
    a("")
    a(", ".join("`%s`" % t for t in tools) or "none")
    a("")
    a("### Neither imported nor runnable (%d), CHECK EACH ONE" % len(orphans))
    a("")
    if orphans:
        for o in orphans:
            a("- `%s.py`" % o)
    else:
        a("none")
    a("")

    # 2. switches with no hand on them -------------------------------------
    a("## 2. Config keys read somewhere and set nowhere")
    a("")
    a("A module that reads a key no file ever writes, and that is not a function "
      "argument either, is a capability that cannot be turned on. This is the "
      "`qsi_feed` and `dep_time_mins` case.")
    a("")
    rows = []
    for name in sorted(reads):
        for k in sorted(reads[name]):
            if k in all_writes or k in kwargs or k.startswith("_"):
                continue
            rows.append((k, name))
    if rows:
        a("| Key | Read in | Written in |")
        a("|---|---|---|")
        for k, name in rows:
            a("| `%s` | `%s.py` | nothing |" % (k, name))
    else:
        a("None: every config key read is written or passed somewhere.")
    a("")

    a("### Keys written by only one file")
    a("")
    a("Not wrong, but worth a look: a switch only the back-test sets has never "
      "been used in production.")
    a("")
    who = defaultdict(set)
    for name, w in writes.items():
        for k in w:
            who[k].add(name)
    single = [(k, sorted(v)[0]) for k, v in sorted(who.items())
              if len(v) == 1 and any(k in reads[o] for o in reads if o != sorted(v)[0])]
    if single:
        a("| Key | Only written by | Read elsewhere |")
        a("|---|---|---|")
        for k, w in single:
            other = [o for o in reads if k in reads[o] and o != w]
            a("| `%s` | `%s.py` | %s |" % (k, w, ", ".join("`%s`" % o for o in other[:4])))
    else:
        a("none")
    a("")

    # 3. data files --------------------------------------------------------
    a("## 3. Data files named in code that are not in the tree")
    a("")
    a("The 6 August failure: a loader opens a file by path, the file is not "
      "beside it, and the except returns a neutral value.")
    a("")
    # The tree is indexed once. Walking it per candidate file turned this into an
    # O(n squared) scan that never finished on a synced folder.
    present = set()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        present |= {f.lower() for f in fn}
    missing = defaultdict(set)
    for name, m in mods.items():
        for f in data_files(m["src"]):
            base = os.path.basename(f).lower()
            if base not in present:
                missing[os.path.basename(f)].add(name)
    if missing:
        a("| File | Named in |")
        a("|---|---|")
        for f in sorted(missing):
            a("| `%s` | %s |" % (f, ", ".join("`%s.py`" % n for n in sorted(missing[f])[:5])))
        a("")
        a("Some will be outputs the tool writes rather than reads. Check the "
          "direction before acting.")
    else:
        a("None missing.")
    a("")

    # 4. swallowed failures ------------------------------------------------
    a("## 4. Where failure is swallowed")
    a("")
    a("Every one of the four capabilities lost this week failed inside one of "
      "these. A fallback is fine; a silent one is not.")
    a("")
    sw = [(name, swallows(m["tree"])) for name, m in sorted(mods.items())]
    sw = [(n, s) for n, s in sw if s]
    total = sum(len(s) for _n, s in sw)
    a("%d swallowed handlers across %d modules." % (total, len(sw)))
    a("")
    a("| Module | Count | Lines |")
    a("|---|---|---|")
    for n, s in sorted(sw, key=lambda x: -len(x[1]))[:25]:
        a("| `%s.py` | %d | %s |" % (n, len(s), ", ".join(str(l) for l, _w in s[:8])))
    a("")

    # 5. environment -------------------------------------------------------
    envs = defaultdict(set)
    for name, m in mods.items():
        for e in env_vars(m["src"]):
            envs[e].add(name)
    a("## 5. Environment variables the tool reads")
    a("")
    a("Every one of these changes behaviour and none of them is visible in the "
      "tree. They belong in the README before the first commit.")
    a("")
    for e in sorted(envs):
        a("- `%s` in %s" % (e, ", ".join("`%s.py`" % n for n in sorted(envs[e])[:4])))
    a("")
    a("Copyright Avia Solutions Limited. All rights reserved.")

    text = "\n".join(L)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("written: %s  (%d lines)" % (out_path, len(L)))
    else:
        print(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", required=True, help="the folder to audit, e.g. the app directory")
    ap.add_argument("--out", default="", help="write markdown here instead of the console")
    args = ap.parse_args()
    if not os.path.isdir(args.tree):
        sys.exit("not a directory: %s" % args.tree)
    report(os.path.abspath(args.tree), args.out or None)


if __name__ == "__main__":
    main()
