#!/usr/bin/env python3
r"""
Avia Solutions - single-airport bias diagnostic (is a per-airport catchment correction legitimate?).
==================================================================================================
A secondary airport (SJC under SFO) can be systematically UNDER-forecast because the catchment model sends too
much of its metro to the primary. This checks, for ONE airport, whether that bias is CONSISTENT across years
(so a correction generalises) or just small-sample noise (so it's the overfit airport-factor that failed T7).

    fc/out median on FIT years (2016-2018)  ->  the centring factor f = 1/median
    apply f to the HELD-OUT years           ->  does the median centre on 1.0 and does +/-20% rise?

If the held-out median centres and +/-20% improves, the bias is real and a catchment/capture correction is
justified (structural: lift the airport's catchment share to the observed Sabre split). If held-out doesn't
follow the fit correction, it's noise - leave it.

    py -3.12 analyze_airport.py bt_v2_6yr.csv --airport SJC --fit-years 2016,2017,2018

Reads the CSV only. Grades on fc/out (total onboard), the same basis as the track-record page.
"""
import argparse, csv


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
    ap.add_argument("--airport", required=True)
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--forecastable-only", action="store_true", help="exclude new-market (induced) routes")
    a = ap.parse_args()
    A = a.airport.strip().upper()
    fit_years = set(a.fit_years.split(","))
    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        if A not in ((r.get("dep") or "").upper(), (r.get("arr") or "").upper()):
            continue
        out = _f(r.get("outturn_pax")); fc = _f(r.get("forecast_pax")); fo = _f(r.get("fc_over_out"))
        nat = _f(r.get("natural")); p2p = _f(r.get("p2p_outturn"))
        if fo is None and out and fc:
            fo = fc / out
        if out is None or out < a.min_outturn or fo is None or fo <= 0:
            continue
        if a.forecastable_only and (nat is None or p2p is None or nat < p2p):
            continue
        rows.append({"year": str(r.get("year")), "fo": fo,
                     "route": f"{r.get('dep')}-{r.get('arr')}"})
    if not rows:
        print(f"No graded routes touching {A}."); return

    fit = [r for r in rows if r["year"] in fit_years]
    held = [r for r in rows if r["year"] not in fit_years]
    print(f"\n{A} bias diagnostic ({a.csv}): {len(rows)} routes touching {A}")
    print(f"  ALL:  n={len(rows):>3}  median fc/out {_median([r['fo'] for r in rows]):.2f}  +/-20% {100*_w20([r['fo'] for r in rows])//len(rows)}%")
    if fit:
        fm = _median([r["fo"] for r in fit])
        print(f"  FIT {sorted(fit_years)}:  n={len(fit):>3}  median {fm:.2f}  +/-20% {100*_w20([r['fo'] for r in fit])//len(fit)}%")
    for y in sorted({r["year"] for r in held}):
        hy = [r["fo"] for r in held if r["year"] == y]
        print(f"  held {y}:  n={len(hy):>3}  median {_median(hy):.2f}  +/-20% {100*_w20(hy)//len(hy) if hy else 0}%")

    if len(fit) < 4:
        print("\n  too few fit-year routes to fit a correction reliably."); return
    fm = _median([r["fo"] for r in fit])
    f = (1.0 / fm) if fm > 0 else 1.0
    print(f"\n  CENTRING FACTOR from fit years: {f:.2f}x  (fit median {fm:.2f} -> 1.00)")
    if held:
        ho = [r["fo"] for r in held]
        hc = [r["fo"] * f for r in held]
        print(f"  applied to held-out (n={len(ho)}): median {_median(ho):.2f} -> {_median(hc):.2f}   "
              f"+/-20% {100*_w20(ho)//len(ho)}% -> {100*_w20(hc)//len(hc)}%")
        print("\n  Verdict: if the held-out median centres near 1.0 AND +/-20% rises, the under-forecast is a REAL,")
        print("  consistent bias -> a catchment/capture correction for this airport is justified (calibrate its")
        print("  share to the observed Sabre split). If held-out doesn't follow, it's noise - leave it (that's the")
        print("  overfit that failed the blanket airport factor).")


if __name__ == "__main__":
    main()
