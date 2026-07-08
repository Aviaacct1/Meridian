#!/usr/bin/env python3
r"""
Avia Solutions - market-size capture trim calibration (accuracy plan, level-bias fix).
==================================================================================================
The offset-0 held-out grade shows the engine over-forecasts FORECASTABLE P2P by ~1.5x, uniform across
airline type (FSC 1.46, LCC 1.49, ULCC 1.50) but strongly size-dependent: thin markets read ~1.95
(169 over / 48 under) while 15-50k reads ~1.19. Type does not discriminate; measured market size does.
So the fix is a capture trim keyed on the MEASURED market (known at forecast time, no outturn leak),
strong in thin markets and light in mid/large ones - replacing the Item 9 flat per-type trim.

This learns that size table from the FIT years only (2016-2018), choosing per size bucket the multiplier
that MAXIMISES the share of forecastable routes within +/-20% of outturn (not the one that centres the
median - a trim that slides the already-right routes off their mark is a loss even if the median improves),
tie-broken toward the least intervention (m closest to 1.0).

DISCIPLINE (Fable): fit on 2016-2018 ONLY. The held-out years (2024, 2025 at offset 0) are the truth and
are graded by compare_market_trim.py, never fitted here.

    py -3.12 calib_market_trim.py E:\Avia\QSI\backtests\decomp_6yr.csv --fit-years 2016,2017,2018 \
        --applied-trim type --out market_trim.json

--applied-trim says what trim the CSV's fc_over_p2p ALREADY carries, so the raw (untrimmed) engine ratio
is recovered before fitting: "type" = the live flat per-type table was on (the run used --market-factor);
"none" = no trim was applied. Set it to match how the CSV was produced.
"""
import argparse, csv, json, math

# The live flat per-type trim (route_forecast.MARKET_FACTOR_BY_TYPE), so we can divide it back out to
# recover the raw engine ratio when the fit CSV was produced with --market-factor on.
TYPE_FLAT = {"FSC": 0.85, "ULCC": 0.85, "LCC": 0.95, "Regional": 0.90}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _applied_mult(row_type, mode):
    """The trim already baked into fc_over_p2p, to divide back out to raw."""
    if mode == "none":
        return 1.0
    return TYPE_FLAT.get(row_type, TYPE_FLAT["FSC"])   # "type"


def _w20(ratios):
    return sum(1 for x in ratios if 0.8 <= x <= 1.2)


