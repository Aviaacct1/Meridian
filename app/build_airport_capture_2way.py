#!/usr/bin/env python3
r"""
Avia Solutions - DIRECTIONAL airport capture correction (John's refinement: factor inbound and outbound apart).
==================================================================================================
The origin-only factor conflated an airport's inbound and outbound routes and looked like noise. But direction
is known at forecast time, so we can factor the two apart: SJC-outbound forecasts fine (~1.0), SJC-inbound is
0.64, so we lift ONLY the inbound bucket and never touch the accurate outbound routes. Fit an origin effect
o[A] and a destination effect d[A] per airport (2-way, alternating, shrunk toward 0), so a route's correction is
    factor(X->Y) = exp(-(o[X] + d[Y]))
and validate HONESTLY with k-fold cross-validation: fit the effects on the training folds, apply to the held-out
fold, read the aggregate within-+/-20%. If CV +/-20% RISES, the directional correction generalises (it's real,
tight, systematic bias); if it doesn't beat 'before', the biased buckets are too spread for centring to help.

    py -3.12 build_airport_capture_2way.py bt_v2_6yr.csv --out airport_capture_2way.json

Grades fc/out (total onboard), the track-record basis. Reads the CSV only.
"""
import argparse, csv, math, random, statistics


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


def fit_effects(rows, K, clamp, iters=30):
    """Alternating 2-way fit: log(fc/out) ~ o[dep] + d[arr], each shrunk toward 0 for thin airports/clamped."""
    o, d = {}, {}
    dep_rows, arr_rows = {}, {}
    for r in rows:
        dep_rows.setdefault(r["dep"], []).append(r)
        arr_rows.setdefault(r["arr"], []).append(r)
    for a in dep_rows: o[a] = 0.0
    for a in arr_rows: d[a] = 0.0
    for _ in range(iters):
        for a, rs in dep_rows.items():
            s = sum(r["lfo"] - d.get(r["arr"], 0.0) for r in rs)
            o[a] = max(-clamp, min(clamp, s / (len(rs) + K)))
        for a, rs in arr_rows.items():
            s = sum(r["lfo"] - o.get(r["dep"], 0.0) for r in rs)
            d[a] = max(-clamp, min(clamp, s / (len(rs) + K)))
    return o, d


_OGRID = [round(0.40 + 0.01 * i, 2) for i in range(211)]  # 0.40 .. 2.50


def best_factor(fos, n_floor):
    """Factor that MAXIMISES this group's routes within +/-20%; 1.0 kept on ties (a centred/normal histogram
    stays at 1.0, only a SKEWED one gets corrected - John's condition falls out automatically)."""
    if len(fos) < n_floor:
        return 1.0
    bf, bc = 1.0, sum(1 for v in fos if 0.8 <= v <= 1.2)
    for f in _OGRID:
        c = sum(1 for v in fos if 0.8 <= v * f <= 1.2)
        if c > bc:
            bf, bc = f, c
    return bf


def _gate(logs, n_floor, t_thresh, mag_floor, clamp, shrink):
    """John's rule, corrected: lift only when the bias is (a) real (clears its own noise), (b) coherent
    (mean & median agree), AND (c) MATERIAL - the airport's median is far enough off 1.0 that its routes
    actually sit outside +/-20%. A significant-but-small bias (median ~0.90, already in the band) is left
    alone, because centring it pushes its top routes OUT. Returns a multiplier, or None to leave alone."""
    n = len(logs)
    if n < n_floor:
        return None
    m = statistics.mean(logs); med = statistics.median(logs)
    if m == 0 or (m > 0) != (med > 0):              # coherence: mean & median agree in sign
        return None
    if abs(med) < mag_floor:                        # MATERIAL: median must be genuinely off 1.0
        return None
    s = statistics.pstdev(logs) or 1e-9
    if abs(m) / (s / math.sqrt(n)) < t_thresh:      # significance: bias clears the scatter
        return None
    b = max(-clamp, min(clamp, sum(logs) / (n + shrink)))
    return math.exp(-b)


