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


def _coupons_path():
    try:
        import config
        return str(config.DB1B_COUPONS_DUCKDB)
    except Exception:
        return os.environ.get("AVIA_DB1B_COUPONS_DUCKDB", r"C:\Avia\db1b_coupons.duckdb")


_YEAR_OK = {}


def _year_complete(coupons_db, year):
    """True only if all four quarters of `year` are logged as built.

    2016 is short Q1 on the E: store, as bt2_db1b.py already records, and 2001 and 2002
    are short three quarters between them. A three-quarter year read as a four-quarter
    year under-states every market in it by circa a quarter, which is a silent gap-fill
    in the other direction. Refuse the year rather than scale it.
    """
    key = (coupons_db, int(year))
    if key in _YEAR_OK:
        return _YEAR_OK[key]
    ok = False
    try:
        from db_registry import con_ro
        con = con_ro(coupons_db)
        try:
            row = con.execute("SELECT count(*) FROM build_log WHERE year=? AND status='built'",
                              [int(year)]).fetchone()
            bad = con.execute("SELECT count(*) FROM build_log WHERE year=? AND status<>'built'",
                              [int(year)]).fetchone()
        finally:
            con.close()
        ok = bool(row and row[0] == 4 and bad and bad[0] == 0)
    except Exception:
        ok = False
    _YEAR_OK[key] = ok
    return ok


_AP = {}


def _latest_complete(coupons_db):
    """The most recent year whose four quarters are all logged built, or None."""
    try:
        from db_registry import con_ro
        con = con_ro(coupons_db)
        try:
            row = con.execute(
                "SELECT year FROM build_log GROUP BY year "
                "HAVING count(*) FILTER (WHERE status='built') = 4 "
                "AND count(*) FILTER (WHERE status<>'built') = 0 "
                "ORDER BY year DESC LIMIT 1").fetchone()
        finally:
            con.close()
        return int(row[0]) if row else None
    except Exception:
        return None


def _index_mode():
    """Vintage indexing: off unless AVIA_OD_INDEX_VINTAGE is set to 1, true, on or yes."""
    return os.environ.get("AVIA_OD_INDEX_VINTAGE", "0").strip().lower() in ("1", "true", "on", "yes")


# A growth factor outside this range is not a market growing, it is two different
# populations being compared, and the run falls back to Sabre rather than publish it.
INDEX_MIN, INDEX_MAX = 0.5, 2.0


def _us(code):
    """True if `code` is a US airport. The table is loaded once: a feed scope runs to
    hundreds of points and airportsdata.load re-reads its file on every call."""
    if not _AP:
        try:
            import airportsdata
            _AP.update(airportsdata.load("IATA"))
        except Exception:
            return False
    return (_AP.get(code) or {}).get("country") == "US"


