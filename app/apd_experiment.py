#!/usr/bin/env python3
r"""
Avia Solutions - did APD changes move NI demand, leakage or fares? A natural-experiment read of Sabre 2013-2025.
===============================================================================================================
The duty history gives us dated events to test against the data:

    2009 (Budget)     Republic introduces Air Travel Tax, EUR10 / EUR2 by distance
    01 Mar 2011       flattened to EUR3 (EU internal-market ruling)
    Jan 2013          NI zero-rates DIRECT LONG-HAUL APD (to save Belfast-Newark); short-haul unchanged
    01 Apr 2014       Republic ABOLISHES the Air Travel Tax -> Dublin EUR3 cheaper overnight
    2012 -> 2024      UK APD short-haul held GBP13, then GBP15 from 2024 (this rate still applies at Belfast)

So the standing wedge on a short-haul departure is roughly GBP13 (Belfast) vs nothing (Dublin) post-2014. The one
clean step-change to look for is April 2014: if the abolition mattered, Dublin's share of GB-poo demand should step
up across 2014-2015, and the Belfast-minus-Dublin fare gap should widen. This prints leakage share, both volumes
and (if the store carries fares) the fare gap by year, so you can read the step against the dated events.

    py -3.12 apd_experiment.py

Reads read-only. Sabre store only covers 2013 on, so the 2009/2011 events pre-date the data; 2014 is in-window.
"""
import duckdb, collections, csv

SAB = r"C:\Avia\sabre.duckdb"
NI = ["BFS", "BHD", "LDY"]
LEAK = "DUB"
EVENTS = {2013: "NI long-haul APD -> 0 (Jan)", 2014: "ROI abolishes air travel tax (1 Apr)", 2024: "UK APD 13->15"}


def pick(cols, *cands):
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c in low:
            return low[c]
    return None


def main():
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")
    cols = [r[1] for r in con.execute("PRAGMA table_info('sabre')").fetchall()]
    fare_c = pick(cols, "avg_fare", "fare", "outturn_fare", "base_fare", "total_fare", "yield")
    apts = NI + [LEAK]; ph = ",".join("?" * len(apts))

    sel = f"""SELECT source_year yr, origin_airport='{LEAK}' isdub,
                 SUM(passengers) pax{f", SUM({fare_c}*passengers)/NULLIF(SUM(passengers),0) fare" if fare_c else ""}
        FROM sabre WHERE poo_country='GB' AND origin_airport IN ({ph}) GROUP BY 1,2 ORDER BY 1"""
    rows = con.execute(sel, apts).fetchall(); con.close()

    bel = collections.defaultdict(float); dub = collections.defaultdict(float)
    belf = {}; dubf = {}
    for r in rows:
        yr, isdub = r[0], bool(r[1]); pax = r[2] or 0.0
        (dub if isdub else bel)[yr] = pax
        if fare_c:
            (dubf if isdub else belf)[yr] = r[3]
    years = sorted(set(bel) | set(dub))

    print(f"=== APD natural experiment: GB-poo demand, leakage and fares by year "
          f"({'fares from '+fare_c if fare_c else 'no fare column - volumes/leakage only'}) ===")
    hdr = f"{'yr':6}{'Belfast':>10}{'Dublin':>10}{'DUBshare':>9}{'BEL yoy':>9}{'DUB yoy':>9}"
    if fare_c:
        hdr += f"{'BELfare':>9}{'DUBfare':>9}{'gap':>7}"
    print(hdr)
    pb = pd = None
    out = []
    for y in years:
        b, d = bel.get(y, 0), dub.get(y, 0); sh = 100*d/((b+d) or 1)
        by = f"{100*(b/pb-1):+.0f}%" if pb else "   -"
        dy = f"{100*(d/pd-1):+.0f}%" if pd else "   -"
        line = f"{y:6}{int(b):>10,}{int(d):>10,}{sh:>8.1f}%{by:>9}{dy:>9}"
        row = [y, int(b), int(d), round(sh, 1)]
        if fare_c:
            bf, df = belf.get(y), dubf.get(y)
            gap = (bf - df) if (bf and df) else None
            line += f"{(bf or 0):>9.0f}{(df or 0):>9.0f}{(gap if gap is not None else 0):>+7.0f}"
            row += [round(bf or 0, 1), round(df or 0, 1), round(gap, 1) if gap is not None else ""]
        if y in EVENTS:
            line += f"   <- {EVENTS[y]}"
        print(line); out.append(row)
        pb, pd = b or pb, d or pd

    hd = ["year", "belfast_pax", "dublin_pax", "dublin_share_pct"] + (["bel_fare", "dub_fare", "gap"] if fare_c else [])
    with open("apd_experiment.csv", "w", newline="") as f:
        csv.writer(f).writerows([hd] + out)
    print("\nwrote apd_experiment.csv")
    print("Read: a share step across 2014-2015 = the ROI abolition biting; a widening fare gap in the same window "
          "= Dublin passing the saved duty into lower fares. Flat through 2014 = the wedge was already priced in.")


if __name__ == "__main__":
    main()
