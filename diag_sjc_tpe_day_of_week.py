#!/usr/bin/env python3
"""Avia Solutions - John's 21 August ask: for the one-off SJC-TPE question, look at the
last year of Sabre/OAG and see which days of the week carried the most people, so we
can pick specific operating days for the three forecasts rather than just "5x weekly".
Also a first prototype of a day-allocation step for the Meridian development list.

STAGE 1 IS A SCHEMA CHECK, DELIBERATELY, BEFORE STAGE 2 RUNS ANYTHING. Confirmed on the
first run: Sabre here has no date/day column at all (monthly/annual aggregate, as
app/sabre_carrier_diff.py's source_year-only filtering already implied), so Stage 2 is
correctly skipped every time. OAG has days_of_op / arr_days_of_op - standard OAG "Days of
Operation" fields - which the FIRST version of this script's Stage 3 failed to recognise
(its match list checked for "dow" or the exact names "days"/"day_pattern"/"operating_days",
none of which days_of_op satisfies). Fixed below.

STAGE 3, REWRITTEN. Before trusting any tally, this stage (a) samples real days_of_op
values so the digit/character encoding is confirmed rather than assumed, (b) samples
eff_from/eff_to so the "last 12 months" question is answered against what the table
actually holds rather than assumed, and (c) pulls the route's own top connecting markets
beyond TPE dynamically (same technique as diag_beyond_tpe_region_split.py: the raw,
unfiltered beyond_detail market map, base > 5,000 each-way) rather than a hardcoded city
list, so the scope matches whatever the current engine actually returns. Only after all
three are printed does it run a first-pass day tally - clearly labelled as needing
eyeballing against the sample before it goes anywhere near a client-facing number, per
house method (test everything, never declare settled pre-test).

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


def _connecting_scope(threshold=5000.0):
    """Same technique as diag_beyond_tpe_region_split.py: patch route_forecast.forecast to
    capture the raw, unfiltered beyond_detail market map, then take the cities whose
    each-way base exceeds `threshold`. One airline (CI) is enough since base is meant to be
    market-level, not airline-level - the region-split script is what checks that claim;
    if it prints its disagreement warning, treat this scope list as suspect too."""
    import route_forecast as RFC
    captured = {}
    orig = RFC.forecast

    def _wrap(*a, **kw):
        r = orig(*a, **kw)
        captured["beyond_detail"] = r.get("beyond_detail") or {}
        return r

    RFC.forecast = _wrap
    import cortex_app as CA
    fc = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                                 aircraft="A359", freq=5)
    RFC.forecast = orig
    if not fc.get("ok") or not captured.get("beyond_detail"):
        print("  could not pull a connecting scope from the engine - falling back to no "
              "city restriction (whole-network TPE departures).")
        return []
    scope = [code for code, row in captured["beyond_detail"].items()
             if float((row or {}).get("base") or 0) > threshold]
    print(f"  connecting scope: {len(scope)} cities with each-way base > {threshold:,.0f} "
          f"({', '.join(sorted(scope)[:20])}{' ...' if len(scope) > 20 else ''})")
    return scope


def stage3_oag_connecting_banks():
    """The onward-connection signal: for the beyond-TPE cities this route's forecast
    actually depends on, which day of the week has the most onward seats/departures from
    TPE. This is the schedule-side answer to "best days" and does not depend on Sabre
    having date granularity at all."""
    print("\nSTAGE 3 (OAG): onward departure pattern from TPE, by day of week, to the "
          "route's own connecting markets")
    hits = describe(OAG_DB, "oag")
    dow_col = next((c for c in hits if "days_of_op" in c.lower()
                     or "dow" in c.lower()
                     or c.lower() in ("days", "day_pattern", "operating_days")), None)
    date_col = next((c for c in hits if "date" in c.lower()), None)
    if not (dow_col or date_col):
        print("  no day-of-week or date column found on oag either - the table may "
              "be keyed purely by representative 'week' label (as route_feed.py's "
              "hub_onward_carriers() uses it), with no per-flight day granularity "
              "at all. If so, this question cannot be answered from either store as "
              "currently loaded, and needs a different OAG extract before Stage 3 can "
              "run for real.")
        return
    print(f"  found column to use: {dow_col!r}")

    con = duckdb.connect(OAG_DB, read_only=True)
    try:
        print(f"\n  sample of real {dow_col} values ex-TPE, to confirm the encoding "
              f"before trusting any tally below:")
        rows = con.execute(f"""
            SELECT {dow_col}, count(*) AS n
            FROM oag WHERE dep_airport = 'TPE'
            GROUP BY 1 ORDER BY n DESC LIMIT 20
        """).fetchall()
        for val, n in rows:
            print(f"    {val!r:<12} seen {n:,} times")

        print(f"\n  eff_from / eff_to range ex-TPE, to confirm what period this table "
              f"actually covers ('last 12 months' cannot be assumed without checking):")
        span = con.execute("""
            SELECT min(eff_from), max(eff_to) FROM oag WHERE dep_airport = 'TPE'
        """).fetchone()
        print(f"    eff_from min = {span[0]}, eff_to max = {span[1]}")
    except Exception as e:
        print(f"  sampling failed, column name or grain may differ from assumed: {e}")
        con.close()
        return

    print("\n  pulling connecting scope from the engine (top beyond-TPE cities by base):")
    scope = _connecting_scope()

    print(f"\n  FIRST-PASS TALLY - eyeball against the sample {dow_col} values above "
          f"before trusting this. Assumes the standard OAG convention: {dow_col} is a "
          f"string where digits 1-7 (Mon-Sun) present = operates that day. If the sample "
          f"above does not look like that (e.g. it's 'Y'/'N' flags, or 7 fixed characters "
          f"with '.' for non-operating days), this parse is wrong and needs rewriting "
          f"before use, not trusting.")
    scope_clause = ""
    if scope:
        codes = ",".join(f"'{c}'" for c in scope)
        scope_clause = f"AND arr_airport IN ({codes})"
    try:
        rows = con.execute(f"""
            SELECT {dow_col}, seats, frequency, arr_airport
            FROM oag
            WHERE dep_airport = 'TPE' {scope_clause}
        """).fetchall()
        tally_dep = {str(d): 0 for d in range(1, 8)}
        tally_seats = {str(d): 0.0 for d in range(1, 8)}
        unparsed = 0
        for dow_val, seats, freq, arr in rows:
            s = str(dow_val or "")
            days_hit = [d for d in "1234567" if d in s]
            if not days_hit:
                unparsed += 1
                continue
            for d in days_hit:
                tally_dep[d] += 1
                tally_seats[d] += float(seats or 0)
        names = {"1": "Monday", "2": "Tuesday", "3": "Wednesday", "4": "Thursday",
                 "5": "Friday", "6": "Saturday", "7": "Sunday"}
        print(f"\n  {len(rows):,} OAG rows ex-TPE in scope, {unparsed:,} did not parse "
              f"against the digit convention (should be 0 or near it if the convention "
              f"holds - if this is a large fraction, do not trust the tally):")
        for d in sorted(tally_dep, key=lambda x: -tally_seats[x]):
            print(f"    {names[d]:<10} rows-operating {tally_dep[d]:>5,}   "
                  f"seats(per-departure, summed) {tally_seats[d]:>12,.0f}")
    except Exception as e:
        print(f"  tally query failed: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    print("STAGE 1: what is actually in the stores")
    sabre_hits = describe(SABRE_DB, "sabre")
    stage2_sabre_by_dow(sabre_hits)
    stage3_oag_connecting_banks()
