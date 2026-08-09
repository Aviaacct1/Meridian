#!/usr/bin/env python3
r"""A size-conditioned calibration on BT2's blind forecast. Diagnosed 9 August 2026.

    AVIA_BT2_COHORTS=2016,2017,2018,2019,2024,2025 python3 bt2_size_calib.py

THE DIAGNOSIS. bt2_tier_diagnose showed that the predicted-spread deciles carry no bias at all,
median ratio 0.97 to 1.02 across every one of the ten, so tier B and C are wider rather than wrong
and there is no mechanism to name in the tier split. Banding the same blind predictions by route
SIZE told a different story: median ratio 1.14 on routes under 5,000 passengers, 0.98 at 5-15k,
0.89 at 15-40k and 0.85 at 40-100k. That is a monotone size bias, the signature of a median
quantile loss on log O&D-per-seat pulling every prediction toward the middle of the training
distribution.

THE TRAP IN FIXING IT, and it is the whole point of this file. Those bands were cut on the ACTUAL
outturn, which is the answer. A correction keyed on actual size is not a forecast, it is a lookup
of the thing being forecast, and it would score beautifully and be worthless. The bands here are
cut on the FORECAST, which is known before the outturn is. If the bias survives that change of
axis it is correctable; if it does not, it was regression to the mean read backwards and there is
nothing to fix.

THE CORRECTION IS FITTED INSIDE THE FOLD. Within each leave-one-cohort-out fold, the model is fit
on the training cohorts, then the median actual-over-forecast per forecast-size band is taken from
those SAME training cohorts, then both are applied to the held-out cohort. Fitting the correction
on all cohorts and scoring held-out would leak the outcome into the calibration.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import statistics
from collections import defaultdict
from math import comb

import bt2_gbm as G
import bt2_lib as B

SPEC = ["car", "qcx", "gro"]
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)

# Forecast-size bands. Wide enough that the median in each is taken from hundreds of routes, not
# from a handful, which is the failure mode the kickoff records at 891 cells over 1,343 routes.
EDGES = [3000, 6000, 10000, 16000, 26000, 45000]


def size_band(x):
    for i, e in enumerate(EDGES):
        if x < e:
            return i
    return len(EDGES)


def key(r):
    return "%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])


def run():
    """One LOCO pass returning, per held-out route, the raw and the size-calibrated forecast."""
    raw, cal = {}, {}
    for L in B.COHORTS:
        tr = [r for r in G.rows if r["cohort"] != L]
        te = [r for r in G.rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(G.X_of(tr, SPEC), G.y_of(tr))

        # in-fold forecasts on the TRAINING cohorts, which is where the correction comes from
        ptr = m.predict(G.X_of(tr, SPEC))
        cells = defaultdict(list)
        for r, p in zip(tr, ptr):
            f = r["seats_ly"] * math.exp(p)
            if f > 0 and r["actual"] > 0:
                cells[size_band(f)].append(r["actual"] / f)
        allr = [v for vs in cells.values() for v in vs]
        gmed = statistics.median(allr) if allr else 1.0
        corr = {k: (statistics.median(v) if len(v) >= 40 else gmed) for k, v in cells.items()}

        for r, p in zip(te, m.predict(G.X_of(te, SPEC))):
            f = r["seats_ly"] * math.exp(p)
            if f <= 0 or r["actual"] <= 0:
                continue
            raw[key(r)] = (f, r["actual"], r)
            cal[key(r)] = (f * corr.get(size_band(f), gmed), r["actual"], r)
    return raw, cal


def w20(d):
    return 100.0 * sum(1 for f, a, _ in d.values() if abs(f / a - 1) <= 0.20) / len(d)


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if abs(a[k][0] / a[k][1] - 1) > 0.20 >= abs(b[k][0] / b[k][1] - 1))
    n10 = sum(1 for k in ks if abs(b[k][0] / b[k][1] - 1) > 0.20 >= abs(a[k][0] / a[k][1] - 1))
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def main():
    raw, cal = run()
    print("blind leave-one-cohort-out on %d launches, cohorts %s"
          % (len(raw), ",".join(str(c) for c in B.COHORTS)))

    print("\n=== does the bias survive the change of axis, from actual size to FORECAST size ===")
    print("  %-18s %6s %9s %14s %14s"
          % ("band", "n", "+-20% raw", "median ratio raw", "median ratio cal"))
    gr, gc = defaultdict(list), defaultdict(list)
    for k, (f, a, r) in raw.items():
        gr[size_band(f)].append(f / a)
        gc[size_band(f)].append(cal[k][0] / a)
    lab = ["<3k", "3-6k", "6-10k", "10-16k", "16-26k", "26-45k", "45k+"]
    for i in sorted(gr):
        rs = gr[i]
        print("  %-18s %6d %8.1f%% %14.2f %14.2f"
              % (lab[i], len(rs), 100.0 * sum(1 for x in rs if abs(x - 1) <= 0.20) / len(rs),
                 statistics.median(rs), statistics.median(gc[i])))

    g, l, p = mcnemar(raw, cal)
    print("\n=== blind score ===")
    print("  raw                        %.1f%%" % w20(raw))
    print("  size-calibrated            %.1f%%   +%d -%d  p=%.4f%s"
          % (w20(cal), g, l, p, "" if p < 0.05 else "   NOT MEASURABLE"))
    print("\n  The correction is fitted inside each fold on the training cohorts only, and the")
    print("  bands are cut on the forecast, never on the outturn.")


if __name__ == "__main__":
    main()
