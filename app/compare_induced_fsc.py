#!/usr/bin/env python3
r"""
Avia Solutions - held-out A/B for extending the induced capacity floor to FSC (hub-carrier launches).
==================================================================================================
FSC induced routes (LOT/other hub carriers launching into thin markets that fill via network + feed) are
62% of the induced cohort and currently get NO floor (INDUCED_TYPES = LCC/ULCC only), so they read low - the
WAW under-read. analyze_induced shows they fill to a load factor about as tight as the low-cost carriers, so
a capacity x LF floor should work. This validates it WITHOUT a re-run: fit the FSC load factors on 2016-2018,
apply the floor to the HELD-OUT FSC induced routes, grade fc/outturn (the capacity-anchored test) with vs
without the floor.

The floor only ever LIFTS (floored = max(engine forecast, capacity x LF)), so it can only help an under-read;
it grades against outturn_pax (onboard), the induced test. Detector matches the live engine: FSC + measured
market / capacity < 0.40.

    py -3.12 compare_induced_fsc.py E:\Avia\QSI\backtests\bt_6yr_induced.csv --fit-years 2016,2017,2018

FSC induced keeps its NORMAL fare in the economics (no stimulation discount); this script only tests the demand
floor. Reads the CSV only.
"""
import argparse, csv

HAUL_E = [800.0, 2500.0, 6000.0]
MKT_CAP_MAX = 0.40


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _haul_idx(g):
    g = g or 0.0
    for i, e in enumerate(HAUL_E):
        if g < e:
            return i
    return len(HAUL_E)


def _w20(rs):
    return sum(1 for x in rs if 0.8 <= x <= 1.2)


def load(path, min_outturn):
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        if (r.get("type") or "") != "FSC":
            continue
        nat = _f(r.get("natural")); p2p = _f(r.get("p2p_outturn")); out = _f(r.get("outturn_pax"))
        cap = _f(r.get("capacity")); fc = _f(r.get("forecast_pax")); gcd = _f(r.get("gcd_km"))
        feed = (_f(r.get("feed_beyond")) or 0.0) + (_f(r.get("feed_behind")) or 0.0)  # alliance-weighted
        if None in (nat, p2p, out, cap, fc, gcd) or out < min_outturn or cap <= 0 or fc <= 0:
            continue
        if nat >= p2p:                                # induced only (measured market < carried)
            continue
        if nat / cap >= MKT_CAP_MAX:                  # live detector: market/capacity < 0.40
            continue
        rows.append({"year": str(r.get("year")), "hi": _haul_idx(gcd),
                     "out": out, "cap": cap, "fc": fc, "achlf": out / cap,
                     "feed_share": feed / cap})       # hub-feed strength (forecast-time, alliance-weighted)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--feed-gate", type=float, default=0.10,
                    help="min alliance feed / capacity for the floor to fire (John's hub-feed gate)")
    a = ap.parse_args()
    fit_years = set(a.fit_years.split(","))
    rows = load(a.csv, a.min_outturn)
    if not rows:
        print("No FSC induced rows (need type=FSC, natural<p2p, market/cap<0.40)."); return

    # 1. fit FSC load factor by haul on the fit years (median achieved LF)
    labels = ["<800", "800-2500", "2500-6000", ">6000"]
    lf = {}
    print(f"FSC INDUCED FLOOR - held-out A/B ({a.csv})")
    print(f"\n  FSC load factor fitted on {sorted(fit_years)} (median achieved LF by haul):")
    for i, lbl in enumerate(labels):
        v = [r["achlf"] for r in rows if r["hi"] == i and r["year"] in fit_years]
        lf[i] = _median(v) if len(v) >= 8 else _median([r["achlf"] for r in rows if r["year"] in fit_years])
        print(f"    {lbl:>11}  n={len(v):>4}  LF {lf[i]:.2f}")

    def _floored(r):
        return max(r["fc"], r["cap"] * lf[r["hi"]])

    def _grade(name, rs):
        if len(rs) < 10:
            print(f"  {name}: n={len(rs)} (too few)"); return
        wo = [r["fc"] / r["out"] for r in rs]
        w = [_floored(r) / r["out"] for r in rs]
        # feed-gated: only floor where the carrier has material alliance feed at the hub (John's point)
        g = [(_floored(r) if r["feed_share"] >= a.feed_gate else r["fc"]) / r["out"] for r in rs]
        print(f"\n  {name}: FSC induced n={len(rs)}")
        print(f"                          within +/-20%     median fc/out   over(>1.2)")
        for lab, xs in [("no floor (now)", wo), ("blanket floor", w),
                        (f"feed-gated floor (>= {a.feed_gate:.2f})", g)]:
            over = sum(1 for x in xs if x > 1.2)
            print(f"    {lab:>26}  {_w20(xs):>4}/{len(rs)} ({100*_w20(xs)//len(rs):>2}%)   "
                  f"{_median(xs):>5.2f}      {100*over//len(rs):>2}%")
        print(f"    blanket floor within +/-20%: {_w20(w)-_w20(wo):+d} ({100*(_w20(w)-_w20(wo))/len(rs):+.1f}pp)")

    _grade("fit " + ",".join(sorted(fit_years)), [r for r in rows if r["year"] in fit_years])
    held = [r for r in rows if r["year"] not in fit_years]
    for y in sorted({r["year"] for r in held}):
        _grade("held-out " + y, [r for r in held if r["year"] == y])

    # FEED SPLIT on held-out: does the blanket floor OVER-FLOW the feed-thin (no hub) FSC routes?
    if held:
        print(f"\n  HELD-OUT FEED SPLIT (does the floor over-flow feed-thin routes? blanket floor, graded fc/out):")
        print(f"    {'group':>18}  {'n':>4}  {'median fc/out':>13}  {'over(>1.2)':>10}  {'+/-20%':>7}")
        for lab, sub in [("feed present", [r for r in held if r["feed_share"] >= a.feed_gate]),
                         ("feed thin (no hub)", [r for r in held if r["feed_share"] < a.feed_gate])]:
            if len(sub) < 5:
                print(f"    {lab:>18}  {len(sub):>4}   (too few)"); continue
            w = [_floored(r) / r["out"] for r in sub]
            over = sum(1 for x in w if x > 1.2)
            print(f"    {lab:>18}  {len(sub):>4}  {_median(w):>13.2f}  {100*over//len(sub):>9}%  "
                  f"{100*_w20(w)//len(sub):>6}%")
        print("    -> if 'feed thin' shows a high median / high over-share, the floor is over-flowing feed-less\n"
              "       routes and should be feed-GATED; if feed-thin is tiny or also centred, the blanket floor is safe.")
    print("\n  ships if within +/-20% is positive on the held-out year(s) and the median centres toward 1.0.")


if __name__ == "__main__":
    main()
