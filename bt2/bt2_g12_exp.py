#!/usr/bin/env python3
r"""G12 on six cohorts: carrier base strength at the endpoints, plus the sister-airport flag.

    AVIA_BT2_COHORTS=2016,2017,2018,2019,2024,2025 python3 bt2_g12_exp.py

THE LAST KNOWN GAIN, banked. G11 and G12 measured these two additions on five cohorts and logged
them as KEPT: base strength took blind from 51.0% to 52.5%, and base strength with the sister flag
took the five-cohort control from 52.7% to 53.7% (bt2_experiments.log lines 46 and 47, 5 August
2026). Cohort 2024 was built on 9 August and neither addition had been run with it in.

WHAT THEY ARE, and both come from files already on disk rather than from a new pull.

  base strength  the launching carrier's own departing seats at each endpoint in the pre-launch
                 month, from base_strength_L.json, with that carrier's SHARE of all departing seats
                 at the same airport and month. An airline launching from a base it already
                 dominates is a different proposition from one launching into a stranger's airport.
  sister flag    whether the metro pair already had established nonstop service, taken as more than
                 1,500 passengers in L-1 on the metro pair, from metro_ns_L.json. bt2_metro's own
                 definition is used rather than a new one, so this reproduces rather than reinvents.

The sister flag is a DEMOTION signal, not an improvement: log line 45 records that the sister subset
scores 46.0% blind against 51.3% clean, so the flag tells the model which routes it will read badly
because the demand may land at the other airport in the metro.

Blind leave-one-cohort-out, paired on identical routes against the six-cohort G09 control.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import json
import math
import os
from collections import defaultdict
from math import comb

import numpy as np

import bt2_gbm as G
import bt2_lib as B
from bt2_paths import BT2

SPEC = ["car", "qcx", "gro"]
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)


def metro_map():
    import airportsdata
    ap = airportsdata.load("IATA")
    return {k: (v.get("city", "") or k, v.get("country", "")) for k, v in ap.items()}


def attach(rows):
    """Base strength and the sister flag, per launch, from the artifacts bt2_base and bt2_metro
    already wrote. Anything missing is left as None and counted, never filled with a zero that
    would read as 'this carrier has no base here' when it means 'no file'."""
    M = metro_map()
    bs, mm = {}, {}
    for L in B.COHORTS:
        pb = "%s/base_strength_%d.json" % (BT2, L)
        pm = "%s/metro_ns_%d.json" % (BT2, L)
        bs[L] = json.load(open(pb)) if os.path.exists(pb) else None
        mm[L] = json.load(open(pm)) if os.path.exists(pm) else None
        if bs[L] is None or mm[L] is None:
            print("  cohort %d: missing %s%s, reported not filled"
                  % (L, "base_strength " if bs[L] is None else "",
                     "metro_ns" if mm[L] is None else ""))

    # airport-month totals across all carriers, derived from the same file rather than re-queried
    tot = {L: defaultdict(float) for L in B.COHORTS}
    for L, d in bs.items():
        if not d:
            continue
        for k, v in d.items():
            car, ap_, wk = k.split("|")
            tot[L]["%s|%s" % (ap_, wk)] += v

    nb = ns = 0
    for r in rows:
        L, pm_ = r["cohort"], r["pre_month"]
        car = r["oag_carrier"]
        d = bs.get(L)
        if d:
            sa = d.get("%s|%s|%s" % (car, r["a"], pm_))
            sb = d.get("%s|%s|%s" % (car, r["b"], pm_))
            ta = tot[L].get("%s|%s" % (r["a"], pm_), 0.0)
            tb = tot[L].get("%s|%s" % (r["b"], pm_), 0.0)
            if sa is not None or sb is not None:
                nb += 1
            r["_base"] = (sa or 0.0, sb or 0.0, ta, tb)
        else:
            r["_base"] = None
        m = mm.get(L)
        if m:
            ma = M.get(r["a"], (r["a"], ""))
            mb = M.get(r["b"], (r["b"], ""))
            mk = "|".join(sorted(["%s|%s" % ma, "%s|%s" % mb]))
            prior = m.get(str(L - 1), {}).get(mk, 0.0)
            r["_sister"] = 1.0 if prior > 1500 else 0.0
            ns += int(r["_sister"])
        else:
            r["_sister"] = None
    print("base strength on %d of %d launches; sister flag set on %d"
          % (nb, len(rows), ns))


def extra_of(r, which):
    v = []
    if "base" in which:
        b = r.get("_base")
        if b:
            sa, sb, ta, tb = b
            v += [math.log1p(min(sa, sb)), math.log1p(max(sa, sb)),
                  (sa / ta if ta else 0.0), (sb / tb if tb else 0.0)]
        else:
            v += [float("nan")] * 4
    if "sister" in which:
        s = r.get("_sister")
        v.append(float("nan") if s is None else s)
    return v


def X_of(rs, which):
    x = G.X_of(rs, SPEC)
    if not which:
        return x
    return np.hstack([x, np.array([extra_of(r, which) for r in rs])])


def blind(rows, which):
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(X_of(tr, which), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, which))):
            f = r["seats_ly"] * math.exp(p)
            out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                abs(f / r["actual"] - 1) <= 0.20
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
    attach(rows)
    ctl = blind(rows, None)
    print("\n=== blind leave-one-cohort-out, n=%d, cohorts %s ==="
          % (len(rows), ",".join(str(c) for c in B.COHORTS)))
    print("  %-34s %9s   %s" % ("", "BLIND", "against the G09 control"))
    print("  %-34s %8.1f%%" % ("G09 control", 100.0 * sum(ctl.values()) / len(ctl)))
    best = None
    for which, label in ((["base"], "G11: + carrier base strength"),
                         (["sister"], "+ sister-airport flag"),
                         (["base", "sister"], "G12: + base strength + sister")):
        h = blind(rows, which)
        g, l, p = mcnemar(ctl, h)
        pct = 100.0 * sum(h.values()) / len(h)
        print("  %-34s %8.1f%%   +%-4d -%-4d p=%.4f%s"
              % (label, pct, g, l, p, "" if p < 0.05 else "  NOT MEASURABLE"))
        if which == ["base", "sister"]:
            best = h

    seg = [("short-haul, domestic or LCC",
            lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")),
           ("long-haul, international, full-service",
            lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC")]
    print("\n=== G12 by segment, the rule stated in advance ===")
    for label, fn in seg:
        ks = {"%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])
              for r in rows if fn(r)}
        a = {k: v for k, v in ctl.items() if k in ks}
        b = {k: v for k, v in best.items() if k in ks}
        print("  %-40s n=%-5d %6.1f%% -> %5.1f%%"
              % (label, len(a), 100.0 * sum(a.values()) / len(a),
                 100.0 * sum(b.values()) / len(b)))


if __name__ == "__main__":
    main()
