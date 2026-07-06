#!/usr/bin/env python3
r"""
Avia Solutions - item-9 calibration sizer: is the market-size over-read STABLE across year-groups?
==================================================================================================
The forecastable deep-dive shows demand over-reads thin markets and under-reads big ones (a market-
size gradient, not a uniform level). The review's rule is that a bucket correction only goes in as a
CAPPED factor and only if at least two independent year-groups agree on its sign and rough size. This
reads a back-test CSV and prints median fc/p2p by market-size bucket BROKEN OUT BY YEAR, on the clean
forecastable routes (pre-existing market >= carried, seasonal routes optionally excluded), then
proposes a capped factor per bucket anchored on the bucket that's already unbiased.

    py -3.12 analyze_calib.py E:\bt_v2_6yr_det.csv
    py -3.12 analyze_calib.py E:\bt_v2_6yr_det.csv --keep-seasonal   (include summer/winter routes)
    py -3.12 analyze_calib.py E:\bt_v2_6yr_det.csv --fsc-only        (FSC only; LCC/ULCC are stim-led)
"""
import argparse, csv, os, sys

EDGES = [15000, 50000, 150000]
LABELS = ["<15k", "15-50k", "50-150k", ">150k"]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _bucket(v):
    v = v or 0
    for i, e in enumerate(EDGES):
        if v < e:
            return LABELS[i]
    return LABELS[-1]


HAUL_E, HAUL_L = [800, 2500, 6000], ["<800km", "800-2500", "2500-6000", ">6000km"]


def _haul(v):
    v = v or 0
    for i, e in enumerate(HAUL_E):
        if v < e:
            return HAUL_L[i]
    return HAUL_L[-1]


def _group_of(r, mode):
    """The segment a route falls in for region/type/haul; market is handled inline (needs the edges)."""
    if mode == "region":
        return r.get("region") or "OTH"
    if mode == "type":
        return r.get("type") or "?"
    if mode == "haul":
        return _haul(_f(r.get("gcd_km")))
    return None


