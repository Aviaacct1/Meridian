#!/usr/bin/env python3
"""Alliance seat share at an airport for the OAG snapshot week.

Built 18 August 2026 so ONE workbook download can populate a client deck's
competition slide (the EVA deck review found the alliance table was the one figure
no Meridian output carried). The forecast pack's competition page takes the same
shape, so this one function can feed both.

THE DEDUPE IS route_watch.daily_seats', copied not re-derived: days_of_op is a
seven-character SSIM mask and the store repeats one schedule record per REGION
label, so one figure per (carrier, flight_no, dep, arr, local_dep_time), max(mask)
and max(seats) across the duplicates, BEFORE any summing. A record whose mask holds
no digit has no weekly frequency and is left out, never spread.

The alliance map is route_feed.ALLIANCE, the same one that prices the connecting
feed, so the competition table and the engine can never name different alliances.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

_NAMES = {"*A": "Star Alliance", "OW": "oneworld", "ST": "SkyTeam"}


def _aggregate(rows, alliance_map):
    """(carrier, mask, seats) rows -> {"rows": [(alliance, share)], "weekly_seats": n}.
    Pure, so the fixture test needs no store. Weekly seats = seats x operating days."""
    tot = 0.0
    by = {}
    for car, mask, seats in rows:
        days = sum(ch.isdigit() for ch in (mask or ""))
        if not days or not seats or seats <= 0:
            continue
        wk = float(seats) * days
        tot += wk
        al = _NAMES.get(alliance_map.get((car or "").strip().upper()), "Unaligned")
        by[al] = by.get(al, 0.0) + wk
    if tot <= 0:
        return None
    out = sorted(((k, v / tot) for k, v in by.items()), key=lambda x: -x[1])
    return {"rows": out, "weekly_seats": round(tot)}


def seat_share(db, airport):
    """{"ok", "airport", "week", "rows": [(alliance, share)], "weekly_seats"} or a
    named refusal. Departing seats, scheduled passenger service only."""
    import route_watch as RW
    from route_feed import ALLIANCE
    airport = (airport or "").strip().upper()
    if not airport:
        return {"ok": False, "error": "no airport given"}
    con = RW._con(db)
    try:
        cur, _prior, note, _form = RW.pick_weeks(con, airport)
        if not cur:
            return {"ok": False, "error": note or "no snapshot holds this airport"}
        svc = RW._svc_filter(con)
        rows = con.execute(
            f"WITH d AS ("
            f"  SELECT carrier, flight_no, dep_airport, arr_airport, local_dep_time, "
            f"         max(coalesce(days_of_op, '')) AS mask, "
            f"         max(coalesce(TRY_CAST(seats_total AS DOUBLE), 0.0)) AS seats "
            f"  FROM oag WHERE week = ? AND dep_airport = ? AND {svc} "
            f"  GROUP BY carrier, flight_no, dep_airport, arr_airport, local_dep_time) "
            f"SELECT carrier, mask, seats FROM d", [cur, airport]).fetchall()
    finally:
        con.close()
    agg = _aggregate(rows, ALLIANCE)
    if not agg:
        return {"ok": False, "error": "no departing seats measured in week %s" % cur}
    return {"ok": True, "airport": airport, "week": cur, **agg}
