#!/usr/bin/env python3
r"""The full claim set on whichever sample AVIA_BT2_DIR points at. 9 August 2026.

    AVIA_BT2_DIR=C:\Avia\bt2          python3 bt2_claimset.py     the canon
    AVIA_BT2_DIR=C:\Avia\bt2_relaxed  python3 bt2_claimset.py     the relaxed sample

Produces every figure the claim structure rests on, from one sample, so the two populations can be
compared line for line rather than by pulling numbers from different runs on different bases.

  fitted            the calibrated figure, history known. Within +-20% and within +-10%
  blind             leave-one-cohort-out, route level
  tier A            blind, on the narrowest tenth of predicted spread, identified in advance
  portfolios of 20  blind, random baskets of twenty within a cohort, which is the published 94%

THE FITTED CONFIG WAS NEVER COMMITTED, and that is worth stating plainly because the fitted figure
is the one on the website. It has been reconstructed here against its published value: on the sample
it was published on, n=2,915 over cohorts 2016-2019 and 2025, this config returns 89.2% within +-20%
and 81.4% within +-10% against a published 89.8% and 82.5%.

AND THE FITTED FIGURE IS MOSTLY A CHOICE. On that same sample, the regularisation alone moves it
from 72.1% to 93.8%: lighter leaves and no l2 buy as much as the model does. A calibrated number is
therefore a statement about how hard the model was allowed to fit its own history, not a property of
the forecast, which is why it must never travel without the word calibrated attached and why the
blind figures are the ones that carry information.

Avia Solutions Limited. All rights reserved.
"""
import math
import random
import statistics
from collections import defaultdict

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_score import within

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
BLIND_KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
FITTED_KW = dict(lr=0.06, it=800, minleaf=5, l2=0.0, leaves=63)   # reconstructed, see docstring


def main():
    rows = G.rows
    F.attach(rows)
    print("\nsample: n=%d, cohorts %s, from %s"
          % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))

    X, y = F.X_of(rows, G12), G.y_of(rows)
    m = G.make(SPEC, **FITTED_KW)
    m.fit(X, y)
    fr = [r["seats_ly"] * math.exp(p) / r["actual"] for r, p in zip(rows, m.predict(X))]
    print("\n  CALIBRATED, history known")
    print("    within +-20%%      %5.1f%%" % (100.0 * sum(1 for x in fr if within(x)) / len(fr)))
    print("    within +-10%%      %5.1f%%" % (100.0 * sum(1 for x in fr if within(x, 0.10)) / len(fr)))

    out = []
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        Xtr, ytr, Xte = F.X_of(tr, G12), G.y_of(tr), F.X_of(te, G12)
        q = {}
        for qq, nm in ((0.5, "p50"), (0.25, "p25"), (0.75, "p75")):
            mm = G.make(SPEC, **BLIND_KW)
            mm.set_params(quantile=qq)
            mm.fit(Xtr, ytr)
            q[nm] = mm.predict(Xte)
        for i, r in enumerate(te):
            f = r["seats_ly"] * math.exp(q["p50"][i])
            if f > 0 and r["actual"] > 0:
                out.append({"c": L, "fc": f, "act": r["actual"], "ratio": f / r["actual"],
                            "iqr": float(q["p75"][i] - q["p25"][i])})

    print("\n  BLIND, leave one cohort out")
    print("    route level       %5.1f%%   n=%d"
          % (100.0 * sum(1 for o in out if within(o["ratio"])) / len(out), len(out)))

    cut = sorted(o["iqr"] for o in out)[len(out) // 10]
    tier = [o for o in out if o["iqr"] <= cut]
    print("    tier A            %5.1f%%   n=%d, the narrowest tenth of predicted spread"
          % (100.0 * sum(1 for o in tier if within(o["ratio"])) / len(tier), len(tier)))

    for n in (10, 20):
        random.seed(11)
        groups = []
        for L in B.COHORTS:
            co = [o for o in out if o["c"] == L]
            random.shuffle(co)
            groups += [co[i:i + n] for i in range(0, len(co), n) if len(co[i:i + n]) == n]
        sh = []
        for g in groups:
            A = sum(o["act"] for o in g)
            if A > 0:
                sh.append(sum(o["fc"] for o in g) / A)
        print("    portfolios of %-2d  %5.1f%%   %d baskets"
              % (n, 100.0 * sum(1 for x in sh if within(x)) / len(sh), len(sh)))

    print("\n  BY SEGMENT, blind")
    seg = [("short-haul, domestic or LCC", lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")),
           ("long-haul, international, FSC", lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC")]
    idx = {id(r): i for i, r in enumerate(rows)}
    byrow = {}
    k = 0
    for L in B.COHORTS:
        for r in [x for x in rows if x["cohort"] == L]:
            byrow[k] = r
            k += 1
    # rebuild the row alignment simply, by recomputing the segment from the same ordering
    order = [r for L in B.COHORTS for r in rows if r["cohort"] == L]
    order = [r for r in order if r["actual"] > 0 and r["seats_ly"] > 0]
    for label, fn in seg:
        v = [o["ratio"] for o, r in zip(out, order) if fn(r)]
        if v:
            print("    %-30s %5.1f%%   n=%d"
                  % (label, 100.0 * sum(1 for x in v if within(x)) / len(v), len(v)))


if __name__ == "__main__":
    main()