def gated_factors(rows, n_floor, t_thresh, mag_floor, clamp, shrink):
    dep_logs, arr_logs = {}, {}
    for r in rows:
        dep_logs.setdefault(r["dep"], []).append(r["lfo"])
        arr_logs.setdefault(r["arr"], []).append(r["lfo"])
    of = {a_: f for a_, logs in dep_logs.items() if (f := _gate(logs, n_floor, t_thresh, mag_floor, clamp, shrink)) is not None}
    df = {a_: f for a_, logs in arr_logs.items() if (f := _gate(logs, n_floor, t_thresh, mag_floor, clamp, shrink)) is not None}
    return of, df


_LO, _HI = math.log(0.8), math.log(1.2)


def _band_gate(logs, n_floor, side_floor, clamp, shrink):
    """John's rule stated correctly: lift an airport only when MOST of its routes miss the SAME way, i.e. sit
    OUTSIDE +/-20% on one side. net = (share below the band) - (share above it); |net| high means one-directional
    misses (CMN, KOS, SJC), low means a wide airport already half in the band (SIN, DMK) - leave those alone.
    Returns a multiplier or None."""
    n = len(logs)
    if n < n_floor:
        return None
    below = sum(1 for x in logs if x < _LO); above = sum(1 for x in logs if x > _HI)
    net = (below - above) / n
    if abs(net) < side_floor:                       # not one-directional enough -> leave alone
        return None
    b = sum(logs) / (n + shrink)
    if (b < 0) != (net > 0):                         # mean bias and the miss-direction must agree
        return None
    return math.exp(-max(-clamp, min(clamp, b)))


def band_factors(rows, n_floor, side_floor, clamp, shrink):
    dep_logs, arr_logs = {}, {}
    for r in rows:
        dep_logs.setdefault(r["dep"], []).append(r["lfo"])
        arr_logs.setdefault(r["arr"], []).append(r["lfo"])
    of = {a_: f for a_, logs in dep_logs.items() if (f := _band_gate(logs, n_floor, side_floor, clamp, shrink)) is not None}
    df = {a_: f for a_, logs in arr_logs.items() if (f := _band_gate(logs, n_floor, side_floor, clamp, shrink)) is not None}
    return of, df


def _apply_gated(r, of, df):
    """Apply the correction WITHOUT double-lifting: take the stronger of the two endpoint factors, never
    the product, so a route with two biased ends can't be centred twice and overshoot."""
    fo_ = of.get(r["dep"], 1.0); fd_ = df.get(r["arr"], 1.0)
    return fo_ if abs(math.log(fo_)) >= abs(math.log(fd_)) else fd_


