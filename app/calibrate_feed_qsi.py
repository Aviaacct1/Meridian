#!/usr/bin/env python3
"""
Avia Solutions - connecting-QSI calibration against the proven method.
==============================================================================
The connecting-feed combiner is structurally correct (per-city demand x QSI capture,
summed), but the live run_multihub_qsi produces capture shares ~15x the proven
method's (China Airlines TPE-SJC deck: overall 1.5% connecting at the hub, individual
cities 0.1-17%). This harness runs the engine for that exact service and lays its
per-city capture next to the deck's, so we can see whether the over-credit is a uniform
scale (one fix) or structural per-city (competition set incomplete), and tune from there.

Reads ci_tpe_sjc_connecting_fixture.json (the deck's per-city table) and runs
run_multihub_qsi for CI TPE-SJC, 4x weekly, on the OAG store. Needs oag.duckdb.

RUN:
  py -3.12 calibrate_feed_qsi.py --oag-db "C:\\Avia\\oag.duckdb" --week 2025-05-26
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description="Calibrate connecting QSI vs the China Airlines deck.")
    ap.add_argument("--oag-db", required=True, help="oag.duckdb")
    ap.add_argument("--week", required=True, help="OAG week string, e.g. 2025-05-26")
    ap.add_argument("--fixture", default=os.path.join(HERE, "ci_tpe_sjc_connecting_fixture.json"))
    ap.add_argument("--flymin", type=int, default=825, help="SJC-TPE flying minutes (default 825)")
    ap.add_argument("--circuity", type=float, default=1.25)
    ap.add_argument("--explain", default=None,
                    help="comma list of market codes to dump every competing routing for, "
                         "e.g. SGN,NKG (an over-credited and an under-credited market)")
    ap.add_argument("--nonstops", action="store_true",
                    help="CANDIDATE improvement (off by default): add direct/nonstop competition to the denominator")
    a = ap.parse_args()
    explain_markets = [x.strip().upper() for x in a.explain.split(",")] if a.explain else None
    if not os.path.exists(a.oag_db):
        sys.exit(f"oag store not found: {a.oag_db}")

    fx = json.load(open(a.fixture))
    svc = fx["service"]
    deck = {c["code"]: c for c in fx["connecting_at_hub"]["cities"]}

    import run_multihub_qsi as MQ
    flymin = svc.get("fly_min", a.flymin)   # per-fixture sector time; --flymin overrides only if absent
    spec = f"{svc['carrier']},{svc['hub']},{svc['home']},1300,0800,{flymin}"
    prop = MQ._proposed_leg(spec)
    res = MQ.run(None, [x.strip() for x in svc["catchment"].split(",")], proposed=prop,
                 circuity_cut=a.circuity, db=a.oag_db, week=a.week, qsi2=True,
                 explain_markets=explain_markets, include_nonstops=a.nonstops)
    print(f"(nonstop competition in QSI denominator: {'ON' if a.nonstops else 'OFF'})\n")
    eng = {r["market"]: r["proposed_capture"] for r in res["rows"]}

    if res.get("explain"):
        print("Per-market routing dump (why the proposed hub wins its share):\n")
        print(f"{'mkt':>5} {'hub':>5} {'carriers':>10} {'freq':>5} {'elapsed':>8} {'excess':>7} "
              f"{'cnxtype':>9} {'qsi':>8} {'share':>7} {'prop':>5}")
        print("-" * 78)
        for r in res["explain"]:
            print(f"{r['market']:>5} {str(r['hub']):>5} {r['carriers']:>10} {r['freq']:>5.0f} "
                  f"{r['elapsed_min']:>8.0f} {r['excess_min']:>7.0f} {r['cnx_type']:>9} "
                  f"{r['qsi']:>8.3f} {r['share']:>7.1%} {('YES' if r['proposed'] else ''):>5}")
        print("-" * 78 + "\n")

    print(f"CI TPE-SJC connecting-at-hub: engine capture vs proven deck capture\n")
    print(f"{'city':>6} {'demand':>10} {'deck %':>8} {'engine %':>9} {'ratio':>7}")
    print("-" * 46)
    wsum_deck = wsum_eng = dsum = 0.0
    for code, c in deck.items():
        e = eng.get(code)
        d = c["capture"]
        dem = c["demand"]
        e_str = f"{e:>8.1%}" if e is not None else f"{'-':>8}"
        ratio = f"{(e/d):>6.1f}x" if (e is not None and d > 0) else f"{'-':>7}"
        print(f"{code:>6} {dem:>10,} {d:>8.1%} {e_str} {ratio}")
        if e is not None:
            wsum_deck += d * dem
            wsum_eng += e * dem
            dsum += dem
    print("-" * 46)
    if dsum:
        dk = wsum_deck / dsum
        en = wsum_eng / dsum
        print(f"demand-weighted capture  deck {dk:.2%}  engine {en:.2%}  "
              f"engine over-credit {en/dk:.1f}x" if dk else "")
        print(f"matched cities: {sum(1 for c in deck if c in eng)} of {len(deck)} "
              f"(unmatched = engine saw no routing for that market over TPE)")
    print("\nRead: a roughly constant ratio across cities = a single scale fix (the QSI "
          "normalisation or a missing constant). A ratio that swings city to city = the "
          "competition set is incomplete (missing nonstops / hubs), so the proposed service "
          "wins too much where the engine can't see the real alternatives.")


if __name__ == "__main__":
    main()
