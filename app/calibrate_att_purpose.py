#!/usr/bin/env python3
"""
Avia Solutions - validate the PURPOSE-linked size pull on both baskets at once, and read Genoa.
===============================================================================================
The domestic basket wanted att ~0.75, the served long-haul (leisure) set wanted ~0.50, and the thing
that separates them is trip purpose, not distance. So att is now driven by the route's premium-cabin
share (Sabre): leisure -> 0.50, business -> 0.80 (route_forecast.att_from_premium). This checks the
ONE mechanism reproduces BOTH baskets - if it does, the size pull is calibrated on measured purpose,
not a hand-picked constant - and prints what Genoa lands at on its own premium mix.

RUN where both stores live:
    py -3.12 calibrate_att_purpose.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GENOA_COMPET = ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"]
GENOA_DEST = ["JFK", "EWR", "LGA"]
GENOA_CAP = 132496 * 0.85


def _stats(rs):
    rs = sorted(rs); n = len(rs)
    med = (rs[n//2] if n % 2 else (rs[n//2-1]+rs[n//2])/2) if rs else 0
    logs = [math.log(r) for r in rs if r > 0]
    mu = sum(logs)/len(logs) if logs else 0
    sd = (sum((x-mu)**2 for x in logs)/len(logs))**0.5 if logs else 0
    within = sum(1 for r in rs if 0.8 <= r <= 1.25) / len(rs) if rs else 0
    return med, sum(rs)/len(rs), sd, within


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--stim", type=float, default=1.15)
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return

    import route_forecast as RF, oag_served as OAS, sabre_catchment as SC
    import calibrate_share_domestic as CSD, calibrate_share_longhaul as CLH

    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)

    def week_for(year):
        yy = year if year in wyear else min(wyear, key=lambda k: abs(k - year))
        return sorted([w for w in wyear[yy] if w[5:7] == "05"] or wyear[yy])[-1]

    idx_cache = {}
    def index(wk):
        if wk not in idx_cache:
            idx_cache[wk] = OAS.build_served_index(a.oag, wk)
        return idx_cache[wk]

    def collect(basket, dest_metro, min_carried, longhaul):
        out = []
        for orig, (compet, dests) in basket.items():
            for d in dests:
                dc = dest_metro.get(d, [d])
                yr = actual = None
                for y in CLH.CLEAN_YEARS:
                    c = CSD._carried(a.sabre, orig, dc, y)
                    if c >= min_carried:
                        yr, actual = y, c; break
                if yr is None:
                    continue
                wk = week_for(yr)
                if longhaul and not CLH._has_nonstop(a.oag, wk, orig, dc):
                    continue
                _, market, _ = SC.destination_market_split(a.sabre, compet, dc, year=yr)
                if not market:
                    continue
                out.append(dict(orig=orig, d=d, dc=dc, compet=compet, yr=yr, wk=wk,
                                block=20.0 + CSD._gcd_nm(orig, d) / 7.0, act=actual / market))
        return out

    groups = [("DOMESTIC", collect(CSD.BASKET, CSD.DEST_METRO, CSD.MIN_CARRIED, False)),
              ("LONG-HAUL", collect(CLH.BASKET, CLH.DEST_METRO, CLH.MIN_CARRIED, True))]

    all_ratios = []
    for name, cases in groups:
        print(f"\n=== {name} ({len(cases)} routes) ===")
        print(f"{'route':12} {'prem':>6} {'att':>5} {'act shr':>8} {'eng shr':>8} {'eng/act':>8}")
        ratios = []
        for c in cases:
            prem = RF.premium_share(a.sabre, c["compet"], c["dc"], year=c["yr"])
            att = RF.att_from_premium(prem)
            eng, _ = RF.qsi_capture_share(a.oag, c["wk"], c["orig"], c["dc"], c["compet"],
                                          7 if name == "LONG-HAUL" else 14, c["block"],
                                          att_exponent=att, served_index=index(c["wk"]))
            r = (eng / c["act"]) if c["act"] else 0
            ratios.append(r); all_ratios.append(r)
            print(f"{c['orig']+'-'+c['d']:12} {prem:>6.0%} {att:>5.2f} {c['act']:>7.1%} {eng:>8.1%} {r:>8.2f}")
        med, mean, sd, within = _stats(ratios)
        print(f"  -> median {med:.2f}  mean {mean:.2f}  spread {sd:.3f}  in-band {within:.0%}")

    med, mean, sd, within = _stats(all_ratios)
    print(f"\nBOTH baskets ({len(all_ratios)} routes): median {med:.2f}  spread {sd:.3f}  in-band {within:.0%}")

    # Genoa on its own premium mix
    gprem = RF.premium_share(a.sabre, GENOA_COMPET, GENOA_DEST, year=2025)
    gatt = RF.att_from_premium(gprem)
    gweek = week_for(2025)
    _, gmkt, _ = SC.destination_market_split(a.sabre, GENOA_COMPET, GENOA_DEST, year=2025)
    gshr, _ = RF.qsi_capture_share(a.oag, gweek, "GOA", GENOA_DEST, GENOA_COMPET, 7, 540,
                                   att_exponent=gatt, served_index=index(gweek))
    gcar = min(gmkt * gshr * a.stim, GENOA_CAP)
    print(f"\nGENOA-NY: premium {gprem:.0%} -> att {gatt:.2f}; market {gmkt:,.0f}; share {gshr:.1%}; "
          f"carried {gcar:,.0f}")
    print("Want: both baskets centred near 1.0 with tight spread on ONE mechanism, and a Genoa "
          "number that stands on its measured premium mix rather than a hand-set exponent.")


if __name__ == "__main__":
    main()
