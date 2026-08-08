#!/usr/bin/env python3
r"""
Avia Solutions - inspect / drop one OAG (region, period) snapshot.
==================================================================
Shows a snapshot's source file, row count and eff span. Deletes only with --confirm.
Use to remove a mistagged snapshot the eff-year check flags (e.g. the Europe 2016-05-30
weekly baseline that was sourced from 2015 data).

  py -3.12 oag_drop_period.py --region "Europe" --period 2016-05-30            # inspect only
  py -3.12 oag_drop_period.py --region "Europe" --period 2016-05-30 --confirm  # delete it
Author: Avia Solutions.
"""
import os, sys, argparse
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import duckdb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--period", required=True)
    ap.add_argument("--db", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--confirm", action="store_true", help="actually delete (otherwise inspect only)")
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=not a.confirm)
    info = con.execute("""
        SELECT count(*), min(eff_from), max(eff_to),
               count(DISTINCT source_file), min(source_file)
        FROM oag WHERE region=? AND week=?""", [a.region, a.period]).fetchone()
    n, ef, et, nsrc, src = info
    print(f"{a.region} {a.period}: {n:,} rows, eff {str(ef)[:10]} -> {str(et)[:10]}")
    print(f"   source file(s): {nsrc} distinct, e.g. {src}")
    if n == 0:
        print("   nothing to drop."); con.close(); return
    if not a.confirm:
        print("   (inspect only. add --confirm to delete this snapshot.)"); con.close(); return
    con.execute("DELETE FROM oag WHERE region=? AND week=?", [a.region, a.period])
    left = con.execute("SELECT count(*) FROM oag").fetchone()[0]
    con.close()
    print(f"   DELETED. store now holds {left:,} rows.")


if __name__ == "__main__":
    main()
