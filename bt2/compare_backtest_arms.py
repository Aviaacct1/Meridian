#!/usr/bin/env python3
"""Avia Solutions - pair two backtest.py arms and say whether the difference is real.

    py -3.12 bt2\\compare_backtest_arms.py control.csv qsifeed.csv [more.csv ...]

Written 11 August 2026 so the connecting back-test is one answer rather than two spreadsheets.
It pairs on (dep, arr, year) and reports ONLY the routes BOTH arms scored, because arms that ran
different route sets are two populations and their headline rates are not a comparison. That is the
same trap the relaxed-sample work of 9 August recorded: 3,697 paired routes said one thing and the
two headline figures said another.

Scoring is the +-20% band on forecast over outturn, the band every published Avia figure uses. It is
NOT symmetric in logs, so it is written once here in ratio form and not restated.

Prints, for each arm: the median ratio, the share within +-20%, and the share within +-50%. Then the
paired movement, and a McNemar test on the routes that changed side, because a net gain of four
routes out of a thousand is noise and should be shown as noise.
"""
import csv
import math
import os
import sys
from collections import defaultdict

BAND_LO, BAND_HI = 0.80, 1.20          # forecast / outturn, the published band


def load(path):
    """{(dep, arr, year): ratio} for every scored route in one arm."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            key = (r.get("dep"), r.get("arr"), str(r.get("year")))
            for col in ("fc_over_p2p", "fc_over_out"):
                v = r.get(col)
                if v not in (None, "", "None"):
                    try:
                        f = float(v)
                    except ValueError:
                        continue
                    if f > 0:
                        out.setdefault(key, {})[col] = f
    return out


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return float("nan")
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def mcnemar(b, c):
    """Two-sided exact-ish p for b gains against c losses. Normal approximation over 25, which is
    where it is accurate enough to decide, and the exact binomial below that."""
    n = b + c
    if n == 0:
        return 1.0
    if n > 25:
        z = (abs(b - c) - 1) / math.sqrt(n)
        return math.erfc(z / math.sqrt(2))
    tot = 2 ** n
    k = min(b, c)
    cum = sum(math.comb(n, i) for i in range(0, k + 1))
    return min(1.0, 2.0 * cum / tot)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    paths = sys.argv[1:]
    arms = []
    for p in paths:
        if not os.path.exists(p):
            print(f"missing: {p}")
            return 2
        arms.append((os.path.basename(p), load(p)))

    for col, label in (("fc_over_p2p", "FORECAST over PURE P2P OUTTURN (the like-for-like demand test)"),
                       ("fc_over_out", "FORECAST over TOTAL OUTTURN (p2p plus all connecting feed)")):
        common = None
        for _, d in arms:
            keys = {k for k, v in d.items() if col in v}
            common = keys if common is None else (common & keys)
        common = common or set()
        print(f"\n=== {label}")
        print(f"    paired on {len(common):,} routes both arms scored")
        if not common:
            print("    nothing in common on this measure")
            continue
        print(f"    {'arm':<34} {'n':>7} {'median':>8} {'+/-20%':>8} {'+/-50%':>8}")
        vals = {}
        for name, d in arms:
            v = [d[k][col] for k in common]
            vals[name] = v
            w20 = sum(1 for x in v if BAND_LO <= x <= BAND_HI) / len(v)
            w50 = sum(1 for x in v if 0.50 <= x <= 1.50) / len(v)
            print(f"    {name:<34} {len(v):>7,} {median(v):>8.3f} {w20:>7.1%} {w50:>7.1%}")

        if len(arms) >= 2:
            (n0, d0), (n1, d1) = arms[0], arms[1]
            gained = lost = 0
            for k in common:
                a_in = BAND_LO <= d0[k][col] <= BAND_HI
                b_in = BAND_LO <= d1[k][col] <= BAND_HI
                gained += (b_in and not a_in)
                lost += (a_in and not b_in)
            p = mcnemar(gained, lost)
            verdict = ("MEASURABLE" if p < 0.05 else
                       "not measurable" if p < 0.20 else "no effect")
            print(f"\n    {n1} against {n0}: +{gained} -{lost}, p={p:.3f}  {verdict}")
            if gained + lost < 30:
                print("    NOTE: fewer than 30 routes changed side. Underpowered either way;")
                print("    a difference this small cannot be told from noise on this sample.")

    print("\nRead the FORECAST over PURE P2P line for the demand test and the TOTAL line for the")
    print("connecting change, since that is the only one the feed can move.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
