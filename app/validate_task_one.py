#!/usr/bin/env python3
"""
Avia Solutions - task-one validation on the real stores.
==============================================================================
One command, no placeholders. Run from the app dir on the machine that holds the
stores (defaults C:\\Avia\\oag.duckdb and C:\\Avia\\sabre.duckdb):

    py -3.12 validate_task_one.py
    py -3.12 validate_task_one.py --week 2025-05-26          # force a week
    py -3.12 validate_task_one.py --oag D:\\oag.duckdb --sabre D:\\sabre.duckdb

It does the three checks that turn task one from "proven logic" into "real numbers":
  1. builds the OAG served index for a chosen week and shows the size proxy for the
     Genoa airports against the hand-set size_pull_m (GOA ~1.2, MXP ~28.5, ...);
  2. computes the real OAG-QSI capture for Genoa-New York (expected near 0.30);
  3. runs the whole general path with every input OAG/Sabre-derived (no hand guesses)
     and prints it beside the canonical case (natural 138,608, directional 47,913,
     margin ~4%).
Paste the output back.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

HAND_SET_SIZE = {"GOA": 1.2, "MXP": 28.5, "LIN": 9.3, "BGY": 17.0, "TRN": 4.5, "BLQ": 9.9}
GENOA_CATCHMENT = ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"]
NYC = ["JFK", "EWR", "LGA"]


def pick_week(weeks, prefer_month="05"):
    """Choose a summer (late-May) week if present, else the latest available."""
    may = [w for w in weeks if len(w) >= 7 and w[5:7] == prefer_month]
    return sorted(may)[-1] if may else sorted(weeks)[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--week", default=None, help="OAG week string; default = a summer week")
    ap.add_argument("--sabre-year", type=int, default=2024,
                    help="Sabre travel year for propensity (2025 is a partial/best-estimate ingest)")
    ap.add_argument("--drive-cache", default=os.path.join(HERE, "genoa_drive.json"))
    ap.add_argument("--fuel", type=float, default=0.90, help="planning jet fuel $/kg")
    a = ap.parse_args()

    import oag_served as OAS
    import qsi_capture as QC
    import route_engine as RE

    if not os.path.exists(a.oag):
        print(f"OAG store not found: {a.oag}  (pass --oag)"); return
    weeks = OAS.list_weeks(a.oag)
    week = a.week or pick_week(weeks)
    print(f"OAG store: {a.oag}")
    print(f"weeks held ({len(weeks)}): {weeks}")
    print(f"using week: {week}\n")

    # 1. served index + size proxy sanity-check
    idx = OAS.build_served_index(a.oag, week)
    served_path = os.path.join(HERE, f"served_{week}.json")
    OAS.save_index(idx, served_path)
    print(f"[1] served index: {len(idx['airports'])} airports with service; saved {served_path}")
    print(f"    {'apt':4} {'OAG size_m':>11} {'hand-set':>9}  freq  dests")
    for c in GENOA_CATCHMENT:
        a_ = idx["airports"].get(c)
        if a_:
            print(f"    {c:4} {a_['size_m']:>11.2f} {HAND_SET_SIZE[c]:>9.1f}  "
                  f"{a_['dep_freq']:>5.0f}  {a_['dest_count']}")
        else:
            print(f"    {c:4} {'(not served / below freq cut)':>30}")
    print("    -> if OAG size_m tracks the hand-set column, the seats->size scaling holds;")
    print("       if off by a roughly constant factor, tune LOAD_PROXY in oag_served.py.\n")

    # 2. real OAG-QSI capture for Genoa-New York
    try:
        qc = QC.qsi_capture_default(a.oag, week, "GOA", NYC, GENOA_CATCHMENT,
                                    proposed_freq=7, proposed_block_min=540)
        d = qc["detail"]
        print(f"[2] OAG-QSI capture GOA-New York: {qc['capture']:.3f}  (hand-set case value 0.30)")
        print(f"    itineraries scored: {qc['n_itineraries']} "
              f"(nonstops {d['nonstops']}, connections {d['connections']}, hubs {d['hubs']})")
        for s in qc["itineraries"][:6]:
            print(f"      {s['label'][:42]:42} freq {s['frequency']:>5}  qsi {s.get('qsi',0):.2f}")
    except Exception as e:
        print(f"[2] OAG-QSI capture failed: {e}")
    print()

    # 3. whole general path, every input derived
    sabre = a.sabre if os.path.exists(a.sabre) else None
    r = RE.assess("Genoa", "New York", served_index=served_path, sabre_db=sabre,
                  qsi_db=a.oag, qsi_week=week, year=a.sabre_year,
                  drive_cache=(a.drive_cache if os.path.exists(a.drive_cache) else None),
                  econ_fare=345, bus_fare=1400.0, econ_share=0.80, freq=7, fuel_price=a.fuel)
    print("[3] general path (sabre/oag-derived inputs), vs canonical case:")
    print(f"    competing airports : {r['competing_airports']}")
    print(f"    natural            : {r['natural_catchment_demand']:>12,.0f}   (case 138,608)")
    print(f"    directional        : {r['directional_demand']:>12,.0f}   (case 47,913)")
    print(f"    propensity         : {r['propensity']:.4f} ({r['propensity_basis']}, "
          f"year {r.get('propensity_year')}); gravity x-check {r['propensity_crosscheck']}  "
          f"(case 0.0424)")
    print(f"    capture            : {r['capture']:.3f} ({r['capture_basis']})")
    e = r.get("economics", {})
    if r.get("economics_ok"):
        print(f"    margin / annual    : {e['margin']*100:.1f}%  ${e['annual_profit']:,.0f}  "
              f"(case 4.0%  $2.02m)")
    else:
        print(f"    economics error    : {r.get('economics_error')}")
    print("\nDone. Paste this output back.")


if __name__ == "__main__":
    main()
