#!/usr/bin/env python3
r"""
Avia Solutions - full-year operated-capacity provider for the backtest recalibration.
=====================================================================================
Replaces the two-week-snapshot annualisation with a true full-year sum of monthly
operated seats, from the rebuilt oag.duckdb (monthly labels YYYY-MM).

Why this module exists (validated 24 Jul 2026, see the OAG validation notes):
  * The store holds the SAME flights at several granularities per year (annual, 12
    monthly, half-year, 2 weekly snapshots). Summing across them double-counts.
    This provider reads MONTHLY labels only.
  * seats_total = seats x frequency already, verified exactly. So annual capacity is
    SUM(seats_total); multiplying by frequency again (as the shipped _operated and
    oag_served do via SUM(s*f) and x52) double-counts frequency. This provider does
    NOT multiply by frequency and does NOT x52.
  * The pull is directional (each-way). A both-way route total is the sum of the two
    directions.
  * service_type='J' is the scheduled-passenger filter (140.6m of 141.8m rows).

Additive by design: it touches no shipped module. Wire it into backtest.py behind a
--fy-capacity flag (see FY_CAPACITY_WIRING.md); default off keeps shipped behaviour.

  import fy_capacity as FY
  mby = FY.months_by_year(oag)                 # {year: [YYYY-MM, ...]}
  cap = FY.route_capacity_fy(oag, "LHR", "JFK", 2018, mby[2018])
  idx = FY.build_served_index_fy(oag, 2018, mby[2018])
"""
import re

MONTH_RE = "regexp_full_match(week,'[0-9]{4}-[0-9]{2}')"
PAX = "service_type='J'"

# match oag_served conventions so size_m stays on the calibrated attractiveness scale
LOAD_PROXY = 0.80
DIRECTIONS = 2


def _connect(db, read_only=True):
    import duckdb
    con = duckdb.connect(db, read_only=read_only)
    # route through the shared limiter when available (memory cap, named temp dir,
    # threads=1 so a SUM near a freq threshold does not flip run-to-run); fall back
    # to a hard local cap for a small box.
    try:
        from db_registry import apply_limits
        apply_limits(con)
    except Exception:
        try:
            con.execute("SET memory_limit='2GB'"); con.execute("SET threads=2")
        except Exception:
            pass
    return con


def months_by_year(db):
    """{year:int -> [monthly label, ...]} for every year that has monthly data.
    Monthly labels only; weekly snapshots, half-year and annual rollups excluded so
    a downstream sum cannot mix granularities."""
    con = _connect(db)
    try:
        rows = con.execute(
            f"SELECT DISTINCT week FROM oag WHERE {MONTH_RE} ORDER BY week").fetchall()
    finally:
        con.close()
    by = {}
    for (w,) in rows:
        by.setdefault(int(w[:4]), []).append(w)
    return by


def _weeks_in(months):
    """Operating weeks implied by the number of monthly labels present (52/12 each).
    Two fortnightly Asia-Aug-2018 labels (YYYY-08p01/p16) count as one month."""
    base = {m[:7] for m in months}
    return max(1.0, len(base) * (52.0 / 12.0))


def route_capacity_fy(db, dep, arr, year, months, con=None):
    """Full-year operated capacity for a route in `year`, summed over `months`.

    Returns dict:
      annual_cap  both-direction annual operated seats (sum of seats_total, no x52)
      freq        representative weekly dep->arr frequency = peak monthly deps / 4.345
      gcd         mean great-circle km on the route
      service     'annual' if >=11 months flown, else 'seasonal', 'na' if unflown
      months      count of distinct months the route was flown (either direction)
    """
    own = con is None
    con = con or _connect(db)
    try:
        ph = ",".join("?" * len(months))
        # both-direction annual seats + mean gcd + months flown
        r = con.execute(
            f"SELECT COALESCE(SUM(TRY_CAST(seats_total AS DOUBLE)),0), "
            f"       AVG(TRY_CAST(gcd_km AS DOUBLE)), COUNT(DISTINCT substr(week,1,7)) "
            f"FROM oag WHERE week IN ({ph}) AND {PAX} "
            f"  AND ((dep_airport=? AND arr_airport=?) OR (dep_airport=? AND arr_airport=?))",
            months + [dep, arr, arr, dep]).fetchone()
        annual_cap = float(r[0] or 0.0)
        gcd = float(r[1]) if r[1] is not None else 0.0
        nmonths = int(r[2] or 0)
        # peak monthly dep->arr departures -> representative weekly frequency
        pk = con.execute(
            f"SELECT MAX(mf) FROM (SELECT substr(week,1,7) mo, "
            f"  SUM(TRY_CAST(frequency AS DOUBLE)) mf FROM oag "
            f"  WHERE week IN ({ph}) AND {PAX} AND dep_airport=? AND arr_airport=? "
            f"  GROUP BY mo)",
            months + [dep, arr]).fetchone()[0]
        freq = (float(pk) / 4.345) if pk else 0.0
        service = "annual" if nmonths >= 11 else "seasonal" if nmonths > 0 else "na"
        return {"annual_cap": annual_cap, "freq": freq, "gcd": gcd,
                "service": service, "months": nmonths}
    finally:
        if own:
            con.close()


def build_served_index_fy(db, year, months, min_weekly_freq=1.0):
    """Full-year served-airport index for `year` (drop-in for oag_served.build_served_index,
    but a monthly sum instead of one-week x52, and no seats_total x frequency double-count).

    Returns {'year': year, 'months': n, 'airports': {IATA: {dep_freq, dest_count,
    ann_seats, size_m, city, country}}}. dep_freq is a weekly-equivalent (annual deps / 52)
    so the min_weekly_freq guard keeps the same meaning as the shipped index."""
    con = _connect(db)
    try:
        ph = ",".join("?" * len(months))
        rows = con.execute(f"""
            SELECT dep_airport,
                   SUM(TRY_CAST(frequency AS DOUBLE))            AS ann_deps,
                   COUNT(DISTINCT arr_airport)                   AS dest_count,
                   SUM(TRY_CAST(seats_total AS DOUBLE))          AS ann_seats,
                   MIN(dep_city)                                 AS city,
                   MIN(dep_country)                              AS country
            FROM oag
            WHERE week IN ({ph}) AND {PAX}
              AND dep_airport IS NOT NULL AND TRIM(dep_airport) <> ''
            GROUP BY dep_airport
        """, months).fetchall()
    finally:
        con.close()
    wk = _weeks_in(months)
    airports = {}
    for dep, ann_deps, dest_count, ann_seats, city, country in rows:
        code = (dep or "").strip().upper()
        dep_freq = float(ann_deps or 0.0) / 52.0
        if not code or dep_freq < min_weekly_freq:
            continue
        ann_seats = float(ann_seats or 0.0)
        # if only part of the year is present (e.g. 2019 H1), scale to a full-year
        # equivalent so size_m stays comparable across years; flagged via 'months'.
        if wk < 52.0:
            ann_seats *= (52.0 / wk)
        size_m = ann_seats * DIRECTIONS * LOAD_PROXY / 1e6
        airports[code] = {
            "dep_freq": round(dep_freq, 1),
            "dest_count": int(dest_count or 0),
            "ann_seats": round(ann_seats),
            "size_m": round(size_m, 3),
            "city": (city or "").strip().upper(),
            "country": (country or "").strip().upper(),
        }
    return {"year": year, "months": len({m[:7] for m in months}), "airports": airports}
