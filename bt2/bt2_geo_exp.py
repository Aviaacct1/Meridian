#!/usr/bin/env python3
r"""Geography as a BT2 feature, from the tail signature. 9 August 2026.

    python3 bt2_geo_exp.py            all arms
    python3 bt2_geo_exp.py touch home when a run has to be split

WHERE THIS CAME FROM, and it came from a diagnosis rather than a list. Splitting the long-haul
international full-service segment by the DIRECTION of the error gave the first nameable signature
of the day. No continuous variable separates the two tails: bigger aircraft, longer sectors, higher
frequency and far more capacity than the existing market describe BOTH tails equally, which says
those routes are hard rather than which way they go. The composition does separate them.

  over-read   MU 13, HU 10, CZ 7, QR 14, CX 7, DL 8, on AU-CN, CN-FR, CA-CN, QA-US
  under-read  UA 11, WS 8, AA 6, EI 5, SU 5, on IE-US 7, GB-US 5, IT-US 5, IL-US 4

Chinese and Gulf carriers launching China-facing long-haul are over-read; North Atlantic launches
are under-read. Those are two different industries, and BT2 cannot see the difference because it has
no geography at all: a domestic flag, and a carrier identity for carriers with fifteen or more
launches in sample, and nothing else about where in the world any of it is happening.

ARMS.

  touch  seven indicators, one per OAG region, set when the route touches that region
  home   seven indicators for the launching carrier's home region, plus a flag for a carrier
         operating away from home at both ends
  both   the two together

WHY THIS IS NOT FITTING THE SAMPLE, and the objection deserves answering rather than ignoring. The
scoring is leave-one-cohort-out, so a region effect has to hold in cohorts the model never saw to
pay anything. There are seven regions over 3,700 launches, so the smallest cell is in the hundreds,
not the 1.5 routes per cell that made the kickoff's 891-cell row score 84% fitted and 43% held-out.
And the effect being tested is a structural fact about the industry over a decade rather than a
route-level lookup. If it were a lookup it would show as fitted rising while blind does not.

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

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
REGIONS = ["Asia", "North America", "Europe", "Latin America",
           "Middle East", "Africa", "Southwest Pacific"]


def attach_geo(rows):
    rc = json.load(open("%s/region_by_country.json" % BT2))["map"]
    ch = json.load(open("%s/carrier_home.json" % BT2))["map"]
    miss_r = miss_h = 0
    for r in rows:
        ra, rb = rc.get(r.get("ctry_a"), ""), rc.get(r.get("ctry_b"), "")
        if not ra or not rb:
            miss_r += 1
        h = ch.get(r["oag_carrier"], {})
        if not h:
            miss_h += 1
        r["_geo"] = {"ra": ra, "rb": rb, "hr": h.get("region", ""), "hc": h.get("country", "")}
    print("geography attached; %d launches with an unmapped endpoint region, %d with an unknown "
          "carrier home (left as all-zero indicators, not guessed)" % (miss_r, miss_h))


def extra_of(r, arms):
    g = r.get("_geo") or {}
    v = []
    if "touch" in arms:
        v += [1.0 if (g.get("ra") == x or g.get("rb") == x) else 0.0 for x in REGIONS]
    if "home" in arms:
        v += [1.0 if g.get("hr") == x else 0.0 for x in REGIONS]
        # away from home at both ends: the carrier's home country is neither endpoint. Reads
        # fifth-freedom and long-haul-from-a-third-country flying, which is a different business
        # from flying out of your own market.
        v.append(1.0 if (g.get("hc") and g["hc"] not in (r.get("ctry_a"), r.get("ctry_b"))) else 0.0)
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


def fitted(rows, arms):
    m = G.make(SPEC, **KW)
    m.fit(X_of(rows, arms), G.y_of(rows))
    p = m.predict(X_of(rows, arms))
    n = sum(1 for r, q in zip(rows, p)
            if abs(r["seats_ly"] * math.exp(q) / r["actual"] - 1) <= 0.20)
    return 100.0 * n / len(rows)


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
    want = sys.argv[1:] or ["touch", "home", "both"]
    rows = G.rows
    F.attach(rows)
    attach_geo(rows)
    ctl = blind(rows, None)
    ek = {k for k, v in ctl.items() if EASY(v[1])}
    hk = {k for k, v in ctl.items() if HARD(v[1])}

    print("\n=== blind LOCO, n=%d, against the G12 control ===" % len(rows))
    print("  %-26s %8s %8s %8s %8s   %s"
          % ("", "FITTED", "ALL", "easy", "hard", "against control, all routes"))

    def line(label, h, fit, base=None):
        e = {k: v for k, v in h.items() if k in ek}
        d = {k: v for k, v in h.items() if k in hk}
        tail = ""
        if base is not None:
            g, l, p = mcnemar(base, h)
            tail = "+%-4d -%-4d p=%.4f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
        print("  %-26s %7.1f%% %7.1f%% %7.1f%% %7.1f%%   %s"
              % (label, fit, pct(h), pct(e), pct(d), tail))

    line("G12 control", ctl, fitted(rows, None))
    names = {"touch": "+ region touched", "home": "+ carrier home region",
             "both": "+ both"}
    for a in want:
        arms = ["touch", "home"] if a == "both" else [a]
        line(names[a], blind(rows, arms), fitted(rows, arms), ctl)
    print("\n  Fitted is printed so the lookup objection can be checked: if geography were a")
    print("  route-level lookup, fitted would climb while blind stood still.")


if __name__ == "__main__":
    main()