def _best_mult(raws, lo=0.40, hi=1.15, step=0.01, min_n=20, center_floor=0.92):
    """The multiplier that maximises within-+/-20% on this bucket's raw ratios; tie-break to least trim.
    Returns (mult, hits_at_mult, hits_at_1.0). Falls back to 1.0 (no trim) for a thin bucket. A hit-max
    on a wide right-skewed bucket can under-centre (trim so hard the median drops below 1), banking a
    big-market UNDER-forecast to catch the left mass. center_floor stops that: the trimmed median may not
    fall below it (trimmed median = raw median x m, so this is a lower bound m >= center_floor/raw_median)."""
    if len(raws) < min_n:
        return 1.0, _w20(raws), _w20(raws)
    rm = _median(raws)
    lo_eff = max(lo, (center_floor / rm) if rm > 0 else lo)
    best = None
    m = lo_eff
    while m <= hi + 1e-9:
        hits = _w20([r * m for r in raws])
        key = (hits, -abs(math.log(m)))     # max hits, then least |log m|
        if best is None or key > best[0]:
            best = (key, m, hits)
        m += step
    return round(best[1], 3), best[2], _w20(raws)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018", help="years to LEARN from (never the held-out)")
    ap.add_argument("--applied-trim", choices=["type", "none"], default="type",
                    help="trim already in fc_over_p2p: 'type'=--market-factor was on; 'none'=raw")
    ap.add_argument("--edges", default="15000,50000,150000", help="market-size bucket edges (ascending)")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--floor", type=float, default=0.45, help="do not trim below this")
    ap.add_argument("--cap", type=float, default=1.10, help="do not lift above this")
    ap.add_argument("--center-floor", type=float, default=0.92,
                    help="a bucket's trimmed median may not fall below this (stops big-market under-trim)")
    ap.add_argument("--by-type", action="store_true", help="fit a separate size table per airline type")
    ap.add_argument("--out", default="market_trim.json")
    a = ap.parse_args()
    fit = set(a.fit_years.split(","))
    edges = [float(x) for x in a.edges.split(",")]

    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        if str(r.get("year")) not in fit:
            continue
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        if p2p is None or p2p < a.min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p:          # forecastable only (market pre-existed)
            continue
        raw = fw / _applied_mult(r.get("type"), a.applied_trim)
        rows.append({"type": r.get("type") or "?", "mkt": nat, "raw": raw})
    if not rows:
        print("No forecastable fit-year rows. Check --fit-years and the CSV columns "
              "(need natural, p2p_outturn, fc_over_p2p)."); return

    def bucket_idx(mkt):
        for i, e in enumerate(edges):
            if mkt < e:
                return i
        return len(edges)

    def fit_table(recs, label):
        table = []
        print(f"\n  {label}: n={len(recs)}  raw median fc/p2p {_median([x['raw'] for x in recs]):.2f}")
        print(f"    {'bucket':>14}  {'n':>4}  {'raw med':>8}  {'mult':>6}  {'trimmed med':>11}  "
              f"{'+/-20% raw':>10}  {'+/-20% trim':>11}")
        nb = len(edges) + 1
        lbls = []
        for i in range(nb):
            lo = 0 if i == 0 else edges[i - 1]
            hi = edges[i] if i < len(edges) else None
            lbls.append(f"<{int(edges[0]/1000)}k" if i == 0 else
                        (f">{int(edges[-1]/1000)}k" if i == len(edges) else
                         f"{int(edges[i-1]/1000)}-{int(edges[i]/1000)}k"))
        for i in range(nb):
            b = [x for x in recs if bucket_idx(x["mkt"]) == i]
            raws = [x["raw"] for x in b]
            if not b:
                m = 1.0
            else:
                m, _, _ = _best_mult(raws, center_floor=a.center_floor)
                m = max(a.floor, min(a.cap, m))
            trimmed = [r * m for r in raws]
            print(f"    {lbls[i]:>14}  {len(b):>4}  {_median(raws):>8.2f}  {m:>6.3f}  "
                  f"{_median(trimmed):>11.2f}  {_w20(raws):>4}/{len(raws) or 0:<4}  "
                  f"{_w20(trimmed):>5}/{len(raws) or 0:<4}")
            if i < len(edges):
                table.append([edges[i], m])
            else:
                if m != 1.0:
                    table.append([1e12, m])
        # whole-set hit rate before/after
        before = _w20([x["raw"] for x in recs])
        after = _w20([x["raw"] * _lookup(table, x["mkt"]) for x in recs])
        print(f"    fit-year +/-20%: {before}/{len(recs)} raw  ->  {after}/{len(recs)} trimmed "
              f"({100*(after-before)/len(recs):+.1f}pp in-sample)")
        return table

    def _lookup(table, mkt):
        for edge, f in table:
            if mkt < edge:
                return f
        return 1.0

    out = {"meta": {"fit_years": sorted(fit), "applied_trim": a.applied_trim,
                    "edges": edges, "floor": a.floor, "cap": a.cap, "n_fit": len(rows)}}
    print(f"MARKET-SIZE TRIM FIT (fit years {sorted(fit)}, applied-trim {a.applied_trim})")
    if a.by_type:
        out["by_type"] = {}
        for t in ("FSC", "LCC", "ULCC", "Regional"):
            tr = [x for x in rows if x["type"] == t]
            if len(tr) >= 30:
                out["by_type"][t] = fit_table(tr, f"type {t}")
    else:
        out["pooled"] = fit_table(rows, "pooled (all types)")
    json.dump(out, open(a.out, "w"), indent=0)
    print(f"\nwrote {a.out}. Validate held-out:  py -3.12 compare_market_trim.py "
          f"<val CSV> {a.out} --applied-trim {a.applied_trim}")


if __name__ == "__main__":
    main()
