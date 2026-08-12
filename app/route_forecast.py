#!/usr/bin/env python3
"""
Avia Solutions - route forecast as ONE connected loop (measured demand -> capture -> capacity).
================================================================================================
Rebuilt 30 June 2026 after the audit (John). The calibrated SJC/LHR method is
forecast = base_demand x growth x stimulation x capture, where base_demand is the MEASURED Sabre
O&D market by TRUE ORIGIN, never population x propensity. And the forecast is bounded by the
recommended aircraft's capacity: demand above it is spill, not passengers carried.

The loop:
  1. CATCHMENT, by RESIDENCE. The origin's catchment = point-of-origin cities whose residents LIVE
     near the origin airport (poo_city_name geocoded, within a radius). This is residence, not
     departures: a Genoa resident who drives to Milan for New York is still Genoa demand. It is the
     fix for both the visitor pollution (Londoners flying home from Genoa) and the long-haul case
     (locals using the hub).
  2. MEASURED MARKET. natural = the catchment's measured demand to the destination metro, by true
     origin, whatever airport they use today. current = the part already departing the origin.
  3. REPATRIATION. A new nonstop wins back a share of the leaked (natural - current).
     captured = current + leaked x capture_rate.
  4. STIMULATION x growth, then the CAPACITY BOUND: carried = min(captured, capacity x load).

Runs on the machine with sabre.duckdb + oag.duckdb.
"""
import math, os, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DUMP = os.path.join(HERE, "cities5000.txt")
MAX_PLAN_LF = 0.875
DEFAULT_CAPTURE_RATE = 0.65

# Plain-English explanation of each market-build step, keyed on the step label. The label says what the
# line is; the note says why it is there. Written for an airline planner reading the table on a slide
# for the first time, not for someone who knows the model, because that is who the table is shown to.
STEP_NOTES = {
    "Passengers flying to the destination from the whole service area today":
        "Everyone within reach of this airport who already flies to the destination, whichever airport "
        "they use today. Measured from Sabre bookings, grossed up for the bookings Sabre does not see.",
    "Of those, the share a nonstop from this airport would win":
        "Most of these passengers drive past this airport to a larger one. This is the share who would "
        "switch once the nonstop exists, from how far they live from each airport and what each offers.",
    "Of those, the share using this destination airport":
        "Where the destination city has more than one airport, the share whose journey ends at this one.",
    "Extra passengers created by having a direct service":
        "Journeys nobody makes today because the connection is too long, which a nonstop makes worth "
        "taking. A full-service long-haul launch is assumed to add 15%.",
    "Trim applied because one new service wins less of a very large market":
        "In a very large market a single new service takes proportionally less than in a small one. "
        "Measured on past launches and applied only to the local traffic.",
    "Adjustment for how this airport has performed on its own past launches":
        "Some airports repeatedly hold more or less of their own catchment than the general model "
        "expects. This factor is learned from that airport's own launch history.",
    "Uplift where the destination airport serves a thin market":
        "Inbound demand to a genuine secondary airport is under-allocated by a catchment model. The "
        "uplift applies only where the market is thin enough for that to be the reason.",
    "Adjustment for airports of this size and distance, from past launches":
        "A correction fitted across every launch in the back-test for airports of this size flying "
        "this distance, so a route is not forecast in isolation from what comparable routes did.",
    "Limited to what the aircraft and frequency can seat; the rest is turned away":
        "Demand above what the chosen aircraft and weekly frequency can carry at a sensible load "
        "factor cannot be flown. It is removed here rather than counted as traffic.",
    "Re-split between local and connecting passengers; the total does not change":
        "How the same total divides between passengers flying only this route and those connecting at "
        "either end, set by how much of each airport's traffic is transfer traffic.",
    "Point to point passengers carried each year":
        "Passengers flying only this route, both directions. Connecting passengers are added to this "
        "to reach the route total.",
}
DEMAND_RADIUS_KM = 110.0          # the origin's OWN residence catchment (tight; the hub is a
                                  # competitor it leaks to, not part of its demand)
def _resolve_friction():
    """Find the friction raster: AVIA_FRICTION env wins, else the known MAP filenames in C:\\Avia."""
    if os.environ.get("AVIA_FRICTION"):
        return os.environ["AVIA_FRICTION"]
    for c in (r"C:\Avia\2020_motorized_friction_surface.geotiff",
              r"C:\Avia\2020_motorized_friction_surface.tif",
              r"C:\Avia\friction_2019.tif", r"C:\Avia\friction_2019.geotiff"):
        if os.path.exists(c):
            return c
    return r"C:\Avia\friction_2019.tif"


FRICTION_PATH = _resolve_friction()
_DRIVE = None
_DT_CACHE = {}                    # (origin, radius, airport, n_locs) -> [minutes]; drive times are
                                  # att/logit-independent, so cache across calibration sweeps


def _drive_engine():
    """Lazy global friction-raster drive-time engine; None if the raster/libs are absent so the
    catchment falls back to great-circle cleanly. Built once per process."""
    global _DRIVE
    if _DRIVE is None:
        try:
            from drive_times import DriveTimes
            d = DriveTimes(FRICTION_PATH)
            _DRIVE = d if d.available() else False
        except Exception:
            _DRIVE = False
    return _DRIVE or None


def _con(db):
    # R3: reuse one read-only base connection per store path (cursor per call). See db_registry.
    from db_registry import con_ro
    return con_ro(db)


def _norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().replace(".", " ").replace("-", " ").split())


def _gc_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


_NAME_IDX = None
def _name_index(dump=DUMP):
    """Geonames city name -> (lat, lon), most-populous match per name. Loaded once."""
    global _NAME_IDX
    if _NAME_IDX is None:
        idx = {}
        with open(dump, encoding="utf-8") as fh:
            for line in fh:
                f = line.rstrip("\n").split("\t")
                if len(f) < 15:
                    continue
                try:
                    lat, lon, pop = float(f[4]), float(f[5]), int(f[14] or 0)
                except ValueError:
                    continue
                for nm in (f[1], f[2]):
                    k = _norm(nm)
                    if k and (k not in idx or pop > idx[k][2]):
                        idx[k] = (lat, lon, pop)
        _NAME_IDX = idx
    return _NAME_IDX


_AP = None
def _origin_geo(code):
    global _AP
    if _AP is None:
        import airportsdata
        _AP = airportsdata.load("IATA")
    r = _AP.get(code.upper())
    return (r["lat"], r["lon"], r["country"]) if r and r["lat"] is not None else (None, None, None)


