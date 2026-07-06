#!/usr/bin/env python3
r"""
Avia Solutions - Sabre pre-aggregation builder (REVIEW_QSI_for_Opus_05Jul2026, fix R1).
=========================================================================================
The back-test full-scanned the multi-GB Sabre store 6-10 times PER ROUTE (p2p_traffic and
sector_traffic in backtest.py; connecting_market and behind_market in route_feed.py), times ~6,471
routes. This builder does those scans ONCE, up front, into three small derived tables. After it runs,
every per-route Sabre read becomes an indexed point lookup on a table a thousandth the size.

The three tables reproduce the EXACT filters of the live queries, so preagg-backed reads are identical
to the penny (verify with verify_identity.py --extra "--preagg <out>"):

  od_p2p(year, o, d, pax)      SUM(passengers) GROUP BY (source_year, origin, dest)
                               WHERE connecting_airport1 IS NULL OR TRIM(connecting_airport1)=''
                               -> p2p_traffic(a,b,year) = od_p2p[a,b] + od_p2p[b,a]

  od_single(year, o, d, pax)   SUM(passengers) GROUP BY (source_year, origin, dest)
                               WHERE connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL
                               -> connecting_market: SUM over catchment origins per beyond dest x factor
                               -> behind_market:    SUM over route dests per feeder x factor
                               (matches the live single-stop filter exactly, including the c1='' quirk:
                                '' IS NOT NULL is true, so empty-string c1 rows are single-stop here,
                                exactly as the live query counts them)

  sector_adj(year, u, v, pax)  the leg-exploded adjacency for sector_traffic. u<=v (unordered), and each
                               Sabre row is counted ONCE per distinct unordered pair it contains, because
                               the live sector_traffic is a row-level (adj(a,b) OR adj(b,a)) - a row is
                               counted once if the pair appears as a consecutive leg in EITHER direction,
                               NOT once per leg occurrence. -> sector_traffic(a,b,year) = sector_adj[{a,b}]

The leg set per row matches adj() precisely: the "from" side uses the raw column (so an empty/NULL
connecting airport starts no leg), the "to" side is COALESCE(NULLIF(cN,''), destination) (so a blank
connector collapses to the final destination). rowid identifies the row for the count-once DISTINCT.

Usage:
    py -3.12 build_preagg.py --sabre C:\Avia\sabre.duckdb --out preagg.duckdb
    # then, to confirm zero drift on 100 routes:
    py -3.12 verify_identity.py --oag C:\Avia\oag.duckdb --sabre C:\Avia\sabre.duckdb --extra "--preagg preagg.duckdb"
"""
import argparse, os, sys, time

# {src} is the attached base Sabre table (e.g. src.sabre). It MUST be the base table, not a view:
# DuckDB exposes rowid only on base tables, and the sector explosion needs rowid to count each row once.
SQL_OD_P2P = """
CREATE TABLE od_p2p AS
SELECT source_year AS year, origin_airport AS o, destination_airport AS d,
       SUM(passengers) AS pax
FROM {src}
WHERE connecting_airport1 IS NULL OR TRIM(connecting_airport1) = ''
GROUP BY 1, 2, 3
"""

SQL_OD_SINGLE = """
CREATE TABLE od_single AS
SELECT source_year AS year, origin_airport AS o, destination_airport AS d,
       SUM(passengers) AS pax
FROM {src}
WHERE connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL
GROUP BY 1, 2, 3
"""

# Leg explosion for sector_traffic. NULLIF blanks the connectors first; the "to" side COALESCEs a blank
# connector to the destination, matching adj()'s COALESCE(NULLIF(cN,''),dest). DISTINCT on
# (rid, u, v) counts each source row once per unordered pair it contains (row-level OR semantics).
SQL_SECTOR_ADJ = """
CREATE TABLE sector_adj AS
WITH r AS (
    SELECT source_year AS year, rowid AS rid,
           CAST(passengers AS DOUBLE) AS pax,
           origin_airport AS o, destination_airport AS d,
           NULLIF(connecting_airport1, '') AS c1,
           NULLIF(connecting_airport2, '') AS c2,
           NULLIF(connecting_airport3, '') AS c3
    FROM {src}
),
legs AS (
    SELECT year, rid, pax, o                AS f, COALESCE(c1, d) AS t FROM r
    UNION ALL
    SELECT year, rid, pax, c1               AS f, COALESCE(c2, d) AS t FROM r WHERE c1 IS NOT NULL
    UNION ALL
    SELECT year, rid, pax, c2               AS f, COALESCE(c3, d) AS t FROM r WHERE c2 IS NOT NULL
    UNION ALL
    SELECT year, rid, pax, c3               AS f, d              AS t FROM r WHERE c3 IS NOT NULL
),
pairs AS (
    SELECT DISTINCT year, rid, pax,
           LEAST(f, t) AS u, GREATEST(f, t) AS v
    FROM legs
    WHERE f IS NOT NULL AND t IS NOT NULL
)
SELECT year, u, v, SUM(pax) AS pax
FROM pairs
GROUP BY 1, 2, 3
"""


