#!/usr/bin/env python3
r"""
Avia Solutions - calibrated 2/3 interval (replaces the failed confidence tier and the fixed band).
==================================================================================================
The confidence TIER failed: +/-20% membership is not predictable from forecast-time features (held-out AUC
~0.52-0.58, no subset reaches or holds 2/3). The honest deliverable is not a per-route grade but a per-route
INTERVAL sized to the ACTUAL spread of forecast-vs-outturn, reported as "the central forecast, and 2 in 3
comparable past launches landed between LOWx and HIGHx." A single-number competitor cannot make that claim;
stating the real uncertainty is the pitch.

For a central forecast F the outturn is F / (forecast/actual ratio), so the 2/3-interval multipliers on F are
the inverse central percentiles of that ratio: low = 1/p83, high = 1/p17 (the middle 66.7%).

This differs from calib_bands.py in three ways that matter for a CLAIM:
  1. It reflects the SHIPPED size trim: the CSV's fc_over_p2p carries the OLD flat trim, so the raw engine
     ratio is recovered (/ old flat) and the NEW _SIZE_TRIM re-applied, so the band matches what the live
     tool now produces.
  2. It fits on the FIT years only, then reports the band's ACHIEVED coverage on each HELD-OUT year - a 2/3
     band should contain ~67% of held-out outturns. That coverage is the calibration test.
  3. It reports the band in plain pitch language.

    py -3.12 calib_interval.py E:\Avia\QSI\backtests\decomp_6yr.csv --fit-years 2016,2017,2018 \
        --validate E:\Avia\QSI\backtests\val24_o0.csv --validate E:\Avia\QSI\backtests\val25_o0.csv

Keep --applied-trim matching how the CSVs were produced (type = --market-factor was on). Reads CSVs only.
"""
import argparse, csv

# Must match route_forecast: the OLD flat per-type trim baked into the CSV, and the SHIPPED size trim.
TYPE_FLAT = {"FSC": 0.85, "ULCC": 0.85, "LCC": 0.95, "Regional": 0.90}
SIZE_TRIM = [(15000.0, 0.765), (50000.0, 0.821), (150000.0, 0.809), (float("inf"), 0.745)]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    i = min(len(xs) - 1, max(0, int(round(p / 100.0 * (len(xs) - 1)))))
    return xs[i]


def _flat(t):
    return TYPE_FLAT.get(t, TYPE_FLAT["FSC"])


def _size_mult(mkt):
    for edge, f in SIZE_TRIM:
        if (mkt or 0) < edge:
            return f
    return 1.0


def load_ratios(path, min_outturn, applied):
    """Post-ship forecast/actual records for forecastable routes: {year, ratio, nat}."""
    out = []
    for r in csv.DictReader(open(path, newline="")):
        p2p = _f(r.get("p2p_outturn")); nat = _f(r.get("natural")); fw = _f(r.get("fc_over_p2p"))
        if p2p is None or p2p < min_outturn or fw is None or fw <= 0:
            continue
        if nat is None or nat < p2p:                    # forecastable only
            continue
        t = r.get("type") or "?"
        raw = fw / (_flat(t) if applied == "type" else 1.0)   # strip the OLD trim
        ratio = raw * _size_mult(nat)                          # re-apply the SHIPPED size trim
        if ratio > 0:
            out.append({"year": str(r.get("year")), "ratio": ratio, "nat": nat})
    return out


def _band(ratios, lo_p, hi_p):
    p_lo, p_hi = _pct(ratios, lo_p), _pct(ratios, hi_p)
    return (1.0 / p_hi if p_hi else 0.0), (1.0 / p_lo if p_lo else 0.0), p_lo, p_hi


_SIZE_EDGES, _SIZE_LBL = [15000, 50000, 150000], ["<15k", "15-50k", "50-150k", ">150k"]


