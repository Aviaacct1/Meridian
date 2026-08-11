#!/usr/bin/env python3
r"""Avia Solutions - does this connecting market already have a nonstop? The competition bucket.

    py -3.12 direct_competition.py SJC MNL SGN BKK

WHY. Every Avia route forecast in the client format splits connecting markets into two buckets, O&Ds
that already have a direct service and O&Ds that do not, and applies a materially different capture
rate to each. On the China Airlines TPE-SJC forecast of August 2026 the split reads 0.0% against 1.5%
beyond Taipei and 0.2% against 4.7% behind San Jose. It is the first thing an airline planner looks
for, because it separates the traffic a one-stop can realistically win from the traffic that already
has a better option.

Meridian scores every routing through the QSI machinery and returns one capture per market, so the
information to build the bucket exists and is thrown away. This module recovers it from the same OAG
schedule the engine already reads: a market has DIRECT COMPETITION if any carrier flies the O&D
nonstop in the scheduled week.

WHAT IT IS NOT. This is competition on the O&D, not competition on the route. A nonstop flown once a
week by a carrier nobody would connect over still counts as direct competition here, because the
passenger has the option. Frequency-weighting the test would be a modelling change and is deliberately
not done: the bucket is a fact about the schedule, and the capture rate inside each bucket is where
judgement belongs.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def nonstop_markets(oag_db, week, origin_airports, market_codes):
    """The subset of market_codes that ALREADY have a nonstop from any of origin_airports, in either
    direction, in this scheduled week. One query, whatever the size of the market list."""
    if not market_codes or not origin_airports:
        return set()
    import duckdb
    o = [str(a).strip().upper() for a in origin_airports if a]
    m = [str(a).strip().upper() for a in market_codes if a]
    if not o or not m:
        return set()
    con = duckdb.connect(oag_db, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=3; SET enable_progress_bar=false")
    try:
        ph_o = ",".join("?" * len(o))
        ph_m = ",".join("?" * len(m))
        rows = con.execute(f"""
            SELECT DISTINCT arr_airport FROM oag
             WHERE week = ? AND service_type='J' AND try_cast(stops AS INT)=0
               AND dep_airport IN ({ph_o}) AND arr_airport IN ({ph_m})
            UNION
            SELECT DISTINCT dep_airport FROM oag
             WHERE week = ? AND service_type='J' AND try_cast(stops AS INT)=0
               AND arr_airport IN ({ph_o}) AND dep_airport IN ({ph_m})
        """, [week] + o + m + [week] + o + m).fetchall()
    finally:
        con.close()
    return {r[0] for r in rows if r[0]}


def bucket(detail, oag_db, week, origin_airports):
    """Split a feed detail map into the two buckets and total each.

    detail is {code: {"base":..., "captured":..., "pdew":..., ...}} as route_feed returns it.
    Returns (rows, totals) where rows carries a direct flag per market and totals carries the two
    bucket subtotals with their own blended capture rate, which is the number the client table shows.
    """
    codes = [c for c in (detail or {})]
    try:
        direct = nonstop_markets(oag_db, week, origin_airports, codes)
    except Exception:
        direct = set()                       # fail open: everything reads as no direct competition,
                                             # which is the conservative side for a capture rate
    rows, tot = [], {"direct": {"base": 0.0, "forecast": 0.0, "n": 0},
                     "no_direct": {"base": 0.0, "forecast": 0.0, "n": 0}}
    for code, c in (detail or {}).items():
        is_direct = code in direct
        b = float(c.get("base") or 0.0)
        f = float(c.get("captured") or 0.0)
        rows.append({"code": code, "direct_competition": is_direct,
                     "base": round(b), "forecast": round(f),
                     "share": (round(f / b, 4) if b else None)})
        k = "direct" if is_direct else "no_direct"
        tot[k]["base"] += b; tot[k]["forecast"] += f; tot[k]["n"] += 1
    for k in tot:
        b, f = tot[k]["base"], tot[k]["forecast"]
        tot[k] = {"markets": tot[k]["n"], "base": round(b), "forecast": round(f),
                  "capture": (round(f / b, 4) if b else None)}
    rows.sort(key=lambda r: -r["forecast"])
    return rows, tot


if __name__ == "__main__":
    import capacity_frame as CF
    db = CF._oag()
    if not db:
        sys.exit("no OAG store found. Set AVIA_OAG_DUCKDB or AVIA_LOCAL_CACHE.")
    import duckdb
    con = duckdb.connect(db, read_only=True)
    con.execute("SET enable_progress_bar=false")
    wk = con.execute("SELECT max(week) FROM oag").fetchone()[0]
    con.close()
    org = sys.argv[1] if len(sys.argv) > 1 else "SJC"
    mk = sys.argv[2:] or ["MNL", "SGN", "BKK", "PVG", "HKG", "ICN", "NRT", "SIN"]
    d = nonstop_markets(db, wk, [org], mk)
    print("week %s, nonstop from %s:" % (wk, org))
    for m in mk:
        print("  %-5s %s" % (m, "DIRECT COMPETITION" if m in d else "no direct service"))
