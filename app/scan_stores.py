#!/usr/bin/env python3
r"""Scan DuckDB stores and report which table carries the Sabre fares.
Prints every table's columns + rowcount, and flags tables that have both an
origin-like column and a fare/revenue-like column (the base MIDT store).

    py -3.12 scan_stores.py
    py -3.12 scan_stores.py E:\Avia\Extract        # extra roots to sweep
"""
import duckdb, glob, os, sys

roots = [r"E:\Avia\Extract", r"E:\Avia"] + sys.argv[1:]
known = [r"E:\preagg.duckdb",
         r"E:\Avia\Extract\proof\md.duckdb",
         r"E:\Avia\Extract\proof\benchmark.duckdb",
         r"E:\Avia\Extract\proof\bench_demo.duckdb"]

paths = set(p for p in known if os.path.exists(p))
for root in roots:
    if os.path.isdir(root):
        paths.update(glob.glob(os.path.join(root, "**", "*.duckdb"), recursive=True))

if not paths:
    sys.exit("No .duckdb files found. Pass the folder as an argument, e.g. py -3.12 scan_stores.py E:\\SomeFolder")

def flt(cols, *needles):
    return [c for c in cols if any(n in c.lower() for n in needles)]

for db in sorted(paths):
    print("\n" + "=" * 78)
    print(db, f"({os.path.getsize(db)/1e9:.2f} GB)")
    try:
        con = duckdb.connect(db, read_only=True)
    except Exception as e:
        print("  cannot open:", e); continue
    try:
        tabs = [r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall()]
    except Exception as e:
        print("  no catalog:", e); con.close(); continue
    for t in tabs:
        try:
            cols = [r[1] for r in con.execute(f"PRAGMA table_info('{t}')").fetchall()]
            n = con.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
        except Exception as e:
            print(f"  {t}: err {e}"); continue
        fare = flt(cols, "fare", "revenue", "yield", "rev")
        orig = flt(cols, "origin", "orig")
        flag = "  <== FARES + O&D" if fare and orig else ("  <== has fares" if fare else "")
        print(f"  {t}: {n:,} rows{flag}")
        print(f"      cols: {', '.join(cols)}")
    con.close()
print("\nDone. The table flagged FARES + O&D is the base store for od_fare (--sabre + --sabre-table).")
