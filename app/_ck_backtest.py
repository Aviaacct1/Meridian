#!/usr/bin/env python3
"""
Avia Solutions - automatic forecast back-test (model vs outturn, across the OAG history).
==========================================================================================
The calibration test John set: run the tool's forecast AS IF standing the year before a new
route launched, then compare it to what the route actually carried, over many routes and every
airline type, to learn where the engine is biased and by how much.

It needs no hand-transcribed route list. The OAG store IS the route inventory: a nonstop
airport pair that has scheduled service in year Y but NOT in years Y-1 and Y-2 is a route that
launched around Y. For each one:

  AS-IF FORECAST  route_engine.assess(origin, dest) using the Y-1 OAG served index and the Y-1
                  Sabre year for propensity (no peeking at post-launch data), prior capture.
  OUTTURN         the EXACT traffic the sector carried in the first full year after launch
                  (Sabre, P2P + all connecting feed, both directions) = sector_traffic.
  TYPE            the operating carrier's OAG category (Mainline / Low Cost) + a light map to
                  FSC / LCC / ULCC / Regional, so residuals segment by airline type.

Output: a per-route table (forecast, outturn, ratio) and a by-type summary (median ratio, the
calibration factor per type), plus a CSV. Runs on the machine that holds both stores:

    py -3.12 backtest.py --oag "C:\\Avia\\oag.duckdb" --sabre "C:\\Avia\\sabre.duckdb"
    py -3.12 backtest.py --oag ... --sabre ... --start-year 2017 --min-gcd 1500 --limit 60 --out backtest_2017.csv

Knobs: --start-year (only routes launching that year; default = all years with Y-1 and Y+1 data),
--min-gcd (km, drop very short sectors), --limit (cap routes for a quick pass), --capture (prior),
--radius-km. Every route is wrapped, so one failure never stops the run.
"""
import argparse, csv, json, os, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Light operating-carrier -> airline-type map (extend freely). OAG carrier_category gives
# Mainline/Low Cost; these split Low Cost into ULCC vs LCC and flag regionals, John's taxonomy.
ULCC = {"FR", "W6", "W9", "WZ", "NK", "F9", "G4", "VY", "U2", "EW", "PC", "DY"}
REGIONAL = {"YV", "OO", "9E", "ZW", "G7", "C5", "EV", "QX", "YX"}
TYPE_BY_CAT = {"LOW COST": "LCC", "LOWCOST": "LCC", "L": "LCC", "MAINLINE": "FSC", "M": "FSC"}

# Per-type stimulation prior: full-service adds little new demand (measured O&D ~= outturn), low-cost
# manufactures it with fares that don't pre-exist, ULCC most of all. These are the stimulation
# educated-guess (John): FSC is held to precision, ULCC is judged on sanity. --stim overrides to flat.
STIM_BY_TYPE = {"FSC": 1.15, "LCC": 1.35, "ULCC": 1.80, "Regional": 1.15}


def _con(db):
    import duckdb
    return duckdb.connect(db, read_only=True)


def weeks_by_year(oag):
    con = _con(oag)
    try:
        rows = con.execute("SELECT DISTINCT week FROM oag ORDER BY week").fetchall()
    finally:
        con.close()
    by = defaultdict(list)
    for (w,) in rows:
        by[int(w[:4])].append(w)
    return dict(by)


def nonstop_pairs(oag, weeks):
    """Directional nonstop pairs flown in any of `weeks`, with the busiest operating carrier and
    its category. Returns {(dep,arr): {carrier, category, freq}}."""
    if not weeks:
        return {}
    con = _con(oag)
    try:
        ph = ",".join("?" * len(weeks))
        rows = con.execute(f"""
            SELECT dep_airport, arr_airport, carrier, ANY_VALUE(carrier_category) cat,
                   SUM(COALESCE(TRY_CAST(frequency AS DOUBLE),1.0)) f
            FROM oag WHERE week IN ({ph}) AND dep_airport IS NOT NULL AND arr_airport IS NOT NULL
            GROUP BY dep_airport, arr_airport, carrier
        """, weeks).fetchall()
    finally:
        con.close()
    best = {}
    for dep, arr, car, cat, f in rows:
        k = (dep, arr)
        if k not in best or f > best[k]["freq"]:
            best[k] = {"carrier": car, "category": (cat or "").strip(), "freq": float(f or 0)}
    return best


