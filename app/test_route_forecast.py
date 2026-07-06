#!/usr/bin/env python3
"""
Avia Solutions - sanity driver for the rebuilt connected-loop forecast (route_forecast.py).
============================================================================================
Runs the new measured-demand -> QSI capture -> capacity-bound loop on two routes so we can see
it produce sane numbers before rewiring the full back-test:
  - Genoa-New York (the calibrated anchor; expect ~50-65k carried on a daily A321XLR)
  - Sacramento-New York (read 983,000 under the old blended model; expect a sane, capacity-bound
    number now that demand is the measured Sacramento market by true origin, not population x a
    San-Francisco-blended rate)

RUN on the machine with both stores:
    py -3.12 test_route_forecast.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
Pick --week from oag_served.list_weeks; --year is the Sabre base year.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import route_forecast as RF


CASES = [
    {"name": "Genoa - New York", "origin": "GOA", "dest": ["JFK", "EWR", "LGA"],
     "competing": ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"],
     "aircraft": "A21X", "freq": 7, "block_min": 540},
    {"name": "Sacramento - New York", "origin": "SMF", "dest": ["JFK", "EWR", "LGA"],
     "competing": ["SMF", "SFO", "OAK", "SJC"],
     "aircraft": "A21X", "freq": 7, "block_min": 330},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--week", default=None, help="OAG week; default = the latest summer week")
    ap.add_argument("--year", type=int, default=None, help="Sabre base year; default = latest")
    ap.add_argument("--stim", type=float, default=1.15)
    a = ap.parse_args()

    if not os.path.exists(a.sabre) or not os.path.exists(a.oag):
        print("need both stores; pass --oag and --sabre"); return
    import oag_served as OAS
    weeks = OAS.list_weeks(a.oag)
    week = a.week or ([w for w in sorted(weeks) if w[5:7] == "05"] or sorted(weeks))[-1]
    import duckdb
    con = duckdb.connect(a.sabre, read_only=True)
    year = a.year or con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
    con.close()
    print(f"OAG week {week}; Sabre year {year}; stimulation {a.stim}\n")

    for c in CASES:
        try:
            r = RF.forecast(a.sabre, a.oag, week, c["origin"], c["dest"], c["competing"],
                            year=year, aircraft=c["aircraft"], freq=c["freq"],
                            block_min=c["block_min"], stimulation=a.stim)
            print(f"=== {c['name']} ({c['origin']}->{'/'.join(c['dest'])}) ===")
            print(f"  measured wide market  : {r['natural_market']:,}  (whole service area -> dest, Sabre, avg fare ${r['avg_fare']:,.0f})")
            print(f"  already via origin    : {r['current_via_origin']:,}")
            print(f"  QSI capture share     : {r['qsi_share']:.1%}  (origin's schedule quality vs the field)")
            print(f"  captured demand       : {r['captured_demand']:,}  (market x QSI share x stim {r['stimulation']})")
            print(f"  aircraft / capacity   : {r['aircraft']} {r['frequency']}x/wk = {r['annual_capacity']:,}/yr")
            print(f"  CARRIED forecast      : {r['carried_forecast']:,}  @ {r['planned_load_factor']:.0%} load")
            print(f"  spill                 : {r['spill']:,}")
            print(f"  recommendation        : {r['recommendation']}\n")
        except Exception as e:
            import traceback
            print(f"=== {c['name']}: ERROR {e}"); traceback.print_exc(); print()


if __name__ == "__main__":
    main()
