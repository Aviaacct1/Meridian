#!/usr/bin/env python3
r"""Recency and era weighting on the training set. Diagnosed 9 August 2026, tested nested.

    python3 bt2_recency_exp.py

WHERE THIS CAME FROM. Forecasting cohort 2019 from either side of the COVID break showed the two
segments moving in opposite directions: adding 2024 and 2025 to a 2016-2018 training set takes
short-haul domestic and low-cost launches from 65.5% to 67.2% and long-haul international
full-service from 40.2% down to 35.4%. Training on post-COVID cohorts alone scores 49.8% against
54.3%, +64 -90, p=0.044. The model has no era term and weights every launch alike, so a 2025
long-haul launch counts for as much as a contemporaneous one when the target is 2019.

TWO FORMS, because the break is not the same thing as the passage of time.

  calendar   weight = exp(-lam . |target year - cohort year|). Smooth, and treats the four years
             from 2019 to 2024 as four years rather than as a structural break.
  era        weight = 1 on the same side of COVID as the target, alpha on the other side. Treats
             the break as a break, which is what the 2019 run suggests it is.

lam = 0 and alpha = 1 are the current model, and both appear in the grid as the control so the
comparison is like for like rather than against a remembered number.

NESTED, so the answer can be trusted. The setting is chosen on the 2016-2019 folds only, then the
single winner is confirmed on the 2024 and 2025 folds, which took no part in the choice. Reporting
the best of nine numbers would report the maximum of nine noisy numbers.

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
WHICH = ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)

PRE = 2019          # cohorts at or below this are pre-COVID


def weights(train, target, lam, alpha):
    w = []
    for r in train:
        c = r["cohort"]
        x = math.exp(-lam * abs(target - c))
        if alpha < 1.0 and ((c <= PRE) != (target <= PRE)):
            x *= alpha
        w.append(x)
    return np.array(w)


# Declared before anything is run, so the grid cannot grow to fit a result.
GRID = [
    ("control, no weighting",        0.00, 1.0),
    ("calendar lam 0.05",            0.05, 1.0),
    ("calendar lam 0.10",            0.10, 1.0),
    ("calendar lam 0.20",            0.20, 1.0),
    ("calendar lam 0.40",            0.40, 1.0),
    ("era alpha 0.7",                0.00, 0.7),
    ("era alpha 0.5",                0.00, 0.5),
    ("era alpha 0.3",                0.00, 0.3),
    ("era 0.5 + calendar lam 0.10",  0.10, 0.5),
]


def fold(rows, target, pool, lam, alpha):
    tr = [r for r in rows if r["cohort"] in pool and r["cohort"] != target]
    te = [r for r in rows if r["cohort"] == target]
    m = G.make(SPEC, **KW)
    m.fit(F.X_of(tr, WHICH), G.y_of(tr), sample_weight=weights(tr, target, lam, alpha))
    out = {}
    for r, p in zip(te, m.predict(F.X_of(te, WHICH))):
        f = r["seats_ly"] * math.exp(p)
        out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
            (abs(f / r["actual"] - 1) <= 0.20, r)
    return out


def pct(h):
    return 100.0 * sum(1 for v in h.values() if v[0]) / len(h) if h else 0.0


def main():
    # Run in two phases because the whole grid is 36 model fits and the select phase is the only
    # thing the confirm phase needs from it, which is one line: the chosen setting.
    #     python3 bt2_recency_exp.py select
    #     python3 bt2_recency_exp.py confirm "era alpha 0.5" 0.0 0.5
    import sys
    phase = sys.argv[1] if len(sys.argv) > 1 else "select"

    rows = G.rows
    F.attach(rows)
    ALL = tuple(B.COHORTS)
    SELECT = (2016, 2017, 2018, 2019)
    CONFIRM = (2024, 2025)

    if phase == "select":
        print("\n=== SELECT: the 2016-2019 folds only, trained on every other cohort ===")
        # The grid can be run in slices, because 36 model fits does not always finish inside a
        # single call and a partial table is worse than two complete halves.
        lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        hi = int(sys.argv[3]) if len(sys.argv) > 3 else len(GRID)
        res = []
        for label, lam, alpha in GRID[lo:hi]:
            h = {}
            for L in SELECT:
                h.update(fold(rows, L, ALL, lam, alpha))
            res.append((pct(h), label, lam, alpha))
            print("  %-32s %6.1f%%  on n=%d" % (label, pct(h), len(h)))
        ctl = res[0][0]
        ranked = sorted(res[1:], reverse=True)
        best_s, best_label, best_lam, best_alpha = ranked[0]
        print("\n  control %.1f%%, chosen %s at %.1f%%" % (ctl, best_label, best_s))
        print("  That is the best of eight and is biased upward. The confirm run is the finding.")
        print("\n  next: python3 bt2_recency_exp.py confirm %r %s %s"
              % (best_label, best_lam, best_alpha))
        return

    best_label, best_lam, best_alpha = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])

    print("\n=== CONFIRM: the 2024 and 2025 folds, which took no part in the choice ===")
    print("  %-32s %9s %9s" % ("", "2024", "2025"))
    keep = {}
    for label, lam, alpha in (("control, no weighting", 0.0, 1.0), (best_label, best_lam, best_alpha)):
        cells, h = [], {}
        for L in CONFIRM:
            f = fold(rows, L, ALL, lam, alpha)
            cells.append(pct(f))
            h.update(f)
        keep[label] = h
        print("  %-32s %8.1f%% %8.1f%%" % (label, cells[0], cells[1]))

    print("\n=== if it stands: the full six-cohort control, and by segment ===")
    seg = [("short-haul, domestic or LCC",
            lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")),
           ("long-haul, international, full-service",
            lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC")]
    print("  %-40s %8s %11s %11s" % ("", "n", "control", "weighted"))
    full = {}
    for label, lam, alpha in (("control", 0.0, 1.0), ("weighted", best_lam, best_alpha)):
        h = {}
        for L in ALL:
            h.update(fold(rows, L, ALL, lam, alpha))
        full[label] = h
    print("  %-40s %8d %10.1f%% %10.1f%%"
          % ("all launches", len(full["control"]), pct(full["control"]), pct(full["weighted"])))
    for label, fn in seg:
        a = {k: v for k, v in full["control"].items() if fn(v[1])}
        b = {k: v for k, v in full["weighted"].items() if fn(v[1])}
        print("  %-40s %8d %10.1f%% %10.1f%%" % (label, len(a), pct(a), pct(b)))


if __name__ == "__main__":
    main()
