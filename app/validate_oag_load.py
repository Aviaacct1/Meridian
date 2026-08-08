#!/usr/bin/env python3
r"""
Avia Solutions - OAG store completeness / fitness check.
========================================================
Run AFTER oag_ingest_periodic.py to confirm a period loaded cleanly and is fit for
the QSI back-test. Reports, for the chosen year(s):
  - the (period, region) grid actually loaded, with flight-row counts
  - a null-rate per mapped column  -> catches a COLMAP header mismatch (a column that
    came in empty means Jess's export used a header spelling COLMAP does not know)
  - seat-total and airport/carrier coverage, against the existing two-week baseline
  - missing-region / missing-month flags

  py -3.12 validate_oag_load.py --year 2015
  py -3.12 validate_oag_load.py --year 2015 --db C:\Avia\oag.duckdb

Author: Avia Solutions.
"""
import os, sys, argparse
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # always run from this script's own folder
import duckdb

REGIONS = ["Europe", "North America", "Latin America", "Africa",
           "Middle East", "Asia", "Southwest Pacific"]
# columns that must be substantially populated for the store to be usable
CORE = ["carrier", "dep_airport", "arr_airport", "seats", "seats_total",
        "dep_country", "arr_country", "aircraft_code", "frequency", "gcd_km"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--db", default=r"C:\Avia\oag.duckdb")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    y = a.year

    print(f"=== OAG store check, year {y} ===\n")
    grid = con.execute(
        "SELECT region, week AS period, count(*) n FROM oag WHERE year=? "
        "GROUP BY 1,2 ORDER BY 1,2", [y]).fetchall()
    if not grid:
        print("NOTHING loaded for this year. Did the ingest run / infer the period?"); return
    for r, p, n in grid:
        print(f"  {r:16} {str(p):8} {n:>10,} flights")
    periods = sorted({p for _, p, _ in grid})
    regions_seen = sorted({r for r, _, _ in grid})
    print(f"\n  periods: {periods}")
    print(f"  regions present: {len(regions_seen)}/7", 
          "" if len(regions_seen) == 7 else f"MISSING: {set(REGIONS)-set(regions_seen)}")

    # monthly completeness (only meaningful where a region is loaded monthly)
    monthly = {}
    for r, p, n in grid:
        ps = str(p)
        if len(ps) == 7 and ps[4] == '-' and ps[5:].isdigit():
            monthly.setdefault(r, set()).add(int(ps[5:]))
    for r, mset in monthly.items():
        miss = sorted(set(range(1, 13)) - mset)
        print(f"  {r}: {len(mset)}/12 months" + (f"  MISSING months {miss}" if miss else "  complete"))

    print("\n=== null-rate per core column (high null => header/COLMAP mismatch) ===")
    tot = con.execute("SELECT count(*) FROM oag WHERE year=?", [y]).fetchone()[0]
    for c in CORE:
        nz = con.execute(
            f"SELECT count(*) FROM oag WHERE year=? AND ({c} IS NULL OR CAST({c} AS VARCHAR)='')",
            [y]).fetchone()[0]
        flag = "  <-- CHECK" if nz > 0.02 * tot else ""
        print(f"  {c:16} {100*nz/tot:6.2f}% null{flag}")

    print("\n=== eff-year vs label-year (catches mistagged/mis-sourced snapshots) ===")
    chk = con.execute("""
        SELECT region, week AS period, year, count(*) n,
               count(*) FILTER (WHERE TRY_CAST(eff_from AS DATE) IS NOT NULL
                    AND EXTRACT(year FROM TRY_CAST(eff_from AS DATE)) <> year) off_year
        FROM oag WHERE year=? GROUP BY 1,2,3 ORDER BY 1,2""", [y]).fetchall()
    flagged = 0
    for region, period, yr, n, off in chk:
        frac = (off / n) if n else 0.0
        if frac > 0.5:
            flagged += 1
            print(f"   FLAG {region:16} {str(period):9}: {100*frac:4.0f}% of rows have eff_from outside {yr}")
    if not flagged:
        print("   all periods: eff dates sit inside their label year")

    print("\n=== coverage vs baseline ===")
    apts = con.execute("SELECT count(DISTINCT dep_airport) FROM oag WHERE year=?", [y]).fetchone()[0]
    carr = con.execute("SELECT count(DISTINCT carrier) FROM oag WHERE year=?", [y]).fetchone()[0]
    seats = con.execute("SELECT sum(TRY_CAST(seats AS BIGINT)) FROM oag WHERE year=?", [y]).fetchone()[0]
    print(f"  distinct dep airports: {apts:,}")
    print(f"  distinct carriers:     {carr:,}")
    print(f"  summed seats (all loaded periods): {seats:,}")
    print("\n(For a full-year monthly load expect roughly 12x the flight rows and seat sum")
    print(" of a single-week snapshot for the same region; a monthly file should hold")
    print(" ~4-5x a one-week pull. Large short-falls flag a truncated download.)")
    con.close()


if __name__ == "__main__":
    main()
