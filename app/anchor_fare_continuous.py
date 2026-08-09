#!/usr/bin/env python3
r"""Fare on the anchor as a CONTINUOUS variable, plus a sanity check on the fare itself.

    python3 anchor_fare_continuous.py bt_v1_baseline.csv prelaunch_fare.csv

WHY A SECOND TEST. The banded test scored fare through a median correction per cell, which is a
coarse estimator: four quartile bands throw away the ordering inside each band, and a cell median
cannot express "more of this means more of that". If the fare hypothesis is right at all, it is
right monotonically, so it deserves the estimator that can express it before it is written off.

    ln(O&D per seat) = a + b.ln(pre-launch fare) + haul fixed effects, fitted on the training
    cohort by ordinary least squares, then scored on the later cohort within +-20%.

THE COEFFICIENT IS THE FINDING, not the hit rate. If b holds its sign and rough size when the
cohorts swap, fare carries signal and only the banding was wrong. If b flips, fare is noise and no
estimator will rescue it.

THE SANITY CHECK COMES FIRST. A feature that fails should be shown to be a real variable before the
hypothesis is blamed: fare should rise with distance and the elasticity should look like an airline
fare curve rather than like a join that has gone wrong.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
import statistics
import sys

import numpy as np


def _f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except (TypeError, ValueError):
        return None


HAULS = ["<800", "800-2500", "2500-6000", ">6000"]


def haul(r):
    d = _f(r.get("gcd_km")) or 0
    return "<800" if d < 800 else "800-2500" if d < 2500 else "2500-6000" if d < 6000 else ">6000"


def load(base_p, fare_p):
    fare = {}
    for r in csv.DictReader(open(fare_p, newline="", encoding="utf-8-sig")):
        fare[(r["a"], r["b"], int(r["pre_year"]))] = r
    out = []
    for r in csv.DictReader(open(base_p, newline="", encoding="utf-8-sig")):
        cap, act = _f(r.get("capacity")), _f(r.get("outturn_pax"))
        if not (cap and act and _f(r.get("forecast_pax"))):
            continue
        d, x = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
        fr = fare.get((min(d, x), max(d, x), int(r["year"]) - 1))
        r["_fare"] = _f(fr.get("pre_fare_usd")) if fr else None
        r["_prepax"] = _f(fr.get("pre_pax")) if fr else None
        r["_ops"] = act / cap
        out.append(r)
    return out


def design(rows, use_fare):
    """Intercept, haul dummies (first level dropped), optionally ln(fare)."""
    X, y = [], []
    for r in rows:
        row = [1.0] + [1.0 if haul(r) == h else 0.0 for h in HAULS[1:]]
        if use_fare:
            row.append(math.log(r["_fare"]))
        X.append(row)
        y.append(math.log(r["_ops"]))
    return np.array(X), np.array(y)


def score(rows, X, beta, tol=0.20):
    pred = np.exp(X @ beta)
    act = np.array([r["_ops"] for r in rows])
    ratio = pred / act
    return 100.0 * float(np.mean(np.abs(ratio - 1.0) <= tol))


def main():
    rows = load(sys.argv[1], sys.argv[2])
    withf = [r for r in rows if r["_fare"]]
    print("usable rows %d, with a pre-launch fare %d" % (len(rows), len(withf)))

    print("\n=== sanity check on the fare variable itself ===")
    print("  %-14s %6s %10s %10s %10s" % ("haul", "n", "med fare", "med km", "med USD/km"))
    for h in HAULS:
        g = [r for r in withf if haul(r) == h]
        if not g:
            continue
        print("  %-14s %6d %9.0f%s %9.0f%s %9.3f%s"
              % (h, len(g), statistics.median([r["_fare"] for r in g]), "",
                 statistics.median([_f(r["gcd_km"]) for r in g]), "",
                 statistics.median([r["_fare"] / _f(r["gcd_km"]) for r in g]), ""))
    lf = np.log([r["_fare"] for r in withf])
    lk = np.log([_f(r["gcd_km"]) for r in withf])
    A = np.vstack([np.ones_like(lk), lk]).T
    b = np.linalg.lstsq(A, lf, rcond=None)[0]
    rho = float(np.corrcoef(lk, lf)[0, 1])
    print("  ln(fare) on ln(distance): elasticity %.3f, correlation %.3f" % (b[1], rho))
    print("  Source: Sabre, revenue-weighted fare in the pre-launch year, built this session.")

    by = {y: [r for r in withf if str(r.get("year")) == y] for y in ("2017", "2018")}
    print("\n=== ln(O&D per seat) = a + b.ln(fare) + haul, fitted on train, scored held-out ===")
    print("  %-26s %8s %10s %12s" % ("", "FITTED", "HELD-OUT", "b on ln(fare)"))
    for tr_y, te_y in (("2017", "2018"), ("2018", "2017")):
        tr, te = by[tr_y], by[te_y]
        print("  train %s n=%d, score %s n=%d" % (tr_y, len(tr), te_y, len(te)))
        for label, uf in (("haul only", False), ("haul + ln(fare)", True)):
            Xtr, ytr = design(tr, uf)
            beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
            Xte, _ = design(te, uf)
            bstr = "%+.4f" % beta[-1] if uf else "-"
            print("    %-24s %7.1f%% %9.1f%% %12s"
                  % (label, score(tr, Xtr, beta), score(te, Xte, beta), bstr))

    print("\n  READ THE COEFFICIENT COLUMN FIRST. A b that changes sign when the cohorts swap is")
    print("  noise wearing a decimal point, and no estimator rescues it.")


if __name__ == "__main__":
    main()
