#!/usr/bin/env python3
r"""
Avia Solutions - add fares to the pre-aggregation (od_fare + od_fare_pos).
=========================================================================
Companion to build_preagg.py. That builder keeps volumes only (year/o/d/pax).
This one reads the SAME base Sabre store the tool uses (C:\Avia\sabre.duckdb,
table `sabre`) and emits fare-carrying twins so the synced working store
(preagg.duckdb) supports price work without shipping the multi-GB base store:

  od_fare(year, o, d, pax, avg_base_fare_usd, avg_total_fare_usd)   # p2p, matches od_p2p filter
  od_fare_pos(year, o, d, poo_country, pax)                          # point-of-sale split (residence cross-check)

Base columns (per the store): origin_airport, destination_airport,
connecting_airport1..3, passengers, avg_base_fare_usd, avg_total_fare_usd,
poo_country, source_year. Fares are passenger-weighted across each O&D group.

Usage:
    py -3.12 build_od_fare.py
    py -3.12 build_od_fare.py --airports BFS,BHD,LDY,DUB,LHR,LGW,STN,LTN,MAN,EDI,GLA,LPL,BHX,NCL,BRS
    py -3.12 build_od_fare.py --all-airports        # whole world (slower, bigger)
"""
import argparse, os, sys, tempfile

def pick(cols, *needles, required=True, label=""):
    low = {c.lower(): c for c in cols}
    for n in needles:
        if n.lower() in low:
            return low[n.lower()]
    for n in needles:
        for lc, orig in low.items():
            if n.lower() in lc:
                return orig
    if required:
        sys.exit(f"Column for {label or needles[0]} not found. Columns:\n  {', '.join(cols)}")
    return None

NI_DUB_GB = "BFS,BHD,LDY,DUB,LHR,LGW,STN,LTN,MAN,EDI,GLA,LPL,BHX,NCL,BRS"