def _corr(r, o, d, clamp):
    e = o.get(r["dep"], 0.0) + d.get(r["arr"], 0.0)
    return math.exp(-max(-clamp, min(clamp, e)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--shrink", type=float, default=4.0)
    ap.add_argument("--clamp", type=float, default=0.69)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--sweep", default="", help="comma list of shrink K to cross-validate, e.g. 4,10,20,40,80")
    ap.add_argument("--gated", action="store_true", help="John's rule: correct only airports consistently AND materially off")
    ap.add_argument("--band", action="store_true", help="John's rule stated right: lift only where most routes miss the SAME side")
    ap.add_argument("--optimise", action="store_true", help="John's exact idea: per-airport factor that MAXIMISES that airport's own +/-20%")
    ap.add_argument("--temporal", action="store_true", help="fit airport factors on EARLY years, apply to LATER years (past bias -> future?)")
    ap.add_argument("--fit-years", default="2016,2017,2018", help="years to LEARN each airport's factor from")
    ap.add_argument("--test-years", default="", help="years to grade on (default: everything not in fit-years)")
    ap.add_argument("--only-years", default="", help="restrict ALL rows to these years first (e.g. 2024 = single-regime CV)")
    ap.add_argument("--deploy", action="store_true", help="John's full option: optimise every airport on ALL data (origin+dest), write the deployable table")
    ap.add_argument("--live-year", default="2024", help="within-regime year to report as the honest live-accuracy proxy")
    ap.add_argument("--n-floor", type=int, default=6, help="min routes for an airport-direction to be eligible")
    ap.add_argument("--t-thresh", type=float, default=1.5, help="significance threshold (bias clears its scatter)")
    ap.add_argument("--mag-sweep", default="0.05,0.10,0.15,0.20,0.30", help="materiality floors |median log| to cross-validate")
    ap.add_argument("--side-sweep", default="0.30,0.40,0.50,0.60,0.70", help="one-sided miss-share floors to cross-validate")
    ap.add_argument("--out", default="airport_capture_2way.json")
    a = ap.parse_args()
    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        out = _f(r.get("outturn_pax")); fc = _f(r.get("forecast_pax")); fo = _f(r.get("fc_over_out"))
        if fo is None and out and fc:
            fo = fc / out
        if out is None or out < a.min_outturn or fo is None or fo <= 0:
            continue
        rows.append({"dep": (r.get("dep") or "").upper(), "arr": (r.get("arr") or "").upper(),
                     "fo": fo, "lfo": math.log(fo), "year": str(r.get("year") or "")})
    if a.only_years:
        keep = set(a.only_years.split(","))
        rows = [r for r in rows if r["year"] in keep]
        print(f"  [restricted to years {sorted(keep)}: {len(rows)} routes]")
    if not rows:
        print("No graded routes."); return
    n = len(rows)
    base = [r["fo"] for r in rows]
    random.seed(7)
    idx = list(range(n)); random.shuffle(idx)

    def cross_val(K):
        cv = [None] * n
        for k in range(a.folds):
            test = set(idx[k::a.folds])
            train = [rows[i] for i in range(n) if i not in test]
            ok, dk = fit_effects(train, K, a.clamp)
            for i in test:
                cv[i] = rows[i]["fo"] * _corr(rows[i], ok, dk, a.clamp)
        return cv

    if a.deploy:
        # OPTIMISE every airport on ALL the data we have (John's full option), directional (origin + dest).
        dep_fos, arr_fos = {}, {}
        for r in rows:
            dep_fos.setdefault(r["dep"], []).append(r["fo"])
            arr_fos.setdefault(r["arr"], []).append(r["fo"])
        of = {ap_: f for ap_, fos in dep_fos.items() if (f := best_factor(fos, a.n_floor)) != 1.0}
        df = {ap_: f for ap_, fos in arr_fos.items() if (f := best_factor(fos, a.n_floor)) != 1.0}
        full = [r["fo"] * _apply_gated(r, of, df) for r in rows]

        # honest live-accuracy proxy: same-regime within-year cross-validation (fit on other routes of that year)
        live = None
        ly = [i for i in range(n) if rows[i]["year"] == a.live_year]
        if len(ly) > 50:
            random.seed(11)
            lidx = ly[:]; random.shuffle(lidx)
            cvv = {}
            for k in range(a.folds):
                test = set(lidx[k::a.folds]); train = [rows[i] for i in ly if i not in test]
                td, ta = {}, {}
                for r in train:
                    td.setdefault(r["dep"], []).append(r["fo"]); ta.setdefault(r["arr"], []).append(r["fo"])
                ofk = {ap_: f for ap_, fos in td.items() if (f := best_factor(fos, a.n_floor)) != 1.0}
                dfk = {ap_: f for ap_, fos in ta.items() if (f := best_factor(fos, a.n_floor)) != 1.0}
                for i in test:
                    cvv[i] = rows[i]["fo"] * _apply_gated(rows[i], ofk, dfk)
            lb = [rows[i]["fo"] for i in ly]; lc = [cvv[i] for i in ly]
            live = (100 * _w20(lb) / len(ly), 100 * _w20(lc) / len(ly))

        import json
        tbl = {"meta": {"basis": "fc/out total onboard", "years": sorted({r['year'] for r in rows if r['year']}),
                        "n_routes": n, "n_floor": a.n_floor, "method": "per-airport +/-20%-maximising, directional",
                        "note": "DEPLOY factor. In-sample +/-20% is NOT the live claim; use the within-regime CV number."},
               "origin": {k: round(v, 3) for k, v in of.items()}, "dest": {k: round(v, 3) for k, v in df.items()}}
        outp = a.out if a.out != "airport_capture_2way.json" else "airport_capture_optimised.json"
        json.dump(tbl, open(outp, "w"), indent=1)

        print(f"\nFULL-DATA DEPLOY OPTIMISER ({a.csv}): every airport optimised on ALL years {tbl['meta']['years']}")
        print(f"  {len(of)} origin + {len(df)} dest airports corrected (skewed ones only; centred stay at 1.0).")
        print(f"  DEPLOYED-MODEL fit (in-sample, all data):  +/-20% {100*_w20(base)/n:.1f}% -> {100*_w20(full)/n:.1f}%   <- calibration fit, NOT the client claim")
        if live:
            print(f"  HONEST LIVE PROXY ({a.live_year} within-regime CV):  +/-20% {live[0]:.1f}% -> {live[1]:.1f}%   <- what a NEW route actually gets")
        print(f"  SJC dest {('%.2fx'%df['SJC']) if 'SJC' in df else 'n/a'}   wrote {outp} ({len(of)+len(df)} factors, ready to wire)")
        print(f"  -> deploy this if you want the model to use all the data (correct). But headline the tool with the")
        print(f"     LIVE PROXY, not the fit: with free per-airport factors the two diverge (your regression wouldn't).")
        print(f"     The version whose fit == live is a CAUSE-based bias model (secondary-airport/catchment), next step.")
        return

    if a.temporal:
        def dir_factors(fit_rows, n_floor, clamp, shrink):
            dep_logs, arr_logs = {}, {}
            for r in fit_rows:
                dep_logs.setdefault(r["dep"], []).append(r["lfo"])
                arr_logs.setdefault(r["arr"], []).append(r["lfo"])
            of = {ap_: math.exp(-max(-clamp, min(clamp, sum(L) / (len(L) + shrink))))
                  for ap_, L in dep_logs.items() if len(L) >= n_floor}
            df = {ap_: math.exp(-max(-clamp, min(clamp, sum(L) / (len(L) + shrink))))
                  for ap_, L in arr_logs.items() if len(L) >= n_floor}
            return of, df

        fit_years = set(a.fit_years.split(","))
        allyears = sorted({r["year"] for r in rows if r["year"]})
        test_years = a.test_years.split(",") if a.test_years else [y for y in allyears if y not in fit_years]
        fit_rows = [r for r in rows if r["year"] in fit_years]
        of, df = dir_factors(fit_rows, a.n_floor, a.clamp, a.shrink)
        print(f"\nTEMPORAL TEST ({a.csv}): learn each airport's factor on {sorted(fit_years)}, apply to later years")
        print(f"  This is 'we were under-forecasting for years -> lift it -> does the NEXT year land better?'")
        print(f"  Directional, shrunk factor (stable, not the overfit count-maximiser). Years present: {allyears}")
        print(f"  fit rows {len(fit_rows)}   airports learned: {len(of)} origin + {len(df)} dest   "
              f"SJC dest {('%.2fx'%df['SJC']) if 'SJC' in df else 'n/a'}")
        for y in test_years:
            ty = [r for r in rows if r["year"] == y]
            if not ty:
                continue
            b = [r["fo"] for r in ty]
            c = [r["fo"] * _apply_gated(r, of, df) for r in ty]
            touched = sum(1 for r in ty if _apply_gated(r, of, df) != 1.0)
            db = _w20(c) - _w20(b)
            print(f"  {y}:  n={len(ty):>4}  touched {touched:>4}   +/-20% {100*_w20(b)/len(ty):4.1f}% -> {100*_w20(c)/len(ty):4.1f}% ({100*db/len(ty):+.1f}pp)   "
                  f"median {_median(b):.2f} -> {_median(c):.2f}")
        print("  -> if the LATER years' +/-20% RISES, past bias predicts future bias and your correction ships.")
        print("     If they fall or stay flat, the apparent per-airport bias didn't persist - it was mostly the")
        print("     coin-flip effect, not a standing feature of the airport. This is the honest 'forecast a new route' test.")
        return

    if a.optimise:
        GRID = [round(0.40 + 0.01 * i, 2) for i in range(211)]  # 0.40 .. 2.50

        def best_f(fos, n_floor):
            """The factor that MAXIMISES this airport's routes within +/-20%. f=1.0 always available and is
            kept on ties, so the airport can NEVER be made worse in-sample (John's guarantee)."""
            if len(fos) < n_floor:
                return 1.0
            base = sum(1 for v in fos if 0.8 <= v <= 1.2)
            bf, bc = 1.0, base
            for f in GRID:
                c = sum(1 for v in fos if 0.8 <= v * f <= 1.2)
                if c > bc:                      # strict improve only -> ties keep no-correction
                    bf, bc = f, c
            return bf

        # partition routes by ORIGIN airport (each route in exactly one group -> the guarantee is exact, no overlap)
        dep_fos = {}
        for r in rows:
            dep_fos.setdefault(r["dep"], []).append(r["fo"])
        fac = {ap_: best_f(fos, a.n_floor) for ap_, fos in dep_fos.items()}
        full = [r["fo"] * fac.get(r["dep"], 1.0) for r in rows]
        corrected = sum(1 for v in fac.values() if v != 1.0)

        # honest test: fit each airport's optimal f on TRAINING routes, apply to the HELD-OUT routes
        cv = [None] * n
        for k in range(a.folds):
            test = set(idx[k::a.folds])
            tr_fos = {}
            for i in range(n):
                if i not in test:
                    tr_fos.setdefault(rows[i]["dep"], []).append(rows[i]["fo"])
            fk = {ap_: best_f(fos, a.n_floor) for ap_, fos in tr_fos.items()}
            for i in test:
                cv[i] = rows[i]["fo"] * fk.get(rows[i]["dep"], 1.0)

        # prove the guarantee: count airports helped / unchanged / HURT in-sample
        helped = unch = hurt = 0
        for ap_, fos in dep_fos.items():
            if len(fos) < a.n_floor:
                continue
            b = sum(1 for v in fos if 0.8 <= v <= 1.2)
            aft = sum(1 for v in fos if 0.8 <= v * fac[ap_] <= 1.2)
            helped += aft > b; unch += aft == b; hurt += aft < b

        print(f"\nPER-AIRPORT OPTIMISED FACTOR ({a.csv}): {n} routes, origin-partition, n-floor={a.n_floor}, {a.folds}-fold CV")
        print(f"  Each airport's factor is chosen to MAXIMISE its OWN +/-20% (John's exact method); f=1.0 kept on ties.")
        print(f"  BEFORE:            within +/-20% {100*_w20(base)/n:.1f}%")
        print(f"  AFTER (in-sample): within +/-20% {100*_w20(full)/n:.1f}%   <- optimised on the SAME routes it grades")
        print(f"  AFTER (held-out):  within +/-20% {100*_w20(cv)/n:.1f}%   <- factor fit on the airport's OTHER routes")
        print(f"  airports corrected {corrected}   |  in-sample: helped {helped}, unchanged {unch}, HURT {hurt}")
        print(f"  -> in-sample HURT should be 0 (your guarantee holds). The gap between in-sample and held-out is")
        print(f"     the overfit: optimising on the routes you then grade always wins; on a route it hasn't seen it")
        print(f"     doesn't, because an airport's past routes don't pin where its next one lands. Held-out is what a")
        print(f"     client's new route actually is. SJC's dest bias survives because it has an EXTERNAL cause, not")
        print(f"     because it optimised its own history.")
        return

    if a.band:
        def cross_val_band(side):
            cv = [None] * n
            for k in range(a.folds):
                test = set(idx[k::a.folds])
                train = [rows[i] for i in range(n) if i not in test]
                of, df = band_factors(train, a.n_floor, side, a.clamp, a.shrink)
                for i in test:
                    cv[i] = rows[i]["fo"] * _apply_gated(rows[i], of, df)
            return cv
        print(f"\nONE-SIDED-MISS CORRECTION ({a.csv}): {n} routes, n-floor={a.n_floor}, shrink={a.shrink}, {a.folds}-fold CV")
        print(f"  Rule: lift an airport only when most of its routes miss the SAME side of +/-20% (net one-directional).")
        print(f"  BEFORE (no correction):  within +/-20% {100*_w20(base)/n:.1f}%   median|log| {_median([abs(math.log(v)) for v in base]):.3f}")
        for side in [float(x) for x in a.side_sweep.split(",")]:
            of, df = band_factors(rows, a.n_floor, side, a.clamp, a.shrink)
            full_s = [r["fo"] * _apply_gated(r, of, df) for r in rows]
            cv_s = cross_val_band(side)
            dc = _w20(cv_s) - _w20(base); di = _w20(full_s) - _w20(base)
            print(f"  net-miss>={side:.2f}:  airports {len(of)+len(df):>4} ({len(of)}o+{len(df)}d)   "
                  f"in-sample {100*_w20(full_s)/n:4.1f}% ({100*di/n:+.1f})   CROSS-VAL {100*_w20(cv_s)/n:4.1f}% ({100*dc/n:+.1f}pp)")
        side0 = 0.50
        of, df = band_factors(rows, a.n_floor, side0, a.clamp, a.shrink)
        dep_r, arr_r = {}, {}
        for r in rows:
            dep_r.setdefault(r["dep"], []).append(r); arr_r.setdefault(r["arr"], []).append(r)
        moves = []
        for ap_, f in of.items():
            rs = dep_r[ap_]; b4 = _w20([r["fo"] for r in rs]); af = _w20([r["fo"]*f for r in rs])
            moves.append((af-b4, ap_, "orig", f, len(rs), 100*b4//len(rs), 100*af//len(rs)))
        for ap_, f in df.items():
            rs = arr_r[ap_]; b4 = _w20([r["fo"] for r in rs]); af = _w20([r["fo"]*f for r in rs])
            moves.append((af-b4, ap_, "dest", f, len(rs), 100*b4//len(rs), 100*af//len(rs)))
        print(f"\n  Per-airport +/-20% before -> after at net-miss>={side0} (all corrected airports, worst first):")
        hurt = [m for m in sorted(moves) if m[0] < 0]
        for d_, ap_, side_, f, nn, p0, p1 in (hurt[:6] if hurt else []):
            print(f"    {ap_} {side_:>4} {f:.2f}x  n={nn:>3}  +/-20% {p0}% -> {p1}%  ({d_:+d})  <- HURT")
        print(f"    ...{len(moves)-len(hurt)} airports improved or unchanged; {len(hurt)} hurt.")
        for d_, ap_, side_, f, nn, p0, p1 in sorted(moves, reverse=True)[:5]:
            print(f"    {ap_} {side_:>4} {f:.2f}x  n={nn:>3}  +/-20% {p0}% -> {p1}%  ({d_:+d})")
        sjc = [f"{s} {of.get('SJC') if s=='orig' else df.get('SJC'):.2f}x" for s in ('orig','dest') if ('SJC' in of if s=='orig' else 'SJC' in df)]
        print(f"  SJC: {', '.join(sjc) if sjc else 'left alone at this floor'}")
        print("  -> if a net-miss floor makes CROSS-VAL beat BEFORE, John's rule is right and ships at that floor.")
        return

    if a.gated:
        def cross_val_gated(mag):
            cv = [None] * n
            for k in range(a.folds):
                test = set(idx[k::a.folds])
                train = [rows[i] for i in range(n) if i not in test]
                of, df = gated_factors(train, a.n_floor, a.t_thresh, mag, a.clamp, a.shrink)
                for i in test:
                    cv[i] = rows[i]["fo"] * _apply_gated(rows[i], of, df)
            return cv
        print(f"\nGATED DIRECTIONAL CORRECTION ({a.csv}): {n} routes, n-floor={a.n_floor}, t>={a.t_thresh}, shrink={a.shrink}, {a.folds}-fold CV")
        print(f"  Rule: lift only airports that are consistent (significant + coherent) AND materially off 1.0.")
        print(f"  Correction takes the stronger endpoint factor, never the product (no double-lift).")
        print(f"  BEFORE (no correction):  within +/-20% {100*_w20(base)/n:.1f}%   median|log| {_median([abs(math.log(v)) for v in base]):.3f}")
        for mag in [float(x) for x in a.mag_sweep.split(",")]:
            of, df = gated_factors(rows, a.n_floor, a.t_thresh, mag, a.clamp, a.shrink)
            full_m = [r["fo"] * _apply_gated(r, of, df) for r in rows]
            cv_m = cross_val_gated(mag)
            dc = _w20(cv_m) - _w20(base); di = _w20(full_m) - _w20(base)
            lo, hi = round(math.exp(-mag), 2), round(math.exp(mag), 2)
            print(f"  |med|>={mag:.2f} (outside {lo}-{hi}):  airports {len(of)+len(df):>4} ({len(of)}o+{len(df)}d)   "
                  f"in-sample {100*_w20(full_m)/n:4.1f}% ({100*di/n:+.1f})   CROSS-VAL {100*_w20(cv_m)/n:4.1f}% ({100*dc/n:+.1f}pp)")
        # per-airport before/after at a sensible materiality (0.15 ~ outside 0.86-1.16), so John can SEE SJC win
        mag0 = 0.15
        of, df = gated_factors(rows, a.n_floor, a.t_thresh, mag0, a.clamp, a.shrink)
        print(f"\n  Per-airport +/-20% before -> after at |med|>={mag0} (the corrected airports, biggest movers):")
        dep_r, arr_r = {}, {}
        for r in rows:
            dep_r.setdefault(r["dep"], []).append(r); arr_r.setdefault(r["arr"], []).append(r)
        moves = []
        for ap_, f in of.items():
            rs = dep_r[ap_]; b4 = _w20([r["fo"] for r in rs]); af = _w20([r["fo"]*f for r in rs])
            moves.append((af-b4, ap_, "orig", f, len(rs), 100*b4//len(rs), 100*af//len(rs)))
        for ap_, f in df.items():
            rs = arr_r[ap_]; b4 = _w20([r["fo"] for r in rs]); af = _w20([r["fo"]*f for r in rs])
            moves.append((af-b4, ap_, "dest", f, len(rs), 100*b4//len(rs), 100*af//len(rs)))
        for d_, ap_, side, f, nn, p0, p1 in sorted(moves, reverse=True)[:8]:
            print(f"    {ap_} {side:>4} {f:.2f}x  n={nn:>3}  +/-20% {p0}% -> {p1}%  ({d_:+d} routes)")
        for d_, ap_, side, f, nn, p0, p1 in sorted(moves)[:4]:
            print(f"    {ap_} {side:>4} {f:.2f}x  n={nn:>3}  +/-20% {p0}% -> {p1}%  ({d_:+d} routes)  <- HURT")
        sjc = [f"{s} {of.get('SJC') if s=='orig' else df.get('SJC'):.2f}x" for s in ('orig','dest') if ('SJC' in of if s=='orig' else 'SJC' in df)]
        print(f"  SJC: {', '.join(sjc) if sjc else 'left alone at this materiality'}")
        print("  -> read CROSS-VAL vs BEFORE. If a materiality floor now beats it, John's correction is right and")
        print("     ships at that floor. The per-airport table shows where lifting helps (SJC) vs hurts (near-1.0).")
        return

    if a.sweep:
        print(f"\nSHRINK SWEEP ({a.csv}): {n} routes, {a.folds}-fold cross-validation (the honest column)")
        print(f"  BEFORE (no correction):        within +/-20% {100*_w20(base)/n:.1f}%   median|log| {_median([abs(math.log(v)) for v in base]):.3f}")
        for K in [float(x) for x in a.sweep.split(",")]:
            full_k = [r["fo"] * _corr(r, *fit_effects(rows, K, a.clamp), a.clamp) for r in rows]
            cv_k = cross_val(K)
            dc = _w20(cv_k) - _w20(base)
            print(f"  K={K:>5.0f}:  in-sample {100*_w20(full_k)/n:4.1f}%   CROSS-VAL {100*_w20(cv_k)/n:4.1f}% ({100*dc/n:+.1f}pp)   "
                  f"cv median|log| {_median([abs(math.log(v)) for v in cv_k]):.3f}")
        print("  -> pick the K whose CROSS-VAL beats BEFORE by the most. If none does, the cohort-wide directional")
        print("     correction doesn't generalise at any regularisation -> apply only named, well-evidenced airports.")
        return

    o, d = fit_effects(rows, a.shrink, a.clamp)
    full = [r["fo"] * _corr(r, o, d, a.clamp) for r in rows]

    # k-fold cross-validation: fit effects on the training folds, apply to the held-out fold
    random.seed(7)
    idx = list(range(n)); random.shuffle(idx)
    cv = [None] * n
    for k in range(a.folds):
        test = set(idx[k::a.folds])
        train = [rows[i] for i in range(n) if i not in test]
        ok, dk = fit_effects(train, a.shrink, a.clamp)
        for i in test:
            cv[i] = rows[i]["fo"] * _corr(rows[i], ok, dk, a.clamp)

    print(f"\nDIRECTIONAL AIRPORT CORRECTION ({a.csv}): {n} routes, shrink K={a.shrink}, {a.folds}-fold CV")
    print(f"  BEFORE:            median fc/out {_median(base):.2f}   within +/-20% {100*_w20(base)//n}%   median|log| {_median([abs(math.log(v)) for v in base]):.3f}")
    print(f"  AFTER (in-sample): median {_median(full):.2f}   within +/-20% {100*_w20(full)//n}%   median|log| {_median([abs(math.log(v)) for v in full]):.3f}")
    print(f"  AFTER (cross-val): median {_median(cv):.2f}   within +/-20% {100*_w20(cv)//n}%   median|log| {_median([abs(math.log(v)) for v in cv]):.3f}")
    di = _w20(full) - _w20(base); dc = _w20(cv) - _w20(base)
    print(f"  within +/-20%:  in-sample {di:+d} ({100*di/n:+.1f}pp)   |   cross-validated {dc:+d} ({100*dc/n:+.1f}pp)")
    print(f"  SJC: origin effect {math.exp(-o.get('SJC',0)):.2f}x  destination effect {math.exp(-d.get('SJC',0)):.2f}x")
    print(f"  -> CROSS-VALIDATED is the honest read. If it beats 'before', the directional correction is real and")
    print(f"     generalises; ship it. If it doesn't, the biased buckets are too spread for centring to add +/-20%.")

    import json
    factors = {"origin": {k: round(math.exp(-v), 4) for k, v in o.items() if abs(v) > 1e-3},
               "dest": {k: round(math.exp(-v), 4) for k, v in d.items() if abs(v) > 1e-3}}
    json.dump({"meta": {"shrink": a.shrink, "clamp": a.clamp, "cv_within20_delta_pp": round(100 * dc / n, 1)},
               "origin": factors["origin"], "dest": factors["dest"]}, open(a.out, "w"), indent=0)
    print(f"\n  wrote {a.out}: {len(factors['origin'])} origin + {len(factors['dest'])} dest effects.")


if __name__ == "__main__":
    main()
