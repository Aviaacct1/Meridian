#!/usr/bin/env python3
r"""Departure-time quality as a feature on the capacity anchor. Kickoff section 4.1.

    AVIA_BT2_COHORTS=2016,2017,2018,2019,2024,2025 python3 bt2_qtime_exp.py PRETEST.csv

NOT THE SAME QUESTION AS THE A/B OF 8 AUGUST. That asked whether the wave-timed connecting feed
improves the structural QSI engine's forecast, and it did not: paired on identical routes, 17.9% to
17.9%, median 1.32 to 1.33. This asks whether the schedule-quality measure q predicts O&D-per-seat
on top of a capacity anchor, which is a different estimator being asked a different thing. BT2's
fifteen features carry QSI capture, schedule density and connection-competition strength, and
nothing whatever about time of day.

THE PRIOR IS WEAK AND SHOULD BE STATED BEFORE THE RESULT. On the anchor, connecting share as a cell
scores 40.7% held-out against a 43.6% baseline, so the nearest available proxy is a mild negative.
It is not decisive, because feed share is not departure-time quality.

WHAT q IS. From pretest_qsi_08Aug2026.csv, 3,179 routes: q_flown is the market-weighted QSI share of
onward markets at the departure time actually flown, q_best the same at the best available time, and
opt_over_flown the ratio. It discriminates hard, median q 0.0086 with a 469-fold p90 over p10 spread
and a median optimum 1.90 times the flown value, which is why it earns a product feature. Whether it
earns a forecast feature is what this measures, and the two claims must not be run together.

COVERAGE IS PARTIAL AND IS NOT FILLED. The pretest covers 2017, 2018 and 2019 only, so cohorts 2016,
2024 and 2025 carry no q at all. Missing values are passed as NaN, which HistGradientBoostingRegressor
splits on, and the paired comparison is reported BOTH on all routes and on the covered subset alone,
because a feature present on two fifths of the sample is diluted by the rest.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
import sys
from math import comb

import numpy as np

import bt2_gbm as G
import bt2_lib as B

SPEC = ["car", "qcx", "gro"]
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)
NAN = float("nan")


def _f(v):
    try:
        x = float(v)
        return x
    except (TypeError, ValueError):
        return None


def load_q(path):
    """Keyed on the UNORDERED pair and the year. The pretest writes the route in departure-arrival
    order, not sorted, so YNY-KKJ and KKJ-YNY are the same route and a sorted key is required."""
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8-sig")):
        parts = (r["route"] or "").split("-")
        if len(parts) != 2:
            continue
        a, b = sorted(parts)
        out[(a, b, int(r["year"]))] = r
    return out


def attach(rows, q):
    have = 0
    for r in rows:
        c = q.get((r["a"], r["b"], r["cohort"]))
        r["_q"] = c
        if c:
            have += 1
    print("q attached to %d of %d launches (%.1f%%); cohorts with any coverage: %s"
          % (have, len(rows), 100.0 * have / len(rows),
             ",".join(str(c) for c in sorted({r["cohort"] for r in rows if r["_q"]}))))
    return have


def extra_of(r):
    c = r.get("_q")
    if not c:
        return [NAN, NAN, NAN, NAN]
    qf, oo = _f(c.get("q_flown")), _f(c.get("opt_over_flown"))
    nm, bd = _f(c.get("n_markets")), _f(c.get("best_dep"))
    return [math.log(qf) if (qf and qf > 0) else NAN,
            math.log(oo) if (oo and oo > 0) else NAN,
            math.log1p(nm) if nm is not None else NAN,
            bd if bd is not None else NAN]


def X_of(rs, use):
    x = G.X_of(rs, SPEC)
    if not use:
        return x
    return np.hstack([x, np.array([extra_of(r) for r in rs])])


def blind(rows, use):
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(X_of(tr, use), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, use))):
            f = r["seats_ly"] * math.exp(p)
            out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                abs(f / r["actual"] - 1) <= 0.20
    return out


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if not a[k] and b[k])
    n10 = sum(1 for k in ks if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def report(label, ctl, test, keys=None):
    a = {k: v for k, v in ctl.items() if keys is None or k in keys}
    b = {k: v for k, v in test.items() if keys is None or k in keys}
    g, l, p = mcnemar(a, b)
    print("  %-30s n=%-5d %7.1f%% -> %6.1f%%   +%-4d -%-4d p=%.4f%s"
          % (label, len(a), 100.0 * sum(a.values()) / len(a), 100.0 * sum(b.values()) / len(b),
             g, l, p, "" if p < 0.05 else "  NOT MEASURABLE"))


def main():
    rows = G.rows
    if not attach(rows, load_q(sys.argv[1])):
        raise SystemExit("no q attached: check the pretest file and the cohort list.")

    ctl = blind(rows, False)
    test = blind(rows, True)
    cov = {"%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])
           for r in rows if r["_q"]}
    hard = {"%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"]) for r in rows
            if r["_q"] and r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"}

    print("\n=== blind leave-one-cohort-out, control against control + departure-time quality ===")
    report("all routes", ctl, test)
    report("routes where q exists", ctl, test, cov)
    report("q routes, the hard segment", ctl, test, hard)
    print("\n  The covered-subset row is the one that carries the finding. The all-routes row")
    print("  dilutes it with three cohorts that have no q at all.")


if __name__ == "__main__":
    main()
