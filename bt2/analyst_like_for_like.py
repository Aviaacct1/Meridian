#!/usr/bin/env python3
"""Avia Solutions - Meridian against the 2025 analyst on HIS schedule, 11 August 2026.

Comparing capture rates across two different departure times compares two different products. The
analyst built his connection banks off one assumed schedule; Meridian now chooses its own. Until both
run on the same timings the difference between them is partly method and partly schedule, and there
is no way to say how much of each.

THE ANALYST'S SCHEDULE, from the methodology section of China Airlines TPE-SJC Forecast 17Sep25.pptx:
"The forecast assumes the following schedule: Early morning (09:30) arrival and 2h 30m layover at
SJC. 4x weekly service using A350-900 aircraft. The proposed schedule seeks to mitigate night curfew
restrictions at SJC and capacity constraints at TPE to allow optimal connectivity at both ends of the
route, including onward connections on Southwest Airlines network at San Jose."

So his inbound lands at 09:30 and his outbound departs San Jose at 12:00. He was already working
around the San Jose curfew, and around Taipei's slot constraints, which Meridian does not model.

His stated connecting scope is worth holding beside the result: beyond Taipei he counts China
Airlines, SkyTeam and codeshare partners with basic interline onto other legacy carriers; behind San
Jose he counts SkyTeam carriers AND Southwest, again with basic interline onto other full-service
carriers. Nothing is excluded on either side, which is the same treatment Meridian applies.

Arms: the analyst's departure, Meridian's unrestricted optimum, and Meridian's optimum under the San
Jose night restriction.
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
AIRLINES = ["CI"]

ANALYST_DEP = 12 * 60                            # 09:30 arrival plus a 2h30 layover at San Jose
ARMS = [(ANALYST_DEP, "the analyst's departure, 12:00"),
        (30, "Meridian's optimum, 00:30"),
        (390, "Meridian under the SJC restriction, 06:30")]

# The analyst's blended rates. Beyond 15,969 on a base of 1,097,630; behind 18,609 on a
# connecting-only base of 446,013. Both YE Jun 2028, so his 33% growth cancels out of the rate.
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

    print(f"OAG week {week}, Sabre year {year}")
    print(f"beyond base {sum(b_mkt.values()):,.0f} each way over {len(b_mkt)} markets; "
          f"behind base {sum(h_mkt.values()):,.0f} over {len(h_mkt)}")
    print(f"analyst blended: beyond {ANALYST_BEYOND_RATE:.4%}, behind {ANALYST_BEHIND_RATE:.4%}\n")

    for al in AIRLINES:
        print(f"{al}")
        print(f"  {'departure':42} {'arr TPE':>8} {'beyond':>9} {'vs':>7} {'behind':>9} {'vs':>7}")
        for dep, label in ARMS:
            cfg = {"circuity": 1.35, "route_origin": ORIGIN,
                   "route_flying_mins": FLYING_MINS, "route_freq": FREQ}
            arr = QF._hub_arrival_mins(ORIGIN, DEST, dep, FLYING_MINS, cfg)
            bs = QF.beyond_capture(boards, week, competing, DEST, list(b_mkt.keys()), al,
                                   dep, FLYING_MINS, FREQ, mct=mct, cfg=cfg)
            hs = QF.behind_capture(boards, week, [ORIGIN], [DEST], list(h_mkt.keys()), al,
                                   dep, mct=mct, cfg=cfg)
            wb, wh = weighted(b_mkt, bs), weighted(h_mkt, hs)
            print(f"  {label:42} {arr // 60:02d}:{arr % 60:02d}    {wb:>8.4%} "
                  f"{wb / ANALYST_BEYOND_RATE:>6.2f}x {wh:>9.4%} {wh / ANALYST_BEHIND_RATE:>6.2f}x")


if __name__ == "__main__":
    main()
