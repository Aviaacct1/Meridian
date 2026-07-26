#!/usr/bin/env python3
r"""
Avia Solutions - has the NI -> Dublin leakage catchment shifted over time? Sabre 2013-2025.
============================================================================================
Dublin's traffic is mostly Republic-of-Ireland residents, so a raw airport split is meaningless. To measure NI
residents' airport CHOICE - Belfast (City/Intl/Derry) versus driving south to Dublin - we filter to GB point-of-
origin passengers across the four airports. A Northern Irish resident flying from Dublin still carries a GB point
of origin, so GB-poo at DUB is essentially the leaked NI traveller. Then we watch the Dublin share of that GB
population year by year: rising = leakage growing (APD gap biting harder), flat = structural.

    py -3.12 catchment_trend_ni.py                # all destinations
    py -3.12 catchment_trend_ni.py --dest AGP     # a specific leisure route (leakage runs highest on these)

Reads the store read-only; prints a poo sanity check + the leakage trend, writes a CSV.
"""
import duckdb, csv, argparse, collections

SAB = r"C:\Avia\sabre.duckdb"
NI = ["BFS", "BHD", "LDY"]          # Belfast Intl, Belfast City, Derry
LEAK = "DUB"                        # the leakage sink


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dest", default=None)
    ap.add_argument("--poo", default="GB", help="point-of-origin country code for NI/UK residents")
    a = ap.parse_args()
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")

    # sanity check: confirm GB point-of-origin really is the NI traveller at Dublin (show the poo mix at DUB)
    print("=== Point-of-origin mix of DUB departures (validate the GB = Northern Ireland proxy) ===")
    for col in ("poo_country", "poo_region_name"):
        try:
            r = con.execute(f"SELECT {col}, SUM(passengers) p FROM sabre WHERE origin_airport='DUB' "
                            f"GROUP BY {col} ORDER BY p DESC LIMIT 8").fetchall()
            print(f"  {col}: " + ", ".join(f"{v}={int(p or 0):,}" for v, p in r))
        except Exception as e:
            print(f"  {col}: n/a ({e})")

    apts = NI + [LEAK]
    ph = ",".join("?" * len(apts))
    where = f"origin_airport IN ({ph}) AND poo_country = ?"
    params = apts + [a.poo]
    if a.dest:
        where += " AND destination_airport = ?"; params.append(a.dest.upper())
    rows = con.execute(f"""SELECT source_year yr, origin_airport apt, SUM(passengers) pax
        FROM sabre WHERE {where} GROUP BY source_year, origin_airport ORDER BY yr""", params).fetchall()
    con.close()

    by = collections.defaultdict(dict); tot = collections.defaultdict(float)
    for y, apt, p in rows:
        by[y][apt] = (p or 0.0); tot[y] += (p or 0.0)
    years = sorted(by)
    lbl = f"to {a.dest.upper()}" if a.dest else "all destinations"
    print(f"\n=== NI/UK-resident airport choice ({lbl}), GB point of origin, by year ===")
    print(f"{'year':6}{'GB pax':>10}   " + "  ".join(f"{x:>6}" for x in NI) + "   " + f"{'DUB(leak)':>10}")
    for y in years:
        t = tot[y] or 1
        print(f"{y:6}{int(t):>10,}   " + "  ".join(f"{100*by[y].get(x,0)/t:5.1f}%" for x in NI)
              + f"   {100*by[y].get(LEAK,0)/t:9.1f}%")
    if len(years) >= 2:
        y0, y1 = years[0], years[-1]
        d = 100 * (by[y1].get(LEAK, 0)/(tot[y1] or 1) - by[y0].get(LEAK, 0)/(tot[y0] or 1))
        print(f"\nDublin leakage {y0}: {100*by[y0].get(LEAK,0)/(tot[y0] or 1):.1f}%  ->  {y1}: "
              f"{100*by[y1].get(LEAK,0)/(tot[y1] or 1):.1f}%   ({d:+.1f} share points)")
    fn = f"ni_leakage_trend_{(a.dest or 'all').lower()}.csv"
    with open(fn, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "gb_pax"] + NI + [LEAK + "_leak"])
        for y in years:
            t = tot[y] or 1
            w.writerow([y, int(t)] + [round(by[y].get(x, 0)/t, 4) for x in NI + [LEAK]])
    print(f"wrote {fn}")


if __name__ == "__main__":
    main()
