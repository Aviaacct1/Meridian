#!/usr/bin/env python3
"""Avia Solutions - STEP 3, the feed layer measured on its own, 11 August 2026.

The payload figures for the beyond and behind feed do not scale with k, and P2P moves when only the
feed configuration changes. Both are impossible if the feed is what route_feed returns, so the
payload numbers are being reworked downstream and cannot be used to measure the feed itself.

This calls route_feed.feed_side and route_feed.behind_feed directly, with the catchment, scope, week
and year the engine builds, and prints the RAW totals and the per-market capture rates before
anything downstream touches them.
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

ORIGIN, DEST, AIRLINE = "SJC", "TPE", "CI"
DEP_TIME_MINS, FLYING_MINS, FREQ = 11 * 60, 825, 4

BASE_CFG = {"behind_cap": 0.10, "dom_gain": 1.0, "dom_floor": 1.0,
            "cnx_online": 1.0, "cnx_alliance": 0.615, "cnx_interline": 0.25,
            "circuity": 1.35, "factor_indirect": 1.044, "mct_banking": False}


def ctx():
    c = duckdb.connect(os.environ["AVIA_OAG"], read_only=True)
    week = c.execute("SELECT max(week) FROM oag").fetchone()[0]
    c.close()
    c = duckdb.connect(os.environ["AVIA_SABRE"], read_only=True)
    year = c.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
    c.close()
    return week, year


def report(label, cfg, week, year, competing):
    sabre, oag = os.environ["AVIA_SABRE"], os.environ["AVIA_OAG"]
    cfg = dict(cfg)
    bt, _, bdet = RFEED.feed_side(sabre, oag, week, competing, DEST, year, beyond=True,
                                  airline=AIRLINE, feed_cfg=cfg, detail=True)
    ht, _, hdet = RFEED.behind_feed(sabre, oag, week, [ORIGIN], [DEST], year,
                                    airline=AIRLINE, feed_cfg=cfg, detail=True)
    bshare = sorted({round(v["share"], 6) for v in bdet.values()})
    hshare = sorted({round(v["share"], 6) for v in hdet.values()})
    zeros = [c for c, v in bdet.items() if (v["share"] or 0) == 0]
    print(f"{label}")
    print(f"  beyond raw total each way {bt:>12,.0f}   two-way {2*bt:>12,.0f}   markets {len(bdet)}")
    print(f"  behind raw total each way {ht:>12,.0f}   two-way {2*ht:>12,.0f}   markets {len(hdet)}")
    print(f"  beyond distinct rates ({len(bshare)}): {bshare[:8]}{' ...' if len(bshare) > 8 else ''}")
    print(f"  behind distinct rates ({len(hshare)}): {hshare[:8]}{' ...' if len(hshare) > 8 else ''}")
    print(f"  beyond markets at exactly zero: {len(zeros)} {sorted(zeros)[:12]}")
    print(f"  fallbacks to the flat path: {cfg.get('_qsi_fallbacks', 0)}")
    return bt, ht, bdet


def main():
    week, year = ctx()
    ap = RE._airports()
    competing = [r["iata"] for r in RE.competing_airports(ap[ORIGIN], 220.0, None, True)]
    print(f"OAG week {week}, Sabre year {year}, catchment {len(competing)} airports\n")

    report("BASELINE, flat rate", BASE_CFG, week, year, competing)
    print()
    for k in (1.0, 0.06):
        cfg = dict(BASE_CFG, qsi_feed=True, dep_time_mins=DEP_TIME_MINS,
                   flying_mins=FLYING_MINS, route_freq=FREQ, qsi_k=k, qsi_k_behind=k)
        report(f"QSI FEED, k = {k}", cfg, week, year, competing)
        print()


if __name__ == "__main__":
    main()
