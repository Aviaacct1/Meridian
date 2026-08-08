#!/usr/bin/env python3
r"""
Avia Solutions - OAG store grain / redundancy diagnostic.
=========================================================
The 2015 pull mixes grains (Asia/Europe monthly, Africa/ME half-year, Americas/
Pacific annual) because the big regions had to be sliced finer to download. This
reports, per year:
  - per (region, period): flight rows, distinct services, and the eff_from/eff_to span
  - per region: distinct annual services vs summed rows  -> the overlap/redundancy factor
so you know NOT to sum across periods, and whether monthly files keep full validity
ranges (so a common week/month can be reconstructed uniformly across regions).

  py -3.12 check_oag_grain.py --year 2015
Author: Avia Solutions.
"""
import os, sys, argparse
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import duckdb

SVC = "carrier||'|'||flight_no||'|'||dep_airport||'|'||arr_airport"


def _dump_service(con, year, region, period):
    """Show the busiest (carrier,flight_no,dep,arr) in one region+period and every
    row it has, so the reason for multiple rows per service is visible on screen."""
    top = con.execute("""
        SELECT carrier, flight_no, dep_airport, arr_airport, count(*) n
        FROM oag WHERE year=? AND region=? AND week=?
        GROUP BY 1,2,3,4 ORDER BY n DESC LIMIT 1""", [year, region, period]).fetchone()
    if not top:
        print(f"   ({region} {period}: no rows)"); return
    car, fn, dep, arr, n = top
    print(f"\n{region}  period {period}  busiest service: {car}{fn} {dep}-{arr}  = {n} rows")
    print("   local_dep  days      freq  eff_from    eff_to      acft  seats  svc  dup")
    rows = con.execute("""
        SELECT local_dep_time, days_of_op, frequency, eff_from, eff_to,
               aircraft_code, seats, service_type, dup_marker
        FROM oag WHERE year=? AND region=? AND week=?
          AND carrier=? AND flight_no=? AND dep_airport=? AND arr_airport=?
        ORDER BY eff_from, local_dep_time, days_of_op""",
        [year, region, period, car, fn, dep, arr]).fetchall()
    for (ldt, dow, fq, ef, et, ac, se, st, du) in rows[:40]:
        print(f"   {str(ldt):9} {str(dow):9} {str(fq):>4}  {str(ef)[:10]}  {str(et)[:10]}  "
              f"{str(ac):4} {str(se):>5}  {str(st):3}  {str(du)}")
    if len(rows) > 40:
        print(f"   ... ({len(rows)-40} more rows)")


def sample_probe(con, year):
    grid = con.execute("SELECT region, week FROM oag WHERE year=? GROUP BY 1,2", [year]).fetchall()
    def is_month(p): return len(str(p)) == 7 and str(p)[4] == '-' and str(p)[5:7].isdigit()
    months = [(r, p) for r, p in grid if is_month(p)]
    annual = [(r, p) for r, p in grid if str(p) == str(year)]
    print("=== sample: what makes a service have multiple rows ===")
    if months:
        # densest monthly (region, period) by rows per service
        best = max(months, key=lambda rp: con.execute(
            "SELECT count(*)*1.0/count(DISTINCT carrier||flight_no||dep_airport||arr_airport) "
            "FROM oag WHERE year=? AND region=? AND week=?", [year, rp[0], rp[1]]).fetchone()[0])
        _dump_service(con, year, best[0], best[1])
    else:
        print("   (no monthly-grain period this year)")
    if annual:
        _dump_service(con, year, annual[0][0], annual[0][1])
    else:
        print("\n   (no annual-grain period this year to contrast)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--db", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sample", action="store_true",
                    help="dump the busiest service from a monthly file vs an annual file")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    y = a.year

    print(f"=== grain / validity span, year {y} ===")
    rows = con.execute(f"""
        SELECT region, week AS period, count(*) nrows,
               count(DISTINCT {SVC}) svc, min(eff_from) ef, max(eff_to) et
        FROM oag WHERE year=? GROUP BY 1,2 ORDER BY 1,2""", [y]).fetchall()
    cur = None
    for r, p, n, svc, ef, et in rows:
        if r != cur:
            print(f"\n{r}:"); cur = r
        print(f"   {str(p):9} rows {n:>10,}  services {svc:>10,}  eff {str(ef)[:10]} -> {str(et)[:10]}")

    print("\n=== per-region: summed rows vs distinct annual services (overlap factor) ===")
    for (r,) in con.execute("SELECT DISTINCT region FROM oag WHERE year=? ORDER BY 1", [y]).fetchall():
        tot = con.execute("SELECT count(*) FROM oag WHERE year=? AND region=?", [y, r]).fetchone()[0]
        svc = con.execute(f"SELECT count(DISTINCT {SVC}) FROM oag WHERE year=? AND region=?", [y, r]).fetchone()[0]
        print(f"   {r:16} rows {tot:>11,}  distinct services {svc:>10,}  overlap {tot/svc:4.1f}x")

    print("\n=== dup_marker: codeshare/duplicate exposure (seats to exclude when counting capacity) ===")
    tot_seats = con.execute("SELECT sum(TRY_CAST(seats AS BIGINT)) FROM oag WHERE year=?", [y]).fetchone()[0] or 0
    dups = con.execute("""
        SELECT region,
               sum(TRY_CAST(seats AS BIGINT)) FILTER (WHERE dup_marker NOT IN ('','0')) dup_seats,
               sum(TRY_CAST(seats AS BIGINT)) all_seats
        FROM oag WHERE year=? GROUP BY 1 ORDER BY 1""", [y]).fetchall()
    for r, ds, alls in dups:
        ds = ds or 0; alls = alls or 1
        print(f"   {r:16} duplicate-flagged seats {100*ds/alls:5.1f}% of region")
    markers = con.execute("SELECT dup_marker, count(*) FROM oag WHERE year=? GROUP BY 1 ORDER BY 2 DESC", [y]).fetchall()
    print("   dup_marker values present:", {str(m): n for m, n in markers})

    if a.sample:
        print()
        sample_probe(con, y)
    print("\nReading: overlap ~1x means one row per service (annual-style file); a high")
    print("overlap means the same services are re-listed each sub-period, so DO NOT sum")
    print("across periods. If eff spans run the full year in the monthly files, a common")
    print("week/month can be filtered uniformly from any region regardless of its grain.")
    con.close()


if __name__ == "__main__":
    main()
