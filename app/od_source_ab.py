#!/usr/bin/env python3
r"""
Avia Solutions - the DOT switch, A against B on one route.
=========================================================
Runs the SAME case twice through calibrated_forecast, once with AVIA_OD_SOURCE=sabre
and once with the mode under test, and puts the two side by side leg by leg. Nothing
else changes between the runs, so every difference is the source and only the source.

WHAT TO EXPECT AND THEREFORE WHAT WOULD BE WRONG. dot_ratio_check measured DB1B at
circa 1.09x Sabre on US domestic connecting markets, flat across every nonstop-share
cut, so a US domestic route should move its feed legs by roughly that and its point to
point leg by circa 0.96x to 0.99x. A route with no all-US market on any leg must not
move AT ALL: SJC-TPE is the worked example, since route_feed measures the behind leg
from each feeder to the route DESTINATION, which is Taipei. A nil result there is a
PASS, not a failed run.

Reads the od_source block from each payload, so the run states which source answered
each leg rather than being assumed to have used the one that was asked for.

Usage (workstation):
    py -3.12 od_source_ab.py --origin SJC --dest BOS --airline B6 --aircraft A21N --freq 7
    py -3.12 od_source_ab.py --origin TPA --dest AUS --airline WN --aircraft B738 --freq 14
    py -3.12 od_source_ab.py --origin SJC --dest TPE --airline CI --aircraft A359 --freq 4
        (the control: no all-US leg, so every figure must be identical)
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

LEGS = [("Point to point carried", ("demand", "p2p_carried")),
        ("Connecting carried", ("demand", "connecting_carried")),
        ("Feed beyond", ("demand", "feed_beyond")),
        ("Feed behind", ("demand", "feed_behind")),
        ("Feed total", ("demand", "feed_total")),
        ("Total carried each way", ("demand", "total")),
        ("Natural market", ("demand", "natural")),
        ("Captured", ("demand", "captured"))]


def _g(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or cur.get(k) is None:
            return None
        cur = cur[k]
    return cur


def _run(mode, kw):
    """One forecast at one setting. The mode is set before the import-time cache is used."""
    if mode:
        os.environ["AVIA_OD_SOURCE"] = mode
    else:
        os.environ.pop("AVIA_OD_SOURCE", None)
    import od_source as OS
    OS._YEAR_OK.clear()
    import cortex_app as CA
    return CA.calibrated_forecast(**kw)


def main():
    ap = argparse.ArgumentParser(description="Run one case with the DOT switch off and on.")
    ap.add_argument("--origin", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--airline", default=None)
    ap.add_argument("--carrier-type", default="FSC")
    ap.add_argument("--aircraft", default="A21X")
    ap.add_argument("--freq", type=float, default=7)
    ap.add_argument("--seats", type=float, default=None)
    ap.add_argument("--plan-lf", type=float, default=0.875)
    ap.add_argument("--forecast-year", type=int, default=None)
    ap.add_argument("--mode", default="auto", choices=("auto", "dot"),
                    help="the setting under test; the control is always sabre")
    args = ap.parse_args()

    kw = dict(origin=args.origin, dest=args.dest, airline=args.airline,
              carrier_type=args.carrier_type, aircraft=args.aircraft, freq=args.freq,
              plan_lf=args.plan_lf, with_econ=True)
    if args.seats:
        kw["seats"] = args.seats
    if args.forecast_year:
        kw["forecast_year"] = args.forecast_year

    print(f"{args.origin}-{args.dest}  {args.airline or 'no airline'}  {args.aircraft}  "
          f"{args.freq:g} weekly\n")
    base = _run(None, kw)          # control: the shipped default
    test = _run(args.mode, kw)     # the setting under test

    for label, key in ("point to point", "point_to_point"), ("beyond", "beyond"), ("behind", "behind"):
        b = _g(base, ("od_source", key)) or "not reported"
        t = _g(test, ("od_source", key)) or "not reported"
        print(f"  source, {label:<15} sabre: {b}\n  {'':<24}{args.mode}: {t}")
    for side in ("beyond", "behind"):
        share = _g(test, ("od_source", f"{side}_dot_share"))
        if share is not None:
            print(f"  DOT share of the {side} market under {args.mode}: {share:.1%}")

    print(f"\n  {'leg':<26} {'sabre':>14} {args.mode:>14} {'change':>10}")
    moved = 0
    for label, path in LEGS:
        b, t = _g(base, path), _g(test, path)
        if b is None and t is None:
            continue
        b, t = float(b or 0), float(t or 0)
        pct = (100.0 * (t - b) / b) if b else None
        moved += 1 if (pct is not None and abs(pct) >= 0.05) else 0
        shown = "same" if pct is None or abs(pct) < 0.05 else f"{pct:+.2f}%"
        print(f"  {label:<26} {b:>14,.0f} {t:>14,.0f} {shown:>10}")

    print(f"\n  {moved} of {len(LEGS)} figures moved.")
    if not moved:
        print("  Nothing moved. Either the route has no all-US market on any leg, which is the "
              "expected\n  result for an international route, or the switch did not reach the "
              "engine. The source\n  lines above say which.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
