#!/usr/bin/env python3
r"""The frequency range for Optimise, from the boosted prior instead of the class table. W10, 26 Sep 2026.

    cd C:\src\meridian\bt2   (workstation; the sample lives only there)
    py -3.12 -s bt2_fit_freq_range.py                                   score only, nothing written
    py -3.12 -s bt2_fit_freq_range.py --out E:\Avia\bt2_relaxed\schedule_prior_freq.pkl
    py -3.12 -s bt2_fit_freq_range.py --pair BLQ-JFK:UA GOA-JFK:UA SOU-JFK:UA   live pairs, via route_context

WHY. The class table (bt2_fit_schedule_prior.py, log W10-SCHEDULE-PRIOR-TABLE) holds on gauge but its
frequency median lands within +-20% of the flown frequency on 30.2% of launches against 70.9% for the
gradient-boosted prior (W10-SCHEDULE-PRIOR). As a p25-p75 bound the table is calibrated (48.7% inside),
so its fault is width, not bias. This script tests whether the boosted prior gives a NARROWER band at
the same coverage, which is the only thing that would justify replacing the table's frequency columns.

A LEAK FOUND ON THE WAY, and the reason for arm L below. The boosted prior's feature capa is
capture_L.csv cap_actual, which bt2_capture.py computes AT THE ACTUAL LAUNCH FREQUENCY
(cap_from(..., f_act), f_act = wk_freq_dir). So W10-SCHEDULE-PRIOR's 70.9% on frequency was predicted
partly from the answer. Optimise cannot know the frequency before choosing it. The honest feature is
cap_f5, the same capture at a standard five a week, which bt2_capture writes beside it and which the
live path reproduces by calling route_context at freq=5. Arm L reruns the leaky set so the size of
the leak is measured, not assumed; arm H is the candidate.

ARMS, all blind by cohort (train on five cohorts, score the sixth), quantile loss at 0.25, 0.50, 0.75,
blind configuration (BLIND_KW: lr 0.04, it 600, minleaf 60, l2 5.0), target log weekly frequency per
direction (floor 0.5):
  T  the class table's frequency p25 / median / p75, refitted on each training fold
  L  boosted, W10-SCHEDULE-PRIOR's features as they were (capa at the flown frequency): LEAKY, reference
  H  boosted, the same features with capa replaced by cap_f5: THE CANDIDATE
Scored on the same launches: median within +-20% and +-50%, flown frequency inside p25-p75, and the
median band width p75 / p25. By haul band as well, since long-haul is what the stand will test.

DECISION RULE, stated before the run: H replaces the table's frequency columns if its p25-p75 holds
the flown frequency on 45-55% of launches AND its median width is narrower than T's on the same
launches. Otherwise the table stays and this script's result is logged as a negative.

FEATURES OF ARM H, in order; W1 must build exactly these, from route_context.build(a, b, carrier,
aircraft_seats=<any>, freq=5, year=<latest Sabre year>) so that ctx["capa"] IS cap_f5:
   0 log base_mkt                      ctx["base_mkt"]
   1 log clamp(mkt_growth, 0.2, 5.0)   ctx["mkt_growth"]
   2 log max(gcd_km, 100)              ctx["gcd"]
   3 domestic 1/0                      ctx["dom"]
   4 LCC 1/0                           ctx["typ"] == "LCC"
   5 cap_f5                            ctx["capa"] at freq=5, and ONLY at freq=5
   6 log(1 + legs_n)                   ctx["legs_n"]
   7 log(1 + qcx)                      ctx["qcx"]
   8 log1p(min(base_seats_a, base_seats_b))       0 seats is 0; NaN only when all four are absent
   9 log1p(max(base_seats_a, base_seats_b))
  10 base_seats_a / airport_seats_a (0 when the airport total is 0)
  11 base_seats_b / airport_seats_b
  12 sister flag 1/0                   NaN when ctx["_provenance"]["sister_flag_resolved"] is False
features_from_context() below is that recipe; the pickle carries worked examples (inputs and the
expected p25 / median / p75) so the app can assert it reproduces them before using the model.

OUTPUT with --out: a pickle holding the three fitted estimators (all six cohorts), the feature names,
the blind scores, the build stamp and the parity examples. Nothing under app/ is touched.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import math
import os
import pickle
import statistics
import sys
import time
from collections import defaultdict

import numpy as np

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
import bt2_fit_schedule_prior as T
from bt2_claimset import _provenance, BLIND_KW
from bt2_score import within

QS = (0.25, 0.50, 0.75)
FEATURES = ["log_base_mkt", "log_growth", "log_gcd", "dom", "lcc", "cap_f5", "log1p_legs_n",
            "log1p_qcx", "log1p_base_min", "log1p_base_max", "base_share_a", "base_share_b", "sister"]


def _vec(base_mkt, growth, gcd, dom, lcc, cap, legs_n, qcx, base, sister):
    f = [math.log(base_mkt), math.log(max(min(growth, 5.0), 0.2)), math.log(max(gcd, 100)),
         1.0 if dom else 0.0, 1.0 if lcc else 0.0, float(cap), math.log(1 + legs_n), math.log(1 + qcx)]
    if base:
        sa, sb, ta, tb = base
        f += [math.log1p(min(sa, sb)), math.log1p(max(sa, sb)), (sa / ta if ta else 0.0), (sb / tb if tb else 0.0)]
    else:
        f += [float("nan")] * 4
    f.append(float("nan") if sister is None else float(sister))
    return f


def feats(r, leaky=False):
    """A record row. leaky=True uses capa (capture at the FLOWN frequency), arm L only."""
    return _vec(r["base_mkt"], r["mkt_growth"], r["gcd"], r["dom"], r["typ"] == "LCC",
                r["capa"] if leaky else r["cap5"], r["legs_n"], r["qcx"], r.get("_base"), r.get("_sister"))


def features_from_context(ctx):
    """A live route. ctx is route_context.build(..., freq=5, ...), so ctx['capa'] is cap_f5."""
    if abs(float(ctx["freq"]) - 5.0) > 1e-9:
        raise ValueError("features_from_context needs route_context.build at freq=5 (capa must be cap_f5), got freq=%s"
                         % ctx["freq"])
    bs = (ctx.get("base_seats_a"), ctx.get("base_seats_b"), ctx.get("airport_seats_a"), ctx.get("airport_seats_b"))
    # As in training (bt2_g12_exp.attach): a carrier with no seats at an endpoint is 0, not missing;
    # NaN only when base strength could not be measured at all (no OAG store, all four absent).
    base = None if all(x is None for x in bs) else tuple(float(x or 0.0) for x in bs)
    sister = ctx["sister_flag"] if ctx.get("_provenance", {}).get("sister_flag_resolved") else None
    return _vec(ctx["base_mkt"], ctx["mkt_growth"], ctx["gcd"], ctx["dom"], ctx["typ"] == "LCC",
                ctx["capa"], ctx["legs_n"], ctx["qcx"], base, sister)


def y(r):
    return math.log(max(r["freq"], 0.5))


def fit3(X, Y):
    ms = []
    for q in QS:
        m = G.make([], **BLIND_KW)
        m.set_params(quantile=q)
        m.fit(X, Y)
        ms.append(m)
    return ms


def pred3(ms, X):
    P = np.exp(np.column_stack([m.predict(X) for m in ms]))
    return np.sort(P, axis=1)           # quantile crossing, if any, resolved by sorting


def blind(rows):
    out = {k: [None] * len(rows) for k in "TLH"}
    pos = {id(r): i for i, r in enumerate(rows)}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        idx = T.index(T.fit(tr))
        for r in te:
            t = T.lookup(idx, T.key_of(r))
            out["T"][pos[id(r)]] = (float(t["freq_p25"]), float(t["freq_med"]), float(t["freq_p75"]))
        Ytr = np.array([y(r) for r in tr])
        for arm, leaky in (("L", True), ("H", False)):
            ms = fit3(np.array([feats(r, leaky) for r in tr]), Ytr)
            for r, p in zip(te, pred3(ms, np.array([feats(r, leaky) for r in te]))):
                out[arm][pos[id(r)]] = tuple(float(x) for x in p)
        print("  cohort %d done" % L)
    return out


def score(rows, band):
    n = len(rows)
    w20 = sum(within(b[1] / r["freq"]) for r, b in zip(rows, band))
    w50 = sum(within(b[1] / r["freq"], 0.50) for r, b in zip(rows, band))
    ins = sum(b[0] <= r["freq"] <= b[2] for r, b in zip(rows, band))
    wid = statistics.median(b[2] / b[0] for b in band if b[0] > 0)
    return dict(n=n, w20=100.0 * w20 / n, w50=100.0 * w50 / n, inside=100.0 * ins / n, width=wid)


def report(rows, out):
    names = {"T": "T class table", "L": "L boosted, capa at flown freq (LEAKY)", "H": "H boosted, cap_f5 (candidate)"}
    res = {}
    print("\n=== BLIND BY COHORT: weekly frequency per direction, n=%d ===" % len(rows))
    print("  %-40s %9s %9s %14s %14s" % ("arm", "med+-20%", "med+-50%", "inside p25-p75", "width p75/p25"))
    for k in "TLH":
        s = score(rows, out[k])
        res[k] = s
        print("  %-40s %8.1f%% %8.1f%% %13.1f%% %14.2f" % (names[k], s["w20"], s["w50"], s["inside"], s["width"]))
    print("\n  by haul band (T / H): inside p25-p75, width p75/p25, n")
    hb = defaultdict(list)
    for i, r in enumerate(rows):
        hb[T.haul_band(r["gcd"])].append(i)
    res["by_haul"] = {}
    for h in sorted(hb):
        ii = hb[h]
        rs = [rows[i] for i in ii]
        st = score(rs, [out["T"][i] for i in ii])
        sh = score(rs, [out["H"][i] for i in ii])
        res["by_haul"][h] = {"T": st, "H": sh}
        print("  %s  T %5.1f%% x%.2f   H %5.1f%% x%.2f   n=%d" % (h, st["inside"], st["width"], sh["inside"], sh["width"], len(rs)))
    h, t = res["H"], res["T"]
    ok = 45.0 <= h["inside"] <= 55.0 and h["width"] < t["width"]
    print("\nDECISION RULE (45-55%% inside AND narrower than the table): %s. H inside %.1f%%, width %.2f against table %.2f"
          % ("MET, H replaces the table's frequency columns" if ok else "NOT MET, the table stays",
             h["inside"], h["width"], t["width"]))
    res["decision"] = ok
    return res


def live_pairs(specs, ms):
    from bt2_paths import find_app
    sys.path.insert(0, find_app())
    import duckdb
    import route_context as RC
    c = duckdb.connect(RC._store("sabre"), read_only=True)
    year = int(c.execute("SELECT max(source_year) FROM sabre").fetchone()[0])
    c.close()
    print("\nbase year %d (latest Sabre source year, as the app passes it)" % year)
    out = []
    for spec in specs:
        pair, _, car = spec.partition(":")
        a, b = pair.split("-")
        car = car or "UA"
        ctx = RC.build(a, b, car, aircraft_seats=200, freq=5, year=year)
        if not ctx.get("ok"):
            print("  %s-%s %s: route context refused: %s" % (a, b, car, "; ".join(ctx.get("missing", []))))
            continue
        x = features_from_context(ctx)
        p = pred3(ms, np.array([x]))[0]
        k = {"scope": "D" if ctx["dom"] else "I", "haul_band": T.haul_band(ctx["gcd"]),
             "carrier_type": ctx["typ"], "market_band": T.market_band(ctx["base_mkt"])}
        print("  %s-%s %s: base_mkt %s, %.0f km, %s | H frequency p25 / median / p75 %.1f / %.1f / %.1f per week per direction"
              % (a, b, car, "{:,.0f}".format(ctx["base_mkt"]), ctx["gcd"], k, p[0], p[1], p[2]))
        out.append({"pair": "%s-%s" % (a, b), "carrier": car, "features": x, "expected": [float(v) for v in p]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--pair", nargs="*", default=None)
    a = ap.parse_args()
    rows = [r for r in G.rows if r["gauge"] > 0 and r["freq"] > 0]
    F.attach(rows)
    nocap5 = sum(1 for r in rows if not (r.get("cap5") and r["cap5"] > 0))
    print("\nsample: n=%d, cohorts %s, from %s; rows with no cap_f5: %d"
          % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2, nocap5))
    print("build: %s" % _provenance())
    X = np.array([feats(r) for r in rows])
    ms = fit3(X, np.array([y(r) for r in rows]))
    if a.pair:
        live_pairs(a.pair, ms)
        return
    res = report(rows, blind(rows))
    if a.out:
        ex = []
        for r in rows[:: max(1, len(rows) // 5)][:5]:
            x = feats(r)
            ex.append({"pair": "%s-%s" % (r["a"], r["b"]), "cohort": r["cohort"], "features": x,
                       "expected": [float(v) for v in pred3(ms, np.array([x]))[0]]})
        blob = {"version": "freq-range 1.0 26Sep2026", "features": FEATURES, "quantiles": QS,
                "estimators": ms, "target": "log weekly frequency per direction, floor 0.5; predictions are exp()",
                "live_recipe": "features_from_context(route_context.build(a, b, carrier, aircraft_seats=any, freq=5, year=latest Sabre year))",
                "n_train": len(rows), "cohorts": list(B.COHORTS), "sample": B.BT2, "blind": res,
                "decision_rule_met": res["decision"], "parity_examples": ex, "build": _provenance(),
                "written": time.strftime("%d %b %Y %H:%M")}
        with open(a.out, "wb") as fh:
            pickle.dump(blob, fh)
        print("wrote %s (%s bytes); decision rule %s" % (a.out, "{:,}".format(os.path.getsize(a.out)),
                                                          "MET" if res["decision"] else "NOT MET"))


if __name__ == "__main__":
    main()
