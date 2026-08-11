#!/usr/bin/env python3
"""Avia Solutions - STEP 3 diagnostic: what actually sets the connecting level, 11 August 2026.

route_forecast lines 771 to 793 re-split the CARRIED total between point to point and connecting using
an airport connectivity table, and floor the connecting side at what that table implies. The feed
detail is then rescaled to the re-split total. If that floor binds, the capture rate the feed layer
computes does not set the connecting level at all: it only sets the shape across markets, and the
level comes from the connectivity table.

This measures whether the floor binds on SJC-TPE, under the flat rate and under the QSI feed, and by
how much the feed detail is rescaled in each case.
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
import split_share as SS                         # noqa: E402

ORIGIN, DEST, AIRLINE = "SJC", "TPE", "CI"
DEP_TIME_MINS, FLYING_MINS, FREQ, SEATS = 11 * 60, 825, 4, 306

BASE_CFG = {"behind_cap": 0.10, "dom_gain": 1.0, "dom_floor": 1.0,
            "cnx_online": 1.0, "cnx_alliance": 0.615, "cnx_interline": 0.25,
            "circuity": 1.35, "factor_indirect": 1.044, "mct_banking": False}


def main():
    c = duckdb.connect(os.environ["AVIA_OAG"], read_only=True)
    week = c.execute("SELECT max(week) FROM oag").fetchone()[0]
    c.close()
    c = duckdb.connect(os.environ["AVIA_SABRE"], read_only=True)
    year = c.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
    c.close()

    print(f"split_share.available(): {SS.available()}")
    sh = SS.p2p_share(ORIGIN, DEST)
    print(f"split_share.p2p_share({ORIGIN}, {DEST}): {sh}")

    sabre, oag = os.environ["AVIA_SABRE"], os.environ["AVIA_OAG"]
    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]

    # captured (the P2P leg) is the same in every arm: it does not depend on the feed configuration.
    # Taken from the engine's own baseline payload rather than recomputed.
    import cortex_app as CA
    r = CA.calibrated_forecast(ORIGIN, DEST, airline=AIRLINE, carrier_type="FSC",
                               aircraft="A359", seats=SEATS, freq=FREQ)
    captured = r["demand"]["captured"]
    annual_capacity = SEATS * FREQ * 52.0
    max_plan_lf = 0.875
    print(f"\ncaptured (P2P, each way) {captured:,.0f}; annual capacity each way {annual_capacity:,.0f}; "
          f"seat ceiling {annual_capacity * max_plan_lf:,.0f}\n")

    for label, extra in (("flat rate", {}),
                         ("QSI feed, k = 1.0",
                          {"qsi_feed": True, "dep_time_mins": DEP_TIME_MINS, "flying_mins": FLYING_MINS,
                           "route_freq": FREQ, "qsi_k": 1.0, "qsi_k_behind": 1.0})):
        cfg = dict(BASE_CFG, **extra)
        bt, _, _ = RFEED.feed_side(sabre, oag, week, competing, DEST, year, beyond=True,
                                   airline=AIRLINE, feed_cfg=dict(cfg), detail=True)
        ht, _, _ = RFEED.behind_feed(sabre, oag, week, [ORIGIN], [DEST], year,
                                     airline=AIRLINE, feed_cfg=dict(cfg), detail=True)
        feed = bt + ht
        total_demand = captured + feed
        carried = min(total_demand, annual_capacity * max_plan_lf)
        engine_conn = carried * (feed / max(total_demand, 1.0))
        resplit_conn = carried * (1.0 - sh)
        conn = max(engine_conn, resplit_conn)
        print(f"{label}")
        print(f"  feed the layer computes, each way   {feed:>10,.0f}")
        print(f"  total demand                        {total_demand:>10,.0f}")
        print(f"  carried after the seat ceiling      {carried:>10,.0f}")
        print(f"  connecting the ENGINE implies       {engine_conn:>10,.0f}")
        print(f"  connecting the CONNECTIVITY TABLE implies {resplit_conn:>10,.0f}")
        print(f"  connecting reported                 {conn:>10,.0f}"
              f"   <- {'CONNECTIVITY TABLE binds' if resplit_conn > engine_conn else 'engine binds'}")
        print(f"  feed detail rescaled by             {conn / max(feed, 1.0):>10,.4f}\n")


if __name__ == "__main__":
    main()
