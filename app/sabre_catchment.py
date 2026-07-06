#!/usr/bin/env python3
"""
Avia Solutions - observed airport-choice split from the Sabre store (calibration target).
=========================================================================================
The catchment model's airport-size pull and access weighting must be calibrated against
what passengers ACTUALLY did. Sabre ODPOO carries each itinerary's true point of origin
(poo_city / poo_country = where the passenger's journey began, i.e. roughly where they
live) and the origin_airport they actually departed from. So for a catchment region we can
read the real split: of passengers originating in the region, how many used each airport.

    observed = origin_airport_split(db, poo_cities=["GOA","SVN","SPE",...],
                                    airports=["GOA","MXP","LIN","BGY","TRN","BLQ"])
    -> {"GOA": 41250, "MXP": 88010, ...}    # passengers, by departure airport

Feed that straight into catchment.calibrate(locales, airports, observed). Runs against the
sabre.duckdb store (C:\\Avia\\sabre.duckdb); see sabre_ingest.py for the schema.
"""
import os


def origin_airport_split(db, airports, poo_cities=None, poo_country=None, poo_region=None,
                         year=None, directionality=None, min_pax=0):
    """Passengers ORIGINATING in the catchment region, grouped by the airport they departed.

    db          : path to sabre.duckdb
    airports    : the candidate departure airports to score (e.g. GOA + the Milan/Turin set)
    poo_cities  : Sabre point-of-origin CITY codes that define the catchment (the residents)
    poo_country : alternatively, restrict by point-of-origin country (e.g. "IT")
    poo_region  : alternatively, a point-of-origin region name
    Returns {airport_code: passengers} over the candidate airports only.
    Provide at least one of poo_cities / poo_country / poo_region to scope the residents."""
    import duckdb
    if not os.path.exists(db):
        raise FileNotFoundError(f"Sabre store not found: {db}")
    if not (poo_cities or poo_country or poo_region):
        raise ValueError("scope the catchment residents with poo_cities, poo_country or poo_region")

    def _in(col, vals):
        ph = ",".join("?" * len(vals))
        return f"{col} IN ({ph})", list(vals)
    where, params = [], []
    c, v = _in("origin_airport", list(airports)); where.append(c); params += v
    if poo_cities:
        c, v = _in("poo_city", list(poo_cities)); where.append(c); params += v
    if poo_country:
        where.append("poo_country = ?"); params.append(poo_country)
    if poo_region:
        where.append("poo_region_name = ?"); params.append(poo_region)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    if directionality:
        where.append("directionality = ?"); params.append(directionality)

    sql = (f"SELECT origin_airport, SUM(passengers) AS pax FROM sabre "
           f"WHERE {' AND '.join(where)} GROUP BY origin_airport "
           f"HAVING SUM(passengers) >= {float(min_pax)} ORDER BY pax DESC")
    con = duckdb.connect(db, read_only=True)
    try:
        from db_registry import apply_limits; apply_limits(con)   # memory cap + temp dir + threads
    except Exception:
        pass
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    split = {a: 0.0 for a in airports}
    for ap, pax in rows:
        if ap in split:
            split[ap] = float(pax or 0)
    return split


def destination_market_split(db, airports, dest_airports, poo_country=None, year=None,
                             directionality=None, min_pax=0):
    """O&D passengers to a DESTINATION market (e.g. NYC = JFK/EWR/LGA), grouped by the airport
    they departed. Gives the real baseline leakage for a route case: of the catchment's New-York
    demand, how many depart each airport today (the home airport's 0 = the repatriable prize).
    Returns ({airport_code: pax}, total_pax, avg_total_fare_usd). dest_airports e.g. ["JFK","EWR","LGA"]."""
    import duckdb
    if not os.path.exists(db):
        raise FileNotFoundError(f"Sabre store not found: {db}")
    aph = ",".join("?" * len(airports)); dph = ",".join("?" * len(dest_airports))
    where = [f"origin_airport IN ({aph})", f"destination_airport IN ({dph})"]
    params = [*airports, *dest_airports]
    if poo_country:
        where.append("poo_country = ?"); params.append(poo_country)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    if directionality:
        where.append("directionality = ?"); params.append(directionality)
    sql = (f"SELECT origin_airport, SUM(passengers) AS pax, "
           f"SUM(passengers * avg_total_fare_usd) AS farewt FROM sabre "
           f"WHERE {' AND '.join(where)} GROUP BY origin_airport "
           f"HAVING SUM(passengers) >= {float(min_pax)} ORDER BY pax DESC")
    con = duckdb.connect(db, read_only=True)
    try:
        from db_registry import apply_limits; apply_limits(con)   # memory cap + temp dir + threads
    except Exception:
        pass
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    split = {a: 0.0 for a in airports}
    fare_wt = 0.0
    for ap, pax, farewt in rows:
        if ap in split:
            split[ap] = float(pax or 0)
            fare_wt += float(farewt or 0)
    total = sum(split.values())
    avg_fare = (fare_wt / total) if total else 0.0
    return split, total, avg_fare


def catchment_poo_cities(db, airports, near_cities=None, poo_country="IT", year=None,
                         directionality="POO", top=40):
    """Helper to DISCOVER the point-of-origin city codes that feed the candidate airports,
    when you don't know them up front: the busiest poo_city codes (in the country) whose
    passengers use these airports. Eyeball the list, then pass the catchment ones to
    origin_airport_split as poo_cities."""
    import duckdb
    ph = ",".join("?" * len(airports))
    where, params = [f"origin_airport IN ({ph})", "poo_country = ?"], [*airports, poo_country]
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    if directionality:
        where.append("directionality = ?"); params.append(directionality)
    sql = (f"SELECT poo_city, poo_city_name, SUM(passengers) AS pax FROM sabre "
           f"WHERE {' AND '.join(where)} GROUP BY poo_city, poo_city_name "
           f"ORDER BY pax DESC, poo_city LIMIT {int(top)}")   # deterministic tiebreaker on the top-N cut
    con = duckdb.connect(db, read_only=True)
    try:
        from db_registry import apply_limits; apply_limits(con)   # memory cap + temp dir + threads
    except Exception:
        pass
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()
