#!/usr/bin/env python3
"""
Avia Solutions - set the access-vs-QSI share against ACTUAL Sabre outturn.
==========================================================================
John's steer: actuals are all in Sabre, on the routes that actually started. So for each LAUNCHED
SJC route we take the truth, not the analyst's plan:
  actual_share = (Sabre SJC -> destination boarded, latest clean year) / (the same-year wide market,
                 the whole Bay Area service area -> destination, destination_market_split).
and put the ENGINE's forecast share next to it. The ratio engine_share / actual_share is the trim:
if it is consistently ~2-2.5 the access model is over-crediting the secondary airport (the Sacramento
problem) and the QSI needs to bite harder; if it is ~1 the share is right where the route flew.

P2P-terminating on both sides (board-point SJC, destination-terminating market), so connecting feed
beyond the hub is excluded from BOTH - this calibrates the SHARE cleanly, separate from the feed layer.

Clean year: the latest of 2025/2024/2023 in which the route actually carried (skips the COVID hole and
any pre-launch year). Routes that never operated in those years are reported as 'no clean outturn'.

RUN where both stores live:
    py -3.12 calibrate_sjc_outturn.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BAY_AREA = ["SFO", "SJC", "OAK"]
CLEAN_YEARS = [2025, 2024, 2023]
MIN_CARRIED = 1500          # below this the route wasn't really operating that year


def _con(db):
    import duckdb
    return duckdb.connect(db, read_only=True)


def _actual_carried(sabre, origin, dest_codes, year):
    dc = ",".join("?" * len(dest_codes))
    sql = (f"SELECT COALESCE(SUM(passengers),0) FROM sabre "
           f"WHERE origin_airport=? AND destination_airport IN ({dc}) AND source_year=?")
    con = _con(sabre)
    try:
        return float(con.execute(sql, [origin] + list(dest_codes) + [year]).fetchone()[0] or 0)
    finally:
        con.close()


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

    import route_forecast as RF, oag_served as OAS, geo_resolve as GEO, sabre_catchment as SC
    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)
    routes = [r for r in json.load(open(a.set))["routes"] if r.get("launched")]

    hdr = (f"{'route':16} {'airline':15} {'yr':>4} {'actual':>8} {'market':>9} "
           f"{'act shr':>8} {'eng shr':>8} {'eng/act':>8}")
    print(hdr); print("-" * len(hdr))
    ratios = []
    for r in routes:
        try:
            # latest clean year the route actually carried
            served_yr = None; actual = 0.0; dest_codes = None
            for y in CLEAN_YEARS:
                yy = y if y in wyear else min(wyear, key=lambda k: abs(k - y))
                wk = sorted([w for w in wyear[yy] if w[5:7] == "05"] or wyear[yy])[-1]
                served = OAS.build_served_index(a.oag, wk)
                dc = GEO.resolve_metro(r["dest"], served_index=served, expand=True)["airports"]
                c = _actual_carried(a.sabre, "SJC", dc, y)
                if c >= MIN_CARRIED:
                    served_yr, actual, dest_codes, week = y, c, dc, wk
                    break
            if served_yr is None:
                print(f"{r['id']:16} {r['airline'][:15]:15} {'   -':>4} no clean outturn"); continue
            split, market, _ = SC.destination_market_split(a.sabre, BAY_AREA, dest_codes, year=served_yr)
            act_shr = (actual / market) if market else 0
            block = 20.0 + _gcd_nm("SJC", r["dest"]) / 7.0
            eng_shr, _ = RF.qsi_capture_share(a.oag, week, "SJC", dest_codes, BAY_AREA,
                                               r["freq"], block)
            ratio = (eng_shr / act_shr) if act_shr else 0
            ratios.append(ratio)
            print(f"{r['id']:16} {r['airline'][:15]:15} {served_yr:>4} {actual:>8,.0f} {market:>9,.0f} "
                  f"{act_shr:>7.1%} {eng_shr:>8.1%} {ratio:>8.2f}")
        except Exception as e:
            print(f"{r['id']:16} ERROR: {str(e)[:48]}")

    def med(xs):
        xs = sorted(xs); n = len(xs)
        return (xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2) if xs else 0
    if ratios:
        print(f"\nengine_share / actual_share: median {med(ratios):.2f}, mean {sum(ratios)/len(ratios):.2f}")
        print("median ~1 = share calibrated to what flew; ~2 = access model over-credits the "
              "secondary, divide the trim in. Watch the spread: if hub routes (HKG/SIN) and short "
              "hub routes (ICN) split, the access-vs-QSI balance is haul-dependent, not one factor.")


if __name__ == "__main__":
    main()
