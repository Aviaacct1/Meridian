#!/usr/bin/env python3
"""
Avia Solutions - read the back-test through the PRODUCT lens, not the precision lens.
====================================================================================
For a self-serve QSI tool the enemy is not +/-10% precision, it is getting the VIABILITY CALL wrong
and being off by a factor. So this re-scores the existing backtest_results.csv by the bands that
actually matter to an airport taking a number to an airline: is the forecast directionally right and
roughly the right size (defensible, gap explained by marketing/loyalty), or is it a factor out (a
viability-flip risk that loses trust either way)? Nothing re-run - reads the file already on disk.

    py -3.12 product_readout.py                 # reads app/backtest_results.csv
    py -3.12 product_readout.py --forecastable  # only routes whose market pre-existed
"""
import argparse, csv, os
from collections import defaultdict

def pct(n, d): return f"{(100.0*n/d):.0f}%" if d else "  -"

def main():
    ap = argparse.ArgumentParser()
    HERE = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--csv", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--min-out", type=int, default=10000)
    ap.add_argument("--forecastable", action="store_true", help="only routes whose market pre-existed")
    ap.add_argument("--p2p", action="store_true", help="score P2P demand only (ignore the feed) for comparison")
    a = ap.parse_args()
    rows = []
    with open(a.csv, newline="") as fh:
        for d in csv.DictReader(fh):
            try:
                p2p = float(d["p2p_outturn"]); natural = float(d.get("natural") or 0)
                # TOTAL forecast (P2P + connecting feed, capped) vs TOTAL outturn = the product number;
                # fall back to the P2P demand ratio if the total columns aren't present (older CSV)
                fpax = float(d.get("forecast_pax") or 0); tout = float(d.get("outturn_pax") or 0)
                if a.p2p or fpax <= 0 or tout <= 0:
                    fpax = float(d["captured_uncapped"]); tout = p2p
            except Exception:
                continue
            if fpax <= 0 or tout < a.min_out:
                continue
            if a.forecastable and natural < p2p:
                continue
            rows.append(dict(r=fpax/tout, region=(d.get("region") or "?").strip(),
                             typ=(d.get("type") or "?").strip()))
    if not rows:
        print("no rows"); return

    # directional bands on the demand estimate vs outturn
    def bands(rs):
        n = len(rs)
        b = dict(
            tight=sum(1 for x in rs if 0.85 <= x["r"] <= 1.18),      # ~+/-15%, "on the money"
            usable=sum(1 for x in rs if 0.67 <= x["r"] <= 1.5),       # within a factor of 1.5 - defensible
            rough=sum(1 for x in rs if 0.5 <= x["r"] <= 2.0),         # within a factor of 2 - directionally right
            badlow=sum(1 for x in rs if x["r"] < 0.5),                # >2x UNDER - would wrongly rule a route out
            badhigh=sum(1 for x in rs if x["r"] > 2.0),               # >2x OVER  - would over-promise, burns airline
        )
        return n, b
    n, b = bands(rows)
    print(f"{n} routes {'(forecastable only)' if a.forecastable else '(all material)'} - demand estimate vs outturn\n")
    print("THE PRODUCT SCORECARD (what actually matters for a self-serve QSI number):")
    print(f"  on the money   (within ~15%)     {pct(b['tight'],n):>5}   {b['tight']}/{n}")
    print(f"  defensible     (within 1.5x)     {pct(b['usable'],n):>5}   {b['usable']}/{n}")
    print(f"  directional    (within 2x)       {pct(b['rough'],n):>5}   {b['rough']}/{n}")
    print(f"  too LOW  (>2x under, rules a good route out)   {pct(b['badlow'],n):>5}   {b['badlow']}/{n}")
    print(f"  too HIGH (>2x over, over-promises to airline)  {pct(b['badhigh'],n):>5}   {b['badhigh']}/{n}")
    print("  (too-LOW is mostly thin-GDS coverage, fixable by the country layer; the >2x-over rate is")
    print("   the one that loses airline trust - watch it stays small.)")

    for label, keyfn in [("REGION", lambda x: x["region"]), ("CARRIER TYPE", lambda x: x["typ"])]:
        g = defaultdict(list)
        for x in rows: g[keyfn(x)].append(x)
        print(f"\n  by {label}:  {'':10} {'n':>4} {'within1.5x':>10} {'within2x':>9} {'>2x over':>9}")
        for k in sorted(g, key=lambda z: -len(g[z])):
            nn, bb = bands(g[k])
            if nn >= 8:
                print(f"  {'':13} {k:10} {nn:>4} {pct(bb['usable'],nn):>10} {pct(bb['rough'],nn):>9} {pct(bb['badhigh'],nn):>9}")

if __name__ == "__main__":
    main()
