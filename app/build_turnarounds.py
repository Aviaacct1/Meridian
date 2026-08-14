#!/usr/bin/env python3
r"""
Avia Solutions - measured station turnarounds by aircraft type, from OAG.
========================================================================
WHY. route_feed.turnaround_mins ships planning averages of 60, 90 and 180 minutes by flight
type. They have no source. The turnaround ties the return arrival to the outbound departure
and therefore decides which departures are flyable at all, so an invented figure moves a
client-facing schedule. John's instruction, 14 August: calculate turns from 2025 OAG, and
key them on AIRCRAFT TYPE rather than region, since it is the aeroplane that sets the stand
time and region only proxies for it.

THE METHOD, AND THE FILTER THAT MAKES IT HONEST. OAG carries no tail numbers, so an arrival
cannot be linked with certainty to the departure that reuses the same aircraft. At a hub
that is fatal: an arrival and a departure of the same type ten minutes apart are two
different aeroplanes, and a naive minimum gap would report a ten-minute turn.

So only UNAMBIGUOUS station-days are measured: those where one carrier operated EXACTLY ONE
arrival and EXACTLY ONE departure of one aircraft type at one airport on one day. There the
gap is that aircraft's turn and nothing else. It is also the case a route forecast cares
about, a new service at an outstation, which is precisely where the turnaround binds.

WHAT IS EXCLUDED AND WHY, all counted and reported rather than dropped in silence:
  service_type J only        scheduled passenger service; charter and freight turn differently
  stops = 0                  a through-flight's stop is a transit, not a station turn
  gap >= NIGHT_STOP_MIN      an overnight is a night stop, not a turnaround. Reported
                             separately, because a station that night-stops is a real finding
  gap < FLOOR_MIN            below this the pairing is not credible on any widebody

The output is a table per aircraft type with n, the 10th, 25th and 50th percentiles and the
minimum. THE FIGURE TO USE IS THE LOW PERCENTILE, NOT THE MEDIAN: a turnaround is the time
the aeroplane needs, and the median mixes in stations that simply had a long gap. The 10th
percentile across a large n is the operational floor.

Usage (workstation):
    py -3.12 build_turnarounds.py --weeks 2025 --out E:\Avia\turnarounds_2025.json
    py -3.12 build_turnarounds.py --weeks 2025 --min-n 30 --csv E:\Avia\turnarounds_2025.csv
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

NIGHT_STOP_MIN = 8 * 60      # at or above this it is a night stop, not a turn
FLOOR_MIN = 20               # below this a pairing is not credible; counted, never used
DEFAULT_MIN_N = 20           # types with fewer unambiguous station-days are reported, not used


def _mins(t):
    """OAG local times arrive as HHMM or HH:MM. Returns minutes past midnight, or None."""
    s = str(t or "").strip()
    if not s:
        return None
    s = s.replace(":", "")
    if not s.isdigit() or len(s) not in (3, 4):
        return None
    s = s.zfill(4)
    h, m = int(s[:2]), int(s[2:])
    return (h * 60 + m) if (h < 24 and m < 60) else None


def _days(spec):
    """days_of_op as a set of ints 1-7. OAG writes '1 3 5 7', '1234567' or with dots."""
    out = set()
    for ch in str(spec or ""):
        if ch.isdigit() and ch != "0":
            out.add(int(ch))
    return out


def build(con, weeks, min_n, verbose=True):
    where = ["service_type = 'J'", "try_cast(stops AS INT) = 0",
             "aircraft_code IS NOT NULL", "aircraft_code <> ''"]
    params = []
    if weeks:
        where.append("CAST(year AS VARCHAR) = ?")
        params.append(str(weeks))
    sql = (f"SELECT week, carrier, aircraft_code, aircraft_name, dep_airport, arr_airport, "
           f"local_dep_time, local_arr_time, days_of_op, arr_days_of_op "
           f"FROM oag WHERE {' AND '.join(where)}")
    rows = con.execute(sql, params).fetchall()
    if verbose:
        print(f"  {len(rows):,} scheduled nonstop passenger legs with an aircraft code")

    # (airport, carrier, type, day) -> {"arr": [mins], "dep": [mins]}
    station = {}
    for wk, car, ac, acn, dep_ap, arr_ap, dt, at, dop, adop in rows:
        dm, am = _mins(dt), _mins(at)
        if dm is None or am is None:
            continue
        for day in _days(dop):
            station.setdefault((wk, dep_ap, car, ac, day), {"arr": [], "dep": []})["dep"].append(dm)
        # The arrival day can differ from the departure day; OAG carries its own field for it.
        for day in (_days(adop) or _days(dop)):
            station.setdefault((wk, arr_ap, car, ac, day), {"arr": [], "dep": []})["arr"].append(am)

    names, gaps = {}, {}
    counts = {"ambiguous": 0, "unambiguous": 0, "night_stop": 0, "below_floor": 0}
    for (_wk, _ap, _car, ac, _day), v in station.items():
        if len(v["arr"]) != 1 or len(v["dep"]) != 1:
            counts["ambiguous"] += 1
            continue
        counts["unambiguous"] += 1
        gap = (v["dep"][0] - v["arr"][0]) % 1440
        if gap >= NIGHT_STOP_MIN:
            counts["night_stop"] += 1
            continue
        if gap < FLOOR_MIN:
            counts["below_floor"] += 1
            continue
        gaps.setdefault(ac, []).append(gap)
    for _wk, _car, ac, acn, *_rest in rows:
        if acn and ac not in names:
            names[ac] = acn

    def pct(xs, p):
        xs = sorted(xs)
        return xs[min(int(round(p * (len(xs) - 1))), len(xs) - 1)]

    table = {}
    for ac, xs in gaps.items():
        table[ac] = {"name": names.get(ac, ""), "n": len(xs),
                     "p10": pct(xs, 0.10), "p25": pct(xs, 0.25), "p50": pct(xs, 0.50),
                     "min": min(xs), "usable": len(xs) >= min_n}
    return table, counts


def main():
    ap = argparse.ArgumentParser(description="Measure station turnarounds by aircraft type.")
    ap.add_argument("--oag", default=None, help="defaults to config.OAG_DUCKDB")
    ap.add_argument("--weeks", default="2025", help="OAG year to measure; 2025 per John")
    ap.add_argument("--min-n", type=int, default=DEFAULT_MIN_N)
    ap.add_argument("--out", default=None, help="JSON table for route_feed to read")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    oag = args.oag
    if not oag:
        import config
        oag = str(config.OAG_DUCKDB)
    if not os.path.exists(oag):
        print(f"ERROR: OAG store not found at {oag}")
        return 2

    from db_registry import con_ro
    con = con_ro(oag)
    try:
        table, counts = build(con, args.weeks, args.min_n)
    finally:
        con.close()

    print(f"\n  station-days: {counts['unambiguous']:,} unambiguous, "
          f"{counts['ambiguous']:,} with more than one movement either way and therefore skipped")
    print(f"  of the unambiguous: {counts['night_stop']:,} night stops (8h or more, not a turn), "
          f"{counts['below_floor']:,} below the {FLOOR_MIN}-minute floor")

    usable = {k: v for k, v in table.items() if v["usable"]}
    print(f"\n  {len(table)} aircraft types measured, {len(usable)} with n >= {args.min_n}\n")
    print(f"  {'type':<8} {'name':<26} {'n':>6} {'p10':>6} {'p25':>6} {'p50':>6} {'min':>6}")
    for ac, v in sorted(usable.items(), key=lambda kv: -kv[1]["n"])[:args.top]:
        print(f"  {ac:<8} {(v['name'] or '')[:26]:<26} {v['n']:>6,} {v['p10']:>6} "
              f"{v['p25']:>6} {v['p50']:>6} {v['min']:>6}")

    print("\n  THE FIGURE TO USE IS p10, not the median: a turnaround is the time the aeroplane "
          "needs,\n  and the median mixes in stations that simply had a long gap. Types below the "
          "minimum n are\n  written to the file but marked unusable rather than dropped.")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"source": "OAG %s, unambiguous single-arrival single-departure station-days"
                                 % args.weeks,
                       "night_stop_min": NIGHT_STOP_MIN, "floor_min": FLOOR_MIN,
                       "min_n": args.min_n, "counts": counts, "types": table}, fh, indent=1)
        print(f"\n  wrote {args.out}")
    if args.csv:
        import csv as _csv
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = _csv.writer(fh)
            w.writerow(["aircraft_code", "aircraft_name", "n", "p10", "p25", "p50", "min", "usable"])
            for ac, v in sorted(table.items()):
                w.writerow([ac, v["name"], v["n"], v["p10"], v["p25"], v["p50"], v["min"],
                            v["usable"]])
        print(f"  wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
