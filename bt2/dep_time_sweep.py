#!/usr/bin/env python3
"""Avia Solutions - how much of the QSI feed is the schedule? 11 August 2026.

With the hub arrival corrected, two things about the feed become visible and both need measuring
before anything is switched on.

FIRST, the departure time is invented. cortex_app._schedule_times places the outbound at 11:00 local
by default and says of itself that it is illustrative, not curfew-, slot- or connection-optimised. If
the QSI feed's answer moves a long way across the day then switching it on makes Meridian's
connecting forecast a function of a placeholder, which is worse than the flat rate it replaces.

SECOND, MAX_CONNECT is 720 minutes. qsi_feed's own docstring says that cap is about compute rather
than method, on the reasoning that the elapsed-time decay makes long layovers near-worthless anyway.
A late-afternoon long-haul arrival into an Asian hub connects to a great deal of its short-haul bank
the following morning, so a hard twelve-hour cut may be doing methodological work it was not meant to
do.

This sweeps the departure time across the day and reports the demand-weighted capture on each side,
at two connection windows. Weighted by market size, because an unweighted average of 55 shares tells
you about Ishigaki as loudly as about Manila.
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

ORIGIN, DEST, AIRLINE = "SJC", "TPE", "CI"
FLYING_MINS, FREQ = 825, 4
STEP = 60
SIDE = sys.argv[1] if len(sys.argv) > 1 else "beyond"

# The analyst's blended rates, from the working note of 11 August 2026 section 4.
ANALYST_BEYOND_RATE = 15969 / 1097630
ANALYST_BEHIND_RATE = 18609 / 446013


def weighted(market, shares):
    tot = sum(market.values())
    return sum(market[m] * shares.get(m, 0.0) for m in market) / tot if tot else 0.0


def main():
    oag, sabre = os.environ["AVIA_OAG"], os.environ["AVIA_SABRE"]
    c = duckdb.connect(oag, read_only=True)
    week = c.execute("SELECT max(week) FROM oag").fetchone()[0]
    c.close()
    c = duckdb.connect(sabre, read_only=True)
    year = c.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
    c.close()

    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]
    boards = OagBoards(oag)
    mct = MB.load_mct()

    if SIDE == "beyond":
        scope = [x for x in RFEED.hub_served(oag, week, DEST) if x not in competing]
        scope = RFEED.on_the_way(competing, DEST, scope, circuity=1.35)
        market = RFEED.connecting_market(sabre, competing, scope, year, 1.044)
        ref = ANALYST_BEYOND_RATE
    else:
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
        market = RFEED.behind_market(sabre, kept, [DEST], year, 1.044)
        ref = ANALYST_BEHIND_RATE

    print(f"OAG week {week}, Sabre year {year}. {SIDE} side, {len(market)} markets, "
          f"base {sum(market.values()):,.0f} each way")
    print(f"analyst blended rate for this side: {ref:.4%}\n")
    print(f"  {'dep':>6} {'arr at hub':>11}   " +
          "   ".join(f"maxc {mc:>4}" for mc in (720, 1440)))

    best = {}
    for dep in range(0, 1440, STEP):
        row, arr_lbl = [], ""
        for mc in (720, 1440):
            cfg = {"circuity": 1.35, "route_origin": ORIGIN, "max_connect": mc,
                   "route_flying_mins": FLYING_MINS, "route_freq": FREQ}
            if SIDE == "beyond":
                arr = QF._hub_arrival_mins(ORIGIN, DEST, dep, FLYING_MINS, cfg)
                arr_lbl = f"{arr // 60:02d}:{arr % 60:02d}"
                sh = QF.beyond_capture(boards, week, competing, DEST, list(market.keys()), AIRLINE,
                                       dep, FLYING_MINS, FREQ, mct=mct, cfg=cfg)
            else:
                arr_lbl = "n/a"
                sh = QF.behind_capture(boards, week, [ORIGIN], [DEST], list(market.keys()),
                                       AIRLINE, dep, mct=mct, cfg=cfg)
            w = weighted(market, sh)
            row.append(w)
            if w > best.get(mc, (-1, None))[0]:
                best[mc] = (w, dep)
        print(f"  {dep // 60:02d}:{dep % 60:02d}  {arr_lbl:>11}   " +
              "   ".join(f"{w:>9.4%}" for w in row))

    print()
    for mc in (720, 1440):
        w, dep = best[mc]
        print(f"  best at maxc {mc}: {w:.4%} at a {dep // 60:02d}:{dep % 60:02d} departure "
              f"({w / ref:.2f}x the analyst)")


if __name__ == "__main__":
    main()
