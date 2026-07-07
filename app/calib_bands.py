#!/usr/bin/env python3
r"""
Avia Solutions - confidence-band calibration.
==================================================================================================
The forecast card shows a "likely range" around the central estimate. This sets that range from the
ACTUAL spread of forecast-vs-outturn in the back-test, so the band is the middle two-in-three of what
really happened, not an estimate.

For a forecast F, the outturn is F / (forecast/actual ratio). So the band multipliers on F are the
inverse percentiles of that ratio: low = 1 / p83, high = 1 / p17 (the central 66%). Forecastable routes
use fc/p2p (the P2P demand test); induced-floored LCC/ULCC routes use fc/out (carried vs onboard, the
capacity-anchored test).

    py -3.12 calib_bands.py E:\Avia\QSI\backtests\bt_6yr_induced.csv

Paste the two "band multipliers" lines back; they go into cortex_app calibrated_forecast.
No store access; reads the CSV only.
"""
import argparse, csv


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    i = min(len(xs) - 1, max(0, int(round(p / 100.0 * (len(xs) - 1)))))
    return xs[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    a = ap.parse_args()
    rows = []
    with open(a.csv, newline="") as fh:
        for r in csv.DictReader(fh):
            r["_nat"] = _f(r.get("natural")); r["_p2p"] = _f(r.get("p2p_outturn"))
            r["_out"] = _f(r.get("outturn_pax")); r["_fp2p"] = _f(r.get("fc_over_p2p"))
            r["_fout"] = _f(r.get("fc_over_out"))
            r["_ind"] = str(r.get("induced")).strip().lower() == "true"
            rows.append(r)

    # forecastable = measured market >= what the route carried; test on fc/p2p
    fore = [r["_fp2p"] for r in rows if r["_nat"] is not None and r["_p2p"] and r["_p2p"] >= a.min_outturn
            and r["_nat"] >= r["_p2p"] and r["_fp2p"] and r["_fp2p"] > 0]
    # induced-floored LCC/ULCC = fc/out (carried vs onboard, the capacity-anchored test)
    ind = [r["_fout"] for r in rows if r["_ind"] and r["_fout"] and r["_fout"] > 0
           and (r["_out"] or 0) >= a.min_outturn]

    print(f"\nCONFIDENCE-BAND CALIBRATION: {a.csv}")
    for name, key, xs in [("FORECASTABLE", "forecastable", fore), ("INDUCED-FLOOR", "induced", ind)]:
        if not xs:
            print(f"  {name}: no rows"); continue
        p17, p50, p83 = _pct(xs, 17), _pct(xs, 50), _pct(xs, 83)
        lo = 1.0 / p83 if p83 else 0.0
        hi = 1.0 / p17 if p17 else 0.0
        print(f"  {name}: n={len(xs)}  forecast/actual ratio  p17 {p17:.2f} / median {p50:.2f} / p83 {p83:.2f}")
        print(f"    -> band multipliers on the forecast ({key}): low {lo:.2f}, high {hi:.2f}   (middle 2 in 3)")


if __name__ == "__main__":
    main()