def origin_catchment_poo(sabre_db, origin_airport, dest_codes, year=None, radius_km=DEMAND_RADIUS_KM,
                         dump=DUMP, top=250):
    """Point-of-origin cities whose RESIDENTS live within radius_km of the origin airport (geocoded
    poo_city_name, same country as the origin), ranked by demand to the destination. Residence-based
    so a resident who departs the hub is still counted; geographic so the hub's own city is excluded."""
    olat, olon, octry = _origin_geo(origin_airport)
    if olat is None:
        return []
    dc = ",".join("?" * len(dest_codes))
    where = [f"destination_airport IN ({dc})", "poo_city IS NOT NULL", "TRIM(poo_city) <> ''"]
    params = list(dest_codes)
    if octry:
        where.append("poo_country = ?"); params.append(octry)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    # DETERMINISM: MIN(name) not ANY_VALUE (a stable display name -> stable geocode -> stable radius
    # filter), and a poo_city tiebreaker on the top-N cut so ties at the LIMIT boundary resolve the
    # same way every run. Without these the catchment membership jitters run-to-run (~0.2-0.4% on
    # natural/propensity/captured), which is float-order-class noise, not a model signal.
    sql = (f"SELECT poo_city, MIN(poo_city_name) nm, SUM(passengers) p FROM sabre "
           f"WHERE {' AND '.join(where)} GROUP BY poo_city ORDER BY p DESC, poo_city LIMIT {int(top)}")
    con = _con(sabre_db)
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    idx = _name_index(dump)
    keep = []
    for code, name, _p in rows:
        c = idx.get(_norm(name or ""))
        if c and _gc_km(olat, olon, c[0], c[1]) <= radius_km:
            keep.append(code)
    return keep


def market_and_current(sabre_db, poo_cities, dest_codes, origin_airport, year=None):
    """natural = the catchment residents' measured demand to the destination metro by true origin
    (any departure airport). current = the part already departing the origin. Plus the avg fare."""
    if not poo_cities:
        return 0.0, 0.0, 0.0
    pc = ",".join("?" * len(poo_cities)); dc = ",".join("?" * len(dest_codes))
    where = [f"poo_city IN ({pc})", f"destination_airport IN ({dc})"]
    params = list(poo_cities) + list(dest_codes)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    sql = (f"SELECT COALESCE(SUM(passengers),0), "
           f"COALESCE(SUM(CASE WHEN origin_airport=? THEN passengers ELSE 0 END),0), "
           f"COALESCE(SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),0) "
           f"FROM sabre WHERE {' AND '.join(where)}")
    con = _con(sabre_db)
    try:
        r = con.execute(sql, params + [origin_airport]).fetchone()
        return float(r[0] or 0), float(r[1] or 0), float(r[2] or 0)
    finally:
        con.close()


def haul_radius_km(gcd_km):
    """Catchment radius. NOTE (reverted 30 Jun 2026): a haul-SCALED radius (wide for long sectors) was
    tried and backfired - a 400km circle round a hub merges distinct major metros (Boston/DC leak onto
    JFK), inflating long-haul forecasts (2500-6000km band went 1.36 -> 1.55). Willingness-to-drive is
    real for a SECONDARY airport but must not merge separate primary-metro markets. Held flat at 220km;
    the short-under / long-over haul residual is a genuine effect needing a different lever than radius."""
    return 220.0


def qsi_capture_share(oag_db, week, origin, dest_codes, competing_airports,
                      proposed_freq, proposed_block_min, mct_file=None, dump=DUMP,
                      radius_km=220.0, qsi_scale=100.0, logit_scale=0.008, att_exponent=0.0,
                      served_index=None, diag_out=None):
    # att_exponent default 0.0 (size pull OFF) until real drive-time access is wired: the domestic
    # basket wants ~0.65 but that needs true road times or it collapses Genoa (3.5hr Apennine drive
    # to Milan that great-circle reads as 1.5hr). Size pull + real drive times get calibrated together.
    """The origin's ACCESS + QSI + SIZE share of the market via the catchment choice model: each
    locale chooses an airport by drive-time access, the route's schedule quality (QSI service_value),
    AND the airport's general SIZE pull (attractiveness = OAG size_m ** att_exponent). The size pull
    is what the domestic basket proved necessary: a big hub draws traffic BEYOND its catchment and
    beyond the specific route's frequency (network, fares, reliability, connections), so a Sacramento
    resident uses San Francisco for New York far more than population or drive-time alone implies. The
    old engine zeroed attractiveness when QSI was used (double-count worry); the data shows QSI and
    size are NOT redundant, and dropping size over-credited the secondary ~1.9x. share =
    catchment[origin] / total; propensity cancels, so it multiplies the MEASURED market cleanly."""
    import geonames as G, catchment as C, route_qsi as RQ, oag_served as OAS
    import airportsdata
    ap = airportsdata.load("IATA")
    # diag_out, when a dict is passed, is filled with the connection-set summary the QSI machinery
    # already computes. Nothing else changes: the return signature and every existing caller stand.
    _r = RQ.airport_qsi_to_dest(oag_db, week, dest_codes, competing_airports,
                                proposed_origin=origin, proposed_freq=proposed_freq,
                                proposed_block_min=proposed_block_min, mct_file=mct_file,
                                with_diag=(diag_out is not None))
    if diag_out is not None:
        qd, _d = _r
        if _d:
            diag_out.update(_d)
    else:
        qd = _r
    o = ap.get(origin)
    if not o or o["lat"] is None:
        tot = sum(v for v in qd.values() if v > 0)
        return ((qd.get(origin, 0.0) / tot) if tot else 0.0), qd
    sv = RQ.service_values_from_qsi(qd, scale=qsi_scale)
    idx = served_index if served_index is not None else OAS.build_served_index(oag_db, week)
    locs = G.near_point(dump, o["lat"], o["lon"], radius_km, min_pop=5000, propensity=1.0)
    airports = [C.Airport(c, lat=ap[c]["lat"], lon=ap[c]["lon"],
                          attractiveness=max(OAS.size_m(idx, c, 0.5), 1e-3),
                          service_value=sv.get(c, 0.0))
                for c in competing_airports if c in ap and ap[c]["lat"] is not None]
    # REAL road drive times where the friction raster is present (Genoa->Milan 3.5hr, not great-
    # circle's 1.5hr); run_catchment prefers Locale.drive_min over straight-line. One MCP per airport.
    dt = _drive_engine()
    if dt is not None and locs:
        pts = [(l.lat, l.lon) for l in locs]
        for a in airports:
            key = (origin, round(radius_km, 1), a.code, len(locs))
            times = _DT_CACHE.get(key)
            if times is None:
                times = dt.times_from(a.code, ap[a.code]["lat"], ap[a.code]["lon"], pts)
                _DT_CACHE[key] = times
            if times:
                for l, t in zip(locs, times):
                    l.drive_min[a.code] = t
    params = C.CatchmentParams(method="gencost", logit_scale=logit_scale, value_of_time_per_hr=60.0,
                               att_exponent=att_exponent)
    res = C.run_catchment(locs, airports, params, home=origin)
    cat = res.get("catchment", {}); tot = sum(cat.values())
    return ((cat.get(origin, 0.0) / tot) if tot else 0.0), qd


