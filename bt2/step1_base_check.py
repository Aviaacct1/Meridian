#!/usr/bin/env python3
"""Avia Solutions - STEP 1 of the QSI connecting build, 11 August 2026.

The question: is the `pax` base in route_feed.beyond_capture and behind_capture the TOTAL O&D demand
on each market, or the CONNECTING slice of it? The handover's leading hypothesis is that it is total,
and that k=0.06 exists to re-level a base that is too wide.

This does not infer the answer from the totals. It runs the store query the engine actually runs, on
the SJC-TPE scope the engine actually builds, in three forms:

  A  connecting only  : the filter route_feed uses today, single-connection itineraries, nonstop out
  B  all itineraries  : total O&D demand, nonstop plus every connection depth
  C  nonstop only     : the difference, printed so B = A + C + multi-stop is visible rather than assumed

If A and B are the same number, the base is total demand and the hypothesis holds. If A is materially
smaller than B, the base is already the connecting slice and the hypothesis is refuted.

The beyond base is expected to reproduce 1,216,168 and the behind base 313,530, the two figures
measured on 11 August. Reproducing them is what makes this a measurement rather than a reading.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import duckdb                                   # noqa: E402
import route_engine as RE                       # noqa: E402
import route_feed as RFEED                      # noqa: E402
import oag_served as OAS                        # noqa: E402

OAG = os.environ["AVIA_OAG"]
SABRE = os.environ["AVIA_SABRE"]
ORIGIN = "SJC"
DEST = "TPE"
RADIUS_KM = 220.0                                # cortex_app.calibrated_forecast default
FACTOR_INDIRECT = 1.044                          # the indirect split weighting the engine applies


def _sabre():
    con = duckdb.connect(SABRE, read_only=True)
    con.execute("SET memory_limit='2GB'; SET temp_directory='/tmp/duck'; SET threads=2;")
    return con


def market_sum(origins, dests, year, mode):
    """Sum of Sabre passengers between two airport lists in one year, under one itinerary filter.

    mode 'connecting' is the filter route_feed.connecting_market applies today: exactly one connection.
    mode 'all' is every itinerary, which is total O&D demand. mode 'nonstop' is the nonstop slice.
    """
    where = {"connecting": "AND connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL",
             "all": "",
             "nonstop": "AND connecting_airport1 IS NULL"}[mode]
    oa = ",".join("?" * len(origins))
    da = ",".join("?" * len(dests))
    sql = (f"SELECT SUM(passengers * {FACTOR_INDIRECT}) FROM sabre WHERE source_year=? "
           f"AND origin_airport IN ({oa}) AND destination_airport IN ({da}) {where}")
    con = _sabre()
    try:
        return float(con.execute(sql, [year] + list(origins) + list(dests)).fetchone()[0] or 0.0)
    finally:
        con.close()


def main():
    con = duckdb.connect(OAG, read_only=True)
    week = con.execute("SELECT max(week) FROM oag").fetchone()[0]
    con.close()
    con = _sabre()
    year = con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
    con.close()

    ap = RE._airports()
    served = None
    si = None
    for f in sorted(os.listdir(os.environ.get("AVIA_LOCAL_CACHE", "."))):
        if f.startswith("served") and f.endswith(".json"):
            si = os.path.join(os.environ["AVIA_LOCAL_CACHE"], f)
    if si:
        try:
            served = set(OAS.served_set(OAS.load_index(si)))
        except Exception:
            served = None
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], RADIUS_KM, served, True)]

    print(f"OAG week {week}, Sabre year {year}")
    print(f"origin catchment for {ORIGIN} at {RADIUS_KM:.0f}km: {competing}")

    # BEYOND. The engine's scope: everything TPE serves that week, less the catchment itself, less the
    # destinations where TPE is a backtrack rather than on the way.
    scope = [x for x in RFEED.hub_served(OAG, week, DEST) if x not in competing]
    scope = RFEED.on_the_way(competing, DEST, scope, circuity=1.35)
    print(f"beyond scope: {len(scope)} destinations")
    for mode in ("connecting", "all", "nonstop"):
        print(f"  beyond base, {mode:11}: {market_sum(competing, scope, year, mode):>14,.0f}")

    # BEHIND. The engine uses the specific route origin, not the wider catchment, and the market is
    # feeder -> route destination.
    feeders = [y for y in RFEED.feeders_to(OAG, week, [ORIGIN])
               if y not in [ORIGIN] and y not in [DEST]]
    ocen, dcen = RFEED._centroid([ORIGIN]), RFEED._centroid([DEST])
    od = RFEED._gc(ocen, dcen) or 0
    kept = []
    for y in feeders:
        yc = RFEED._coords(y)
        if not yc:
            continue
        yd = RFEED._gc(yc, dcen)
        if yd and yd > 100 and ((RFEED._gc(yc, ocen) or 0) + od) <= 1.35 * yd:
            kept.append(y)
    print(f"behind scope: {len(kept)} feeders")
    for mode in ("connecting", "all", "nonstop"):
        print(f"  behind base, {mode:11}: {market_sum(kept, [DEST], year, mode):>14,.0f}")


if __name__ == "__main__":
    main()
