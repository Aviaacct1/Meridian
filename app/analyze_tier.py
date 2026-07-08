#!/usr/bin/env python3
r"""
Avia Solutions - confidence tier (accuracy plan T9): the honest route to a 2/3-within-20% claim.
==================================================================================================
A level trim centres the median but cannot shrink the capture SPREAD (~0.5 in log space), so the blanket
+/-20% hit rate stays ~1/5. The tier stops trying to fix every route and instead FLAGS, at forecast time,
the subset where the forecast is trustworthy - so a pitch can carry a grade ("A: on routes like this, 2/3
of past launches landed within 20%") the airline can rely on. This is the defensible form of John's target.

WHAT IT DOES
  1. Characterises: on the FIT years only, the within-+/-20% hit rate sliced by each forecast-time feature
     (market size, hub, type, region, haul, QSI capture share, nonstop share, connecting fraction, capacity
     bind), so you can see which features separate the accurate forecasts from the rest.
  2. Fits a small, L2-regularised logistic model (hit ~ forecast-time features) on the FIT years, ranks
     every route by predicted hit-probability, and carves A/B/C grades by probability thresholds chosen on
     the fit years to make grade A as close to 2/3 hit-rate as the features allow while keeping useful
     coverage.
  3. Validates: reports each grade's hit rate + coverage on the FIT years AND on each held-out file, and
     the model's discrimination (AUC). The held-out grade A hit-rate is the real headline - if the features
     can't reach 2/3 out of sample, the honest claim is whatever they do reach (still worth having: it tells
     the analyst which forecasts to trust before they pitch).

DISCIPLINE (Fable): fit on 2016-2018 ONLY; the model + thresholds are frozen from the fit years and applied
unchanged to the held-out years. Nothing here is tuned on the held-out data.

    py -3.12 analyze_tier.py E:\Avia\QSI\backtests\decomp_6yr.csv --fit-years 2016,2017,2018 \
        --validate E:\Avia\QSI\backtests\val24_o0.csv --validate E:\Avia\QSI\backtests\val25_o0.csv

Uses numpy only. Columns it will use if present: natural, hub_dest, type, region, gcd_km, propensity,
p2p_share (needs the run's --nonstop-share), feed_beyond/feed_behind, captured_uncapped, d_cap_bound.
"""
import argparse, csv, math

try:
    import numpy as np
except Exception:
    np = None


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _truthy(x):
    return 1.0 if str(x).strip().lower() in ("1", "true", "yes", "y") else 0.0


def load(path, min_outturn):
    """Forecastable, gradeable rows with the features and the hit label."""
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        if p2p is None or p2p < min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p:                 # forecastable only
            continue
        fb = (_f(r.get("feed_beyond")) or 0.0) + (_f(r.get("feed_behind")) or 0.0)
        capu = _f(r.get("captured_uncapped")) or _f(r.get("captured")) or 0.0
        feed_frac = fb / (capu + fb) if (capu + fb) > 0 else 0.0
        rows.append({
            "year": str(r.get("year")), "type": r.get("type") or "?",
            "region": r.get("region") or "OTH",
            "nat": nat, "hub": _truthy(r.get("hub_dest")),
            "gcd": _f(r.get("gcd_km")) or 0.0,
            "prop": _f(r.get("propensity")) or 0.0,
            "p2p_share": _f(r.get("p2p_share")),           # may be None (flag off)
            "feed_frac": feed_frac,
            "cap_bound": _truthy(r.get("d_cap_bound")) if r.get("d_cap_bound") not in (None, "") else None,
            "fw": fw, "hit": 1.0 if 0.8 <= fw <= 1.2 else 0.0,
        })
    return rows


# ---- Part 1: single-feature hit-rate slices (fit years) ------------------------------------------
def _bucketise(rows, key, edges, labels):
    out = {lab: [] for lab in labels}
    for r in rows:
        v = r[key]
        if v is None:
            continue
        idx = len(edges)
        for i, e in enumerate(edges):
            if v < e:
                idx = i; break
        out[labels[idx]].append(r)
    return out


def _slice(rows, title, groups):
    print(f"\n  {title}")
    print(f"    {'bucket':>16}  {'n':>5}  {'hit +/-20%':>10}  {'median fc/p2p':>13}")
    for lab, rs in groups.items():
        if not rs:
            continue
        hr = sum(x["hit"] for x in rs) / len(rs)
        print(f"    {lab:>16}  {len(rs):>5}  {100*hr:>8.0f}%  {_median([x['fw'] for x in rs]):>13.2f}")


