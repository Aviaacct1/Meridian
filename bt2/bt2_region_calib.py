#!/usr/bin/env python3
r"""Calibrate BT2 by the launching carrier's home region. Diagnosed 9 August 2026.

    python3 bt2_region_calib.py

THE DIAGNOSIS, and it came from the tails rather than from a list of features. On the long-haul
international full-service segment the blind median forecast over actual, by the launching carrier's
home region, is:

  Middle East      1.30 on n=98,  over-read in five of six cohorts (3.20, 1.47, 1.42, 0.90, 1.39, 1.03)
  Asia             1.09 on n=341, over-read in SIX of six (1.23, 1.07, 1.01, 1.09, 1.04, 1.16)
  Africa           1.15 on n=48
  Europe           0.94 on n=278, under-read in five of six
  North America    0.94 on n=172, under-read in five of six
  Latin America    0.94 on n=101

That is a direction, it is large, and it repeats every cohort. Chinese and Gulf carriers launching
long-haul are read high and North Atlantic and European carriers are read low. Giving the model
seven home-region indicators moved the hard segment from 36.5% to 38.2% and was not measurable,
which is what a heavily regularised quantile GBM does with a level shift buried among twenty-eight
features. A calibration applies the shift directly, which is the method that worked on the airport
bias: name the mechanism and correct that, never a blanket factor.

WHY THIS IS NOT THE TRAP FROM EARLIER TODAY, and the question has to be answered rather than waved
away. The size calibration failed because its bands were cut on the ACTUAL outturn, so it was a
lookup of the answer and it evaporated the moment the axis moved to the forecast. The carrier's home
region is known years before the launch, has nothing to do with the outturn, and cannot move when
the outturn does.

The correction is fitted INSIDE each fold on the training cohorts only, so the held-out cohort
contributes nothing to the factor applied to it.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import statistics
from collections import defaultdict
from math import comb

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_lib as B          # noqa: E402
import bt2_g12_exp as F      # noqa: E402
import bt2_geo_exp as GEO    # noqa: E402

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
MIN_CELL = 40           # below this a region falls back to the global median


def HARD(r):
    return r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"


def EASY(r):
    return r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")


def key(r):
    return "%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])


def cellfn(mode):
    """mode picks what the calibration is keyed on. Each is known before the launch."""
    if mode == "home":
        return lambda r: r["_geo"]["hr"] or "?"
    if mode == "home_hard":
        # the same, but only where the shortfall is; everything else keeps a single global factor
        return lambda r: ("H:" + (r["_geo"]["hr"] or "?")) if HARD(r) else "other"
    if mode == "home_x_dom":
        return lambda r: "%s|%s" % (r["_geo"]["hr"] or "?", "DOM" if r["dom"] else "INT")
    raise ValueError(mode)


def run(rows, mode):
    """LOCO with a NESTED calibration. Returns {route: (raw hit, calibrated hit, row)}.

    The first attempt at this fitted the correction on the model's own training predictions and
    moved five routes out of 3,700. That was the flaw, not the hypothesis: a model has largely
    fitted its own training rows, so its in-sample residual median sits near 1.00 whatever its
    out-of-sample bias is. The bias being corrected is an out-of-sample one and can only be seen
    out of sample.

    So inside each outer fold there is an inner leave-one-cohort-out across the remaining five
    cohorts, and the correction is taken from THOSE out-of-fold residuals. The held-out cohort
    contributes nothing to the factor applied to it, at either level.
    """
    kf = cellfn(mode) if mode else None
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(F.X_of(tr, G12), G.y_of(tr))
        corr, gmed = {}, 1.0
        if kf:
            cells = defaultdict(list)
            allr = []
            inner = [c for c in B.COHORTS if c != L]
            for c in inner:
                itr = [r for r in tr if r["cohort"] != c]
                ite = [r for r in tr if r["cohort"] == c]
                im = G.make(SPEC, **KW)
                im.fit(F.X_of(itr, G12), G.y_of(itr))
                for r, p in zip(ite, im.predict(F.X_of(ite, G12))):
                    f = r["seats_ly"] * math.exp(p)
                    if f > 0 and r["actual"] > 0:
                        cells[kf(r)].append(r["actual"] / f)
                        allr.append(r["actual"] / f)
            gmed = statistics.median(allr) if allr else 1.0
            corr = {k: (statistics.median(v) if len(v) >= MIN_CELL else gmed)
                    for k, v in cells.items()}
        for r, p in zip(te, m.predict(F.X_of(te, G12))):
            f = r["seats_ly"] * math.exp(p)
            if f <= 0 or r["actual"] <= 0:
                continue
            c = corr.get(kf(r), gmed) if kf else 1.0
            out[key(r)] = (abs(f / r["actual"] - 1) <= 0.20,
                           abs(f * c / r["actual"] - 1) <= 0.20, r)
    return out


def mcnemar(pairs):
    n01 = sum(1 for a, b, _ in pairs if not a and b)
    n10 = sum(1 for a, b, _ in pairs if a and not b)
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def main():
    rows = G.rows
    F.attach(rows)
    GEO.attach_geo(rows)

    print("\n=== blind LOCO, n=%d. Calibration fitted inside each fold, on training cohorts ==="
          % len(rows))
    print("  %-30s %9s %9s %9s   %s"
          % ("keyed on", "ALL", "easy", "hard", "against the uncalibrated arm"))
    for mode, label in (("home", "carrier home region"),
                        ("home_hard", "home region, hard segment only"),
                        ("home_x_dom", "home region x domestic")):
        res = run(rows, mode)
        vals = list(res.values())
        for nm, fn in (("raw", None),):
            pass
        raw = 100.0 * sum(1 for a, _, _ in vals if a) / len(vals)
        cal = 100.0 * sum(1 for _, b, _ in vals if b) / len(vals)
        e = [v for v in vals if EASY(v[2])]
        d = [v for v in vals if HARD(v[2])]
        g, l, p = mcnemar(vals)
        if mode == "home":
            print("  %-30s %8.1f%% %8.1f%% %8.1f%%   (uncalibrated control)"
                  % ("none", raw,
                     100.0 * sum(1 for a, _, _ in e if a) / len(e),
                     100.0 * sum(1 for a, _, _ in d if a) / len(d)))
        print("  %-30s %8.1f%% %8.1f%% %8.1f%%   +%-4d -%-4d p=%.4f%s"
              % (label, cal,
                 100.0 * sum(1 for _, b, _ in e if b) / len(e),
                 100.0 * sum(1 for _, b, _ in d if b) / len(d),
                 g, l, p, "" if p < 0.05 else "  NOT MEASURABLE"))


if __name__ == "__main__":
    main()
