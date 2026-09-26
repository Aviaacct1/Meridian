#!/usr/bin/env python3
r"""Fit the schedule prior table Optimise reads. W10, 26 September 2026 (John's ruling 4, GO).

    cd C:\src\meridian\bt2   (workstation; the sample lives only there)
    py -3.12 -s bt2_fit_schedule_prior.py --out E:\Avia\bt2_relaxed\schedule_prior.csv
    py -3.12 -s bt2_fit_schedule_prior.py --lookup base_mkt=37814 gcd_km=6647 scope=I carrier_type=FSC carrier=UA

WHAT IT IS. For every class of pair, the schedule airlines actually launched on it in the record
(6,524 launches, 2016-2019, 2024, 2025): seats per departure (gauge) and weekly frequency per
direction at p25, median and p75, with n. Plus carrier lines: each carrier's own launches by haul
band and scope, same statistics, with n. Optimise bounds its sweep to the class's p25-p75 on gauge
and frequency, ranks by contribution inside that set, and forecasts at the winner (W10-STATUS,
option 2b; bt2_experiments.log W10-SCHEDULE-PRIOR).

THE CLASS KEY, exactly, and what the app must compute to look a pair up:

  market_band  on base_mkt = Sabre passengers on the UNORDERED AIRPORT PAIR, ALL itineraries, BOTH
               directions, in the latest full Sabre source year. This is route_context.market(a, b,
               year)[0] in the app, the calibrated model's own base_mkt. It is NOT market_build step
               1 (the whole service area's traffic to the destination metro, grossed up for GDS
               coverage, each way): on Bologna-New York that is 203,142 against a pair of 37,814, and
               keying on it puts the pair two bands too high.
                 S0  under 8,000      S1  8,000-24,999      S2  25,000-79,999      S3  80,000 and over
  haul_band    on great-circle km between the two airports (bt2_lib.haul_band):
                 H0  under 800        H1  800-1,999         H2  2,000-4,499        H3  4,500 and over
  carrier_type LCC or FSC. The record classes a carrier LCC when it is in
               connection_builder.DEFAULT_LCC_LIST. From the app's carrier types: LCC and ULCC map to
               LCC; FSC, Regional and Charter map to FSC.
  scope        D when both airports are in the same country (airportsdata country), else I.

LOOKUP RULE. Rows carry a level. Take the first level whose row exists and has n >= 20:
  level 1  scope, haul_band, carrier_type, market_band
  level 2  haul_band, carrier_type, market_band          (scope blank)
  level 3  haul_band, market_band                        (scope and carrier_type blank)
  level 4  haul_band                                     (everything else blank)
Every haul band has a level-4 row, so a lookup never fails. The row used is reported in the payload.

CARRIER LINES, table = carrier: key carrier (OAG two-letter code as in the record), haul_band,
scope; plus one row per carrier with haul_band and scope blank (all its launches). Rows written only
where n >= 5; below five the payload says "fewer than 5 comparable launches" (John's ruling 4).

UNITS. gauge = seats per departure (OAG seats over operations in the operated months). freq =
departures per week per direction. Seats a year for a candidate schedule = gauge x freq x 2 x 52
(two-way, the calibrated model's basis; halve for each way).

THE TABLE IS SCORED, not assumed: the script fits it leave-one-cohort-out and prints how often the
looked-up median lands within +-20% and +-50% of the gauge and frequency actually flown, and how
often the actual falls inside the looked-up p25-p75. The gradient-boosted prior scored 71% within
+-20% on each (W10-SCHEDULE-PRIOR); a lookup table is coarser and its score is printed beside it.

Output: the CSV at --out, and a .meta.txt beside it with the build stamp, sample and cohorts.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import time
from collections import defaultdict

import bt2_gbm as G
import bt2_lib as B
from bt2_claimset import _provenance
from bt2_score import within

MIN_CLASS = 20
MIN_CARRIER = 5
COLS = ["table", "level", "scope", "haul_band", "carrier_type", "market_band", "carrier", "n",
        "gauge_p25", "gauge_med", "gauge_p75", "freq_p25", "freq_med", "freq_p75"]


def market_band(bm):
    return "S0" if bm < 8000 else "S1" if bm < 25000 else "S2" if bm < 80000 else "S3"


def haul_band(km):
    return "H0" if km < 800 else "H1" if km < 2000 else "H2" if km < 4500 else "H3"


def key_of(r):
    return {"scope": "D" if r["dom"] else "I", "haul_band": haul_band(r["gcd"]),
            "carrier_type": r["typ"], "market_band": market_band(r["base_mkt"])}


LEVELS = {1: ("scope", "haul_band", "carrier_type", "market_band"),
          2: ("haul_band", "carrier_type", "market_band"),
          3: ("haul_band", "market_band"),
          4: ("haul_band",)}


def q(v, f):
    v = sorted(v)
    if not v:
        return None
    x = f * (len(v) - 1)
    lo, hi = int(x), min(int(x) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (x - lo)


def stats(rs):
    g = [r["gauge"] for r in rs]
    f = [r["freq"] for r in rs]
    return {"n": len(rs),
            "gauge_p25": round(q(g, .25)), "gauge_med": round(q(g, .5)), "gauge_p75": round(q(g, .75)),
            "freq_p25": round(q(f, .25), 1), "freq_med": round(q(f, .5), 1), "freq_p75": round(q(f, .75), 1)}


def fit(rows):
    out = []
    for lv, fields in LEVELS.items():
        g = defaultdict(list)
        for r in rows:
            k = key_of(r)
            g[tuple(k[f] for f in fields)].append(r)
        for kv, rs in sorted(g.items()):
            row = {"table": "class", "level": lv, "scope": "", "haul_band": "", "carrier_type": "",
                   "market_band": "", "carrier": ""}
            row.update(dict(zip(fields, kv)))
            row.update(stats(rs))
            out.append(row)
    g = defaultdict(list)
    for r in rows:
        k = key_of(r)
        g[(r["oag_carrier"], k["haul_band"], k["scope"])].append(r)
        g[(r["oag_carrier"], "", "")].append(r)
    for (car, hb, sc), rs in sorted(g.items()):
        if len(rs) >= MIN_CARRIER:
            row = {"table": "carrier", "level": "", "scope": sc, "haul_band": hb, "carrier_type": "",
                   "market_band": "", "carrier": car}
            row.update(stats(rs))
            out.append(row)
    return out


def index(table):
    idx = {}
    for t in table:
        if t["table"] == "class":
            fields = LEVELS[int(t["level"])]
            idx[(int(t["level"]),) + tuple(t[f] for f in fields)] = t
    return idx


def lookup(idx, k):
    for lv, fields in LEVELS.items():
        t = idx.get((lv,) + tuple(k[f] for f in fields))
        if t and int(t["n"]) >= MIN_CLASS:
            return t
    return None


def blind_score(rows):
    hit = defaultdict(int)
    n = 0
    lv = defaultdict(int)
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        idx = index(fit(tr))
        for r in te:
            t = lookup(idx, key_of(r))
            if not t:
                continue
            n += 1
            lv[int(t["level"])] += 1
            for m in ("gauge", "freq"):
                pred = float(t[m + "_med"])
                if pred > 0:
                    ratio = pred / r[m]
                    hit[m + "20"] += within(ratio)
                    hit[m + "50"] += within(ratio, 0.50)
                hit[m + "in"] += float(t[m + "_p25"]) <= r[m] <= float(t[m + "_p75"])
    print("\n=== BLIND BY COHORT: the table's median against the schedule flown, n=%d ===" % n)
    for m, name in (("gauge", "gauge (seats per departure)"), ("freq", "weekly frequency per direction")):
        print("  %-32s within +-20%% %5.1f%%   within +-50%% %5.1f%%   inside p25-p75 %5.1f%%"
              % (name, 100.0 * hit[m + "20"] / n, 100.0 * hit[m + "50"] / n, 100.0 * hit[m + "in"] / n))
    print("  level used: " + ", ".join("%d: %d" % (k, v) for k, v in sorted(lv.items())))
    print("  (the gradient-boosted prior: gauge 71.1 / 91.2, frequency 70.9 / 88.2; W10-SCHEDULE-PRIOR)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--lookup", nargs="*", default=None)
    a = ap.parse_args()
    rows = [r for r in G.rows if r["gauge"] > 0 and r["freq"] > 0]
    print("\nsample: n=%d usable of %d, cohorts %s, from %s"
          % (len(rows), len(G.rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("build: %s" % _provenance())
    table = fit(rows)
    if a.lookup is not None:
        kv = dict(s.split("=", 1) for s in a.lookup)
        k = {"scope": kv.get("scope", "I"), "haul_band": haul_band(float(kv["gcd_km"])),
             "carrier_type": "LCC" if kv.get("carrier_type", "FSC").upper() in ("LCC", "ULCC") else "FSC",
             "market_band": market_band(float(kv["base_mkt"]))}
        t = lookup(index(table), k)
        print("\nkey %s" % k)
        print("class row: %s" % {c: t[c] for c in COLS})
        car = kv.get("carrier")
        if car:
            cl = [x for x in table if x["table"] == "carrier" and x["carrier"] == car]
            best = [x for x in cl if x["haul_band"] == k["haul_band"] and x["scope"] == k["scope"]]
            print("carrier line (%s, %s, %s): %s" % (car, k["haul_band"], k["scope"],
                  ({c: best[0][c] for c in COLS} if best else "fewer than 5 comparable launches")))
            allr = [x for x in cl if not x["haul_band"]]
            print("carrier, all launches: %s" % ({c: allr[0][c] for c in COLS} if allr else "fewer than 5"))
        return
    blind_score(rows)
    n_cls = sum(1 for t in table if t["table"] == "class")
    n_car = sum(1 for t in table if t["table"] == "carrier")
    print("\ntable: %d class rows (levels 1-4), %d carrier rows" % (n_cls, n_car))
    if a.out:
        with open(a.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            for t in table:
                w.writerow({c: t.get(c, "") for c in COLS})
        with open(a.out + ".meta.txt", "w") as fh:
            fh.write("schedule_prior.csv, written %s by bt2/bt2_fit_schedule_prior.py\n"
                     "sample %s, n=%d, cohorts %s\nbuild %s\n"
                     "class key and lookup rule: see the script's docstring; min n %d (class), %d (carrier)\n"
                     % (time.strftime("%d %b %Y %H:%M"), B.BT2, len(rows),
                        ",".join(str(c) for c in B.COHORTS), _provenance(), MIN_CLASS, MIN_CARRIER))
        print("wrote %s and %s.meta.txt" % (a.out, a.out))


if __name__ == "__main__":
    main()
