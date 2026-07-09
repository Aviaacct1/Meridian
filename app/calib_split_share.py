#!/usr/bin/env python3
r"""
Avia Solutions - total-preserving P2P/connecting re-split, calibration (step 1, CSV-only, no re-run).
==================================================================================================
The engine over-attributes onboard demand to the P2P leg on connecting-heavy routes (fc/p2p up to 24x on
DOH-ATL while fc/tot is ~1.0). Fixing the SPLIT without touching the TOTAL (so +/-20% on the total cannot move):
keep the engine total, and re-split it into P2P vs connecting by an AIRPORT-CONNECTIVITY model.

    total          = forecast_pax                 (engine's onboard, UNCHANGED - +/-20% is graded on this)
    hub_score[apt] = 1 - median(P2P share of the airport's routes)   (big connecting hub -> high)
    p2p_share(o,d) = local_o x local_d  where local = 1 - hub_score   (a true P2P pax is local at BOTH ends)
    new_p2p        = total x p2p_share
    new_conn       = total x (1 - p2p_share)

hub_score is learned on the FIT years only, then applied out-of-sample. The true P2P share of a route is proxied
by p2p_outturn / outturn_pax (the P2P O&D market over onboard), clamped to [0,1]; connecting-hub routes read low.

This checks: does the connectivity split (a) collapse the wild fc/p2p toward the total (honest split) and (b)
IMPROVE fc/p2p +/-20% (it ties P2P to the better-behaved total), while fc/tot is untouched by construction. If it
holds on held-out, wire it into route_forecast (re-split the output + scale the PDEW connecting magnitude) and
value the connecting share at a prorated yield in the economics.

    py -3.12 calib_split_share.py C:\AviaDev\app\bt_v2_6yr.csv --fit-years 2016,2017,2018

Reads the CSV only. hub_score is a STABLE structural feature (connectivity), not the noisy per-airport capture
factor that failed; a route touching ATL/DOH/IST reads connecting-heavy because those airports do.
"""
import argparse, csv, math, json


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _median(xs):
    xs = sorted(xs); n = len(xs)
    return (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2) if xs else 0.0


def _haul(g):
    g = g or 0
    return "<800" if g < 800 else "800-2500" if g < 2500 else "2500-6000" if g < 6000 else ">6000"


def _w20(xs):
    return sum(1 for x in xs if 0.8 <= x <= 1.2)


# COVERAGE gross-up: Sabre under-reports LCC / US-domestic O&D, so the RAW P2P outturn understates true P2P and
# a Southwest focus city (MDW, BWI, DAL) FALSELY reads connecting-heavy. Gross the P2P up by the engine's own
# country/haul coverage factor before scoring localness, so the connectivity measure isn't a GDS-coverage artefact.
try:
    import coverage as _COV, airportsdata as _APD
    _AP = _APD.load("IATA")
except Exception:
    _COV = None; _AP = None


def _cov_factor(dep, arr, gcd):
    if _COV is None or _AP is None:
        return 1.0
    o = _AP.get((dep or "").upper()); d = _AP.get((arr or "").upper())
    try:
        return float(_COV.gross_up(o.get("country") if o else None,
                                   d.get("country") if d else None, gcd or 0.0))
    except Exception:
        return 1.0