def dest_metro_share(oag_db, week, origin, dest_airport, dest_codes, freq, block_min, mct_file=None):
    """The specific destination airport's QSI share of its metro for service from the origin - the
    DESTINATION leg of the split. Without it, a route into a SECONDARY metro airport (Southend or
    Luton for London, Bergamo for Milan, Vnukovo for Moscow) is wrongly credited the WHOLE metro's
    market and over-reads many-fold. Symmetric to the origin share: the metro's airports 'compete'
    for the origin's traffic, scored by QSI (frequency/service), origin and destination swapped in
    the same scorer. Returns 1.0 for a single-airport metro or an unknown destination airport."""
    if not dest_airport or len(dest_codes) <= 1 or dest_airport not in dest_codes:
        return 1.0
    import route_qsi as RQ
    qd = RQ.airport_qsi_to_dest(oag_db, week, [origin], list(dest_codes),
                                proposed_origin=dest_airport, proposed_freq=freq,
                                proposed_block_min=block_min, mct_file=mct_file)
    tot = sum(v for v in qd.values() if v > 0)
    return (qd.get(dest_airport, 0.0) / tot) if tot else 1.0


# Purpose-linked size pull (att_exponent), calibrated on measured outturn: leisure routes let a
# secondary keep its catchment (att ~0.50, Hawaii/Cancun served set), business routes are hub-loyal
# but only modestly (att ~0.55). The driver is trip purpose, not distance: 5hr Hawaii and 5hr
# SF-NY split on it. Premium cabin share (Sabre F/J/W) is the measured proxy.
# NOTE: business end cut 0.75 -> 0.55 after the feed-inclusive Y2 back-test - the steep exponent
# over-credited the big hub airport's local capture (FSC-forecastable ran 2.21x hot, hub 1.46 vs
# non-hub 0.84). 0.55 compresses that; re-calibrate here first if the hub/non-hub split persists.
ATT_LEISURE, ATT_BUSINESS = 0.50, 0.55
PREM_LO, PREM_HI = 0.05, 0.15      # premium share spans ~4% (leisure) to ~15% (business trunks);
                                   # the New York transcons read 13-15%, Hawaii/Cancun ~5%


def att_from_premium(prem):
    """Map a route's premium-cabin share to the size-pull exponent (leisure 0.50 .. business 0.80)."""
    if prem <= PREM_LO:
        return ATT_LEISURE
    if prem >= PREM_HI:
        return ATT_BUSINESS
    return ATT_LEISURE + (ATT_BUSINESS - ATT_LEISURE) * (prem - PREM_LO) / (PREM_HI - PREM_LO)


def front_cabin_share(sabre_db, airports, dest_codes, year=None):
    """Measured BUSINESS AND FIRST share of the market, from Sabre. Excludes premium economy.

    Added 10 August 2026 for the economics, which splits demand between the front cabin and the back
    and caps each separately. It could not use premium_share below, because that counts premium
    economy as premium while OAG's business_seats + first_seats does not, and the store has no
    premium economy column at all: it sits inside economy_seats. Measured on SJC-TPE, the two
    definitions read 26.95% and 18.06% of the same market, against a China Airlines A350-900 cabin
    that is 10.5% business and first. Comparing a demand share on one definition with a seat share
    on another produces a spill figure that means nothing.

    premium_share is deliberately left alone: it feeds att_from_premium, which is calibrated on its
    current definition, and changing it would move every forecast for a reason that has nothing to
    do with cabins.
    """
    ph_a = ",".join("?" * len(airports)); ph_d = ",".join("?" * len(dest_codes))
    where = [f"origin_airport IN ({ph_a})", f"destination_airport IN ({ph_d})"]
    params = list(airports) + list(dest_codes)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    sql = ("SELECT COALESCE(SUM(CASE WHEN upper(cabin_class) LIKE '%BUSINESS%' "
           "OR upper(cabin_class) LIKE '%FIRST%' THEN passengers ELSE 0 END),0), "
           "COALESCE(SUM(passengers),0) "
           f"FROM sabre WHERE {' AND '.join(where)}")
    con = _con(sabre_db)
    try:
        p, t = con.execute(sql, params).fetchone()
        return (float(p) / float(t)) if t else 0.0
    finally:
        con.close()


def premium_share(sabre_db, airports, dest_codes, year=None):
    """Measured premium-cabin share (business/first/premium-economy) of the market, from Sabre.
    Feeds the att size-pull term ONLY. For a cabin split use front_cabin_share above, which is on
    the same definition as the seat counts."""
    ph_a = ",".join("?" * len(airports)); ph_d = ",".join("?" * len(dest_codes))
    where = [f"origin_airport IN ({ph_a})", f"destination_airport IN ({ph_d})"]
    params = list(airports) + list(dest_codes)
    if year is not None:
        where.append("source_year = ?"); params.append(year)
    sql = ("SELECT COALESCE(SUM(CASE WHEN upper(cabin_class) LIKE '%BUSINESS%' "
           "OR upper(cabin_class) LIKE '%FIRST%' OR upper(cabin_class) LIKE '%PREMIUM%' "
           "THEN passengers ELSE 0 END),0), COALESCE(SUM(passengers),0) "
           f"FROM sabre WHERE {' AND '.join(where)}")
    con = _con(sabre_db)
    try:
        p, t = con.execute(sql, params).fetchone()
        return (float(p) / float(t)) if t else 0.0
    finally:
        con.close()


# P2P level trim, MARKET-SIZE-KEYED (supersedes the Item 9 flat per-type trim, 8 Jul 2026). The offset-0
# held-out grade (val24_o0/val25_o0) showed the engine over-forecasts forecastable P2P ~1.5x UNIFORM across
# type (FSC/LCC/ULCC all ~1.5 - type does not discriminate), so the trim is keyed on the MEASURED market
# (known at forecast time), not type. Fitted on 2016-2018 ONLY (calib_market_trim.py), each size bucket
# taking the multiplier that MAXIMISES the share within +/-20% of outturn, floored so no bucket's trimmed
# median falls below 0.92 (stops a wide right-skewed bucket being over-trimmed into a big-market
# UNDER-forecast). Validated held-out with the isolated A/B (compare_market_trim.py) vs the old flat trim:
# +/-20% +1.4pp (2024) / +1.3pp (2025), median de-biased and |log err| lower on BOTH years - clears the
# ship gate. Applied to every type (type does not discriminate; induced LCC/ULCC handled by the demand
# floor, not here). The remaining error is capture SPREAD not level - the confidence tier (T9) scopes the
# 2/3-within-20% claim, a trim cannot reach it. Edit both numbers and re-validate to change.
_SIZE_TRIM = [(15000.0, 0.765), (50000.0, 0.821), (150000.0, 0.809), (float("inf"), 0.745)]
MARKET_FACTOR_BY_TYPE = {
    "FSC":      _SIZE_TRIM,
    "ULCC":     _SIZE_TRIM,
    "LCC":      _SIZE_TRIM,
    "Regional": _SIZE_TRIM,
}
DEFAULT_MARKET_FACTOR = MARKET_FACTOR_BY_TYPE["FSC"]      # fallback for an unknown type


def market_factor_for(airline_type):
    """The trim table for an airline type (FSC / LCC / ULCC / Regional); FSC's if unknown."""
    return MARKET_FACTOR_BY_TYPE.get(airline_type, DEFAULT_MARKET_FACTOR)


