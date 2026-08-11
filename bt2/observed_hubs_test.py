#!/usr/bin/env python3
"""Avia Solutions - are we competing against hubs nobody actually connects over? 11 August 2026.

THE HYPOTHESIS. qsi_feed builds its competitor set from OAG alone: any airport the catchment can
reach with at least three weekly frequency, that also flies to the market, and that passes a 1.35
circuity screen. Its own docstring names the shortcut:

    "Sabre would narrow this to hubs observed carrying the market; OAG-side the serves-the-market
     test below does the same job without a second store dependency."

It does not do the same job. "Can be routed" and "is routed" are different sets. A hub that is
physically capable of carrying San Jose to Cebu but carries none of it still adds QSI points to the
denominator, and every point in the denominator dilutes the new route's share. The 2025 analyst
enumerated transit points from a Sabre extract, so his competitor set is the observed one.

Sabre carries connecting_airport1 on every connecting itinerary, so the observed set is measurable
rather than assumed. This counts, per beyond market: how many hubs Meridian competes against, how
many are actually observed carrying that market, and what share of the real connecting traffic the
observed set represents.

If Meridian is competing against a large tail of hubs carrying no traffic, that is a defect with a
data answer, and it pushes the beyond share down exactly where the analyst says it should not be.
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
FLYING_MINS, FREQ, DEP = 825, 4, 12 * 60


def main():
    oag, sabre = os.environ["AVIA_OAG"], os.environ["AVIA_SABRE"]
    week = duckdb.connect(oag, read_only=True).execute("SELECT max(week) FROM oag").fetchone()[0]
    con = duckdb.connect(sabre, read_only=True)
    con.execute("SET memory_limit='2GB'; SET temp_directory='/tmp/duck'; SET threads=2;")
    year = con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]

    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]
    scope = [x for x in RFEED.hub_served(oag, week, DEST) if x not in competing]
    scope = RFEED.on_the_way(competing, DEST, scope, circuity=1.35)
    b_mkt = RFEED.connecting_market(sabre, competing, scope, year, 1.044)

    # OBSERVED: which connect points Sabre actually records carrying this catchment to each market.
    oa = ",".join("?" * len(competing))
    ba = ",".join("?" * len(list(b_mkt.keys())))
    rows = con.execute(
        f"SELECT destination_airport, connecting_airport1, SUM(passengers) FROM sabre "
        f"WHERE source_year=? AND origin_airport IN ({oa}) AND destination_airport IN ({ba}) "
        f"AND connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL GROUP BY 1,2",
        [year] + competing + list(b_mkt.keys())).fetchall()
    con.close()
    observed = {}
    for m, h, pax in rows:
        observed.setdefault(m, {})[h] = float(pax or 0)

    # MODELLED: the competitor hubs qsi_feed actually enumerates for each market.
    boards, mct = OagBoards(oag), MB.load_mct()
    cfg = {"circuity": 1.35, "route_origin": ORIGIN,
           "route_flying_mins": FLYING_MINS, "route_freq": FREQ}
    origin_boards = QF._dep_boards(boards, week, competing)
    cand = QF._candidate_hubs(origin_boards, exclude={ORIGIN}, min_hub_freq=3.0)
    modelled = {}
    for m in b_mkt:
        hs = set()
        for h in cand:
            if h == m:
                continue
            by_arr, _ = QF._grouped_dep_board(boards, week, h)
            if by_arr.get(m) and QF._circuity_ok(ORIGIN, h, m, 1.35):
                hs.add(h)
        modelled[m] = hs

    print(f"OAG week {week}, Sabre year {year}. Beyond {DEST}, {len(b_mkt)} markets.\n")
    print(f"  {'mkt':5} {'base pax':>9} {'modelled':>9} {'observed':>9} {'both':>6} "
          f"{'traffic on modelled hubs':>25}")
    tot_m = tot_o = tot_b = 0
    cover = []
    for m in sorted(b_mkt, key=lambda x: -b_mkt[x])[:18]:
        mo, ob = modelled.get(m, set()), set(observed.get(m, {}))
        both = mo & ob
        obs_pax = sum(observed.get(m, {}).values()) or 1.0
        on_mod = sum(v for h, v in observed.get(m, {}).items() if h in mo) / obs_pax
        cover.append(on_mod)
        tot_m += len(mo); tot_o += len(ob); tot_b += len(both)
        print(f"  {m:5} {b_mkt[m]:>9,.0f} {len(mo):>9} {len(ob):>9} {len(both):>6} "
              f"{on_mod:>24.1%}")
    allm = sum(len(modelled.get(m, set())) for m in b_mkt)
    allo = sum(len(observed.get(m, {})) for m in b_mkt)
    print(f"\n  across all {len(b_mkt)} markets: {allm:,} modelled competitor hubs, "
          f"{allo:,} observed carrying traffic")
    print(f"  modelled hubs per market {allm / max(len(b_mkt), 1):.1f}, "
          f"observed {allo / max(len(b_mkt), 1):.1f}")
    if cover:
        print(f"  share of real connecting traffic on hubs Meridian models "
              f"(top 18 markets): {sum(cover) / len(cover):.1%}")


if __name__ == "__main__":
    main()