def _med(xs):
    xs = sorted(v for v in xs if v is not None)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def main():
    ap = argparse.ArgumentParser(description="By-year x by-market median fc/p2p on forecastable routes.")
    ap.add_argument("csv")
    ap.add_argument("--min-outturn", type=float, default=3000)
    ap.add_argument("--keep-seasonal", action="store_true", help="include summer/winter-only routes")
    ap.add_argument("--fsc-only", action="store_true", help="restrict to FSC (LCC/ULCC are stimulation-led)")
    ap.add_argument("--type", default=None, help="restrict to one airline type (FSC / LCC / ULCC / Regional)")
    ap.add_argument("--group-by", default="market", choices=["market", "region", "type", "haul"],
                    help="what to segment the over-read by: market size (default), region, airline type, "
                         "or haul band. region and haul are CLEAN keys (not the ratio's denominator).")
    ap.add_argument("--sweep", action="store_true",
                    help="HIT-RATE view: for a range of uniform trims k, report the share of forecastable "
                         "routes within x1.05 / x1.2 / x1.4. Pick the k that MAXIMISES the tight bands, not "
                         "the one that centres the median - a trim that slides the already-right routes off "
                         "their mark is a loss even if the median improves.")
    ap.add_argument("--anchor", default="50-150k", help="bucket assumed unbiased; factors are relative to it")
    ap.add_argument("--floor", type=float, default=0.6, help="cap: no factor below this (don't over-correct)")
    ap.add_argument("--bucket-by", default="p2p_outturn",
                    help="field that defines the size bucket: p2p_outturn (actual, post-hoc) or natural "
                         "(the measured market = the LIVE key the factor uses). Size the factor on natural.")
    ap.add_argument("--edges", default="15000,50000,150000",
                    help="bucket upper edges; use larger edges for --bucket-by natural (it runs ~1.3x P2P)")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        print(f"not found: {a.csv}"); return 2
    global EDGES, LABELS
    EDGES = [float(x) for x in a.edges.split(",")]
    LABELS = [f"<{int(EDGES[0]//1000)}k"] + \
             [f"{int(EDGES[i]//1000)}-{int(EDGES[i+1]//1000)}k" for i in range(len(EDGES) - 1)] + \
             [f">{int(EDGES[-1]//1000)}k"]

    rows = list(csv.DictReader(open(a.csv, newline="")))
    fore = []
    for r in rows:
        fp = _f(r.get("fc_over_p2p"))
        p2p = _f(r.get("p2p_outturn")) or 0
        nat = _f(r.get("natural")) or 0
        if fp is None or p2p < a.min_outturn or nat < p2p:      # forecastable = pre-existing >= carried
            continue
        if a.fsc_only and (r.get("type") or "").upper() != "FSC":
            continue
        if a.type and (r.get("type") or "").upper() != a.type.upper():
            continue
        svc = (r.get("service") or "").strip().lower()
        if not a.keep_seasonal and svc in ("summer", "winter"):
            continue
        bkt = _bucket(_f(r.get(a.bucket_by)) or 0) if a.group_by == "market" else _group_of(r, a.group_by)
        r["_fp"], r["_bkt"], r["_yr"] = fp, bkt, str(r.get("year"))
        fore.append(r)

    if not fore:
        print("no forecastable routes after filters"); return 0
    years = sorted({r["_yr"] for r in fore})
    if a.group_by == "market":
        groups = LABELS
    else:
        from collections import Counter
        cnt = Counter(r["_bkt"] for r in fore)
        groups = [g for g, _ in cnt.most_common()]
    seasonal_note = "excluded" if not a.keep_seasonal else "included"
    scope = a.type.upper() if a.type else ("FSC only" if a.fsc_only else "all types")
    print(f"\n{os.path.basename(a.csv)}: forecastable routes, seasonal {seasonal_note}, {scope} "
          f"(n={len(fore)})")
    print(f"median fc/p2p by {a.group_by}, split by launch year (n in brackets):\n")
    hdr = f"  {'group':9} {'ALL':>13} " + " ".join(f"{y:>11}" for y in years)
    print(hdr)
    for b in groups:
        allb = [r["_fp"] for r in fore if r["_bkt"] == b]
        cells = []
        for y in years:
            xs = [r["_fp"] for r in fore if r["_bkt"] == b and r["_yr"] == y]
            m = _med(xs)
            cells.append(f"{m:>6.2f}({len(xs):>3})" if m is not None else f"{'-':>11}")
        m_all = _med(allb)
        allc = f"{m_all:>6.2f}({len(allb):>4})" if m_all is not None else f"{'-':>13}"
        print(f"  {b:9} {allc} " + " ".join(cells))

    # proposed capped factors, anchored so the unbiased bucket stays put
    anchor_med = _med([r["_fp"] for r in fore if r["_bkt"] == a.anchor]) or 1.0
    print(f"\nproposed capped factors (anchor {a.anchor} median {anchor_med:.2f} -> 1.0; "
          f"floor {a.floor}; SIGN must agree across >=2 years before applying):")
    for b in groups:
        med_all = _med([r["_fp"] for r in fore if r["_bkt"] == b])
        if med_all is None:
            continue
        raw = anchor_med / med_all            # multiply a bucket's forecast by this to centre it
        capped = max(a.floor, min(1.0 / a.floor, raw))
        yr_meds = [(_med([r["_fp"] for r in fore if r["_bkt"] == b and r["_yr"] == y]))
                   for y in years]
        over = sum(1 for m in yr_meds if m is not None and m > 1.05 * anchor_med)
        under = sum(1 for m in yr_meds if m is not None and m < 0.95 * anchor_med)
        agree = "OVER in " + str(over) + "yr" if over >= 2 else \
                "UNDER in " + str(under) + "yr" if under >= 2 else "NO 2-year agreement -> HOLD"
        print(f"  {b:9} factor {capped:>4.2f}   ({agree})")
    print("\nRead: apply a factor only where the sign agrees in two or more years. The anchor bucket "
          "should come out ~1.00 (no change). Thin-market factors < 1 trim the over-read; leave the "
          "rest alone. Seasonal routes are already out of this cut.")

    if a.sweep:
        fps = [r["_fp"] for r in fore]
        n = len(fps)
        def _within(k, f):
            lo, hi = 1.0 / f, f
            return sum(1 for x in fps if lo <= x * k <= hi)
        print(f"\nHIT-RATE sweep (uniform trim k applied to fc/p2p; share of the {n} forecastable routes "
              "within each factor band). Pick the k that MAXIMISES x1.05/x1.2, not the median:")
        print(f"  {'k':>5} {'within x1.05':>13} {'within x1.2':>13} {'within x1.4':>13}")
        for k in (1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70):
            w5, w2, w4 = _within(k, 1.05), _within(k, 1.2), _within(k, 1.4)
            print(f"  {k:>5.2f} {w5:>5}/{n} {100*w5/n:>3.0f}%  {w2:>5}/{n} {100*w2/n:>3.0f}%  "
                  f"{w4:>5}/{n} {100*w4/n:>3.0f}%")
        print("Read: the best k is where x1.05 and x1.2 peak. If they peak at k=1.0 (no trim), the median "
              "is a right-skewed TAIL, not a shift, and the fix is a tail cap (CRE sanity rail), not a "
              "trim that would move the routes we already get right.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