def feed_market(sabre_fn, origins, dests, year, factor_indirect=1.044, group="dest"):
    """The CONNECTING market for one feed side, led by DOT where DOT can see it.

    route_feed measures the feed market as single-connection O&D only, so the quantity
    here is DB1B MktCoupons = 2, which is the same itinerary shape as Sabre's
    connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL.

    A feed scope is rarely all one country: a US hub serves US and foreign points in the
    same list. Rather than refuse the whole side because one destination is foreign, the
    scope is PARTITIONED. The all-US pairs are read from DB1B and the rest from Sabre
    through `sabre_fn`, which is the "leads with DB1B, Sabre underneath" rule applied at
    the level it was written for.

        sabre_fn(origins, dests) -> {key: pax}, already carrying factor_indirect
        group="dest"   key by destination  (the beyond side, connecting_market)
        group="origin" key by origin       (the behind side, behind_market)

    factor_indirect is applied to the DOT figures identically to the Sabre ones. It is a
    Sabre-era constant from the 2013 BA method and may well not belong on DOT data, but
    that is a second measurement: swapping the source has to change one thing at a time
    or nothing afterwards is attributable.

    Returns (market, source, dot_share). dot_share is the share of the returned market
    that came from DB1B, so a slide can state what it is actually reading rather than
    claiming the whole side.
    """
    mode = _mode()
    # The grouped side is the one the market is keyed by and is partitioned US / not-US.
    # The fixed side is the other end of every pair and must be all-US for DB1B to hold
    # the market at all.
    grouped = list(dests) if group == "dest" else list(origins)
    fixed = list(origins) if group == "dest" else list(dests)
    coupons_db = _coupons_path()

    if (mode not in ("dot", "auto") or not origins or not dests
            or not os.path.exists(coupons_db)
            or not all(_us(c) for c in fixed if c)):
        return sabre_fn(origins, dests), SABRE, 0.0

    # THE VINTAGE PROBLEM, and it is structural rather than a fault. DOT publishes a year
    # or more behind, so the engine's base year is routinely outside the DOT store: on
    # 15 August 2026 the store ends at 2024 and a live run asks for 2025. Left alone,
    # _year_complete refuses on EVERY live run and DOT only ever answers a back-test,
    # which makes the US proposition undeliverable. Indexing reads DOT's most recent
    # complete year and carries it forward on Sabre's OWN growth for the same markets and
    # the same quantity, so the LEVEL is DOT's and only the year-on-year movement is
    # Sabre's. Off unless AVIA_OD_INDEX_VINTAGE is set, because it is a method choice.
    read_year, index_factor = int(year), 1.0
    if not _year_complete(coupons_db, year):
        latest = _latest_complete(coupons_db) if _index_mode() else None
        if latest is None or latest >= int(year):
            return sabre_fn(origins, dests), SABRE, 0.0
        read_year = latest

    us_side = [c for c in grouped if c and _us(c)]
    other_side = [c for c in grouped if c and not _us(c)]
    if not us_side:
        return sabre_fn(origins, dests), SABRE, 0.0

    try:
        if group == "dest":
            dot = _db1b_feed(coupons_db, origins, us_side, read_year, factor_indirect, "dest")
        else:
            dot = _db1b_feed(coupons_db, us_side, dests, read_year, factor_indirect, "origin")
        if read_year != int(year):
            index_factor = _growth_factor(sabre_fn, origins, dests, us_side, group,
                                          read_year, int(year))
            if index_factor is None:
                return sabre_fn(origins, dests), SABRE, 0.0
            dot = {k: v * index_factor for k, v in dot.items()}
    except Exception:
        return sabre_fn(origins, dests), SABRE, 0.0      # any DB1B problem -> safe Sabre fallback

    market = dict(dot)
    if other_side:
        rest = (sabre_fn(origins, other_side) if group == "dest"
                else sabre_fn(other_side, dests))
        for k, v in (rest or {}).items():
            market[k] = market.get(k, 0.0) + v

    total = sum(market.values())
    dot_pax = sum(dot.values())
    share = (dot_pax / total) if total else 0.0
    source = DB1B if not other_side else f"{DB1B} for the US domestic markets, {SABRE} otherwise"
    if read_year != int(year):
        # The vintage and the indexing go INTO the label. A reader who is told DOT and not
        # told the year would take a 2024 measurement for a 2025 one.
        source = (f"{source} [{read_year} vintage, indexed to {int(year)} "
                  f"on Sabre growth x{index_factor:.3f}]")
    return market, source, share


def _growth_factor(sabre_fn, origins, dests, us_side, group, from_year, to_year):
    """Sabre's own growth on the SAME markets and the SAME quantity, from_year to to_year.

    Aggregate rather than per market: a per-market factor on a thin feeder is mostly noise,
    and the quantity being carried forward is a level for the side as a whole. Returns None
    when either end is empty or the factor falls outside INDEX_MIN to INDEX_MAX, since a
    market does not halve or double in a year and a figure that says it did is two
    populations rather than one.
    """
    if group == "dest":
        a = sabre_fn(origins, us_side, from_year)
        b = sabre_fn(origins, us_side, to_year)
    else:
        a = sabre_fn(us_side, dests, from_year)
        b = sabre_fn(us_side, dests, to_year)
    base, later = sum((a or {}).values()), sum((b or {}).values())
    if base <= 0 or later <= 0:
        return None
    factor = later / base
    return factor if INDEX_MIN <= factor <= INDEX_MAX else None


def _db1b_feed(coupons_db, origins, dests, year, factor_indirect, group):
    """Single-connection DB1B market, grouped by destination or by origin."""
    from db_registry import con_ro
    key = "dest" if group == "dest" else "origin"
    oph = ",".join("?" * len(origins)); dph = ",".join("?" * len(dests))
    sql = (f"SELECT {key} k, SUM(pax) * ? p FROM od_market_coupons "
           f"WHERE year = ? AND coupons = 2 "
           f"AND origin IN ({oph}) AND dest IN ({dph}) GROUP BY 1")
    con = con_ro(coupons_db)
    try:
        rows = con.execute(sql, [float(factor_indirect), int(year), *origins, *dests]).fetchall()
    finally:
        con.close()
    return {r[0]: float(r[1] or 0) for r in rows}


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
