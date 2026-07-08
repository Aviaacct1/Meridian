#!/usr/bin/env python3
r"""
Avia Solutions - T4 error-variance attribution (Fable accuracy plan).
==================================================================================================
Reads a backtest CSV produced with --decompose and splits each forecastable route's P2P log-error
into two MEASURABLE legs, then attributes the variance:

  captured / p2p_outturn  =  L_market  x  L_capture

  L_market  = (mkt_asif x growth_applied) / mkt_outturn      how wrong the projected outturn-year market
                                                             was (measurement + growth vs realised)
  L_capture = (captured x mkt_outturn) / (mkt_asif x growth_applied x p2p_outturn)
                                                             how wrong the capture intensity was
                                                             (QSI share x dshare x stim x coverage vs achieved)

Variance attribution is the linear covariance split: Var(logT) = Cov(logT, logA) + Cov(logT, logB), so
each leg's share = Cov(logT, leg)/Var(logT), and they sum to 1. Reported overall and by segment, so week
2 targets the leg that actually carries the variance, not the one intuition suggests.

    py -3.12 analyze_decomp.py E:\Avia\QSI\backtests\decomp.csv
    py -3.12 analyze_decomp.py <csv> --fit-years 2016,2017,2018   (report the fit split separately)

Forecastable only (market pre-existed); reads the CSV only.
"""
import argparse, csv, math
from collections import defaultdict


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _var(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def _cov(xs, ys):
    if len(xs) < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _legs(rows):
    """Per-route log legs on the forecastable set with complete decomposition fields."""
    out = []
    for r in rows:
        ma = _f(r.get("d_mkt_asif")); mo = _f(r.get("d_mkt_outturn")); g = _f(r.get("d_growth_applied"))
        cap = _f(r.get("d_captured")); p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural"))
        if None in (ma, mo, g, cap, p2p) or min(ma, mo, g, cap, p2p) <= 0:
            continue
        if nat is None or nat < p2p:      # forecastable only (market pre-existed)
            continue
        Mpred = ma * g
        Lmkt = Mpred / mo
        Lcap = (cap * mo) / (Mpred * p2p)
        T = cap / p2p                      # = fc/p2p on the P2P demand
        out.append({"row": r, "T": math.log(T), "mkt": math.log(Lmkt), "cap": math.log(Lcap),
                    "rT": T, "rmkt": Lmkt, "rcap": Lcap})
    return out


def _attrib(name, legs):
    if len(legs) < 20:
        print(f"  {name}: n={len(legs)} (too few)")
        return
    lt = [x["T"] for x in legs]; la = [x["mkt"] for x in legs]; lb = [x["cap"] for x in legs]
    vt = _var(lt)
    sm = _cov(lt, la) / vt if vt else 0.0
    sc = _cov(lt, lb) / vt if vt else 0.0
    w20 = sum(1 for x in legs if 0.8 <= x["rT"] <= 1.2)
    print(f"  {name}: n={len(legs)}  sigma_log(total) {math.sqrt(vt):.2f}  within +/-20% {100*w20//len(legs)}%")
    print(f"      variance share:  MARKET/GROWTH {100*sm:.0f}%   CAPTURE {100*sc:.0f}%")
    print(f"      leg median (bias): market x{_median([x['rmkt'] for x in legs]):.2f}  "
          f"capture x{_median([x['rcap'] for x in legs]):.2f}   "
          f"leg sigma_log: market {math.sqrt(_var(la)):.2f}  capture {math.sqrt(_var(lb)):.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default=None, help="comma years to report separately as the fit split")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, newline="")))
    legs = _legs(rows)
    if not legs:
        print("No rows with complete --decompose fields. Was the CSV produced with --decompose?")
        return
    print(f"\nERROR-VARIANCE ATTRIBUTION: {a.csv}   (forecastable n={len(legs)})")
    _attrib("ALL", legs)

    def _seg(title, keyfn, order=None):
        print(f"\n  by {title}:")
        d = defaultdict(list)
        for x in legs:
            d[keyfn(x["row"])].append(x)
        for k in (order or sorted(d, key=lambda k: -len(d[k]))):
            if k in d:
                _attrib(f"    {k}", d[k])

    def _mktbkt(r):
        v = _f(r.get("natural")) or 0
        return "<15k" if v < 15000 else "15-50k" if v < 50000 else "50-150k" if v < 150000 else ">150k"

    _seg("carrier type", lambda r: r.get("type") or "?", ["FSC", "LCC", "ULCC", "Regional"])
    _seg("market size (natural)", _mktbkt, ["<15k", "15-50k", "50-150k", ">150k"])
    _seg("hub", lambda r: "hub" if str(r.get("hub_dest")).lower() == "true" else "non-hub", ["hub", "non-hub"])
    _seg("region", lambda r: r.get("region") or "?")

    # --- AIRPORT-LEVEL CAPTURE EFFECT (John's hypothesis): does an origin airport consistently capture
    #     more/less than the general model, so a factor learned from its past routes cuts the capture
    #     error? Between-airport variance = the correctable part; leave-one-out = the honest gain.
    byap = defaultdict(list)
    for x in legs:
        byap[(x["row"].get("dep") or "?")].append(x["cap"])   # log(L_capture) by origin airport
    gmean = _mean([x["cap"] for x in legs])
    K = 3.0  # shrinkage toward the global mean (partial pooling) for thin-history airports
    print("\n  AIRPORT-LEVEL CAPTURE EFFECT (leave-one-out is the honest gain; more launches = more reliable):")
    print("      min launches | airports | routes | raw sigma | LOO sigma | % variance removed OOS")
    for thr in (2, 3, 4, 6):
        multi = {k: v for k, v in byap.items() if len(v) >= thr}
        if not multi:
            continue
        allmulti = [x for v in multi.values() for x in v]
        v_raw = _var(allmulti)
        loo = []
        for v in multi.values():
            for i in range(len(v)):
                others = [v[j] for j in range(len(v)) if j != i]
                pred = (sum(others) + K * gmean) / (len(others) + K)
                loo.append(v[i] - pred)
        v_loo = _var(loo)
        red = 100 * (1 - v_loo / v_raw) if v_raw else 0
        print(f"      >={thr:>2}          | {len(multi):>7} | {len(allmulti):>6} | "
              f"{math.sqrt(v_raw):>8.2f} | {math.sqrt(v_loo):>8.2f} | {red:>5.0f}%")
    print("      -> if the % rises with launch count, the factor is strong for airports with real history "
          "(the ones that pitch), even if the thin-history average is modest.")

    if a.fit_years:
        ys = set(a.fit_years.split(","))
        fit = [x for x in legs if str(x["row"].get("year")) in ys]
        hold = [x for x in legs if str(x["row"].get("year")) not in ys]
        print("\n  FIT vs HELD-OUT split (never tune on held-out):")
        _attrib("    fit-years", fit)
        _attrib("    held-out", hold)


if __name__ == "__main__":
    main()
