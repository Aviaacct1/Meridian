#!/usr/bin/env python3
"""Avia Solutions - the behind-side under-read and the collapse key, 11 August 2026.

THE HYPOTHESIS. qsi_feed._collapse groups one-stop itineraries by (onward carrier, connection type),
keeps the best elapsed of the group and sums their connectable frequency into a single capped entry.
That grouping is not symmetric between the two feed sides:

  beyond side  leg 2 is the hub's onward bank, many carriers, so the new route earns one entry per
               onward carrier and can reach several
  behind side  leg 2 IS the new route, one carrier, so every feeder arrival at the origin collapses
               into exactly ONE entry, capped at freq_cap, against thirty to ninety competing entries

If that is the cause, keying on both operating carriers should lift the behind side materially. It
also changes the competitor sets on both sides, so the beyond side has to be measured too: a change
that fixes one side by breaking the other is not a fix.

Measured at the optimised departure for the carrier, so the comparison is like for like, and against
the 2025 analyst's blended rates as a diagnostic rather than a target.
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
DEP = int(sys.argv[1]) if len(sys.argv) > 1 else 30      # 00:30, the optimised time for CI
AIRLINES = (sys.argv[2].split(",") if len(sys.argv) > 2 else ["CI"])

ANALYST_BEYOND_RATE = 15969 / 1097630            # 1.455%
ANALYST_BEHIND_RATE = 18609 / 446013             # 4.172%


def main():
    oag, sabre = os.environ["AVIA_OAG"], os.environ["AVIA_SABRE"]
    week = duckdb.connect(oag, read_only=True).execute("SELECT max(week) FROM oag").fetchone()[0]
    year = duckdb.connect(sabre, read_only=True).execute(
        "SELECT max(source_year) FROM sabre").fetchone()[0]

    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]
    boards = OagBoards(oag)
    mct = MB.load_mct()

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

    print(f"OAG week {week}, Sabre year {year}, departure {DEP // 60:02d}:{DEP % 60:02d}")
    print(f"analyst blended rates: beyond {ANALYST_BEYOND_RATE:.4%}, behind {ANALYST_BEHIND_RATE:.4%}\n")
    print(f"  {'carrier':8} {'collapse key':22} {'beyond':>9} {'vs analyst':>11} "
          f"{'behind':>9} {'vs analyst':>11}")

    for al in AIRLINES:
        for both, label in ((False, "onward carrier only"), (True, "both operating carriers")):
            QF.COLLAPSE_BY_BOTH_LEGS = both
            cfg = {"circuity": 1.35, "route_origin": ORIGIN,
                   "route_flying_mins": FLYING_MINS, "route_freq": FREQ}
            bs = QF.beyond_capture(boards, week, competing, DEST, list(b_mkt.keys()), al,
                                   DEP, FLYING_MINS, FREQ, mct=mct, cfg=cfg)
            hs = QF.behind_capture(boards, week, [ORIGIN], [DEST], list(h_mkt.keys()), al,
                                   DEP, mct=mct, cfg=cfg)
            wb, wh = weighted(b_mkt, bs), weighted(h_mkt, hs)
            nz = sum(1 for y in h_mkt if hs.get(y, 0.0) > 0)
            print(f"  {al:8} {label:22} {wb:>9.4%} {wb / ANALYST_BEYOND_RATE:>10.2f}x "
                  f"{wh:>9.4%} {wh / ANALYST_BEHIND_RATE:>10.2f}x   "
                  f"({nz} of {len(h_mkt)} feeders non-zero)")


if __name__ == "__main__":
    main()
