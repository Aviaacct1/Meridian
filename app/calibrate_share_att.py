#!/usr/bin/env python3
"""
Avia Solutions - sweep the airport SIZE-pull exponent against the domestic basket AND the Genoa anchor.
======================================================================================================
The logit sweep ruled out choice-sharpness: the over-credit floored at ~1.9x with the spread
exploding. The cause is the missing hub SIZE pull (attractiveness = OAG size_m ** att_exponent),
which the old engine zeroed whenever QSI was used. att_exponent 0 = flat (the ~1.9x over-credit);
higher = the big hub draws more, harder where it's dominant (the New York case), which is what should
both centre the median AND kill the haul-dependence.

The catch: more size pull also lowers GENOA's share (Milan's size pull grows), and Genoa must stay in
its trusted 50-63k band. So this sweeps att_exponent over BOTH the 38-route domestic basket and the
Genoa anchor, and we pick the value that lands the basket median on 1.0 with the tightest spread while
Genoa holds. logit fixed at 0.008.

RUN where both stores live:
    py -3.12 calibrate_share_att.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ATT_GRID = [0.0, 0.20, 0.35, 0.50, 0.65, 0.80, 1.00]
GENOA_COMPET = ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"]
GENOA_DEST = ["JFK", "EWR", "LGA"]
GENOA_CAP = 132496 * 0.85          # daily A321XLR planning capacity (from test_route_forecast)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--grid", default=None)
    ap.add_argument("--stim", type=float, default=1.15)
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return

    import route_forecast as RF, oag_served as OAS, sabre_catchment as SC
    import calibrate_share_domestic as CSD
    grid = [float(x) for x in a.grid.split(",")] if a.grid else ATT_GRID

    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)

    def week_for(year):
        yy = year if year in wyear else min(wyear, key=lambda k: abs(k - year))
        return sorted([w for w in wyear[yy] if w[5:7] == "05"] or wyear[yy])[-1]

    idx_cache = {}
    def index(week):
        if week not in idx_cache:
            idx_cache[week] = OAS.build_served_index(a.oag, week)
        return idx_cache[week]

    # domestic basket inputs (actual shares read once)
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
            cases.append(dict(orig=orig, dest_codes=dest_codes, compet=compet,
                              week=week_for(yr), block=20.0 + CSD._gcd_nm(orig, d) / 7.0,
                              act_shr=actual / market))
    # Genoa anchor inputs
    gweek = week_for(2025)
    _, gmarket, _ = SC.destination_market_split(a.sabre, GENOA_COMPET, GENOA_DEST, year=2025)
    print(f"{len(cases)} domestic routes; Genoa market {gmarket:,.0f}, cap {GENOA_CAP:,.0f}\n")

    def stats(rs):
        rs = sorted(rs); n = len(rs)
        med = (rs[n//2] if n % 2 else (rs[n//2-1]+rs[n//2])/2) if rs else 0
        logs = [math.log(r) for r in rs if r > 0]
        mu = sum(logs)/len(logs) if logs else 0
        sd = (sum((x-mu)**2 for x in logs)/len(logs))**0.5 if logs else 0
        within = sum(1 for r in rs if 0.8 <= r <= 1.25) / len(rs) if rs else 0
        return med, sum(rs)/len(rs), sd, within

    print(f"{'att':>5} {'median':>7} {'mean':>6} {'spread':>7} {'in-band':>8} {'GOA shr':>8} {'GOA carried':>12}")
    print("-" * 60)
    for ae in grid:
        ratios = []
        for c in cases:
            eng, _ = RF.qsi_capture_share(a.oag, c["week"], c["orig"], c["dest_codes"], c["compet"],
                                          14, c["block"], att_exponent=ae, served_index=index(c["week"]))
            if c["act_shr"]:
                ratios.append(eng / c["act_shr"])
        med, mean, sd, within = stats(ratios)
        gshr, _ = RF.qsi_capture_share(a.oag, gweek, "GOA", GENOA_DEST, GENOA_COMPET, 7, 540,
                                       att_exponent=ae, served_index=index(gweek))
        gcar = min(gmarket * gshr * a.stim, GENOA_CAP)
        print(f"{ae:>5.2f} {med:>7.2f} {mean:>6.2f} {sd:>7.3f} {within:>7.0%} {gshr:>7.1%} {gcar:>12,.0f}")
    print("\nPick att where the domestic median sits on ~1.0 with the lowest spread and the highest "
          "in-band, while GOA carried stays in 50-63k. That value becomes the qsi_capture_share default.")


if __name__ == "__main__":
    main()
