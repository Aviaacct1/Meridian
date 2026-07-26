#!/usr/bin/env python3
r"""
Avia Solutions - systematic per-airport capture correction + leave-one-out assessment (John's structural test).
==================================================================================================
A secondary airport (SJC under SFO) is systematically under-forecast because the catchment model sends too much
of its metro to the primary. Rather than a one-off SJC fudge, build a correction for EVERY origin airport from
the whole back-test (all years), shrunk toward no-correction for thin airports, and assess it HONESTLY by
leave-one-out: correct each route by its airport's factor computed from that airport's OTHER routes, so no route
scores itself. Then read whether the aggregate within-+/-20% rises.

    factor[origin] = exp(-shrunk mean log(fc/out) over the airport's routes)    (centres the airport on 1.0)
    LOO grade      = fc/out x factor_excluding_this_route                        (the honest test)

CAVEAT (why the year-split version failed T7): LOO tests whether an airport's routes are internally consistent,
NOT whether the bias holds across eras. A good LOO centres the historical track record and helps SJC today, but
is weaker evidence for a genuinely-future forecast. Use it to fix the record + assess the cohort, eyes open.

    py -3.12 build_airport_capture.py bt_v2_6yr.csv --out airport_capture_factors.json

Then re-run the back-test with  --airport-capture airport_capture_factors.json  to regenerate the track record
and confirm the aggregate +/-20%. Reads the CSV only.
"""
import argparse, csv, math


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _w20(xs):
    return sum(1 for x in xs if 0.8 <= x <= 1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--min-routes", type=int, default=4, help="min routes to correct an airport (else no correction)")
    ap.add_argument("--shrink", type=float, default=4.0, help="partial-pool strength toward no-correction")
    ap.add_argument("--clamp", type=float, default=0.69, help="max |log factor| (~x2 cap)")
    ap.add_argument("--forecastable-only", action="store_true")
    ap.add_argument("--out", default="airport_capture_factors.json")
    a = ap.parse_args()
    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        out = _f(r.get("outturn_pax")); fc = _f(r.get("forecast_pax")); fo = _f(r.get("fc_over_out"))
        nat = _f(r.get("natural")); p2p = _f(r.get("p2p_outturn"))
        if fo is None and out and fc:
            fo = fc / out
        if out is None or out < a.min_outturn or fo is None or fo <= 0:
            continue
        if a.forecastable_only and (nat is None or p2p is None or nat < p2p):
            continue
        rows.append({"dep": (r.get("dep") or "").upper(), "lfo": math.log(fo), "fo": fo})
    if not rows:
        print("No graded routes."); return

    by_ap = {}
    for r in rows:
        by_ap.setdefault(r["dep"], []).append(r["lfo"])
    K = a.shrink

    def shrunk_bias(logs):        # mean log bias shrunk toward 0 (no correction), clamped
        b = sum(logs) / (len(logs) + K)          # shrink toward 0: (sum + K*0)/(n+K)
        return max(-a.clamp, min(a.clamp, b))

    factors = {}
    for ap_, logs in by_ap.items():
        if len(logs) >= a.min_routes:
            factors[ap_] = round(math.exp(-shrunk_bias(logs)), 4)      # >1 lifts an under-forecast airport

    # LEAVE-ONE-OUT aggregate assessment (the honest test)
    base = [r["fo"] for r in rows]
    loo = []
    for r in rows:
        logs = by_ap[r["dep"]]
        if len(logs) >= a.min_routes:
            others = [x for x in logs if x is not r["lfo"]]           # exclude this route's own log
            # rebuild others properly (identity compare is unreliable for equal floats): drop one occurrence
            others = logs[:]; others.remove(r["lfo"])
            f = math.exp(-shrunk_bias(others))
            f = max(math.exp(-a.clamp), min(math.exp(a.clamp), f))
            loo.append(r["fo"] * f)
        else:
            loo.append(r["fo"])
    full = [r["fo"] * factors.get(r["dep"], 1.0) for r in rows]      # in-sample: each route x its airport's factor
    n = len(rows)
    print(f"\nAIRPORT CAPTURE CORRECTION ({a.csv}): {n} routes, {len(factors)} airports corrected (>= {a.min_routes} routes, shrink K={a.shrink})")
    print(f"  BEFORE:                median fc/out {_median(base):.2f}   within +/-20% {100*_w20(base)//n}%   median|log| {_median([abs(math.log(v)) for v in base]):.3f}")
    print(f"  AFTER (in-sample/full):    median {_median(full):.2f}   within +/-20% {100*_w20(full)//n}%   median|log| {_median([abs(math.log(v)) for v in full]):.3f}")
    print(f"  AFTER (leave-one-out):     median {_median(loo):.2f}   within +/-20% {100*_w20(loo)//n}%   median|log| {_median([abs(math.log(v)) for v in loo]):.3f}")
    df = _w20(full) - _w20(base); d = _w20(loo) - _w20(base)
    print(f"  aggregate within +/-20%:  in-sample {df:+d} ({100*df/n:+.1f}pp)   |   leave-one-out {d:+d} ({100*d/n:+.1f}pp)")
    print(f"  gap (in-sample - LOO) = {100*(df-d)/n:+.1f}pp = the non-generalising / noise portion; a SMALL gap means")
    print(f"  the gain is mostly real systematic bias (helps future forecasts too), a LARGE gap means mostly overfit.")
    # show the biggest lifts (under-forecasting airports), and SJC
    ex = sorted(factors.items(), key=lambda kv: -kv[1])[:10]
    print("  biggest lifts (under-forecast airports): " + ", ".join(f"{k} {v:.2f}x" for k, v in ex))
    if "SJC" in factors:
        print(f"  SJC factor: {factors['SJC']:.2f}x  (n={len(by_ap['SJC'])} routes)")

    import json
    json.dump({"meta": {"min_routes": a.min_routes, "shrink": K, "clamp": a.clamp,
                        "n_airports": len(factors), "loo_within20_delta_pp": round(100 * d / n, 1)},
               "factors": factors}, open(a.out, "w"), indent=0)
    print(f"\n  wrote {a.out}: {len(factors)} origin-airport factors.")
    print("  If the LOO +/-20% RISES, the process helps the cohort -> re-run the back-test with")
    print("  --airport-capture " + a.out + " to recentre the track record and confirm. If it FALLS, it's the")
    print("  overfit that failed before - keep only the specific well-evidenced airports (SJC) as manual overrides.")


if __name__ == "__main__":
    main()
