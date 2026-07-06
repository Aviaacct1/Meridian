#!/usr/bin/env python3
"""
Avia Solutions - work BACKWARDS from outturn to the minimal correction table.
=============================================================================
John's idea: the analyst spends days researching one route to land a manual adjustment. Do that for
EVERY airport at once. If all routes at an airport read the same way, that's a catchment error we can
correct once at the airport, not patch route by route. This reads the full back-test result file and
asks, in order of parsimony:

  1. Where does the forecast error actually live? Variance of the error explained by ORIGIN AIRPORT
     vs country vs region vs carrier type vs haul vs market size - so we know whether it is an airport
     (catchment) thing, an Asia-under / Europe-over thing, or an FSC-over / ULCC-under thing.
  2. The MINIMAL model: greedily add the one dimension that most tightens the fit, stop when it stops
     helping - the fewest variables that pull the most forecasts onto actual.
  3. The ADJUSTMENT TABLE at airport level (and country, for thin airports): one factor per airport,
     plus whether that single factor is enough or the airport still splits by type/haul.
  4. Does it GENERALISE across time? Fit the factors on even launch years, test on odd - if a factor
     only works on the years it was fit to, it is noise, not a catchment truth.

Nothing is baked back into the engine here - this CALCULATES the variables that would. Ratio used is
the demand ratio captured/outturn (capacity-limited routes excluded, since there the metal, not the
estimate, set the number). A group factor = 1 / median(ratio): <1 trims an over-read, >1 lifts an under.

    py -3.12 calibration_fit.py                     # reads app/backtest_results.csv
    py -3.12 calibration_fit.py --csv path\to.csv --target 1.05 --min-n 4
"""
import argparse, csv, math, os
from collections import defaultdict

def med(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2) if xs else 0.0
def logvar(rs):
    ls = [math.log(r) for r in rs if r > 0]
    if len(ls) < 2: return 0.0
    m = sum(ls)/len(ls); return sum((x-m)**2 for x in ls)/len(ls)
def within(rs, lo=0.8, hi=1.2):
    return (sum(1 for r in rs if lo <= r <= hi)/len(rs)) if rs else 0.0
def haul_band(g):
    g = g or 0
    return "<800km" if g < 800 else "800-2500" if g < 2500 else "2500-6000" if g < 6000 else ">6000km"
def mkt_band(p):
    p = p or 0
    return "<15k" if p < 15000 else "15-50k" if p < 50000 else "50-150k" if p < 150000 else ">150k"


def load(path, min_out, keep_capbound):
    rows = []
    with open(path, newline="") as fh:
        for d in csv.DictReader(fh):
            try:
                cap = float(d["captured_uncapped"]); p2p = float(d["p2p_outturn"])
                capacity = float(d.get("capacity") or 0)
            except Exception:
                continue
            if cap <= 0 or p2p < min_out:
                continue
            r = cap / p2p
            # keep factor-correctable routes only: below ~0.1 the measured market has essentially
            # collapsed (pure stimulation / deep coverage hole) - no static per-airport factor fixes
            # that, it is the judgement layer, and it just drags the medians and hides the signal.
            if r < 0.1 or r > 10:
                continue
            capbound = capacity > 0 and p2p > 0.85 * capacity
            if capbound and not keep_capbound:
                continue
            dep = (d.get("dep") or d.get("route", "-").split("-")[0]).strip()
            arr = (d.get("arr") or d.get("route", "-x-").split("-")[-1]).strip()
            rows.append(dict(dep=dep, arr=arr, country=(d.get("dep_country") or "?").strip(),
                             arr_country=(d.get("arr_country") or "?").strip(),
                             region=(d.get("region") or "?").strip(), typ=(d.get("type") or "?").strip(),
                             year=int(float(d.get("year") or 0)),
                             haul=haul_band(float(d.get("gcd_km") or 0)),
                             mkt=mkt_band(p2p), ratio=r))
    return rows


