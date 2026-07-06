#!/usr/bin/env python3
"""
Avia Solutions - is the hub size-pull haul-dependent? Calibrate att on LONG-HAUL-DISTANCE outturn.
=================================================================================================
The domestic basket fixed the size-pull at att ~0.75, but every route in it was short/medium-haul,
and Genoa-New York is long-haul. Hub-pull may behave differently over distance: people drive past a
secondary for a domestic hop they would take nonstop on a long sector. If so, long-haul att < 0.75
and Genoa keeps more share legitimately; if att is still ~0.75, Genoa really is a small neutral route
and the 55k was pitch optimism. We settle it on measured truth, not assumption.

The clean long-haul-distance test is Hawaii and Cancun from secondary-vs-hub metros: 5-6hr widebody
sectors that are PURE point-to-point (nobody connects beyond Honolulu or Cancun), so the terminating
share is uncontaminated by the connecting feed that wrecked the SJC long-haul set. Same harness as
calibrate_share_att, sweeping att, but on these long sectors. Compare the best att to the domestic
0.75 - the gap is the haul-dependence.

RUN where both stores live:
    py -3.12 calibrate_share_longhaul.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ATT_GRID = [0.0, 0.20, 0.35, 0.50, 0.65, 0.80, 1.00]
# secondary -> (competing metro set, [pure-O&D long-haul-distance destinations it/its hub serve])
BASKET = {
    "SMF": (["SFO", "SJC", "OAK", "SMF"], ["HNL", "OGG", "CUN"]),
    "SJC": (["SFO", "SJC", "OAK", "SMF"], ["HNL", "OGG", "CUN"]),
    "OAK": (["SFO", "SJC", "OAK", "SMF"], ["HNL", "OGG", "CUN"]),
    "BUR": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["HNL", "OGG"]),
    "SNA": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["HNL", "OGG", "CUN"]),
    "ONT": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["HNL", "CUN"]),
    "MDW": (["ORD", "MDW"], ["CUN"]),
    "DAL": (["DFW", "DAL"], ["CUN"]),
    "HOU": (["IAH", "HOU"], ["CUN"]),
}
DEST_METRO = {"HNL": ["HNL"], "OGG": ["OGG"], "CUN": ["CUN"]}
CLEAN_YEARS = [2024, 2023, 2025]
MIN_CARRIED = 2500


def _has_nonstop(oag, week, origin, dest_codes):
    """True if the secondary actually OPERATES a nonstop to the destination that week (OAG). The
    Genoa-relevant case: we only calibrate the size-pull on routes the secondary really flies, since
    a forecast always assumes the proposed nonstop exists. Unserved secondaries (share ~0, everyone
    uses the hub) are a different question and would swamp the average."""
    import duckdb
    ph = ",".join("?" * len(dest_codes))
    con = duckdb.connect(oag, read_only=True)
    try:
        n = con.execute(f"SELECT COUNT(*) FROM oag WHERE week=? AND dep_airport=? "
                        f"AND arr_airport IN ({ph})", [week, origin] + list(dest_codes)).fetchone()[0]
        return (n or 0) > 0
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--grid", default=None)
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

    cases = []
    for orig, (compet, dests) in BASKET.items():
        for d in dests:
            dest_codes = DEST_METRO.get(d, [d])
            yr = actual = None
            for y in CLEAN_YEARS:
                c = CSD._carried(a.sabre, orig, dest_codes, y)
                if c >= MIN_CARRIED:
                    yr, actual = y, c; break
            if yr is None:
                continue
            _, market, _ = SC.destination_market_split(a.sabre, compet, dest_codes, year=yr)
            if not market:
                continue
            wk = week_for(yr)
            cases.append(dict(orig=orig, d=d, dest_codes=dest_codes, compet=compet,
                              week=wk, block=20.0 + CSD._gcd_nm(orig, d) / 7.0,
                              act_shr=actual / market,
                              served=_has_nonstop(a.oag, wk, orig, dest_codes)))
    served = [c for c in cases if c["served"]]
    print(f"{len(cases)} clean long-haul-distance P2P routes ({len(served)} the secondary actually flies)\n")
    for c in cases:
        tag = "nonstop" if c["served"] else "no nonstop (hub-only)"
        print(f"  {c['orig']}-{c['d']}  actual share {c['act_shr']:.1%}  [{tag}]")
    print("\nCalibrating on the SERVED routes only (the Genoa case):")

    def stats(rs):
        rs = sorted(rs); n = len(rs)
        med = (rs[n//2] if n % 2 else (rs[n//2-1]+rs[n//2])/2) if rs else 0
        logs = [math.log(r) for r in rs if r > 0]
        mu = sum(logs)/len(logs) if logs else 0
        sd = (sum((x-mu)**2 for x in logs)/len(logs))**0.5 if logs else 0
        within = sum(1 for r in rs if 0.8 <= r <= 1.25) / len(rs) if rs else 0
        return med, sum(rs)/len(rs), sd, within

    print(f"{'att':>5} {'median':>7} {'mean':>6} {'spread':>7} {'in-band':>8}")
    print("-" * 40)
    best = None
    for ae in grid:
        ratios = []
        for c in served:
            eng, _ = RF.qsi_capture_share(a.oag, c["week"], c["orig"], c["dest_codes"], c["compet"],
                                          7, c["block"], att_exponent=ae, served_index=index(c["week"]))
            if c["act_shr"]:
                ratios.append(eng / c["act_shr"])
        med, mean, sd, within = stats(ratios)
        print(f"{ae:>5.2f} {med:>7.2f} {mean:>6.2f} {sd:>7.3f} {within:>7.0%}")
        score = abs(math.log(med)) + sd if med > 0 else 9
        if best is None or score < best[0]:
            best = (score, ae, med, sd)
    print(f"\nbest long-haul att {best[1]:.2f} (median {best[2]:.2f}, spread {best[3]:.3f}) "
          f"vs domestic ~0.75.")
    print("If long-haul att is clearly below 0.75, the size-pull weakens with distance and Genoa "
          "recovers share on data; if ~0.75, Genoa is genuinely a small neutral route.")


if __name__ == "__main__":
    main()
