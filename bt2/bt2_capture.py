#!/usr/bin/env python3
"""Avia Solutions - BT2 Stage 4: QSI capture vs the contemporaneous pre-launch month.
Per pair: rebuilds a representative week (schedule rows covering the 15th-21st of the
pre-launch month), runs the QSI connection builder, stores capture at freq=5 (old
basis) and at ACTUAL launch frequency, plus connection-quality components by type
(ONLINE/ALLIANCE/INTERLINE sums) so weights can be re-tuned without recompute.
Resumable: appends to capture_L.csv, exits cleanly near the 45s cap. Re-run until done.
"""
import argparse, csv, math, os, statistics, sys, time
from collections import defaultdict
import duckdb

# PATHS. Rewritten 8 August 2026 and now shared, see bt2_paths.py. These were three hardcoded
# Cowork session mounts (/sessions/wizardly-peaceful-tesla/...) that resolve on neither machine,
# so this stage could not run anywhere. It matters more than most: it produces the QSI capture
# feature BT2's model uses, and that model produces the published 89% and 82% claims.
from bt2_paths import BT2, OAG, find_app, mct_master, require
APP = find_app()                      # loud: BT2 imports the QSI connection builder
require(OAG=OAG, APP=APP)
# The 33 second budget was set by the 45 second call cap of the Cowork session that wrote this
# stage. It is not a property of the work, and on a machine with no such cap it means the stage
# reloads the airport coordinates and the MCT master once for every 33 seconds of useful capture.
# Made settable on 9 August 2026, default unchanged so nothing that relied on it moves.
T0, BUDGET = time.time(), float(os.environ.get("AVIA_BT2_BUDGET", "33"))

sys.path.insert(0, APP)
import connection_builder as CB
import schedule_chain as SC

# ONE IMPLEMENTATION, NOT TWO. _et, load_legs, components and cap_from moved to
# app/bt2_capture_core.py on 12 August 2026 so the training chain and the live path build capa, qcx
# and legs_n with the same code. They did not until then and nobody had compared them: route_context
# set capa to the engine's qsi_share, a different quantity on a different scale, which would have fed
# every live route into the model below the tenth percentile of training in silence. The measurement
# is in that file. sys.path already carries APP, three lines above.
from bt2_capture_core import (elapsed_penalty as _et, load_legs, components, cap_from,   # noqa: F401
                              capa_from_components, qcx_feature_from_components)         # noqa: F401

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cohort", type=int, required=True)
    L = ap.parse_args().cohort
    prof = list(csv.DictReader(open(f"{BT2}/launch_profile_{L}.csv")))
    outp = f"{BT2}/capture_{L}.csv"
    done = set()
    if os.path.exists(outp):
        done = {(r["a"], r["b"]) for r in csv.DictReader(open(outp))}
    todo = [r for r in prof if (r["a"], r["b"]) not in done]
    if not todo:
        print(f"cohort {L}: COMPLETE ({len(done)}/{len(prof)})"); return
    coords = SC.load_airport_coords()
    mct = {}
    try:
        from config import MCT_MASTER
        mct = CB.load_mct_data(str(MCT_MASTER), 90)
    except Exception:
        try:
            mct = CB.load_mct_data(str(mct_master() or ""), 90)
        except Exception:
            mct = {}
    con = duckdb.connect(OAG, read_only=True)
    con.execute("SET memory_limit='2GB'"); con.execute("SET threads=4")
    by_pm = defaultdict(list)
    for r in todo: by_pm[r["pre_month"]].append(r)
    fields = ["a","b","pre_month","legs_n","so_ab","sa_ab","si_ab","mn_ab","so_ba","sa_ba","si_ba","mn_ba","block","cap_f5","cap_actual"]
    newf = not os.path.exists(outp)
    fh = open(outp, "a", newline=""); w = csv.writer(fh)
    if newf: w.writerow(fields)
    ndone = 0
    for pm in sorted(by_pm):
        for r in by_pm[pm]:
            if time.time() - T0 > BUDGET:
                fh.close(); print(f"cohort {L}: paused, {len(done)+ndone}/{len(prof)} done"); return
            a, b = r["a"], r["b"]
            legs = load_legs(con, pm, {a, b})
            if not legs:
                w.writerow([a, b, pm, 0] + [""]*11); ndone += 1; continue
            alliances = SC.alliances_from_legs(legs) or CB.load_alliance_data()
            lcc = SC.lcc_from_legs(legs) or CB.DEFAULT_LCC_LIST
            d = float(r["gcd_km"] or 0) or 1000.0
            block = int(d / 13.5) + 30
            comp = components(legs, a, b, alliances, mct, lcc, coords, block)
            (so1, sa1, si1, mn1), (so2, sa2, si2, mn2) = comp
            f_act = max(1.0, float(r["wk_freq_dir"] or 1))
            c5 = statistics.mean([cap_from(so1, sa1, si1, mn1, block, 5),
                                  cap_from(so2, sa2, si2, mn2, block, 5)])
            ca = statistics.mean([cap_from(so1, sa1, si1, mn1, block, f_act),
                                  cap_from(so2, sa2, si2, mn2, block, f_act)])
            w.writerow([a, b, pm, len(legs), round(so1,3), round(sa1,3), round(si1,3), mn1,
                        round(so2,3), round(sa2,3), round(si2,3), mn2, block,
                        round(c5,5), round(ca,5)])
            ndone += 1
    fh.close(); print(f"cohort {L}: COMPLETE ({len(done)+ndone}/{len(prof)})")

if __name__ == "__main__":
    main()