def _size_bucket(nat):
    for i, e in enumerate(_SIZE_EDGES):
        if (nat or 0) < e:
            return _SIZE_LBL[i]
    return _SIZE_LBL[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--fit-years", default="2016,2017,2018")
    ap.add_argument("--validate", action="append", default=[])
    ap.add_argument("--applied-trim", choices=["type", "none"], default="type")
    ap.add_argument("--min-outturn", type=float, default=3000.0)
    ap.add_argument("--coverage", type=float, default=0.667, help="central interval to size (2/3 default)")
    a = ap.parse_args()
    fit_years = set(a.fit_years.split(","))
    tail = (1.0 - a.coverage) / 2.0 * 100.0                    # e.g. 16.65
    lo_p, hi_p = tail, 100.0 - tail

    fit_recs = [r for r in load_ratios(a.csv, a.min_outturn, a.applied_trim) if r["year"] in fit_years]
    if not fit_recs:
        print("No forecastable fit-year rows."); return
    fit = [r["ratio"] for r in fit_recs]
    held = []          # held-out records (all validate files pooled)
    for vp in a.validate:
        held += load_ratios(vp, a.min_outturn, a.applied_trim)
    pool_recs = fit_recs + held
    pool = [r["ratio"] for r in pool_recs]

    def _cov(ratios, p_lo, p_hi):
        return sum(1 for x in ratios if p_lo <= x <= p_hi) / len(ratios) if ratios else 0.0

    # (1) FIT band + held-out coverage (the calibration test)
    b_low, b_high, p_lo_f, p_hi_f = _band(fit, lo_p, hi_p)
    print(f"\nCALIBRATED {int(round(a.coverage*100))}% INTERVAL (post-ship size trim)")
    print(f"  [fit {sorted(fit_years)}] band low {b_low:.2f}, high {b_high:.2f}  (median fc/actual {_pct(fit,50):.2f})")
    print(f"    coverage:  fit {100*_cov(fit,p_lo_f,p_hi_f):.0f}%  (n={len(fit)})", end="")
    for vp in a.validate:
        vr = [r["ratio"] for r in load_ratios(vp, a.min_outturn, a.applied_trim)]
        if vr:
            print(f"   held-out {vp.split(chr(92))[-1]} {100*_cov(vr,p_lo_f,p_hi_f):.0f}% (n={len(vr)})", end="")
    print()

    # (2) POOLED band (all gradeable years) = the RECOMMENDED wire-in band (conservative, uses all evidence)
    pb_low, pb_high, p_lo_p, p_hi_p = _band(pool, lo_p, hi_p)
    print(f"\n  RECOMMENDED (pooled all years, n={len(pool)}): low {pb_low:.2f}, high {pb_high:.2f}")
    print(f"    pitch: \"2 in 3 comparable launches landed between {pb_low:.2f}x and {pb_high:.2f}x the central forecast\"")

    # (3) BY MARKET SIZE (pooled) - does a size-conditioned band give the pitched mid-markets a tighter,
    #     still-2/3 interval? Reports each bucket's band, width and coverage; wire per-bucket only if the
    #     narrower buckets genuinely hold ~2/3.
    print(f"\n  BY MARKET SIZE - band fitted on FIT years, coverage checked on HELD-OUT (the validation):")
    print(f"    {'bucket':>10}  {'fit n':>6}  {'low':>5}  {'high':>5}  {'width':>6}  {'held n':>6}  {'held cov':>8}")
    for lbl in _SIZE_LBL:
        frs = [r["ratio"] for r in fit_recs if _size_bucket(r["nat"]) == lbl]
        hrs = [r["ratio"] for r in held if _size_bucket(r["nat"]) == lbl]
        if len(frs) < 15:
            print(f"    {lbl:>10}  {len(frs):>6}   (too few to fit)"); continue
        lo, hi, pl, ph = _band(frs, lo_p, hi_p)
        hc = f"{100*_cov(hrs, pl, ph):.0f}%" if len(hrs) >= 10 else f"n={len(hrs)}"
        print(f"    {lbl:>10}  {len(frs):>6}  {lo:>5.2f}  {hi:>5.2f}  {hi-lo:>6.2f}  {len(hrs):>6}  {hc:>8}")
    print("\n  Ship a size-conditioned band only for buckets whose HELD-OUT coverage stays ~2/3 (else the tighter\n"
          "  band is fit-year luck). Otherwise wire the single pooled band. The width ordering is the finding:\n"
          "  small markets are genuinely tighter - the honest, calibrated uncertainty a single-number rival can't show.")


if __name__ == "__main__":
    main()
