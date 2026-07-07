#!/usr/bin/env python3
r"""
Avia Solutions - induced / new-market characterisation.
==================================================================================================
The engine sizes demand as measured_market x share x dshare x stimulation. For an INDUCED route the
measured Sabre O&D barely exists yet (few fly the pair because there is no nonstop), so captured is
tiny and the forecast reads ~0.1 of outturn. A 1.2 stimulation multiplier cannot create a market from
nothing. The backtest is a labelled set of launches, INCLUDING induced ones, with each route's
forecast-time features and its outturn, so we can test what actually predicts induced demand.

This reads a back-test results CSV and characterises the induced cohort (measured market < what the
route carried), testing one hypothesis in particular: is DEPLOYED CAPACITY at a stable load factor a
tighter predictor of induced outturn than the measured market? If so, the induced fix is a capacity-
anchored demand floor, not a bigger stimulation multiplier. It also looks for a FORECAST-TIME signal
that separates induced routes from forecastable ones before the outturn is known.

    py -3.12 analyze_induced.py E:\Avia\QSI\backtests\bt_v2_6yr_det.csv
    py -3.12 analyze_induced.py <csv> --keep-seasonal   (include summer/winter routes)
    py -3.12 analyze_induced.py <csv> --min-outturn 3000

No store access; reads the CSV only. Safe to run anywhere.
"""
import argparse, csv, math, statistics as st

HAUL_E, HAUL_L = [800, 2500, 6000], ["<800km", "800-2500", "2500-6000", ">6000km"]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _haul(v):
    v = v or 0
    for i, e in enumerate(HAUL_E):
        if v < e:
            return HAUL_L[i]
    return HAUL_L[-1]


def _med(xs):
    return st.median(xs) if xs else 0.0