def main():
    ap = argparse.ArgumentParser(description="Build the Sabre pre-aggregation tables (fix R1).")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "preagg.duckdb"))
    ap.add_argument("--sabre-table", default="sabre", help="source table name in the Sabre store")
    ap.add_argument("--temp-dir", default=None,
                    help="DuckDB scratch/spill directory (default: a local system-temp subfolder). "
                         "Keep it OFF any OneDrive-synced path.")
    ap.add_argument("--mem", default="4GB",
                    help="DuckDB memory_limit (default 4GB). Caps RAM so a big build spills to --temp-dir "
                         "instead of exhausting memory and forcing Windows to page (which freezes the PC).")
    ap.add_argument("--skip-sector", action="store_true",
                    help="build only od_p2p + od_single (the fast, core tables; ~40s). Skips the heavy "
                         "sector_adj leg-explosion; sector_traffic then full-scans (one scan per route).")
    a = ap.parse_args()
    if not os.path.exists(a.sabre):
        print(f"Sabre store not found: {a.sabre}"); return 2
    if os.path.exists(a.out):
        print(f"removing existing {a.out}"); os.remove(a.out)

    import duckdb, tempfile
    con = duckdb.connect(a.out)      # writable target
    # Spill DuckDB's scratch to a LOCAL temp dir. If --out is on a OneDrive-synced folder, the default
    # spill (beside the db file) would be synced as it's written and stall the build for tens of minutes.
    tmp = a.temp_dir or os.path.join(tempfile.gettempdir(), "duckdb_preagg")
    os.makedirs(tmp, exist_ok=True)
    con.execute(f"SET temp_directory='{tmp.replace(chr(92), '/')}'")
    con.execute(f"SET memory_limit='{a.mem}'")    # cap RAM: spill to temp_dir, never page the machine
    con.execute("SET enable_progress_bar=true")   # live % bar for the long sector_adj build
    if a.out.lower().startswith(os.path.expanduser("~").lower()) and "onedrive" in a.out.lower():
        print("WARNING: --out is on a OneDrive folder; the growing db is synced as it's written and "
              "will be slow. Prefer --out C:\\Avia\\preagg.duckdb (local).")
    # ATTACH won't take a bound '?' parameter, so the path is inlined (single quotes doubled). The SQL
    # reads the attached BASE table directly (src."<table>") - not a view - because rowid, which the
    # sector explosion needs to count each row once, is only exposed on base tables.
    esc = a.sabre.replace("'", "''")
    con.execute(f"ATTACH '{esc}' AS src (READ_ONLY)")
    src = f'src."{a.sabre_table}"'

    builds = [("od_p2p", SQL_OD_P2P), ("od_single", SQL_OD_SINGLE)]
    if not a.skip_sector:
        builds.append(("sector_adj", SQL_SECTOR_ADJ))
    for name, sql in builds:
        print(f"  building {name} ...", flush=True)
        t = time.time()
        con.execute(sql.format(src=src))
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:11} {n:>12,} rows   {time.time()-t:>6.0f}s")

    # indexes for the per-route point lookups
    con.execute("CREATE INDEX ix_p2p ON od_p2p(year, o, d)")
    con.execute("CREATE INDEX ix_single_o ON od_single(year, o)")   # connecting_market: fix origins, group dest
    con.execute("CREATE INDEX ix_single_od ON od_single(year, o, d)")
    if not a.skip_sector:
        con.execute("CREATE INDEX ix_sector ON sector_adj(year, u, v)")
    con.execute("DETACH src")
    con.close()
    print(f"\nwrote {a.out}. Point it at a run with backtest.py --preagg {a.out} "
          f"(or verify_identity.py --extra \"--preagg {a.out}\").")
    return 0


if __name__ == "__main__":
    sys.exit(main())
