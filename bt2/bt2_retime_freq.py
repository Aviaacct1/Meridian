#!/usr/bin/env python3
r"""Re-measure launch frequency as the timetable flew it, and refit the schedule prior table on it. W10, 26 Sep 2026.

    cd C:\src\meridian\bt2   (workstation; pair_months_L.csv lives only there)
    py -3.12 -s bt2_retime_freq.py                    measure, score, decide; nothing written
    py -3.12 -s bt2_retime_freq.py --out E:\Avia\bt2_relaxed\schedule_prior.csv
                                                      writes ONLY if the decision rule below is met, after
                                                      copying the current table to schedule_prior_v1.csv

WHY. The record's frequency (bt2_profile.py, wk_freq_dir) is every carrier's departures over every
operated month of the launch year, divided by months x 4.345 x 2. The launch month is usually part
of a month and the later months carry seasonal cuts, so a route timetabled at 3x from mid-June reads
circa 2.4, which is a schedule nobody flew. The class table built on it (W10-SCHEDULE-PRIOR-TABLE)
holds the flown figure inside its p25-p75 on 48.7% of launches, but its band is wide (x2.19) and its
p25 on Bologna-New York is 2.2 a week. Optimise bounds a timetable, so the table should describe
timetables.

THE NEW MEASURE, fixed before the run. For each launch, from pair_months_L.csv (the same OAG monthly
extract the record was built from; unordered pair, both directions, departures per carrier-month):
  primary    tt_freq = the LAUNCHING CARRIER's departures in the FIRST FULL MONTH (the month after the
             launch month), per week per direction: ops / (days in month / 7) / 2.
  fallback   if that month is absent or under 4 departures, the median of the carrier's later operated
             months; if there are none (a December launch), the launch month itself. Each fallback is
             counted and printed, never silent.
  reported   the all-carrier first full month, and the carrier's median later month, for comparison.
Gauge is unchanged: the record's seats per departure (W10-SCHEDULE-PRIOR-TABLE, 69.5%) stands.

THE REGION LEVEL, tested on the new measure only. Level 0 adds region_pair (bt2_record_mix.region_pair:
EU, NA, AS, ME, OT by country, e.g. EU-NA; domestic US / EU / other) to the level 1 key. A lookup takes
level 0 when its row has n of 20 or more, else falls to level 1 as before.

ARMS, blind by cohort (fit on five cohorts, score the sixth), all scored against tt_freq:
  T1   the current table's frequency band (fitted on the averaged measure)
  T2   the table refitted on tt_freq, levels 1-4
  T2R  T2 with level 0 (region pair)
Metrics: median within +-20% and +-50%, tt_freq inside p25-p75, median width p75 / p25, the share of
medians within 0.25 of a whole weekly frequency, all by haul band as well.

DECISION RULE, stated before the run:
  T2 replaces the current table's frequency columns if its p25-p75 holds tt_freq on 45-55% of
  launches AND its median within +-20% beats T1's on the same target.
  T2R is adopted over T2 if it also holds 45-55%, its width is at least 5% narrower than T2's, and
  its median within +-20% is not worse than T2's.
--out writes the winning table (region_pair column blank on levels 1-4, filled on level 0 when T2R
wins; carrier lines refitted on tt_freq; gauge columns as before) and refuses when neither rule is met.

W1 SHOULD WIRE THE LOOKUP WITH LEVEL 0 FROM THE START: the CSV carries a region_pair column either
way, and a file with no level-0 rows falls to level 1 exactly as the v1 table does. Then whichever
table wins is a data swap, never a rewire.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import calendar
import csv
import os
import shutil
import statistics
import time
from collections import defaultdict

import bt2_gbm as G
import bt2_lib as B
import bt2_fit_schedule_prior as T
from bt2_claimset import _provenance
from bt2_record_mix import region_pair
from bt2_score import within

MIN_OPS = 4
COLS = ["table", "level", "scope", "haul_band", "carrier_type", "market_band", "region_pair", "carrier", "n",
        "gauge_p25", "gauge_med", "gauge_p75", "freq_p25", "freq_med", "freq_p75"]
LEVELS = dict([(0, ("scope", "haul_band", "carrier_type", "market_band", "region_pair"))] + list(T.LEVELS.items()))


def wk(ops, mon):
    y, m = int(mon[:4]), int(mon[5:7])
    return ops / (calendar.monthrange(y, m)[1] / 7.0) / 2.0


def next_mon(mon):
    y, m = int(mon[:4]), int(mon[5:7])
    return "%04d-%02d" % (y + (m == 12), 1 if m == 12 else m + 1)


def measure(rows):
    """Attach tt_freq (and the comparison measures) to every record row. Counts every fallback."""
    cnt = defaultdict(int)
    by_c = defaultdict(list)
    for r in rows:
        by_c[r["cohort"]].append(r)
    for L, rs in by_c.items():
        ser = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))   # pair -> mon -> carrier -> ops
        with open("%s/pair_months_%d.csv" % (B.BT2, L)) as f:
            for x in csv.DictReader(f):
                mon = x["mon"]
                if len(mon) != 7 or mon[4] != "-":
                    continue                     # monthly labels only (the spine rule)
                ser[(x["a"], x["b"])][mon][x["carrier"]] += int(float(x["ops"] or 0))
        for r in rs:
            s = ser.get((r["a"], r["b"]), {})
            lm, car = r["launch_month"][:7], r["oag_carrier"]
            nm = next_mon(lm)
            later = sorted(m for m in s if m > lm and s[m].get(car, 0) >= MIN_OPS)
            if s.get(nm, {}).get(car, 0) >= MIN_OPS:
                r["tt_freq"] = wk(s[nm][car], nm)
                cnt["first full month"] += 1
            elif later:
                r["tt_freq"] = statistics.median(wk(s[m][car], m) for m in later)
                cnt["fallback: median of later months"] += 1
            elif s.get(lm, {}).get(car, 0) > 0:
                r["tt_freq"] = wk(s[lm][car], lm)
                cnt["fallback: launch month only"] += 1
            else:
                r["tt_freq"] = None
                cnt["no carrier months found (row dropped)"] += 1
            r["tt_all"] = wk(sum(s[nm].values()), nm) if nm in s and sum(s[nm].values()) >= MIN_OPS else None
            r["tt_med"] = statistics.median(wk(s[m][car], m) for m in later) if later else None
            r["region_pair"] = region_pair(r)
    return cnt


def key_of(r):
    k = T.key_of(r)
    k["region_pair"] = r["region_pair"]
    return k


def fit(rows, levels):
    """Class rows on tt_freq for frequency and the record's gauge; carrier lines likewise."""
    sh = [dict(r, freq=r["tt_freq"]) for r in rows]
    out = []
    for lv in levels:
        fields = LEVELS[lv]
        g = defaultdict(list)
        for r in sh:
            k = key_of(r)
            g[tuple(k[f] for f in fields)].append(r)
        for kv, rs in sorted(g.items()):
            row = {c: "" for c in COLS}
            row.update(table="class", level=lv)
            row.update(dict(zip(fields, kv)))
            row.update(T.stats(rs))
            out.append(row)
    for t in T.fit(sh):
        if t["table"] == "carrier":
            row = {c: "" for c in COLS}
            row.update(t)
            out.append(row)
    return out


