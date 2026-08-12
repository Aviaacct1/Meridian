#!/usr/bin/env python3
r"""Grade US domestic launches against the DOT, everything else against Sabre. 9 August 2026.

    python3 bt2_mixed_basis.py

John's rule, adopted 5 August 2026: an airport is graded against the source it can verify, so a US
domestic route is graded against the US DOT's DB1B ticket survey and not against Sabre MIDT. The
relaxed sample built earlier on 9 August had no DOT outturns, because they existed only for the
narrower pair list, so the site briefly described a basis its evidence file did not have. This
applies the rule to the relaxed sample.

COVERAGE, and it is not complete, so it is stated rather than assumed. DB1B Market quarters on the
store run 2000 to 2024 with 2016 Q1 absent and nothing yet for 2025. So cohorts 2016 (three
quarters, scaled and flagged), 2017, 2018, 2019 and 2024 are graded against the DOT, and US domestic
launches in 2025 keep their Sabre grading until the 2025 release lands. Every row carries which
source graded it.

THREE THINGS ARE MEASURED, in this order, because the second only means anything given the first.

  1. THE RULER. How far apart the two sources are on the launches both can measure. If they disagree
     materially then part of what any model is scored on is the disagreement, not the forecast.
  2. THE EFFECT ON THE MODEL, trained and scored on the mixed basis against trained and scored on
     Sabre throughout. Both blind and calibrated.
  3. THE US SLICE ALONE, which is what a US airport will actually ask about.

attach() is importable so the builder and any experiment can use the same basis rather than each
deciding for itself what an outturn is.

Avia Solutions Limited. All rights reserved.
"""
import csv
import math
import os
import statistics

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_paths import BT2
from bt2_score import within
# One implementation of the build stamp, not two. bt2_claimset already imports the same three
# modules, so this adds no work at import time and cannot drift from the line the claim set prints.
from bt2_claimset import _provenance

SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
BLIND_KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)
CALIB_KW = dict(lr=0.08, it=1600, minleaf=3, l2=0.0, leaves=95)


def load_dot():
    dot = {}
    for L in B.COHORTS:
        p = "%s/db1b_outturn_%d.csv" % (BT2, L)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            try:
                v = float(r["db1b_pax"])
            except (TypeError, ValueError):
                continue
            if v > 0:
                dot[(r["a"], r["b"], L)] = (v, r.get("scaled") == "True")
    return dot


def attach(rows):
    """Set r['actual'] to the DOT figure on US domestic launches where one exists. Returns the
    Sabre figure alongside so the two rulers can be compared rather than silently swapped."""
    dot = load_dot()
    n = 0
    for r in rows:
        r["_sabre"] = r["actual"]
        r["_src"] = "Sabre MIDT"
        r["_scaled"] = False
        if r.get("ctry_a") == "US" and r.get("ctry_b") == "US":
            v = dot.get((r["a"], r["b"], r["cohort"]))
            if v:
                r["actual"] = v[0]
                r["_src"] = "US DOT DB1B"
                r["_scaled"] = v[1]
                n += 1
    return n


def blind(rows, kw=None):
    out = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make(SPEC, **(kw or BLIND_KW))
        m.fit(F.X_of(tr, G12), G.y_of(tr))
        for r, p in zip(te, m.predict(F.X_of(te, G12))):
            f = r["seats_ly"] * math.exp(p)
            if f > 0 and r["actual"] > 0:
                out[id(r)] = f / r["actual"]
    return out


def calibrated(rows):
    m = G.make(SPEC, **CALIB_KW)
    m.fit(F.X_of(rows, G12), G.y_of(rows))
    return {id(r): r["seats_ly"] * math.exp(p) / r["actual"]
            for r, p in zip(rows, m.predict(F.X_of(rows, G12))) if r["actual"] > 0}


def rate(d, keys=None, tol=0.20):
    v = [x for k, x in d.items() if keys is None or k in keys]
    return 100.0 * sum(1 for x in v if within(x, tol)) / len(v) if v else 0.0


