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

    # 1. fit FSC load factor by haul on the fit years - two ways:
    #    median  = centres the median fc/out at 1.0
    #    hit-max = the LF that MAXIMISES within-+/-20% count on the fit routes (John's goal), tie-break to median
    labels = ["<800", "800-2500", "2500-6000", ">6000"]
    fit_rows = [r for r in rows if r["year"] in fit_years]
    lf_med, lf_hm = {}, {}

    def _hitmax_lf(haul_rows, med):
        if len(haul_rows) < 8:
            return med
        best = None; x = 0.20
        while x <= 0.95 + 1e-9:
            hits = sum(1 for r in haul_rows if 0.8 <= max(r["fc"], r["cap"] * x) / r["out"] <= 1.2)
            key = (hits, -abs(x - med))          # max hits, then nearest the median (least extreme)
            if best is None or key > best[0]:
                best = (key, x)
            x += 0.01
        return round(best[1], 2)

    print(f"FSC INDUCED FLOOR - held-out A/B ({a.csv})")
    print(f"\n  FSC load factor fitted on {sorted(fit_years)} by haul:")
    print(f"    {'haul':>11}  {'n':>4}  {'median LF':>9}  {'hit-max LF':>10}")
    allmed = _median([r["achlf"] for r in fit_rows])
    for i, lbl in enumerate(labels):
        hr = [r for r in fit_rows if r["hi"] == i]
        med = _median([r["achlf"] for r in hr]) if len(hr) >= 8 else allmed
        lf_med[i] = med
        lf_hm[i] = _hitmax_lf(hr, med)
        print(f"    {lbl:>11}  {len(hr):>4}  {med:>9.2f}  {lf_hm[i]:>10.2f}")

    def _fl(r, tbl):
        return max(r["fc"], r["cap"] * tbl[r["hi"]])

    def _grade(name, rs):
        if len(rs) < 10:
            print(f"  {name}: n={len(rs)} (too few)"); return
        wo = [r["fc"] / r["out"] for r in rs]
        wm = [_fl(r, lf_med) / r["out"] for r in rs]
        wh = [_fl(r, lf_hm) / r["out"] for r in rs]
        print(f"\n  {name}: FSC induced n={len(rs)}")
        print(f"                          within +/-20%     median fc/out   over(>1.2)")
        for lab, xs in [("no floor (now)", wo), ("median-LF floor", wm), ("hit-max-LF floor", wh)]:
            over = sum(1 for x in xs if x > 1.2)
            print(f"    {lab:>24}  {_w20(xs):>4}/{len(rs)} ({100*_w20(xs)//len(rs):>2}%)   "
                  f"{_median(xs):>5.2f}      {100*over//len(rs):>2}%")

    _grade("fit " + ",".join(sorted(fit_years)), fit_rows)
    held = [r for r in rows if r["year"] not in fit_years]
    for y in sorted({r["year"] for r in held}):
        _grade("held-out " + y, [r for r in held if r["year"] == y])
    print("\n  Take the LF table (median or hit-max) with the higher HELD-OUT +/-20%; that is the one to wire.")

    # GATE CEILING: an alliance/feed gate can only move a route INTO +/-20% where the blanket floor
    # OVER-forecasts it AND the engine's UNFLOORED forecast was already in-band. Count that from the CSV -
    # it's the most any gate (alliance or otherwise) could add, before we build the alliance flag + re-run.
    if held:
        helps = hurts = 0
        hurt_feed = []
        for r in held:
            u = r["fc"] / r["out"]; f = _fl(r, lf_med) / r["out"]
            uin = 0.8 <= u <= 1.2; fin = 0.8 <= f <= 1.2
            if fin and not uin:
                helps += 1                     # floor rescued it (engine was out) -> must keep flooring
            elif uin and not fin:
                hurts += 1                     # engine was right, floor broke it -> a gate would recover it
                hurt_feed.append(r["feed_share"])
        base = _w20([_fl(r, lf_med) / r["out"] for r in held])
        n = len(held)
        print(f"\n  GATE CEILING (held-out, median floor, n={n}):")
        print(f"    floor RESCUES (engine out-of-band, floored in): {helps}  -> these need the floor, a gate must keep them")
        print(f"    floor BREAKS  (engine in-band, floored out):    {hurts}  -> the ONLY routes a gate could recover")
        print(f"    current floored within +/-20%: {base}/{n} ({100*base//n}%);  a PERFECT gate ceiling: "
              f"{base+hurts}/{n} ({100*(base+hurts)//n}%)")
        if hurt_feed:
            lo = sum(1 for x in hurt_feed if x < a.feed_gate)
            print(f"    of the {hurts} recoverable, {lo} have feed < {a.feed_gate:.2f} (a feed/alliance gate could target these)")
        print("    -> if 'floor BREAKS' is small, the blanket floor is already near the ceiling and a gate can't")
        print("       add much; if it's large AND those routes are low-feed, an alliance gate is worth building.")
    print("\n  ships if within +/-20% is positive on the held-out year(s) and the median centres toward 1.0.")


if __name__ == "__main__":
    main()