def airline_type(carrier, category):
    c = (carrier or "").upper()
    if c in ULCC:
        return "ULCC"
    if c in REGIONAL:
        return "Regional"
    return TYPE_BY_CAT.get((category or "").upper().strip(), "FSC")


# Domestic GDS coverage is thin in these countries (most domestic tickets sold off-GDS), so Sabre
# under-reads domestic O&D there and those routes test COVERAGE, not the demand engine. Excluded from
# the calibration run by default; international routes to/from them are fine (GDS covers international).
THIN_GDS = {"CN", "IN", "ID", "VN", "BD", "PK", "NP", "MM", "LK", "KH", "LA", "PH",
            # ex-Soviet domestic books off-GDS too (Russia-domestic reads ~0.01 like China-domestic)
            "RU", "BY", "KZ", "UZ", "AZ", "GE", "AM", "MD", "TJ", "TM", "KG", "UA",
            # Latin domestic also heavily off-GDS (Brazil/Mexico low-cost direct booking)
            "BR", "MX"}
# GDS barely covers these AT ALL, so exclude on ANY endpoint, not just domestic (Cuba: embargo-era
# direct booking; the market is invisible to Sabre even on international sectors like HAV-CLT = 0.01)
COVERAGE_BLACKHOLE = {"CU"}
REGION = {
    "GB": "EU", "IE": "EU", "FR": "EU", "DE": "EU", "ES": "EU", "IT": "EU", "NL": "EU", "BE": "EU",
    "CH": "EU", "AT": "EU", "PT": "EU", "SE": "EU", "NO": "EU", "DK": "EU", "FI": "EU", "PL": "EU",
    "CZ": "EU", "GR": "EU", "RO": "EU", "HU": "EU", "HR": "EU", "RS": "EU", "BG": "EU", "SK": "EU",
    "UA": "EU", "IS": "EU", "LU": "EU", "EE": "EU", "LV": "EU", "LT": "EU", "CY": "EU", "MT": "EU",
    "US": "NA", "CA": "NA",
    "MX": "LATAM", "BR": "LATAM", "AR": "LATAM", "CL": "LATAM", "CO": "LATAM", "PE": "LATAM",
    "EC": "LATAM", "BO": "LATAM", "PY": "LATAM", "UY": "LATAM", "VE": "LATAM", "PA": "LATAM",
    "CR": "LATAM", "GT": "LATAM", "DO": "LATAM", "CU": "LATAM", "JM": "LATAM", "BZ": "LATAM",
    "HN": "LATAM", "NI": "LATAM", "SV": "LATAM", "TT": "LATAM",
    "AE": "MEA", "SA": "MEA", "QA": "MEA", "IL": "MEA", "TR": "MEA", "JO": "MEA", "KW": "MEA",
    "OM": "MEA", "BH": "MEA", "LB": "MEA", "EG": "MEA",
    "ZA": "AFR", "KE": "AFR", "NG": "AFR", "ET": "AFR", "MA": "AFR", "TN": "AFR", "GH": "AFR",
    "TZ": "AFR", "MU": "AFR",
    "JP": "APAC", "KR": "APAC", "AU": "APAC", "NZ": "APAC", "SG": "APAC", "HK": "APAC", "TW": "APAC",
    "TH": "APAC", "MY": "APAC",
    "CN": "CN", "IN": "IN", "ID": "ID", "VN": "VN",
}
_AP_BT = None


def _country(code):
    global _AP_BT
    if _AP_BT is None:
        import airportsdata
        _AP_BT = airportsdata.load("IATA")
    r = _AP_BT.get((code or "").upper())
    return r["country"] if r else None


def is_thin_domestic(dep, arr):
    """A route Sabre can't size: a domestic sector inside a thin-GDS country, or any sector touching a
    coverage black hole (Cuba). These test data completeness, not the demand engine."""
    cd, ca = _country(dep), _country(arr)
    if cd in COVERAGE_BLACKHOLE or ca in COVERAGE_BLACKHOLE:
        return True
    return cd is not None and cd == ca and cd in THIN_GDS


