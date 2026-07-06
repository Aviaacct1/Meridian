#!/usr/bin/env python3
"""
Avia Solutions - sweep the airport-choice sharpness against the domestic P2P basket.
====================================================================================
calibrate_share_domestic showed the engine over-credits the secondary by a median ~2x, but
HAUL-dependently: ~1.1 where the secondary genuinely holds its market (short, dense, competitive
service), 4-6x on long thin routes to New York where the hub out-frequencies it. A flat trim is
wrong. The knob is the logit_scale in the gencost airport choice: higher = the service/frequency
gap bites harder, so the share swings to the better-served airport where the gap is large (the New
York case) and barely moves where the secondary matches the hub (Seattle, Denver).

This sweeps logit_scale over the same 38-route basket. For each value it reports the median and mean
engine/actual ratio and the SPREAD (stdev of ln(ratio), the haul-dependence we want to crush). Pick
the value that puts the median on 1.0 with the smallest spread. Actual shares are read once; only the
catchment choice is re-run per value.

RUN where both stores live:
    py -3.12 calibrate_share_sweep.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

LOGIT_GRID = [0.008, 0.012, 0.016, 0.020, 0.025, 0.030, 0.040, 0.055]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--grid", default=None, help="comma logit_scale values to override the default grid")
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return

    import route_forecast as RF, oag_served as OAS, sabre_catchment as SC
    import calibrate_share_domestic as CSD
    grid = [float(x) for x in a.grid.split(",")] if a.grid else LOGIT_GRID

    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)

    def week_for(year):
        yy = year if year in wyear else min(wyear, key=lambda k: abs(k - year))
        return sorted([w for w in wyear[yy] if w[5:7] == "05"] or wyear[yy])[-1]

    # 1) actual shares + the per-route inputs, read once
    cases = []
    for orig, (compet, dests) in CSD.BASKET.items():
        for d in dests:
            dest_codes = CSD.DEST_METRO.get(d, [d])
            yr = actual = None
            for y in CSD.CLEAN_YEARS:
                c = CSD._carried(a.sabre, orig, dest_codes, y)
                if c >= CSD.MIN_CARRIED:
                    yr, actual = y, c; break
            if yr is None:
                continue
            _, market, _ = SC.destination_market_split(a.sabre, compet, dest_codes, year=yr)
            if not market:
                continue
            cases.append(dict(orig=orig, d=d, dest_codes=dest_codes, compet=compet, yr=yr,
                              week=week_for(yr), block=20.0 + CSD._gcd_nm(orig, d) / 7.0,
                              act_shr=actual / market))
    print(f"{len(cases)} clean P2P routes loaded\n")

    def stats(rs):
        rs = sorted(rs); n = len(rs)
        med = (rs[n//2] if n % 2 else (rs[n//2-1]+rs[n//2])/2) if rs else 0
        logs = [math.log(r) for r in rs if r > 0]
        mu = sum(logs)/len(logs) if logs else 0
        sd = (sum((x-mu)**2 for x in logs)/len(logs))**0.5 if logs else 0
        within = sum(1 for r in rs if 0.8 <= r <= 1.25) / len(rs) if rs else 0
        return med, sum(rs)/len(rs), sd, within

    print(f"{'logit':>7} {'median':>7} {'mean':>6} {'spread':>7} {'within 0.8-1.25':>16}")
    print("-" * 48)
    best = None
    for ls in grid:
        ratios = []
        for c in cases:
            eng, _ = RF.qsi_capture_share(a.oag, c["week"], c["orig"], c["dest_codes"], c["compet"],
                                          14, c["block"], logit_scale=ls)
            if c["act_shr"]:
                ratios.append(eng / c["act_shr"])
        med, mean, sd, within = stats(ratios)
        print(f"{ls:>7.3f} {med:>7.2f} {mean:>6.2f} {sd:>7.3f} {within:>15.0%}")
        score = abs(math.log(med)) + sd if med > 0 else 9
        if best is None or score < best[0]:
            best = (score, ls, med, sd, within)
    print(f"\nbest: logit_scale {best[1]:.3f}  median {best[2]:.2f}  spread {best[3]:.3f}  "
          f"within-band {best[4]:.0%}")
    print("spread = stdev of ln(ratio); lower is flatter across haul lengths. If even the best still "
          "leaves a wide spread, the hub needs a size/frequency PULL term, not just sharper choice.")


if __name__ == "__main__":
    main()