def load(path, min_outturn):
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        p2p = _f(r.get("p2p_outturn")); out = _f(r.get("outturn_pax")); fc = _f(r.get("forecast_pax"))
        nat = _f(r.get("natural")); fp = _f(r.get("fc_over_p2p")); gcd = _f(r.get("gcd_km"))
        if None in (p2p, out, fc, fp) or p2p < min_outturn or out <= 0 or fc <= 0 or fp <= 0:
            continue
        if nat is None or nat < p2p:                       # forecastable only (the clean engine test)
            continue
        cov = _cov_factor(r.get("dep"), r.get("arr"), gcd)   # gross up the under-reported P2P before scoring
        rows.append({"year": str(r.get("year")), "dep": r.get("dep"), "arr": r.get("arr"),
                     "haul": _haul(gcd), "type": (r.get("type") or "?"), "p2p": p2p, "out": out, "total": fc,
                     "cur_fp": fp, "true_share": min(1.0, (p2p * cov) / out)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--shrink", type=float, default=4.0, help="partial-pool hub_score toward global for thin airports")
    ap.add_argument("--min-routes", type=int, default=3)
    ap.add_argument("--out", default=None, help="write the airport localness table to this JSON (for the engine)")
    ap.add_argument("--fit-types", default="FSC",
                    help="carrier types used to SCORE airports (default FSC only - LCC/ULCC domestic is GDS-"
                         "under-covered and falsely reads connecting; 'all' to use every type)")
    ap.add_argument("--load-table", default=None,
                    help="validate an EXTERNAL localness table (e.g. Sabre transfer-share) instead of fitting one")
    a = ap.parse_args()
    fit_years = set(a.fit_years.split(","))
    rows = load(a.csv, a.min_outturn)
    if not rows:
        print("No forecastable rows."); return
    fit = [r for r in rows if r["year"] in fit_years]
    print(f"CONNECTIVITY SPLIT CALIBRATION (forecastable, fit {sorted(fit_years)}): {a.csv}")

    if a.load_table:
        # VALIDATE an external table (e.g. the Sabre transfer-share table from build_hub_connectivity.py):
        # don't fit anything, just load it and grade the re-split it implies.
        _d = json.load(open(a.load_table))
        local = {k: float(v) for k, v in (_d.get("local", _d) or {}).items()}
        g_local = float(_d.get("global_localness", 0.9))
        print(f"  loaded table {a.load_table}: {len(local)} airports, global localness {g_local:.2f}")
    else:
        # score airports on well-covered routes only (default FSC); LCC/ULCC domestic is GDS-under-covered and
        # falsely reads connecting (MDW/BWI). Grading still uses ALL routes.
        ft = a.fit_types.strip().lower()
        score = fit if ft == "all" else [r for r in fit if r["type"] in set(a.fit_types.split(","))]
        if len(score) < 50:
            score = fit
        print(f"  scoring airports on {len(score)} routes (fit-types {a.fit_types}); grading on all {len(fit)} fit routes")
        # BILINEAR DECOMPOSITION: fit each airport's OWN localness so local_o x local_d ~ true_share.
        g_local = math.sqrt(max(0.02, _median([r["true_share"] for r in score])))
        lg = math.log(g_local)
        rlist = {}
        for r in score:
            rlist.setdefault(r["dep"], []).append((r["arr"], r["true_share"]))
            rlist.setdefault(r["arr"], []).append((r["dep"], r["true_share"]))
        L = {ap_: lg for ap_ in rlist}
        K = a.shrink
        for _ in range(40):
            for ap_, rs in rlist.items():
                s = sum(math.log(max(1e-3, ts)) - L.get(oth, lg) for oth, ts in rs)
                L[ap_] = max(math.log(0.02), min(0.0, (s + K * lg) / (len(rs) + K)))
        local = {ap_: math.exp(v) for ap_, v in L.items() if len(rlist[ap_]) >= a.min_routes}
    print(f"  global localness {g_local:.2f}; airports scored {len(local)}")
    top = sorted(local.items(), key=lambda kv: kv[1])[:12]     # lowest localness = biggest connecting hub
    print("  biggest connecting hubs (1-localness): " + ", ".join(f"{k} {1-v:.2f}" for k, v in top))

    def p2p_share(o, d):
        return max(0.02, min(1.0, local.get(o, g_local) * local.get(d, g_local)))

    if a.out:
        json.dump({"meta": {"fit_years": sorted(fit_years), "global_localness": round(g_local, 4),
                            "n_airports": len(local), "model": "p2p_share(o,d)=local_o*local_d"},
                   "global_localness": round(g_local, 4),
                   "local": {k: round(v, 4) for k, v in local.items()}},
                  open(a.out, "w"), indent=0)
        print(f"  wrote {a.out}: {len(local)} airport localness scores + global {g_local:.3f}")

    def _grade(name, rs):
        if len(rs) < 10:
            print(f"  {name}: n={len(rs)} (too few)"); return
        cur = [r["cur_fp"] for r in rs]
        new = [(r["total"] * p2p_share(r["dep"], r["arr"])) / r["p2p"] for r in rs]
        tot = [r["total"] / r["out"] for r in rs]
        print(f"\n  {name} (n={len(rs)}):")
        print(f"    fc/p2p  median {_median(cur):.2f} -> {_median(new):.2f}   +/-20% {100*_w20(cur)//len(rs)}% -> {100*_w20(new)//len(rs)}%")
        print(f"    fc/tot  median {_median(tot):.2f}  +/-20% {100*_w20(tot)//len(rs)}%   (UNCHANGED - total preserved)")

    _grade("FIT " + ",".join(sorted(fit_years)), fit)
    held = [r for r in rows if r["year"] not in fit_years]
    for y in sorted({r["year"] for r in held}):
        _grade("HELD-OUT " + y, [r for r in held if r["year"] == y])

    # by-haul on held-out: does the long-haul fc/p2p collapse from ~1.8 to ~1.0?
    if held:
        print("\n  HELD-OUT by haul (fc/p2p current -> re-split):")
        for lbl in ["<800", "800-2500", "2500-6000", ">6000"]:
            b = [r for r in held if r["haul"] == lbl]
            if len(b) < 10:
                continue
            cur = [r["cur_fp"] for r in b]
            new = [(r["total"] * p2p_share(r["dep"], r["arr"])) / r["p2p"] for r in b]
            print(f"    {lbl:>11}  n={len(b):>4}  {_median(cur):.2f} -> {_median(new):.2f}   "
                  f"+/-20% {100*_w20(cur)//len(b)}% -> {100*_w20(new)//len(b)}%")
    print("\n  Want: fc/p2p median collapses toward the total (~0.9) and its +/-20% RISES, with fc/tot untouched.")
    print("  If it holds, wire p2p_share into route_forecast (re-split output + PDEW magnitude) + prorate the")
    print("  connecting yield in the economics. hub_score becomes a per-airport table shipped with the engine.")


if __name__ == "__main__":
    main()
