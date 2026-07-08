#!/usr/bin/env python3
r"""
Avia Solutions - per-airport capture calibration (John's hypothesis, accuracy plan T7).
==================================================================================================
Learns a per-origin-airport capture factor from the decomposition back-test: an airport that
consistently captures more or less than the general catchment model gets a factor from its OWN past
launches, applied to the P2P capture of future forecasts. The factor corrects the airport-SPECIFIC
deviation from the global mean (not the global bias, which cancels against the market leg), shrunk
toward 1.0 for airports with little history (partial pooling).

DISCIPLINE (Fable): fit on 2016-2018 ONLY (--fit-years); the factors are then applied out-of-sample and
2019/2024 are the validation. Reads a --decompose CSV; writes airport_capture.json.

    py -3.12 build_airport_factors.py E:\Avia\QSI\backtests\decomp_6yr.csv --fit-years 2016,2017,2018 \
        --out airport_capture.json

Then validate:  backtest.py ... --airport-capture airport_capture.json   (held-out years tell the truth).
"""
import argparse, csv, json, math


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018", help="years to LEARN factors from (never the held-out)")
    ap.add_argument("--shrink", type=float, default=3.0, help="partial-pooling strength toward 1.0")
    ap.add_argument("--clamp", type=float, default=0.5, help="max |log factor| (cap the correction)")
    ap.add_argument("--out", default="airport_capture.json")
    a = ap.parse_args()
    fit = set(a.fit_years.split(","))
    by_ap = {}
    all_lc = []
    for r in csv.DictReader(open(a.csv, newline="")):
        if str(r.get("year")) not in fit:
            continue
        ma = _f(r.get("d_mkt_asif")); mo = _f(r.get("d_mkt_outturn")); g = _f(r.get("d_growth_applied"))
        cap = _f(r.get("d_captured")); p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural"))
        if None in (ma, mo, g, cap, p2p) or min(ma, mo, g, cap, p2p) <= 0:
            continue
        if nat is None or nat < p2p:      # forecastable only (market pre-existed)
            continue
        lc = math.log((cap * mo) / (ma * g * p2p))    # log(L_capture)
        by_ap.setdefault(r.get("dep") or "?", []).append(lc)
        all_lc.append(lc)
    if not all_lc:
        print("No forecastable fit-year rows with --decompose fields."); return
    gmean = sum(all_lc) / len(all_lc)
    K = a.shrink
    factors = {}
    for apn, xs in by_ap.items():
        shrunk = (sum(xs) + K * gmean) / (len(xs) + K)      # shrink toward the global
        dev = shrunk - gmean                                 # airport-specific deviation
        dev = max(-a.clamp, min(a.clamp, dev))               # cap the correction
        factors[apn] = round(math.exp(-dev), 4)              # >1 lifts capture, <1 trims it
    meta = {"global_log": round(gmean, 4), "shrink": K, "clamp": a.clamp,
            "fit_years": sorted(fit), "n_airports": len(factors), "n_routes": len(all_lc)}
    json.dump({"meta": meta, "factors": factors}, open(a.out, "w"), indent=0)
    lo = min(factors.values()); hi = max(factors.values())
    print(f"wrote {a.out}: {len(factors)} airports from {len(all_lc)} fit-year routes "
          f"(fit {sorted(fit)}); factor range {lo:.2f}-{hi:.2f}")
    ex = sorted(factors.items(), key=lambda kv: kv[1])
    print("  strongest trims (over-capturers):  " + ", ".join(f"{k} {v:.2f}" for k, v in ex[:6]))
    print("  strongest lifts (under-capturers): " + ", ".join(f"{k} {v:.2f}" for k, v in ex[-6:]))


if __name__ == "__main__":
    main()
