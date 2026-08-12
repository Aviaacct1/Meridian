#!/usr/bin/env python3
r"""One sample, both numbers: the calibrated model and the Cortex path on the PINNED route set.

    py -3.12 bt2_pin_score.py --arm C:\src\meridian\app\backtest_control_11Aug2026.csv
                              --pin E:\Avia\backtest_routes_11Aug2026.json

WHY THIS EXISTS. The 60.4% and the 16.8% have never been a comparison, and the reason is larger
than the sample. Three things differ at once, and every one of them moves a score:

  POPULATION   the calibrated model was scored on its own discovery, a VIRGIN-pair rule (at least
               1,500 nonstop passengers in the launch year, under 500 in each of the two years
               before) with a market floor and a capacity-ratio ceiling. The Cortex path was scored
               on the pin, an OAG new-service rule with a minimum frequency of 3, a minimum sector
               of 1,500 km and a minimum outturn of 3,000. Neither rule is a subset of the other.

  TARGET       the calibrated model is graded against Sabre itinerary='NON-STOP' passengers on the
               pair, which is the LOCAL market and excludes anyone connecting at either end
               (bt2_discover.py line 64). The Cortex path's 16.8% is fc_over_out, graded against
               sector traffic, which counts every passenger on the sector INCLUDING connecting feed
               (backtest.py lines 246 to 264). The second quantity is larger than the first on
               79.3% of routes and equal on the rest.

  YEAR         the calibrated model forecasts the LAUNCH year and is graded there. The pin is
               graded at offset 1, the first full year.

So this script does not report one number. It reports the calibrated model against BOTH denominators
the pin carries, beside the Cortex path on the same routes, and it says how many of the 4,342 the
calibrated model can answer at all. That last figure is not a footnote: it is the size of the leaked
secondary airport problem, measured rather than argued.

WHAT IT DOES NOT DO. It runs no engine and no forecast. Every calibrated-model input is read from
the artefacts the training chain already built (capture_L.csv, launch_profile_L.csv,
base_strength_L.json, metro_ns_L.json), and every Cortex number is read from the arm CSV. So it
costs one refit per cohort and no store scans, which is minutes.

READ THIS BEFORE QUOTING ANY NUMBER IT PRINTS. The re-anchored figures apply the model's predicted
passengers-per-seat to the capacity the route actually operated in the first full year, taken from
the arm CSV. That is what makes the two engines comparable on one denominator. It assumes the
passengers-per-seat the model read for the launch year still holds a year later. The native figures
beside them are the model on its own terms, so the cost of the assumption is visible rather than
buried.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import json
import math
import os
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Score the calibrated model on the pinned back-test routes.")
    p.add_argument("--arm", required=True, help="a backtest.py arm CSV run against the pin")
    p.add_argument("--pin", default=None, help="the pinned route list JSON, for coverage accounting")
    p.add_argument("--cohorts", default="2016,2017,2018,2024",
                   help="launch years, and they must match the pin's --years")
    p.add_argument("--bt2-dir", default=None,
                   help="the sample folder, e.g. E:\\Avia\\bt2_relaxed. Sets AVIA_BT2_DIR")
    p.add_argument("--out", default=None, help="write the joined per-route rows to this CSV")
    p.add_argument("--band", type=float, default=0.20, help="the accuracy band, default +-20%%")
    return p.parse_args()


def binom_two_sided(k, n):
    """Exact two-sided binomial p at 0.5. Used rather than scipy so the script has no new dependency."""
    if n == 0:
        return 1.0
    def c(a, b):
        return math.comb(a, b)
    lo = min(k, n - k)
    tail = sum(c(n, i) for i in range(0, lo + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def mcnemar(pairs):
    """pairs is a list of (a_hit, b_hit). Returns b_only, a_only, p for a moving to b."""
    b_only = sum(1 for a, b in pairs if b and not a)
    a_only = sum(1 for a, b in pairs if a and not b)
    return b_only, a_only, binom_two_sided(min(b_only, a_only), b_only + a_only)


def band_rate(ratios, band):
    n = len(ratios)
    if not n:
        return 0.0, 0
    hit = sum(1 for x in ratios if x and abs(x - 1.0) <= band)
    return 100.0 * hit / n, n


def main():
    a = parse_args()
    os.environ["AVIA_BT2_COHORTS"] = a.cohorts
    if a.bt2_dir:
        os.environ["AVIA_BT2_DIR"] = a.bt2_dir

    # Imported here and not at the top: bt2_lib reads AVIA_BT2_COHORTS and AVIA_BT2_DIR at import
    # time and bt2_gbm builds its row set on import, so the environment has to be set first.
    import bt2_gbm as G
    import bt2_lib as B
    import bt2_g12_exp as F

    SPEC, G12 = ["car", "qcx", "gro"], ["base", "sister"]
    BLIND_KW = dict(lr=0.04, it=600, minleaf=60, l2=5.0)    # bt2_build_v13.py line 43, unchanged

    rows = G.rows
    F.attach(rows)
    print("CALIBRATED MODEL SAMPLE")
    print("  folder   %s" % B.BT2)
    print("  cohorts  %s" % ",".join(str(c) for c in B.COHORTS))
    print("  routes   %d" % len(rows))

    # THE BLIND PREDICTION, leave-one-cohort-out, the same loop and the same parameters as
    # bt2_build_v13. No route contributes to the model that forecasts it.
    blind = {}
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        if not te:
            continue
        Xtr, ytr, Xte = F.X_of(tr, G12), G.y_of(tr), F.X_of(te, G12)
        m = G.make(SPEC, **BLIND_KW)
        m.set_params(quantile=0.5)
        m.fit(Xtr, ytr)
        for r, p in zip(te, m.predict(Xte)):
            blind[id(r)] = math.exp(float(p))              # predicted passengers per seat
    print("  blind predictions produced for %d of them" % len(blind))

    native = [(r["seats_ly"] * blind[id(r)]) / r["actual"] for r in rows
              if id(r) in blind and r["actual"] > 0]
    rate, n = band_rate(native, a.band)
    print("  native blind, its own population and its own target: %.1f%% within +-%.0f%%, n=%d"
          % (rate, 100 * a.band, n))
    print("  (Sabre throughout. The published 60.4%% regrades US domestic launches onto the DOT,")
    print("   which this script does not do, because the pin is graded against Sabre.)")

    # THE PIN, and the arm the Cortex path was scored on.
    pin_n = None
    if a.pin and os.path.exists(a.pin):
        with open(a.pin) as fh:
            pin = json.load(fh)
        pin_n = len(pin if isinstance(pin, list) else pin.get("routes", []))

    arm = {}
    dup = 0
    with open(a.arm, newline="") as fh:
        for r in csv.DictReader(fh):
            k = (min(r["dep"], r["arr"]), max(r["dep"], r["arr"]), int(r["year"]))
            if k in arm:
                # Two directional rows collapsing onto one alphabetised pair. Counted and reported
                # rather than overwritten in silence: a silent overwrite here would quietly halve
                # the sample and nothing would say so.
                dup += 1
                continue
            arm[k] = r
    print("\nCORTEX PATH ARM")
    print("  file     %s" % a.arm)
    print("  rows     %d graded" % len(arm))
    if pin_n:
        print("  pin      %d routes, so %d produced no gradeable row" % (pin_n, pin_n - len(arm)))
    if dup:
        print("  NOTE     %d rows collapsed onto a pair already seen and were dropped" % dup)

    # THE JOIN. The calibrated model keys on the alphabetised pair and the cohort; a pair with two
    # launching carriers in one year is resolved on the carrier the arm recorded, and reported when
    # it cannot be.
    by_key = {}
    for r in rows:
        by_key.setdefault((r["a"], r["b"], int(r["cohort"])), []).append(r)

    joined, ambiguous = [], 0
    for k, arow in arm.items():
        cands = by_key.get(k)
        if not cands:
            continue
        r = cands[0]
        if len(cands) > 1:
            match = [c for c in cands if (c.get("oag_carrier") or "") == (arow.get("carrier") or "")]
            if len(match) == 1:
                r = match[0]
            else:
                ambiguous += 1
                continue
        if id(r) not in blind:
            continue
        joined.append((arow, r, blind[id(r)]))

    print("\nOVERLAP")
    print("  the calibrated model can answer %d of the %d routes the arm graded, %.1f%%"
          % (len(joined), len(arm), 100.0 * len(joined) / max(len(arm), 1)))
    if ambiguous:
        print("  %d skipped: two launching carriers on one pair and year, carrier did not resolve"
              % ambiguous)
    print("  THE REMAINDER IS THE POINT OF TASK 2. A route is absent because the pair was not")
    print("  virgin by the calibrated rule, or its market sat below the training floor, which is")
    print("  the leaked secondary airport, or no capture row was ever built for it. Separating")
    print("  those three needs a discovery pass and is not attempted here.")

    def col(rw, name):
        v = rw.get(name)
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    out_rows = []
    cx_p2p, cx_out, bt_p2p, bt_out, bt_native = [], [], [], [], []
    for arow, r, lf in joined:
        cap = col(arow, "capacity")                  # OAG operated seats in the graded year
        p2p = col(arow, "p2p_outturn")
        tot = col(arow, "outturn_pax")
        fc_re = (lf * cap) if cap else None          # the model re-anchored on the graded year
        row = {
            "route": arow["route"], "year": arow["year"], "carrier": arow.get("carrier", ""),
            "type": arow.get("type", ""), "gcd_km": arow.get("gcd_km", ""),
            "p2p_outturn": p2p, "outturn_pax": tot, "capacity_graded_year": cap,
            "cx_forecast": col(arow, "forecast_pax"), "cx_captured": col(arow, "captured_uncapped"),
            "cx_over_p2p": col(arow, "fc_over_p2p"), "cx_over_out": col(arow, "fc_over_out"),
            "bt2_pax_per_seat": round(lf, 4),
            "bt2_native_forecast": round(r["seats_ly"] * lf),
            "bt2_native_actual": r["actual"],
            "bt2_native_ratio": round((r["seats_ly"] * lf) / r["actual"], 3) if r["actual"] else None,
            "bt2_forecast_regraded": round(fc_re) if fc_re else None,
            "bt2_over_p2p": round(fc_re / p2p, 3) if (fc_re and p2p) else None,
            "bt2_over_out": round(fc_re / tot, 3) if (fc_re and tot) else None,
            "base_mkt": r["base_mkt"], "seats_ly_launch": r["seats_ly"],
        }
        out_rows.append(row)
        cx_p2p.append(row["cx_over_p2p"]); cx_out.append(row["cx_over_out"])
        bt_p2p.append(row["bt2_over_p2p"]); bt_out.append(row["bt2_over_out"])
        bt_native.append(row["bt2_native_ratio"])

    print("\nONE SAMPLE, BOTH NUMBERS. n=%d routes, every one scored by both." % len(out_rows))
    print("  Local market, forecast over PURE P2P outturn in the graded year")
    r1, _ = band_rate([x for x in cx_p2p if x], a.band)
    r2, _ = band_rate([x for x in bt_p2p if x], a.band)
    print("    Cortex path (captured, pre-capacity-cap)   %5.1f%% within +-%.0f%%" % (r1, 100 * a.band))
    print("    calibrated model, re-anchored              %5.1f%%" % r2)
    pairs = [(abs((c or 9) - 1) <= a.band, abs((b or 9) - 1) <= a.band)
             for c, b in zip(cx_p2p, bt_p2p) if c and b]
    bo, ao, p = mcnemar(pairs)
    print("    +%d -%d, p=%.4f" % (bo, ao, p))

    print("  Whole sector, forecast over TOTAL outturn including connecting feed")
    r3, _ = band_rate([x for x in cx_out if x], a.band)
    r4, _ = band_rate([x for x in bt_out if x], a.band)
    print("    Cortex path (carried, capacity-capped)     %5.1f%% within +-%.0f%%" % (r3, 100 * a.band))
    print("    calibrated model, re-anchored              %5.1f%%" % r4)
    pairs = [(abs((c or 9) - 1) <= a.band, abs((b or 9) - 1) <= a.band)
             for c, b in zip(cx_out, bt_out) if c and b]
    bo, ao, p = mcnemar(pairs)
    print("    +%d -%d, p=%.4f" % (bo, ao, p))
    print("    READ THIS ONE WITH CARE. The calibrated model forecasts the LOCAL market and is")
    print("    being held against a denominator that includes connecting passengers, so it is")
    print("    expected to read low. It is printed because the client's number is the sector total.")

    r5, _ = band_rate([x for x in bt_native if x], a.band)
    print("  Control, the calibrated model on its own terms over these same routes: %.1f%%" % r5)

    if a.out:
        if out_rows:
            with open(a.out, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
                w.writeheader()
                w.writerows(out_rows)
            print("\nwrote %d rows to %s" % (len(out_rows), a.out))
        else:
            print("\nnothing to write: the join produced no rows")

    return 0


if __name__ == "__main__":
    sys.exit(main())
