#!/usr/bin/env python3
"""
Avia Solutions - propensity / demand-sizing model.
==============================================================================
Fix 3 of the general route engine, and the genuinely hard input. Propensity is
air trips per head per year from the origin catchment to the destination metro;
catchment population x propensity = the destination market the catchment generates.

Three tiers, best first (John's steer, 29 June): use real data where it exists,
estimate only where it does not, and label which.

  1. sabre-direct   - the city pair's real O&D from the Sabre store, divided by
                      catchment population. This is the validated path: Sabre is
                      global O&D, so most real city pairs resolve here.
  2. cache          - the same number read from a saved observed-split JSON, for
                      offline / laptop runs (no 15 GB store at run time).
  3. gravity-estimate - where neither exists: a rough estimate anchored to the
                      Genoa-New York benchmark (propensity 0.0424), shaped by a
                      standard distance decay. Flagged 'estimate'; treat the route
                      as unproven until Sabre or observed data calibrates it.

  from propensity import size_demand
  r = size_demand(catchment_pop=19_536_487, dest_codes=["JFK","EWR","LGA"],
                  origin_codes=["GOA","MXP","LIN","BGY","TRN","BLQ"],
                  sabre_db=None, observed_cache="cases/genoa_nyc_observed.json")
  # -> {'propensity': 0.0424, 'basis': 'cache', 'total_od': 828760.7, 'avg_fare': 700.0}
"""
import json
import os

# Genoa-New York anchor for the gravity estimate (the one calibrated benchmark).
ANCHOR_PROPENSITY = 0.0424          # GOA catchment NYC trips per head per year
ANCHOR_DIST_KM = 6450.0             # Genoa - New York great-circle
ANCHOR_DEST_M = 56.0                # New York metro size proxy (pax, millions, both ways)
DIST_DECAY = 1.0                    # gravity distance exponent (standard prior)
DEST_PULL = 0.6                     # destination-size exponent (sub-linear prior)


def _gc_km(a, b, c, d):
    import math
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def _latest_year(sabre_db):
    """The most recent travel year in the Sabre store (so a propensity pull is a SINGLE
    year, never the sum of every year held - the bug that gave a 6x-too-high figure)."""
    try:
        import duckdb
        con = duckdb.connect(sabre_db, read_only=True)
        try:
            return con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
        finally:
            con.close()
    except Exception:
        return None


def propensity_from_sabre(sabre_db, origin_codes, dest_codes, pop,
                          poo_country=None, year=None):
    """Tier 1: real O&D from the Sabre store / catchment population. The store holds many
    travel years; year MUST be pinned to one (defaults to the latest) or the O&D sums across
    every year and inflates the propensity several-fold."""
    import sabre_catchment as S
    if year is None:
        year = _latest_year(sabre_db)
    split, total, avg_fare = S.destination_market_split(
        sabre_db, list(origin_codes), list(dest_codes),
        poo_country=poo_country, year=year)
    prop = (total / pop) if pop else 0.0
    return {"propensity": prop, "basis": "sabre-direct", "total_od": total,
            "avg_fare": avg_fare, "observed_split": split, "year": year}


def propensity_from_cache(cache_path, pop):
    """Tier 2: the saved observed split (offline). Reads {total, avg_fare,
    observed_split}. propensity = total / population."""
    with open(cache_path, encoding="utf-8") as fh:
        c = json.load(fh)
    total = float(c.get("total") or sum(c.get("observed_split", {}).values()))
    prop = (total / pop) if pop else 0.0
    return {"propensity": prop, "basis": "cache", "total_od": total,
            "avg_fare": float(c.get("avg_fare") or 0.0),
            "observed_split": c.get("observed_split", {})}


def gravity_estimate(origin_centre, dest_centre, dest_size_m):
    """Tier 3: a rough estimate anchored on Genoa-New York. With a single
    benchmark we can fix only the level, not the exponents, so the distance decay
    and destination-pull priors come from the airport-choice / gravity literature.
    This is an ESTIMATE; Sabre or observed data should replace it per route."""
    dist = _gc_km(origin_centre[0], origin_centre[1], dest_centre[0], dest_centre[1])
    dist = max(dist, 100.0)
    size = max(dest_size_m, 1.0)
    shape = (size ** DEST_PULL) / (dist ** DIST_DECAY)
    anchor_shape = (ANCHOR_DEST_M ** DEST_PULL) / (ANCHOR_DIST_KM ** DIST_DECAY)
    prop = ANCHOR_PROPENSITY * shape / anchor_shape
    return {"propensity": prop, "basis": "gravity-estimate", "total_od": None,
            "avg_fare": 0.0, "observed_split": {}, "distance_km": round(dist)}


def size_demand(catchment_pop, dest_codes, origin_codes=None, sabre_db=None,
                observed_cache=None, origin_centre=None, dest_centre=None,
                dest_size_m=None, poo_country=None, year=None):
    """Resolve propensity by the best available tier and return a uniform dict:
    {propensity, basis, total_od, avg_fare, observed_split, [distance_km]}.

    Preference: sabre_db (if it exists and origin_codes given) -> observed_cache
    -> gravity estimate (needs origin_centre, dest_centre, dest_size_m). The gravity
    estimate is ALSO computed as a visible cross-check whenever the centres are given,
    even when a data basis wins, so an estimate is never mistaken for a calibrated
    figure (John, 29 June): the data figure is the answer, the gravity number sits
    beside it as 'gravity_crosscheck'."""
    primary = None
    if sabre_db and origin_codes and os.path.exists(sabre_db):
        try:
            primary = propensity_from_sabre(sabre_db, origin_codes, dest_codes,
                                             catchment_pop, poo_country=poo_country, year=year)
        except Exception:                            # fall through to cache / estimate
            primary = None
    if primary is None and observed_cache and os.path.exists(observed_cache):
        primary = propensity_from_cache(observed_cache, catchment_pop)
    grav = None
    if origin_centre and dest_centre and dest_size_m is not None:
        grav = gravity_estimate(origin_centre, dest_centre, dest_size_m)
    if primary is None:
        if grav is None:
            raise ValueError("no propensity source: provide a Sabre store with origin_codes, "
                             "an observed_cache, or origin_centre+dest_centre+dest_size_m")
        return grav
    if grav is not None:                             # data wins; keep gravity as a cross-check
        primary = dict(primary)
        primary["gravity_crosscheck"] = round(grav["propensity"], 5)
    return primary
