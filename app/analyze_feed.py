#!/usr/bin/env python3
r"""
Avia Solutions - feed-leg under-credit diagnostic (the coupled P2P/feed recalibration, step 1).
==================================================================================================
The P2P-vs-TOTAL split (analyze_split.py) showed one root cause behind two symptoms: the connecting-FEED leg
is under-credited, so (a) the P2P leg absorbs the missing demand and over-reads (fc/p2p 1.25, long-haul 2.03),
and (b) the total still lands mildly under (fc/out 0.89) because the feed under-read outweighs the P2P over-read.
The fix is to raise feed credit and trim P2P capture so BOTH grades centre at 1.0.

This step SIZES the feed gap from the back-test CSV, so we know the multiplier and whether it's uniform or
bucket-specific before touching a knob. Per route:
    engine feed        = feed_beyond + feed_behind        (what the model credited)
    implied actual feed = outturn_pax - p2p_outturn        (onboard minus the P2P O&D market; rough but directional)
    under-credit factor = implied actual feed / engine feed
A factor > 1 means the feed model is crediting too little. Reported overall and by haul / hub / type / market,
alongside the current fc/out median, so a global vs conditional feed bump can be judged.

    py -3.12 analyze_feed.py C:\AviaDev\app\bt_v2_6yr.csv

Directional sizing only (implied actual feed assumes the route carries ~all of its P2P market); the actual
calibration is a backtest that tunes the feed level (qsi_k / DEFAULT_CONN_CAPTURE) + a P2P trim and grades BOTH
fc/p2p and fc/out on 2016-2018 fit / held-out. Reads the CSV only.
"""
import argparse, csv


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _haul(g):
    g = g or 0
    return "<800" if g < 800 else "800-2500" if g < 2500 else "2500-6000" if g < 6000 else ">6000"


def _mkt(m):
    m = m or 0
    return "<15k" if m < 15000 else "15-50k" if m < 50000 else "50-150k" if m < 150000 else ">150k"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--forecastable-only", action="store_true", help="exclude induced (floored) routes")
    a = ap.parse_args()
    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); out = _f(r.get("outturn_pax"))
        fo = _f(r.get("fc_over_out")); fb = _f(r.get("feed_beyond")); bh = _f(r.get("feed_behind"))
        if p2p is None or p2p < a.min_outturn or out is None or out <= 0 or fo is None or fo <= 0:
            continue
        if a.forecastable_only and (nat is None or nat < p2p):
            continue
        efeed = (fb or 0.0) + (bh or 0.0)
        afeed = max(0.0, out - p2p)                      # implied actual feed (onboard minus P2P market)
        rows.append({"type": r.get("type") or "?", "haul": _haul(_f(r.get("gcd_km"))),
                     "mkt": _mkt(nat), "hub": "hub" if str(r.get("hub_dest")).strip().lower() in ("1", "true", "yes") else "non-hub",
                     "efeed": efeed, "afeed": afeed,
                     "ratio": (afeed / efeed) if efeed > 50 else None, "fo": fo,
                     "feedshare": afeed / out if out else 0.0})
    if not rows:
        print("No rows."); return

    def _line(label, rs):
        n = len(rs)
        rats = [r["ratio"] for r in rs if r["ratio"] is not None]
        fs = [r["feedshare"] for r in rs]
        fo = [r["fo"] for r in rs]
        rtxt = f"{_median(rats):>6.1f}x" if rats else "   n/a"
        print(f"    {label:>12}  {n:>5}   {rtxt} ({len(rats)})   feed {100*_median(fs):>3.0f}% of onboard   fc/out {_median(fo):.2f}")

    def _block(title, keyfn, order):
        print(f"\n  {title}")
        print(f"    {'bucket':>12}  {'n':>5}   {'under-credit':>12}   {'actual feed':>16}   {'total':>10}")
        g = {}
        for r in rows:
            g.setdefault(keyfn(r), []).append(r)
        for k in order:
            if g.get(k):
                _line(k, g[k])

    tag = "forecastable" if a.forecastable_only else "all graded"
    print(f"\nFEED UNDER-CREDIT ({tag}, n={len(rows)}): {a.csv}")
    print("  under-credit = implied actual feed / engine feed (>1 = model credits too little);")
    print("  feed % = implied actual feed as a share of onboard; fc/out = current total grade.")
    _line("ALL", rows)
    _block("by haul", lambda r: r["haul"], ["<800", "800-2500", "2500-6000", ">6000"])
    _block("by hub", lambda r: r["hub"], ["hub", "non-hub"])
    _block("by type", lambda r: r["type"], ["FSC", "LCC", "ULCC", "Regional"])
    _block("by market", lambda r: r["mkt"], ["<15k", "15-50k", "50-150k", ">150k"])
    print("\n  Read: a large, fairly UNIFORM under-credit -> a single feed-level bump (qsi_k / DEFAULT_CONN_CAPTURE);")
    print("  if it concentrates in hub / long-haul, the bump should be conditional (dominance / haul). Next: a")
    print("  backtest tuning the feed level + a P2P trim, grading BOTH fc/p2p and fc/out on 2016-2018 / held-out.")


if __name__ == "__main__":
    main()
