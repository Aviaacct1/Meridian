#!/usr/bin/env python3
"""
Avia Cortex - airport capture-factor extractor (the morning-after tool for the overnight back-test).
====================================================================================================
From the back-test residuals, per ORIGIN airport, how far the model's captured point-to-point sits
from the actual P2P outturn:

    factor = median( p2p_outturn / captured )   per origin airport

  factor > 1  ->  the model UNDER-captures that airport (needs an uplift; the SJC pattern - a genuine
                  secondary whose own catchment the size-pull hands to the big hub).
  factor < 1  ->  the model OVER-captures it.

Trust-gated, same discipline as the coverage and stimulation tables: an airport earns a PUBLISHED
factor only with enough launched routes AND a factor that holds across the early and late halves of
the period (so it's structural signal, not a couple of noisy routes). This is the back-test feed for
airport_capture.py, complementing the survey-measured entries like SJC.

    py -3.12 airport_fit.py                              # reads app/backtest_results.csv
    py -3.12 airport_fit.py --csv backtest_global.csv --min-n 4
"""
import argparse, csv, os, statistics as st
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    HERE = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--csv", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--min-n", type=int, default=4, help="launched routes an airport needs to PUBLISH")
    ap.add_argument("--tol", type=float, default=0.30, help="max early-vs-late gap to call a factor stable")
    ap.add_argument("--out", default=os.path.join(HERE, "airport_capture_factors.csv"))
    a = ap.parse_args()

    rows = []
    with open(a.csv, newline="") as fh:
        for d in csv.DictReader(fh):
            try:
                cap = float(d["captured_uncapped"]); p2p = float(d["p2p_outturn"]); yr = int(float(d["year"]))
            except Exception:
                continue
            if cap <= 0 or p2p <= 0:
                continue
            r = p2p / cap
            if r < 0.05 or r > 20:
                continue
            rows.append(dict(dep=d["dep"], country=d.get("dep_country", ""), yr=yr, r=r))
    if not rows:
        print("no usable rows"); return

    yrs = sorted(set(x["yr"] for x in rows)); mid = yrs[len(yrs) // 2] if yrs else 0
    g = defaultdict(list); early = defaultdict(list); late = defaultdict(list); ctry = {}
    for x in rows:
        g[x["dep"]].append(x["r"]); ctry[x["dep"]] = x["country"]
        (early if x["yr"] < mid else late)[x["dep"]].append(x["r"])

    out = []
    for dep in sorted(g, key=lambda z: -len(g[z])):
        v = g[dep]; n = len(v); m = st.median(v)
        e, l = early.get(dep, []), late.get(dep, [])
        stable = None
        if len(e) >= 2 and len(l) >= 2:
            me, ml = st.median(e), st.median(l)
            stable = (abs(me - ml) / ((me + ml) / 2.0) <= a.tol) if (me + ml) > 0 else None
        published = (n >= a.min_n) and (stable is True)
        out.append(dict(airport=dep, country=ctry.get(dep, ""), n=n, factor=round(m, 3),
                        stable=("" if stable is None else stable), published=published))

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["airport", "country", "n", "factor", "stable", "published"])
        w.writeheader(); w.writerows(out)

    pub = [o for o in out if o["published"]]
    print(f"{len(rows)} routes, {len(g)} origin airports; {len(pub)} PUBLISHED (n>={a.min_n} & stable)\n")
    print("UNDER-CAPTURED, factor > 1.3 (the SJC pattern - model too low, candidates for an uplift):")
    for o in sorted([o for o in pub if o["factor"] > 1.3], key=lambda z: -z["factor"])[:30]:
        print(f"  {o['airport']:4} ({o['country']:2})  x{o['factor']:<5}  n={o['n']}")
    print("\nOVER-CAPTURED, factor < 0.7 (model too high):")
    for o in sorted([o for o in pub if o["factor"] < 0.7], key=lambda z: z["factor"])[:15]:
        print(f"  {o['airport']:4} ({o['country']:2})  x{o['factor']:<5}  n={o['n']}")
    print(f"\nwrote {a.out}  (review, then promote the confident ones into airport_capture.py)")


if __name__ == "__main__":
    main()
