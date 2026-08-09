#!/usr/bin/env python3
r"""What makes tier B and C hard: model error, or the ruler?

    AVIA_BT2_COHORTS=2016,2017,2018,2019,2024,2025 python3 bt2_tier_diagnose.py

John's question of 9 August 2026, and it is the right one: if tier A reaches 75% blind, what stops
tier B and C being lifted too. The answer decides whether there is work to do or a claim to write.

Tier A is not a tier that was improved. It is the tenth of routes where the model's OWN predicted
spread is narrowest, chosen in advance. It scores high because those are the routes it already knew
it could call. So the diagnostic question is not "how do we lift tier C" but "what is tier C's
error made of":

  * a DIRECTION and a segment signature, meaning the model reads a named kind of route wrong, which
    is fixable by correcting that mechanism. This is the method that worked on the airport bias
    work: diagnose the signature, correct the named mechanism, never apply a blanket factor.
  * SYMMETRIC spread around 1.0 with no signature, meaning the outturn itself is uncertain at that
    size. On the 381 US routes where the outturn can be measured twice, Sabre and DOT agree within
    +-20% on only 64% (bt2_experiments.log line 43, 5 August 2026). Below some route size the
    measurement is the limit and no feature recovers it.

Everything here is BLIND, leave-one-cohort-out, including the predicted spread that defines the
tier: a tier cut fitted on the routes it is scored on would be a fitted number wearing a tier's
name.

Avia Solutions Limited. All rights reserved.
"""
import math
import statistics
from collections import Counter

import bt2_gbm as G
import bt2_lib as B

SPEC = ["car", "qcx", "gro"]
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)


def blind_predictions():
    """Per route, blind: forecast, actual, and the predicted log-IQR that defines the tier."""
    out = []
    for L in B.COHORTS:
        tr = [r for r in G.rows if r["cohort"] != L]
        te = [r for r in G.rows if r["cohort"] == L]
        Xtr, ytr, Xte = G.X_of(tr, SPEC), G.y_of(tr), G.X_of(te, SPEC)
        p = {}
        for q, nm in ((0.5, "q50"), (0.25, "q25"), (0.75, "q75")):
            m = G.make(SPEC, **KW)
            m.set_params(quantile=q)
            m.fit(Xtr, ytr)
            p[nm] = m.predict(Xte)
        for i, r in enumerate(te):
            f = r["seats_ly"] * math.exp(p["q50"][i])
            if r["actual"] <= 0 or f <= 0:
                continue
            out.append({"r": r, "fc": f, "act": r["actual"],
                        "ratio": f / r["actual"], "iqr": float(p["q75"][i] - p["q25"][i])})
    return out


def decile(vals, x):
    return sum(1 for v in vals if v < x) * 10 // max(1, len(vals))


def main():
    rows = blind_predictions()
    print("blind predictions on %d launches, cohorts %s"
          % (len(rows), ",".join(str(c) for c in B.COHORTS)))
    iqrs = sorted(d["iqr"] for d in rows)

    print("\n=== by decile of predicted spread, narrowest first. Tier A is decile 1 ===")
    print("  %-8s %6s %9s %9s %11s %11s %10s"
          % ("decile", "n", "+-20%", "median", "median pax", "median seats", "share |r-1|>0.5"))
    groups = {}
    for d in rows:
        groups.setdefault(decile(iqrs, d["iqr"]), []).append(d)
    for k in sorted(groups):
        g = groups[k]
        rs = [x["ratio"] for x in g]
        w20 = 100.0 * sum(1 for x in rs if abs(x - 1) <= 0.20) / len(rs)
        big = 100.0 * sum(1 for x in rs if abs(x - 1) > 0.50) / len(rs)
        print("  %-8d %6d %8.1f%% %9.2f %11.0f %11.0f %9.1f%%"
              % (k + 1, len(g), w20, statistics.median(rs),
                 statistics.median([x["act"] for x in g]),
                 statistics.median([x["r"]["seats_ly"] for x in g]), big))

    print("\n  READ THE MEDIAN COLUMN. A median away from 1.00 in a decile is a DIRECTION and a")
    print("  mechanism to name. A median at 1.00 with a wide tail is spread, not bias, and no")
    print("  correction moves it.")

    wide = [d for d in rows if decile(iqrs, d["iqr"]) >= 7]
    narrow = [d for d in rows if decile(iqrs, d["iqr"]) <= 2]
    print("\n=== what the widest three deciles are made of, against the narrowest three ===")
    print("  %-22s %14s %14s" % ("", "narrowest 30%", "widest 30%"))

    def line(label, fn):
        a = [fn(d) for d in narrow if fn(d) is not None]
        b = [fn(d) for d in wide if fn(d) is not None]
        print("  %-22s %14.0f %14.0f" % (label, statistics.median(a), statistics.median(b)))

    line("median outturn pax", lambda d: d["act"])
    line("median planned seats", lambda d: d["r"]["seats_ly"])
    line("median base market", lambda d: d["r"]["base_mkt"])
    line("median gcd km", lambda d: d["r"]["gcd"])
    line("median weekly freq", lambda d: d["r"]["freq"])
    for label, key in (("LCC share", "typ"), ("domestic share", "dom")):
        a = 100.0 * sum(1 for d in narrow if (d["r"][key] == "LCC" if key == "typ" else d["r"][key])) / len(narrow)
        b = 100.0 * sum(1 for d in wide if (d["r"][key] == "LCC" if key == "typ" else d["r"][key])) / len(wide)
        print("  %-22s %13.0f%% %13.0f%%" % (label, a, b))

    print("\n=== the size question, which is where the ruler argument lives ===")
    print("  %-18s %6s %9s %9s" % ("outturn pax", "n", "+-20%", "median ratio"))
    bands = [(0, 5000), (5000, 15000), (15000, 40000), (40000, 100000), (100000, 10 ** 12)]
    for lo, hi in bands:
        g = [d for d in rows if lo <= d["act"] < hi]
        if not g:
            continue
        rs = [x["ratio"] for x in g]
        print("  %-18s %6d %8.1f%% %9.2f"
              % ("%s-%s" % (format(lo, ","), "+" if hi > 10 ** 11 else format(hi, ",")),
                 len(g), 100.0 * sum(1 for x in rs if abs(x - 1) <= 0.20) / len(rs),
                 statistics.median(rs)))

    print("\n  If the hit rate climbs with route size while the median stays near 1.00, the small")
    print("  end is spread rather than bias, and the honest product answer on a thin route is a")
    print("  band with the tier stated, not a point forecast anyone should trade on.")

    print("\n=== carriers most often in the widest 30%, where n>=15 in sample ===")
    cw = Counter(d["r"]["oag_carrier"] for d in wide)
    ca = Counter(d["r"]["oag_carrier"] for d in rows)
    over = [(cw[c] / ca[c], c, ca[c]) for c in ca if ca[c] >= 15]
    over.sort(reverse=True)
    for share, c, n in over[:8]:
        print("    %-5s %3d launches, %.0f%% of them in the widest 30%%" % (c, n, 100 * share))


if __name__ == "__main__":
    main()
