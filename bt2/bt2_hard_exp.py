#!/usr/bin/env python3
r"""The long-haul international full-service segment, taken on its own. 9 August 2026.

    python3 bt2_hard_exp.py

WHY. The whole shortfall lives here. At the standing G12 configuration the segment rule splits blind
accuracy 70.4% on short-haul domestic or low-cost launches against 36.5% on long-haul international
full-service, and the pooled 55.9% is the average of the two. Nothing tried today moves the second
number at the whole-sample level, but a pattern has appeared and it is worth taking seriously rather
than reporting six times as noise:

  connection components   36.5% -> 37.8% on the hard segment (p=0.161 when the segment was scored
                          from the whole-sample fit)
  country presence        36.5% -> 37.5%
  carrier network size    36.5% -> 37.0%
  opens a new country     36.5% -> 37.3%
  all network arms        36.5% -> 37.8%

Every one positive, none of them measurable alone on 1,090 routes. Two explanations fit that, and
they call for different work. Either they are five draws of the same noise, or they are real and
each too small to see, in which case putting them together and giving the segment its own model is
the way to see them.

FOUR ARMS.

  H0  the shared G12 model, scored on the hard segment. The control, and the current 36.5%
  H1  a model trained ONLY on hard-segment launches, same G12 features. Tests whether the segment
      is being crowded out by the 2,610 launches that are not like it
  H2  H1 plus the connection components and the network reach features together
  H3  the shared model plus those same extras, scored on the segment

If H1 beats H0 the segment needs its own model. If H3 beats H0 and H1 does not, the features carry
the signal and the shared fit is fine. If neither moves, the five positives above were noise and the
segment's error is the market rather than the model.

Everything is blind leave-one-cohort-out and paired on identical routes.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
from math import comb

import numpy as np

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G              # noqa: E402
import bt2_lib as B              # noqa: E402
import bt2_g12_exp as F          # noqa: E402
import bt2_feed_exp as FE        # noqa: E402
import bt2_network_exp as NE     # noqa: E402

SPEC = ["car", "qcx", "gro"]
G12 = ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
# A model trained on 1,090 launches instead of 3,700 needs the regularisation it was given at that
# size, not the setting tuned on the larger set. Stated here rather than discovered later.
KW_SMALL = dict(lr=0.04, it=600, minleaf=30, l2=5.0)

NET = ["ctry", "sys", "new"]


def HARD(r):
    return r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"


def key(r):
    return "%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])


def X_of(rs, extras):
    x = F.X_of(rs, G12)
    if not extras:
        return x
    add = []
    for r in rs:
        v = []
        if "feed" in extras:
            v += FE.extra_of(r, ["cmp", "asym", "fgain"])
        if "net" in extras:
            v += NE.extra_of(r, NET)
        add.append(v)
    return np.hstack([x, np.array(add)])


def blind(rows, score_rows, extras, kw):
    """LOCO. rows is the training pool, score_rows the launches scored."""
    sk = {key(r) for r in score_rows}
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in score_rows if r["cohort"] == L]
        if not te or len(tr) < 50:
            continue
        m = G.make(SPEC, **kw)
        m.fit(X_of(tr, extras), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, extras))):
            f = r["seats_ly"] * math.exp(p)
            if key(r) in sk:
                out[key(r)] = abs(f / r["actual"] - 1) <= 0.20
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


def main():
    rows = G.rows
    F.attach(rows)
    FE.attach(rows, FE.load_components())
    NE.attach_network(rows)
    hard = [r for r in rows if HARD(r)]
    print("hard segment: %d of %d launches" % (len(hard), len(rows)))

    arms = [
        ("H0  shared model, G12", rows, None, KW),
        ("H1  hard-only model", hard, None, KW_SMALL),
        ("H2  hard-only + feed + network", hard, ["feed", "net"], KW_SMALL),
        ("H3  shared + feed + network", rows, ["feed", "net"], KW),
    ]
    base = None
    print("\n=== blind LOCO on the hard segment, n=%d ===" % len(hard))
    print("  %-34s %9s   %s" % ("", "+-20%", "against H0"))
    for label, pool, extras, kw in arms:
        h = blind(pool, hard, extras, kw)
        if base is None:
            base = h
            print("  %-34s %8.1f%%" % (label, 100.0 * sum(h.values()) / len(h)))
            continue
        g, l, p = mcnemar(base, h)
        print("  %-34s %8.1f%%   +%-3d -%-3d p=%.4f%s"
              % (label, 100.0 * sum(h.values()) / len(h), g, l, p,
                 "" if p < 0.05 else "  NOT MEASURABLE"))


if __name__ == "__main__":
    main()
