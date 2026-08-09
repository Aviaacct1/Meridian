#!/usr/bin/env python3
r"""What the engine knows that BT2 throws away: the connecting structure. 9 August 2026.

    AVIA_BT2_COHORTS=2016,2017,2018,2019,2024,2025 python3 bt2_feed_exp.py

WHERE THIS CAME FROM. bt2_tier_diagnose showed the predicted-spread deciles carry no bias at all,
so tier B and C are wider rather than wrong. What separates them is composition. The narrowest 30%
of routes are 55% LCC, 51% domestic, median 1,674 km and 10,738 planned seats. The widest 30% are
5% LCC, 12% domestic, median 3,524 km and 23,411 planned seats, and the carriers most often in it
are QR, BT, A3, CX, SU and LH. The routes BT2 cannot call are legacy long-haul international
launches, and those are launched for network reasons.

That is BT2's own stated residual, the "network decisions not visible in a pre-launch schedule",
and BT2 already has the data to see more of it than it uses. bt2_capture writes the connection
components per direction, so_ab / sa_ab / si_ab and the same for ba, plus capture at a standard
five weekly frequencies and at the actual planned frequency. bt2_lib collapses six of those into
ONE number, qcx, and passes cap_actual while dropping cap_f5 entirely.

Four things are tested, each a single change against the G09 control:

  cmp   the six connection components separately instead of one combined qcx
  asym  directional asymmetry of the feed, |ab - ba| over the total. A route feeding hard in one
        direction and not the other is a different proposition from a balanced one, and the
        combined qcx cannot express it
  fgain cap_f5 over cap_actual, which is how much this route's capture depends on frequency.
        Currently computed on every route, then discarded
  all   the three together

Everything is BLIND, leave-one-cohort-out, paired on identical routes against the control.

Which of the three things in section 1 changed: BT2, and only BT2. The QSI engine is untouched,
though what is being tested is whether the engine's own output carries signal BT2 is discarding.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
from math import comb

import numpy as np

import bt2_gbm as G
import bt2_lib as B
from bt2_paths import BT2

SPEC = ["car", "qcx", "gro"]
KW = dict(minleaf=60, l2=5.0, lr=0.04, it=600)
NAN = float("nan")


def load_components():
    """The raw capture components per pair per cohort, as bt2_capture wrote them."""
    out = {}
    for L in B.COHORTS:
        try:
            fh = open("%s/capture_%d.csv" % (BT2, L), newline="", encoding="utf-8-sig")
        except FileNotFoundError:
            print("  no capture file for %d, reported not filled" % L)
            continue
        for r in csv.DictReader(fh):
            out[(r["a"], r["b"], L)] = r
    return out


def _f(v):
    try:
        x = float(v)
        return x
    except (TypeError, ValueError):
        return None


def attach(rows, comp):
    have = 0
    for r in rows:
        c = comp.get((r["a"], r["b"], r["cohort"]))
        if not c:
            r["_cmp"] = None
            continue
        have += 1
        vals = {k: (_f(c.get(k)) or 0.0) for k in
                ("so_ab", "sa_ab", "si_ab", "so_ba", "sa_ba", "si_ba")}
        ab = vals["so_ab"] + vals["sa_ab"] + vals["si_ab"]
        ba = vals["so_ba"] + vals["sa_ba"] + vals["si_ba"]
        r["_cmp"] = vals
        r["_asym"] = (abs(ab - ba) / (ab + ba)) if (ab + ba) > 0 else NAN
        f5, fa = _f(c.get("cap_f5")), _f(c.get("cap_actual"))
        r["_fgain"] = (f5 / fa) if (f5 and fa and fa > 0) else NAN
    print("connection components attached to %d of %d launches (%.1f%%)"
          % (have, len(rows), 100.0 * have / len(rows)))


def extra_of(r, which):
    v = []
    c = r.get("_cmp")
    if "cmp" in which:
        ks = ("so_ab", "sa_ab", "si_ab", "so_ba", "sa_ba", "si_ba")
        v += [math.log1p(c[k]) for k in ks] if c else [NAN] * 6
    if "asym" in which:
        v.append(r.get("_asym", NAN) if c else NAN)
    if "fgain" in which:
        v.append(math.log(r["_fgain"]) if (c and r.get("_fgain") and r["_fgain"] > 0) else NAN)
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
    attach(rows, load_components())
    ctl = blind(rows, None)
    print("\n=== blind leave-one-cohort-out, n=%d, against the G09 control ===" % len(rows))
    print("  %-38s %9s   %s" % ("", "BLIND", "movers and p"))
    print("  %-38s %8.1f%%" % ("G09 control", 100.0 * sum(ctl.values()) / len(ctl)))
    for which, label in ((["cmp"], "+ six connection components"),
                         (["asym"], "+ feed directional asymmetry"),
                         (["fgain"], "+ frequency gain on capture"),
                         (["cmp", "asym", "fgain"], "+ all three")):
        h = blind(rows, which)
        g, l, p = mcnemar(ctl, h)
        print("  %-38s %8.1f%%   +%-4d -%-4d p=%.4f%s"
              % (label, 100.0 * sum(h.values()) / len(h), g, l, p,
                 "" if p < 0.05 else "  NOT MEASURABLE"))

    print("\n=== the same, on the routes the model finds hard: long-haul international non-LCC ===")
    hk = {"%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"]) for r in rows
          if r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC"}
    ek = {"%s-%s|%d|%s" % (r["a"], r["b"], r["cohort"], r["oag_carrier"]) for r in rows
          if r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")}
    easy = {k: v for k, v in ctl.items() if k in ek}
    print("  hard segment %d launches, easy segment (short-haul, domestic or LCC) %d"
          % (len(hk & set(ctl)), len(easy)))
    print("  %-38s %8.1f%%   the easy segment, control" % ("", 100.0 * sum(easy.values()) / len(easy)))
    sub = {k: v for k, v in ctl.items() if k in hk}
    print("  %-38s %8.1f%%" % ("G09 control", 100.0 * sum(sub.values()) / len(sub)))
    for which, label in ((["cmp"], "+ six connection components"),
                         (["cmp", "asym", "fgain"], "+ all three")):
        h = blind(rows, which)
        hs = {k: v for k, v in h.items() if k in hk}
        g, l, p = mcnemar(sub, hs)
        print("  %-38s %8.1f%%   +%-4d -%-4d p=%.4f%s"
              % (label, 100.0 * sum(hs.values()) / len(hs), g, l, p,
                 "" if p < 0.05 else "  NOT MEASURABLE"))


if __name__ == "__main__":
    main()
