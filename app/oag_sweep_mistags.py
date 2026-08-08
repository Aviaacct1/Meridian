#!/usr/bin/env python3
r"""
Avia Solutions - sweep the whole OAG store for mistagged snapshots.
===================================================================
Scans every (region, period) across all years and flags any where most rows carry
eff_from dates outside the period's label year - the Europe 2016-05-30 case, where a
weekly file was sourced from the wrong year. Report only; fix with oag_drop_period.py.

  py -3.12 oag_sweep_mistags.py
  py -3.12 oag_sweep_mistags.py --threshold 0.5
Author: Avia Solutions.
"""
import os, sys, argparse
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import duckdb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="flag a period if this fraction of rows falls outside its label year")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    rows = con.execute("""
        SELECT year, region, week AS period, count(*) n,
               count(*) FILTER (WHERE TRY_CAST(eff_from AS DATE) IS NOT NULL
                    AND EXTRACT(year FROM TRY_CAST(eff_from AS DATE)) <> year) off_year
        FROM oag GROUP BY 1,2,3 ORDER BY 1,2,3""").fetchall()
    flags = [(yr, rg, p, n, off) for yr, rg, p, n, off in rows if n and off / n > a.threshold]
    print(f"scanned {len(rows)} (region, period) snapshots across the store")
    if not flags:
        print("no mistagged snapshots: every period eff dates sit inside its label year")
    else:
        print(f"{len(flags)} FLAGGED (>{a.threshold:.0%} of rows outside label year):")
        for yr, rg, p, n, off in flags:
            print(f"   {yr}  {rg:16} {str(p):9}  {100*off/n:4.0f}% off-year  ({n:,} rows)")
        print("")
        print('fix each: py -3.12 oag_drop_period.py --region "<R>" --period <P> --confirm')
    con.close()


if __name__ == "__main__":
    main()
