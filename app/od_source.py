#!/usr/bin/env python3
"""
Avia Solutions - O&D source selector (DB1B vs Sabre) with a source label.
========================================================================
US-market credibility rule: for US domestic markets the tool leads with DB1B
(the US DOT O&D actual the US audience validates against) and shows it; Sabre
runs underneath for the commuter/EAS tail DB1B cannot see, for cabin/routing/
point-of-origin detail, and for everything non-US.

This is a drop-in wrapper over sabre_catchment.destination_market_split that adds
a per-market source choice and a source label, returning the SAME (split, market,
avg_fare) triple plus a `source` string.

Behaviour is controlled by AVIA_OD_SOURCE:
    sabre (default) : always Sabre - BYTE-IDENTICAL to the pre-change engine.
    dot             : DB1B for all-US markets, Sabre otherwise.
    auto            : DB1B for all-US markets WHERE DB1B has the market (reporting-
                      carrier network); fall back to Sabre for the EAS/commuter/
                      inter-island tail where DB1B is blind, but keep the DOT label
                      (the engine used the accurate number; the label stays DOT).

The DOT label is kept ONLY where DB1B could have seen the market and did not. A base
year outside the store's own span is a different case: there DB1B reads nothing for
any US market, the engine reads Sabre for all of them, and the label must say Sabre.
Keeping the DOT label there would put "US DOT O&D Survey (DB1B)" on a slide produced
entirely from a Sabre run, on every market rather than on a tail.

DB1B is US DOMESTIC ONLY, measured on the store: no rows exist for TPE, LHR, NRT, CDG
or YYZ, so an international market reads Sabre whatever the mode. A route such as
SJC-TPE has no all-US market on any leg, since route_feed measures the behind leg
from each feeder to the route DESTINATION rather than to the origin.

Nothing changes until AVIA_OD_SOURCE is set and db1b.duckdb exists, so the
calibrated baseline is untouched until it is deliberately backtested.
"""
import os

SABRE = "Sabre ODPOO"
DB1B  = "US DOT O&D Survey (DB1B)"


def _mode():
    return os.environ.get("AVIA_OD_SOURCE", "sabre").strip().lower()


def _db1b_path():
    try:
        import config
        return str(config.DB1B_DUCKDB)
    except Exception:
        return os.environ.get("AVIA_DB1B_DUCKDB", r"C:\Avia\db1b.duckdb")


_YEARS = {}


def _db1b_years(db1b_db):
    """(min_year, max_year) present in od_market, or None if it cannot be read.

    The store is built from published DOT extracts and therefore ends a year or more
    behind the Sabre store. A base year outside that span returns no rows for EVERY
    US market, not for a thin one, so it must not be read as DB1B being blind to a
    market: see the label rule in market_split.
    """
    if db1b_db in _YEARS:
        return _YEARS[db1b_db]
    span = None
    try:
        from db_registry import con_ro
        con = con_ro(db1b_db)
        try:
            row = con.execute("SELECT MIN(year), MAX(year) FROM od_market").fetchone()
        finally:
            con.close()
        if row and row[0] is not None:
            span = (int(row[0]), int(row[1]))
    except Exception:
        span = None
    _YEARS[db1b_db] = span
    return span


def _all_us(codes):
    """True if every non-empty IATA code is a US airport (DB1B's domestic scope)."""
    try:
        import airportsdata
        ap = airportsdata.load("IATA")
        codes = [c for c in codes if c]
        return bool(codes) and all((ap.get(c) or {}).get("country") == "US" for c in codes)
    except Exception:
        return False


def market_split(sabre_db, competing_airports, dest_codes, year=None):
    """Drop-in for sabre_catchment.destination_market_split, plus a source label.
    Returns (split, market, avg_fare, source)."""
    import sabre_catchment as SC
    mode = _mode()
    db1b_db = _db1b_path()
    span = _db1b_years(db1b_db) if os.path.exists(db1b_db) else None
    in_span = bool(span) and (year is None or span[0] <= int(year) <= span[1])
    use_dot = (mode in ("dot", "auto")
               and os.path.exists(db1b_db)
               and in_span
               and _all_us([*competing_airports, *dest_codes]))
    if use_dot:
        try:
            split, market, avg_fare = _db1b_split(db1b_db, competing_airports, dest_codes, year)
            if mode == "auto" and market <= 0:
                # DB1B blind here (EAS/commuter/inter-island) - use Sabre's number, keep DOT label
                split, market, avg_fare = SC.destination_market_split(
                    sabre_db, competing_airports, dest_codes, year=year)
            return split, market, avg_fare, DB1B
        except Exception:
            pass  # any DB1B problem -> safe Sabre fallback
    split, market, avg_fare = SC.destination_market_split(
        sabre_db, competing_airports, dest_codes, year=year)
    return split, market, avg_fare, SABRE


def _db1b_split(db1b_db, airports, dest_airports, year):
    """DB1B equivalent of destination_market_split: annual directional O&D from od_market."""
    from db_registry import con_ro
    aph = ",".join("?" * len(airports)); dph = ",".join("?" * len(dest_airports))
    where = [f"origin IN ({aph})", f"dest IN ({dph})"]
    params = [*airports, *dest_airports]
    if year is not None:
        where.append("year = ?"); params.append(year)
    sql = (f"SELECT origin, SUM(pax) AS pax, SUM(pax*avg_fare) AS farewt FROM od_market "
           f"WHERE {' AND '.join(where)} GROUP BY origin")
    con = con_ro(db1b_db)
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    split = {a: 0.0 for a in airports}; fw = 0.0
    for ap, pax, farewt in rows:
        if ap in split:
            split[ap] = float(pax or 0); fw += float(farewt or 0)
    total = sum(split.values())
    return split, total, (fw / total if total else 0.0)