def characterise(fit):
    n = len(fit); base = sum(x["hit"] for x in fit) / n
    print(f"\nFORECAST-TIME FEATURE SLICES (fit years, n={n}, baseline hit {100*base:.0f}%)")
    _slice(fit, "by market size", _bucketise(fit, "nat", [15000, 50000, 150000],
           ["<15k", "15-50k", "50-150k", ">150k"]))
    _slice(fit, "by hub destination", {"hub": [x for x in fit if x["hub"]],
           "non-hub": [x for x in fit if not x["hub"]]})
    _slice(fit, "by airline type", {t: [x for x in fit if x["type"] == t]
           for t in ("FSC", "LCC", "ULCC", "Regional")})
    _slice(fit, "by region", {rg: [x for x in fit if x["region"] == rg]
           for rg in sorted({x["region"] for x in fit})})
    _slice(fit, "by haul (km)", _bucketise(fit, "gcd", [800, 2500, 6000],
           ["<800", "800-2500", "2500-6000", ">6000"]))
    _slice(fit, "by QSI capture share", _bucketise(fit, "prop", [0.15, 0.35, 0.60],
           ["<0.15", "0.15-0.35", "0.35-0.60", ">0.60"]))
    _slice(fit, "by connecting fraction", _bucketise(fit, "feed_frac", [0.1, 0.3, 0.5],
           ["<10%", "10-30%", "30-50%", ">50%"]))
    if any(x["p2p_share"] is not None for x in fit):
        _slice(fit, "by nonstop share", _bucketise(fit, "p2p_share", [0.2, 0.5, 0.8],
               ["<20%", "20-50%", "50-80%", ">80%"]))
    if any(x["cap_bound"] is not None for x in fit):
        _slice(fit, "by capacity bind", {"capped": [x for x in fit if x["cap_bound"] == 1.0],
               "uncapped": [x for x in fit if x["cap_bound"] == 0.0]})


# ---- Part 2: logistic tier -----------------------------------------------------------------------
FEATURES = ["log_nat", "hub", "log_gcd", "prop", "feed_frac", "is_FSC", "is_LCC", "is_ULCC"]


def _featurise(rows, use_nonstop, use_cap):
    names = list(FEATURES)
    if use_cap:
        names = names + ["cap_bound"]        # capacity cap binds = a mechanistic accuracy signal
    if use_nonstop:
        names = names + ["p2p_share"]
    X = []
    for r in rows:
        row = [math.log10(max(r["nat"], 1.0)), r["hub"], math.log10(max(r["gcd"], 1.0)),
               r["prop"], r["feed_frac"],
               1.0 if r["type"] == "FSC" else 0.0, 1.0 if r["type"] == "LCC" else 0.0,
               1.0 if r["type"] == "ULCC" else 0.0]
        if use_cap:
            row.append(r["cap_bound"] if r["cap_bound"] is not None else 0.0)
        if use_nonstop:
            row.append(r["p2p_share"] if r["p2p_share"] is not None else 0.5)
        X.append(row)
    return np.array(X, dtype=float), names


def _fit_logit(X, y, l2=1.0, iters=500, lr=0.3):
    """Standardise, then fit L2 logistic by full-batch gradient descent (no sklearn dependency)."""
    mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    n, d = Xs.shape
    w = np.zeros(d); b = 0.0
    for _ in range(iters):
        z = Xs @ w + b
        p = 1.0 / (1.0 + np.exp(-z))
        gw = Xs.T @ (p - y) / n + l2 * w / n
        gb = float((p - y).mean())
        w -= lr * gw; b -= lr * gb
    return {"w": w, "b": b, "mu": mu, "sd": sd}


def _predict(model, X):
    Xs = (X - model["mu"]) / model["sd"]
    return 1.0 / (1.0 + np.exp(-(Xs @ model["w"] + model["b"])))


