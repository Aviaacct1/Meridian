#!/usr/bin/env python3
r"""
Avia Solutions - isolated A/B for the per-airport capture factor (accuracy plan T7 validation).
==================================================================================================
Measures the airport factor's effect on ONLY the routes it touched, exactly, from a single held-out
backtest CSV + the factor JSON - no second run, no dilution. Because the factor multiplies capture,
fc/p2p_with = fc/p2p_without x factor, so the counterfactual (without the factor) is exact:
fc_without = fc/p2p (in the CSV) / factor.

Run the CSV on the HELD-OUT years (2019, 2024) with the factors LEARNED on 2016-2018:

    py -3.12 compare_airport_factor.py E:\Avia\QSI\backtests\held_apf.csv airport_capture.json

Reports, on the corrected forecastable routes: within +/-20% and median |log-error| WITH vs WITHOUT the
factor, and the share of routes it moved closer to outturn. This is the honest, isolated bank-or-bin test.
"""
import argparse, csv, json, math


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("factors_json")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--tol", type=float, default=0.01, help="min |1-factor| to count a route as corrected")
    a = ap.parse_args()
    fj = json.load(open(a.factors_json))
    factors = fj.get("factors", fj)
    rows = list(csv.DictReader(open(a.csv, newline="")))
    recs = []
    for r in rows:
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        if p2p is None or p2p < a.min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p:          # forecastable only
            continue
        fac = _f(factors.get(r.get("dep"))) or 1.0
        if abs(1.0 - fac) < a.tol:            # route not materially corrected
            continue
        fo = fw / fac                          # exact counterfactual (without the factor)
        recs.append({"y": str(r.get("year")), "fw": fw, "fo": fo,
                     "we": abs(math.log(fw)), "woe": abs(math.log(fo))})
    if not recs:
        print("No corrected forecastable routes in this CSV (no origin had a non-trivial factor). "
              "Are these held-out routes from airports with 2016-2018 history?")
        return

    def w20(rs):
        return sum(1 for x in rs if 0.8 <= x <= 1.2)

    def _report(name, rs):
        n = len(rs)
        if n < 10:
            print(f"  {name}: n={n} (too few)"); return
        fw_r = [x["fw"] for x in rs]; fo_r = [x["fo"] for x in rs]
        we = [x["we"] for x in rs]; woe = [x["woe"] for x in rs]
        imp = sum(1 for x in rs if x["we"] < x["woe"] - 1e-9)
        d20 = w20(fw_r) - w20(fo_r)
        print(f"\n  {name}: corrected forecastable n={n}")
        print(f"                       within +/-20%     median fc/p2p     median |log err|")
        print(f"    WITHOUT the factor   {w20(fo_r):>4}/{n} ({100*w20(fo_r)//n:>2}%)      "
              f"{_median(fo_r):>6.2f}          {_median(woe):.3f}")
        print(f"    WITH the factor      {w20(fw_r):>4}/{n} ({100*w20(fw_r)//n:>2}%)      "
              f"{_median(fw_r):>6.2f}          {_median(we):.3f}")
        print(f"    moved closer: {imp}/{n} ({100*imp//n}%)   within +/-20%: {d20:+d} ({100*d20/n:+.1f}pp)")

    print(f"\nAIRPORT-FACTOR ISOLATED A/B: {a.csv}")
    _report("ALL held-out", recs)
    for y in sorted({x["y"] for x in recs}):
        _report(f"year {y}", [x for x in recs if x["y"] == y])
    print("\n  ships if within +/-20% is positive on BOTH held-out years and the median does not degrade.")


if __name__ == "__main__":
    main()
