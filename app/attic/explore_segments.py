#!/usr/bin/env python3
"""
Avia Solutions - segmentation explorer / goal-seek for the back-test.
====================================================================
John's process with the held-out discipline built in. For a chosen grouping it centres each
cell on the FIT launch years and measures whether that lifts +/-20% on the GRADE launch years -
the years the correction never saw. --sweep runs EVERY grouping and ranks them by held-out
accuracy: the inverse question, "what grouping would we need, and how close to 80% does it get
on unseen routes, and is the required per-cell correction coherent enough to become a model".

Why held-out and not in-sample: any target is trivially reachable in-sample by segmenting finely
enough (one route per cell = 100% in-sample, 0% out-of-sample). The held-out number is the real
ceiling a grouping delivers; the fit-vs-held-out gap is the overfit tell.

No engine re-run: fc/p2p already carries the forecast, so a per-cell correction k just rescales
the ratio (fc/p2p -> k*fc/p2p). Isolated-A/B: recover the counterfactual, apply, re-score.

Usage:
  py -3.12 explore_segments.py bt_na_precovid.csv --dim haul --fit 2016,2017 --grade 2018
  py -3.12 explore_segments.py bt_na_precovid.csv --sweep --fit 2016,2017 --grade 2018
Guards: --min-cell (min FIT routes to trust a cell's correction) and --cap (cap the correction).
"""
import argparse, csv, statistics as st
from collections import defaultdict


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(path):
    """Forecastable rows only (pre-existing market >= what the route carried), fc/p2p present."""
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        fc = _f(r.get("fc_over_p2p"))
        p2p = _f(r.get("p2p_outturn"))
        nat = _f(r.get("natural"))
        yr = _f(r.get("year"))
        if fc is None or p2p is None or yr is None or fc <= 0:
            continue
        if nat is None or nat < p2p:
            continue
        r["_fc"] = fc
        r["_yr"] = int(yr)
        r["_gcd"] = _f(r.get("gcd_km")) or 0
        r["_p2p"] = p2p
        rows.append(r)
    return rows


def haul_bin(r):
    g = r["_gcd"]
    return "<800km" if g < 800 else "800-2500" if g < 2500 else "2500-6000" if g < 6000 else ">6000km"


def mkt_bin(r):
    p = r["_p2p"]
    return "<15k" if p < 15000 else "15-50k" if p < 50000 else "50-150k" if p < 150000 else ">150k"


DIMS = {
    "haul": haul_bin,
    "type": lambda r: r.get("type", "?"),
    "market": mkt_bin,
    "hub": lambda r: "hub" if str(r.get("hub_dest")).lower() in ("true", "1") else "non-hub",
    "region": lambda r: r.get("region", "?"),
    "dep_country": lambda r: r.get("dep_country", "?"),
    "carrier": lambda r: r.get("carrier", "?"),
    "haul_type": lambda r: f'{haul_bin(r)} | {r.get("type","?")}',
    "haul_market": lambda r: f'{haul_bin(r)} | {mkt_bin(r)}',
    "haul_hub": lambda r: f'{haul_bin(r)} | {"hub" if str(r.get("hub_dest")).lower() in ("true","1") else "non-hub"}',
    "type_market": lambda r: f'{r.get("type","?")} | {mkt_bin(r)}',
    "haul_type_market": lambda r: f'{haul_bin(r)} | {r.get("type","?")} | {mkt_bin(r)}',
}


def med(xs):
    return st.median(xs) if xs else 0.0


def w20(xs):
    return sum(1 for x in xs if 0.8 <= x <= 1.2)


def cell_corrections(fit, seg, min_cell, cap):
    fby = defaultdict(list)
    for r in fit:
        fby[seg(r)].append(r["_fc"])
    cells = {}
    for c, xs in fby.items():
        m = med(xs)
        k = 1.0
        if len(xs) >= min_cell and m > 0:
            k = max(1.0 / cap, min(cap, 1.0 / m))
        cells[c] = (k, len(xs), m)
    return cells


