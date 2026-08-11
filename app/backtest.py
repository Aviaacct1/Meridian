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
    # R3: reuse one read-only base connection per store path (cursor per call). See db_registry.
    from db_registry import con_ro
    return con_ro(db)


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
    When Y-2 is NOT loaded (the store skips the Covid years, so 2024 launches have no 2022 and
    2016 launches no 2014), screen on Y-1 alone rather than dropping the whole year, and TAG a
    route that flew in any loaded pre-gap year as reinstated=True (a post-Covid restart behaves
    differently from a genuine launch - it has history and an established brand).
    Deduped to one direction per market. Returns dicts {dep,arr,carrier,category,type,year,
    freq,reinstated}."""
    wby = weeks_by_year(oag)
    years = sorted(wby)
    out = []
    seen = set()
    targets = [start_year] if start_year else years
    for Y in targets:
        if Y not in wby or (Y - 1) not in wby:
            continue
        cur = nonstop_pairs(oag, wby[Y])
        prev = set(nonstop_pairs(oag, wby[Y - 1]))
        if (Y - 2) in wby:
            prev |= set(nonstop_pairs(oag, wby[Y - 2]))
        # pre-gap reference for reinstatement tagging: loaded years well before Y (excluding
        # Y-1/Y-2 which already screen). For 2024/2025 this is the pre-Covid record.
        pre = set()
        for py in (y for y in years if y <= Y - 3):
            pre |= set(nonstop_pairs(oag, wby[py]))
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
                        "year": Y, "freq": round(info["freq"], 1),
                        "reinstated": (dep, arr) in pre or (arr, dep) in pre})
    return out


def gcd_km(oag, dep, arr):
    con = _con(oag)
    try:
        r = con.execute("SELECT ANY_VALUE(TRY_CAST(gcd_km AS DOUBLE)) FROM oag "
                        "WHERE dep_airport=? AND arr_airport=?", [dep, arr]).fetchone()
        return float(r[0]) if r and r[0] else None
    finally:
        con.close()


# R1: optional Sabre pre-aggregation. When _PREAGG points at a valid preagg store, the four hot
# per-route Sabre scans become point lookups on the small derived tables. None -> the original full
# scans (default). Set once per process in main() (and per worker under the R2 pool).
_PREAGG = None


def _preagg_store():
    if not _PREAGG:
        return None
    import preagg
    return _PREAGG if preagg.available(_PREAGG) else None


def sector_traffic(db, a, b, year):
    """EXACT pax flown on the a-b sector (both directions) in a travel year: every itinerary where
    a and b are consecutive in the routing (P2P + connecting feed). Lifted from validate_sjc."""
    pa = _preagg_store()
    if pa:
        import preagg
        if preagg.has_sector(pa):        # optional table; full-scan below if it wasn't built
            return preagg.sector_traffic(pa, a, b, year)
    def adj(x, y):
        c1 = "NULLIF(connecting_airport1,'')"; c2 = "NULLIF(connecting_airport2,'')"; c3 = "NULLIF(connecting_airport3,'')"
        return (f"(origin_airport='{x}' AND COALESCE({c1},destination_airport)='{y}')"
                f" OR (connecting_airport1='{x}' AND COALESCE({c2},destination_airport)='{y}')"
                f" OR (connecting_airport2='{x}' AND COALESCE({c3},destination_airport)='{y}')"
                f" OR (connecting_airport3='{x}' AND destination_airport='{y}')")
    con = _con(db)
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
    pa = _preagg_store()
    if pa:
        import preagg
        return preagg.p2p_traffic(pa, a, b, year)
    con = _con(db)
    try:
        sql = (f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE source_year={int(year)} "
               f"AND ((origin_airport='{a}' AND destination_airport='{b}') "
               f"OR (origin_airport='{b}' AND destination_airport='{a}')) "
               f"AND (connecting_airport1 IS NULL OR TRIM(connecting_airport1)='')")
        return float(con.execute(sql).fetchone()[0] or 0)
    finally:
        con.close()


def route_avg_fare(db, a, b, year):
    """Passenger-weighted average PURE P2P fare (both directions) in a year - the achieved yield of a
    launch, used to set the induced/stimulation fare in the economics. None if no P2P pax."""
    con = _con(db)
    try:
        sql = (f"SELECT COALESCE(SUM(passengers*avg_total_fare_usd),0), COALESCE(SUM(passengers),0) "
               f"FROM sabre WHERE source_year={int(year)} "
               f"AND ((origin_airport='{a}' AND destination_airport='{b}') "
               f"OR (origin_airport='{b}' AND destination_airport='{a}')) "
               f"AND (connecting_airport1 IS NULL OR TRIM(connecting_airport1)='')")
        rev, pax = con.execute(sql).fetchone()
        return round(float(rev) / float(pax), 2) if pax else None
    finally:
        con.close()


def _served_for_week(oag, week, cache):
    if week not in cache:
        import oag_served as OAS
        cache[week] = OAS.build_served_index(oag, week)
    return cache[week]


# Season lengths for annualising the two OAG snapshots (John's definition: summer Apr-mid Oct,
# winter mid Oct-end March). The store holds a summer (~May) and a winter (~Oct) pull per year;
# annualising a single pull x52 over-credits a seasonal route a full year at its peak schedule, which
# reads as a low-load-factor "empty plane" in the back-test. Blending the two fixes the cap and the LF.
_SUMMER_WEEKS = 28.0
_WINTER_WEEKS = 24.0


def _week_season(wk):
    """'S' if the snapshot week is in the summer season (Apr-Sep -> the ~May pull), else 'W' (the
    ~Oct pull = winter schedule). Snapshots are May and October, so month decides it cleanly."""
    try:
        m = int(str(wk)[5:7])
    except Exception:
        return "S"
    return "S" if 4 <= m <= 9 else "W"


def _operated(oag, weeks, dep, arr):
    """The route's ACTUAL operated annual capacity (both directions), a representative weekly frequency
    (dep->arr) and great-circle km, blended across the year's seasonal OAG snapshots.

    `weeks` is the list of the outturn year's snapshot weeks (typically a summer and a winter pull; a
    bare string is accepted for back-compat). Annual capacity = summer weekly cap x _SUMMER_WEEKS +
    winter weekly cap x _WINTER_WEEKS, so a route absent from the winter pull is not credited a winter
    it never flew. If the store holds only ONE season for the year we can't infer the other, so we fall
    back to the old behaviour (that pull x 52). Frequency for the QSI share is the peak operating
    season's weekly frequency (the service level the airline actually offers when it operates)."""
    if isinstance(weeks, str):
        weeks = [weeks]
    weeks = weeks or []
    import re as _re
    # each OAG row is one dated departure (frequency=1, seats_total = per-departure seats), so annual
    # capacity is the SUM of seats_total over the year's departures. Classify the label granularities and
    # NEVER double-count: prefer the MONTHLY labels (a true full-year sum); fall back to the WEEKLY snapshots
    # (that week's seats x operating weeks) for routes/years the store only holds as snapshots (NA pre-2019,
    # 2023+). Exclude the annual (YYYY) and half-year (YYYY-Hn) rollups so no granularity is summed twice.
    monthly = [w for w in weeks if _re.fullmatch(r"\d{4}-\d{2}(p\d{2})?", w)]
    weekly = [w for w in weeks if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", w)]
    con = _con(oag)
    try:
        # 1) MONTHLY full-year sum (Euro/Asia 2015-2019): annual = SUM(seats_total), no x52, no season blend
        if monthly:
            ph = ",".join("?" * len(monthly))
            r = con.execute(
                f"SELECT COALESCE(SUM(TRY_CAST(seats_total AS DOUBLE)),0), AVG(TRY_CAST(gcd_km AS DOUBLE)), "
                f"COUNT(DISTINCT substr(week,1,7)), "
                f"COALESCE(SUM(CASE WHEN dep_airport=? THEN TRY_CAST(frequency AS DOUBLE) ELSE 0 END),0) "
                f"FROM oag WHERE week IN ({ph}) AND service_type='J' "
                f"AND ((dep_airport=? AND arr_airport=?) OR (dep_airport=? AND arr_airport=?))",
                [dep] + monthly + [dep, arr, arr, dep]).fetchone()
            cap_m = float(r[0] or 0.0)
            if cap_m > 0:
                gcd = float(r[1]) if r[1] is not None else 0.0
                nmo = int(r[2] or 0)
                ann_deps = float(r[3] or 0.0)
                if 0 < nmo < 12:                          # part-year (e.g. 2019 to Nov) -> full-year equivalent
                    cap_m *= 12.0 / nmo
                    ann_deps *= 12.0 / nmo
                return cap_m, ann_deps / 52.0, gcd, ("annual" if nmo >= 11 else "seasonal")
        # 2) WEEKLY snapshots (NA pre-2019, all 2023+): that week's seats x operating weeks, seasonal blend
        cap = {"S": 0.0, "W": 0.0}
        frq = {"S": 0.0, "W": 0.0}
        seen = set()
        gcds = []
        for wk in weekly:
            r = con.execute(
                "SELECT COALESCE(SUM(TRY_CAST(seats_total AS DOUBLE)),0), "
                "COALESCE(SUM(CASE WHEN dep_airport=? THEN TRY_CAST(frequency AS DOUBLE) ELSE 0 END),0), "
                "AVG(TRY_CAST(gcd_km AS DOUBLE)) FROM oag WHERE week=? "
                "AND ((dep_airport=? AND arr_airport=?) OR (dep_airport=? AND arr_airport=?))",
                [dep, wk, dep, arr, arr, dep]).fetchone()
            s = _week_season(wk)
            seen.add(s)
            cap[s] = max(cap[s], float(r[0] or 0))       # busiest week in that season's snapshot
            frq[s] = max(frq[s], float(r[1] or 0))
            if r[2] is not None:
                gcds.append(float(r[2]))
        if "S" in seen and "W" in seen:
            annual_cap = cap["S"] * _SUMMER_WEEKS + cap["W"] * _WINTER_WEEKS
            service = "annual" if (cap["S"] > 0 and cap["W"] > 0) else \
                      "summer" if cap["S"] > 0 else "winter" if cap["W"] > 0 else "na"
        else:                                            # only one season snapshot: annualise x52
            annual_cap = (cap["S"] or cap["W"]) * 52.0
            service = "unknown"
        freq = frq["S"] if cap["S"] >= cap["W"] else frq["W"]
        gcd = (sum(gcds) / len(gcds)) if gcds else 0.0
        return annual_cap, freq, gcd, service
    finally:
        con.close()


def asif_forecast(route, oag, sabre, served_cache, wby, stimulation=1.15, radius_km=220.0, outturn_offset=1,
                  lcc_cat=1.0, feed_cfg=None, market_factor=None, season_grade=False, induced_floor=False,
                  nonstop_share=False, decompose=False, airport_capture=1.0):
    """The tool's forecast, standing the year before launch, via the rebuilt connected loop
    (route_forecast): measured wide market (Y-1 Sabre) x QSI share (Y-1 OAG + the proposed nonstop)
    x stimulation, capped by the route's ACTUAL operated capacity (OAG launch year)."""
    import route_forecast as RF, geo_resolve as GEO, route_engine as RE, oag_served as OAS, od_source
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
    cap_weeks = wby.get(Y + outturn_offset) or wby.get(Y + 1) or wby.get(Y) or wby.get(Y - 1) or []
    annual_cap, freq, gcd, service = _operated(oag, cap_weeks, dep, arr)   # blends the seasonal snapshots
    # haul-scaled catchment radius: tight for short sectors, wide for long (same rule the engine uses
    # internally for the share), so the competing-airport set and the share stay consistent
    # LCC/ULCC draw a wider catchment (price-driven pax drive further for a cheap fare); widen the
    # competing-airport set AND the engine's internal radius by the same factor so they stay consistent.
    cmult = lcc_cat if route.get("type") in ("LCC", "ULCC") else 1.0
    rad = (RF.haul_radius_km(gcd) if gcd else radius_km) * cmult
    competing = [r["iata"] for r in RE.competing_airports(o, rad, sset, True)] if o else [dep]
    freq = max(int(round(freq)), 1)
    block = 20.0 + (gcd / 1.852) / 7.0 if gcd else 540.0
    # Engine V2 calibration discipline: the QSI feed runs at the route's ACTUAL flown departure
    # time (from the wave cache), so the calibrated model re-solves to the real outturn. Routes
    # with no flown schedule fall back to the V1 flat feed for that route (dep_time_mins None).
    if feed_cfg is not None and feed_cfg.get("qsi_feed"):
        fl = None
        try:
            boards = feed_cfg.get("_boards")
            if boards is None:
                from wave_cache import CacheBoards
                wc = feed_cfg.get("wave_cache")
                if wc and os.path.exists(wc):
                    boards = CacheBoards(wc)
                    feed_cfg["_boards"] = boards
            if boards is not None and hasattr(boards, "flown"):
                fl = boards.flown(dep, arr, Y, route.get("carrier"))
        except Exception:
            fl = None
        if fl and fl.get("dep_mins") is not None:
            feed_cfg["dep_time_mins"] = fl["dep_mins"]
            feed_cfg["flying_mins"] = fl.get("flying") or block
            feed_cfg["route_freq"] = fl.get("freq") or freq
        else:
            feed_cfg["dep_time_mins"] = None
            feed_cfg["_qsi_no_flown"] = feed_cfg.get("_qsi_no_flown", 0) + 1
    stim = stimulation if stimulation is not None else STIM_BY_TYPE.get(route.get("type"), 1.2)
    # organic market growth: base is Y-1, outturn is Y+1, so project the market forward 2 years at its
    # OWN measured CAGR (Y-3 -> Y-1), clamped sane. A fast-growing market (Poland) is under-sized
    # otherwise; a real forecast projects growth, we just weren't feeding the term.
    def _mkt(yr):
        try:
            return od_source.market_split(sabre, competing, dest_codes, year=yr)[1] or 0.0
        except Exception:
            return 0.0
    m1, m3 = _mkt(Y - 1), _mkt(Y - 3)
    growth = ((m1 / m3) ** 0.5 - 1.0) if (m1 > 0 and m3 > 0) else 0.04
    # ceiling 20%/yr (44% over the 2yr base-to-outturn gap): above that a measured CAGR is a burst
    # that won't sustain. Not tuned finer because the haul bands are too small-n to calibrate against.
    growth = max(min(growth, 0.20), -0.05)
    # market_factor True = resolve the trim table by airline type (FSC/ULCC 0.85, LCC 0.95); a table
    # passes through as-is; None/False = off.
    _mf = RF.market_factor_for(route.get("type")) if market_factor is True else market_factor
    # C1 SEASON GRADE: a one-season route ('S'/'W' from the OAG service pattern) is forecast in its
    # season, so the demand is the season's share of the annual O&D, matched to its season-only outturn.
    # Capacity is already the operated seasonal cap (annual_cap), so season_weeks is not needed here.
    graded_season = ""; season_share = 1.0
    if season_grade and service in ("summer", "winter"):
        import seasonality_engine as SE
        graded_season = service       # _operated tags one-season routes "summer"/"winter"
        _g = gcd or 0
        _rt = "intra_european" if _g < 1500 else "transatlantic" if _g < 6000 else "europe_asia"
        _ds = "leisure" if route.get("type") in ("LCC", "ULCC") else "mixed"
        season_share = SE.season_share_for(graded_season, route_type=_rt, demand_split=_ds)
    r = RF.forecast(sabre, oag, asif_week, dep, dest_codes, competing, year=Y - 1, freq=freq,
                    block_min=block, stimulation=stim, dest_airport=arr, airline=route.get("carrier"),
                    growth=growth, growth_years=1 + outturn_offset,
                    annual_capacity=(annual_cap or None), catchment_mult=cmult, feed_cfg=feed_cfg,
                    market_factor=_mf, season=(graded_season or "annual"), season_share=season_share,
                    airline_type=route.get("type"), induced_floor=induced_floor,
                    airport_capture=airport_capture)
    hub = (served.get("airports", {}).get(arr, {}) or {}).get("dest_count", 0)
    _p2p_share = None
    if nonstop_share:   # forecast-time connecting-heaviness proxy (Y-1 nonstop O&D fraction)
        try:
            _p2p_share = round(SC.nonstop_share(sabre, competing, dest_codes, Y - 1)[0], 4)
        except Exception:
            _p2p_share = None
    # T3 ERROR DECOMPOSITION: each multiplicative leg of the forecast, so the analysis can attribute the
    # log-error variance (fc/actual) to market measurement, growth, share, stimulation, feed, capacity.
    decomp = None
    if decompose:
        try:
            _mkt_out = _mkt(Y + outturn_offset)
        except Exception:
            _mkt_out = None
        decomp = {
            "mkt_asif": round(m1),                                   # measured market, Y-1 (raw O&D)
            "mkt_outturn": round(_mkt_out) if _mkt_out else None,    # measured market, outturn year (raw)
            "growth_applied": round((1.0 + growth) ** (1 + outturn_offset), 4),
            "stim": round(stim, 3),
            "share": round(r.get("qsi_share") or 0, 4),
            "dshare": round(r.get("dest_share") or 0, 4),
            "coverage": round(r.get("coverage_gross_up") or 0, 3),
            "captured": round(r.get("captured_demand") or 0),        # P2P forecast (pre-feed, pre-cap)
            "feed_fc": round(r.get("connecting_feed") or 0),
            "cap_bound": 1 if (r.get("spill") or 0) > 0 else 0,      # did the capacity cap bind?
        }
    return {"forecast_pax": r["carried_forecast"], "market": r["natural_market"], "p2p_share": _p2p_share,
            "decomp": decomp,
            "share": r["qsi_share"], "captured": r["captured_demand"], "spill": r["spill"],
            "total_demand": r.get("total_demand", 0), "feed_beyond": r.get("feed_beyond", 0),
            "feed_behind": r.get("feed_behind", 0),
            "capacity": annual_cap or 0, "natural": r["natural_market"], "propensity": r["qsi_share"],
            "propensity_basis": "qsi-share", "dest_count": hub, "gcd_km": gcd or 0, "service": service,
            "graded_season": graded_season, "season_share": round(season_share, 3),
            "induced": bool(r.get("induced")), "avg_fare": r.get("avg_fare"),
            # FULL forecast-time feature set (exported under --full-features) - the route's own operated
            # schedule and the engine's internal QSI legs, so the feature search sees everything the engine
            # knows, not a hand-picked subset. All are forecast-time (Y-1 / operated), no outturn leakage.
            "freq": freq, "block_min": round(block, 1),
            "gauge": round((annual_cap or 0) / (max(freq, 1) * 52.0 * 2), 1) if annual_cap else 0,
            "dest_share": r.get("dest_share"), "stimulation": r.get("stimulation"),
            "coverage": r.get("coverage_gross_up"), "premium_share": r.get("premium_share"),
            "att_exponent": r.get("att_exponent"), "planned_lf": r.get("planned_load_factor"),
            "freq_discount": r.get("freq_discount"), "haul_trim_applied": r.get("haul_trim"),
            "od_source": r.get("od_source"), "capture_rate": r.get("capture_rate")}


# ----------------------------------------------------------------------------- R2: parallel route pool
# The route loop is embarrassingly parallel (every store is read-only). A worker forecasts one route
# and returns its result row; the parent collects them. Config travels once via the pool initializer,
# and each worker keeps its OWN served-index cache (per process, warmed by year-grouped chunking).
_CFG = {}
_SERVED_CACHE = {}


def _worker_init(cfg):
    global _CFG, _SERVED_CACHE, _PREAGG, _SUMMER_WEEKS, _WINTER_WEEKS
    _CFG = cfg
    _SERVED_CACHE = {}
    _PREAGG = cfg.get("preagg")
    if cfg.get("summer_weeks") is not None:
        _SUMMER_WEEKS = cfg["summer_weeks"]
    if cfg.get("winter_weeks") is not None:
        _WINTER_WEEKS = cfg["winter_weeks"]
    if cfg.get("fy_capacity"):
        # per-process swap of the capacity + served-index readers to the full-year monthly provider,
        # so both the serial path and every pool worker read true operated capacity. Additive; only
        # active under --fy-capacity. See fy_capacity.py / FY_CAPACITY_WIRING.md.
        import fy_capacity as FY
        global _operated, _served_for_week
        _mby = cfg.get("wby") or {}

        def _served_for_week(oag, week, cache):          # noqa: F811  (fy override)
            y = int(str(week)[:4])
            if y not in cache:
                cache[y] = FY.build_served_index_fy(oag, y, _mby.get(y) or [])
            return cache[y]

        def _operated(oag, weeks, dep, arr):             # noqa: F811  (fy override)
            y = int(str(weeks[0])[:4]) if weeks else None
            if not y:
                return 0.0, 0.0, 0.0, "na"
            c = FY.route_capacity_fy(oag, dep, arr, y, weeks)
            return c["annual_cap"], c["freq"], c["gcd"], c["service"]


def _forecast_route(r):
    """Forecast one route into its output-row dict (identical to the serial body). Returns the row,
    or None if sub-material (skipped), or {'__error__': line} so one bad route never stops the run."""
    c = _CFG
    off = c["offset"]
    try:
        p2p = p2p_traffic(c["sabre"], r["dep"], r["arr"], r["year"] + off)
        if p2p < c["min_outturn"]:
            return None
        out = sector_traffic(c["sabre"], r["dep"], r["arr"], r["year"] + off)
        _apf = (c.get("airport_factors") or {}).get(r["dep"], 1.0)
        f = asif_forecast(r, c["oag"], c["sabre"], _SERVED_CACHE, c["wby"], c["stim"],
                          c["radius_km"], off, c["lcc_cat"], c["feed_cfg"], c.get("market_factor"),
                          c.get("season_grade"), c.get("induced_floor"), c.get("nonstop_share"),
                          c.get("decompose"), _apf)
        graded = f["forecast_pax"]
        ratio = (graded / out) if out else None
        ratio_p2p = (f["captured"] / p2p) if p2p else None
        hub = bool((f.get("dest_count") or 0) >= c["hub_threshold"])
        row = {"route": f"{r['dep']}-{r['arr']}", "dep": r["dep"], "arr": r["arr"],
                "dep_country": _country(r["dep"]) or "", "arr_country": _country(r["arr"]) or "",
                "type": r["type"], "year": r["year"],
                "region": route_region(r["dep"], r["arr"]),
                "carrier": r["carrier"], "hub_dest": hub, "forecast_pax": round(graded),
                "captured_uncapped": round(f["captured"]), "capacity": round(f.get("capacity") or 0),
                "feed_beyond": round(f.get("feed_beyond") or 0), "feed_behind": round(f.get("feed_behind") or 0),
                "p2p_outturn": round(p2p), "fc_over_p2p": round(ratio_p2p, 3) if ratio_p2p else "",
                "outturn_pax": round(out), "fc_over_out": round(ratio, 3) if ratio else "",
                "natural": round(f["natural"] or 0), "propensity": round(f["propensity"] or 0, 4),
                "propensity_basis": f["propensity_basis"],
                "gcd_km": round(f.get("gcd_km") or r.get("gcd_km") or 0),
                "service": f.get("service", "")}
        if c.get("season_grade"):     # extra columns only under --season-grade, so default runs are unchanged
            row["graded_season"] = f.get("graded_season", "")
            row["season_share"] = f.get("season_share", 1.0)
        if c.get("induced_floor"):    # extra columns only under --induced-floor
            row["induced"] = bool(f.get("induced"))
            row["base_fare"] = f.get("avg_fare")   # measured pre-launch market fare
            row["outturn_fare"] = route_avg_fare(c["sabre"], r["dep"], r["arr"], r["year"] + off)
        if c.get("nonstop_share"):    # connecting-heaviness diagnostic
            row["p2p_share"] = f.get("p2p_share")
        if c.get("full_features"):    # complete route-level engine feature set for the feature search
            for _k in ("freq", "block_min", "gauge", "dest_share", "stimulation", "coverage",
                       "premium_share", "att_exponent", "planned_lf", "freq_discount",
                       "haul_trim_applied", "od_source", "capture_rate", "avg_fare"):
                row[_k] = f.get(_k)
        if c.get("decompose") and f.get("decomp"):   # T3: per-route error legs
            for _k, _v in f["decomp"].items():
                row["d_" + _k] = _v
        if c.get("horizons"):
            # STEP 0: grade the ONE Y1-pinned forecast (growth + capacity fixed at Y1) against the pure-P2P
            # outturn at Y+1/Y+2/Y+3; only the denominator moves (NOT the retired H7 forecast-growth overshoot).
            # captured = the P2P forecast leg (pre-feed) = the same numerator as fc_over_p2p. mature=mean(Y2,Y3).
            cap = f["captured"]
            row["p2p_out_y1"] = round(p2p) if p2p else ""
            row["fc_over_p2p_y1"] = round(ratio_p2p, 3) if ratio_p2p else ""
            for h in (2, 3):
                try:
                    _ph = p2p_traffic(c["sabre"], r["dep"], r["arr"], r["year"] + h)
                except Exception:
                    _ph = 0
                if _ph and _ph >= c["min_outturn"]:
                    row[f"p2p_out_y{h}"] = round(_ph)
                    row[f"fc_over_p2p_y{h}"] = round(cap / _ph, 3) if cap else ""
                else:                                    # COVID gap / route not material at this horizon
                    row[f"p2p_out_y{h}"] = ""; row[f"fc_over_p2p_y{h}"] = ""
            _p2, _p3 = row["p2p_out_y2"], row["p2p_out_y3"]
            if _p2 != "" and _p3 != "":
                _pm = (_p2 + _p3) / 2.0
                row["p2p_out_mature"] = round(_pm)
                row["fc_over_p2p_mature"] = round(cap / _pm, 3) if cap else ""
            else:
                row["p2p_out_mature"] = ""; row["fc_over_p2p_mature"] = ""
        return row
    except Exception as e:
        return {"__error__": f"{r['dep']+'-'+r['arr']:12} {r.get('type',''):9} "
                             f"{r.get('year',''):>4} {'ERROR: '+str(e)[:48]}"}


def _print_route_line(row):
    rp = f"{row['fc_over_p2p']:>7.2f}" if row["fc_over_p2p"] != "" else f"{'-':>7}"
    rs = f"{row['fc_over_out']:>7.2f}" if row["fc_over_out"] != "" else f"{'-':>7}"
    print(f"{row['dep']+'-'+row['arr']:12} {row['type']:9} {row['year']:>4} "
          f"{row['forecast_pax']:>10,.0f} {row['p2p_outturn']:>9,.0f} {rp} {row['outturn_pax']:>9,.0f} {rs} "
          f"{'H' if row['hub_dest'] else ' '} {row['carrier']}")


def _detect_ram_gb():
    """Best-effort total physical RAM in GB (psutil -> Windows API -> None)."""
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        pass
    try:
        import ctypes
        class _MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = _MS(); m.dwLength = ctypes.sizeof(_MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullTotalPhys / (1024 ** 3)
    except Exception:
        return None


def _configure_duckdb_limits(a):
    """Set the per-worker DuckDB memory cap and temp dir in the ENVIRONMENT before the pool spawns, so
    every worker (which inherits the parent env) is bounded and the box can't be over-committed. Honours
    a value the user set by hand. THIS is the fix for the 97%/OOM freezes: without it each of --jobs
    DuckDB connections defaults to ~80% of RAM and they collectively exhaust the machine."""
    import os, tempfile
    if "AVIA_DUCKDB_MEMORY" not in os.environ:
        total = a.mem_total or _detect_ram_gb()
        if total:
            budget = max(2.0, total - a.mem_reserve)
            per_worker = max(1.0, budget / max(int(a.jobs or 1), 1))
            os.environ["AVIA_DUCKDB_MEMORY"] = f"{per_worker:.1f}GB"
            print(f"DuckDB memory cap: {per_worker:.1f}GB/worker ({total:.0f}GB RAM - "
                  f"{a.mem_reserve:.0f}GB OS, / {a.jobs} workers)")
        else:
            os.environ["AVIA_DUCKDB_MEMORY"] = "3GB"
            print("DuckDB memory cap: 3GB/worker (RAM auto-detect failed; pass --mem-total to size it)")
    if "AVIA_DUCKDB_TEMP" not in os.environ:
        tmp = a.temp_dir or os.path.join(tempfile.gettempdir(), "avia_duckdb")
        try:
            os.makedirs(tmp, exist_ok=True)
        except Exception:
            pass
        os.environ["AVIA_DUCKDB_TEMP"] = tmp
        print(f"DuckDB temp spill: {tmp}")


def _coerce_row(r):
    """Coerce a CSV-read row back to the numeric types the summary expects (used on --resume, where
    already-done rows are read from the partial output file)."""
    for k in ("forecast_pax", "captured_uncapped", "capacity", "feed_beyond", "feed_behind",
              "p2p_outturn", "outturn_pax", "natural", "gcd_km"):
        try:
            r[k] = float(r.get(k) or 0)
        except Exception:
            r[k] = 0.0
    for k in ("fc_over_p2p", "fc_over_out"):
        v = r.get(k)
        try:
            r[k] = float(v) if v not in ("", None) else ""
        except Exception:
            r[k] = ""
    try:
        r["propensity"] = float(r.get("propensity") or 0)
    except Exception:
        r["propensity"] = 0.0
    r["hub_dest"] = str(r.get("hub_dest")).strip().lower() == "true"
    try:
        r["year"] = int(float(r.get("year")))
    except Exception:
        pass
    return r


def main():
    ap = argparse.ArgumentParser(description="Automatic forecast back-test over the OAG/Sabre history.")
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--start-year", type=int, default=None, help="only routes launching this year (default all)")
    ap.add_argument("--years", default=None,
                    help="comma list of launch years to keep, e.g. 2016,2017,2018,2019,2024,2025 "
                         "(the clean sample: Covid-hit 2020-2023 excluded). Overrides --start-year.")
    ap.add_argument("--discover-only", action="store_true",
                    help="discover + filter + pin the route set, then exit without forecasting "
                         "(so the wave cache can be built before the first long run)")
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
    ap.add_argument("--full-features", action="store_true",
                    help="export the COMPLETE route-level engine feature set (route frequency, gauge, block "
                         "time, and the QSI legs: dest_share, stimulation, coverage, premium_share, "
                         "att_exponent, planned_lf, capture_rate, avg_fare) so the feature search sees "
                         "everything the engine knows. Combine with --decompose --nonstop-share for the "
                         "full substrate. All forecast-time, no outturn leakage.")
    ap.add_argument("--horizons", action="store_true",
                    help="STEP 0: grade ONE Y1-pinned forecast against Y1/Y2/Y3 and mature=mean(Y2,Y3) "
                         "in a single run; report +/-20% and median fc/p2p by horizon + attrition. The "
                         "forecast growth is held fixed (only the outturn/denominator year moves), so this "
                         "is NOT the retired H7 overshoot. Forces --offset 1. ~2 extra Sabre queries/route.")
    ap.add_argument("--offset", type=int, default=None,
                    help="grade against launch year + OFFSET, overriding --mature/--y3. --offset 0 grades "
                         "against the LAUNCH-YEAR outturn (as-if Y-1), so 2024/2025 launches are gradeable "
                         "from 2023/2024/2025 Sabre despite the Covid gap - two held-out cohorts without "
                         "2026 data. Launch-year outturn is immature (noisier); cross-check it agrees with "
                         "the Y+1 read before trusting it.")
    ap.add_argument("--keep-thin", action="store_true",
                    help="keep thin-GDS domestic routes (China/India domestic etc); off by default")
    ap.add_argument("--regions", default=None,
                    help="comma list to keep, e.g. EU,NA,LATAM,INTL,APAC,MEA,AFR (default all)")
    ap.add_argument("--out", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--routes-file", default=None,
                    help="pin the route set: first run writes it, later runs reuse it for clean A/B")
    ap.add_argument("--lcc-cat", type=float, default=1.0,
                    help="catchment radius multiplier for LCC/ULCC (price pax drive further); 1.0 = off")
    ap.add_argument("--feed-fix", action="store_true",
                    help="hub-aware feed: zero P2P carriers, scale capture by origin/hub dominance")
    ap.add_argument("--feed-behind-cap", type=float, default=0.10, help="behind base capture under --feed-fix")
    ap.add_argument("--feed-dom-gain", type=float, default=1.0, help="dominance gain under --feed-fix")
    ap.add_argument("--feed-dom-floor", type=float, default=0.5, help="dominance floor under --feed-fix")
    ap.add_argument("--no-split-floor", action="store_true",
                    help="run WITHOUT the split_share connectivity floor (arm 3). The floor is "
                         "total-preserving, so it moves the P2P/connecting split rather than the "
                         "headline; read fc_over_out for its effect.")
    ap.add_argument("--mct-banking", action="store_true",
                    help="schedule-bank the beyond feed via MCT + the OAG onward wave (opt-in; test vs baseline)")
    ap.add_argument("--qsi-feed", action="store_true",
                    help="Engine V2: schedule-quality QSI feed at each route's ACTUAL flown dep time "
                         "(opt-in; needs the wave cache; test vs bt_v1_baseline)")
    ap.add_argument("--wave-cache", default=os.path.join(HERE, "qsi_wave_cache.duckdb"),
                    help="wave cache from wave_cache.py (flown times + boards for --qsi-feed)")
    ap.add_argument("--preagg", default=None,
                    help="R1 pre-aggregation store from build_preagg.py: replaces the per-route Sabre "
                         "full scans (p2p/sector/connecting/behind markets) with point lookups. "
                         "Identity-preserving; falls back to full scans if the store is missing/invalid.")
    ap.add_argument("--jobs", type=int, default=1,
                    help="R2 parallel route pool: number of worker processes (default 1 = serial). "
                         "Routes are grouped by launch year so each worker's served-index/board caches "
                         "stay warm. Set AVIA_DUCKDB_THREADS=1 so N workers don't oversubscribe cores.")
    ap.add_argument("--summer-weeks", type=float, default=28.0,
                    help="weeks in the summer season (Apr-mid Oct) for annualising the summer OAG pull")
    ap.add_argument("--winter-weeks", type=float, default=24.0,
                    help="weeks in the winter season (mid Oct-end Mar) for annualising the winter pull")
    ap.add_argument("--mem-reserve", type=float, default=8.0,
                    help="GB of RAM to leave for the OS; the rest is split across --jobs workers as each "
                         "DuckDB connection's memory_limit, so the pool can't over-commit and freeze the box")
    ap.add_argument("--mem-total", type=float, default=None,
                    help="total machine RAM in GB (default: auto-detect); used to size the per-worker cap")
    ap.add_argument("--temp-dir", default=None,
                    help="DuckDB spill directory for every worker (default: a local system-temp folder). "
                         "Point it at a disk with space, e.g. E:\\duckdb_tmp, and clean it deliberately.")
    ap.add_argument("--market-factor", action="store_true",
                    help="Item 9: apply the capped market-size discount on P2P capture "
                         "(route_forecast.DEFAULT_MARKET_FACTOR, keyed off the measured market). Opt-in; "
                         "the confirming run to check the forecastable buckets centre on ~1.0.")
    ap.add_argument("--resume", action="store_true",
                    help="crash-safe resume: rows are written to --out as each route finishes (not just at "
                         "the end), and on restart the routes already in --out are skipped. Use for any long "
                         "run so an interruption never restarts from scratch.")
    ap.add_argument("--fy-capacity", action="store_true",
                    help="full-year operated capacity from monthly OAG (fy_capacity module) instead of the "
                         "two-week snapshot annualisation: sum of monthly seats_total, no x52, no "
                         "seats_total*frequency double-count. Clean set = Europe/Asia 2015-18 + all 2019 H1. "
                         "Additive and gated; off = shipped behaviour.")
    ap.add_argument("--induced-floor", action="store_true",
                    help="INDUCED model (LCC/ULCC only): where the measured market is far below deployed "
                         "capacity (a new market the low fare will stimulate), floor demand at capacity x "
                         "the achieved seat factor comparable launches reached, instead of measured-market x "
                         "stim. Adds induced/base_fare/outturn_fare columns; FSC and forecastable routes are "
                         "unchanged. Use analyze_induced.py to read the result.")
    ap.add_argument("--airport-capture", default=None,
                    help="T7: apply per-origin-airport capture factors from a build_airport_factors.py "
                         "JSON. Learn on 2016-2018, run this on the held-out years (2019,2024) to validate: "
                         "within-x1.2 share should rise without degrading the median.")
    ap.add_argument("--decompose", action="store_true",
                    help="T3 accuracy plan: write each graded route's multiplicative forecast legs "
                         "(d_mkt_asif, d_mkt_outturn, d_growth_applied, d_share, d_dshare, d_stim, "
                         "d_coverage, d_captured, d_feed_fc, d_cap_bound) so the variance can be attributed "
                         "to legs by segment. Adds one Sabre query per route (the outturn-year market).")
    ap.add_argument("--nonstop-share", action="store_true",
                    help="diagnostic: add a p2p_share column = the Y-1 nonstop fraction of the catchment's "
                         "O&D to the destination (connecting-heaviness proxy). Adds a Sabre query per route; "
                         "use with calib_bands.py to test/fit the connecting-heavy over-read discount.")
    ap.add_argument("--season-grade", action="store_true",
                    help="C1: grade one-season routes fairly. A route the OAG shows as summer-only ('S') or "
                         "winter-only ('W') is forecast in that SEASON (demand scaled to the season's share of "
                         "the annual O&D), then graded against its outturn, which for a one-season route IS the "
                         "season actual. Turns the seasonal over-read tail into a graded seasonal claim. Adds "
                         "graded_season/season_share columns; annual routes are unchanged.")
    ap.add_argument("--qsi-k", type=float, default=0.06, help="QSI feed level k (calibrate to outturn)")
    ap.add_argument("--qsi-k-behind", type=float, default=None,
                    help="behind-side k (default = --qsi-k)")
    ap.add_argument("--qsi-lambda", type=float, default=1.0,
                    help="QSI share logit exponent (1.0 = proportional fair share; >1 sharpens "
                         "winner-take-most; the reserve knob for the forecastable feed-heavy slice)")
    a = ap.parse_args()
    global _PREAGG, _SUMMER_WEEKS, _WINTER_WEEKS
    _PREAGG = a.preagg
    _SUMMER_WEEKS, _WINTER_WEEKS = a.summer_weeks, a.winter_weeks
    _configure_duckdb_limits(a)      # cap DuckDB RAM per worker + set the spill dir BEFORE the pool spawns
    market_factor = True if a.market_factor else None
    if market_factor:
        import route_forecast as _RF
        print(f"P2P level trim ON (type-aware): "
              f"{ {t: v[0][1] for t, v in _RF.MARKET_FACTOR_BY_TYPE.items()} }")
    if a.preagg:
        import preagg
        if preagg.available(a.preagg):
            print(f"R1 pre-aggregation ON: {a.preagg} (per-route Sabre reads are point lookups)")
        else:
            print(f"WARNING --preagg {a.preagg} missing/invalid - falling back to full Sabre scans")
    feed_cfg = ({"behind_cap": a.feed_behind_cap, "dom_gain": a.feed_dom_gain,
                 "dom_floor": a.feed_dom_floor}
                if (a.feed_fix or a.mct_banking or a.qsi_feed or a.no_split_floor) else None)
    # THE CONNECTIVITY FLOOR AS ITS OWN ARM. split_share re-splits the carried total using an
    # airport connectivity table and can only ever lift connecting, never cut it. It was sized for
    # the FLAT feed, which under-credited transfer traffic at non-US hubs. Whether it is still right
    # under the QSI feed is a separate question from whether the QSI feed is right, and folding the
    # two into one arm would leave no way to say which moved the score. Hence a third arm.
    if feed_cfg is not None and a.no_split_floor:
        feed_cfg["split_floor"] = False
    if feed_cfg is not None and a.preagg:
        feed_cfg["preagg"] = a.preagg
    if feed_cfg is not None and a.mct_banking:
        feed_cfg["mct_banking"] = True
    if feed_cfg is not None and a.qsi_feed:
        feed_cfg["qsi_feed"] = True
        feed_cfg["wave_cache"] = a.wave_cache
        feed_cfg["qsi_k"] = a.qsi_k
        if a.qsi_k_behind is not None:
            feed_cfg["qsi_k_behind"] = a.qsi_k_behind
        if a.qsi_lambda != 1.0:
            feed_cfg["logit_lambda"] = a.qsi_lambda
    keep_regions = set(s.strip().upper() for s in a.regions.split(",")) if a.regions else None
    offset = a.offset if a.offset is not None else (3 if a.y3 else 2 if a.mature else 1)   # Y+offset
    if a.horizons:
        offset = 1   # multi-horizon: the forecast is pinned at the Y1 reference; only the outturn year moves

    if not os.path.exists(a.oag):
        print(f"OAG store not found: {a.oag}"); return
    if not os.path.exists(a.sabre):
        print(f"Sabre store not found: {a.sabre}"); return

    if a.fy_capacity:
        # swap the period source to monthly labels so discovery, the survival filter and asif_forecast
        # all read full-year operated capacity (see fy_capacity, FY_CAPACITY_WIRING.md). Global swap so
        # discover_new_routes' internal weeks_by_year() call picks it up too. _operated / _served_for_week
        # are swapped per process in _worker_init.
        import fy_capacity as FY
        globals()["weeks_by_year"] = FY.months_by_year
        print("FY-CAPACITY ON: monthly operated capacity (no x52, no double-count)")
    wby = weeks_by_year(a.oag)
    print(f"OAG years: {sorted(wby)}")
    # PIN by storing the filtered route records and BYPASSING discovery when the pin exists. Route
    # discovery does not return identical membership run-to-run, so the pin is authoritative for clean
    # A/B (base 145 vs feed-fix 83 when key-matching a fresh discovery). The fields in _PIN are all the
    # main loop + asif_forecast read.
    # R4: the pin check now runs BEFORE discovery, so an existing pin skips discovery AND every
    # discovery-time scan below (the survival nonstop_pairs passes, min-gcd, thin-GDS, region filters).
    # Previously discovery ran in full and was then discarded by the pin load (observed in the 5 Jul
    # log: the 11,999-route discovery executed before "discovery bypassed"), 4-7 wasted minutes a run.
    _PIN = ("dep", "arr", "year", "carrier", "type", "gcd_km", "reinstated")
    if a.routes_file and os.path.exists(a.routes_file):
        routes = json.load(open(a.routes_file))
        if a.limit:
            routes = routes[:a.limit]
        print(f"{len(routes)} routes loaded from pinned set {a.routes_file} (discovery bypassed)"
              + (f"; capped to {a.limit}" if a.limit else ""))
    else:
        routes = discover_new_routes(a.oag, a.start_year, a.min_freq)
        print(f"discovered {len(routes)} new nonstop routes "
              f"{'in '+str(a.start_year) if a.start_year else 'across the history'}")
        if a.years:
            keep_years = {int(y) for y in a.years.split(",")}
            missing = sorted(y for y in keep_years if y not in wby or (y - 1) not in wby)
            if missing:
                print(f"note: launch years lacking Y-1/Y OAG coverage will yield little: {missing}")
            routes = [r for r in routes if r["year"] in keep_years]
            print(f"{len(routes)} in launch years {sorted(keep_years)}")
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
        if a.routes_file:
            json.dump([{k: r.get(k) for k in _PIN} for r in routes], open(a.routes_file, "w"))
            print(f"pinned {len(routes)} routes to {a.routes_file} (reuse with the same --routes-file)")
    if a.discover_only:
        from collections import Counter
        print(f"--discover-only: stopping after pinning. Launch years: "
              f"{dict(sorted(Counter(r['year'] for r in routes).items()))}")
        rein = Counter(r["year"] for r in routes if r.get("reinstated"))
        if rein:
            print(f"of which REINSTATED (flew pre-gap, e.g. pre-Covid restarts): "
                  f"{dict(sorted(rein.items()))}")
        print("Next: py -3.12 wave_cache.py --oag <store> --routes-file "
              f"{a.routes_file or '<routes file>'} --out qsi_wave_cache.duckdb")
        return

    HUB_THRESHOLD = 40       # dest serves >= this many nonstop destinations -> a hub (feed-heavy)
    MIN_OUTTURN = a.min_outturn   # ignore sub-material sectors in the ratio stats (default 3000)
    _airport_factors = {}
    if a.airport_capture:
        try:
            _af = json.load(open(a.airport_capture))
            _airport_factors = _af.get("factors", _af)
            print(f"Airport capture factors: {len(_airport_factors)} airports from {a.airport_capture}")
        except Exception as _e:
            print(f"WARNING: could not load --airport-capture {a.airport_capture}: {_e}")
    cfg = {"oag": a.oag, "sabre": a.sabre, "wby": wby, "stim": a.stim, "radius_km": a.radius_km,
           "offset": offset, "lcc_cat": a.lcc_cat, "feed_cfg": feed_cfg, "min_outturn": MIN_OUTTURN,
           "hub_threshold": HUB_THRESHOLD, "preagg": a.preagg,
           "summer_weeks": a.summer_weeks, "winter_weeks": a.winter_weeks,
           "market_factor": market_factor, "season_grade": a.season_grade,
           "induced_floor": a.induced_floor, "nonstop_share": a.nonstop_share,
           "decompose": a.decompose, "airport_factors": _airport_factors,
           "fy_capacity": a.fy_capacity, "horizons": a.horizons, "full_features": a.full_features}
    # make sure the --out directory exists, so a long run never dies at the final write (e.g. a fresh
    # E:\Avia\QSI\backtests path). Created up front so --resume streaming also has somewhere to write.
    _outdir = os.path.dirname(os.path.abspath(a.out))
    if _outdir:
        os.makedirs(_outdir, exist_ok=True)
    rows = []
    done_keys = set()
    _resuming = bool(a.resume and os.path.exists(a.out))
    if _resuming:
        for pr in csv.DictReader(open(a.out, newline="")):
            done_keys.add((pr.get("dep"), pr.get("arr"), str(pr.get("year"))))
            rows.append(_coerce_row(pr))
        before = len(routes)
        routes = [r for r in routes if (r["dep"], r["arr"], str(r["year"])) not in done_keys]
        print(f"resume: {len(done_keys)} routes already in {a.out}; {before - len(routes)} skipped, "
              f"{len(routes)} still to run")
    # Crash-safe write: with --resume each finished route is flushed to --out immediately (append), so an
    # interruption never loses completed work. Without --resume the file is written once at the end (old
    # behaviour). The header goes down with the first new row of a fresh file.
    _out_fh = open(a.out, "a" if _resuming else "w", newline="") if a.resume else None
    _wr = {"w": None}
    def _emit(row):
        if _out_fh is None:
            return
        if _wr["w"] is None:
            _wr["w"] = csv.DictWriter(_out_fh, fieldnames=list(row.keys()))
            if not _resuming:
                _wr["w"].writeheader()
        _wr["w"].writerow(row); _out_fh.flush()
    t0 = time.time()
    hdr = (f"{'route':12} {'type':9} {'yr':>4} {'forecast':>10} {'p2p_out':>9} {'fc/p2p':>7} "
           f"{'tot_out':>9} {'fc/tot':>7}  carrier")
    print("\n" + hdr); print("-" * (len(hdr) + 6))
    if a.jobs and a.jobs > 1:
        # R2 parallel pool. Year-grouped so each worker's served-index cache stays warm (R5); output
        # rows are collected as they finish (order differs from serial, which the identity harness
        # handles by key-matching). forecast_pax etc. are unchanged - this is pure performance.
        import multiprocessing as mp
        ordered = sorted(routes, key=lambda r: r["year"])
        # Small chunks so results stream to the console promptly (a big chunk makes a worker finish
        # ~100 routes before the parent prints anything). The per-worker served-index cache persists
        # across chunks regardless, so small chunks don't cost extra rebuilds.
        chunk = max(1, min(4, len(ordered) // (a.jobs * 8) or 1))
        done = 0
        with mp.Pool(a.jobs, initializer=_worker_init, initargs=(cfg,)) as pool:
            for res in pool.imap(_forecast_route, ordered, chunksize=chunk):
                done += 1
                if res is None:
                    pass
                elif "__error__" in res:
                    print(res["__error__"])
                else:
                    rows.append(res); _emit(res); _print_route_line(res)
                if a.limit is None and done % 100 == 0:
                    print(f"  ... {done}/{len(ordered)} ({time.time()-t0:.0f}s)")
    else:
        _worker_init(cfg)     # set the same process-global config for the serial path
        for i, r in enumerate(routes):
            res = _forecast_route(r)
            if res is None:
                continue
            if "__error__" in res:
                print(res["__error__"])
            else:
                rows.append(res); _emit(res); _print_route_line(res)
            if a.limit is None and (i + 1) % 25 == 0:
                print(f"  ... {i+1}/{len(routes)} ({time.time()-t0:.0f}s)")

    def med(xs):
        xs = sorted(xs); n = len(xs)
        return (xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2) if xs else 0
    def balance(xs):
        return sum(1 for x in xs if x > 1.0), sum(1 for x in xs if x < 1.0)
    # The like-for-like test: P2P forecast vs PURE P2P outturn (feed removed). Isolates whether the
    # P2P demand engine is UNBIASED (median ~1.0, errors balanced over/under) from the separate
    # connecting-feed gap. fc/TOTAL (with feed) shown for context = the full gap.
    gradable = [r for r in rows if r["fc_over_p2p"] != "" and r["p2p_outturn"] >= MIN_OUTTURN]
    clean = [r for r in gradable if not r["hub_dest"]]
    print("\nP2P ENGINE vs PURE P2P OUTTURN (feed removed = the like-for-like demand test; an "
          "unbiased forecast has median ~1.0 with over and under roughly equal):")
    print(f"  {'type':9} {'n':>4} {'median fc/p2p':>14} {'over':>5} {'under':>6} {'+/-5%':>7} {'+/-20%':>7}")
    bytype = defaultdict(list)
    for r in clean:
        bytype[r["type"]].append(r["fc_over_p2p"])
    for t in ("FSC", "LCC", "ULCC", "Regional"):
        xs = bytype.get(t, [])
        if xs:
            ov, un = balance(xs)
            w5 = sum(1 for x in xs if 0.95 <= x <= 1.05)
            w20 = sum(1 for x in xs if 0.8 <= x <= 1.2)
            # +/-5% is the stretch target, and only fair on FSC (LCC/ULCC are stimulation-led)
            print(f"  {t:9} {len(xs):>4} {med(xs):>14.2f} {ov:>5} {un:>6} {w5:>4}/{len(xs):<2} {w20:>4}/{len(xs):<2}")
    cl = [r["fc_over_p2p"] for r in clean]
    if cl:
        ov, un = balance(cl); within = sum(1 for x in cl if 0.8 <= x <= 1.2)
        tot = [r["fc_over_out"] for r in clean if r["fc_over_out"] != ""]
        print(f"  {'ALL P2P':9} {len(cl):>4} {med(cl):>14.2f} {ov:>5} {un:>6}   "
              f"(within +/-20%: {within}/{len(cl)}; same routes median fc/TOTAL {med(tot):.2f})")

    # SEASONAL COHORT (C1): one-season routes (OAG service "summer"/"winter"). --season-grade forecasts
    # these IN-SEASON (demand scaled to the season). It CANNOT be validly graded on the annual stores:
    # fc/p2p divides by the ANNUAL O&D market (year-round demand routes over off-season connections), and
    # fc/out divides by onboard sector traffic (all connecting pax, so <1 even for annual routes). Neither
    # is a season-scoped P2P truth. A validated seasonal grade needs the monthly Sabre O&D pull; until
    # then the seasonal forecast is MODELLED, not back-tested. Counts shown for scope only, NOT a grade.
    seas = [r for r in rows if r.get("service") in ("summer", "winter")]
    if seas:
        s_sum = sum(1 for r in seas if r.get("service") == "summer")
        s_win = len(seas) - s_sum
        print(f"\n  SEASONAL one-season routes: n={len(seas)} ({s_sum} summer, {s_win} winter), "
              f"forecast {'IN-SEASON' if a.season_grade else 'full-year'}. NOT graded: the annual stores "
              f"have no season-scoped P2P outturn (p2p is annual O&D; onboard includes connecting pax). "
              f"A validated seasonal grade needs the monthly Sabre O&D pull.")

    # INDUCED-FLOOR cohort: the LCC/ULCC routes the floor lifted. Graded on fc/OUT (carried vs onboard),
    # since the floor is capacity-anchored, that is the like-for-like test for a filled-plane forecast.
    if a.induced_floor:
        fl = [r for r in rows if r.get("induced") and r.get("fc_over_out") not in ("", None)
              and (r.get("outturn_pax") or 0) >= MIN_OUTTURN]
        if fl:
            fv = [float(r["fc_over_out"]) for r in fl]; ov, un = balance(fv)
            w20 = sum(1 for x in fv if 0.8 <= x <= 1.2)
            w40 = sum(1 for x in fv if 0.6 <= x <= 1.4)
            print("\n  INDUCED-FLOOR cohort (LCC/ULCC floored to capacity x achieved LF; graded fc/OUT):")
            print(f"    n={len(fv)}  median {med(fv):.2f}  over {ov} under {un}  "
                  f"within +/-20% {w20}/{len(fv)}  within +/-40% {w40}/{len(fv)}")
        else:
            print("\n  INDUCED-FLOOR: no LCC/ULCC routes were floored (check the market/capacity threshold).")

    # by REGION (non-hub clean P2P) - reads where Sabre coverage is complete vs not
    print(f"\n  by region (non-hub P2P):  {'region':8} {'n':>4} {'median':>7} {'over':>5} {'under':>6} {'+/-20%':>7}")
    byreg = defaultdict(list)
    for r in clean:
        byreg[r.get("region", "OTH")].append(r["fc_over_p2p"])
    for reg in sorted(byreg, key=lambda k: -len(byreg[k])):
        xs = byreg[reg]; ov, un = balance(xs); w20 = sum(1 for x in xs if 0.8 <= x <= 1.2)
        print(f"  {'':24} {reg:8} {len(xs):>4} {med(xs):>7.2f} {ov:>5} {un:>6} {w20:>4}/{len(xs):<2}")
    # split: did the market pre-EXIST (forecastable) or did the route CREATE it (induced)?
    fore = [r for r in clean if (r.get("natural") or 0) >= r["p2p_outturn"]]
    indu = [r for r in clean if (r.get("natural") or 0) < r["p2p_outturn"]]
    if fore:
        fv = [r["fc_over_p2p"] for r in fore]; ov, un = balance(fv)
        w = sum(1 for x in fv if 0.8 <= x <= 1.2)
        print(f"\n  FORECASTABLE (pre-existing market >= what the route carried) - the engine's real "
              f"test:\n    n={len(fv)}  median fc/p2p {med(fv):.2f}  over {ov} under {un}  within +/-20%: {w}/{len(fv)}")
    if indu:
        iv = [r["fc_over_p2p"] for r in indu]
        print(f"  INDUCED (route created a market absent from history - the stimulation/judgement "
              f"layer, not a data forecast):\n    n={len(iv)}  median fc/p2p {med(iv):.2f}")

    # ---- FORECASTABLE deep-dive (hubs INCLUDED so hub-ness is a driver; fc/p2p is P2P-vs-P2P,
    #      so feed is already netted out). This is the clean engine test, split every way that
    #      might drive the spread, so we see WHERE the error lives rather than a single median. ----
    fore_g = [r for r in gradable if (r.get("natural") or 0) >= r["p2p_outturn"] and r["fc_over_p2p"] != ""]
    if fore_g:
        def grp(items, keyfn, order=None):
            d = defaultdict(list)
            for r in items:
                d[keyfn(r)].append(r["fc_over_p2p"])
            for k in (order or sorted(d, key=lambda k: -len(d[k]))):
                xs = d.get(k)
                if xs:
                    ov, un = balance(xs); w = sum(1 for x in xs if 0.8 <= x <= 1.2)
                    print(f"      {str(k):11} n={len(xs):<4} median {med(xs):.2f}  over {ov} under {un}  +/-20% {w}/{len(xs)}")

        def bkt(v, edges, labels):
            v = v or 0
            for i, e in enumerate(edges):
                if v < e:
                    return labels[i]
            return labels[-1]
        HAUL_E, HAUL_L = [800, 2500, 6000], ["<800km", "800-2500", "2500-6000", ">6000km"]
        MKT_E, MKT_L = [15000, 50000, 150000], ["<15k", "15-50k", "50-150k", ">150k"]
        print(f"\n  FORECASTABLE deep-dive (n={len(fore_g)}, the clean engine test):")
        print("    by type:");   grp(fore_g, lambda r: r["type"], ["FSC", "LCC", "ULCC", "Regional"])
        print("    by region:"); grp(fore_g, lambda r: r.get("region", "OTH"))
        print("    by haul:");   grp(fore_g, lambda r: bkt(r.get("gcd_km"), HAUL_E, HAUL_L), HAUL_L)
        print("    by hub:");    grp(fore_g, lambda r: "hub" if r.get("hub_dest") else "non-hub", ["hub", "non-hub"])
        print("    by market:"); grp(fore_g, lambda r: bkt(r.get("p2p_outturn"), MKT_E, MKT_L), MKT_L)

    if a.horizons:
        _HZ = [("Y1", "fc_over_p2p_y1", "p2p_out_y1"), ("Y2", "fc_over_p2p_y2", "p2p_out_y2"),
               ("Y3", "fc_over_p2p_y3", "p2p_out_y3"), ("mature(Y2,Y3)", "fc_over_p2p_mature", "p2p_out_mature")]
        print("\n  MULTI-HORIZON GRADING (Step 0): ONE Y1-pinned forecast, only the outturn year moves.")
        print("    Forecastable P2P at each horizon (natural >= that horizon's P2P outturn); the Y1 row")
        print("    reconciles with the FORECASTABLE deep-dive above (same population).")
        print(f"    {'horizon':14} {'n':>4} {'median':>7} {'over':>5} {'under':>6} {'+/-20%':>9}")
        for lbl, rk, pk in _HZ:
            xs = [r[rk] for r in rows
                  if r.get(rk) not in (None, "") and r.get(pk) not in (None, "")
                  and (r.get("natural") or 0) >= (r.get(pk) or 0)]
            if xs:
                ov, un = balance(xs); w = sum(1 for x in xs if 0.8 <= x <= 1.2)
                print(f"    {lbl:14} {len(xs):>4} {med(xs):>7.2f} {ov:>5} {un:>6} {w:>5}/{len(xs):<3}")
            else:
                print(f"    {lbl:14} {'0':>4}   (no gradeable outturn - COVID gap 2020-22 or attrition)")
        _y1 = sum(1 for r in rows if r.get("p2p_out_y1") not in (None, ""))
        _att = []
        for lbl, _rk, pk in _HZ[:3]:
            _sv = sum(1 for r in rows if r.get(pk) not in (None, ""))
            _att.append(f"{lbl} {_sv}" + (f" ({_sv*100//_y1}%)" if _y1 else ""))
        print("    survivorship (routes with a material P2P outturn at the horizon): " + ", ".join(_att))
        # haul x horizon: the direct ramp test - does the long-haul over-read shrink as the outturn matures?
        _HAUL_E, _HAUL_L = [800, 2500, 6000], ["<800km", "800-2500", "2500-6000", ">6000km"]
        def _hb(v):
            v = v or 0
            for i, e in enumerate(_HAUL_E):
                if v < e:
                    return _HAUL_L[i]
            return _HAUL_L[-1]
        print("    by haul x horizon (median fc/p2p, +/-20% hit in brackets):")
        print(f"    {'haul':11} {'Y1':>15} {'Y2':>15} {'Y3':>15}")
        for hl in _HAUL_L:
            cells = []
            for lbl, rk, pk in _HZ[:3]:
                xs = [r[rk] for r in rows
                      if r.get(rk) not in (None, "") and r.get(pk) not in (None, "")
                      and (r.get("natural") or 0) >= (r.get(pk) or 0) and _hb(r.get("gcd_km")) == hl]
                if xs:
                    w = sum(1 for x in xs if 0.8 <= x <= 1.2)
                    cells.append(f"{med(xs):.2f} ({w}/{len(xs)})")
                else:
                    cells.append("-")
            print(f"    {hl:11} {cells[0]:>15} {cells[1]:>15} {cells[2]:>15}")
        print("    Read: if the long-haul (2500-6000km) over-read at Y1 falls toward 1.0 at Y2/Y3 it was a")
        print("    start-up ramp and mature-horizon grading is the fix; if it holds ~2x it is a real distance")
        print("    bias for the two-sided haul recalibration (then validate on the hold-out).")

    print(f"\ndropped from stats: {len(rows)-len(gradable)} routes (no P2P outturn / failed / < {MIN_OUTTURN})")

    if a.resume:
        if _out_fh is not None:
            _out_fh.close()                    # rows were flushed incrementally as they finished
        print(f"\nwrote {a.out}  ({len(rows)} routes, {time.time()-t0:.0f}s)")
    elif rows:
        with open(a.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(f"\nwrote {a.out}  ({len(rows)} routes, {time.time()-t0:.0f}s)")
    else:
        print(f"\nNO ROUTES GRADED - nothing written to {a.out}. Every route had outturn < {MIN_OUTTURN} "
              f"(usually the outturn year has no Sabre O&D: e.g. 2026 not loaded, or the Covid gap). "
              f"For --offset 0 the LAUNCH-year Sabre must exist.")
    if feed_cfg is not None and feed_cfg.get("qsi_feed"):
        print(f"QSI feed: {feed_cfg.get('_qsi_no_flown', 0)} routes without a flown schedule "
              f"(V1 fallback), {feed_cfg.get('_qsi_fallbacks', 0)} in-run fallbacks (errors)")
    print("\nCalibrate on the FORECASTABLE deep-dive, NOT the blended by-type medians (those are "
          "dragged by induced/ULCC). Read: is the FSC-forecastable median ~1.0 with over/under even, "
          "and which haul/hub/market bucket carries the spread. That bucket is the next fix.")


if __name__ == "__main__":
    main()
