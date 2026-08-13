#!/usr/bin/env python3
r"""
Avia Solutions - DB1B coupon-split store builder.
=================================================
Why this exists. `od_market` in db1b.duckdb is a single figure per origin, destination
and year, aggregated over every itinerary type. That is the right quantity for the
point to point leg, which reads all itineraries through
sabre_catchment.destination_market_split, and it is the WRONG quantity for the feed
legs, which read connecting itineraries only:

    route_feed.connecting_market  line 203   connecting_airport1 IS NOT NULL
    route_feed.behind_market      line 345   AND connecting_airport2 IS NULL

Dropping DB1B into those legs as `od_market` stands would replace a connecting-only
market with a total market and inflate the feed base by the whole nonstop share.

The raw DB1BMarket extracts carry MktCoupons, which is the itinerary length: 1 is a
nonstop, 2 is a single connection, 3 or more is a multi-stop. bt2/bt2_db1b.py already
reads them that way for the nonstop outturn. This builder keeps the coupon count
rather than collapsing it, so each leg can read the quantity it actually wants:

    coupons = 1        nonstop            matches Sabre connecting_airport1 IS NULL
    coupons = 2        single connection  matches the live feed filter exactly
    coupons >= 3       multi-stop         collapsed to 4, kept rather than dropped
    all coupons        total O&D          reproduces od_market

Passengers are grossed x10, DB1B being a 10 per cent ticket sample. That convention is
the one already in bt2/bt2_db1b.py line 3 and in the existing od_market, whose figures
are all multiples of ten.

NO FILTERS ARE APPLIED in this build: no bulk-fare exclusion, no country test, no fare
sanity range. The build convention behind od_market is not recorded anywhere in the
repo, so the first build reproduces it and is CHECKED against it by
db1b_coupons_check.py. Filters are a decision to take once that comparison says what
od_market did, not a guess to bake in beforehand.

Missing quarters are recorded in build_log with status "missing" and never skipped in
silence.

Usage (workstation):
    py -3.12 build_db1b_coupons.py --years 2023-2024
    py -3.12 build_db1b_coupons.py --years 2024 --quarters 4     # time one quarter first
    py -3.12 build_db1b_coupons.py --years 2000-2024             # overnight

Re-running is safe: a year and quarter already in build_log with status "built" is
skipped unless --rebuild is given.
"""
import argparse
import glob
import os
import sys
import time
from datetime import datetime, timezone

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

EXTRACT_GLOB = "Origin_and_Destination_Survey_DB1BMarket_{year}_{quarter}"
MAX_COUPONS = 4          # 4 means "4 or more": the tail is kept, not dropped


def default_extracts():
    """The DOT extract folder, from config if it resolves, else the bt2 resolver."""
    try:
        import config
        cand = os.path.join(str(config.LOCAL_CACHE), "Usmarket data")
        if os.path.isdir(cand):
            return cand
    except Exception:
        pass
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(APP_DIR), "bt2"))
        from bt2_paths import US_MARKET
        return US_MARKET
    except Exception:
        return None


def default_out():
    try:
        import config
        return str(config.DB1B_COUPONS_DUCKDB)
    except Exception:
        return os.path.join(os.path.expanduser("~"), "db1b_coupons.duckdb")


def parse_years(spec):
    """'2024', '2023-2024' or '2015,2018,2024' -> a sorted list of years."""
    years = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            years.update(range(int(lo), int(hi) + 1))
        else:
            years.add(int(part))
    return sorted(years)


def extract_csv(extracts, year, quarter):
    """The one CSV for a year and quarter, or None. The .zip beside it is ignored."""
    folder = os.path.join(extracts, EXTRACT_GLOB.format(year=year, quarter=quarter))
    if not os.path.isdir(folder):
        return None
    found = sorted(glob.glob(os.path.join(folder, "*.csv")))
    return found[0] if found else None


def open_store(path, memory, threads, temp):
    import duckdb
    con = duckdb.connect(path)
    con.execute(f"SET memory_limit='{memory}'")
    con.execute(f"SET threads={int(threads)}")
    if temp:
        os.makedirs(temp, exist_ok=True)
        con.execute(f"SET temp_directory='{temp}'")
    con.execute("""
        CREATE TABLE IF NOT EXISTS od_market_coupons (
            origin VARCHAR, dest VARCHAR, year BIGINT, quarter BIGINT,
            coupons BIGINT, pax DOUBLE, avg_fare DOUBLE)
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS build_log (
            year BIGINT, quarter BIGINT, status VARCHAR, source_file VARCHAR,
            rows_out BIGINT, pax_grossed DOUBLE, seconds DOUBLE, built_at VARCHAR)
    """)
    return con


def already_built(con, year, quarter):
    row = con.execute("SELECT count(*) FROM build_log WHERE year=? AND quarter=? AND status='built'",
                      [year, quarter]).fetchone()
    return bool(row and row[0])


