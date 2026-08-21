#!/usr/bin/env python3
"""Avia Solutions - John's 21 August ask: for the one-off SJC-TPE question, look at the
last year of Sabre/OAG and see which days of the week carried the most people, so we
can pick specific operating days for the three forecasts rather than just "5x weekly".
Also a first prototype of a day-allocation step for the Meridian development list.

STAGE 1 IS A SCHEMA CHECK, DELIBERATELY, BEFORE STAGE 2 RUNS ANYTHING. I have not
seen the Sabre or OAG DuckDB schemas directly in this sandbox, and I do not want to
write a query against a guessed column name and hand back an empty or silently wrong
answer. Sabre Global Demand Data, everywhere else it is used in this codebase (see
app/sabre_carrier_diff.py, filtered only by source_year, no date), reads as MONTHLY
or ANNUAL aggregate O&D volume - if that holds here too, Sabre will not have
day-of-week granularity at all, and "which days carried the most people" has to be
answered from OAG's schedule side instead: which days the connecting banks this
route depends on actually operate, which is the figure that matters for choosing
operating days in any case. Stage 1 prints what is actually in both tables so Stage
2 can be finished correctly rather than guessed.

    py -3.12 diag_sjc_tpe_day_of_week.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")

try:
    import config as CFG
    SABRE_DB = os.environ.get("AVIA_SABRE", str(CFG.SABRE_DUCKDB))
    OAG_DB = os.environ.get("AVIA_OAG", str(CFG.OAG_DUCKDB))
except Exception as e:
    print("could not resolve store paths from config.py:", e)
    SABRE_DB = os.environ.get("AVIA_SABRE", r"C:\Avia\sabre.duckdb")
    OAG_DB = os.environ.get("AVIA_OAG", r"C:\Avia\oag.duckdb")

import duckdb


def describe(db_path, table):
    print(f"\n--- {table} @ {db_path} ---")
    try:
        con = duckdb.connect(db_path, read_only=True)
        cols = con.execute(f"PRAGMA table_info('{table}')").fetchall()
        for c in cols:
            print(f"  {c[1]:<24} {c[2]}")
        date_like = [c[1] for c in cols if any(
            k in c[1].lower() for k in ("date", "dow", "day", "week"))]
        print(f"  date/day/week-like columns: {date_like or 'NONE FOUND'}")
        con.close()
        return date_like
    except Exception as e:
        print(f"  could not open/describe: {e}")
        return []


def stage2_sabre_by_dow(sabre_hits):
    """Only attempted if Stage 1 found a genuine date column on the sabre table."""
    date_col = next((c for c in sabre_hits if "date" in c.lower()), None)
    if not date_col:
        print("\nSTAGE 2 (Sabre): skipped, no date column found - Sabre here is "
              "monthly/annual aggregate, as expected, so day-of-week has to come "
              "from OAG's schedule side (Stage 3), not from Sabre passenger volume.")
        return
    print(f"\nSTAGE 2 (Sabre): found '{date_col}', pulling last 12 months, SJC-TPE, "
          "both directions, by day of week")
    con = duckdb.connect(SABRE_DB, read_only=True)
    try:
        rows = con.execute(f"""
            SELECT dayname({date_col}) AS dow, sum(passengers) AS pax
            FROM sabre
            WHERE ((origin_airport='SJC' AND destination_airport='TPE')
                OR (origin_airport='TPE' AND destination_airport='SJC'))
              AND {date_col} >= current_date - INTERVAL 365 DAY
            GROUP BY 1 ORDER BY 2 DESC
        """).fetchall()
        for dow, pax in rows:
            print(f"  {dow:<10} {pax:>10,.0f}")
    except Exception as e:
        print(f"  query failed, column name or grain may differ from assumed: {e}")
    finally:
        con.close()


def stage3_oag_connecting_banks():
    """The onward-connection signal: for the beyond-TPE cities this route's forecast
    actually depends on (the same top markets as the packs: Manila, Ho Chi Minh City,
    Bangkok, Shanghai, Hong Kong, Seoul, Beijing, Guangzhou...), which day of the week
    has the most onward seats/departures from TPE over the last 12 months. This is
    the schedule-side answer to "best days" - which days genuinely bank well - and
    does not depend on Sabre having date granularity at all."""
    print("\nSTAGE 3 (OAG): onward departure seats from TPE by day of week, last 12 "
          "months, to the route's own top connecting markets")
    hits = describe(OAG_DB, "oag")
    dow_col = next((c for c in hits if "dow" in c.lower() or c.lower() in
                    ("days", "day_pattern", "operating_days")), None)
    date_col = next((c for c in hits if "date" in c.lower()), None)
    if not (dow_col or date_col):
        print("  no day-of-week or date column found on oag either - the table may "
              "be keyed purely by representative 'week' label (as route_feed.py's "
              "hub_onward_carriers() uses it), with no per-flight day granularity "
              "at all. If so, this question cannot be answered from either store as "
              "currently loaded, and needs a different OAG extract (a schedules pull "
              "with day-of-week operating patterns, not the current week-snapshot "
              "load) before Stage 3 can run for real.")
        return
    print(f"  found column(s) to use: dow={dow_col} date={date_col} - "
          "query not run automatically; confirm the grain with John before trusting "
          "the output, then extend this stage.")


if __name__ == "__main__":
    print("STAGE 1: what is actually in the stores")
    sabre_hits = describe(SABRE_DB, "sabre")
    stage2_sabre_by_dow(sabre_hits)
    stage3_oag_connecting_banks()
