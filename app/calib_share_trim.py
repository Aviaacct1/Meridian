#!/usr/bin/env python3
r"""
Avia Solutions - capture-share level trim (accuracy plan, second bias lever after the size trim).
==================================================================================================
The tier slices show a forecast-time LEVEL bias keyed on the QSI capture share (propensity): low-share
routes UNDER-forecast (median ~0.65) and high-share routes OVER-forecast (~1.26). Share is known at forecast
time, so this is a correctable bias (unlike the capture SPREAD, which is not). This fits a share-keyed
correction that LIFTS low-share buckets and TRIMS high-share ones, centring each toward 1.0.

It is calibrated on the RESIDUAL left after the SHIPPED size trim (recover raw / old flat, apply the live
_SIZE_TRIM, THEN bucket by share), so the share trim is an INCREMENT on the size trim, not a double-count.
The live trim becomes size_mult(market) x share_mult(propensity).

Per bucket it takes the multiplier that MAXIMISES within-+/-20%, constrained so the bucket's trimmed median
stays in [center_floor, center_ceil] (so a lift can't overshoot and a trim can't under-cut); tie-break to
least intervention. Fit on 2016-2018 ONLY; held-out 2024/2025 graded by compare_share_trim.py.

    py -3.12 calib_share_trim.py E:\Avia\QSI\backtests\decomp_6yr.csv --fit-years 2016,2017,2018 \
        --applied-trim type --out share_trim.json
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


def _best_mult(base, lo=0.40, hi=1.75, step=0.01, min_n=20, cfloor=0.92, cceil=1.08):
    """Multiplier that maximises within-+/-20% on this share bucket's POST-size-trim ratios, constrained so
    the bucket's trimmed median stays in [cfloor, cceil] (centres a lift or a trim without overshoot)."""
    if len(base) < min_n:
        return 1.0
    rm = _median(base)
    if rm <= 0:
        return 1.0
    lo_eff = max(lo, cfloor / rm)
    hi_eff = min(hi, cceil / rm)
    if hi_eff < lo_eff:                 # median already outside the target: clamp to the nearest edge
        return round(cfloor / rm if rm > cceil else cceil / rm, 3)
    best = None; m = lo_eff
    while m <= hi_eff + 1e-9:
        hits = _w20([r * m for r in base])
        key = (hits, -abs(math.log(m)))
        if best is None or key > best[0]:
            best = (key, m)
        m += step
    return round(best[1], 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--applied-trim", choices=["type", "none"], default="type")
    ap.add_argument("--edges", default="0.15,0.35,0.60", help="QSI capture-share bucket edges")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--out", default="share_trim.json")
    a = ap.parse_args()
    fit = set(a.fit_years.split(","))
    edges = [float(x) for x in a.edges.split(",")]
    lbls = ([f"<{edges[0]}"] +
            [f"{edges[i-1]}-{edges[i]}" for i in range(1, len(edges))] + [f">{edges[-1]}"])

    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        if str(r.get("year")) not in fit:
            continue
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        prop = _f(r.get("propensity"))
        if p2p is None or p2p < a.min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p or prop is None:
            continue
        raw = fw / (_flat(r.get("type")) if a.applied_trim == "type" else 1.0)
        base = raw * _size_mult(nat)                 # residual AFTER the shipped size trim
        rows.append({"prop": prop, "base": base})
    if not rows:
        print("No forecastable fit-year rows with propensity."); return

    def bidx(p):
        for i, e in enumerate(edges):
            if p < e:
                return i
        return len(edges)

    print(f"CAPTURE-SHARE TRIM FIT (residual after size trim; fit {sorted(fit)}, applied-trim {a.applied_trim})")
    print(f"  {'share bucket':>14}  {'n':>4}  {'post-size med':>13}  {'mult':>6}  {'trimmed med':>11}  "
          f"{'+/-20% base':>11}  {'+/-20% trim':>11}")
    table = []
    for i, lbl in enumerate(lbls):
        b = [x["base"] for x in rows if bidx(x["prop"]) == i]
        if len(b) < 20:
            m = 1.0
        else:
            m = _best_mult(b)
        tr = [x * m for x in b]
        print(f"  {lbl:>14}  {len(b):>4}  {_median(b):>13.2f}  {m:>6.3f}  {_median(tr):>11.2f}  "
              f"{_w20(b):>4}/{len(b) or 0:<4}  {_w20(tr):>4}/{len(b) or 0:<4}")
        if i < len(edges):
            table.append([edges[i], m])
        elif m != 1.0:
            table.append([1e12, m])

    def _lookup(p):
        for edge, f in table:
            if p < edge:
                return f
        return 1.0
    before = _w20([x["base"] for x in rows])
    after = _w20([x["base"] * _lookup(x["prop"]) for x in rows])
    print(f"  fit-year +/-20% (post-size): {before}/{len(rows)} -> {after}/{len(rows)} "
          f"({100*(after-before)/len(rows):+.1f}pp in-sample)")
    json.dump({"meta": {"fit_years": sorted(fit), "applied_trim": a.applied_trim, "edges": edges,
                        "note": "increment on the shipped size trim; live = size_mult x share_mult"},
               "share": table}, open(a.out, "w"), indent=0)
    print(f"\nwrote {a.out}. Validate:  py -3.12 compare_share_trim.py <val CSV> {a.out} --applied-trim {a.applied_trim}")


if __name__ == "__main__":
    main()