def twoway_fit(rows, iters=25, shrink=4.0):
    """ROBUST two-way (gravity) fit by median polish: ln(outturn/captured) = g + o[origin] + d[dest].
    Demand flows both ways, so each airport gets an OUTBOUND factor (as origin) and an INBOUND factor
    (as destination); a route's correction = o[dep] x d[arr]. Alternating MEDIANS (not means) so one
    odd route can't drag an airport's factor; small-n airports shrunk toward neutral. Returns g (global
    median), o{}, d{}, variance-explained, corrected ratios."""
    lnF = [math.log(1.0 / r["ratio"]) for r in rows]                    # ln of the ideal correction
    g = med(lnF)
    deps, arrs = defaultdict(list), defaultdict(list)
    for i, r in enumerate(rows):
        deps[r["dep"]].append(i); arrs[r["arr"]].append(i)
    o = {k: 0.0 for k in deps}; d = {k: 0.0 for k in arrs}
    for _ in range(iters):
        for k, idx in deps.items():
            raw = med([lnF[i] - g - d[rows[i]["arr"]] for i in idx])
            o[k] = raw * len(idx) / (len(idx) + shrink)
        for k, idx in arrs.items():
            raw = med([lnF[i] - g - o[rows[i]["dep"]] for i in idx])
            d[k] = raw * len(idx) / (len(idx) + shrink)
    resid = [lnF[i] - g - o[rows[i]["dep"]] - d[rows[i]["arr"]] for i in range(len(rows))]
    tot = logvar([r["ratio"] for r in rows])
    mr = med(resid); rv = sum((x - mr) ** 2 for x in resid) / len(resid)
    ve = (1 - rv / tot) if tot > 0 else 0.0
    corrected = [rows[i]["ratio"] * math.exp(g + o[rows[i]["dep"]] + d[rows[i]["arr"]]) for i in range(len(rows))]
    return g, o, d, ve, corrected


