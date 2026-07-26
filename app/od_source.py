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
    use_dot = (mode in ("dot", "auto")
               and os.path.exists(db1b_db)
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
