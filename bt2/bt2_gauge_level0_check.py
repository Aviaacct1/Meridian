#!/usr/bin/env python3
r"""Does the region level (level 0) hold for GAUGE as well as frequency? W10, 26 Sep 2026.

    cd C:\src\meridian\bt2   (workstation)
    py -3.12 -s bt2_gauge_level0_check.py                     score only
    py -3.12 -s bt2_gauge_level0_check.py --fix E:\Avia\bt2_relaxed\schedule_prior.csv
                                                              if the rule fails, rewrite the level 0 rows' gauge
                                                              columns from their level 1 parent; frequency untouched

WHY. bt2_retime_freq.py adopted a region pair level 0 on frequency (log W10-RETIME-FREQ). The same
class rows carry the gauge band, so level 0 re-keys gauge too, and that was not scored. On Bologna-New
York the gauge band moved from 239 / 278 / 294 (level 1) to 226 / 266 / 287 (level 0).

ARMS, blind by cohort, target the record's seats per departure (unchanged):
  G1  gauge from levels 1-4 (the table as scored in W10-SCHEDULE-PRIOR-TABLE: 69.5% within +-20%)
  G0  gauge from levels 0-4 (what the written v2 file gives)

DECISION RULE, stated before the run: G0's gauge stands if its p25-p75 holds the flown gauge on
45-55% of launches AND its median within +-20% is no more than 1.0 point below G1's. Otherwise --fix
replaces every level 0 row's gauge_p25 / gauge_med / gauge_p75 with its level 1 parent's, so W1 keeps
one lookup and the gauge behaves exactly as the scored v1 table. Without --fix nothing is written.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import statistics
from collections import defaultdict

import bt2_gbm as G
import bt2_lib as B
import bt2_fit_schedule_prior as T
import bt2_retime_freq as R
from bt2_claimset import _provenance
from bt2_score import within


def band(t):
    return float(t["gauge_p25"]), float(t["gauge_med"]), float(t["gauge_p75"])


def score(rows, bands):
    n = len(rows)
    y = [r["gauge"] for r in rows]
    return dict(n=n,
                w20=100.0 * sum(within(b[1] / v) for v, b in zip(y, bands)) / n,
                w50=100.0 * sum(within(b[1] / v, 0.50) for v, b in zip(y, bands)) / n,
                inside=100.0 * sum(b[0] <= v <= b[2] for v, b in zip(y, bands)) / n,
                width=statistics.median(b[2] / b[0] for b in bands if b[0] > 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", default=None)
    a = ap.parse_args()
    rows = [r for r in G.rows if r["gauge"] > 0 and r["freq"] > 0]
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("build: %s" % _provenance())
    R.measure(rows)                       # attaches tt_freq and region_pair, the v2 table's inputs
    rows = [r for r in rows if r["tt_freq"]]
    out = {"G1": [None] * len(rows), "G0": [None] * len(rows)}
    pos = {id(r): i for i, r in enumerate(rows)}
    n0 = 0
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        i1 = R.index(R.fit(tr, (1, 2, 3, 4)))
        i0 = R.index(R.fit(tr, (0, 1, 2, 3, 4)))
        for r in te:
            k = R.key_of(r)
            out["G1"][pos[id(r)]] = band(R.lookup(i1, k))
            t = R.lookup(i0, k)
            n0 += int(t["level"]) == 0
            out["G0"][pos[id(r)]] = band(t)
    res = {}
    print("\n=== BLIND BY COHORT: gauge (seats per departure), n=%d ===" % len(rows))
    print("  %-34s %9s %9s %14s %10s" % ("arm", "med+-20%", "med+-50%", "inside p25-p75", "width"))
    for k, name in (("G1", "G1 levels 1-4 (scored v1 table)"), ("G0", "G0 levels 0-4 (written v2 file)")):
        s = score(rows, out[k])
        res[k] = s
        print("  %-34s %8.1f%% %8.1f%% %13.1f%% %9.2fx" % (name, s["w20"], s["w50"], s["inside"], s["width"]))
    print("  G0 took level 0 on %d of %d lookups" % (n0, len(rows)))
    hb = defaultdict(list)
    for i, r in enumerate(rows):
        hb[T.haul_band(r["gcd"])].append(i)
    print("\n  by haul band: within +-20%, inside p25-p75, width, G1 | G0")
    for h in sorted(hb):
        ii = hb[h]
        rs = [rows[i] for i in ii]
        c = []
        for k in ("G1", "G0"):
            s = score(rs, [out[k][i] for i in ii])
            c.append("%5.1f%% %5.1f%% x%.2f" % (s["w20"], s["inside"], s["width"]))
        print("  %s  %s  n=%d" % (h, " | ".join(c), len(rs)))
    g0, g1 = res["G0"], res["G1"]
    ok = 45.0 <= g0["inside"] <= 55.0 and g0["w20"] >= g1["w20"] - 1.0
    print("\nDECISION RULE (G0 inside 45-55%% AND within +-20%% no more than 1.0 point below G1): %s. "
          "G0 inside %.1f%%, +-20%% %.1f%% against G1 %.1f%%"
          % ("MET, the level 0 gauge stands" if ok else "NOT MET, level 0 rows take their level 1 parent's gauge",
             g0["inside"], g0["w20"], g1["w20"]))
    if a.fix and not ok:
        with open(a.fix, newline="") as fh:
            tab = list(csv.DictReader(fh))
            cols = list(tab[0].keys())
        par = {tuple(t[f] for f in T.LEVELS[1]): t for t in tab if t["table"] == "class" and t["level"] == "1"}
        nfix = 0
        for t in tab:
            if t["table"] == "class" and t["level"] == "0":
                p = par[tuple(t[f] for f in T.LEVELS[1])]
                for c in ("gauge_p25", "gauge_med", "gauge_p75"):
                    t[c] = p[c]
                nfix += 1
        with open(a.fix, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(tab)
        with open(a.fix + ".meta.txt", "a") as fh:
            fh.write("gauge on level 0 rows replaced by the level 1 parent's (W10-GAUGE-LEVEL0, rule not met): %d rows\n" % nfix)
        print("rewrote %s: %d level 0 rows now carry their level 1 parent's gauge; frequency untouched" % (a.fix, nfix))
    elif a.fix:
        print("--fix: nothing to do, the rule is met and %s is left as written" % a.fix)


if __name__ == "__main__":
    main()
