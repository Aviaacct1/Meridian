#!/usr/bin/env python3
r"""What is in the tails of the long-haul segment, and does anything separate them. 9 August 2026.

    python3 bt2_tails.py            the hard segment
    python3 bt2_tails.py all        every launch

THE METHOD, and it is the one that worked on the airport bias. Do not guess another feature. Take
the routes the model gets badly wrong, split them by DIRECTION, and look for what the two tails have
that the routes in the band do not. A variable that separates the band from both tails identifies
routes that are hard. A variable that separates the two tails FROM EACH OTHER identifies a driver,
because it says which way the model will be wrong, and that is the thing a correction can use.

The arithmetic that makes this worth doing: the long-haul international full-service segment is
1,090 of 3,700 launches and scores 38.2%. Taking it to 50% with the rest held takes the pooled blind
figure from 55.9% to 59.9%. The whole remaining gap is in this one segment.

TAILS ARE CUT ON THE RATIO, so over-read and under-read are separated rather than pooled into an
absolute error that hides the direction.

  over    forecast at least 1.5x the outturn
  under   forecast at most 0.67x the outturn
  band    within +-20%

EVERY VARIABLE HERE IS KNOWN BEFORE LAUNCH. A separator that needs the outturn is not a driver, it
is the answer, and the size-calibration trap earlier today came from exactly that mistake.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import statistics
import sys
from collections import Counter

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G              # noqa: E402
import bt2_lib as B              # noqa: E402
import bt2_g12_exp as F          # noqa: E402
import bt2_feed_exp as FE        # noqa: E402
import bt2_network_exp as NE     # noqa: E402

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)


def HARD(r):
    return r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"


def blind(rows):
    out = []
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(F.X_of(tr, G12), G.y_of(tr))
        for r, p in zip(te, m.predict(F.X_of(te, G12))):
            f = r["seats_ly"] * math.exp(p)
            if r["actual"] > 0 and f > 0:
                out.append((r, f / r["actual"]))
    return out


def sep(a, b):
    """Standardised difference between two groups, so variables on different scales compare.
    Not a p-value: with these group sizes a p-value would mostly measure the group size."""
    if len(a) < 8 or len(b) < 8:
        return 0.0
    ma, mb = statistics.mean(a), statistics.mean(b)
    va, vb = statistics.pvariance(a), statistics.pvariance(b)
    s = math.sqrt((va + vb) / 2) or 1e-9
    return (mb - ma) / s


# All read before launch. The lambda returns None when the value is not available for that launch,
# and Nones are dropped rather than replaced, per flag rather than fill.
VARS = [
    ("planned seats (log)",        lambda r: math.log(r["seats_ly"]) if r["seats_ly"] > 0 else None),
    ("base market (log)",          lambda r: math.log(r["base_mkt"]) if r["base_mkt"] > 0 else None),
    ("seats over base market",     lambda r: math.log(r["seats_ly"] / r["base_mkt"]) if r["base_mkt"] > 0 else None),
    ("gcd km (log)",               lambda r: math.log(max(r["gcd"], 100))),
    ("weekly frequency",           lambda r: r["freq"]),
    ("gauge, seats per op",        lambda r: r["gauge"] or None),
    ("months operated",            lambda r: float(r["months"])),
    ("QSI capture at actual freq", lambda r: r["capa"]),
    ("capture at freq 5",          lambda r: r["cap5"]),
    ("schedule density, legs",     lambda r: math.log1p(r["legs_n"])),
    ("connection competition qcx", lambda r: math.log1p(r["qcx"])),
    ("carriers on the pair",       lambda r: float(r["ncar"])),
    ("market growth L-2 to L-1",   lambda r: math.log(max(min(r["mkt_growth"], 5.0), 0.2))),
    ("launch month",               lambda r: float(r["launch_month"][5:7])),
    ("base seats, smaller end",    lambda r: math.log1p(min(r["_base"][0], r["_base"][1])) if r.get("_base") else None),
    ("base share, smaller end",    lambda r: min(r["_base"][0] / r["_base"][2] if r["_base"][2] else 0,
                                                 r["_base"][1] / r["_base"][3] if r["_base"][3] else 0) if r.get("_base") else None),
    ("carrier country seats",      lambda r: math.log1p(min(r["_net"]["sa"], r["_net"]["sb"])) if r.get("_net") else None),
    ("carrier system seats",       lambda r: math.log1p(r["_net"]["sys"]) if r.get("_net") else None),
    ("feed asymmetry",             lambda r: r.get("_asym")),
    ("capture gain from freq",     lambda r: math.log(r["_fgain"]) if r.get("_fgain") and r["_fgain"] > 0 else None),
]


def main():
    rows = G.rows
    F.attach(rows)
    FE.attach(rows, FE.load_components())
    NE.attach_network(rows)
    pool = rows if (len(sys.argv) > 1 and sys.argv[1] == "all") else [r for r in rows if HARD(r)]
    scope = "every launch" if pool is rows else "the long-haul international full-service segment"

    preds = [(r, x) for r, x in blind(rows) if r in pool] if pool is not rows else blind(rows)
    over = [r for r, x in preds if x >= 1.5]
    under = [r for r, x in preds if x <= 0.67]
    band = [r for r, x in preds if abs(x - 1) <= 0.20]
    print("%s: %d launches. over-read %d, in band %d, under-read %d"
          % (scope, len(preds), len(over), len(band), len(under)))

    def col(fn, g):
        # NaN is dropped alongside None. A NaN reaching the variance would stop the run, and a
        # variable that is absent on some launches should narrow the sample, not end it.
        return [v for v in (fn(r) for r in g) if v is not None and v == v]

    print("\n=== medians, and how far each tail sits from the band ===")
    print("  %-28s %9s %9s %9s   %7s %7s"
          % ("", "over", "band", "under", "d over", "d under"))
    scored = []
    for label, fn in VARS:
        o, bd, u = col(fn, over), col(fn, band), col(fn, under)
        if min(len(o), len(bd), len(u)) < 8:
            continue
        do, du = sep(bd, o), sep(bd, u)
        scored.append((abs(do - du), label, do, du))
        print("  %-28s %9.2f %9.2f %9.2f   %+7.2f %+7.2f"
              % (label, statistics.median(o), statistics.median(bd), statistics.median(u), do, du))

    print("\n=== the separators. A variable that pushes the two tails APART is a driver, because")
    print("    it says which way the model will be wrong. One that moves both the same way only")
    print("    says the route is hard. ===")
    for gap, label, do, du in sorted(scored, reverse=True)[:8]:
        arrow = "SPLITS THE TAILS" if do * du < 0 else "both tails same way"
        print("  %-28s over %+5.2f  under %+5.2f  gap %4.2f   %s" % (label, do, du, gap, arrow))

    print("\n=== who is in each tail ===")
    for nm, g in (("over-read", over), ("under-read", under)):
        c = Counter(r["oag_carrier"] for r in g).most_common(6)
        print("  %-10s carriers: %s" % (nm, ", ".join("%s %d" % x for x in c)))
    for nm, g in (("over-read", over), ("under-read", under)):
        c = Counter("%s-%s" % tuple(sorted([r["ctry_a"], r["ctry_b"]])) for r in g).most_common(6)
        print("  %-10s country pairs: %s" % (nm, ", ".join("%s %d" % x for x in c)))


if __name__ == "__main__":
    main()
