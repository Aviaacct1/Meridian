#!/usr/bin/env python3
r"""Build the v1.3 production artefacts on whichever sample AVIA_BT2_DIR points at.

    AVIA_BT2_DIR=C:\Avia\bt2_relaxed python3 bt2_build_v13.py --out-app C:\AviaDev\app

Produces, all stamped with the population they were built on, because the 5 August artefacts were
not and it took a day to work out what the published figure described:

    bt2_model_v1_3.pkl          the q25/q50/q75 estimators, blind config, plus carid
    master_backtest_scored.csv  the evidence file the track record page reads
    accuracy_dist.json          the histogram the site chart draws

THE CALIBRATED CONFIG IS A CHOICE AND THE CHOICE IS RECORDED HERE, not left to whoever runs this.
A fitted figure is a statement about how hard a model was allowed to fit its own history, so it has
no meaning independent of model capacity, and capacity has no neutral definition across samples of
different size. Three defensible rules give three different answers on the same data:

    published        the 5 August config unchanged
    capacity         max_iter scaled with n so iterations x leaves per route is held constant
    memorisation     capacity raised until the share of routes reproduced within 1% matches the
                     published file's own 65.4%

--calib selects one and the choice is written into the provenance string and into the evidence
file's basis column, so no future reader has to reverse engineer it from the numbers.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import json
import math
import os
import pickle

import numpy as np

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_score import within

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
BLIND_KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)

CALIB = {
    "published":    dict(lr=0.06, it=800,  minleaf=5, l2=0.0, leaves=63),
    "capacity":     dict(lr=0.06, it=1800, minleaf=5, l2=0.0, leaves=63),
    "memorisation": dict(lr=0.08, it=1600, minleaf=3, l2=0.0, leaves=95),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", choices=sorted(CALIB), default="published")
    ap.add_argument("--out-app", default=None, help="where to write the evidence file and histogram")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rows = G.rows
    F.attach(rows)
    pop = os.path.basename(B.BT2.rstrip("/\\"))
    print("sample %s, n=%d, cohorts %s, calibration rule '%s'"
          % (pop, len(rows), ",".join(str(c) for c in B.COHORTS), a.calib))

    X, y = F.X_of(rows, G12), G.y_of(rows)
    cm = G.make(SPEC, **CALIB[a.calib])
    cm.fit(X, y)
    fc = [r["seats_ly"] * math.exp(p) for r, p in zip(rows, cm.predict(X))]
    ratios = [f / r["actual"] for f, r in zip(fc, rows)]
    w20 = 100.0 * sum(1 for x in ratios if within(x)) / len(ratios)
    w10 = 100.0 * sum(1 for x in ratios if within(x, 0.10)) / len(ratios)
    w1 = 100.0 * sum(1 for x in ratios if within(x, 0.01)) / len(ratios)
    print("  calibrated: within +-20%% %.1f%%, within +-10%% %.1f%%, within +-1%% %.1f%%"
          % (w20, w10, w1))

    blind = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        Xtr, ytr, Xte = F.X_of(tr, G12), G.y_of(tr), F.X_of(te, G12)
        q = {}
        for qq, nm in ((0.5, "p50"), (0.25, "p25"), (0.75, "p75")):
            mm = G.make(SPEC, **BLIND_KW)
            mm.set_params(quantile=qq)
            mm.fit(Xtr, ytr)
            q[nm] = mm.predict(Xte)
        for i, r in enumerate(te):
            blind[id(r)] = (r["seats_ly"] * math.exp(q["p50"][i]),
                            float(q["p75"][i] - q["p25"][i]))
    br = [blind[id(r)][0] / r["actual"] for r in rows if id(r) in blind]
    print("  blind route level: %.1f%% within +-20%%" % (100.0 * sum(1 for x in br if within(x)) / len(br)))

    if a.dry_run:
        print("  dry run, nothing written")
        return

    basis = "calibrated-fitted v1.3 %s sample, %s rule" % (pop, a.calib)
    prov = ("BT2 v1.3, sample %s n=%d, cohorts %s. Calibration rule '%s' (%s). "
            "Calibrated %.1f%% within +-20%%, %.1f%% within +-10%%. Blind LOCO %.1f%% within +-20%%. "
            "A calibrated figure states how hard the model was allowed to fit its own history and "
            "has no meaning independent of model capacity."
            % (pop, len(rows), ",".join(str(c) for c in B.COHORTS), a.calib, CALIB[a.calib],
               w20, w10, 100.0 * sum(1 for x in br if within(x)) / len(br)))

    m = {"carid": G.carid, "version": "1.3 09Aug2026", "author": "Avia Solutions",
         "n_train": len(rows), "population": pop, "calib_rule": a.calib,
         "calib_config": CALIB[a.calib], "blind_config": BLIND_KW, "provenance": prov}
    for qq, nm in ((0.5, "q50"), (0.25, "q25"), (0.75, "q75")):
        mm = G.make(SPEC, **BLIND_KW)
        mm.set_params(quantile=qq)
        mm.fit(X, y)
        m[nm] = mm
    with open("%s/bt2_model_v1_3.pkl" % B.BT2, "wb") as fh:
        pickle.dump(m, fh)
    print("  wrote %s/bt2_model_v1_3.pkl" % B.BT2)

    if a.out_app:
        # The evidence file must carry every column track_record.py reads, not just the ones the
        # headline needs. Dropping region, natural and p2p_outturn does not fail: the page renders
        # with every route in a blank peer group and a forecastable count of zero. That is the
        # silent-degradation shape this programme keeps finding, so the columns are written here
        # and the loader's expectations are the specification.
        rc = {}
        rp = os.path.join(B.BT2, "region_by_country.json")
        if os.path.exists(rp):
            rc = json.load(open(rp))["map"]
        else:
            print("  WARNING: no region_by_country.json, region column will be blank")
        p = os.path.join(a.out_app, "master_backtest_scored.csv")
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["route", "dep", "arr", "year", "region", "carrier", "type", "forecast_pax",
                        "outturn_pax", "p2p_outturn", "natural", "fc_over_out",
                        "corrected_fc_over_out", "engine", "basis", "outturn_source", "population"])
            for r, f in zip(rows, fc):
                reg = rc.get(r.get("ctry_a"), "") or rc.get(r.get("ctry_b"), "")
                # For a BT2 row the outturn IS the nonstop O&D, so p2p_outturn is the outturn, and
                # base_mkt is the measured existing market that stands where the engine's natural
                # market size would. corrected_fc_over_out stays empty: it was empty on every row of
                # the 5 August file too, and the page already handles that.
                w.writerow(["%s-%s" % (r["a"], r["b"]), r["a"], r["b"], r["cohort"], reg,
                            r["oag_carrier"], r["typ"], round(f), round(r["actual"]),
                            round(r["actual"]), round(r["base_mkt"]),
                            round(f / r["actual"], 4), "", "bt2", basis, "Sabre MIDT", pop])
        print("  wrote %s" % p)
        print("  NOTE: outturn_source is Sabre MIDT on every row. The mixed basis adopted on")
        print("  5 August, US domestic graded against DOT DB1B, is NOT in this build: the DB1B")
        print("  outturns were built for the canon pairs and would have to be rebuilt for these.")
        errs = [100.0 * (x - 1) for x in ratios]
        bins = []
        for lo in range(-55, 55, 5):
            n = sum(1 for e in errs if lo <= e < lo + 5)
            if n:
                bins.append({"lo": lo, "hi": lo + 5, "n": n})
        j = os.path.join(a.out_app, "accuracy_dist.json")
        json.dump({"bins": bins, "w20": w20, "w10": w10, "n": len(rows),
                   "population": pop, "calib_rule": a.calib, "note": prov}, open(j, "w"))
        print("  wrote %s" % j)


if __name__ == "__main__":
    main()
