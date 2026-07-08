#!/usr/bin/env python3
r"""
Avia Solutions - held-out A/B for the capture-share trim (increment on the shipped size trim).
==================================================================================================
WITHOUT = the CURRENT live behaviour: raw x size_mult(market)  (the shipped size trim).
WITH    = raw x size_mult(market) x share_mult(propensity)      (add the candidate share trim).
Raw recovered by dividing fc_over_p2p by the OLD flat trim (--applied-trim type). No re-run.

    py -3.12 compare_share_trim.py E:\Avia\QSI\backtests\val24_o0.csv share_trim.json --applied-trim type
    py -3.12 compare_share_trim.py E:\Avia\QSI\backtests\val25_o0.csv share_trim.json --applied-trim type

Ships if within +/-20% is positive on BOTH held-out years and median |log err| does not degrade.
"""
import argparse, csv, json, math

TYPE_FLAT = {"FSC": 0.85, "ULCC": 0.85, "LCC": 0.95, "Regional": 0.90}
SIZE_TRIM = [(15000.0, 0.765), (50000.0, 0.821), (150000.0, 0.809), (float("inf"), 0.745)]


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


def _size_mult(mkt):
    for edge, f in SIZE_TRIM:
        if (mkt or 0) < edge:
            return f
    return 1.0


def _w20(rs):
    return sum(1 for x in rs if 0.8 <= x <= 1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("share_json")
    ap.add_argument("--applied-trim", choices=["type", "none"], default="type")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    a = ap.parse_args()
    tbl = json.load(open(a.share_json)).get("share", [])

    def share_mult(p):
        for edge, f in tbl:
            if (p if p is not None else 0) < edge:
                return float(f)
        return 1.0

    recs = []
    for r in csv.DictReader(open(a.csv, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        prop = _f(r.get("propensity"))
        if p2p is None or p2p < a.min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p or prop is None:
            continue
        raw = fw / (_flat(r.get("type")) if a.applied_trim == "type" else 1.0)
        without = raw * _size_mult(nat)
        with_ = without * share_mult(prop)
        recs.append({"y": str(r.get("year")), "wo": without, "w": with_,
                     "woe": abs(math.log(without)), "we": abs(math.log(with_))})
    if not recs:
        print("No forecastable rows with propensity."); return

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
        print(f"    size trim only        {_w20(wo):>4}/{n} ({100*_w20(wo)//n:>2}%)      "
              f"{_median(wo):>6.2f}          {_median(woe):.3f}")
        print(f"    size x share trim     {_w20(w):>4}/{n} ({100*_w20(w)//n:>2}%)      "
              f"{_median(w):>6.2f}          {_median(we):.3f}")
        print(f"    moved closer: {imp}/{n} ({100*imp//n}%)   within +/-20%: {d20:+d} ({100*d20/n:+.1f}pp)")

    print(f"\nCAPTURE-SHARE TRIM A/B: {a.csv}   (candidate: {a.share_json}, applied-trim {a.applied_trim})")
    _report("ALL held-out", recs)
    for y in sorted({x["y"] for x in recs}):
        _report(f"year {y}", [x for x in recs if x["y"] == y])
    print("\n  ships if within +/-20% is positive on BOTH held-out years and median |log err| does not degrade.")


if __name__ == "__main__":
    main()
