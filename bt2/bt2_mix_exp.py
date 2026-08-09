#!/usr/bin/env python3
r"""Point of sale and cabin mix as BT2 features, and does either NARROW the error. 9 August 2026.

    python3 bt2_mix_exp.py            all arms
    python3 bt2_mix_exp.py pos cab    named arms, when a run has to be split

THE TEST HAS CHANGED SHAPE, and that is the point. Every earlier arm today was judged on the hit
rate within +-20%. The width analysis showed why that kept coming out flat: on the long-haul
international full-service segment the blind log error has a robust sigma of 0.424 against 0.187 on
the short-haul segment, and BOTH are already centred, so perfectly centring the hard segment changes
its hit rate by nothing. Reaching 50% there needs the spread cut by 36%. So this run reports the
robust sigma beside the hit rate, and a feature that narrows sigma is worth something even if the
hit rate has not caught up yet.

WHAT IS BEING ADDED, and why it is the last family that could plausibly narrow rather than shift.
Everything tested so far describes how MUCH demand exists. These describe what KIND it is, which is
what separates two markets of the same size that behave differently.

  pos   the pre-launch market's point of sale: the share sold at each end, order-normalised so the
        pair's direction does not matter, the share sold in a third country, and the imbalance
        between the two ends. A market sold entirely at one end is a different proposition from a
        balanced one, and a market sold mostly in third countries is connecting demand that a new
        nonstop may not capture at all
  cab   premium share of the pre-launch market, business plus first plus premium coach

Read from year L-1, so nothing here is knowable only after launch. Coverage is 3,823 of 3,823 pairs.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
import os
import statistics
import sys
from math import comb

import numpy as np

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_lib as B          # noqa: E402
import bt2_g12_exp as F      # noqa: E402
from bt2_paths import BT2    # noqa: E402

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
NAN = float("nan")
TOL = math.log(1.2)


def attach(rows):
    mix = {}
    p = "%s/demand_mix.csv" % BT2
    for r in csv.DictReader(open(p, newline="", encoding="utf-8-sig")):
        mix[(r["a"], r["b"], int(r["pre_year"]))] = r
    have = 0
    for r in rows:
        c = mix.get((r["a"], r["b"], r["cohort"] - 1))
        r["_mix"] = c
        if c:
            have += 1
    print("demand mix on %d of %d launches (%.1f%%)" % (have, len(rows), 100.0 * have / len(rows)))


def _f(c, k):
    try:
        v = float(c[k])
        return v
    except (TypeError, ValueError, KeyError):
        return NAN


def extra_of(r, arms):
    c = r.get("_mix")
    v = []
    if "pos" in arms:
        if c:
            sa, sb = _f(c, "pos_share_a"), _f(c, "pos_share_b")
            v += [min(sa, sb), max(sa, sb), _f(c, "pos_share_third"), _f(c, "pos_imbalance")]
        else:
            v += [NAN] * 4
    if "cab" in arms:
        v.append(_f(c, "premium_share") if c else NAN)
    return v


def X_of(rs, arms):
    x = F.X_of(rs, G12)
    if not arms:
        return x
    return np.hstack([x, np.array([extra_of(r, arms) for r in rs])])


def blind(rows, arms):
    """Returns {route: (log ratio, row)} so both the hit rate and the width can be read off it."""
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(X_of(tr, arms), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, arms))):
            f = r["seats_ly"] * math.exp(p)
            if f > 0 and r["actual"] > 0:
                out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                    (math.log(f / r["actual"]), r)
    return out


def within20(x):
    """The published band, |forecast/actual - 1| <= 0.20, which is the ratio range 0.80 to 1.20.

    Corrected 9 August 2026. The first version of this file scored |log(f/a)| <= log(1.2), which is
    the range 0.833 to 1.20: symmetric in logs, tighter on the low side, and NOT the basis every
    other number in the programme and the client-facing claim are measured on. It read the control
    at 51.3% against its true 55.9% and at 32.8% on the hard segment against 36.5%. The arm-versus-
    control comparison was unaffected because both sides used the same rule, but the levels were not
    comparable with anything else, which is how a scoring basis quietly drifts.
    """
    return abs(math.exp(x) - 1.0) <= 0.20


def stats(h):
    xs = [v[0] for v in h.values()]
    if not xs:
        return 0.0, 0.0
    med = statistics.median(xs)
    # The width stays in logs, where it is symmetric and comparable across segments of different
    # size. Only the hit rate has to be on the published band.
    sig = statistics.median([abs(x - med) for x in xs]) * 1.4826
    return 100.0 * sum(1 for x in xs if within20(x)) / len(xs), sig


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if not within20(a[k][0]) and within20(b[k][0]))
    n10 = sum(1 for k in ks if within20(a[k][0]) and not within20(b[k][0]))
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


HARD = lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"
EASY = lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")


def main():
    want = sys.argv[1:] or ["pos", "cab", "both"]
    rows = G.rows
    F.attach(rows)
    attach(rows)
    ctl = blind(rows, None)
    ek = {k for k, v in ctl.items() if EASY(v[1])}
    hk = {k for k, v in ctl.items() if HARD(v[1])}

    print("\n=== blind LOCO, n=%d. sigma is the robust width; lower is the thing we need ===" % len(ctl))
    print("  %-24s %16s %26s   %s"
          % ("", "ALL", "hard segment, n=%d" % len(hk), "against control"))
    print("  %-24s %8s %7s %13s %12s" % ("", "+-20%", "sigma", "+-20%", "sigma"))

    def line(label, h, base=None):
        aH, aS = stats(h)
        d = {k: v for k, v in h.items() if k in hk}
        dH, dS = stats(d)
        tail = ""
        if base is not None:
            g, l, p = mcnemar(base, h)
            tail = "+%-4d -%-4d p=%.4f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
        print("  %-24s %7.1f%% %7.3f %12.1f%% %12.3f   %s" % (label, aH, aS, dH, dS, tail))

    line("G12 control", ctl)
    names = {"pos": "+ point of sale", "cab": "+ premium share", "both": "+ both"}
    for a in want:
        arms = ["pos", "cab"] if a == "both" else [a]
        line(names[a], blind(rows, arms), ctl)


if __name__ == "__main__":
    main()