def _market_size_mult(market, table):
    """Multiplier for the captured P2P demand given the measured addressable market and a bucket table."""
    if not table:
        return 1.0
    for edge, f in table:
        if (market or 0) < edge:
            return float(f)
    return 1.0


# --- INDUCED / new-market demand floor (LCC/ULCC + FSC hub launches) ------------------------------
# An induced route carries far more than its measured O&D: the market did not pre-exist. Two fill
# mechanisms, one floor. LCC/ULCC: an ultra-low fare stimulates point-to-point demand on a thin route.
# FSC: a hub carrier launches into a thin O&D and fills the aircraft from its NETWORK/alliance feed
# (LOT over WAW, etc). Both fill deployed capacity to a stable seat factor, so a low measured-market/
# capacity ratio flags them before outturn (induced <=0.18, forecastable >=0.73) and we FLOOR demand at
# capacity x the achieved load factor for the type and haul. FSC ADDED 8 Jul: FSC induced is 62% of the
# cohort (976/1568) and read ~0.17 of outturn un-floored; the floor lifts held-out 2024 from 1% to 45%
# within +/-20% (compare_induced_fsc.py, fit 2016-2018). We do NOT feed-gate it: the engine's own feed
# estimate is too low to identify the fed routes (that under-read is what we are fixing), and feed-thin
# and feed-present FSC routes centre alike under the blanket floor (0.89 vs 0.88 held-out). The stimulation
# FARE (below) is LCC/ULCC only - FSC fills at a normal fare via feed, so FSC keeps its measured market
# fare in the economics (no INDUCED_FARE entry), and the floor is a MAX so it only ever lifts an under-read.
INDUCED_TYPES = ("LCC", "ULCC", "FSC")   # FSC kept (preserves the LOT@WAW fortress-hub fill). The LGA-FWA over-read is
                                         # prevented upstream instead: auto-gauge sizes metal to demand so the floor is
                                         # never handed oversized capacity to fill (cortex_app api_forecast / api_optimise).
INDUCED_MKT_CAP_MAX = 0.40          # measured-market/capacity below this = induced-likely
_INDUCED_HAUL_KM = (800.0, 2500.0, 6000.0)
# achieved seat factor by [type][haul band: <800 / 800-2500 / 2500-6000 / >6000 km], from the 6yr launch
# history (analyze_induced.py section C, type x haul medians on bt_v2_6yr_factored). Well-populated cells
# at their median; two thin/noisy cells nudged (see notes) - adjust with domain judgement.
INDUCED_LF = {   # 6yr run (bt_6yr_induced) section C, type x haul medians
    "LCC":  (0.77, 0.72, 0.73, 0.42),   # <800 n42, 800-2500 n155, 2500-6000 n109, >6000 n16
    "ULCC": (0.77, 0.82, 0.50, 0.45),   # <800 n48, 800-2500 n176; 2500-6000 median 0.46 (n41, wide IQR
                                         # .39-.87, nudged to 0.50 - lower than LCC same haul, twice); >6000 n5 thin
    "FSC":  (0.69, 0.68, 0.43, 0.38),   # fit-year (2016-2018) medians, validated held-out (compare_induced_fsc.py)
}
# achieved ONE-WAY fare (USD) an induced route stimulates at, by [type][same haul bands]. This is the low
# fare that BUYS the fill, applied in the economics so an induced route shows a full cabin at a thin yield.
# 6yr run (bt_6yr_induced) section G, outturn-year P2P avg fare. ULCC sits below LCC on short/medium haul
# (the cheaper model), as expected; both converge ~$475 on the rare >6000km cell.
INDUCED_FARE = {
    "LCC":  (114.0, 166.0, 244.0, 471.0),
    "ULCC": (108.0, 139.0, 185.0, 481.0),
}


def _induced_haul_idx(gcd_km):
    g = gcd_km or 0.0
    for k, edge in enumerate(_INDUCED_HAUL_KM):
        if g < edge:
            return k
    return len(_INDUCED_HAUL_KM)


def _induced_lf(gcd_km, airline_type):
    """Achieved induced seat factor for a type and haul, or None if the type is not induced-modelled."""
    tbl = INDUCED_LF.get((airline_type or "").upper())
    return tbl[_induced_haul_idx(gcd_km)] if tbl else None


def _induced_fare(gcd_km, airline_type):
    """Stimulation one-way fare (USD) for an induced type and haul, or None if not induced-modelled."""
    tbl = INDUCED_FARE.get((airline_type or "").upper())
    return tbl[_induced_haul_idx(gcd_km)] if tbl else None