def route_region(dep, arr):
    cd, ca = _country(dep), _country(arr)
    rd, ra = REGION.get(cd, "OTH"), REGION.get(ca, "OTH")
    return rd if rd == ra else "INTL"


def discover_new_routes(oag, start_year=None, min_freq=3.0):
    """New nonstop markets: a pair flown in year Y but not in Y-1 or Y-2 (genuinely new service).
    Deduped to one direction per market. Returns list of dicts {dep,arr,carrier,category,type,year}."""
    wby = weeks_by_year(oag)
    years = sorted(wby)
    out = []
    seen = set()
    targets = [start_year] if start_year else years
    for Y in targets:
        if Y not in wby or (Y - 1) not in wby or (Y - 2) not in wby:
            continue
        cur = nonstop_pairs(oag, wby[Y])
        prev = set(nonstop_pairs(oag, wby[Y - 1])) | set(nonstop_pairs(oag, wby[Y - 2]))
        for (dep, arr), info in cur.items():
            if info["freq"] < min_freq:
                continue
            if (dep, arr) in prev or (arr, dep) in prev:
                continue                                   # not new (existed before)
            mk = frozenset((dep, arr))
            if mk in seen:
                continue
            seen.add(mk)
            out.append({"dep": dep, "arr": arr, "carrier": info["carrier"],
                        "category": info["category"],
                        "type": airline_type(info["carrier"], info["category"]),
                        "year": Y, "freq": round(info["freq"], 1)})
    return out


def gcd_km(oag, dep, arr):
    con = _con(oag)
    try:
        r = con.execute("SELECT ANY_VALUE(TRY_CAST(gcd_km AS DOUBLE)) FROM oag "
                        "WHERE dep_airport=? AND arr_airport=?", [dep, arr]).fetchone()
        return float(r[0]) if r and r[0] else None
    finally:
        con.close()


def sector_traffic(db, a, b, year):
    """EXACT pax flown on the a-b sector (both directions) in a travel year: every itinerary where
    a and b are consecutive in the routing (P2P + connecting feed). Lifted from validate_sjc."""
    import duckdb
    def adj(x, y):
        c1 = "NULLIF(connecting_airport1,'')"; c2 = "NULLIF(connecting_airport2,'')"; c3 = "NULLIF(connecting_airport3,'')"
        return (f"(origin_airport='{x}' AND COALESCE({c1},destination_airport)='{y}')"
                f" OR (connecting_airport1='{x}' AND COALESCE({c2},destination_airport)='{y}')"
                f" OR (connecting_airport2='{x}' AND COALESCE({c3},destination_airport)='{y}')"
                f" OR (connecting_airport3='{x}' AND destination_airport='{y}')")
    con = duckdb.connect(db, read_only=True)
    try:
        where = f"({adj(a, b)}) OR ({adj(b, a)})"
        sql = f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE source_year={int(year)} AND ({where})"
        return float(con.execute(sql).fetchone()[0] or 0)
    finally:
        con.close()


def p2p_traffic(db, a, b, year):
    """PURE point-to-point pax (both directions): true origin a, true destination b, NO connecting
    airport = the local O&D market, the like-for-like comparison for a P2P forecast (sector_traffic
    additionally counts all connecting feed, which a P2P-only forecast can never match)."""
    import duckdb
    con = duckdb.connect(db, read_only=True)
    try:
        sql = (f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE source_year={int(year)} "
               f"AND ((origin_airport='{a}' AND destination_airport='{b}') "
               f"OR (origin_airport='{b}' AND destination_airport='{a}')) "
               f"AND (connecting_airport1 IS NULL OR TRIM(connecting_airport1)='')")
        return float(con.execute(sql).fetchone()[0] or 0)
    finally:
        con.close()


def _served_for_week(oag, week, cache):
    if week not in cache:
        import oag_served as OAS
        cache[week] = OAS.build_served_index(oag, week)
    return cache[week]