def _auc(p, y):
    order = np.argsort(p); yy = y[order]
    pos = yy.sum(); neg = len(yy) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    ranks = np.argsort(np.argsort(p)) + 1
    return float((ranks[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def _grade_by_thresholds(p, hi, lo):
    return np.where(p >= hi, "A", np.where(p >= lo, "B", "C"))


def _report_grades(name, grades, y):
    print(f"\n  {name}: n={len(y)}")
    print(f"    {'grade':>6}  {'n':>5}  {'coverage':>8}  {'hit +/-20%':>10}")
    for g in ("A", "B", "C"):
        m = grades == g
        k = int(m.sum())
        if k == 0:
            print(f"    {g:>6}  {0:>5}  {'0%':>8}  {'-':>10}"); continue
        hr = float(y[m].mean())
        print(f"    {g:>6}  {k:>5}  {100*k/len(y):>6.0f}%  {100*hr:>8.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--validate", action="append", default=[], help="held-out CSV (repeatable)")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--l2", type=float, default=1.0)
    ap.add_argument("--target", type=float, default=0.667, help="grade-A hit-rate target")
    ap.add_argument("--min-coverage", type=float, default=0.15, help="min share of routes in grade A")
    a = ap.parse_args()
    if np is None:
        print("numpy required (py -3.12 -m pip install numpy)."); return
    fit_years = set(a.fit_years.split(","))
    allrows = load(a.csv, a.min_outturn)
    fit = [r for r in allrows if r["year"] in fit_years]
    if not fit:
        print("No forecastable fit-year rows."); return

    characterise(fit)

    use_nonstop = any(x["p2p_share"] is not None for x in fit)
    use_cap = any(x["cap_bound"] is not None for x in fit)
    Xf, names = _featurise(fit, use_nonstop, use_cap)
    yf = np.array([r["hit"] for r in fit], dtype=float)
    model = _fit_logit(Xf, yf, l2=a.l2)
    pf = _predict(model, Xf)
    print(f"\nTIER MODEL (L2 logistic, features: {', '.join(names)})")
    print(f"  fit AUC {_auc(pf, yf):.3f}   baseline hit {100*yf.mean():.0f}%")
    coef = sorted(zip(names, model["w"]), key=lambda kv: -abs(kv[1]))
    print("  standardised weights (|larger| = stronger driver of confidence):")
    for nm, wv in coef:
        print(f"    {nm:>12}  {wv:+.2f}")

    # choose grade-A threshold on FIT: highest prob cut whose fit hit-rate >= target, subject to coverage;
    # if the target is unreachable at min coverage, take the cut that MAXIMISES fit hit-rate at min coverage.
    order = np.argsort(-pf)
    ys = yf[order]; ps = pf[order]
    nfit = len(ys); min_k = max(10, int(a.min_coverage * nfit))
    best_hi = None
    # walk down the ranking; at each k>=min_k, cumulative hit-rate of the top-k
    cum = np.cumsum(ys)
    reach = None; best_alt = (-1.0, None)
    for k in range(min_k, nfit + 1):
        hr = cum[k - 1] / k
        if hr >= a.target and reach is None:
            reach = ps[k - 1]                     # largest coverage still >= target
        if hr > best_alt[0]:
            best_alt = (hr, ps[k - 1])
    hi = reach if reach is not None else best_alt[1]
    # grade B floor: probability above the fit baseline odds (better-than-average routes)
    lo = float(np.quantile(pf, 0.5))
    if lo >= hi:
        lo = hi * 0.9
    print(f"\n  grade cuts (fit): A if p>={hi:.3f}, B if p>={lo:.3f}, else C")
    if reach is None:
        print(f"  NOTE: 2/3 target NOT reachable at {int(100*a.min_coverage)}% coverage on the fit years; "
              f"grade A set to the highest-hit-rate cut ({100*best_alt[0]:.0f}% fit hit).")

    _report_grades("FIT " + a.fit_years, _grade_by_thresholds(pf, hi, lo), yf)
    for vp in a.validate:
        vr = load(vp, a.min_outturn)
        if not vr:
            print(f"\n  {vp}: no forecastable rows"); continue
        Xv, _ = _featurise(vr, use_nonstop, use_cap)
        yv = np.array([r["hit"] for r in vr], dtype=float)
        pv = _predict(model, Xv)
        print(f"\n  held-out {vp.split(chr(92))[-1]}: AUC {_auc(pv, yv):.3f}")
        _report_grades(vp.split(chr(92))[-1], _grade_by_thresholds(pv, hi, lo), yv)
    print("\n  The held-out grade-A hit rate is the headline. If it holds near the fit A hit rate across "
          "both years, the tier generalises and the claim is real.")


if __name__ == "__main__":
    main()
