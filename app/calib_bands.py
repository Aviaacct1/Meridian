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
from collections import defaultdict


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
            r["_hub"] = str(r.get("hub_dest")).strip().lower() == "true"
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

    # --- CONDITIONAL bands: is the band tighter for bigger/denser markets? If so, a market-size-aware
    #     band gives the routes airports actually pitch a much tighter number than the population average.
    fr = [r for r in rows if r["_nat"] is not None and r["_p2p"] and r["_p2p"] >= a.min_outturn
          and r["_nat"] >= r["_p2p"] and r["_fp2p"] and r["_fp2p"] > 0]
    EDGES, LBL = [15000, 50000, 150000], ["<15k", "15-50k", "50-150k", ">150k"]

    def _bkt(v):
        for i, e in enumerate(EDGES):
            if v < e:
                return LBL[i]
        return LBL[-1]

    def _seg(title, groups):
        print(f"\n  {title}")
        for gk, xs in groups:
            if len(xs) < 15:
                continue
            p17, p50, p83 = _pct(xs, 17), _pct(xs, 50), _pct(xs, 83)
            w20 = sum(1 for x in xs if 0.8 <= x <= 1.2)
            w40 = sum(1 for x in xs if 0.6 <= x <= 1.4)
            print(f"    {gk:9} n={len(xs):<4} p17/med/p83 {p17:.2f}/{p50:.2f}/{p83:.2f}  "
                  f"band {1/p83 if p83 else 0:.2f}-{1/p17 if p17 else 0:.2f}  "
                  f"+/-20% {100*w20//len(xs):>3}%  +/-40% {100*w40//len(xs):>3}%")

    bym = defaultdict(list)
    for r in fr:
        bym[_bkt(r["_nat"])].append(r["_fp2p"])
    _seg("BAND BY MARKET SIZE (forecastable) - the conditional-band test:",
         [(k, bym.get(k, [])) for k in LBL])
    byh = defaultdict(list)
    for r in fr:
        byh["hub" if r["_hub"] else "non-hub"].append(r["_fp2p"])
    _seg("BAND BY HUB (forecastable):", [(k, byh.get(k, [])) for k in ("hub", "non-hub")])

    # --- what drives the WIDE high side? profile the over-forecast tail (fc/p2p > 1.8). Hypothesis:
    #     connecting-heavy markets (big natural O&D, small P2P) over-forecast P2P, so their natural/p2p
    #     ratio runs high. If so, discount the P2P capture where the market is connecting-heavy = tightens
    #     the band AND improves accuracy, rather than just widening the interval.
    tail = [r for r in fr if r["_fp2p"] > 1.8]
    if tail:
        def _ratio(rs):
            v = [r["_nat"] / r["_p2p"] for r in rs if r["_p2p"]]
            return _pct(v, 50) if v else 0.0
        print(f"\n  OVER-FORECAST TAIL (fc/p2p > 1.8): n={len(tail)} of {len(fr)} ({100*len(tail)//len(fr)}%)")
        print(f"    natural / P2P-outturn ratio (high = connecting-heavy market):")
        print(f"      tail median {_ratio(tail):.1f}   vs all-forecastable {_ratio(fr):.1f}")
        tt = defaultdict(int)
        for r in tail:
            tt[r.get("type") or "?"] += 1
        print("    tail by type: " + ", ".join(f"{k} {v}" for k, v in sorted(tt.items(), key=lambda x: -x[1])))
        print(f"    tail hub share: {100*sum(1 for r in tail if r['_hub'])//len(tail)}%  "
              f"(all-forecastable {100*sum(1 for r in fr if r['_hub'])//len(fr)}%)")

    # --- if the connecting-heaviness diagnostic is present (--nonstop-share run), test it directly:
    #     do LOW nonstop-share (connecting-heavy) markets carry the over-read and the wide band?
    fps = [r for r in fr if _f(r.get("p2p_share")) is not None]
    if fps:
        def _psb(v):
            return "<20%" if v < 0.2 else "20-50%" if v < 0.5 else "50-80%" if v < 0.8 else ">=80%"
        byp = defaultdict(list)
        for r in fps:
            byp[_psb(_f(r.get("p2p_share")))].append(r["_fp2p"])
        _seg("BAND BY NONSTOP-SHARE (forecastable) - the connecting-heavy test "
             "(low share should over-read + widen):", [(k, byp.get(k, []))
             for k in ("<20%", "20-50%", "50-80%", ">=80%")])


if __name__ == "__main__":
    main()
