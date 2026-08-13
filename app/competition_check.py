#!/usr/bin/env python3
r"""
Avia Solutions - the competition bucket as it stands today.
===========================================================
JOB 3, THE MEASUREMENT BEFORE THE CHANGE. direct_competition.py classifies every
connecting market by whether a nonstop already exists, and cortex_app puts the result in
the payload. But the classification happens AFTER capture: feed_side and behind_feed
compute cap x conn_coeff, where conn_coeff varies by alliance and knows nothing about
competition. So the two buckets today are one rate sorted into two piles, not two rates.

The 2025 analyst used two rates going in. From slide 32 of China Airlines TPE-SJC
Forecast 17Sep25.pptx, recorded at ANALYST-SEGMENTS-BY-COMPETITION on 14 August:

    beyond Taipei      0.0% on the competed half, 1.5% on the uncompeted
    behind San Jose    0.2% on the competed half, 4.7% on the uncompeted

This prints ours beside his so the size and the DIRECTION of the difference are known
before anything is changed. Two things to read off it:

  1. How close our two bucket rates are to each other. If they are near-identical, that
     is the single-rate engine showing through and it is the thing Job 3 fixes.
  2. What SHARE of our connecting forecast comes from markets that already have a
     nonstop. If that share is large and the analyst captures nothing there, we and he
     are forecasting different traffic and the 19% gap has a named mechanism rather
     than a candidate.

Nothing here changes a forecast.

Usage (workstation):
    py -3.12 competition_check.py --origin SJC --dest TPE --airline CI --aircraft A359 --freq 4
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# The analyst's rates, for the SJC-TPE case only. Read from slide 32 of the September 2025
# deck; they are HIS assumptions on HIS market definitions and are printed for comparison,
# never used in a calculation.
ANALYST = {("SJC", "TPE"): {"beyond": (0.000, 0.015), "behind": (0.002, 0.047)}}


def _pct(v):
    return "-" if v is None else f"{v * 100:.2f}%"


def main():
    ap = argparse.ArgumentParser(description="Print the competition bucket for one case.")
    ap.add_argument("--origin", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--airline", default=None)
    ap.add_argument("--carrier-type", default="FSC")
    ap.add_argument("--aircraft", default="A21X")
    ap.add_argument("--freq", type=float, default=7)
    ap.add_argument("--seats", type=float, default=None)
    ap.add_argument("--forecast-year", type=int, default=None)
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    kw = dict(origin=args.origin, dest=args.dest, airline=args.airline,
              carrier_type=args.carrier_type, aircraft=args.aircraft, freq=args.freq,
              with_econ=True)
    if args.seats:
        kw["seats"] = args.seats
    if args.forecast_year:
        kw["forecast_year"] = args.forecast_year

    import cortex_app as CA
    fc = CA.calibrated_forecast(**kw)
    cs = fc.get("competition_split")
    if not cs:
        print("No competition_split in the payload. The engine returned no feed detail, "
              "which happens when the carrier is point to point or the feed is switched off.")
        return 2

    ref = ANALYST.get((args.origin.upper(), args.dest.upper()))
    print(f"{args.origin}-{args.dest}  {args.airline or 'no airline'}  week {cs.get('week')}\n")

    for side in ("beyond", "behind"):
        blk = cs.get(side) or {}
        tot = blk.get("totals") or {}
        d, n = tot.get("direct") or {}, tot.get("no_direct") or {}
        print(f"  {side.upper()}  ({blk.get('test', 'test not stated')})")
        print(f"    {'bucket':<22} {'markets':>8} {'base':>14} {'forecast':>12} {'capture':>9}")
        for label, blk2 in (("with direct competition", d), ("no direct competition", n)):
            print(f"    {label:<22} {blk2.get('markets', 0):>8,} {blk2.get('base', 0):>14,} "
                  f"{blk2.get('forecast', 0):>12,} {_pct(blk2.get('capture')):>9}")
        f_d, f_n = float(d.get("forecast") or 0), float(n.get("forecast") or 0)
        if f_d + f_n:
            print(f"    share of this side's forecast coming from COMPETED markets: "
                  f"{f_d / (f_d + f_n):.1%}")
        c_d, c_n = d.get("capture"), n.get("capture")
        if c_d and c_n:
            print(f"    uncompeted rate against competed rate: {c_n / c_d:.2f}x "
                  f"(one blended rate would give circa 1.0)")
        if ref:
            a_d, a_n = ref[side]
            print(f"    2025 analyst on this side: {_pct(a_d)} competed, {_pct(a_n)} uncompeted, "
                  f"{a_n / a_d if a_d else float('inf'):.1f}x apart")
        print()

    if args.top:
        for side in ("beyond", "behind"):
            rows = ((cs.get(side) or {}).get("rows") or [])[:args.top]
            if not rows:
                continue
            print(f"  {side.upper()}, {len(rows)} largest markets by forecast:")
            for r in rows:
                print(f"    {r['code']:<5} {'COMPETED' if r['direct_competition'] else 'open':<9} "
                      f"base {r['base']:>10,}  forecast {r['forecast']:>9,}  "
                      f"capture {_pct(r.get('share'))}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
