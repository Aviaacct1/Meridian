#!/usr/bin/env python3
r"""
Avia Solutions - what the behind market excludes, filter by filter.
===================================================================
JOB 3. On SJC-TPE the 2025 analyst's behind market is 1,128,500 and ours is circa
188,000, a factor of 6.3, while our behind capture rate is circa 2.5% against his 1.6%,
a factor of 0.6 the other way. The market definition is the larger term by an order of
magnitude, so it is the one to resolve first.

There are three named filters between a whole market and ours, all in route_feed:

  SINGLE-CONNECTION   behind_market line 345 keeps connecting_airport1 IS NOT NULL AND
                      connecting_airport2 IS NULL, so nonstop and double-connection
                      itineraries are both out.
  OAG FEEDERS         feeders_to keeps only airports OAG shows flying into the origin
                      catchment in the scheduled week.
  ON THE WAY          the circuity test drops a feeder whose routing via the origin
                      exceeds 1.35 times its own great circle to the destination.

This measures each one on the engine's OWN inputs, taken from a live payload rather than
retyped, so the last line reproduces what the engine used and the differences above it
are attributable one at a time.

NOTHING IS CHANGED AND NO FILTER IS JUDGED HERE. A filter that removes a lot may still be
the right filter: a passenger who will not route via the origin is not addressable market.
The purpose is to know which one carries the factor of six before arguing about it.

Usage (workstation):
    py -3.12 behind_market_decompose.py --origin SJC --dest TPE --airline CI --aircraft A359 --freq 4
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

FACTOR_INDIRECT = 1.044
CIRCUITY = 1.35


def _sabre_behind_by_origin(sabre_db, dest_codes, year, single_only=True, factor=FACTOR_INDIRECT):
    """The behind market per origin airport, every origin. Used to cut US against the rest
    without passing a fifteen-hundred-code IN list."""
    from db_registry import con_ro
    where = ["source_year = ?", "destination_airport IN (%s)" % ",".join("?" * len(dest_codes))]
    params = [int(year), *dest_codes]
    if single_only:
        where.append("connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL")
    con = con_ro(sabre_db)
    try:
        rows = con.execute(
            f"SELECT origin_airport, SUM(passengers * {factor}) FROM sabre "
            f"WHERE {' AND '.join(where)} GROUP BY 1", params).fetchall()
    finally:
        con.close()
    return {r[0]: float(r[1] or 0.0) for r in rows if r[0]}


def _sabre_behind(sabre_db, feeders, dest_codes, year, single_only=True, factor=FACTOR_INDIRECT):
    """Total behind market. feeders empty means EVERY origin, which is the whole market."""
    # con_ro, not duckdb.connect. The engine has already opened the Sabre store in this
    # process with its own configuration, and DuckDB refuses a second connection to the
    # same file under a different one. The registry hands out a cursor over the existing
    # base connection, which is what every other reader in the engine uses.
    from db_registry import con_ro
    where = ["source_year = ?"]
    params = [int(year)]
    if feeders:
        where.append("origin_airport IN (%s)" % ",".join("?" * len(feeders)))
        params += list(feeders)
    where.append("destination_airport IN (%s)" % ",".join("?" * len(dest_codes)))
    params += list(dest_codes)
    if single_only:
        where.append("connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL")
    con = con_ro(sabre_db)
    try:
        row = con.execute(
            f"SELECT count(DISTINCT origin_airport), SUM(passengers * {factor}) "
            f"FROM sabre WHERE {' AND '.join(where)}", params).fetchone()
    finally:
        con.close()
    return int(row[0] or 0), float(row[1] or 0.0)


def main():
    ap = argparse.ArgumentParser(description="Decompose the behind market filter by filter.")
    ap.add_argument("--origin", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--airline", default=None)
    ap.add_argument("--carrier-type", default="FSC")
    ap.add_argument("--aircraft", default="A21X")
    ap.add_argument("--freq", type=float, default=7)
    ap.add_argument("--dest-codes", default=None,
                    help="destination airport group; defaults to --dest alone")
    ap.add_argument("--analyst", type=float, default=None,
                    help="the comparison figure, printed beside ours; not used in any sum")
    args = ap.parse_args()

    import cortex_app as CA
    import route_feed as RF
    import config

    fc = CA.calibrated_forecast(origin=args.origin, dest=args.dest, airline=args.airline,
                                carrier_type=args.carrier_type, aircraft=args.aircraft,
                                freq=args.freq, with_econ=True)
    week, year = fc.get("week"), fc.get("year")
    shares = ((fc.get("catchment") or {}).get("observed_share")) or {}
    catchment = sorted(shares) or [args.origin.upper()]
    dest_codes = ([c.strip().upper() for c in args.dest_codes.split(",")]
                  if args.dest_codes else [args.dest.upper()])
    sabre_db, oag_db = str(config.SABRE_DUCKDB), str(config.OAG_DUCKDB)

    print(f"{args.origin}-{args.dest}  week {week}  year {year}")
    print(f"  origin catchment as the engine resolved it: {', '.join(catchment)}")
    print(f"  the BEHIND side uses the route origin alone, {args.origin.upper()}, per "
          f"route_forecast line 635")
    print(f"  destination group: {', '.join(dest_codes)}\n")

    # 0. Whole market, every origin, every itinerary type.
    n0, m0 = _sabre_behind(sabre_db, None, dest_codes, year, single_only=False)
    # 1. Whole market, single-connection only.
    n1, m1 = _sabre_behind(sabre_db, None, dest_codes, year, single_only=True)
    # 1b. US origins only, single-connection. The comparison figure is expected to sit near
    #     this if the analyst took the whole US market to the destination as his behind market.
    per_origin = _sabre_behind_by_origin(sabre_db, dest_codes, year, single_only=True)
    try:
        import airportsdata
        _ap = airportsdata.load("IATA")
        us = [a for a in per_origin if (_ap.get(a) or {}).get("country") == "US"]
    except Exception:
        us = []
    n1b, m1b = len(us), sum(per_origin[a] for a in us)
    # THE BEHIND SIDE USES THE ROUTE ORIGIN, NOT THE CATCHMENT. route_forecast line 635 calls
    # behind_feed with [origin] and says why at line 633: a route into a small airport must not
    # inherit a big neighbour's feed bank. The first version of this tool used the catchment and
    # therefore reconstructed a market the engine does not use.
    origin_side = [args.origin.upper()]
    # 2. Restricted to the OAG feeders into the route origin.
    feeders = [y for y in RF.feeders_to(oag_db, week, origin_side)
               if y not in origin_side and y not in dest_codes]
    n2, m2 = _sabre_behind(sabre_db, feeders, dest_codes, year, single_only=True)
    # 3. Plus the on-the-way circuity test, replicating behind_feed lines 368 to 379.
    ocen, dcen = RF._centroid(origin_side), RF._centroid(dest_codes)
    od = RF._gc(ocen, dcen) or 0
    kept = []
    for y in feeders:
        yc = RF._coords(y)
        if not yc:
            continue
        yd = RF._gc(yc, dcen)
        if yd and yd > 100 and ((RF._gc(yc, ocen) or 0) + od) <= CIRCUITY * yd:
            kept.append(y)
    n3, m3 = _sabre_behind(sabre_db, kept, dest_codes, year, single_only=True)

    rows = [("every origin, every itinerary", n0, m0),
            ("every origin, single-connection only", n1, m1),
            ("US origins only, single-connection", n1b, m1b),
            (f"OAG feeders into {origin_side[0]} alone", n2, m2),
            ("and on the way, circuity 1.35", n3, m3)]
    print(f"  {'level':<38} {'origins':>8} {'market':>14} {'kept':>8}")
    for label, n, m in rows:
        kept_pct = (m / m0) if m0 else None
        print(f"  {label:<38} {n:>8,} {m:>14,.0f} "
              f"{('-' if kept_pct is None else f'{kept_pct:.1%}'):>8}")

    print(f"\n  each filter's own cost:")
    for (la, _, ma), (lb, _, mb) in zip(rows, rows[1:]):
        drop = (1 - mb / ma) if ma else None
        print(f"    {lb:<40} removes {('-' if drop is None else f'{drop:.1%}')} of the level above")

    if args.analyst:
        print(f"\n  comparison figure {args.analyst:,.0f}: the whole market is "
              f"{m0 / args.analyst:.2f}x it, single-connection {m1 / args.analyst:.2f}x, "
              f"the engine's own market {m3 / args.analyst:.2f}x")
        print("  Read which level his definition sits nearest. That names the difference "
              "rather than arguing about the rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
