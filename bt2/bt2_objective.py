#!/usr/bin/env python3
r"""BT2 forecasts the median. The claim is scored on a band. Those are not the same target.

    python3 bt2_objective.py shift      the fixed, derived shift
    python3 bt2_objective.py window     the per-route window placement, needs the quantile cache

A DIFFERENT KIND OF IDEA FROM THE REST OF 9 AUGUST. Every other arm that day added information.
This one adds none and changes what the model is aiming at, which is worth trying precisely because
twenty-five attempts to add information moved nothing.

BT2 fits a quantile regression at 0.5, so it returns the median of the predicted distribution of
O&D per seat. The claim is scored on whether the forecast lands within +-20% of the outturn. Those
ask for different numbers, and the gap is not a rounding matter:

    within +-20% means  |f/A - 1| <= 0.20,  so  A in [f/1.2, f/0.8]

Writing f = seats.exp(m) and A = seats.exp(Z), the route is a hit when

    Z in [m - log(1.2), m + log(1.25)]  =  [m - 0.1823, m + 0.2231]

THE BAND IS ASYMMETRIC IN LOGS. It is wider above than below, because being 20% under the outturn
and 20% over it are not the same distance in ratio terms. The window's midpoint is m + 0.0204, so a
forecast placed at the median of Z puts the median 0.0204 ABOVE the centre of its own scoring
window, and gives away coverage on every route. The correction is to forecast at

    median - 0.0204,  a multiplier of exp(-0.0204) = 0.9798

This is DERIVED, not fitted. It comes from the definition of the band and nothing else, so there is
no grid, no selection, and no best-of-N to discount. The curve over other multipliers is printed for
information and is explicitly not where the recommended value comes from.

The window arm goes further and places the window per route rather than globally, using nine
predicted quantiles to find the placement that captures the most mass for that route's own skew.
Same objective, adapted rather than fixed.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import sys
from math import comb

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_lib as B          # noqa: E402
import bt2_g12_exp as F      # noqa: E402

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)

# CORRECTED 9 August 2026. The first version of this file wrote the band as [-log(1.2), +log(1.25)],
# which is the real band inverted: wide above instead of wide below. It read the control at 54.2%
# against its true 55.9% and made the derived shift appear to point upward. The band now comes from
# bt2_score, which is the only place it is written down and which self-tests the asymmetry.
from bt2_score import LOG_LO, LOG_HI, MID, within_log, rate_log
DERIVED = MID              # -0.02041, the window centre, and the shift that puts the median on it

HARD = lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"
EASY = lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")


def base_predictions():
    """Blind LOCO median forecasts. Returns [(row, log(f/actual))]."""
    out = []
    for L in B.COHORTS:
        tr = [r for r in G.rows if r["cohort"] != L]
        te = [r for r in G.rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(F.X_of(tr, G12), G.y_of(tr))
        for r, p in zip(te, m.predict(F.X_of(te, G12))):
            f = r["seats_ly"] * math.exp(p)
            if f > 0 and r["actual"] > 0:
                out.append((r, math.log(f / r["actual"])))
    return out


def hit(e, shift=0.0):
    """A hit when the log error, with the forecast multiplied by exp(shift), sits in the band."""
    return within_log(e, shift)


def mcnemar(pairs):
    n01 = sum(1 for a, b in pairs if not a and b)
    n10 = sum(1 for a, b in pairs if a and not b)
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def pct(es, shift=0.0):
    return rate_log(es, shift)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "shift"
    F.attach(G.rows)
    preds = base_predictions()
    alle = [e for _, e in preds]
    hard = [e for r, e in preds if HARD(r)]
    easy = [e for r, e in preds if EASY(r)]

    print("\n=== the band, written out ===")
    print("  a hit is log(f/A) in [%+.5f, %+.5f], midpoint %+.5f" % (LOG_LO, LOG_HI, MID))
    print("  the band is WIDER BELOW than above, so the window centre is below zero")
    print("  derived multiplier on the forecast: exp(%+.5f) = %.5f" % (MID, math.exp(MID)))

    print("\n=== blind LOCO, n=%d ===" % len(preds))
    print("  %-30s %9s %9s %9s   %s" % ("", "ALL", "easy", "hard", "against the median forecast"))
    print("  %-30s %8.1f%% %8.1f%% %8.1f%%" % ("median forecast, as shipped",
                                               pct(alle), pct(easy), pct(hard)))
    pairs = [(hit(e), hit(e, DERIVED)) for e in alle]
    g, l, p = mcnemar(pairs)
    print("  %-30s %8.1f%% %8.1f%% %8.1f%%   +%-4d -%-4d p=%.4f%s"
          % ("window-centred, x%.4f" % math.exp(DERIVED),
             pct(alle, DERIVED), pct(easy, DERIVED), pct(hard, DERIVED),
             g, l, p, "" if p < 0.05 else "  NOT MEASURABLE"))

    print("\n  for information only, and NOT where the recommendation comes from: the curve")
    print("  %-14s %9s" % ("multiplier", "ALL"))
    for k in (0.94, 0.96, 0.9798, 1.00, 1.02, 1.04, 1.06):
        print("  %-14.4f %8.1f%%%s" % (k, pct(alle, math.log(k)),
                                       "   <- derived" if abs(k - 0.9798) < 1e-6 else ""))


if __name__ == "__main__":
    main()
