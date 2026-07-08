#!/usr/bin/env python3
r"""
Avia Solutions - held-out A/B for the market-size capture trim (accuracy plan, level-bias fix).
==================================================================================================
Tests a fitted size table (market_trim.json from calib_market_trim.py) against the CURRENTLY LIVE flat
per-type trim, on a held-out backtest CSV, with no re-run. Shipping the size table means REPLACING the
flat trim, so the honest comparison is:
    WITHOUT (current live)  = raw engine ratio x flat-per-type trim   (0.85 FSC/ULCC, 0.95 LCC, 0.90 Reg)
    WITH    (candidate)     = raw engine ratio x size-bucket mult(measured market)
The raw ratio is recovered by dividing fc_over_p2p by whatever trim the CSV already carries (--applied-trim).

    py -3.12 compare_market_trim.py E:\Avia\QSI\backtests\val24_o0.csv market_trim.json --applied-trim type
    py -3.12 compare_market_trim.py E:\Avia\QSI\backtests\val25_o0.csv market_trim.json --applied-trim type

Ships if within +/-20% is positive on BOTH held-out years and the median does not degrade.
"""
import argparse, csv, json, math

TYPE_FLAT = {"FSC": 0.85, "ULCC": 0.85, "LCC": 0.95, "Regional": 0.90}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _flat(t):
    return TYPE_FLAT.get(t, TYPE_FLAT["FSC"])


def _applied_mult(t, mode):
    return 1.0 if mode == "none" else _flat(t)


def _size_lookup(table, mkt):
    for edge, f in table:
        if (mkt or 0) < edge:
            return float(f)
    return 1.0


def _w20(ratios):
    return sum(1 for x in ratios if 0.8 <= x <= 1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("trim_json")
    ap.add_argument("--applied-trim", choices=["type", "none"], default="type",
                    help="trim already in fc_over_p2p (must match how the CSV was produced)")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    a = ap.parse_args()
    tj = json.load(open(a.trim_json))
    pooled = tj.get("pooled")
    by_type = tj.get("by_type") or {}

    def size_table_for(t):
        if pooled:
            return pooled
        return by_type.get(t, by_type.get("FSC", []))

    recs = []
    for r in csv.DictReader(open(a.csv, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        if p2p is None or p2p < a.min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p:          # forecastable only
            continue
        t = r.get("type") or "?"
        raw = fw / _applied_mult(t, a.applied_trim)
        without = raw * _flat(t)                              # current live flat trim
        with_ = raw * _size_lookup(size_table_for(t), nat)   # candidate size trim
        recs.append({"y": str(r.get("year")), "mkt": nat,
                     "wo": without, "w": with_,
                     "woe": abs(math.log(without)), "we": abs(math.log(with_))})
    if not recs:
        print("No forecastable rows (need natural >= p2p_outturn >= min-outturn)."); return

    def _report(name, rs):
        n = len(rs)
        if n < 10:
            print(f"  {name}: n={n} (too few)"); return
        wo = [x["wo"] for x in rs]; w = [x["w"] for x in rs]
        woe = [x["woe"] for x in rs]; we = [x["we"] for x in rs]
        imp = sum(1 for x in rs if x["we"] < x["woe"] - 1e-9)
        d20 = _w20(w) - _w20(wo)
        print(f"\n  {name}: forecastable n={n}")
        print(f"                          within +/-20%     median fc/p2p     median |log err|")
        print(f"    flat per-type trim    {_w20(wo):>4}/{n} ({100*_w20(wo)//n:>2}%)      "
              f"{_median(wo):>6.2f}          {_median(woe):.3f}")
        print(f"    size-bucket trim      {_w20(w):>4}/{n} ({100*_w20(w)//n:>2}%)      "
              f"{_median(w):>6.2f}          {_median(we):.3f}")
        print(f"    moved closer: {imp}/{n} ({100*imp//n}%)   within +/-20%: {d20:+d} ({100*d20/n:+.1f}pp)")

    print(f"\nMARKET-SIZE TRIM A/B: {a.csv}   (candidate: {a.trim_json}, applied-trim {a.applied_trim})")
    _report("ALL held-out", recs)
    for y in sorted({x["y"] for x in recs}):
        _report(f"year {y}", [x for x in recs if x["y"] == y])
    print("\n  ships if within +/-20% is positive on BOTH held-out years and the median does not degrade.")


if __name__ == "__main__":
    main()
