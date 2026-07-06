#!/usr/bin/env python3
"""
Avia Cortex - MCT back-test comparison. Reads two backtest.py output CSVs, the current model and the
MCT-banked model, and judges which FITS outturn better. The trick: banking only scales the feed down,
so its median forecast/outturn ratio drops; comparing raw ratios would be unfair. So each model is
re-centred to a median ratio of 1.0 (simulating re-calibrating the level to hit outturn on average),
and only the DISPERSION is compared, the real question of whether schedule timing explains variance.
Lower dispersion (med|ln ratio|, more routes within +/-20%) = the better model.

    py -3.12 backtest.py --feed-fix --routes-file pinned_global.json --out bt_base.csv
    py -3.12 backtest.py --feed-fix --mct-banking --routes-file pinned_global.json --out bt_mct.csv
    py -3.12 compare_mct.py bt_base.csv bt_mct.csv
"""
import sys
import csv
import math


def load(path):
    d = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                ratio = float(r["fc_over_out"])
            except (ValueError, KeyError):
                continue
            if ratio <= 0:
                continue
            out = float(r.get("outturn_pax") or 0)
            feed = float(r.get("feed_beyond") or 0) + float(r.get("feed_behind") or 0)
            d[r["route"]] = {"ratio": ratio, "out": out, "feed": feed,
                             "hub": str(r.get("hub_dest", "")).strip().lower() in ("true", "1")}
    return d


def med(xs):
    xs = sorted(xs); n = len(xs)
    return 0.0 if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def stats(ratios):
    m = med(ratios) or 1.0
    rec = [x / m for x in ratios]                       # re-centre to median 1.0
    logs = [abs(math.log(x)) for x in rec if x > 0]
    n = len(rec) or 1
    w20 = 100.0 * sum(1 for x in rec if abs(x - 1) <= 0.20) / n
    w30 = 100.0 * sum(1 for x in rec if abs(x - 1) <= 0.30) / n
    return {"n": len(ratios), "median": m, "medlog": med(logs), "w20": w20, "w30": w30}


def report(name, base, banked, subset):
    keys = [k for k, v in base.items() if k in banked and subset(v)]
    if not keys:
        print(f"\n{name}: no matched routes")
        return
    db = stats([base[k]["ratio"] for k in keys])
    dm = stats([banked[k]["ratio"] for k in keys])
    print(f"\n{name}  (n={db['n']})")
    print(f"  {'':9}{'median':>9}{'med|ln|':>9}{'within20':>10}{'within30':>10}")
    print(f"  {'baseline':9}{db['median']:>9.2f}{db['medlog']:>9.3f}{db['w20']:>9.0f}%{db['w30']:>9.0f}%")
    print(f"  {'banked':9}{dm['median']:>9.2f}{dm['medlog']:>9.3f}{dm['w20']:>9.0f}%{dm['w30']:>9.0f}%")
    better = "banked" if dm["medlog"] < db["medlog"] else "baseline"
    delta = (db["medlog"] - dm["medlog"])
    print(f"  -> tighter fit after re-centring: {better}  (med|ln| {'improves' if delta > 0 else 'worsens'} by {abs(delta):.3f})")


def main():
    if len(sys.argv) < 3:
        print("usage: py -3.12 compare_mct.py <baseline.csv> <banked.csv>")
        return
    base, banked = load(sys.argv[1]), load(sys.argv[2])
    print(f"matched routes: {len(set(base) & set(banked))}")
    report("ALL routes", base, banked, lambda v: True)
    report("HUB routes (feed-heavy destinations)", base, banked, lambda v: v["hub"])
    report("routes with material feed (>10% of outturn)", base, banked,
           lambda v: v["out"] > 0 and v["feed"] / v["out"] > 0.10)
    print("\nRead-out: banking helps only if it tightens the fit (lower med|ln|, higher within-20%),"
          " especially on the hub / feed-heavy rows where the feed actually matters. If it doesn't,"
          " keep the current model or tune the window / weighting in mct_bank.py.")


if __name__ == "__main__":
    main()
