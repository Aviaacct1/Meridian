#!/usr/bin/env python3
r"""Pre-launch fare as a BT2 feature. Kickoff section 4.2, the residual BT2 itself names.

    python3 bt2_fare_exp.py prelaunch_fare_bt2.csv

BT2's own conclusion is that what it cannot see is "fare and network decisions not visible in a
pre-launch schedule", and fare is in none of its fifteen features. This adds it and re-runs the
leave-one-cohort-out blind score against the G09 control, which reproduces at 51.0% within +-20% on
2,208 routes, matching bt2_experiments.log line 28 of 29 July 2026.

THE FARE IS READ FROM YEAR L-1. A launch-year fare is an outcome and would predict the outturn by
knowing it.

MISSING FARES ARE PASSED AS NaN, not imputed. HistGradientBoostingRegressor learns a split on
missingness, which is the honest treatment: an absent pre-launch fare means an absent pre-launch
market, and that is information rather than a gap to fill with a mean.

ONE CHANGE AT A TIME, AND PAIRED. Each variant is scored on the same 2,208 routes as the control,
so the comparison is paired and only the routes crossing the +-20% band carry information. A
two-sided exact binomial on those says whether a gap is larger than the noise. Every number here is
BLIND, leave-one-cohort-out. Fitted is printed beside it and is never the finding.

Which of the three things in section 1 changed: BT2, and only BT2. The QSI engine is untouched.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
import sys
from collections import defaultdict
from math import comb

import numpy as np

import bt2_gbm as G
import bt2_lib as B


def load_fare(path):
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8-sig")):
        def g(k):
            try:
                v = float(r[k])
                return v if v > 0 else None
            except (TypeError, ValueError, KeyError):
                return None
        out[(r["a"], r["b"], int(r["pre_year"]))] = (g("pre_fare_usd"), g("pre_base_fare_usd"),
                                                     g("pre_pax"))
    return out


NAN = float("nan")


def attach(rows, fare):
    """Attach the pre-launch fare to each launch, and the fare relative to the median of its own
    haul band, which is the form the hypothesis takes: dear or cheap FOR ITS LENGTH."""
    for r in rows:
        f, bf, px = fare.get((r["a"], r["b"], r["cohort"] - 1), (None, None, None))
        r["_fare"], r["_basefare"], r["_prepax"] = f, bf, px
        r["_yield"] = (f / r["gcd"]) if (f and r["gcd"] > 0) else None
    med = {}
    for h in {B.haul_band(r["gcd"]) for r in rows}:
        vs = sorted(r["_fare"] for r in rows if B.haul_band(r["gcd"]) == h and r["_fare"])
        med[h] = vs[len(vs) // 2] if vs else None
    for r in rows:
        m = med.get(B.haul_band(r["gcd"]))
        r["_fvh"] = (r["_fare"] / m) if (r["_fare"] and m) else None
    have = sum(1 for r in rows if r["_fare"])
    print("fare attached to %d of %d launches (%.1f%%)" % (have, len(rows), 100.0 * have / len(rows)))


def _log(v):
    return math.log(v) if v and v > 0 else NAN


EXTRA = {
    "fare":  lambda r: [_log(r["_fare"])],
    "base":  lambda r: [_log(r["_basefare"])],
    "yield": lambda r: [_log(r["_yield"])],
    "fvh":   lambda r: [_log(r["_fvh"])],
    "both":  lambda r: [_log(r["_fare"]), _log(r["_fvh"])],
}

BASE_SPEC = ["car", "qcx", "gro"]          # G09, the control
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)


def X_of(rs, extra):
    x = G.X_of(rs, BASE_SPEC)
    if not extra:
        return x
    add = np.array([EXTRA[extra](r) for r in rs])
    return np.hstack([x, add])


def blind(rows, extra):
    """Leave one cohort out, exactly as bt2_gbm.run does. Returns {route key: within +-20%}."""
    hit = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(BASE_SPEC, **KW)
        m.fit(X_of(tr, extra), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, extra))):
            f = r["seats_ly"] * math.exp(p)
            hit["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                abs(f / r["actual"] - 1) <= 0.20
    return hit


def fitted(rows, extra):
    m = G.make(BASE_SPEC, **KW)
    m.fit(X_of(rows, extra), G.y_of(rows))
    p = m.predict(X_of(rows, extra))
    return B.score([(r["seats_ly"] * math.exp(q), r["actual"]) for r, q in zip(rows, p)])["w20"] * 100


def mcnemar(a, b):
    keys = set(a) & set(b)
    n01 = sum(1 for k in keys if not a[k] and b[k])
    n10 = sum(1 for k in keys if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def main():
    fare = load_fare(sys.argv[1])
    rows = G.rows
    attach(rows, fare)

    print("\n=== G09 control and the fare variants, blind leave-one-cohort-out, n=%d ===" % len(rows))
    print("  %-28s %8s %10s   %s" % ("", "FITTED", "BLIND", "against the G09 control"))
    ctl = blind(rows, None)
    print("  %-28s %7.1f%% %9.1f%%" % ("G09 control", fitted(rows, None),
                                       100.0 * sum(ctl.values()) / len(ctl)))
    for name, label in (("fare", "G09 + ln(pre fare)"),
                        ("base", "G09 + ln(pre base fare)"),
                        ("yield", "G09 + ln(pre yield)"),
                        ("fvh", "G09 + ln(fare vs haul)"),
                        ("both", "G09 + fare + fare vs haul")):
        h = blind(rows, name)
        g, l, p = mcnemar(ctl, h)
        print("  %-28s %7.1f%% %9.1f%%   +%-4d -%-4d p=%.3f%s"
              % (label, fitted(rows, name), 100.0 * sum(h.values()) / len(h), g, l, p,
                 "" if p < 0.05 else "  NOT MEASURABLE"))

    print("\n  Control reproduces bt2_experiments.log line 28 of 29 July 2026 at 51.0% blind.")
    print("  Read the BLIND column. Fitted is printed to show the gap, never as the result.")


if __name__ == "__main__":
    main()
