#!/usr/bin/env python3
"""Avia Solutions - the competitor-hub exclusion, measured, 11 August 2026.

THE DEFECT. route_forecast passes the whole 44-airport catchment to beyond_capture as
`origin_airports` and the single route origin to behind_capture. Both then exclude `origin_airports`
from the set of airports that may act as a competing connecting point. So the beyond side barred every
Bay Area airport including San Francisco, and the behind side barred only San Jose.

San Francisco carries nonstops to Taipei, Seoul, Tokyo, Hong Kong, Shanghai and Singapore. Removing it
from the beyond competition deletes the strongest set of rival routings a San Jose passenger has, so
the beyond share should read high. Keeping it in the behind competition, which is correct, leaves the
behind share looking low beside it. One inconsistent exclusion, two errors in opposite directions,
which is exactly the pattern in the numbers: beyond 1.48x the analyst and behind 0.68x.

Measured at the analyst's own 12:00 departure, so the schedule is not a variable.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import duckdb                                    # noqa: E402
import route_engine as RE                        # noqa: E402
import route_feed as RFEED                       # noqa: E402
import qsi_feed as QF                            # noqa: E402
import mct_bank as MB                            # noqa: E402
from wave_cache import OagBoards                 # noqa: E402

ORIGIN, DEST = "SJC", "TPE"
FLYING_MINS, FREQ = 825, 4
DEP = 12 * 60                                    # the analyst's departure
AIRLINES = ["CI", "BR", "UA"]

ANALYST_BEYOND_RATE = 15969 / 1097630
ANALYST_BEHIND_RATE = 18609 / 446013


def main():
    oag, sabre = os.environ["AVIA_OAG"], os.environ["AVIA_SABRE"]
    week = duckdb.connect(oag, read_only=True).execute("SELECT max(week) FROM oag").fetchone()[0]
    year = duckdb.connect(sabre, read_only=True).execute(
        "SELECT max(source_year) FROM sabre").fetchone()[0]

    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]
    boards, mct = OagBoards(oag), MB.load_mct()

    scope = [x for x in RFEED.hub_served(oag, week, DEST) if x not in competing]
    scope = RFEED.on_the_way(competing, DEST, scope, circuity=1.35)
    b_mkt = RFEED.connecting_market(sabre, competing, scope, year, 1.044)

    feeders = [y for y in RFEED.feeders_to(oag, week, [ORIGIN]) if y not in (ORIGIN, DEST)]
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
    h_mkt = RFEED.behind_market(sabre, kept, [DEST], year, 1.044)

    def weighted(mkt, sh):
        t = sum(mkt.values())
        return sum(mkt[m] * sh.get(m, 0.0) for m in mkt) / t if t else 0.0

    print(f"OAG week {week}, Sabre year {year}, departure {DEP // 60:02d}:{DEP % 60:02d} "
          f"(the analyst's)")
    print(f"analyst blended: beyond {ANALYST_BEYOND_RATE:.4%}, behind {ANALYST_BEHIND_RATE:.4%}\n")
    print(f"  {'carrier':8} {'competitor hubs barred':32} {'beyond':>9} {'vs':>7} "
          f"{'behind':>9} {'vs':>7}")

    for al in AIRLINES:
        for whole, label in ((True, "the whole catchment, 44 airports"),
                             (False, "the route origin only, SJC")):
            cfg = {"circuity": 1.35, "route_origin": ORIGIN, "exclude_whole_catchment": whole,
                   "route_flying_mins": FLYING_MINS, "route_freq": FREQ}
            bs = QF.beyond_capture(boards, week, competing, DEST, list(b_mkt.keys()), al,
                                   DEP, FLYING_MINS, FREQ, mct=mct, cfg=cfg)
            hs = QF.behind_capture(boards, week, [ORIGIN], [DEST], list(h_mkt.keys()), al,
                                   DEP, mct=mct, cfg=cfg)
            wb, wh = weighted(b_mkt, bs), weighted(h_mkt, hs)
            print(f"  {al:8} {label:32} {wb:>9.4%} {wb / ANALYST_BEYOND_RATE:>6.2f}x "
                  f"{wh:>9.4%} {wh / ANALYST_BEHIND_RATE:>6.2f}x")


if __name__ == "__main__":
    main()
