#!/usr/bin/env python3
r"""
Avia Solutions - has the catchment split shifted over time? Sabre 2013-2025.
============================================================================
For a metro's airports, this measures each airport's SHARE of the region's outbound O&D each year - i.e. which
airport the region's residents actually chose - so you can see whether the catchment has drifted (and when) or
stayed flat. Runs overall (all destinations) and, optionally, for one destination so you can see a specific
route's catchment evolve. Reads the store read-only; writes CSVs and prints the share matrix.

    py -3.12 catchment_trend.py                 # Bay Area, all destinations + TPE
    py -3.12 catchment_trend.py --dest LHR      # and a London breakdown

EDIT the CATCHMENT list for a different metro.
"""
import duckdb, csv, argparse, collections

SAB = r"C:\Avia\sabre.duckdb"
CATCHMENT = ["SFO", "OAK", "SJC", "SMF", "STS", "MRY", "SCK", "FAT"]   # Bay Area + spill; edit for another metro


def run(dest=None, label="all destinations"):
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")
    ph = ",".join("?" * len(CATCHMENT))
    where = f"origin_airport IN ({ph})"
    params = list(CATCHMENT)
    if dest:
        where += " AND destination_airport = ?"; params.append(dest.upper())
    rows = con.execute(f"""SELECT source_year AS year, origin_airport AS apt, SUM(passengers) AS pax
        FROM sabre WHERE {where} GROUP BY source_year, origin_airport ORDER BY year, apt""", params).fetchall()
    con.close()
    by_year = collections.defaultdict(dict); totals = collections.defaultdict(float)
    for y, a, p in rows:
        by_year[y][a] = (p or 0.0); totals[y] += (p or 0.0)
    years = sorted(by_year)
    present = [a for a in CATCHMENT if any(by_year[y].get(a) for y in years)]
    print(f"\n=== Catchment share by year ({label}) - Bay Area outbound O&D ===")
    print("year   total_od   " + "  ".join(f"{a:>7}" for a in present))
    for y in years:
        t = totals[y] or 1
        print(f"{y}  {int(t):>9,}   " + "  ".join(f"{100*by_year[y].get(a,0)/t:6.1f}%" for a in present))
    if len(years) >= 2:
        y0, y1 = years[0], years[-1]
        print(f"\nshift {y0}->{y1} (share points):  " +
              "  ".join(f"{a} {100*(by_year[y1].get(a,0)/(totals[y1] or 1) - by_year[y0].get(a,0)/(totals[y0] or 1)):+.1f}" for a in present))
    fn = f"catchment_trend_{(dest or 'all').lower()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "total_od"] + present)
        for y in years:
            t = totals[y] or 1
            w.writerow([y, int(t)] + [round(by_year[y].get(a, 0) / t, 4) for a in present])
    print(f"wrote {fn}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dest", default=None)
    a = ap.parse_args()
    run(None, "all destinations")
    run(a.dest or "TPE", f"to {(a.dest or 'TPE')}")
