#!/usr/bin/env python3
r"""Does adding a cohort raise the blind score, and by how much on identical routes?

    AVIA_BT2_COHORTS=... python3 bt2_cohort_exp.py

Adding a cohort is the one change with a measured value already attached: +1.7 points blind going
from four cohorts to five, bt2_experiments.log line 38 of 5 August 2026. Cohort 2024 was built on
9 August 2026 (798 launches) because the OAG store covers 2023 and 2024 and it was the only cohort
that could still be built: OAG runs 2015-2019 and 2023-2026, so nothing before 2016 and nothing in
2020-2023 will ever exist.

THE COMPARISON THAT MATTERS IS PAIRED. A run with more cohorts also SCORES more routes, so its
overall blind figure is measured on a different sample and cannot be compared with the four-cohort
number. Every configuration is therefore also scored on the ORIGINAL 2016-2019 routes only, which
are identical across all of them, so the only thing that varies is what the model was trained on.
The overall figure is printed beside it for the record and is not the comparison.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
from math import comb


def hits(cohorts):
    """Blind leave-one-cohort-out at the G09 configuration. Returns {route key: within +-20%}."""
    os.environ["AVIA_BT2_COHORTS"] = ",".join(str(c) for c in cohorts)
    for m in ("bt2_lib", "bt2_gbm"):
        import sys
        sys.modules.pop(m, None)
    import bt2_gbm as G
    import bt2_lib as B
    spec, kw = ["car", "qcx", "gro"], dict(minleaf=60, l2=5.0, lr=0.04, it=600)
    out = {}
    for L in B.COHORTS:
        tr = [r for r in G.rows if r["cohort"] != L]
        te = [r for r in G.rows if r["cohort"] == L]
        m = G.make(spec, **kw)
        m.fit(G.X_of(tr, spec), G.y_of(tr))
        for r, p in zip(te, m.predict(G.X_of(te, spec))):
            f = r["seats_ly"] * math.exp(p)
            out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                abs(f / r["actual"] - 1) <= 0.20
    return out


def mcnemar(a, b):
    keys = set(a) & set(b)
    n01 = sum(1 for k in keys if not a[k] and b[k])
    n10 = sum(1 for k in keys if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


CONFIGS = [
    ("2016-2019, the control", (2016, 2017, 2018, 2019)),
    ("+ 2025", (2016, 2017, 2018, 2019, 2025)),
    ("+ 2024", (2016, 2017, 2018, 2019, 2024)),
    ("+ 2024 + 2025", (2016, 2017, 2018, 2019, 2024, 2025)),
]


def main():
    res = {}
    for label, cs in CONFIGS:
        res[label] = hits(cs)
    base_label = CONFIGS[0][0]
    base = res[base_label]
    orig = set(base)

    print("\n=== blind leave-one-cohort-out, G09 configuration ===")
    print("  %-26s %6s %9s   %s   %s"
          % ("training cohorts", "n", "BLIND all", "on the 2016-2019 routes only",
             "against the control"))
    for label, _ in CONFIGS:
        h = res[label]
        allp = 100.0 * sum(h.values()) / len(h)
        sub = {k: v for k, v in h.items() if k in orig}
        subp = 100.0 * sum(sub.values()) / len(sub)
        if label == base_label:
            print("  %-26s %6d %8.1f%%   %8.1f%% on n=%d" % (label, len(h), allp, subp, len(sub)))
            continue
        g, l, p = mcnemar(base, sub)
        print("  %-26s %6d %8.1f%%   %8.1f%% on n=%d   +%-4d -%-4d p=%.3f%s"
              % (label, len(h), allp, subp, len(sub), g, l, p,
                 "" if p < 0.05 else "  NOT MEASURABLE"))

    print("\n  The paired column is the finding. The all-routes column is measured on a different")
    print("  sample every time a cohort is added and cannot carry a comparison.")


if __name__ == "__main__":
    main()
