#!/usr/bin/env python3
r"""
Avia Solutions - P2P vs TOTAL grade split (is the FSC forecastable over-read real, or a P2P/feed attribution artefact?).
==================================================================================================
The full-run FORECASTABLE deep-dive shows FSC over-reading on the PURE-P2P grade (median fc/p2p 1.25, long-haul
1.89, thin-market 1.78), while the SAME routes' fc/TOTAL is ~0.91. If the over-read is only on the P2P leg and
the total is centred, it's an ATTRIBUTION artefact: on connecting-heavy long-haul the engine assigns too much of
a healthy total to the P2P leg and too little to feed. Trimming that would push the total UNDER to fix a ratio
the customer never sees. If the over-read survives on the TOTAL, it's a REAL over-forecast worth a lever.

This grades fc/p2p and fc/out side by side, forecastable routes only, across the same type / haul / hub / market
buckets, so you can read per bucket: does the total stay centred where the P2P over-reads?

    py -3.12 analyze_split.py C:\AviaDev\app\bt_v2_6yr.csv

Reads the CSV only. fc_over_out (total onboard grade) and fc_over_p2p (P2P-only grade) both need to be present.
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


def _w20(xs):
    return sum(1 for x in xs if 0.8 <= x <= 1.2)


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
    a = ap.parse_args()
    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); out = _f(r.get("outturn_pax"))
        fp = _f(r.get("fc_over_p2p")); fo = _f(r.get("fc_over_out"))
        if fo is None and out and _f(r.get("forecast_pax")):
            fo = _f(r.get("forecast_pax")) / out
        if p2p is None or p2p < a.min_outturn or fp is None or fp <= 0 or fo is None or fo <= 0:
            continue
        if nat is None or nat < p2p:                  # forecastable only
            continue
        rows.append({"type": r.get("type") or "?", "haul": _haul(_f(r.get("gcd_km"))),
                     "mkt": _mkt(nat), "hub": "hub" if str(r.get("hub_dest")).strip().lower() in ("1", "true", "yes") else "non-hub",
                     "fp": fp, "fo": fo})
    if not rows:
        print("No forecastable rows with both grades."); return

    def _line(label, rs):
        n = len(rs)
        fp = [r["fp"] for r in rs]; fo = [r["fo"] for r in rs]
        print(f"    {label:>12}  {n:>5}   {_median(fp):>7.2f}  {100*_w20(fp)//n:>4}%     "
              f"{_median(fo):>7.2f}  {100*_w20(fo)//n:>4}%")

    def _block(title, keyfn, order):
        print(f"\n  {title}")
        print(f"    {'bucket':>12}  {'n':>5}   {'med P2P':>7}  {'+-20%':>5}     {'med TOTAL':>7}  {'+-20%':>5}")
        groups = {}
        for r in rows:
            groups.setdefault(keyfn(r), []).append(r)
        for k in order:
            if groups.get(k):
                _line(k, groups[k])

    print(f"\nP2P vs TOTAL grade (forecastable, n={len(rows)}): {a.csv}")
    print("  a bucket where med P2P is high but med TOTAL ~1.0 = attribution (feed under-credited on the split,")
    print("  total is right, do NOT trim); a bucket high on BOTH = a real over-forecast worth a lever.")
    _line("ALL", rows)
    _block("by type", lambda r: r["type"], ["FSC", "LCC", "ULCC", "Regional"])
    _block("by haul", lambda r: r["haul"], ["<800", "800-2500", "2500-6000", ">6000"])
    _block("by market", lambda r: r["mkt"], ["<15k", "15-50k", "50-150k", ">150k"])
    _block("by hub", lambda r: r["hub"], ["hub", "non-hub"])
    # FSC long-haul + thin, the two suspect buckets, isolated
    for lbl, sub in [("FSC >6000km", [r for r in rows if r["type"] == "FSC" and r["haul"] == ">6000"]),
                     ("FSC <15k market", [r for r in rows if r["type"] == "FSC" and r["mkt"] == "<15k"])]:
        if len(sub) >= 10:
            print(f"\n  SUSPECT: {lbl}")
            print(f"    {'':>12}  {'n':>5}   {'med P2P':>7}  {'+-20%':>5}     {'med TOTAL':>7}  {'+-20%':>5}")
            _line(lbl, sub)
    print("\n  If the SUSPECT buckets read high on P2P but ~1.0 on TOTAL, the over-read is attribution and the")
    print("  fix (if any) is to shift P2P->feed on the split, not trim the total. Only chase it if TOTAL is high too.")


if __name__ == "__main__":
    main()