def forecast(sabre_db, oag_db, week, origin, dest_codes, competing_airports, *, year=None,
             aircraft="A21X", freq=7, block_min=540, stimulation=1.15, growth=0.0, growth_years=0,
             max_plan_lf=MAX_PLAN_LF, mct_file=None, annual_capacity=None, att_exponent=None,
             dest_airport=None, airline=None, catchment_mult=1.0, feed_cfg=None,
             coverage_override=None, market_override=None, share_override=None,
             market_factor=None, season="annual", season_share=1.0, season_weeks=52.0,
             airline_type=None, induced_floor=False, airport_capture=1.0,
             p2p_demand_override=None, **_ignore):
    """The connected loop, the calibrated way. The WIDE market = the whole service area's measured
    O&D to the destination (Sabre, all competing airports - board-point, which is what Sabre gives).
    The origin's forecast = that measured market x its QSI SHARE (its schedule quality vs the field,
    which is small for a secondary airport because the hub dominates) x stimulation, then bounded by
    the aircraft. NO population, NO propensity - the share, not a population apportionment, is the
    splitter. annual_capacity overrides the computed capacity (e.g. the route's actual OAG capacity)."""
    import sabre_catchment as SC
    import od_source
    # O&D source selector (DB1B vs Sabre). Default AVIA_OD_SOURCE=sabre -> byte-identical to Sabre.
    split, market, avg_fare, od_src = od_source.market_split(sabre_db, competing_airports, dest_codes,
                                                             year=year)
    market *= (1 + growth) ** growth_years
    current = float(split.get(origin, 0.0)) * ((1 + growth) ** growth_years)
    # SABRE COVERAGE GROSS-UP: the recorded market under-reads off-GDS bookings (LCC-country and
    # short-haul), so gross the measured market up to true size BEFORE capture - the forecast is
    # then a share of the real market, not the GDS fragment. P2P only for now; the feed carries its
    # own coverage correction later. See coverage.py for the country/haul factors and provenance.
    _cov = 1.0
    try:
        import coverage as COV, airportsdata as _APD
        _ap = _APD.load("IATA")
        _dref = dest_airport or (dest_codes[0] if dest_codes else "")
        _o, _d = _ap.get(origin), _ap.get(_dref)
        _oc = _o.get("country") if _o else None
        _dc = _d.get("country") if _d else None
        if _o and _d and _o.get("lat") is not None and _d.get("lat") is not None:
            _gcd = _gc_km(_o["lat"], _o["lon"], _d["lat"], _d["lon"])
        else:
            _gcd = max((block_min - 20.0) * 7.0 * 1.852, 100.0)
        _cov = COV.gross_up(_oc, _dc, _gcd)
    except Exception:
        _cov = 1.0
    if od_src == od_source.DB1B:
        _cov = 1.0   # DB1B is the full-market actual; the GDS coverage gross-up is Sabre-only
    if coverage_override is not None:          # EXPERT override of the auto coverage factor
        _cov = float(coverage_override)
    market *= _cov
    current *= _cov
    if market_override is not None:            # EXPERT: custom catchment market (use their number)
        market = float(market_override)
    # purpose-linked size pull: measure the route's premium share, map to att, unless overridden
    prem = premium_share(sabre_db, competing_airports, dest_codes, year=year)
    att = att_from_premium(prem) if att_exponent is None else att_exponent
    # Measured on the seat-count definition, for the economics cabin split. Not used here.
    try:
        front = front_cabin_share(sabre_db, competing_airports, dest_codes, year=year)
    except Exception:
        front = None
    # catchment radius scaled to this sector's length (inverse of the block-time formula gcd_km ~
    # (block-20)*7*1.852), so short sectors use a tight catchment and long ones a wide one
    gcd_est = max((block_min - 20.0) * 7.0 * 1.852, 100.0)
    # catchment_mult widens the catchment for price-driven traffic (LCC/ULCC pax drive further for a
    # cheap fare than FSC pax will). Default 1.0 = unchanged; the caller sets it by the named airline's
    # business model. Distinct from the reverted haul-scaling: this is purpose-driven, not distance.
    radius = haul_radius_km(gcd_est) * catchment_mult
    # _qdiag carries the connection-set summary out of the QSI machinery so BT2 can read the
    # connecting structure the engine already builds. Added 9 August 2026; nothing else changes.
    _qdiag = {}
    share, qd = qsi_capture_share(oag_db, week, origin, dest_codes, competing_airports,
                                  freq, block_min, mct_file=mct_file, att_exponent=att, radius_km=radius, diag_out=_qdiag)
    if share_override is not None:             # EXPERT override of the origin's capture share (wins)
        share = float(share_override)
    else:                                      # measured airport capture truth (surveys / mobility data)
        try:
            import airport_capture as _ACAP
            _apc = _ACAP.capture_for(origin, market)   # tapered on very large markets a secondary can't supply
            if _apc is not None:
                # FREQUENCY SENSITIVITY. Measured 10 August 2026: with the measured factor in force
                # the capture is a CONSTANT, so SJC-TPE returns 0.32 at three, five, seven, ten and
                # fourteen weekly, and the forecast cannot answer what a seventh frequency buys.
                # That is the first question an airline planner asks in the room.
                #
                # The QSI share does move: 0.0449 at 3/wk to 0.0835 at 14/wk on SJC-TPE, 86% across
                # the range. It is simply discarded here. But it cannot replace the measured factor
                # either: it reads 0.059 at daily against a measured 0.32, the factor of five that
                # is exactly the "access over-credits a secondary once it has a nonstop" problem the
                # measured factors were introduced to fix.
                #
                # So the measured factor is kept as the ANCHOR and the QSI share supplies only the
                # SHAPE, as a ratio to the same computation at a daily reference. At seven weekly
                # the answer is unchanged, which is why the default is off and nothing moves without
                # being asked. AVIA_FREQ_SENSITIVE=1 turns it on.
                _apc = float(_apc)
                if os.environ.get("AVIA_FREQ_SENSITIVE", "").strip() in ("1", "true", "on"):
                    try:
                        # REFERENCE FREQUENCY. The anchor holds where the shape term is 1.0, so this
                        # is the frequency at which the route reproduces the measured airport factor.
                        # It stays at daily. airport_capture records SJC's 0.32 as "30-35% with
                        # service" from the Avia survey and cell-phone data, with no frequency
                        # attached, so the reference is a judgement rather than a measurement. Daily
                        # is the one setting that leaves the verified case alone: SJC-TPE CI at 7x
                        # returns 134,616 two-way with the switch on or off. Measured 10 August 2026,
                        # a reference of 4.0 lifts the same 7x case to 159,784, which is 18.7% above
                        # the figure the dashboard has been reproducing. Settable for testing only.
                        _fref_sw = float(os.environ.get("AVIA_FREQ_REF", "7.0") or 7.0)
                        _ref = qsi_capture_share(oag_db, week, origin, dest_codes,
                                                 competing_airports, _fref_sw, block_min,
                                                 mct_file=mct_file, att_exponent=att,
                                                 radius_km=radius)[0]
                        if _ref and share and _ref > 0:
                            _apc *= (float(share) / float(_ref))
                    except Exception:
                        pass                    # anchor unchanged rather than a wrong shape
                share = _apc
        except Exception:
            pass
    # DESTINATION leg: the specific destination airport takes only its QSI share of its metro, so a
    # route into a secondary metro airport is not credited the whole metro market (1.0 if single-airport).
    dshare = dest_metro_share(oag_db, week, origin, dest_airport, dest_codes, freq, block_min, mct_file)
    captured = market * share * dshare * stimulation

    # THE CALIBRATED MODEL, when the caller has one. p2p_demand_override is BT2's own local nonstop
    # forecast for this route, and it REPLACES the whole line above rather than scaling it.
    #
    # NONE OF THE FOUR MULTIPLIERS IS REAPPLIED, and that is the part to get right. BT2's training
    # target is launch_pax, the actual nonstop passengers a new route carried, so the market, the
    # origin's capture share, the destination metro share and the stimulation uplift are all already
    # inside the number it returns. Multiplying by them again would count each of them twice.
    #
    # GROWTH IS THE ONE THING THAT MUST BE ADDED. Line 489 grows `market` to the forecast year before
    # this point, so `captured` above is a forecast-year figure. BT2 is anchored on base_mkt, the
    # measured O&D in the latest full year, so its output is a CURRENT-year figure and has to be
    # carried forward the same way or the two are a year apart. That is the basis fault that cost 13
    # August twice over.
    #
    # AND NO SEPARATE MATURITY FACTOR, which is a decision rather than an omission. BT2 predicts a
    # route's FIRST year. connecting_maturation of 13 August measured the local leg on the same
    # routes at x1.013 from year one to year two and x1.104 to year three, and market growth alone
    # over two years accounts for most of that, so a route-specific ramp is not separable from the
    # growth already applied here. Applying both would double count the same 10%.
    _model_p2p = p2p_demand_override is not None
    if _model_p2p:
        captured = float(p2p_demand_override) * ((1 + growth) ** growth_years)
    # CONNECTING FEED (beyond the destination hub), alliance-weighted for the named airline - the other
    # half of a QSI total. Grown with the market. 0 unless an airline is given (feed is carrier-specific).
    feed_beyond = feed_behind = 0.0
    beyond_pdew = behind_pdew = {}
    beyond_detail = behind_detail = {}
    if airline and dest_airport:
        try:
            import route_feed as RFEED
            g = (1 + growth) ** growth_years
            # Name the route origin for the feed layer. competing_airports is the whole catchment and
            # its order is the catchment builder's, so the QSI feed cannot take the first entry as the
            # origin: on SJC-TPE that is Sonoma County. The timezone reference for the hub arrival and
            # the circuity screen both key off it.
            if feed_cfg is not None:
                feed_cfg.setdefault("route_origin", origin)
            bt, beyond_pdew, beyond_detail = RFEED.feed_side(sabre_db, oag_db, week, competing_airports,
                                              dest_airport, year, beyond=True, airline=airline,
                                              feed_cfg=feed_cfg, detail=True)
            # behind uses the SPECIFIC route origin (feeders physically connect there), not the wider
            # catchment - else a route into a small airport wrongly inherits a big neighbour's feed bank.
            ht, behind_pdew, behind_detail = RFEED.behind_feed(sabre_db, oag_db, week, [origin], [dest_airport],
                                              year, airline=airline, feed_cfg=feed_cfg, detail=True)
            feed_beyond, feed_behind = (bt or 0.0) * g, (ht or 0.0) * g
            if g != 1.0:
                for _dm in (beyond_detail, behind_detail):
                    for _c in _dm.values():
                        _c["base"] *= g; _c["captured"] *= g; _c["pdew"] *= g
        except Exception:
            feed_beyond = feed_behind = 0.0
            beyond_pdew = behind_pdew = {}
            beyond_detail = behind_detail = {}
    # Item 9: capped market-size discount on the P2P capture, keyed off the MEASURED market (natural),
    # so a thin-market over-read is trimmed while mid/large markets (already unbiased) are untouched.
    # Applied to captured only (the P2P over-read); the feed carries its own calibration.
    # MARKET BUILD, recorded 11 August 2026. Every step below already happened; nothing here changes a
    # number. It exists because the payload reported a single "natural market" of 321,830 two-way on
    # SJC-TPE and a single capture of 0.32, and 99.3% of that market boards at San Francisco today. A
    # planner shown "the market is 321,830 and we will capture 32%" answers that this is San
    # Francisco's market, and the meeting stops there. The chain has to be visible so the base each
    # rate applies to is unambiguous, and so the combined allocation-and-capture step is not mistaken
    # for a capture of San Jose's own catchment.
    # The labels below are the ones a client sees. They are written for a reader meeting the model for
    # the first time, because this table goes on a slide: every line says what it is in words, and
    # STEP_NOTES carries one sentence of explanation for each. Shorthand a modeller understands
    # ("dshare", "market-size trim") reads as jargon to an airline planner and gets queried.
    # THE BUILD LIST MUST DESCRIBE THE DERIVATION THAT ACTUALLY HAPPENED. This table goes on a slide,
    # and when the calibrated model produced the local number none of the four QSI steps below took
    # place: there was no catchment market, no capture share, no destination metro share and no
    # stimulation uplift. Printing them anyway would be a client-facing explanation of arithmetic
    # that was not performed, which is the same fault as a status line that says what the code did
    # not check, on the one page where it would be read by an airline.
    if _model_p2p:
        _bld = [("Passengers flying to the destination from the whole service area today", market, None),
                ("Local passengers forecast by the calibrated model, from this airport's own "
                 "record and the proposed schedule", float(p2p_demand_override), None)]
        if growth_years:
            _bld.append(("Carried forward to the forecast year at the stated market growth",
                         captured, (1 + growth) ** growth_years))
    else:
        _bld = [("Passengers flying to the destination from the whole service area today", market, None),
                ("Of those, the share a nonstop from this airport would win", market * share, share),
                ("Of those, the share using this destination airport", market * share * dshare, dshare),
                ("Extra passengers created by having a direct service", captured, stimulation)]
    # THE CALIBRATION FACTORS BELOW ARE QSI'S AND ARE NOT APPLIED TO THE MODEL. market_factor is a
    # trim learned to correct the QSI capture on large markets, and airport_capture is a per-airport
    # correction learned from the same engine's past errors. BT2 was trained on outturn directly, so
    # both are corrections to a derivation it did not use, and applying them would be correcting a
    # different engine's bias on this one's number.
    if market_factor and not _model_p2p:
        _msz = _market_size_mult(market, market_factor)
        captured *= _msz
        _bld.append(("Trim applied because one new service wins less of a very large market",
                     captured, _msz))
    # PER-AIRPORT CAPTURE CALIBRATION (T7): an origin that consistently captures more/less than the
    # general catchment model gets a factor learned from its own past launches (build_airport_factors.py).
    if airport_capture and airport_capture != 1.0 and not _model_p2p:
        captured *= float(airport_capture)
        _bld.append(("Adjustment for how this airport has performed on its own past launches",
                     captured, float(airport_capture)))
    # DESTINATION thin-market lift: a genuine secondary (SJC) has its INBOUND demand under-allocated by the
    # catchment model, but ONLY where the O&D is thin/catchment-fed; a big directly-measured market (LHR-SJC)
    # needs no help. Conditioned on the measured market so it can't over-forecast a mature large route.
    if dest_airport and not _model_p2p:
        try:
            _dtf = __import__("airport_capture").dest_thin_factor(dest_airport, market)
            captured *= _dtf
            if _dtf != 1.0:
                _bld.append(("Uplift where the destination airport serves a thin market",
                             captured, _dtf))
        except Exception:
            pass
    # HAUL recalibration (opt-in, default OFF): a TWO-SIDED distance-response correction around a healthy
    # 800-2500km middle. The mature-horizon backtest (Step 0, confirmed NOT a start-up ramp) shows a stable
    # haul bias: <800km UNDER-forecasts (median circa 0.45, likely Sabre under-reading short-haul O&D) and
    # 2500-6000km OVER-forecasts (median circa 1.83). Lift captured below the SHORT floor, trim it above the
    # LONG floor, leave the middle untouched. All params tune on the hold-out. Short uplift is OFF by default
    # (_sbeta 0) so the DB1B source test - which may close the short side as a data gap, not a factor - is
    # tried first. AVIA_HAUL_TRIM=1 enables. Old AVIA_HAUL_TRIM_FLOOR/BETA still work as the long-side names.
    haul_trim = 1.0
    if (not _model_p2p) and os.environ.get("AVIA_HAUL_TRIM", "").strip().lower() in ("1", "true", "on", "yes"):
        _hk = gcd_est if (gcd_est and gcd_est > 0) else max((block_min - 20.0) * 7.0 * 1.852, 100.0)
        _sfloor = float(os.environ.get("AVIA_HAUL_SHORT_FLOOR", "800"))
        _sbeta  = float(os.environ.get("AVIA_HAUL_SHORT_BETA", "0"))      # 0 = short uplift OFF (test DB1B first)
        _scap   = float(os.environ.get("AVIA_HAUL_SHORT_CAP", "2.2"))     # cap the short-haul uplift
        _lfloor = float(os.environ.get("AVIA_HAUL_LONG_FLOOR", os.environ.get("AVIA_HAUL_TRIM_FLOOR", "2500")))
        _lbeta  = float(os.environ.get("AVIA_HAUL_LONG_BETA",  os.environ.get("AVIA_HAUL_TRIM_BETA", "0.35")))
        if _sbeta > 0 and _hk < _sfloor:
            haul_trim = min((_sfloor / _hk) ** _sbeta, _scap)            # short-haul uplift (capped)
            captured *= haul_trim
        elif _hk > _lfloor:
            haul_trim = (_lfloor / _hk) ** _lbeta                        # long-haul trim
            captured *= haul_trim
    # FREQUENCY capture discount (opt-in, default OFF): a thin, low-frequency long-haul nonstop is over-
    # credited by the QSI share - it is scored as winning the market when a 2x-weekly 3000km nonstop wins a
    # sliver (time-sensitive demand still connects on the hubs, the rest does not fly). Discount captured
    # toward the daily-service benchmark for long sectors; high-frequency and short-haul untouched.
    # Diagnosed on the NA pre-COVID long-haul set: fc/p2p vs deployed capacity corr -0.42, low-capacity
    # median 2.16 vs high-capacity 1.15, worst on ULCC/leisure P2P (ORF-PHX, OAK-MEM, SJU-PIT). Cause-based
    # and forecast-time-knowable (proposed frequency is an input). AVIA_FREQ_DISCOUNT=1 enables; FLOOR
    # (2500 km), REF (7/wk = daily), BETA (0.5), CAP (0.4 floor on the discount) tune it on the hold-out.
    freq_discount = 1.0
    if (not _model_p2p) and os.environ.get("AVIA_FREQ_DISCOUNT", "").strip().lower() in ("1", "true", "on", "yes"):
        _ffloor = float(os.environ.get("AVIA_FREQ_DISC_FLOOR", "2500"))
        _fref = float(os.environ.get("AVIA_FREQ_DISC_REF", "7"))
        _fbeta = float(os.environ.get("AVIA_FREQ_DISC_BETA", "0.5"))
        _fcap = float(os.environ.get("AVIA_FREQ_DISC_CAP", "0.4"))
        if gcd_est > _ffloor and freq and freq < _fref:
            freq_discount = max((freq / _fref) ** _fbeta, _fcap)
            captured *= freq_discount
    # SEASONAL mode: scale the annual demand to the operating season's share of the year (from the
    # monthly profile; caller supplies the SEASON's capacity via annual_capacity). season_share 1.0 =
    # annual, unchanged. A summer service carries its summer share of the O&D, not half of it.
    if season_share and season_share != 1.0:
        captured *= season_share
        feed_beyond *= season_share
        feed_behind *= season_share
        # scale the itemised feed volume too, so the per-market detail rows sum to the seasonal
        # totals. base (the annual O&D market) and pdew (a per-departure intensity) are left as-is.
        for _dm in (beyond_detail, behind_detail):
            for _c in _dm.values():
                if _c.get("captured") is not None:
                    _c["captured"] *= season_share
    feed = feed_beyond + feed_behind
    total_demand = captured + feed
    natural, leaked, repatriated, capture_rate = market, max(market - current, 0.0), 0.0, share

    if annual_capacity is None:
        try:
            from aircraft_economics import AIRCRAFT
            ac = AIRCRAFT.get(aircraft, {})
            seats = (ac.get("econ_seats", 0) + ac.get("bus_seats", 0)) or 180
        except Exception:
            seats = 180
        annual_capacity = seats * freq * season_weeks          # EACH-WAY annual seats (demand is each-way;
        # season_weeks<52 for a seasonal service). Matches the economics, aircraft_select and the backtest's
        # operated capacity, which are all each-way. NB: was seats*freq*weeks*2 (both directions), which
        # halved the reported load factor against each-way demand and doubled the induced-floor basis.
    # INDUCED FLOOR: for a low-cost route whose measured market is far below the metal it is deploying,
    # measured-market x share x stim cannot see the fare-stimulated demand. Floor total demand at the
    # capacity times the seat factor comparable LCC/ULCC launches reached (INDUCED_LF). The low fare that
    # buys this fill is applied in the economics by the caller, so the P&L stays honest.
    induced = False
    induced_lf_used = None
    induced_fare_used = None
    # THE INDUCED FLOOR IS A QSI CORRECTION TOO, and it is the least obvious of the six. It exists
    # because the engine anchors on the MEASURED O&D and an induced route carries far more than a
    # market that did not pre-exist, so demand is floored at capacity times an achieved load factor.
    # BT2 is trained on outturn, which already contains whatever the induced routes in its sample
    # actually carried, so flooring its output would add the correction a second time.
    #
    # And it would do so in the most damaging place: INDUCED-MODELLING of the memory records the
    # flagship under-read on new markets at circa 0.10, which is exactly the population where a
    # double correction is largest. If BT2 turns out to under-read induced routes as well, that is
    # measured on BT2 and corrected on BT2, not inherited from the engine it replaced.
    if induced_floor and annual_capacity and not _model_p2p \
            and (airline_type or "").upper() in INDUCED_TYPES:
        if (market / annual_capacity) < INDUCED_MKT_CAP_MAX:
            _lf = _induced_lf(gcd_est, airline_type)
            if _lf:
                _floor = annual_capacity * _lf
                if total_demand < _floor:
                    induced = True
                    induced_lf_used = _lf
                    induced_fare_used = _induced_fare(gcd_est, airline_type)   # low fare for the economics
                    captured = max(captured, _floor - feed)   # uplift attributed to stimulated P2P
                    total_demand = captured + feed
    # ALL-DATA BUCKET CALIBRATION (bucket_model.json): nudge total demand by the airport-bucket factor fitted on
    # the whole launch history (the all-data calibration). Bounded; flows through the cap, split and economics.
    # SUPPRESSED WHEN THE CALIBRATED MODEL PRODUCED THE LOCAL LEG, and this one is suppressed WHOLE
    # rather than on the captured term alone. bucket_correct is fitted on TOTAL demand against the
    # whole launch history, so it corrects the QSI engine's total error. When the local leg comes
    # from BT2 the total is no longer that engine's, and a factor fitted against one engine's bias
    # applied to another engine's number is not a calibration, it is noise with a provenance.
    #
    # The feed loses its share of the correction too. That is a real cost and it is stated rather
    # than worked around: the honest way back is to refit bucket_correct on whichever engine ships,
    # not to apply half of an old fit to half of a new number.
    try:
        import bucket_correct as _BC
        _bf = 1.0 if _model_p2p else _BC.forecast_factor(origin, dest_airport, market, gcd_est)
        if _bf and _bf != 1.0:
            captured *= _bf; feed *= _bf; feed_beyond *= _bf; feed_behind *= _bf
            total_demand = captured + feed
            _bld.append(("Adjustment for airports of this size and distance, from past launches",
                         captured, _bf))
            for _dm in (beyond_detail, behind_detail):
                for _c in _dm.values():
                    if _c.get("captured") is not None: _c["captured"] *= _bf
                    if _c.get("pdew") is not None: _c["pdew"] *= _bf
    except Exception:
        pass
    carried = min(total_demand, annual_capacity * max_plan_lf)      # P2P + feed compete for the seats
    spill = max(total_demand - carried, 0.0)
    load = (carried / annual_capacity) if annual_capacity else 0.0

    # TOTAL-PRESERVING P2P/CONNECTING RE-SPLIT (split_share): the engine's leg split over-credits P2P on
    # connecting-heavy routes (a route into DOH/ATL/IST is mostly transfer, not local). Re-split the CARRIED
    # total by each endpoint's connectivity so the reported P2P/connecting, the PDEW connecting magnitude and
    # the economics read correctly - WITHOUT changing the total (so +/-20% on the total is untouched). Inert
    # until hub_localness.json exists (falls back to global localness ~= no re-split). Feed detail is scaled
    # to the corrected connecting magnitude, keeping its per-city shape.
    _rawtot = max(total_demand, 1.0)                     # default: keep the raw engine legs, scaled to carried
    p2p_share_v = captured / _rawtot
    p2p_carried = carried * p2p_share_v
    if carried < total_demand:
        _bld.append(("Limited to what the aircraft and frequency can seat; the rest is turned away",
                     captured * carried / _rawtot, carried / _rawtot))
    conn_carried = carried - p2p_carried
    # THE CONNECTIVITY FLOOR, and whether it should still be applied.
    #
    # It exists because the engine's leg split under-credited transfer traffic at non-US hubs, where
    # the US GDS misses Asian transfer bookings. That was true of the FLAT feed. It is no longer
    # obviously true of the QSI feed: measured on SJC-TPE against the 2025 analyst on his own 12:00
    # schedule, the raw QSI feed reads 1.04x his beyond and 0.83x his behind, while the floor then
    # rescales the reported beyond from 12,467 to 27,324 two-way. A correction sized for a feed that
    # under-read is an over-correction on a feed that does not.
    #
    # So it is now a switch rather than an assumption. DEFAULT ON, because it is what shipped and
    # what every previous number was produced with, and because retiring it moves the headline. Set
    # feed_cfg["split_floor"] = False to run without it. The back-test decides which ships; this
    # exists so the two can be measured against each other rather than argued about.
    _floor_on = True if feed_cfg is None else bool(feed_cfg.get("split_floor", True))
    try:
        import split_share as _SS
        if _floor_on and _SS.available():                # only re-split when a real connectivity table is loaded
            _dref = dest_airport or (dest_codes[0] if dest_codes else "")
            _sh = _SS.p2p_share(origin, _dref)
            _engine_conn = carried * (feed / _rawtot)    # the engine's own connecting, scaled to carried
            _resplit_conn = carried * (1.0 - _sh)        # what connectivity implies
            # ONLY LIFT connecting, never cut it: the engine's known failure is UNDER-crediting connecting, so a
            # re-split that says LESS means the hub is under-scored in Sabre (esp. non-US hubs like TPE/HKG/ICN
            # where the US GDS misses Asian transfer traffic). Floor at the engine's estimate so it can't regress.
            conn_carried = max(_engine_conn, _resplit_conn)
            p2p_carried = max(0.0, carried - conn_carried)
            p2p_share_v = (p2p_carried / carried) if carried else _sh
            if feed > 1.0:                               # scale the connecting aggregates + PDEW detail to match
                _sc = conn_carried / feed
                feed_beyond *= _sc                       # behind/beyond breakdown reconciles to conn_carried
                feed_behind *= _sc
                for _dm in (beyond_detail, behind_detail):
                    for _c in _dm.values():
                        if _c.get("captured") is not None:
                            _c["captured"] *= _sc
                        if _c.get("pdew") is not None:
                            _c["pdew"] *= _sc
    except Exception:
        pass

    # The connectivity re-split is the last thing that moves point to point, and it can move it a long
    # way: on SJC-TPE it takes P2P from 62% of the carried total to 45%, because a route into a hub
    # like Taipei is mostly transfer traffic and the engine's own leg split under-credits that.
    if abs(p2p_carried - captured * carried / max(_rawtot, 1.0)) > 1.0:
        _bld.append(("Re-split between local and connecting passengers; the total does not change",
                     p2p_carried, None))
    _bld.append(("Point to point passengers carried each year", p2p_carried, None))

    rec = "demand fits the aircraft"
    if spill > 0.02 * max(total_demand, 1):
        need = math.ceil(total_demand / (annual_capacity * max_plan_lf / freq)) if annual_capacity else freq
        rec = f"demand exceeds {freq}x/week {aircraft}: {spill:,.0f} spilled - upsize or ~{need}x/week"
    return {
        "origin": origin, "dest_metro": dest_codes, "competing_airports": len(competing_airports),
        "natural_market": round(natural), "current_via_origin": round(current),
        "leaked": round(leaked), "avg_fare": round(avg_fare, 2),
        "qsi_share": round(share, 4), "dest_share": round(dshare, 4), "capture_rate": capture_rate,
        # The connection set, summarised. legs_n and the three connection-type sums are what BT2
        # needs and what bt2_capture used to recompute by calling build_connections a second time.
        "legs_n": _qdiag.get("n_legs"), "n_connections": _qdiag.get("n_connections"),
        "s_online": _qdiag.get("s_online"), "s_alliance": _qdiag.get("s_alliance"),
        "s_interline": _qdiag.get("s_interline"),
        "repatriated": round(repatriated), "premium_share": round(prem, 4), "att_exponent": round(att, 3),
        "front_cabin_share": (round(front, 4) if front is not None else None),
        "coverage_gross_up": round(_cov, 3), "od_source": od_src, "haul_trim": round(haul_trim, 3),
        "freq_discount": round(freq_discount, 3),
        "captured_demand": round(captured), "connecting_feed": round(feed),
        # The point-to-point chain, step by step, each with the multiplier that produced it. Each-way.
        "market_build": [{"step": n, "value": round(v), "factor": (round(m, 4) if m else None),
                          "note": STEP_NOTES.get(n)}
                         for n, v, m in _bld],
        "market_measured_pre_grossup": round(market / _cov) if _cov else round(market),
        "p2p_carried": round(p2p_carried), "connecting_carried": round(conn_carried),
        "p2p_share": round(p2p_share_v, 3),
        "feed_beyond": round(feed_beyond), "feed_behind": round(feed_behind),
        "total_demand": round(total_demand), "stimulation": stimulation,
        "induced": induced, "induced_lf": induced_lf_used, "induced_fare": induced_fare_used,
        "aircraft": aircraft, "frequency": freq, "annual_capacity": round(annual_capacity),
        "carried_forecast": round(carried), "spill": round(spill),
        "season": season, "season_share": round(season_share, 3),
        "planned_load_factor": round(load, 3), "recommendation": rec,
        "beyond_pdew": beyond_pdew, "behind_pdew": behind_pdew,
        "beyond_detail": beyond_detail, "behind_detail": behind_detail,
    }
