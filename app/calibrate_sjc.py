#!/usr/bin/env python3
"""
Avia Solutions - calibrate the rebuilt forecast loop on the SJC analyst forecasts.
==================================================================================
The clean calibration set: 25 prepared FSC long-haul SJC forecasts (sjc_validation_set.json),
each with the ANALYST's own capture and stimulation as targets and good GDS coverage. For each,
run route_forecast (measured California market x QSI share x stim, capacity-bounded) and put the
engine's QSI SHARE next to the analyst's hand-set CAPTURE. The ratio QSI-share / analyst-capture
is the calibration factor we fold into the share; if it is roughly constant the share just needs a
single scaling, if it varies by route it tells us where the QSI scoring is off.

RUN on the machine with both stores:
    py -3.12 calibrate_sjc.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BAY_AREA = ["SFO", "SJC", "OAK"]          # the SJC service-area catchment (the analyst's basis)


def _gcd_nm(a, b):
    import airportsdata
    ap = airportsdata.load("IATA")
    ra, rb = ap.get(a), ap.get(b)
    if not ra or not rb or ra["lat"] is None or rb["lat"] is None:
        return 4500.0
    la1, lo1, la2, lo2 = map(math.radians, [ra["lat"], ra["lon"], rb["lat"], rb["lon"]])
    x = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * 6371.0 * math.asin(math.sqrt(x)) / 1.852


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--set", default=os.path.join(HERE, "sjc_validation_set.json"))
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return

    import route_forecast as RF, oag_served as OAS, geo_resolve as GEO
    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)
    routes = json.load(open(a.set))["routes"]

    hdr = (f"{'route':16} {'airline':16} {'anl cap':>8} {'qsi shr':>8} {'shr/cap':>8} "
           f"{'anl f/c':>10} {'engine':>10} {'eng/anl':>8}")
    print(hdr); print("-" * len(hdr))
    ratios, fcr = [], []
    for r in routes:
        try:
            byr = r["base_yr"]
            # OAG week: same year if held, else nearest available
            yr = byr if byr in wyear else min(wyear, key=lambda y: abs(y - byr))
            week = sorted([w for w in wyear[yr] if w[5:7] == "05"] or wyear[yr])[-1]
            served = OAS.build_served_index(a.oag, week)
            dm = GEO.resolve_metro(r["dest"], served_index=served, expand=True)
            dest_codes = dm["airports"]
            block = 20.0 + _gcd_nm("SJC", r["dest"]) / 7.0
            cap = r["seats"] * r["freq"] * 52 * 2
            fr = RF.forecast(a.sabre, a.oag, week, "SJC", dest_codes, BAY_AREA, year=byr,
                             freq=r["freq"], block_min=block, stimulation=r["stim"],
                             annual_capacity=cap)
            anl_fc = r["seats"] * r["freq"] * 52 * 2 * r["lf"]
            shr = fr["qsi_share"]; cap_anl = r["capture"]
            sc = (shr / cap_anl) if cap_anl else 0
            eng = fr["carried_forecast"]; ea = (eng / anl_fc) if anl_fc else 0
            ratios.append(sc); fcr.append(ea)
            print(f"{r['id']:16} {r['airline'][:16]:16} {cap_anl:>7.0%} {shr:>8.1%} {sc:>8.2f} "
                  f"{anl_fc:>10,.0f} {eng:>10,.0f} {ea:>8.2f}")
        except Exception as e:
            print(f"{r['id']:16} ERROR: {str(e)[:50]}")

    def med(xs):
        xs = sorted(xs); n = len(xs)
        return (xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2) if xs else 0
    if ratios:
        print(f"\nQSI-share / analyst-capture: median {med(ratios):.2f}, mean {sum(ratios)/len(ratios):.2f} "
              f"(>1 = engine share too high, the leakage trim)")
        print(f"engine / analyst forecast:   median {med(fcr):.2f}, mean {sum(fcr)/len(fcr):.2f}")
        print("\nRead: a roughly constant share/cap ratio = one scaling on the QSI share fixes it; "
              "if it varies a lot, the QSI scoring itself needs work per route type.")


if __name__ == "__main__":
    main()
