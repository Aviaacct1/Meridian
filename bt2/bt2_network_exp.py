#!/usr/bin/env python3
r"""Carrier network reach as a BT2 feature, on top of G12. 9 August 2026.

    python3 bt2_network_exp.py                 all arms
    python3 bt2_network_exp.py ctry sys        named arms only, when a run has to be split

MORE OF THE ONLY THING THAT WORKED. Base strength was the one feature family that paid today, and
it is an AIRPORT measure: the launching carrier's own seats at each endpoint, and its share there.
The hard half of the problem is long-haul international, where the question is not what the carrier
holds at the airport but what it holds in the COUNTRY, and whether it flies there at all.

ARMS, each a single change against the standing G12 control.

  ctry  the carrier's departing seats from each endpoint's country in the pre-launch month, as min
        and max across the two, and its share of all seats from each country
  sys   the carrier's total departing seats anywhere that month. BT2 carries carrier IDENTITY for
        carriers with fifteen or more launches in sample and nothing at all for the rest, so a
        small carrier and a large one look the same unless the network size is given
  new   whether the carrier flew from either endpoint country at all before the launch. Opening a
        country is a different act from adding a route inside an existing footprint
  all   the three together

Everything is BLIND leave-one-cohort-out, paired on identical routes against the G12 control, and
reported by segment because the whole point of the hypothesis is the long-haul half.

Which of the three things in section 1 changed: BT2, and only BT2.

Avia Solutions Limited. All rights reserved.
"""
import json
import math
import os
import sys
from math import comb

import numpy as np

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")

import bt2_gbm as G          # noqa: E402
import bt2_lib as B          # noqa: E402
import bt2_g12_exp as F      # noqa: E402
from bt2_paths import BT2    # noqa: E402

SPEC = ["car", "qcx", "gro"]
G12 = ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
NAN = float("nan")


def attach_network(rows):
    net = {}
    for L in B.COHORTS:
        p = "%s/network_%d.json" % (BT2, L)
        net[L] = json.load(open(p)) if os.path.exists(p) else None
        if net[L] is None:
            print("  cohort %d: no network file, reported not filled" % L)
    have = 0
    for r in rows:
        d = net.get(r["cohort"])
        if not d:
            r["_net"] = None
            continue
        car, pm = r["oag_carrier"], r["pre_month"]
        ca, cb = r.get("ctry_a"), r.get("ctry_b")
        sa = d.get("%s|%s|%s" % (car, ca, pm))
        sb = d.get("%s|%s|%s" % (car, cb, pm))
        ta = d.get("ALL|%s|%s" % (ca, pm)) or 0
        tb = d.get("ALL|%s|%s" % (cb, pm)) or 0
        syst = d.get("%s|SYSTEM|%s" % (car, pm))
        # A carrier absent from a country has no row, which means zero seats there, not a gap in
        # the data: the month was pulled in full. Zero is the honest value and the "new" flag is
        # exactly that fact, so it is recorded rather than left as NaN.
        r["_net"] = {"sa": sa or 0, "sb": sb or 0, "ta": ta, "tb": tb,
                     "sys": syst or 0, "new": 1.0 if (not sa or not sb) else 0.0}
        have += 1
    print("network reach on %d of %d launches" % (have, len(rows)))


def extra_of(r, arms):
    n = r.get("_net")
    v = []
    if "ctry" in arms:
        if n:
            v += [math.log1p(min(n["sa"], n["sb"])), math.log1p(max(n["sa"], n["sb"])),
                  (n["sa"] / n["ta"] if n["ta"] else 0.0),
                  (n["sb"] / n["tb"] if n["tb"] else 0.0)]
        else:
            v += [NAN] * 4
    if "sys" in arms:
        v.append(math.log1p(n["sys"]) if n else NAN)
    if "new" in arms:
        v.append(n["new"] if n else NAN)
    return v


def X_of(rs, arms):
    x = F.X_of(rs, G12)
    if not arms:
        return x
    return np.hstack([x, np.array([extra_of(r, arms) for r in rs])])


def blind(rows, arms):
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **KW)
        m.fit(X_of(tr, arms), G.y_of(tr))
        for r, p in zip(te, m.predict(X_of(te, arms))):
            f = r["seats_ly"] * math.exp(p)
            out["%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"])] = \
                (abs(f / r["actual"] - 1) <= 0.20, r)
    return out


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if not a[k][0] and b[k][0])
    n10 = sum(1 for k in ks if a[k][0] and not b[k][0])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def pct(h):
    return 100.0 * sum(1 for v in h.values() if v[0]) / len(h) if h else 0.0


HARD = lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"
EASY = lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")


def main():
    want = sys.argv[1:] or ["ctry", "sys", "new", "all"]
    rows = G.rows
    F.attach(rows)
    attach_network(rows)

    ctl = blind(rows, None)
    print("\n=== blind LOCO, n=%d, against the G12 control ===" % len(rows))
    print("  %-30s %8s %9s %9s   %s"
          % ("", "ALL", "easy", "hard", "against control, all routes"))
    ek = {k for k, v in ctl.items() if EASY(v[1])}
    hk = {k for k, v in ctl.items() if HARD(v[1])}

    def line(label, h, base=None):
        e = {k: v for k, v in h.items() if k in ek}
        d = {k: v for k, v in h.items() if k in hk}
        tail = ""
        if base is not None:
            g, l, p = mcnemar(base, h)
            tail = "+%-4d -%-4d p=%.4f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
        print("  %-30s %7.1f%% %8.1f%% %8.1f%%   %s" % (label, pct(h), pct(e), pct(d), tail))

    line("G12 control", ctl)
    names = {"ctry": "+ country presence", "sys": "+ carrier network size",
             "new": "+ opens a new country", "all": "+ all three"}
    for a in want:
        arms = ["ctry", "sys", "new"] if a == "all" else [a]
        line(names[a], blind(rows, arms), ctl)


if __name__ == "__main__":
    main()
