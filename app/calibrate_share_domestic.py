#!/usr/bin/env python3
"""
Avia Solutions - set the access-vs-QSI share against ACTUAL domestic point-to-point outturn.
============================================================================================
The clean calibration the SJC long-haul set couldn't give: domestic US secondary-vs-hub routes.
On a domestic route the destination-terminating traffic IS the whole route (no beyond-hub feed to
contaminate the share), the secondary airport competes head-to-head with its hub for the identical
market, and the routes are actually flying now. So the SHARE can be read against truth.

For each (secondary airport, its metro competing set, destination metro):
  actual_share = Sabre secondary -> destination boarded (clean year) / the wide market over the whole
                 competing set -> destination (destination_market_split, same year).
  engine_share = route_forecast.qsi_capture_share (the access + QSI catchment choice).
  ratio engine/actual: ~1 right, >1 the access model over-credits the secondary (the Sacramento fault).

The basket: Bay Area (SMF/OAK/SJC vs SFO), LA basin (BUR/SNA/ONT vs LAX), Chicago (MDW vs ORD),
Dallas (DAL vs DFW), Houston (HOU vs IAH), Washington (BWI/DCA vs IAD). Each origin scored to a
handful of big domestic destinations to spread the read across haul lengths and hub strengths.

RUN where both stores live:
    py -3.12 calibrate_share_domestic.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CLEAN_YEARS = [2024, 2023, 2025]
MIN_CARRIED = 3000

# secondary -> (competing metro set, [destination metros])
BASKET = {
    "SMF": (["SMF", "SFO", "OAK", "SJC"], ["JFK", "ORD", "ATL", "DFW", "SEA"]),
    "OAK": (["SMF", "SFO", "OAK", "SJC"], ["JFK", "ORD", "DFW", "DEN"]),
    "SJC": (["SMF", "SFO", "OAK", "SJC"], ["JFK", "ORD", "SEA", "DEN"]),
    "BUR": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["JFK", "ORD", "DFW", "SEA"]),
    "SNA": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["JFK", "ORD", "DFW", "DEN"]),
    "ONT": (["LAX", "BUR", "SNA", "ONT", "LGB"], ["ORD", "DFW", "DEN"]),
    "MDW": (["ORD", "MDW"], ["LGA", "ATL", "DEN", "DFW"]),
    "DAL": (["DFW", "DAL"], ["LGA", "ATL", "DEN", "ORD"]),
    "HOU": (["IAH", "HOU"], ["ATL", "DEN", "ORD"]),
    "BWI": (["IAD", "DCA", "BWI"], ["ORD", "ATL", "DEN"]),
}
DEST_METRO = {  # destination expanded to its terminating metro
    "JFK": ["JFK", "EWR", "LGA"], "LGA": ["JFK", "EWR", "LGA"],
    "ORD": ["ORD", "MDW"], "DFW": ["DFW", "DAL"], "ATL": ["ATL"],
    "SEA": ["SEA"], "DEN": ["DEN"],
}


def _con(db):
    import duckdb
    return duckdb.connect(db, read_only=True)


def _carried(sabre, origin, dest_codes, year):
    dc = ",".join("?" * len(dest_codes))
    con = _con(sabre)
    try:
        return float(con.execute(
            f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE origin_airport=? "
            f"AND destination_airport IN ({dc}) AND source_year=?",
            [origin] + list(dest_codes) + [year]).fetchone()[0] or 0)
    finally:
        con.close()


def _gcd_nm(a, b):
    import airportsdata
    ap = airportsdata.load("IATA")
    ra, rb = ap.get(a), ap.get(b)
    if not ra or not rb or ra["lat"] is None or rb["lat"] is None:
        return 1500.0
    la1, lo1, la2, lo2 = map(math.radians, [ra["lat"], ra["lon"], rb["lat"], rb["lon"]])
    x = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * 6371.0 * math.asin(math.sqrt(x)) / 1.852


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return

    import route_forecast as RF, oag_served as OAS, sabre_catchment as SC
    weeks = OAS.list_weeks(a.oag); wyear = {}
    for w in weeks:
        wyear.setdefault(int(w[:4]), []).append(w)

    def week_for(year):
        yy = year if year in wyear else min(wyear, key=lambda k: abs(k - year))
        return sorted([w for w in wyear[yy] if w[5:7] == "05"] or wyear[yy])[-1]

    hdr = (f"{'route':14} {'yr':>4} {'actual':>8} {'market':>9} {'act shr':>8} {'eng shr':>8} {'eng/act':>8}")
    print(hdr); print("-" * len(hdr))
    rows = []
    for orig, (compet, dests) in BASKET.items():
        for d in dests:
            dest_codes = DEST_METRO.get(d, [d])
            try:
                yr = actual = None
                for y in CLEAN_YEARS:
                    c = _carried(a.sabre, orig, dest_codes, y)
                    if c >= MIN_CARRIED:
                        yr, actual = y, c; break
                if yr is None:
                    continue
                split, market, _ = SC.destination_market_split(a.sabre, compet, dest_codes, year=yr)
                act_shr = (actual / market) if market else 0
                block = 20.0 + _gcd_nm(orig, d) / 7.0
                eng_shr, _ = RF.qsi_capture_share(a.oag, week_for(yr), orig, dest_codes, compet, 14, block)
                ratio = (eng_shr / act_shr) if act_shr else 0
                rows.append(ratio)
                print(f"{orig+'-'+d:14} {yr:>4} {actual:>8,.0f} {market:>9,.0f} "
                      f"{act_shr:>7.1%} {eng_shr:>8.1%} {ratio:>8.2f}")
            except Exception as e:
                print(f"{orig+'-'+d:14} ERROR: {str(e)[:46]}")

    def med(xs):
        xs = sorted(xs); n = len(xs)
        return (xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2) if xs else 0
    if rows:
        print(f"\nengine_share / actual_share over {len(rows)} clean P2P routes: "
              f"median {med(rows):.2f}, mean {sum(rows)/len(rows):.2f}")
        print("median is the trim to fold into the share. A tight spread = one factor does it; a wide "
              "spread = the access-vs-QSI balance needs the knob (logit_scale / qsi_scale), not a flat scalar.")


if __name__ == "__main__":
    main()