def _iqr(xs):
    if len(xs) < 4:
        return (0.0, 0.0)
    s = sorted(xs)
    q1 = s[len(s) // 4]
    q3 = s[(3 * len(s)) // 4]
    return (q1, q3)


def _within(xs, lo, hi):
    return sum(1 for x in xs if lo <= x <= hi)


def _spearman(pairs):
    """Rank correlation, pure-python, robust to the wild scale of induced ratios."""
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n < 3:
        return None

    def ranks(vals):
        order = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    xa = [p[0] for p in pairs]
    xb = [p[1] for p in pairs]
    ra, rb = ranks(xa), ranks(xb)
    mra, mrb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - mra) * (rb[i] - mrb) for i in range(n))
    da = math.sqrt(sum((ra[i] - mra) ** 2 for i in range(n)))
    db = math.sqrt(sum((rb[i] - mrb) ** 2 for i in range(n)))
    return (num / (da * db)) if da and db else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--keep-seasonal", action="store_true",
                    help="include summer/winter routes (default drops them; their outturn is season-only)")
    ap.add_argument("--type", default=None, help="filter to one carrier type (FSC/LCC/ULCC/Regional)")
    a = ap.parse_args()

    rows = []
    with open(a.csv, newline="") as fh:
        for r in csv.DictReader(fh):
            r["_nat"] = _f(r.get("natural"))
            r["_p2p"] = _f(r.get("p2p_outturn"))
            r["_out"] = _f(r.get("outturn_pax"))
            r["_cap"] = _f(r.get("capacity"))
            r["_gcd"] = _f(r.get("gcd_km"))
            rows.append(r)

    # gradable routes with the fields we need
    g = [r for r in rows if r["_out"] and r["_out"] >= a.min_outturn
         and r["_nat"] is not None and r["_p2p"] and r["_cap"]]
    if not a.keep_seasonal:
        g = [r for r in g if (r.get("service") or "") not in ("summer", "winter")]
    if a.type:
        g = [r for r in g if (r.get("type") or "") == a.type]

    # induced = the measured market was SMALLER than what the route carried (P2P), so the market did
    # not pre-exist; forecastable = the market was already there.
    ind = [r for r in g if r["_nat"] < r["_p2p"]]
    fore = [r for r in g if r["_nat"] >= r["_p2p"]]
    print(f"\nINDUCED characterisation: {a.csv}")
    print(f"  gradable n={len(g)} (outturn>={a.min_outturn:.0f}"
          + ("" if a.keep_seasonal else ", seasonal excluded")
          + (f", type={a.type}" if a.type else "") + ")")
    print(f"  induced n={len(ind)}   forecastable n={len(fore)}   "
          f"induced share {100*len(ind)/max(len(g),1):.0f}%")
    if not ind:
        print("  no induced routes in this file at these filters.")
        return

    # --- A. cohort by type / haul --------------------------------------------------------------
    def _split(items, keyfn, order=None):
        d = {}
        for r in items:
            d.setdefault(keyfn(r), []).append(r)
        for k in (order or sorted(d, key=lambda k: -len(d[k]))):
            if k in d:
                yield k, d[k]
    print("\n  A. induced cohort")
    print("     by type:")
    for k, xs in _split(ind, lambda r: r.get("type") or "?", ["FSC", "LCC", "ULCC", "Regional"]):
        print(f"       {k:9} n={len(xs)}")
    print("     by haul:")
    for k, xs in _split(ind, lambda r: _haul(r["_gcd"]), HAUL_L):
        print(f"       {k:11} n={len(xs)}")

    # --- B. why the measured-market approach fails ---------------------------------------------
    # the stimulation factor the market x stim path would need = outturn / measured market.
    stim_needed = [r["_out"] / r["_nat"] for r in ind if r["_nat"] and r["_nat"] > 0]
    if stim_needed:
        q1, q3 = _iqr(stim_needed)
        print("\n  B. stimulation the measured-market path would need (outturn / measured market):")
        print(f"       median {_med(stim_needed):.1f}x   IQR {q1:.1f}-{q3:.1f}x   "
              f"(the engine applies ~1.2x, hence the ~0.1 read)")

    # --- C. capacity-anchor test ---------------------------------------------------------------
    # achieved seat factor = onboard outturn / operated annual seats. If induced routes fill to a
    # STABLE load factor, capacity x that factor is a demand floor.
    lf = [(r["_out"] / r["_cap"]) for r in ind if r["_cap"] and r["_cap"] > 0]
    print("\n  C. capacity-anchor test: achieved seat factor (onboard outturn / operated seats)")
    if lf:
        q1, q3 = _iqr(lf)
        print(f"       ALL induced   n={len(lf)}   median {_med(lf):.2f}   IQR {q1:.2f}-{q3:.2f}")
        for k, xs in _split(ind, lambda r: r.get("type") or "?", ["FSC", "LCC", "ULCC", "Regional"]):
            v = [(r["_out"] / r["_cap"]) for r in xs if r["_cap"]]
            if v:
                q1, q3 = _iqr(v)
                print(f"       {k:9}     n={len(v):<4} median {_med(v):.2f}   IQR {q1:.2f}-{q3:.2f}")
        for k, xs in _split(ind, lambda r: _haul(r["_gcd"]), HAUL_L):
            v = [(r["_out"] / r["_cap"]) for r in xs if r["_cap"]]
            if v:
                q1, q3 = _iqr(v)
                print(f"       {k:11}   n={len(v):<4} median {_med(v):.2f}   IQR {q1:.2f}-{q3:.2f}")
        print("     LF by type x haul (LCC/ULCC = the engine table route_forecast.INDUCED_LF):")
        for t in ("LCC", "ULCC"):
            for k in HAUL_L:
                xs = [r for r in ind if (r.get("type") or "") == t and _haul(r["_gcd"]) == k]
                v = [(r["_out"] / r["_cap"]) for r in xs if r["_cap"]]
                if v:
                    q1, q3 = _iqr(v)
                    print(f"       {t:5} {k:11} n={len(v):<4} median {_med(v):.2f}  IQR {q1:.2f}-{q3:.2f}")
        print("       -> a TIGHT IQR here means capacity x load-factor is a good induced demand floor.")

    # --- D. which predicts induced outturn better: capacity or measured market -----------------
    sp_cap = _spearman([(r["_cap"], r["_out"]) for r in ind])
    sp_nat = _spearman([(r["_nat"], r["_out"]) for r in ind])
    print("\n  D. rank correlation with induced outturn (Spearman, higher = better predictor):")
    print(f"       deployed capacity : {sp_cap:+.2f}" if sp_cap is not None else "       capacity: n/a")
    print(f"       measured market   : {sp_nat:+.2f}" if sp_nat is not None else "       market: n/a")

    # --- E. forecast-time detector -------------------------------------------------------------
    # can we flag induced BEFORE outturn? measured-market-to-capacity is a forecast-time observable.
    def _ratio(r):
        return (r["_nat"] / r["_cap"]) if (r["_cap"] and r["_cap"] > 0) else None
    ri = [x for x in (_ratio(r) for r in ind) if x is not None]
    rf = [x for x in (_ratio(r) for r in fore) if x is not None]
    print("\n  E. forecast-time separator: measured market / deployed capacity (known at forecast time)")
    if ri and rf:
        print(f"       induced       median {_med(ri):.2f}   IQR {_iqr(ri)[0]:.2f}-{_iqr(ri)[1]:.2f}")
        print(f"       forecastable  median {_med(rf):.2f}   IQR {_iqr(rf)[0]:.2f}-{_iqr(rf)[1]:.2f}")
        print("       -> a clear gap means a low market/capacity ratio can flag an induced route up front.")

    # --- F. what a capacity floor would deliver ------------------------------------------------
    # provisional floor = capacity x median achieved LF (global), applied to the induced cohort, graded
    # fc/out. This is the ceiling of what a capacity anchor buys before any per-segment refinement.
    if lf:
        floor_lf = _med(lf)
        est = [(r["_cap"] * floor_lf) / r["_out"] for r in ind if r["_out"]]
        w20 = _within(est, 0.8, 1.2)
        w40 = _within(est, 0.6, 1.4)
        print(f"\n  F. provisional capacity floor = seats x {floor_lf:.2f} (median achieved LF), graded fc/out:")
        print(f"       induced n={len(est)}   median {_med(est):.2f}   within +/-20% {w20}/{len(est)}   "
              f"within +/-40% {w40}/{len(est)}")
        print("       (vs the engine's current induced fc/out; compare to the backtest's induced median)")

    # --- G. achieved induced fare (sets the stimulation fare in the economics) ------------------
    # needs the fare columns, present only when the backtest ran with --induced-floor.
    have_fare = any(_f(r.get("outturn_fare")) is not None for r in ind)
    print("\n  G. achieved induced fare (outturn-year P2P, sets the low fare for the economics):")
    if not have_fare:
        print("       run the backtest with --induced-floor to add base_fare / outturn_fare columns.")
    else:
        for t in ("LCC", "ULCC"):
            for k in HAUL_L:
                xs = [r for r in ind if (r.get("type") or "") == t and _haul(r["_gcd"]) == k]
                fares = [_f(r.get("outturn_fare")) for r in xs if _f(r.get("outturn_fare")) is not None]
                if fares:
                    q1, q3 = _iqr(fares)
                    yk = [(_f(r.get("outturn_fare")) / (r["_gcd"] / 1000.0)) for r in xs
                          if _f(r.get("outturn_fare")) is not None and r["_gcd"]]
                    ys = f"  yield ${_med(yk):.0f}/1000km" if yk else ""
                    print(f"       {t:5} {k:11} n={len(fares):<4} median ${_med(fares):.0f}"
                          f"  IQR ${q1:.0f}-${q3:.0f}{ys}")


if __name__ == "__main__":
    main()