def temporal_stability(rows, min_n=4, tol=0.22):
    """Fit the two-way factors on the EARLY half of years and again on the LATE half; an airport's
    outbound factor is TRUSTWORTHY only where the two agree (|ln diff| < tol ~ within 25%). Returns the
    fraction of airports that are stable and a dict {airport: stable_bool} for outbound and inbound."""
    yrs = sorted(set(r["year"] for r in rows))
    if len(yrs) < 4:
        return None
    mid = yrs[len(yrs) // 2]
    early = [r for r in rows if r["year"] < mid]; late = [r for r in rows if r["year"] >= mid]
    if len(early) < 50 or len(late) < 50:
        return None
    _, oe, de, _, _ = twoway_fit(early); _, ol, dl, _, _ = twoway_fit(late)
    def stab(a, b):
        common = [k for k in a if k in b]
        flags = {k: abs(a[k] - b[k]) < tol for k in common}
        frac = (sum(flags.values()) / len(flags)) if flags else 0.0
        return frac, flags
    fo, flo = stab(oe, ol); fi, fli = stab(de, dl)
    return dict(out_frac=fo, in_frac=fi, out_flags=flo, in_flags=fli)


def explain(rows, keyfn, min_n):
    groups = defaultdict(list)
    for r in rows:
        groups[keyfn(r)].append(r["ratio"])
    gmed = {k: med(v) for k, v in groups.items() if len(v) >= min_n}
    tot = logvar([r["ratio"] for r in rows])
    resid = [r["ratio"] / gmed[keyfn(r)] if keyfn(r) in gmed else r["ratio"] for r in rows]
    ve = (1 - logvar(resid)/tot) if tot > 0 else 0.0
    return ve, len(gmed), within(resid), gmed, resid


def main():
    ap = argparse.ArgumentParser()
    HERE = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--csv", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--min-out", type=int, default=10000)
    ap.add_argument("--min-n", type=int, default=4, help="min routes for a group to earn its own factor")
    ap.add_argument("--target", type=float, default=1.0, help="calibration target (1.05 = lean slightly over)")
    ap.add_argument("--keep-capbound", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        print("no csv at", a.csv); return
    rows = load(a.csv, a.min_out, a.keep_capbound)
    if not rows:
        print("no usable rows"); return
    allr = [r["ratio"] for r in rows]
    print(f"{len(rows)} routes (demand ratio captured/outturn; capacity-limited excluded unless --keep-capbound)")
    print(f"OVERALL: median {med(allr):.2f}  within +/-20% {within(allr):.0%}  within +/-10% {within(allr,0.9,1.1):.0%}\n")

    dims = [("origin AIRPORT", lambda r: r["dep"]), ("origin COUNTRY", lambda r: r["country"]),
            ("region", lambda r: r["region"]), ("carrier TYPE", lambda r: r["typ"]),
            ("haul band", lambda r: r["haul"]), ("market band", lambda r: r["mkt"])]
    print("WHERE THE ERROR LIVES  (variance of the error explained by each dimension alone):")
    print(f"  {'dimension':16} {'var explained':>13} {'#factors':>9} {'within20 after':>15}")
    for name, fn in dims:
        ve, ng, wi, _, _ = explain(rows, fn, a.min_n)
        print(f"  {name:16} {ve:>12.0%} {ng:>9} {wi:>14.0%}")

    # over/under by region and type and top countries (John's question, plainly)
    def group_meds(fn, min_n, top=12):
        g = defaultdict(list)
        for r in rows: g[fn(r)].append(r["ratio"])
        items = [(k, med(v), len(v)) for k, v in g.items() if len(v) >= min_n]
        return sorted(items, key=lambda x: -x[2])[:top]
    print("\nBIAS BY REGION (median ratio; <1 under-forecast, >1 over-forecast):")
    for k, m, n in group_meds(lambda r: r["region"], a.min_n): print(f"   {k:8} n={n:<4} {m:.2f}")
    print("BIAS BY CARRIER TYPE:")
    for k, m, n in group_meds(lambda r: r["typ"], a.min_n): print(f"   {k:8} n={n:<4} {m:.2f}")
    print("BIAS BY COUNTRY (top by route count):")
    for k, m, n in group_meds(lambda r: r["country"], a.min_n): print(f"   {k:8} n={n:<4} {m:.2f}")

    # greedy minimal model: keep adding the dimension that most tightens the residual
    print("\nMINIMAL MODEL (greedy - fewest layers that pull the most forecasts in):")
    work = [dict(r) for r in rows]
    chosen = []
    base_within = within([r["ratio"] for r in work])
    for step in range(3):
        best = None
        for name, fn in dims:
            if name in [c[0] for c in chosen]:
                continue
            ve, ng, wi, gmed, resid = explain(work, fn, a.min_n)
            if best is None or wi > best[2]:
                best = (name, fn, wi, gmed)
        if best is None or best[2] <= base_within + 0.005:
            break
        name, fn, wi, gmed = best
        # apply this layer's factors to the working ratios
        for r in work:
            k = fn(r)
            if k in gmed and gmed[k] > 0:
                r["ratio"] = r["ratio"] / gmed[k]
        chosen.append((name, len(gmed)))
        print(f"  + {name:16} ({len(gmed)} factors) -> within +/-20% now {wi:.0%}")
        base_within = wi
    print(f"  layers: {', '.join(c[0] for c in chosen) or 'none improved'}")

    # TWO-WAY GRAVITY FIT: each airport an OUTBOUND (origin) and an INBOUND (dest) factor; route = both
    ve_o, _, wi_o, _, _ = explain(rows, lambda r: r["dep"], a.min_n)
    g2, ofac, dfac, ve2, corrected = twoway_fit(rows)
    print("\nTWO-WAY GRAVITY FIT  (demand flows both ways; airport gets an outbound AND an inbound factor):")
    print(f"  origin factor only    : variance explained {ve_o:>4.0%}   within +/-20% {wi_o:>4.0%}")
    print(f"  origin + destination  : variance explained {ve2:>4.0%}   within +/-20% {within(corrected):>4.0%}")
    print(f"  -> {'the DESTINATION direction adds real signal - the bidirectional model wins' if ve2 > ve_o + 0.05 else 'origin alone captures most of it'}")
    outdir = os.path.dirname(a.csv)
    depn, arrn = defaultdict(int), defaultdict(int)
    for r in rows:
        depn[r["dep"]] += 1; arrn[r["arr"]] += 1
    stab = temporal_stability(rows, a.min_n)
    if stab:
        print(f"  STABLE OVER TIME (early-half vs late-half factors agree within ~25%): "
              f"outbound {stab['out_frac']:.0%} of airports, inbound {stab['in_frac']:.0%}. "
              f"Trust these as catchment truths; treat the rest as route noise.")
    of_flags = stab["out_flags"] if stab else {}
    if_flags = stab["in_flags"] if stab else {}
    def wfac(fname, fac, cnt, flags):
        p = os.path.join(outdir, fname)
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["airport", f"factor(target{a.target})", "n_routes", "stable_over_time"])
            for k in sorted(fac, key=lambda x: -cnt[x]):
                st = flags.get(k)
                w.writerow([k, round(a.target * math.exp(fac[k]), 3), cnt[k],
                            "" if st is None else ("yes" if st else "no")])
        return p
    print(f"  wrote {wfac('adjust_outbound.csv', ofac, depn, of_flags)}")
    print(f"  wrote {wfac('adjust_inbound.csv', dfac, arrn, if_flags)}")
    ev = [r for r in rows if r["year"] % 2 == 0]; od = [r for r in rows if r["year"] % 2 == 1]
    if ev and od and len(ev) > 50:
        gg, oo, dd, _, _ = twoway_fit(ev)
        before = within([r["ratio"] for r in od])
        after = within([r["ratio"] * math.exp(gg + oo.get(r["dep"], 0.0) + dd.get(r["arr"], 0.0)) for r in od])
        print(f"  cross-time (fit even years, test odd): odd within +/-20% {before:.0%} -> {after:.0%} "
              f"({'generalises' if after > before + 0.03 else 'weak - watch for over-fit'})")

    # WHICH GRANULARITY GENERALISES: the honesty check - fit a median factor per airport / origin-
    # country / country-pair / region / haul on EVEN years, apply to ODD. The coarsest layer that
    # still lifts the held-out hit rate is the real, repeatable correction; finer layers that don't
    # lift it are over-fit noise. This decides how many variables the correction table should have.
    if ev and od:
        base = within([r["ratio"] for r in od])
        print("\nWHICH GRANULARITY GENERALISES  (fit EVEN years, test ODD - the honesty check):")
        print(f"  {'no correction':24} within +/-20% {base:.0%}")
        for name, fn in [("per-AIRPORT", lambda r: r["dep"]),
                         ("per-ORIGIN-COUNTRY", lambda r: r["country"]),
                         ("per-COUNTRY-PAIR", lambda r: r["country"] + ">" + r["arr_country"]),
                         ("per-REGION", lambda r: r["region"]),
                         ("per-HAUL", lambda r: r["haul"])]:
            gm = defaultdict(list)
            for r in ev:
                gm[fn(r)].append(r["ratio"])
            fac = {k: med(v) for k, v in gm.items() if len(v) >= a.min_n}
            aft = within([r["ratio"]/fac[fn(r)] if fn(r) in fac else r["ratio"] for r in od])
            print(f"  {name:24} within +/-20% {aft:.0%}   ({len(fac)} factors; "
                  f"{'HOLDS' if aft > base + 0.02 else 'no real gain'})")

    # AIRPORT adjustment table + is one factor enough per airport?
    byap = defaultdict(list)
    for r in rows: byap[r["dep"]].append(r)
    aps = [(d, rs) for d, rs in byap.items() if len(rs) >= a.min_n]
    aps.sort(key=lambda x: -len(x[1]))
    out_ap = os.path.join(os.path.dirname(a.csv), "adjust_by_airport.csv")
    with open(out_ap, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["airport", "country", "n_routes", "median_ratio",
                                        f"factor(target{a.target})", "consistency", "needs_type_split"])
        print(f"\nAIRPORT ADJUSTMENT TABLE (top 20 of {len(aps)} airports with >= {a.min_n} routes; "
              f"factor = {a.target}/median):")
        print(f"  {'apt':4} {'ctry':4} {'n':>3} {'median':>7} {'factor':>7} {'consistent?':>11} {'type-split?':>11}")
        for d, rs in aps:
            rr = [x["ratio"] for x in rs]
            m = med(rr); factor = a.target / m if m > 0 else 0
            disp = logvar(rr) ** 0.5
            consistent = disp < 0.35            # routes at this airport agree -> a single factor works
            # does splitting by type cut the within-airport dispersion a lot?
            tg = defaultdict(list)
            for x in rs: tg[x["typ"]].append(x["ratio"])
            tmed = {k: med(v) for k, v in tg.items() if len(v) >= 2}
            resid = [x["ratio"]/tmed[x["typ"]] if x["typ"] in tmed else x["ratio"] for x in rs]
            needs_split = (disp - logvar(resid) ** 0.5) > 0.15 and len(tmed) > 1
            ctry = rs[0]["country"]
            w.writerow([d, ctry, len(rs), round(m, 3), round(factor, 3),
                        "yes" if consistent else "no", "yes" if needs_split else "no"])
            if aps.index((d, rs)) < 20:
                print(f"  {d:4} {ctry:4} {len(rs):>3} {m:>7.2f} {factor:>7.2f} "
                      f"{'yes' if consistent else 'no':>11} {'yes' if needs_split else 'no':>11}")
    print(f"  ...full table -> {out_ap}")
    ncons = sum(1 for _, rs in aps if logvar([x['ratio'] for x in rs]) ** 0.5 < 0.35)
    print(f"  {ncons}/{len(aps)} airports are internally CONSISTENT (one airport factor fixes them - "
          f"a catchment correction); the rest still vary by route type/haul.")

    # CROSS-TIME hold-out: fit airport factors on EVEN years, test on ODD
    even = [r for r in rows if r["year"] % 2 == 0]
    odd = [r for r in rows if r["year"] % 2 == 1]
    if even and odd:
        gm = defaultdict(list)
        for r in even: gm[r["dep"]].append(r["ratio"])
        fac = {k: med(v) for k, v in gm.items() if len(v) >= a.min_n}
        before = within([r["ratio"] for r in odd])
        after = within([r["ratio"]/fac[r["dep"]] if r["dep"] in fac else r["ratio"] for r in odd])
        print(f"\nCROSS-TIME TEST (airport factors fit on EVEN years, applied to ODD years):")
        print(f"  odd-year routes within +/-20%: {before:.0%} -> {after:.0%}  "
              f"({'generalises' if after > before + 0.03 else 'does NOT generalise - likely noise'})")
    print("\nRead: if origin-AIRPORT explains the most variance and most airports are consistent, the "
          "biggest win is a per-airport catchment factor - the analyst's manual adjustment, automated. "
          "Set --target 1.05 to bake in a slight over-lean for the sales use.")


if __name__ == "__main__":
    main()
