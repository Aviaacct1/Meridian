#!/usr/bin/env python3
r"""
Avia Solutions - fare-gap diagnostic (John's thesis: the demand engine looks better once you account for fare).
==================================================================================================
The engine forecasts P2P demand at the prevailing MARKET fare (base_fare). If the airline then prices ABOVE
that, demand is suppressed and the outturn comes in below our number - which reads as an over-forecast even
though the demand logic was right FOR THE FARE WE ASSUMED. This tests that directly, on the realised fare we
already log (base_fare = pre-launch market fare; outturn_fare = what the airline actually charged). No OAG
schedule data needed.

THREE reads:
  1. CONCORDANCE (John's exact test): do over-forecasts coincide with the airline pricing ABOVE our fare, and
     under-forecasts with pricing BELOW? fare ratio fr = outturn_fare/base_fare; error err = fc/actual (fc_over_p2p).
     Vindicating pattern: fr>1 with err>1, and fr<1 with err<1 (a positive fr-err relationship).
  2. ELASTICITY: regress ln(err) on ln(fr) (fit years only). Slope b>0 = the fare gap explains the error in the
     expected direction; b is the implied demand response to a fare premium.
  3. PAYOFF: adjust the error for the fare gap (err_adj = err / fr**b) and report within-+/-20% and median
     |log err| BEFORE vs AFTER, on fit AND held-out years - "given the fare actually charged, the engine would
     have been within +/-20% on X% of launches" (a MODEL-QUALITY claim, not forward accuracy - forward you
     cannot know the fare, which is why the live forecast sits high).

HONEST CAVEAT printed with the result: airlines also set fare in RESPONSE to demand (endogeneity), so the
slope is an UPPER bound on the true causal fare effect and the adjusted accuracy is an illustrative ceiling,
not a shippable forward number. A strong, correctly-signed result still supports building a fare-conditioned
test (and the demand-side of the fare slider).

    py -3.12 analyze_fare_elasticity.py E:\Avia\QSI\backtests\bt_6yr_induced.csv --fit-years 2016,2017,2018

Needs an --induced-floor run (writes base_fare + outturn_fare). numpy only.
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


def load(path, min_outturn):
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); err = _f(r.get("fc_over_p2p"))
        bf = _f(r.get("base_fare")); of = _f(r.get("outturn_fare"))
        if p2p is None or p2p < min_outturn or err is None or err <= 0:
            continue
        if nat is None or nat < p2p:                       # forecastable only
            continue
        if bf is None or of is None or bf <= 0 or of <= 0:  # need both fares
            continue
        rows.append({"year": str(r.get("year")), "err": err, "fr": of / bf,
                     "type": r.get("type") or "?"})
    return rows


def _w20(errs):
    return sum(1 for e in errs if 0.8 <= e <= 1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    a = ap.parse_args()
    if np is None:
        print("numpy required (py -3.12 -m pip install numpy)."); return
    fit_years = set(a.fit_years.split(","))
    rows = load(a.csv, a.min_outturn)
    if len(rows) < 20:
        print(f"Only {len(rows)} forecastable rows with both fares. Need an --induced-floor run "
              f"(base_fare + outturn_fare columns)."); return

    le = np.array([math.log(r["err"]) for r in rows])
    lf = np.array([math.log(r["fr"]) for r in rows])
    corr = float(np.corrcoef(lf, le)[0, 1])

    # 1. CONCORDANCE (John's directional test)
    over = [r for r in rows if r["err"] > 1.2]
    under = [r for r in rows if r["err"] < 0.8]
    conc = sum(1 for r in rows if (r["err"] > 1.0) == (r["fr"] > 1.0))
    print(f"\nFARE-GAP DIAGNOSTIC: {a.csv}   (n={len(rows)} forecastable with both fares)")
    print(f"\n  1. CONCORDANCE (does the error move with the fare gap?)")
    print(f"     corr[ ln(fare ratio) , ln(fc/actual) ] = {corr:+.2f}   (positive = fare gap explains the error)")
    if over:
        print(f"     of {len(over)} OVER-forecasts (fc/actual>1.2): {100*sum(1 for r in over if r['fr']>1)//len(over)}% had the airline pricing ABOVE our fare")
    if under:
        print(f"     of {len(under)} UNDER-forecasts (fc/actual<0.8): {100*sum(1 for r in under if r['fr']<1)//len(under)}% had the airline pricing BELOW our fare")
    print(f"     overall concordant (error and fare gap same direction): {100*conc//len(rows)}%")

    # 2. ELASTICITY on fit years
    fit = [r for r in rows if r["year"] in fit_years]
    if len(fit) < 15:
        print("\n  (too few fit-year rows to fit the slope)"); return
    lef = np.array([math.log(r["err"]) for r in fit]); lff = np.array([math.log(r["fr"]) for r in fit])
    b = float(np.polyfit(lff, lef, 1)[0])          # slope of ln(err) on ln(fr)
    print(f"\n  2. ELASTICITY (fit years {sorted(fit_years)}, n={len(fit)}): slope ln(err)~ln(fr) = {b:+.2f}")
    print(f"     (a fare {'{:.0f}'.format(100)}% above assumption moves our error by ~{b:+.2f} in log terms)")

    # 3. PAYOFF: adjust error for the fare gap, re-grade fit + held-out
    def _grade(name, rs):
        if len(rs) < 10:
            print(f"     {name}: n={len(rs)} (too few)"); return
        raw = [r["err"] for r in rs]
        adj = [r["err"] / (r["fr"] ** b) for r in rs]
        rle = [abs(math.log(x)) for x in raw]; ale = [abs(math.log(x)) for x in adj]
        print(f"     {name}: n={len(rs):>4}   +/-20% {100*_w20(raw)//len(rs):>3}% -> {100*_w20(adj)//len(rs):>3}%   "
              f"median|log err| {_median(rle):.3f} -> {_median(ale):.3f}   median fc/actual {_median(raw):.2f} -> {_median(adj):.2f}")
    print(f"\n  3. PAYOFF (error adjusted for the realised fare gap; HINDSIGHT = model-quality, not forward):")
    _grade("fit  " + ",".join(sorted(fit_years)), fit)
    for y in sorted({r["year"] for r in rows} - fit_years):
        _grade("held " + y, [r for r in rows if r["year"] == y])

    print(f"\n  READING IT: the main simultaneity concern (airlines pricing in RESPONSE to demand - raising fares\n"
          f"  in strength, cutting to rescue weakness) produces DISCORDANCE, so it biases this signal DOWNWARD.\n"
          f"  A strong positive concordance/slope is therefore conservative evidence FOR a real fare effect, not\n"
          f"  inflated by reverse causation. Residual confounds that could add spurious concordance: common cost/\n"
          f"  macro/seasonal shocks (fuel up -> fares up + demand soft). And it stays HINDSIGHT (uses the realised\n"
          f"  fare) = a model-quality claim, not forward accuracy; forward you cannot know the fare.")


if __name__ == "__main__":
    main()
