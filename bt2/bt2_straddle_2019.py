#!/usr/bin/env python3
r"""Forecast 2019 from cohorts either side of the COVID break. John's question, 9 August 2026.

    python3 bt2_straddle_2019.py

The question is whether post-COVID launch behaviour tells you anything about a pre-COVID year, or
whether the two eras are different enough that 2024 and 2025 are dead weight when the target is
2019. Log line 53 records era sensitivity in the other direction, tier A falling from 75.4% overall
to 67.1% on the 2025-only test, so asking it in this direction is fair.

Cohort 2015 cannot be built and is not a choice anyone can make: bt2_months needs OAG for the
launch year AND the year before, and the OAG store starts at 2015, so 2016 is the earliest cohort
that exists. The run is therefore 2016-2018 as the pre-COVID training set.

  A   train 2016-2018, score 2019               the clean forward test, no post-COVID data
  B   train 2016-2018 + 2024-2025, score 2019   John's question, and the same thing as the 2019
                                                fold of the six-cohort leave-one-cohort-out

Paired on the identical 2019 launches, so the only thing that varies is what the model was trained
on. G12 features throughout.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
from math import comb

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_g12_exp as F      # noqa: E402

SPEC = ["car", "qcx", "gro"]
WHICH = ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)

ARMS = [
    ("A  2016-2018 only",              (2016, 2017, 2018)),
    ("B  2016-2018 + 2024-2025",       (2016, 2017, 2018, 2024, 2025)),
    ("   2016-2018 + 2024",            (2016, 2017, 2018, 2024)),
    ("   2024-2025 only",              (2024, 2025)),
]


def hits(rows, train_cohorts, target=2019):
    tr = [r for r in rows if r["cohort"] in train_cohorts]
    te = [r for r in rows if r["cohort"] == target]
    m = G.make(SPEC, **KW)
    m.fit(F.X_of(tr, WHICH), G.y_of(tr))
    out = {}
    for r, p in zip(te, m.predict(F.X_of(te, WHICH))):
        f = r["seats_ly"] * math.exp(p)
        out["%s-%s|%s" % (r["a"], r["b"], r["oag_carrier"])] = (abs(f / r["actual"] - 1) <= 0.20, r)
    return len(tr), out


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if not a[k][0] and b[k][0])
    n10 = sum(1 for k in ks if a[k][0] and not b[k][0])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def pct(h):
    return 100.0 * sum(1 for v in h.values() if v[0]) / len(h)


def main():
    rows = G.rows
    F.attach(rows)
    res = {}
    print("\n=== forecasting cohort 2019 blind, G12 features, paired on the same launches ===")
    print("  %-30s %8s %7s %9s   %s" % ("training cohorts", "train n", "2019 n", "+-20%",
                                        "against arm A"))
    for label, cs in ARMS:
        ntr, h = hits(rows, cs)
        res[label] = h
        base = res.get("A  2016-2018 only")
        tail = ""
        if base is not None and label != "A  2016-2018 only":
            g, l, p = mcnemar(base, h)
            tail = "+%-3d -%-3d p=%.3f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
        print("  %-30s %8d %7d %8.1f%%   %s" % (label, ntr, len(h), pct(h), tail))

    print("\n=== the same, by the segment rule ===")
    seg = [("short-haul, domestic or LCC",
            lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")),
           ("long-haul, international, full-service",
            lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC")]
    print("  %-40s %8s %10s %10s" % ("", "n", "A", "B"))
    for label, fn in seg:
        a = {k: v for k, v in res["A  2016-2018 only"].items() if fn(v[1])}
        b = {k: v for k, v in res["B  2016-2018 + 2024-2025"].items() if fn(v[1])}
        print("  %-40s %8d %9.1f%% %9.1f%%" % (label, len(a), pct(a), pct(b)))


if __name__ == "__main__":
    main()