def score(fit, grade, seg, min_cell, cap):
    """Return (grade_base, grade_corr, grade_n, fit_base, fit_corr, fit_n, cells)."""
    cells = cell_corrections(fit, seg, min_cell, cap)
    gb = w20([r["_fc"] for r in grade])
    gc = w20([cells.get(seg(r), (1.0, 0, 0))[0] * r["_fc"] for r in grade])
    fb = w20([r["_fc"] for r in fit])
    fc = w20([cells.get(seg(r), (1.0, 0, 0))[0] * r["_fc"] for r in fit])
    return gb, gc, len(grade), fb, fc, len(fit), cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--dim", default="haul", choices=sorted(DIMS))
    ap.add_argument("--sweep", action="store_true", help="run every grouping and rank by held-out accuracy")
    ap.add_argument("--fit", default="2016,2017", help="FIT launch years (comma list)")
    ap.add_argument("--grade", default="2018", help="held-out GRADE launch years (comma list)")
    ap.add_argument("--min-cell", type=int, default=8, help="min FIT routes in a cell to trust its correction")
    ap.add_argument("--cap", type=float, default=2.5, help="cap the per-cell correction (thin-cell guard)")
    a = ap.parse_args()

    fit_y = {int(y) for y in a.fit.split(",")}
    grade_y = {int(y) for y in a.grade.split(",")}
    rows = load(a.csv)
    fit = [r for r in rows if r["_yr"] in fit_y]
    grade = [r for r in rows if r["_yr"] in grade_y]
    print(f"loaded {len(rows)} forecastable rows | FIT {sorted(fit_y)} n={len(fit)} | "
          f"GRADE {sorted(grade_y)} n={len(grade)}")
    if not fit or not grade:
        print("NOT ENOUGH DATA in the fit or grade years - widen --fit/--grade or use a fuller backtest.")
        return

    if a.sweep:
        print(f"\n  GOAL-SEEK sweep: every grouping, ranked by held-out +/-20%. min-cell={a.min_cell} cap={a.cap}")
        print(f"  {'grouping':18} {'cells':>5} {'grdBase':>8} {'grdCorr':>8} {'held-out':>9} {'in-samp':>8}")
        res = []
        for name, seg in DIMS.items():
            gb, gc, gn, fb, fc, fn, cells = score(fit, grade, seg, a.min_cell, a.cap)
            res.append((name, len(cells), gb, gc, gn, fb, fc, fn))
        for name, nc, gb, gc, gn, fb, fc, fn in sorted(res, key=lambda t: -(t[3] - t[2])):
            ho = (gc - gb) / gn * 100 if gn else 0
            ins = (fc - fb) / fn * 100 if fn else 0
            print(f"  {name:18} {nc:>5} {gb:>4}/{gn:<3} {gc:>4}/{gn:<3} {ho:>+7.1f}pp {ins:>+6.1f}pp")
        print("  Read down the held-out column: the grouping with the highest held-out lift is the best real")
        print("  model. Where held-out >> collapses below in-sample, the grouping has cut into noise. The")
        print("  point the held-out stops rising is the reachable ceiling on this data - then inspect that")
        print("  grouping's corrections (--dim <name>) to see if they cohere into an explicable rule.")
        return

    seg = DIMS[a.dim]
    cells = cell_corrections(fit, seg, a.min_cell, a.cap)
    gby = defaultdict(list)
    for r in grade:
        gby[seg(r)].append(r)
    print(f"\n  dim = {a.dim}")
    print(f"  {'cell':28} {'fitN':>4} {'fitMed':>6} {'k':>5} | {'grdN':>4} {'base':>6} {'corr':>6} {'lift':>5}")
    tot_b = tot_c = tot_n = 0
    for c in sorted(set(list(cells) + list(gby)), key=lambda k: -len(gby.get(k, []))):
        k, fn, fm = cells.get(c, (1.0, 0, 0.0))
        gxs = [r["_fc"] for r in gby.get(c, [])]
        gn = len(gxs)
        if gn == 0 and fn == 0:
            continue
        b = w20(gxs)
        cor = w20([k * x for x in gxs])
        tot_b += b
        tot_c += cor
        tot_n += gn
        lift = f"{cor - b:+d}" if gn else "-"
        print(f"  {c:28} {fn:>4} {fm:>6.2f} {k:>5.2f} | {gn:>4} {b:>3}/{gn:<2} {cor:>3}/{gn:<2} {lift:>5}")
    if tot_n:
        print(f"\n  GRADE (held-out) total: baseline {tot_b}/{tot_n} ({tot_b/tot_n*100:.0f}%) "
              f"-> corrected {tot_c}/{tot_n} ({tot_c/tot_n*100:.0f}%)  held-out lift {(tot_c-tot_b)/tot_n*100:+.1f}pp")
    fb = w20([r["_fc"] for r in fit])
    fc = w20([cells.get(seg(r), (1.0, 0, 0))[0] * r["_fc"] for r in fit])
    print(f"  FIT (in-sample) control: baseline {fb}/{len(fit)} ({fb/len(fit)*100:.0f}%) "
          f"-> corrected {fc}/{len(fit)} ({fc/len(fit)*100:.0f}%)  in-sample lift {(fc-fb)/len(fit)*100:+.1f}pp")
    print("  Read: keep the split only if the HELD-OUT lift is positive and near the in-sample lift.")


if __name__ == "__main__":
    main()
