#!/usr/bin/env python3
r"""One sample, one estimator, one pair: the calibration rule grid on the 6,524. W10, 26 September 2026.

    AVIA_BT2_DIR=E:\Avia\bt2_relaxed  py -3.12 -s bt2_calib_grid.py

John's ruling of 26 September: one methodology across the general method and the route-forecast
accuracy sections, on one sample, so the stand hosts have one story. A calibrated figure is a
statement of how hard the model was allowed to fit its own history (V1.3-RULE, 9 Aug), so the
calibration rule is a declared choice, and the estimator that carries the declared rule is the one
the app must run. This script prints, for each candidate rule on the sample AVIA_BT2_DIR points at:

  in-sample      the calibrated pair, within +-20% and +-10%, Sabre throughout and on the mixed basis
  blind          the SAME rule leave-one-cohort-out: route level within +-20% and +-10%, and portfolios
                 of twenty within +-20% (seed 11, as bt2_claimset), so the out-of-sample cost of each
                 rule is beside its in-sample gain and nothing is chosen blind
  band           the share of launches whose actual falls inside the rule's own p25-p75 (50% is honest)

The blind configuration is printed first as the reference. John picks the rule; bt2_build_v13 then
writes THAT estimator into the pickle (its --calib choices are extended to match), and the pair on
every surface describes the model that answers a client. Nothing is written by this script.

Avia Solutions Limited. All rights reserved.
"""
import math
import random

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_claimset import _provenance, SPEC, G12, BLIND_KW
from bt2_score import within

RULES = [
    ("blind (reference)",       dict(lr=0.04, it=600,  minleaf=60, l2=5.0)),
    ("published (it800 ml5 lv63)", dict(lr=0.06, it=800,  minleaf=5, l2=0.0, leaves=63)),
    ("A (it1000 ml5 lv71)",     dict(lr=0.06, it=1000, minleaf=5, l2=0.0, leaves=71)),
    ("B (it1200 ml4 lv79)",     dict(lr=0.07, it=1200, minleaf=4, l2=0.0, leaves=79)),
    ("C (it1400 ml3 lv87)",     dict(lr=0.07, it=1400, minleaf=3, l2=0.0, leaves=87)),
    ("memorisation (it1600 ml3 lv95)", dict(lr=0.08, it=1600, minleaf=3, l2=0.0, leaves=95)),
]


def rate(pairs, tol=0.20):
    v = [f / a for f, a in pairs if a > 0 and f > 0]
    return 100.0 * sum(1 for x in v if within(x, tol)) / len(v)


def portfolios(out, n=20):
    random.seed(11)
    groups = []
    for L in B.COHORTS:
        co = [o for o in out if o["c"] == L]
        random.shuffle(co)
        groups += [co[i:i + n] for i in range(0, len(co), n) if len(co[i:i + n]) == n]
    sh = [sum(o["fc"] for o in g) / sum(o["act"] for o in g) for g in groups if sum(o["act"] for o in g) > 0]
    return 100.0 * sum(1 for x in sh if within(x)) / len(sh), len(sh)


def main():
    rows = G.rows
    F.attach(rows)
    import bt2_mixed_basis as MB
    sabre = [r["actual"] for r in rows]
    n_dot = MB.attach(rows)
    mixed = [r["actual"] for r in rows]
    for r, a in zip(rows, sabre):
        r["actual"] = a
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("target: %s   mixed basis: %d US domestic on DOT DB1B   build: %s" % (B.TARGET, n_dot, _provenance()))
    print("\n%-32s %17s %17s %14s %8s %8s" % ("rule", "in-sample Sabre", "in-sample mixed", "blind route", "pf20", "band"))
    print("%-32s %17s %17s %14s %8s %8s" % ("", "w20 / w10", "w20 / w10", "w20 / w10", "w20", "p25-75"))
    X, y = F.X_of(rows, G12), G.y_of(rows)
    for name, kw in RULES:
        m = G.make(SPEC, **kw); m.fit(X, y)
        fc = [r["seats_ly"] * math.exp(p) for r, p in zip(rows, m.predict(X))]
        ins = (rate(zip(fc, sabre)), rate(zip(fc, sabre), .10))
        inm = (rate(zip(fc, mixed)), rate(zip(fc, mixed), .10))
        lo = G.make(SPEC, **kw); lo.set_params(quantile=0.25); lo.fit(X, y)
        hi = G.make(SPEC, **kw); hi.set_params(quantile=0.75); hi.fit(X, y)
        band = 100.0 * sum(1 for r, a, b in zip(rows, lo.predict(X), hi.predict(X))
                           if r["seats_ly"] * math.exp(a) <= r["actual"] <= r["seats_ly"] * math.exp(b)) / len(rows)
        out = []
        for L in B.COHORTS:
            tr = [r for r in rows if r["cohort"] != L]
            te = [r for r in rows if r["cohort"] == L]
            mm = G.make(SPEC, **kw); mm.fit(F.X_of(tr, G12), G.y_of(tr))
            for r, p in zip(te, mm.predict(F.X_of(te, G12))):
                f = r["seats_ly"] * math.exp(p)
                if f > 0 and r["actual"] > 0:
                    out.append({"c": L, "fc": f, "act": r["actual"]})
        bl = (rate([(o["fc"], o["act"]) for o in out]), rate([(o["fc"], o["act"]) for o in out], .10))
        pf, npf = portfolios(out)
        print("%-32s %7.1f / %7.1f %7.1f / %7.1f %6.1f / %6.1f %7.1f%% %7.1f%%"
              % (name, ins[0], ins[1], inm[0], inm[1], bl[0], bl[1], pf, band), flush=True)
    print("\n  Reading: the in-sample pair is the calibrated claim for that rule; the blind columns are what the same")
    print("  rule does on launches it never saw, and they move the other way. Whichever rule John declares, the")
    print("  estimator fitted under it goes into the pickle, and both its columns go on the methodology page.")


if __name__ == "__main__":
    main()
