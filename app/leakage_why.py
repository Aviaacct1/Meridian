#!/usr/bin/env python3
r"""
Avia Solutions - WHY do NI residents leak to Dublin? Route breadth vs same-route choice. Sabre (+OAG if present).
================================================================================================================
"There is a third leaking to Dublin" is the what. This answers the why. For GB point-of-origin passengers (the NI
traveller) we split the leaked Dublin demand by destination and ask, for each: does Belfast serve this too?

  - Belfast carries ~none of it   -> DUBLIN-ONLY. The leak is route BREADTH: you can't get there from Belfast.
  - Belfast carries a real share  -> OVERLAP.     The leak is CHOICE despite a Belfast option, so we then compare
                                                  fare, airline and frequency on those routes to see what wins it.

Splitting leaked passengers into those two piles is the headline. Then for the overlap pile we show, per route, the
Dublin vs Belfast average fare (if the store carries a fare/revenue field), the airline mix (does Ryanair's Dublin
network pull them?), and a frequency proxy (OAG nonstop departures if an OAG store is found, else O&D volume).

    py -3.12 leakage_why.py            # latest full year
    py -3.12 leakage_why.py --year 2019   # pre-COVID cross-check

Reads read-only. Introspects the schema and adapts, so it runs whatever fare/airline columns your store carries.
"""
import duckdb, argparse, collections, os

SAB = r"C:\Avia\sabre.duckdb"
OAG_CANDIDATES = [r"C:\Avia\oag.duckdb", r"C:\Avia\oag_schedule.duckdb", r"C:\Avia\schedule.duckdb"]
NI = ["BFS", "BHD", "LDY"]
LEAK = "DUB"
MIN_DEST = 300           # ignore trivial destinations (annual GB-poo pax below this, either side)


def pick(cols, *cands):
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c in low:
            return low[c]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=None, help="analysis year (default = latest in store)")
    ap.add_argument("--poo", default="GB")
    a = ap.parse_args()
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")

    cols = [r[1] for r in con.execute("PRAGMA table_info('sabre')").fetchall()]
    print("=== sabre columns ===\n  " + ", ".join(cols))
    fare_c = pick(cols, "avg_fare", "fare", "outturn_fare", "base_fare", "total_fare", "yield", "revenue")
    air_c = pick(cols, "marketing_carrier", "operating_carrier", "marketing_airline", "airline", "carrier",
                 "mkt_al", "op_al", "dominant_carrier")
    yr = a.year or con.execute("SELECT MAX(source_year) FROM sabre").fetchone()[0]
    print(f"\nyear={yr}   fare column={fare_c or 'NONE (fares live in the od_fare store)'}   "
          f"airline column={air_c or 'NONE'}")

    apts = NI + [LEAK]; ph = ",".join("?" * len(apts))
    base = f"source_year = ? AND poo_country = ? AND origin_airport IN ({ph})"
    bp = [yr, a.poo] + apts

    # destination split: Belfast-retained vs Dublin-leaked, GB point of origin
    rows = con.execute(f"""SELECT destination_airport dst,
              SUM(CASE WHEN origin_airport='{LEAK}' THEN passengers ELSE 0 END) leak,
              SUM(CASE WHEN origin_airport<>'{LEAK}' THEN passengers ELSE 0 END) bel
        FROM sabre WHERE {base} GROUP BY destination_airport""", bp).fetchall()
    dest = {d: (lk or 0.0, be or 0.0) for d, lk, be in rows}

    tot_leak = sum(lk for lk, be in dest.values())
    only_leak = sum(lk for lk, be in dest.values() if be < MIN_DEST)          # Dublin-only (breadth)
    over_leak = tot_leak - only_leak                                          # overlap (choice)
    print(f"\n=== WHY: breadth vs choice (GB-poo, {yr}) ===")
    print(f"total Dublin-leaked pax:            {int(tot_leak):>10,}")
    print(f"  on DUBLIN-ONLY routes (breadth):  {int(only_leak):>10,}  ({100*only_leak/(tot_leak or 1):.0f}% of the leak)")
    print(f"  on OVERLAP routes (choice):       {int(over_leak):>10,}  ({100*over_leak/(tot_leak or 1):.0f}% of the leak)")

    print(f"\n--- top DUBLIN-ONLY destinations (Belfast can't take you there) ---")
    only = sorted(((d, lk) for d, (lk, be) in dest.items() if be < MIN_DEST and lk >= MIN_DEST),
                  key=lambda x: -x[1])[:20]
    for d, lk in only:
        print(f"  {d}  {int(lk):>8,}")

    print(f"\n--- top OVERLAP destinations (Belfast serves it, they still drive to Dublin) ---")
    print(f"  {'dst':4}{'leak':>9}{'belfast':>9}{'DUBshr':>8}   fare DUB vs BEL / airline mix")
    over = sorted(((d, lk, be) for d, (lk, be) in dest.items() if be >= MIN_DEST and lk >= MIN_DEST),
                  key=lambda x: -x[1])[:20]
    for d, lk, be in over:
        line = f"  {d:4}{int(lk):>9,}{int(be):>9,}{100*lk/(lk+be):>7.0f}%"
        if fare_c:
            fr = con.execute(f"""SELECT origin_airport='{LEAK}' isdub, SUM({fare_c}*passengers)/NULLIF(SUM(passengers),0)
                FROM sabre WHERE {base} AND destination_airport=? GROUP BY 1""", bp + [d]).fetchall()
            fm = {bool(k): v for k, v in fr}
            if fm.get(True) and fm.get(False):
                line += f"   DUB {fm[True]:.0f} vs BEL {fm[False]:.0f} ({100*(fm[True]-fm[False])/fm[False]:+.0f}%)"
        if air_c:
            al = con.execute(f"""SELECT {air_c}, SUM(passengers) p FROM sabre
                WHERE {base} AND destination_airport=? AND origin_airport='{LEAK}'
                GROUP BY 1 ORDER BY p DESC LIMIT 2""", bp + [d]).fetchall()
            if al:
                line += "   DUB:" + "/".join(f"{c}" for c, _ in al if c)
        print(line)

    # frequency: OAG nonstop departures if a schedule store exists, else the O&D volume above stands in
    oag = next((p for p in OAG_CANDIDATES if os.path.exists(p)), None)
    print(f"\nOAG schedule store: {oag or 'not found (frequency proxied by O&D volume above)'}")
    con.close()


if __name__ == "__main__":
    main()