def main():
    ap = argparse.ArgumentParser(description="Build od_fare / od_fare_pos from the Sabre store.")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--sabre-table", default="sabre")
    ap.add_argument("--out", default=None, help="target duckdb (default: preagg.duckdb beside this script)")
    ap.add_argument("--airports", default=NI_DUB_GB, help="keep rows where origin OR dest is in this list")
    ap.add_argument("--all-airports", action="store_true", help="build for every airport (ignores --airports)")
    ap.add_argument("--mem", default="4GB")
    ap.add_argument("--temp-dir", default=None, help="DuckDB spill dir; keep OFF any OneDrive path")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out = a.out or os.path.join(here, "preagg.duckdb")
    if not os.path.exists(a.sabre):
        sys.exit(f"Sabre store not found: {a.sabre}")

    import duckdb
    tmp = a.temp_dir or os.path.join(tempfile.gettempdir(), "avia_fare_spill")
    os.makedirs(tmp, exist_ok=True)

    con = duckdb.connect(out)
    con.execute(f"PRAGMA memory_limit='{a.mem}'")
    con.execute(f"PRAGMA temp_directory='{tmp}'")
    con.execute(f"ATTACH '{a.sabre}' AS src (READ_ONLY)")

    cols = [r[1] for r in con.execute(f"PRAGMA table_info('src.{a.sabre_table}')").fetchall()]
    yr    = pick(cols, "source_year", "year", label="year")
    o     = pick(cols, "origin_airport", "origin", label="origin")
    d     = pick(cols, "destination_airport", "destination", "dest", label="destination")
    c1    = pick(cols, "connecting_airport1", "connecting1", label="connecting_airport1")
    pax   = pick(cols, "passengers", "pax", label="passengers")
    base  = pick(cols, "avg_base_fare_usd", "base_fare", required=False, label="base fare")
    total = pick(cols, "avg_total_fare_usd", "total_fare", "avgfare", "fare", required=False, label="total fare")
    poo   = pick(cols, "poo_country", "pos_country", required=False, label="point of sale country")
    if not (base or total):
        sys.exit(f"No fare column found. Columns:\n  {', '.join(cols)}")

    p2p = f"({c1} IS NULL OR TRIM({c1})='')"
    where = p2p
    if not a.all_airports:
        al = ",".join("'" + x.strip().upper() + "'" for x in a.airports.split(",") if x.strip())
        where += f" AND ({o} IN ({al}) OR {d} IN ({al}))"

    def wmean(col):
        return f"SUM(CAST({pax} AS DOUBLE)*CAST({col} AS DOUBLE))/NULLIF(SUM(CAST({pax} AS DOUBLE)),0)"
    sel = [f"{yr} AS year", f"{o} AS o", f"{d} AS d", f"SUM(CAST({pax} AS DOUBLE)) AS pax"]
    if base:  sel.append(f"{wmean(base)} AS avg_base_fare_usd")
    if total: sel.append(f"{wmean(total)} AS avg_total_fare_usd")

    print(f"source : {a.sabre} (table {a.sabre_table})")
    print(f"target : {out}")
    print(f"columns: year={yr} o={o} d={d} c1={c1} pax={pax} base={base} total={total} poo={poo}")
    print(f"scope  : {'ALL airports' if a.all_airports else a.airports}")

    con.execute("DROP TABLE IF EXISTS od_fare")
    con.execute(f"CREATE TABLE od_fare AS SELECT {', '.join(sel)} FROM src.{a.sabre_table} WHERE {where} GROUP BY 1,2,3")
    n = con.execute("SELECT COUNT(*) FROM od_fare").fetchone()[0]
    print(f"od_fare: {n:,} rows")

    if poo:
        con.execute("DROP TABLE IF EXISTS od_fare_pos")
        con.execute(f"""CREATE TABLE od_fare_pos AS
            SELECT {yr} AS year, {o} AS o, {d} AS d, {poo} AS poo_country,
                   SUM(CAST({pax} AS DOUBLE)) AS pax
            FROM src.{a.sabre_table} WHERE {where} GROUP BY 1,2,3,4""")
        m = con.execute("SELECT COUNT(*) FROM od_fare_pos").fetchone()[0]
        print(f"od_fare_pos: {m:,} rows")

    fare_col = "avg_total_fare_usd" if total else "avg_base_fare_usd"
    print(f"\nBelfast vs Dublin, 2024, overlap leisure routes ({fare_col}):")
    print(f"  {'dest':4} {'NI pax':>9} {'NI fare':>8} | {'DUB pax':>9} {'DUB fare':>9}")
    for dest in ("AGP","ALC","PMI","FAO","TFS","LPA","BCN","MLA","KRK"):
        row=con.execute(f"""
          SELECT
            (SELECT SUM(pax) FROM od_fare WHERE o IN ('BFS','BHD','LDY') AND d='{dest}' AND year=2024),
            (SELECT SUM(pax*{fare_col})/NULLIF(SUM(pax),0) FROM od_fare WHERE o IN ('BFS','BHD','LDY') AND d='{dest}' AND year=2024),
            (SELECT SUM(pax) FROM od_fare WHERE o='DUB' AND d='{dest}' AND year=2024),
            (SELECT SUM(pax*{fare_col})/NULLIF(SUM(pax),0) FROM od_fare WHERE o='DUB' AND d='{dest}' AND year=2024)
        """).fetchone()
        nip,nif,dp,df=(x or 0 for x in row)
        print(f"  {dest:4} {nip:>9,.0f} {nif:>8,.0f} | {dp:>9,.0f} {df:>9,.0f}")
    con.close()
    print("\nDone. od_fare (+ od_fare_pos) now sit alongside od_p2p in preagg.duckdb.")
    print("Once OneDrive syncs preagg.duckdb, I can run method 4 here (fare differential + diversion elasticity).")

if __name__ == "__main__":
    main()