def log(con, year, quarter, status, source_file, rows_out, pax, seconds):
    con.execute("DELETE FROM build_log WHERE year=? AND quarter=? AND status=?",
                [year, quarter, status])
    con.execute("INSERT INTO build_log VALUES (?,?,?,?,?,?,?,?)",
                [year, quarter, status, source_file, rows_out, pax, seconds,
                 datetime.now(timezone.utc).isoformat(timespec="seconds")])


def build_quarter(con, csv_path, year, quarter):
    """Aggregate one quarter's extract into od_market_coupons. Directional, as od_market is."""
    started = time.time()
    con.execute("DELETE FROM od_market_coupons WHERE year=? AND quarter=?", [year, quarter])
    con.execute(f"""
        INSERT INTO od_market_coupons
        WITH r AS (
            SELECT Origin AS origin, Dest AS dest,
                   try_cast(Year AS BIGINT) AS year,
                   try_cast(Quarter AS BIGINT) AS quarter,
                   least(try_cast(MktCoupons AS BIGINT), {MAX_COUPONS}) AS coupons,
                   try_cast(Passengers AS DOUBLE) AS pax_sample,
                   try_cast(MktFare AS DOUBLE) AS fare
            FROM read_csv(?, header=true)
        )
        SELECT origin, dest, year, quarter, coupons,
               SUM(pax_sample) * 10 AS pax,
               CASE WHEN SUM(pax_sample) > 0
                    THEN SUM(pax_sample * fare) / SUM(pax_sample) ELSE 0 END AS avg_fare
        FROM r
        WHERE origin IS NOT NULL AND dest IS NOT NULL AND coupons IS NOT NULL
              AND pax_sample IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5
    """, [csv_path])
    rows, pax = con.execute(
        "SELECT count(*), SUM(pax) FROM od_market_coupons WHERE year=? AND quarter=?",
        [year, quarter]).fetchone()
    return int(rows or 0), float(pax or 0.0), time.time() - started


def main():
    ap = argparse.ArgumentParser(description="Build the DB1B coupon-split store.")
    ap.add_argument("--extracts", default=default_extracts(),
                    help="folder holding the Origin_and_Destination_Survey_DB1BMarket_* extracts")
    ap.add_argument("--out", default=default_out(), help="output DuckDB store")
    ap.add_argument("--years", default="2023-2024", help="e.g. 2024, 2023-2024, 2015,2024")
    ap.add_argument("--quarters", default="1,2,3,4")
    ap.add_argument("--memory", default="4GB", help="DuckDB memory_limit")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--temp", default=None, help="DuckDB temp_directory")
    ap.add_argument("--rebuild", action="store_true", help="rebuild quarters already logged as built")
    args = ap.parse_args()

    if not args.extracts or not os.path.isdir(args.extracts):
        print(f"ERROR: extract folder not found: {args.extracts}")
        return 2

    years = parse_years(args.years)
    quarters = [int(q) for q in str(args.quarters).split(",") if q.strip()]
    con = open_store(args.out, args.memory, args.threads, args.temp)
    print(f"Store:    {args.out}")
    print(f"Extracts: {args.extracts}")
    print(f"Years:    {years[0]}-{years[-1]} ({len(years)}), quarters {quarters}\n")

    built = missing = skipped = empty = 0
    try:
        for year in years:
            for quarter in quarters:
                tag = f"{year} Q{quarter}"
                if already_built(con, year, quarter) and not args.rebuild:
                    print(f"  {tag}: already built, skipped")
                    skipped += 1
                    continue
                csv_path = extract_csv(args.extracts, year, quarter)
                if not csv_path:
                    print(f"  {tag}: NO EXTRACT (flagged, not filled)")
                    log(con, year, quarter, "missing", "", 0, 0.0, 0.0)
                    missing += 1
                    continue
                rows, pax, secs = build_quarter(con, csv_path, year, quarter)
                if rows == 0:
                    # An extract that parsed to nothing is a format change, not an empty quarter.
                    # The older vintages carry different column names, so this is the shape a
                    # 2000s extract fails in. Logged as its own status so a run cannot be read
                    # as complete when part of it read nothing.
                    log(con, year, quarter, "empty", csv_path, 0, 0.0, secs)
                    print(f"  {tag}: EXTRACT PARSED TO NOTHING (flagged; check the column names)")
                    empty += 1
                    continue
                log(con, year, quarter, "built", csv_path, rows, pax, secs)
                print(f"  {tag}: {rows:,} rows, {pax:,.0f} passengers grossed, {secs:,.0f}s")
                built += 1
    finally:
        con.close()

    print(f"\n{built} quarters built, {skipped} skipped, {missing} missing, {empty} empty.")
    if missing or empty:
        print("Missing and empty quarters are in build_log with their status. A year short a "
              "quarter must not be read as a full year.")
    print("Next: py -3.12 db1b_coupons_check.py --coupons "
          f"{args.out} --year {years[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
