#!/usr/bin/env python3
"""Avia Solutions - why the QSI feed reads the two sides differently, 11 August 2026.

One scoring method reads the beyond side to within 13% of the 2025 analyst and the behind side 3.3
times light, and eleven beyond markets return exactly zero. Both point at the itinerary sets rather
than at the scorer, so this dumps them: for every market, how many itineraries the new route got, how
many the competition got, and the resulting share.

A share of zero has two quite different causes and they need separating. Either the new route has no
legal connection into that market, in which case zero is right, or nothing at all was enumerated, in
which case the market's whole connecting demand is being dropped in silence. `_share` returns 0.0 for
both.

The behind side is called with the same inputs route_feed passes it, including the route_flying_mins
key route_feed sets from flying_mins.
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
DEP_TIME_MINS, FLYING_MINS, FREQ = 11 * 60, 825, 4

# The analyst's behind rates for the four markets his workbook reconciles to, from the working note
# of 11 August 2026 section 2. Printed alongside Meridian's so the comparison is on the page.
ANALYST_BEHIND = {"LAX": 0.03049}


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
    cfg = {"circuity": 1.35, "factor_indirect": 1.044, "route_origin": ORIGIN}

    # BEYOND. Same scope route_feed builds, and the same market keys it hands to qsi_feed.
    scope = [x for x in RFEED.hub_served(oag, week, DEST) if x not in competing]
    scope = RFEED.on_the_way(competing, DEST, scope, circuity=1.35)
    market = RFEED.connecting_market(sabre, competing, scope, year, 1.044)
    shares, dmap = QF.beyond_capture(boards, week, competing, DEST, list(market.keys()), AIRLINE,
                                     DEP_TIME_MINS, FLYING_MINS, FREQ, mct=mct, cfg=cfg, detail=True)
    print(f"OAG week {week}, Sabre year {year}, catchment {len(competing)} airports\n")
    print(f"BEYOND {DEST}: {len(market)} markets")
    print(f"  {'mkt':5} {'base pax':>10} {'share':>8} {'new':>4} {'comp':>5} {'best new':>9} {'best comp':>10}")
    zero_no_new, zero_nothing = [], []
    for m in sorted(market, key=lambda x: -market[x]):
        d = dmap[m]
        if d["share"] == 0.0:
            (zero_nothing if (d["n_new"] == 0 and d["n_comp"] == 0) else zero_no_new).append(m)
        print(f"  {m:5} {market[m]:>10,.0f} {d['share']:>8.5f} {d['n_new']:>4} {d['n_comp']:>5} "
              f"{str(d['best_new']):>9} {str(d['best_comp']):>10}")
    print(f"\n  zero because the new route has NO LEGAL CONNECTION (competition exists): "
          f"{len(zero_no_new)} {sorted(zero_no_new)}")
    print(f"  zero because NOTHING WAS ENUMERATED AT ALL (market demand dropped in silence): "
          f"{len(zero_nothing)} {sorted(zero_nothing)}")
    print(f"  demand on the silently-dropped markets: "
          f"{sum(market[m] for m in zero_nothing):,.0f} each way\n")

    # BEHIND. route_feed uses the specific route origin, not the catchment, and sets
    # route_flying_mins from flying_mins before calling.
    feeders = [y for y in RFEED.feeders_to(oag, week, [ORIGIN])
               if y not in (ORIGIN, DEST)]
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
    bmarket = RFEED.behind_market(sabre, kept, [DEST], year, 1.044)
    cfgb = dict(cfg, route_flying_mins=FLYING_MINS, route_freq=FREQ)
    bshares, bdmap = QF.behind_capture(boards, week, [ORIGIN], [DEST], list(bmarket.keys()),
                                       AIRLINE, DEP_TIME_MINS, mct=mct, cfg=cfgb, detail=True)
    print(f"BEHIND {ORIGIN}: {len(bmarket)} feeders")
    print(f"  {'fdr':5} {'base pax':>10} {'share':>8} {'new':>4} {'comp':>5}   analyst")
    for y in sorted(bmarket, key=lambda x: -bmarket[x]):
        d = bdmap[y]
        an = ANALYST_BEHIND.get(y)
        print(f"  {y:5} {bmarket[y]:>10,.0f} {d['share']:>8.5f} {d['n_new']:>4} {d['n_comp']:>5}"
              f"{('   ' + format(an, '.5f')) if an else ''}")
    tot = sum(bmarket.values())
    wsh = sum(bmarket[y] * bshares.get(y, 0.0) for y in bmarket) / tot if tot else 0.0
    print(f"\n  demand-weighted behind share: {wsh:.5f}")
    print(f"  feeders where the new route got NO itinerary: "
          f"{sorted(y for y in bmarket if bdmap[y]['n_new'] == 0)}")


if __name__ == "__main__":
    main()