def index(table):
    idx = {}
    for t in table:
        if t["table"] == "class":
            lv = int(t["level"])
            idx[(lv,) + tuple(t[f] for f in LEVELS[lv])] = t
    return idx


def lookup(idx, k):
    for lv in sorted(LEVELS):
        t = idx.get((lv,) + tuple(k[f] for f in LEVELS[lv]))
        if t and int(t["n"]) >= T.MIN_CLASS:
            return t
    return None


def score(rows, bands):
    n = len(rows)
    tgt = [r["tt_freq"] for r in rows]
    return dict(n=n,
                w20=100.0 * sum(within(b[1] / y) for y, b in zip(tgt, bands)) / n,
                w50=100.0 * sum(within(b[1] / y, 0.50) for y, b in zip(tgt, bands)) / n,
                inside=100.0 * sum(b[0] <= y <= b[2] for y, b in zip(tgt, bands)) / n,
                width=statistics.median(b[2] / b[0] for b in bands if b[0] > 0),
                whole=100.0 * sum(abs(b[1] - round(b[1])) <= 0.25 for b in bands) / n)


def blind(rows):
    out = {k: [None] * len(rows) for k in ("T1", "T2", "T2R")}
    lvl0 = [0] * 1
    pos = {id(r): i for i, r in enumerate(rows)}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        i1 = T.index(T.fit(tr))
        i2 = index(fit(tr, (1, 2, 3, 4)))
        i2r = index(fit(tr, (0, 1, 2, 3, 4)))
        for r in te:
            p = pos[id(r)]
            t = T.lookup(i1, T.key_of(r))
            out["T1"][p] = (float(t["freq_p25"]), float(t["freq_med"]), float(t["freq_p75"]))
            t = lookup(i2, key_of(r))
            out["T2"][p] = (float(t["freq_p25"]), float(t["freq_med"]), float(t["freq_p75"]))
            t = lookup(i2r, key_of(r))
            lvl0[0] += int(t["level"]) == 0
            out["T2R"][p] = (float(t["freq_p25"]), float(t["freq_med"]), float(t["freq_p75"]))
    return out, lvl0[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = [r for r in G.rows if r["gauge"] > 0 and r["freq"] > 0]
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("build: %s" % _provenance())
    cnt = measure(rows)
    print("\n=== THE NEW MEASURE: launching carrier, first full month, per week per direction ===")
    for k, v in sorted(cnt.items()):
        print("  %-42s %5d" % (k, v))
    rows = [r for r in rows if r["tt_freq"]]
    old = [r["freq"] for r in rows]
    new = [r["tt_freq"] for r in rows]
    al = [r["tt_all"] for r in rows if r["tt_all"]]
    print("  rows scored: %d" % len(rows))
    print("  median: averaged (record) %.2f | first full month, carrier %.2f | first full month, all carriers %.2f"
          % (statistics.median(old), statistics.median(new), statistics.median(al)))
    print("  median ratio new / averaged %.3f; within 0.25 of a whole weekly frequency: averaged %.1f%%, new %.1f%%"
          % (statistics.median(n / o for n, o in zip(new, old)),
             100.0 * sum(abs(x - round(x)) <= 0.25 for x in old) / len(old),
             100.0 * sum(abs(x - round(x)) <= 0.25 for x in new) / len(new)))
    agree = [r for r in rows if r["tt_med"]]
    print("  first full month within +-20%% of the carrier's median later month: %.1f%% (n=%d)"
          % (100.0 * sum(within(r["tt_freq"] / r["tt_med"]) for r in agree) / len(agree), len(agree)))

    out, n0 = blind(rows)
    names = {"T1": "T1 current table (averaged measure)", "T2": "T2 table refitted on first full month",
             "T2R": "T2R + region pair level 0"}
    res = {}
    print("\n=== BLIND BY COHORT against the first-full-month frequency, n=%d ===" % len(rows))
    print("  %-40s %9s %9s %14s %10s %13s" % ("arm", "med+-20%", "med+-50%", "inside p25-p75", "width", "med whole+-.25"))
    for k in ("T1", "T2", "T2R"):
        s = score(rows, out[k])
        res[k] = s
        print("  %-40s %8.1f%% %8.1f%% %13.1f%% %9.2fx %12.1f%%" % (names[k], s["w20"], s["w50"], s["inside"],
                                                                s["width"], s["whole"]))
    print("  T2R took level 0 on %d of %d lookups" % (n0, len(rows)))
    print("\n  by haul band: inside p25-p75 and width, T1 | T2 | T2R")
    hb = defaultdict(list)
    for i, r in enumerate(rows):
        hb[T.haul_band(r["gcd"])].append(i)
    for h in sorted(hb):
        ii = hb[h]
        rs = [rows[i] for i in ii]
        cells = []
        for k in ("T1", "T2", "T2R"):
            s = score(rs, [out[k][i] for i in ii])
            cells.append("%5.1f%% x%.2f" % (s["inside"], s["width"]))
        print("  %s  %s  n=%d" % (h, " | ".join(cells), len(rs)))

    t1, t2, t2r = res["T1"], res["T2"], res["T2R"]
    ok2 = 45.0 <= t2["inside"] <= 55.0 and t2["w20"] > t1["w20"]
    ok2r = ok2 and 45.0 <= t2r["inside"] <= 55.0 and t2r["width"] <= 0.95 * t2["width"] and t2r["w20"] >= t2["w20"]
    win = "T2R" if ok2r else "T2" if ok2 else None
    print("\nDECISION RULE: T2 %s (inside %.1f%%, +-20%% %.1f%% against T1 %.1f%%); T2R %s (inside %.1f%%, width x%.2f "
          "against x%.2f, +-20%% %.1f%%). WINNER: %s"
          % ("MET" if ok2 else "NOT MET", t2["inside"], t2["w20"], t1["w20"],
             "MET" if ok2r else "NOT MET", t2r["inside"], t2r["width"], t2["width"], t2r["w20"],
             win or "none, the current table stays"))

    levels = (0, 1, 2, 3, 4) if win == "T2R" else (1, 2, 3, 4)
    table = fit(rows, levels)
    k = {"scope": "I", "haul_band": "H3", "carrier_type": "FSC", "market_band": "S2", "region_pair": "EU-NA"}
    t = lookup(index(table), k)
    print("\nBologna-New York key %s -> level %s n=%s, freq %s / %s / %s, gauge %s / %s / %s"
          % (k, t["level"], t["n"], t["freq_p25"], t["freq_med"], t["freq_p75"],
             t["gauge_p25"], t["gauge_med"], t["gauge_p75"]))
    for mb in ("S0", "S1"):
        k2 = dict(k, market_band=mb)
        t = lookup(index(table), k2)
        print("  same pair shape at %s (Genoa and Southend are S0): level %s n=%s, freq %s / %s / %s"
              % (mb, t["level"], t["n"], t["freq_p25"], t["freq_med"], t["freq_p75"]))
    ua = [x for x in table if x["table"] == "carrier" and x["carrier"] == "UA" and x["haul_band"] == "H3" and x["scope"] == "I"]
    if ua:
        print("  United, H3 international: n=%s, freq %s / %s / %s" % (ua[0]["n"], ua[0]["freq_p25"], ua[0]["freq_med"], ua[0]["freq_p75"]))

    if a.out:
        if not win:
            print("\nNOT WRITTEN: neither rule is met, the current table stays at %s" % a.out)
            return
        if os.path.exists(a.out):
            bak = os.path.join(os.path.dirname(a.out), "schedule_prior_v1.csv")
            if not os.path.exists(bak):
                shutil.copy2(a.out, bak)
                print("\ncurrent table kept as %s" % bak)
        with open(a.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            for t in table:
                w.writerow({c: t.get(c, "") for c in COLS})
        with open(a.out + ".meta.txt", "w") as fh:
            fh.write("schedule_prior.csv v2 (%s), written %s by bt2/bt2_retime_freq.py\n"
                     "frequency = launching carrier, first full month, per week per direction; gauge = record seats per departure\n"
                     "sample %s, n=%d, cohorts %s\nbuild %s\nblind: %s\n"
                     % (win, time.strftime("%d %b %Y %H:%M"), B.BT2, len(rows),
                        ",".join(str(c) for c in B.COHORTS), _provenance(), res))
        print("wrote %s (%s) and %s.meta.txt" % (a.out, win, a.out))


if __name__ == "__main__":
    main()