def main():
    # THE TARGET MUST BE nonstop, and this could not collide before 13 August 2026 because there was
    # only one target. AVIA_BT2_TARGET now lets bt2_lib grade against p2p_outturn or against the
    # SECTOR total instead of launch_pax. attach() below overwrites r["actual"] with the DOT DB1B
    # figure on US domestic launches, and DB1B is a LOCAL NONSTOP ticket count: dropping it on top of
    # a sector target would grade 595 routes on the local market and 5,929 on the whole sector inside
    # one sample, which is not a mixed ruler but a broken one. Refused by name rather than allowed.
    if B.TARGET != "nonstop":
        raise SystemExit("AVIA_BT2_TARGET=%s. The mixed basis regrades US domestic launches onto DOT "
                         "DB1B, which is a local nonstop ticket count, so it is only coherent against "
                         "the nonstop target. Set AVIA_BT2_TARGET=nonstop." % B.TARGET)

    rows = G.rows
    F.attach(rows)
    print("build:  %s" % _provenance())

    sab_blind = blind(rows)
    sab_cal = calibrated(rows)

    n = attach(rows)
    us = {id(r) for r in rows if r["_src"] == "US DOT DB1B"}
    print("sample n=%d. US domestic launches regraded against the DOT: %d" % (len(rows), n))
    print("  by cohort: " + ", ".join(
        "%d:%d" % (L, sum(1 for r in rows if r["_src"] == "US DOT DB1B" and r["cohort"] == L))
        for L in B.COHORTS))
    sc = sum(1 for r in rows if r["_scaled"])
    if sc:
        print("  %d of them scaled from three quarters (2016 Q1 absent) and flagged" % sc)

    print("\n=== 1. THE RULER: the two sources on the same launches ===")
    d = [(r["_sabre"], r["actual"]) for r in rows if r["_src"] == "US DOT DB1B"]
    ag = [b / a for a, b in d if a > 0]
    print("  n=%d, median DOT over Sabre %.3f, agree within +-20%% on %.1f%%, within +-10%% on %.1f%%"
          % (len(ag), statistics.median(ag),
             100.0 * sum(1 for x in ag if within(x)) / len(ag),
             100.0 * sum(1 for x in ag if within(x, 0.10)) / len(ag)))

    mix_blind = blind(rows)
    mix_cal = calibrated(rows)

    print("\n=== 2. THE MODEL, Sabre throughout against the mixed basis ===")
    print("  %-34s %10s %12s" % ("", "blind", "calibrated"))
    print("  %-34s %9.1f%% %11.1f%%" % ("Sabre throughout", rate(sab_blind), rate(sab_cal)))
    print("  %-34s %9.1f%% %11.1f%%" % ("mixed, US domestic on DOT", rate(mix_blind), rate(mix_cal)))
    # THE PUBLISHED PAIR IS ON THIS LINE AND THE ONE ABOVE, so both tolerances are printed for both
    # bases rather than one figure for one of them. The old version passed a literal "%%" as a label
    # argument, where it does not get consumed by the format operator and printed as "+-10%%", and
    # put 0.0 in the blind column as a placeholder that read as a measurement of zero.
    print("  %-34s %9.1f%% %11.1f%%" % ("  the same, within +-10%",
                                        rate(mix_blind, tol=0.10), rate(mix_cal, tol=0.10)))
    print("  %-34s %9.1f%% %11.1f%%" % ("  Sabre throughout, within +-10%",
                                        rate(sab_blind, tol=0.10), rate(sab_cal, tol=0.10)))

    print("\n=== 3. THE US SLICE ALONE, which is what a US airport asks about ===")
    print("  %-34s %10s %12s" % ("", "blind", "calibrated"))
    print("  %-34s %9.1f%% %11.1f%%" % ("graded on Sabre", rate(sab_blind, us), rate(sab_cal, us)))
    print("  %-34s %9.1f%% %11.1f%%" % ("graded on DOT", rate(mix_blind, us), rate(mix_cal, us)))


if __name__ == "__main__":
    main()
