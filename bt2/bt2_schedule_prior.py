#!/usr/bin/env python3
r"""The schedule prior: can the record say what an airline would launch on this pair? W10, Sep 2026.

    AVIA_BT2_DIR=E:\Avia\bt2_relaxed  py -3.12 -s bt2_schedule_prior.py
    ... --lookup base_mkt=55000 gcd=6600 intl typ=FSC carrier=UA      the check line for one pair

WHY. The calibrated model is accurate given the schedule (log line W10-PICKLE-INSAMPLE-CONFIRMED) and
scales one for one with seats (W10-RECORD-MIX-RELAXED), so Optimise cannot ask it what a market
supports. John's design of 26 September: Optimise first asks what an airline would actually launch
on a pair like this, from the record, then forecasts at that schedule. This script tests whether the
record can answer the first question at all.

THE TEST. For every launch, predict the schedule the airline flew from PRE-LAUNCH facts only: the
pair's existing O&D, its growth, haul, domestic flag, carrier type, the carrier's base strength at
the endpoints, the sister-airport flag, and the connecting competition on the pair. Three targets,
each blind by cohort with the blind configuration: annual seats (both directions, the model's own
anchor), seats per departure (gauge) and weekly frequency per direction. Scored within +-20% and
+-10% of what was flown, whole sample and by class. Seats and frequency are what Optimise needs;
gauge is reported so the new-type point (an A220 or A321XLR is a gauge the record already holds
under other types) can be read off directly.

THE CARRIER CHECK. For carriers with fifteen or more launches, the same three targets are also scored
with the carrier identity as a feature, so the value of "what has this airline launched before" is a
measured number rather than an assumption.

Nothing is written. --lookup prints the record's comparable launches for one pair, which is the
check line the payload would carry.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import math
import statistics

import numpy as np

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_claimset import _provenance, BLIND_KW
from bt2_record_mix import region_pair
from bt2_score import within


def feats(r, carrier=False):
    f = [math.log(r["base_mkt"]), math.log(max(min(r["mkt_growth"], 5.0), 0.2)),
         math.log(max(r["gcd"], 100)), 1.0 if r["dom"] else 0.0, 1.0 if r["typ"] == "LCC" else 0.0,
         r["capa"], math.log(1 + r["legs_n"]), math.log(1 + r["qcx"])]
    f += F.extra_of(r, ["base", "sister"])
    if carrier:
        f.append(G.carid.get(r["oag_carrier"], 0))
    return f


TARGETS = {"annualised seats (gauge x freq x 2 x 52)": lambda r: max(r["gauge"], 1.0) * max(r["freq"], 0.5) * 2.0 * 52.0,
           "annual seats as flown (months operated)": lambda r: r["seats_ly"],
           "seats per departure (gauge)": lambda r: max(r["gauge"], 1.0),
           "weekly frequency per direction": lambda r: max(r["freq"], 0.5)}


def score(rows, pred, label):
    v = [p / t for p, t in zip(pred, rows) if t > 0]
    w20 = 100.0 * sum(1 for x in v if within(x)) / len(v)
    w10 = 100.0 * sum(1 for x in v if within(x, 0.10)) / len(v)
    w50 = 100.0 * sum(1 for x in v if within(x, 0.50)) / len(v)
    print("    %-40s within +-20%% %5.1f%%   +-10%% %5.1f%%   +-50%% %5.1f%%   n=%d"
          % (label, w20, w10, w50, len(v)))


def blind(rows, tfn, carrier):
    out = [None] * len(rows)
    idx = {id(r): i for i, r in enumerate(rows)}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        m = G.make([], **BLIND_KW)
        m.fit(np.array([feats(r, carrier) for r in tr]), np.array([math.log(tfn(r)) for r in tr]))
        for r, p in zip(te, m.predict(np.array([feats(r, carrier) for r in te]))):
            out[idx[id(r)]] = math.exp(p)
    return out


def lookup(rows, spec):
    kv = dict(s.split("=", 1) for s in spec if "=" in s)
    bm = float(kv.get("base_mkt", 0)); gcd = float(kv.get("gcd", 0))
    dom = "dom" in spec; typ = kv.get("typ", "FSC"); car = kv.get("carrier")
    comp = [r for r in rows if r["dom"] == dom and r["typ"] == typ
            and 0.5 * bm <= r["base_mkt"] <= 2.0 * bm and 0.6 * gcd <= r["gcd"] <= 1.6 * gcd]
    print("\n=== LOOKUP: launches on pairs like base_mkt %.0f, %.0f km, %s, %s ==="
          % (bm, gcd, "domestic" if dom else "international", typ))

    def line(label, rs):
        if not rs:
            print("  %-36s none in the record" % label); return
        g = statistics.median(r["gauge"] for r in rs); f = statistics.median(r["freq"] for r in rs)
        s = sorted(r["seats_ly"] for r in rs)
        print("  %-36s n=%4d  gauge med %3.0f  freq med %.1f/wk  annual seats med %s (p25 %s, p75 %s)"
              % (label, len(rs), g, f, "{:,.0f}".format(s[len(s) // 2]),
                 "{:,.0f}".format(s[len(s) // 4]), "{:,.0f}".format(s[3 * len(s) // 4])))
    line("all comparable launches", comp)
    rp = {region_pair(r) for r in comp}
    for k in sorted(rp):
        line("  " + k, [r for r in comp if region_pair(r) == k])
    if car:
        own = [r for r in rows if r["oag_carrier"] == car]
        line("%s, every launch in the record" % car, own)
        cid = {id(r) for r in comp}
        line("%s, comparable pairs" % car, [r for r in own if id(r) in cid])
        line("%s, long-haul international" % car, [r for r in own if r["gcd"] >= 2500 and not r["dom"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookup", nargs="*", default=None)
    a = ap.parse_args()
    rows = G.rows
    F.attach(rows)
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("target: schedule flown, predicted from pre-launch facts   build: %s" % _provenance())
    if a.lookup is not None:
        lookup(rows, a.lookup); return

    print("\n=== BLIND BY COHORT: how often the predicted schedule is within the band of the one flown ===")
    for carrier in (False, True):
        print("  %s" % ("pooled prior (no carrier identity)" if not carrier else
                        "with carrier identity (carriers with >= 15 launches)"))
        for label, tfn in TARGETS.items():
            pred = blind(rows, tfn, carrier)
            score([tfn(r) for r in rows], pred, label)
            if label.startswith("annualised"):
                for name, fn in (("short-haul", lambda r: r["gcd"] < 2500), ("long-haul", lambda r: r["gcd"] >= 2500),
                                 ("long-haul EU-NA", lambda r: r["gcd"] >= 2500 and region_pair(r) == "EU-NA"),
                                 ("market 25-80k", lambda r: 25000 <= r["base_mkt"] < 80000),
                                 ("market over 80k", lambda r: r["base_mkt"] >= 80000)):
                    idx = [i for i, r in enumerate(rows) if fn(r)]
                    if idx:
                        score([tfn(rows[i]) for i in idx], [pred[i] for i in idx], "  " + name)
    print("\n  Reading: a schedule prior that lands within +-50% on most launches bounds the aircraft sweep to")
    print("  the schedules airlines actually launch on such pairs; economics then picks within that set.")
    print("  A prior no better than the +-50% band on a coin toss means launch sizing is not predictable")
    print("  from the market, and Optimise cannot stand on it.")


if __name__ == "__main__":
    main()
