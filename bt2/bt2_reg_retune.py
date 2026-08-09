#!/usr/bin/env python3
r"""Does the G09 regularisation still fit, now the sample is 68% larger? Nested, so the answer is honest.

    python3 bt2_reg_retune.py

WHY ASK. The configuration every BT2 number rests on, learning rate 0.04, 600 iterations, minimum
60 samples per leaf and l2 of 5.0, was chosen by the G03 to G07 sweep on 29 July 2026 against 2,208
launches. The sample is now 3,700, and heavier regularisation is exactly what a small sample needs
and a larger one does not. Leaving the setting untouched because it was once right is how a tuned
number quietly becomes a stale one.

THE TRAP, AND THE DESIGN THAT AVOIDS IT. Running six configurations and reporting the best blind
score reports the maximum of six noisy numbers, which is biased upward by construction. That is the
same error as reading a feature ranking off differences of one percentage point. So the work is
nested:

  SELECT   on cohorts 2016-2019 only, leave-one-cohort-out within those four.
  CONFIRM  the single chosen configuration on 2024 and 2025, cohorts that took no part in the
           choice, trained on 2016-2019.

The confirm number is the one that may be quoted. The select table is printed in full, winner and
losers, because a sweep reported only by its winner cannot be checked.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os

import numpy as np

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_lib as B          # noqa: E402
import bt2_g12_exp as F      # noqa: E402

SPEC = ["car", "qcx", "gro"]
WHICH = ["base", "sister"]                     # G12, the current best feature set

# Declared before anything is run, so the grid cannot grow to fit a result.
GRID = [
    ("G09 setting, lr .04 it 600 leaf 60 l2 5", dict(lr=0.04, it=600, minleaf=60, l2=5.0)),
    ("lighter leaf 30",                          dict(lr=0.04, it=600, minleaf=30, l2=5.0)),
    ("lighter l2 1",                             dict(lr=0.04, it=600, minleaf=60, l2=1.0)),
    ("lighter both",                             dict(lr=0.04, it=600, minleaf=30, l2=1.0)),
    ("more trees, lr .03 it 900",                dict(lr=0.03, it=900, minleaf=30, l2=1.0)),
    ("wider, 63 leaves",                         dict(lr=0.04, it=600, minleaf=30, l2=1.0, leaves=63)),
]


def w20(rows, fc):
    n = sum(1 for r, f in zip(rows, fc) if abs(f / r["actual"] - 1) <= 0.20)
    return 100.0 * n / len(rows)


def fit_predict(tr, te, kw):
    m = G.make(SPEC, **kw)
    m.fit(F.X_of(tr, WHICH), G.y_of(tr))
    return [r["seats_ly"] * math.exp(p) for r, p in zip(te, m.predict(F.X_of(te, WHICH)))]


def loco(rows, cohorts, kw):
    out_r, out_f = [], []
    for L in cohorts:
        tr = [r for r in rows if r["cohort"] != L and r["cohort"] in cohorts]
        te = [r for r in rows if r["cohort"] == L]
        out_r += te
        out_f += fit_predict(tr, te, kw)
    return w20(out_r, out_f)


def main():
    rows = G.rows
    F.attach(rows)
    SELECT = (2016, 2017, 2018, 2019)
    CONFIRM = (2024, 2025)

    print("\n=== SELECT: leave-one-cohort-out within 2016-2019 only, n=%d ==="
          % sum(1 for r in rows if r["cohort"] in SELECT))
    scores = []
    for label, kw in GRID:
        s = loco(rows, SELECT, kw)
        scores.append((s, label, kw))
        print("  %-42s %6.1f%%" % (label, s))
    scores.sort(reverse=True)
    best_s, best_label, best_kw = scores[0]
    print("\n  chosen on the select cohorts: %s at %.1f%%" % (best_label, best_s))
    print("  That figure is the maximum of six noisy numbers and is biased upward. It is not the")
    print("  finding. The confirm run below is.")

    print("\n=== CONFIRM: trained on 2016-2019, scored on 2024 and 2025, which took no part ===")
    tr = [r for r in rows if r["cohort"] in SELECT]
    print("  %-42s %8s %8s" % ("", "2024", "2025"))
    for label, kw in ((GRID[0][0], GRID[0][1]), (best_label, best_kw)):
        cells = []
        for L in CONFIRM:
            te = [r for r in rows if r["cohort"] == L]
            cells.append(w20(te, fit_predict(tr, te, kw)))
        print("  %-42s %7.1f%% %7.1f%%" % (label, cells[0], cells[1]))
    print("\n  If the chosen setting does not beat the incumbent on BOTH unseen cohorts, the sweep")
    print("  found noise and the incumbent stands.")


if __name__ == "__main__":
    main()
