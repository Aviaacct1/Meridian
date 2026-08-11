#!/usr/bin/env python3
"""Avia Solutions - the four connecting options measured, 11 August 2026.

Two changes are on the table and they are separate. The first is the CAPTURE METHOD: the flat rate
Meridian applies today, against the per-market QSI share at k = 1.0, which is the 2025 analyst's
method with no re-levelling constant. The second is the SPLIT FLOOR: route_forecast re-splits the
carried total using the airport connectivity table and floors connecting at what that table implies,
which on SJC-TPE overrides whatever the capture rate produced.

Testing them together would tell us nothing about which one moved the answer, so they are crossed:

    A  flat rate, floor on     the engine as it ships today
    B  QSI feed, floor on      the capture method changed, the floor left alone
    C  QSI feed, floor off     the capture method changed and the floor retired
    D  flat rate, floor off    the control that isolates what the floor alone contributes

Each arm runs at two catchments and two data vintages. The catchment matters because Meridian's
220 km radius takes in San Francisco, Oakland and Sacramento while the 2025 analyst allocated to San
Jose's service area, so a total that agrees with his could agree for the wrong reason. The vintage
matters because the analyst worked on 2024 traffic and a 2025 schedule, and running Meridian on the
same vintage removes that difference from the comparison.

The analyst is a DIAGNOSTIC here and not a target. Agreeing with him is evidence about the
implementation; it is not evidence that the forecast is right. What ships is decided on BT2.

THE ARITHMETIC IS RECONSTRUCTED, NOT ASSUMED. route_forecast lines 705 to 793 are reproduced here so
the floor can be switched off without editing the engine. Every baseline arm prints a reconciliation
against the engine's own payload, and a mismatch is reported rather than passed over.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import duckdb                                    # noqa: E402
import cortex_app as CA                          # noqa: E402
import route_engine as RE                        # noqa: E402
import route_feed as RFEED                       # noqa: E402
import split_share as SS                         # noqa: E402
import oag_served as OAS                         # noqa: E402

ORIGIN, DEST, AIRLINE = "SJC", "TPE", "CI"
AIRCRAFT, SEATS, FREQ = "A359", 306, 4
FLYING_MINS = 825
PLAN_LF = 0.875
WEEKS = 52.0

# The analyst's figures, two-way, from Fcst_TPE-SJC_ChinaAirlines_4xw_v2.xlsm as recorded in
# "Why Meridian differs from the 2025 analyst on connecting traffic - 11Aug2026.md" section 4. His
# forecasts are YE Jun 2028 and carry 33% compound growth; the current-year equivalent divides by 1.33.
ANALYST = {"beyond_2028": 15969, "behind_2028": 18609, "growth": 1.33}
ANALYST_BEYOND = ANALYST["beyond_2028"] / ANALYST["growth"]          # 12,007
ANALYST_BEHIND = ANALYST["behind_2028"] / ANALYST["growth"]          # 13,992

VINTAGES = {"current":  {"week": "2026-05-25", "year": 2025},
            "analyst":  {"week": "2025-05-26", "year": 2024}}
CATCHMENTS = {"product 220km": 220.0, "SJC only": 1.0}


def base_cfg():
    """The feed_cfg cortex_app.calibrated_forecast builds today, at its own defaults."""
    return {"behind_cap": 0.10, "dom_gain": 1.0, "dom_floor": 1.0,
            "cnx_online": 1.0, "cnx_alliance": 0.615, "cnx_interline": 0.25,
            "circuity": 1.35, "factor_indirect": 1.044, "mct_banking": False}


def pin_vintage(week, year):
    """Force the engine onto a chosen OAG week and Sabre year instead of the latest of each."""
    sabre_db, oag_db = CA._db_paths()
    served_obj = None
    si = CA._latest_served_index()
    if si:
        try:
            served_obj = OAS.load_index(si)
        except Exception:
            served_obj = None
    codes = set()
    if served_obj:
        try:
            codes = set(OAS.served_set(served_obj))
        except Exception:
            codes = set()
    CA.S["live"] = dict(sabre_db=sabre_db, oag_db=oag_db, week=week, year=year,
                        served=served_obj, served_codes=codes)


def engine_pass(radius_km):
    """One calibrated_forecast run, for the P2P leg and the payload the reconstruction checks against."""
    return CA.calibrated_forecast(ORIGIN, DEST, airline=AIRLINE, carrier_type="FSC",
                                  aircraft=AIRCRAFT, seats=SEATS, freq=FREQ,
                                  radius_km=radius_km, plan_lf=PLAN_LF)


def raw_feed(cfg, week, year, competing, dep_time_mins):
    """The two feed sides as route_feed returns them, before anything downstream reworks them."""
    sabre, oag = os.environ["AVIA_SABRE"], os.environ["AVIA_OAG"]
    bt, _, _ = RFEED.feed_side(sabre, oag, week, competing, DEST, year, beyond=True,
                               airline=AIRLINE, feed_cfg=dict(cfg), detail=True)
    ht, _, _ = RFEED.behind_feed(sabre, oag, week, [ORIGIN], [DEST], year,
                                 airline=AIRLINE, feed_cfg=dict(cfg), detail=True)
    return bt, ht


def resolve(captured, beyond, behind, p2p_share, floor_on):
    """route_forecast lines 705 to 793, reproduced. Returns beyond and behind each way.

    The seat ceiling applies to P2P and connecting together. With the floor on, connecting is lifted
    to what the connectivity table implies and can only ever be lifted, never cut; the beyond and
    behind split keeps its shape and is rescaled to the lifted total.
    """
    feed = beyond + behind
    total_demand = captured + feed
    capacity = SEATS * FREQ * WEEKS
    carried = min(total_demand, capacity * PLAN_LF)
    engine_conn = carried * (feed / max(total_demand, 1.0))
    conn = max(engine_conn, carried * (1.0 - p2p_share)) if floor_on else engine_conn
    scale = conn / max(feed, 1.0)
    return beyond * scale, behind * scale, carried, conn, scale


def main():
    # One vintage and one catchment per process: a whole sweep in one process runs past the session
    # cap, and a run killed part way through is worse than four runs that each finish.
    only_v = sys.argv[1] if len(sys.argv) > 1 else None
    only_c = sys.argv[2] if len(sys.argv) > 2 else None
    dep_time_mins = 11 * 60                       # 11:00 local, the schedule the engine returns
    p2p_share = SS.p2p_share(ORIGIN, DEST)
    print(f"split_share.available() {SS.available()}, p2p_share({ORIGIN},{DEST}) {p2p_share:.4f}")
    print(f"analyst current-year two-way: beyond {ANALYST_BEYOND:,.0f}, behind {ANALYST_BEHIND:,.0f}\n")

    qsi = {"qsi_feed": True, "dep_time_mins": dep_time_mins, "flying_mins": FLYING_MINS,
           "route_freq": FREQ, "qsi_k": 1.0, "qsi_k_behind": 1.0}
    arms = [("A  flat, floor on ", {}, True),
            ("B  QSI,  floor on ", qsi, True),
            ("C  QSI,  floor off", qsi, False),
            ("D  flat, floor off", {}, False)]

    for vname, v in VINTAGES.items():
        if only_v and vname != only_v:
            continue
        for cname, radius in CATCHMENTS.items():
            if only_c and not cname.startswith(only_c):
                continue
            pin_vintage(v["week"], v["year"])
            r = engine_pass(radius)
            if not r.get("ok"):
                print(f"[{vname} / {cname}] FAILED: {r.get('error')}")
                continue
            d = r["demand"]
            captured = d["captured"]
            ap = RE._airports()
            competing = [x["iata"] for x in RE.competing_airports(ap[ORIGIN], radius, None, True)]
            print(f"=== vintage {vname} (OAG {v['week']}, Sabre {v['year']}) | catchment {cname}, "
                  f"{len(competing)} airports")
            print(f"    P2P demand each way {captured:,.0f}; market each way {d['natural']:,.0f}; "
                  f"qsi_share {d['qsi_share']:.4f}")

            for label, extra, floor_on in arms:
                cfg = dict(base_cfg(), **extra)
                bt, ht = raw_feed(cfg, v["week"], v["year"], competing, dep_time_mins)
                by, bh, carried, conn, scale = resolve(captured, bt, ht, p2p_share, floor_on)
                by2, bh2 = 2 * by, 2 * bh
                note = ""
                if not extra and floor_on:        # arm A is the engine as it ships: reconcile it
                    eb, eh = 2 * d["feed_beyond"], 2 * d["feed_behind"]
                    ok = abs(by2 - eb) < 2 and abs(bh2 - eh) < 2
                    note = ("  [reconciles with the engine payload]" if ok else
                            f"  [MISMATCH vs payload {eb:,.0f} / {eh:,.0f} - reconstruction unsafe]")
                print(f"    {label}  beyond {by2:>9,.0f} ({by2/ANALYST_BEYOND:>5.2f}x analyst)   "
                      f"behind {bh2:>8,.0f} ({bh2/ANALYST_BEHIND:>5.2f}x)   "
                      f"rescale {scale:>6.3f}{note}")
            print()


if __name__ == "__main__":
    main()
