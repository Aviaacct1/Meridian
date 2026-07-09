#!/usr/bin/env python3
r"""
Avia Solutions - P2P/feed split calibration sizing (feed recalibration, the pre-backtest sweep).
==================================================================================================
The engine under-credits connecting feed and over-attributes to P2P; the total is right only because the two
cancel. This SIZES the coupled correction from the existing back-test CSV, no re-run: per haul bucket it finds
the P2P trim (kp) and feed lift (kf) that would centre BOTH grades at once - fc/p2p -> 1.0 (honest split) and
fc/out -> 1.0 (total held). Reweighting the CSV per route:
    P2P forecast  = captured                = fc_over_p2p x p2p_outturn
    engine feed   = feed_beyond + feed_behind
    new fc/p2p    = fc_over_p2p x kp
    new fc/out    = (captured x kp + feed x kf) / outturn_pax
Fit on 2016-2018, then apply the fitted kp/kf to held-out and report both grades. Short-haul has ~no feed so kf
barely bites there (correctly); long-haul is where the lift concentrates. Forecastable routes only (induced are
handled by the floor).

    py -3.12 calib_feed_split.py C:\AviaDev\app\bt_v2_6yr.csv --fit-years 2016,2017,2018

This gives the TARGET shape (how much feed lift by haul, how much P2P trim) to translate into the feed-model
knob (qsi_k / DEFAULT_CONN_CAPTURE x dominance) + P2P trim for ONE confirming backtest. Reweighting approximates
a scalar on the existing feed; the backtest confirms the real (redistributing) model change. Reads the CSV only.
"""
import argparse, csv

HAUL_E = [800.0, 2500.0, 6000.0]
HAUL_L = ["<800", "800-2500", "2500-6000", ">6000"]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _hi(g):
    g = g or 0
    for i, e in enumerate(HAUL_E):
        if g < e:
            return i
    return len(HAUL_E)


def _w20(xs):
    return sum(1 for x in xs if 0.8 <= x <= 1.2)


def load(path, min_outturn):
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); out = _f(r.get("outturn_pax"))
        fp = _f(r.get("fc_over_p2p")); fb = _f(r.get("feed_beyond")); bh = _f(r.get("feed_behind"))
        if None in (p2p, out, fp) or p2p < min_outturn or out <= 0 or fp <= 0:
            continue
        if nat is None or nat < p2p:                      # forecastable only
            continue
        captured = fp * p2p
        feed = (fb or 0.0) + (bh or 0.0)
        rows.append({"year": str(r.get("year")), "hi": _hi(_f(r.get("gcd_km"))),
                     "fp": fp, "cap_p2p": captured, "feed": feed, "out": out})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    a = ap.parse_args()
    fit_years = set(a.fit_years.split(","))
    rows = load(a.csv, a.min_outturn)
    if not rows:
        print("No forecastable rows."); return
    fit = [r for r in rows if r["year"] in fit_years]
    held = [r for r in rows if r["year"] not in fit_years]

    # per haul: kp centres fc/p2p; then grid kf to centre fc/out (given kp)
    kp, kf = {}, {}
    print(f"P2P/FEED SPLIT CALIBRATION (forecastable, fit {sorted(fit_years)}): {a.csv}")
    print(f"  {'haul':>11}  {'n':>4}  {'kp (P2P)':>8}  {'kf (feed)':>9}   {'fc/p2p ->':>16}  {'fc/out ->':>16}")
    for i, lbl in enumerate(HAUL_L):
        b = [r for r in fit if r["hi"] == i]
        if len(b) < 15:
            kp[i] = 1.0; kf[i] = 1.0
            print(f"  {lbl:>11}  {len(b):>4}   (too few, kp=kf=1.0)"); continue
        med_fp = _median([r["fp"] for r in b])
        kp[i] = round(1.0 / med_fp, 3) if med_fp else 1.0
        # grid kf to centre fc/out given kp
        best = None; x = 0.5
        while x <= 8.0 + 1e-9:
            m = _median([(r["cap_p2p"] * kp[i] + r["feed"] * x) / r["out"] for r in b])
            key = abs(m - 1.0)
            if best is None or key < best[0]:
                best = (key, x)
            x += 0.05
        kf[i] = round(best[1], 2)
        fp0 = _median([r["fp"] for r in b]); fp1 = _median([r["fp"] * kp[i] for r in b])
        fo0 = _median([(r["cap_p2p"] + r["feed"]) / r["out"] for r in b])
        fo1 = _median([(r["cap_p2p"] * kp[i] + r["feed"] * kf[i]) / r["out"] for r in b])
        print(f"  {lbl:>11}  {len(b):>4}  {kp[i]:>8.2f}  {kf[i]:>9.2f}   {fp0:>6.2f} -> {fp1:>5.2f}   {fo0:>6.2f} -> {fo1:>5.2f}")

    def _grade(name, rs):
        if len(rs) < 10:
            print(f"  {name}: n={len(rs)} (too few)"); return
        fp0 = [r["fp"] for r in rs]; fp1 = [r["fp"] * kp[r["hi"]] for r in rs]
        fo0 = [(r["cap_p2p"] + r["feed"]) / r["out"] for r in rs]
        fo1 = [(r["cap_p2p"] * kp[r["hi"]] + r["feed"] * kf[r["hi"]]) / r["out"] for r in rs]
        print(f"\n  {name} (n={len(rs)}):")
        print(f"    fc/p2p  median {_median(fp0):.2f} -> {_median(fp1):.2f}   within+-20% {100*_w20(fp0)//len(rs)}% -> {100*_w20(fp1)//len(rs)}%")
        print(f"    fc/out  median {_median(fo0):.2f} -> {_median(fo1):.2f}   within+-20% {100*_w20(fo0)//len(rs)}% -> {100*_w20(fo1)//len(rs)}%")

    _grade("FIT " + ",".join(sorted(fit_years)), fit)
    for y in sorted({r["year"] for r in held}):
        _grade("HELD-OUT " + y, [r for r in held if r["year"] == y])
    print("\n  If BOTH grades centre toward 1.0 on held-out, the split correction generalises. Translate kf by haul")
    print("  into the feed-level knob (bigger lift on long-haul) + kp into the P2P trim, then run ONE confirming")
    print("  backtest grading fc/p2p AND fc/out. kf is a scalar proxy here; the real feed change redistributes.")


if __name__ == "__main__":
    main()
