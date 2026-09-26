#!/usr/bin/env python3
r"""Fix option 2 scored on the record: a market ceiling on the model's local leg. W10, September 2026.

    AVIA_BT2_DIR=E:\Avia\bt2_relaxed  py -3.12 -s bt2_ceiling_test.py

The model's passengers scale one for one with seats (log line W10-RECORD-MIX-RELAXED), so Optimise
cannot ask it what a market supports. Option 2 in routes/W10-STATUS.md caps the model's local figure
at a share of the pair's existing O&D: ceiling = share_p75(class) x base_mkt, forecast = min(model,
ceiling). This script measures what that cap costs the record, honestly:

  BLIND      leave-one-cohort-out with the blind configuration; the share_p75 table is fitted on the
             training cohorts only, never on the held-out one.
  IN-SAMPLE  the blind configuration fitted on all rows (the estimator the app runs) and the share
             table from all rows, which is what the shipped table would be.

Both are printed with and without the cap, within +-20% and +-10%, whole sample and by haul, plus how
many rows the cap touched. The class is the region pair for long-haul international launches where
the training fold holds at least 50 of them, otherwise (haul, market-size band). Nothing is written.

Avia Solutions Limited. All rights reserved.
"""
import math
import statistics
from collections import defaultdict

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_claimset import _provenance, SPEC, G12, BLIND_KW
from bt2_record_mix import region_pair
from bt2_score import within

MIN_CLASS = 50


def klass(r, counts):
    if r["gcd"] >= 2500 and not r["dom"]:
        rp = region_pair(r)
        if counts.get(("rp", rp), 0) >= MIN_CLASS:
            return ("rp", rp)
    return ("hs", "short" if r["gcd"] < 2500 else "long", B.size_band(r["base_mkt"]))


def share_table(train):
    counts = defaultdict(int)
    for r in train:
        if r["gcd"] >= 2500 and not r["dom"]:
            counts[("rp", region_pair(r))] += 1
    g = defaultdict(list)
    for r in train:
        g[klass(r, counts)].append(r["actual"] / r["base_mkt"])
    tab = {}
    for k, v in g.items():
        v = sorted(v)
        tab[k] = v[min(len(v) - 1, int(0.75 * len(v)))]
    allv = sorted(r["actual"] / r["base_mkt"] for r in train)
    return counts, tab, allv[int(0.75 * len(allv))]


def capped(r, fc, counts, tab, fallback):
    c = tab.get(klass(r, counts), fallback) * r["base_mkt"]
    return min(fc, c), fc > c


def report(label, rows, raw, cap, touched):
    def w(v, t):
        return 100.0 * sum(1 for x in v if within(x, t)) / len(v)
    rr = [f / r["actual"] for f, r in zip(raw, rows)]
    cc = [f / r["actual"] for f, r in zip(cap, rows)]
    print("  %-34s n=%5d  raw %5.1f / %5.1f   capped %5.1f / %5.1f   touched %4.1f%%"
          % (label, len(rows), w(rr, .2), w(rr, .1), w(cc, .2), w(cc, .1),
             100.0 * sum(touched) / len(touched)))
    for name, fn in (("short-haul", lambda r: r["gcd"] < 2500), ("long-haul", lambda r: r["gcd"] >= 2500),
                     ("long-haul EU-NA", lambda r: r["gcd"] >= 2500 and region_pair(r) == "EU-NA"),
                     ("market over 25k", lambda r: r["base_mkt"] >= 25000)):
        idx = [i for i, r in enumerate(rows) if fn(r)]
        if not idx:
            continue
        r2 = [rr[i] for i in idx]; c2 = [cc[i] for i in idx]; t2 = [touched[i] for i in idx]
        print("    %-32s n=%5d  raw %5.1f / %5.1f   capped %5.1f / %5.1f   touched %4.1f%%"
              % (name, len(idx), w(r2, .2), w(r2, .1), w(c2, .2), w(c2, .1), 100.0 * sum(t2) / len(t2)))


def main():
    rows = G.rows
    F.attach(rows)
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("target: %s   build: %s" % (B.TARGET, _provenance()))
    print("cap: forecast = min(model, share_p75(class) x base_mkt); class = region pair for long-haul "
          "international with >= %d training launches, else (haul, market band)\n" % MIN_CLASS)

    print("=== BLIND, leave one cohort out; share table fitted on the training cohorts only ===")
    out_rows, raw, cap, touched = [], [], [], []
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **BLIND_KW)
        m.fit(F.X_of(tr, G12), G.y_of(tr))
        counts, tab, fb = share_table(tr)
        for r, p in zip(te, m.predict(F.X_of(te, G12))):
            f = r["seats_ly"] * math.exp(p)
            c, t = capped(r, f, counts, tab, fb)
            out_rows.append(r); raw.append(f); cap.append(c); touched.append(t)
    report("blind route level", out_rows, raw, cap, touched)

    print("\n=== IN-SAMPLE, the blind configuration on all rows (the estimator the app runs); table from all rows ===")
    m = G.make(SPEC, **BLIND_KW)
    m.fit(F.X_of(rows, G12), G.y_of(rows))
    counts, tab, fb = share_table(rows)
    raw2 = [r["seats_ly"] * math.exp(p) for r, p in zip(rows, m.predict(F.X_of(rows, G12)))]
    cap2, t2 = zip(*(capped(r, f, counts, tab, fb) for r, f in zip(rows, raw2)))
    report("in-sample", rows, raw2, list(cap2), list(t2))

    print("\n=== THE SHIPPED TABLE (all rows): class, n, share_p75 ===")
    g = defaultdict(int)
    for r in rows:
        g[klass(r, counts)] += 1
    for k in sorted(tab, key=lambda k: -g[k]):
        print("  %-32s n=%5d  share_p75 %.3f" % (" ".join(str(x) for x in k[1:]), g[k], tab[k]))


if __name__ == "__main__":
    main()