def _operated(oag, week, dep, arr):
    """The route's ACTUAL operated annual capacity (both directions), weekly frequency (dep->arr)
    and great-circle km in an OAG week - the real aircraft/frequency the carrier flew, used to cap
    the carried forecast like-for-like with outturn."""
    import duckdb
    con = duckdb.connect(oag, read_only=True)
    try:
        r = con.execute(
            "SELECT COALESCE(SUM(s*f),0), "
            "COALESCE(SUM(CASE WHEN dep_airport=? THEN f ELSE 0 END),0), AVG(g) FROM ("
            "SELECT dep_airport, COALESCE(TRY_CAST(seats_total AS DOUBLE),TRY_CAST(seats AS DOUBLE),0) s, "
            "COALESCE(TRY_CAST(frequency AS DOUBLE),1) f, TRY_CAST(gcd_km AS DOUBLE) g FROM oag "
            "WHERE week=? AND ((dep_airport=? AND arr_airport=?) OR (dep_airport=? AND arr_airport=?)))",
            [dep, week, dep, arr, arr, dep]).fetchone()
        return float(r[0] or 0) * 52, float(r[1] or 0), float(r[2] or 0)
    finally:
        con.close()


def asif_forecast(route, oag, sabre, served_cache, wby, stimulation=1.15, radius_km=220.0, outturn_offset=1,
                  lcc_cat=1.0, feed_cfg=None):
    """The tool's forecast, standing the year before launch, via the rebuilt connected loop
    (route_forecast): measured wide market (Y-1 Sabre) x QSI share (Y-1 OAG + the proposed nonstop)
    x stimulation, capped by the route's ACTUAL operated capacity (OAG launch year)."""
    import route_forecast as RF, geo_resolve as GEO, route_engine as RE, oag_served as OAS
    import sabre_catchment as SC
    Y = route["year"]; dep = route["dep"]; arr = route["arr"]
    asif_week = sorted(wby.get(Y - 1) or wby.get(Y))[0]
    served = _served_for_week(oag, asif_week, served_cache)
    dm = GEO.resolve_metro(arr, served_index=served, expand=True)
    dest_codes = dm["airports"]
    ap = RE._airports(); o = ap.get(dep)
    sset = OAS.served_set(served) if served else None
    # cap at the COMPARISON year's (Y+1, the first full year) actual deployed capacity - the real
    # aircraft and frequency flown, from OAG - so the forecast is bounded by the same metal as the
    # outturn it's graded against (an ATR42 route can't carry an A320 forecast).
    cap_week = sorted(wby.get(Y + outturn_offset) or wby.get(Y + 1) or wby.get(Y) or wby.get(Y - 1))[0]
    annual_cap, freq, gcd = _operated(oag, cap_week, dep, arr)
    # haul-scaled catchment radius: tight for short sectors, wide for long (same rule the engine uses
    # internally for the share), so the competing-airport set and the share stay consistent
    # LCC/ULCC draw a wider catchment (price-driven pax drive further for a cheap fare); widen the
    # competing-airport set AND the engine's internal radius by the same factor so they stay consistent.
    cmult = lcc_cat if route.get("type") in ("LCC", "ULCC") else 1.0
    rad = (RF.haul_radius_km(gcd) if gcd else radius_km) * cmult
    competing = [r["iata"] for r in RE.competing_airports(o, rad, sset, True)] if o else [dep]
    freq = max(int(round(freq)), 1)
    block = 20.0 + (gcd / 1.852) / 7.0 if gcd else 540.0
    stim = stimulation if stimulation is not None else STIM_BY_TYPE.get(route.get("type"), 1.2)
    # organic market growth: base is Y-1, outturn is Y+1, so project the market forward 2 years at its
    # OWN measured CAGR (Y-3 -> Y-1), clamped sane. A fast-growing market (Poland) is under-sized
    # otherwise; a real forecast projects growth, we just weren't feeding the term.
    def _mkt(yr):
        try:
            return SC.destination_market_split(sabre, competing, dest_codes, year=yr)[1] or 0.0
        except Exception:
            return 0.0
    m1, m3 = _mkt(Y - 1), _mkt(Y - 3)
    growth = ((m1 / m3) ** 0.5 - 1.0) if (m1 > 0 and m3 > 0) else 0.04
    # ceiling 20%/yr (44% over the 2yr base-to-outturn gap): above that a measured CAGR is a burst
    # that won't sustain. Not tuned finer because the haul bands are too small-n to calibrate against.
    growth = max(min(growth, 0.20), -0.05)
    r = RF.forecast(sabre, oag, asif_week, dep, dest_codes, competing, year=Y - 1, freq=freq,
                    block_min=block, stimulation=stim, dest_airport=arr, airline=route.get("carrier"),
                    growth=growth, growth_years=1 + outturn_offset,
                    annual_capacity=(annual_cap or None), catchment_mult=cmult, feed_cfg=feed_cfg)
    hub = (served.get("airports", {}).get(arr, {}) or {}).get("dest_count", 0)
    return {"forecast_pax": r["carried_forecast"], "market": r["natural_market"],
            "share": r["qsi_share"], "captured": r["captured_demand"], "spill": r["spill"],
            "total_demand": r.get("total_demand", 0), "feed_beyond": r.get("feed_beyond", 0),
            "feed_behind": r.get("feed_behind", 0),
            "capacity": annual_cap or 0, "natural": r["natural_market"], "propensity": r["qsi_share"],
            "propensity_basis": "qsi-share", "dest_count": hub, "gcd_km": gcd or 0}


def main():
    ap = argparse.ArgumentParser(description="Automatic forecast back-test over the OAG/Sabre history.")
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--start-year", type=int, default=None, help="only routes launching this year (default all)")
    ap.add_argument("--min-gcd", type=float, default=0.0, help="drop sectors shorter than this (km)")
    ap.add_argument("--min-freq", type=float, default=3.0, help="min weekly departures to count as a route")
    ap.add_argument("--limit", type=int, default=None, help="cap number of routes (quick pass)")
    ap.add_argument("--capture", type=float, default=0.30, help="base leaked-recovery rate")
    ap.add_argument("--stim", type=float, default=None,
                    help="flat stimulation override; default None = per-type prior (FSC 1.15 .. ULCC 1.8)")
    ap.add_argument("--radius-km", type=float, default=220.0)
    ap.add_argument("--min-outturn", type=int, default=3000,
                    help="min P2P outturn to enter the calibration stats (drops tiny-route noise)")
    ap.add_argument("--mature", action="store_true",
                    help="grade against Y2 (second full year, less launch-ramp noise) instead of Y1")
    ap.add_argument("--y3", action="store_true", help="grade against Y3 (most matured)")
    ap.add_argument("--keep-thin", action="store_true",
                    help="keep thin-GDS domestic routes (China/India domestic etc); off by default")
    ap.add_argument("--regions", default=None,
                    help="comma list to keep, e.g. EU,NA,LATAM,INTL,APAC,MEA,AFR (default all)")
    ap.add_argument("--out", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--lcc-cat", type=float, default=1.0,
                    help="catchment radius multiplier for LCC/ULCC (price pax drive further); 1.0 = off")
    ap.add_argument("--feed-fix", action="store_true",
                    help="hub-aware feed: zero P2P carriers, scale capture by origin/hub dominance")
    ap.add_argument("--feed-behind-cap", type=float, default=0.10, help="behind base capture under --feed-fix")
    ap.add_argument("--feed-dom-gain", type=float, default=1.0, help="dominance gain under --feed-fix")
    ap.add_argument("--feed-dom-floor", type=float, default=0.5, help="dominance floor under --feed-fix")
    a = ap.parse_args()
    feed_cfg = ({"behind_cap": a.feed_behind_cap, "dom_gain": a.feed_dom_gain,
                 "dom_floor": a.feed_dom_floor} if a.feed_fix else None)
    keep_regions = set(s.strip().upper() for s in a.regions.split(",")) if a.regions else None
    offset = 3 if a.y3 else 2 if a.mature else 1     # grade against Y+offset (Y1 default, Y2/Y3 matured)

    if not os.path.exists(a.oag):
        print(f"OAG store not found: {a.oag}"); return
    if not os.path.exists(a.sabre):
        print(f"Sabre store not found: {a.sabre}"); return

    wby = weeks_by_year(a.oag)
    print(f"OAG years: {sorted(wby)}")
    routes = discover_new_routes(a.oag, a.start_year, a.min_freq)
    print(f"discovered {len(routes)} new nonstop routes "
          f"{'in '+str(a.start_year) if a.start_year else 'across the history'}")
    if a.min_gcd:
        kept = []
        for r in routes:
            g = gcd_km(a.oag, r["dep"], r["arr"])
            r["gcd_km"] = g
            if g is None or g >= a.min_gcd:
                kept.append(r)
        routes = kept
        print(f"{len(routes)} after min-gcd {a.min_gcd:.0f} km")
    # survival filter: a route not still flown the year after launch is noise (a collapsed carrier,
    # a one-season trial). Require the pair in the Y+1 OAG weeks where we have them.
    yplus = {r["year"] + offset for r in routes}
    surv_pairs = {y: set(nonstop_pairs(a.oag, wby[y])) for y in yplus if y in wby}
    surv = []
    for r in routes:
        ps = surv_pairs.get(r["year"] + offset)
        if ps is None or (r["dep"], r["arr"]) in ps or (r["arr"], r["dep"]) in ps:
            surv.append(r)
    print(f"{len(surv)} survived into year+1 (dropped {len(routes) - len(surv)} that stopped flying)")
    routes = surv
    # COVERAGE filter: drop thin-GDS domestic (China/India domestic etc) where Sabre under-reads the
    # market - those test coverage, not the demand engine, and swamp the calibration. Then region filter.
    if not a.keep_thin:
        before = len(routes)
        routes = [r for r in routes if not is_thin_domestic(r["dep"], r["arr"])]
        print(f"{len(routes)} after dropping thin-GDS domestic (removed {before - len(routes)}; "
              f"--keep-thin to include)")
    if keep_regions:
        routes = [r for r in routes if route_region(r["dep"], r["arr"]) in keep_regions]
        print(f"{len(routes)} in regions {sorted(keep_regions)}")
    if a.limit:
        routes = routes[:a.limit]

    HUB_THRESHOLD = 40       # dest serves >= this many nonstop destinations -> a hub (feed-heavy)
    MIN_OUTTURN = a.min_outturn   # ignore sub-material sectors in the ratio stats (default 3000)
    served_cache = {}
    rows = []
    t0 = time.time()
    hdr = (f"{'route':12} {'type':9} {'yr':>4} {'forecast':>10} {'p2p_out':>9} {'fc/p2p':>7} "
           f"{'tot_out':>9} {'fc/tot':>7}  carrier")
    print("\n" + hdr); print("-" * (len(hdr) + 6))
    for i, r in enumerate(routes):
        try:
            p2p = p2p_traffic(a.sabre, r["dep"], r["arr"], r["year"] + offset)
            if p2p < MIN_OUTTURN:
                continue     # skip sub-material commuter/thin routes entirely (cleaner scroll + faster)
            out = sector_traffic(a.sabre, r["dep"], r["arr"], r["year"] + offset)
            f = asif_forecast(r, a.oag, a.sabre, served_cache, wby, a.stim, a.radius_km, offset, a.lcc_cat, feed_cfg)
            # forecast_pax is now the TOTAL (P2P + connecting feed) capped at deployed capacity; grade it
            # vs the TOTAL outturn (sector_traffic). The P2P-engine test stays clean on captured vs P2P.
            graded = f["forecast_pax"]
            ratio = (graded / out) if out else None
            ratio_p2p = (f["captured"] / p2p) if p2p else None
            hub = bool((f.get("dest_count") or 0) >= HUB_THRESHOLD)
            rows.append({"route": f"{r['dep']}-{r['arr']}", "dep": r["dep"], "arr": r["arr"],
                         "dep_country": _country(r["dep"]) or "", "arr_country": _country(r["arr"]) or "",
                         "type": r["type"], "year": r["year"],
                         "region": route_region(r["dep"], r["arr"]),
                         "carrier": r["carrier"], "hub_dest": hub, "forecast_pax": round(graded),
                         "captured_uncapped": round(f["captured"]), "capacity": round(f.get("capacity") or 0),
                         "feed_beyond": round(f.get("feed_beyond") or 0), "feed_behind": round(f.get("feed_behind") or 0),
                         "p2p_outturn": round(p2p), "fc_over_p2p": round(ratio_p2p, 3) if ratio_p2p else "",
                         "outturn_pax": round(out), "fc_over_out": round(rati