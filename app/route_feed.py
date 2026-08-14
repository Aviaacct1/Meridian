#!/usr/bin/env python3
"""
Avia Solutions - the CONNECTING FEED layer (behind-origin + beyond-destination), the missing half
of a real QSI forecast. A route O-H carries three things: local O-H (P2P, route_forecast has it),
BEHIND-O feed (points behind O connecting at O onto O-H) and BEYOND-H feed (O-H passengers carrying
on past H). Total = P2P + behind + beyond = the number an airline negotiates over. Broken out by
connecting city and expressed as PDEW (passengers daily each way), so it drops into the standard
report tables.

CONSTRUCTION (the validated BA method, sabre_generate_demand reproduced its LHR feed 48,115 to 0.15%):
  beyond market = O-catchment -> {H's served destinations}, measured single-connection O&D from Sabre
                  grouped by destination city, x direct/indirect factor.
  capture       = the new O-H-X one-stop routing's QSI share of that market vs existing routings.
  feed          = sum over X of (market_X x capture_X), as PDEW.
Behind is the mirror: {points that feed O} -> D via O.

ACCEPTANCE TEST: LHR-SJC, California catchment (SFO/LAX/SAN), 2013 - the LHR-side (beyond-LHR) feed
must land near the analyst's 48,115. Run:  py -3.12 route_feed.py --oag C:\\Avia\\oag.duckdb --sabre
C:\\Avia\\sabre.duckdb --origin SFO,LAX,SAN --hub LHR --year 2013

STATUS: v1 - the MARKET side reuses the validated construction; the per-city CAPTURE is rebuilt from
OAG here and is the piece to CALIBRATE against 48,115 (the global connecting-capture constant, like
the POC's qsi_adjustment). Behind-feed wired same as beyond with O/D swapped.
"""
import argparse, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

WORK_DAYS = 365.0                     # PDEW = annual O&D / 365 / 2 (each way)
DEFAULT_CONN_CAPTURE = 0.025          # global connecting-capture, calibrated to BA LHR-SJC = 48,115 with
                                      # the alliance weighting factored out separately (a cleaner residual
                                      # than the old flat capture; the back-test will confirm it generalises)


def _con(db):
    # R3: reuse one read-only base connection per store path (cursor per call). See db_registry.
    from db_registry import con_ro
    return con_ro(db)


def _preagg_from_cfg(feed_cfg):
    """R1: return a valid preagg store path from feed_cfg, or None to use the live full-scan queries.
    connecting_market and behind_market both read the same single-connection O&D, served by the
    od_single table, so both feed sides get point lookups when the store is present."""
    pa = (feed_cfg or {}).get("preagg")
    if not pa:
        return None
    import preagg
    return pa if preagg.available(pa) else None


_AP = None
def _coords(code):
    global _AP
    if _AP is None:
        import airportsdata
        _AP = airportsdata.load("IATA")
    r = _AP.get((code or "").upper())
    return (r["lat"], r["lon"]) if r and r["lat"] is not None else None


def _gc(a, b):
    if not a or not b:
        return None
    la1, lo1 = math.radians(a[0]), math.radians(a[1]); la2, lo2 = math.radians(b[0]), math.radians(b[1])
    x = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def on_the_way(origin_airports, hub, scope, circuity=1.35):
    """Keep only beyond destinations where the hub is roughly ON THE ROUTE, not a backtrack: distance
    origin->hub->X must be <= circuity x direct origin->X. Kills California->LHR->JFK; keeps ->Paris."""
    pts = [c for c in (_coords(o) for o in origin_airports) if c]
    hc = _coords(hub)
    if not pts or not hc:
        return scope
    ocen = (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
    oh = _gc(ocen, hc) or 0
    keep = []
    for x in scope:
        xc = _coords(x)
        if not xc:
            continue
        direct = _gc(ocen, xc)
        if direct and direct > 100 and (oh + (_gc(hc, xc) or 0)) <= circuity * direct:
            keep.append(x)
    return keep


def hub_served(oag_db, week, hub, min_rows=1):
    """Destinations the hub actually serves that week (the beyond scope), from OAG."""
    con = _con(oag_db)
    try:
        return [r[0] for r in con.execute(
            "SELECT arr_airport FROM oag WHERE week=? AND dep_airport=? GROUP BY arr_airport "
            "HAVING COUNT(*) >= ?", [week, hub, min_rows]).fetchall()]
    finally:
        con.close()


def hub_fed_by(oag_db, week, hub, min_rows=1):
    """Origins that feed the hub that week (the behind scope): airports that fly TO the hub."""
    con = _con(oag_db)
    try:
        return [r[0] for r in con.execute(
            "SELECT dep_airport FROM oag WHERE week=? AND arr_airport=? GROUP BY dep_airport "
            "HAVING COUNT(*) >= ?", [week, hub, min_rows]).fetchall()]
    finally:
        con.close()


# Major-carrier alliance map (extendable). Used to price the onward leg: a route into a hub scoops
# the connecting bank when the operating airline flies the onward leg itself (online) or a partner does
# (same-alliance); otherwise it's a weak interline. BA at LHR scoops Oneworld; a Star carrier there can't.
ONEWORLD = {"AA","BA","CX","QF","QR","JL","IB","AY","MH","UL","RJ","AT","LA","AS"}
STAR = {"UA","LH","AC","SQ","NH","TG","OS","LX","SK","TP","TK","OZ","SA","ET","AV","CA","ZH","MS","BR","A3","LO","SN","CM","NZ"}
SKYTEAM = {"DL","AF","KL","AZ","KE","CI","MU","CZ","VN","GA","SV","AR","AM","KQ","ME","RO","OK","UX","SU"}
ALLIANCE = {}
for _al, _set in (("OW", ONEWORLD), ("*A", STAR), ("ST", SKYTEAM)):
    for _c in _set:
        ALLIANCE[_c] = _al
# QSI connection coefficients (same as the engine): online > same-alliance > interline
CNX_ONLINE, CNX_ALLIANCE, CNX_INTERLINE = 1.0, 0.615, 0.25


def hub_onward_carriers(oag_db, week, hub):
    """{beyond_airport: set(operating carriers on hub->that airport)} that week, from OAG."""
    con = _con(oag_db)
    try:
        out = {}
        for arr, car in con.execute(
                "SELECT arr_airport, carrier FROM oag WHERE week=? AND dep_airport=? "
                "GROUP BY arr_airport, carrier", [week, hub]).fetchall():
            out.setdefault(arr, set()).add((car or "").upper())
        return out
    finally:
        con.close()


def conn_coeff(airline, onward_carriers, cfg=None):
    """How well the operating airline connects onto the onward leg: it flies it itself (online), a
    same-alliance partner flies it, or only unrelated carriers do (interline). 1.0 if no airline given.
    cfg may override the three coefficients (Expert connection-modelling)."""
    if not airline:
        return 1.0
    onl = (cfg or {}).get("cnx_online", CNX_ONLINE)
    alw = (cfg or {}).get("cnx_alliance", CNX_ALLIANCE)
    itl = (cfg or {}).get("cnx_interline", CNX_INTERLINE)
    a = airline.upper(); al = ALLIANCE.get(a)
    cs = {c for c in onward_carriers if c}
    if a in cs:
        return onl
    if al and any(ALLIANCE.get(c) == al for c in cs):
        return alw
    return itl


# Point-to-point carriers that do not interline - a route they fly carries no connecting feed. Applied
# only under feed_cfg (the fix), so default behaviour is unchanged. Extend as the carrier set grows.
P2P_CARRIERS = {"FR", "W6", "U2", "G4", "NK", "F9", "VY", "EW", "W9", "DY", "PC", "VF", "HV", "TO",
                "0B", "6E", "QZ", "AK", "JQ", "TR", "5J", "SY", "XY", "LS", "BY", "OR", "XQ", "DP"}


def hub_dominance(oag_db, week, airport, airline):
    """Operating airline's share of departures at 'airport' that week - the proxy for how much of the
    connecting bank it scoops at its own fortress (Lufthansa at Frankfurt scoops; a spoke carrier does
    not). Returns 0..1, or 0 if unknown."""
    if not airline or not airport:
        return 0.0
    con = _con(oag_db)
    try:
        # Distinct flights, not raw rows: the store repeats each record per region label and the
        # factor varies by carrier, so a raw count mis-states dominance. One rule, in wave_cache.
        from wave_cache import carrier_flights
        rows = carrier_flights(con, week, [airport])
    finally:
        con.close()
    tot = sum(int(n or 0) for _, n in rows)
    if not tot:
        return 0.0
    a = airline.upper()
    return sum(int(n or 0) for c, n in rows if (c or "").upper() == a) / tot


def _cap_eff(base, dominance, cfg):
    """Feed capture scaled by the operating airline's hub dominance. cfg None = flat base (current
    behaviour, preserves the BA LHR-SJC calibration). With cfg: base x (floor + gain x dominance), so a
    fortress carrier scoops far more of its own feed than a spoke carrier of the same market."""
    if not cfg:
        return base
    return base * (cfg.get("dom_floor", 0.5) + cfg.get("dom_gain", 1.0) * dominance)


def connecting_market(sabre_db, origin_airports, beyond_airports, year, factor_indirect=1.044):
    """Measured single-connection + direct O&D from the origin catchment to each beyond destination,
    grouped by destination city (the beyond market to be captured). Returns {dest_city: pax}."""
    if not origin_airports or not beyond_airports:
        return {}
    oa = ",".join("?" * len(origin_airports)); ba = ",".join("?" * len(beyond_airports))
    # CONNECTING itineraries only (single stop, exclude NON-STOP): a nonstop O->X flyer won't reroute
    # via the hub, so only the already-connecting market is addressable feed the new route wins a share of.
    sql = (f"SELECT destination_airport dc, SUM(passengers * {factor_indirect}) p "
           f"FROM sabre WHERE source_year=? AND origin_airport IN ({oa}) "
           f"AND destination_airport IN ({ba}) "
           f"AND connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL "
           f"GROUP BY 1")
    con = _con(sabre_db)
    try:
        rows = con.execute(sql, [year] + list(origin_airports) + list(beyond_airports)).fetchall()
        return {r[0]: float(r[1] or 0) for r in rows}
    finally:
        con.close()


def feed_side(sabre_db, oag_db, week, origin_airports, hub, year, capture=DEFAULT_CONN_CAPTURE,
              factor_indirect=1.044, beyond=True, airline=None, feed_cfg=None, detail=False):
    """One side of the feed. beyond=True: O-catchment -> H's destinations (beyond H). beyond=False:
    H's feeders -> the route dest via O (behind). Per-city capture is alliance-weighted by the operating
    airline's connection onto the onward leg (online/alliance/interline). Returns (total, {city: pdew}).
    feed_cfg (the fix): zero for point-to-point carriers, and scale capture by the airline's dominance at
    the hub (it scoops the onward bank at its own fortress)."""
    if feed_cfg and airline and airline.upper() in P2P_CARRIERS:
        return (0.0, {}, {}) if detail else (0.0, {})
    _circ = (feed_cfg or {}).get("circuity", 1.35)
    _fac = (feed_cfg or {}).get("factor_indirect", factor_indirect)
    scope = hub_served(oag_db, week, hub) if beyond else hub_fed_by(oag_db, week, hub)
    scope = [x for x in scope if x not in origin_airports]           # exclude the local O-H leg
    scope = on_the_way(origin_airports, hub, scope, circuity=_circ)  # drop backtracking destinations
    _pa = _preagg_from_cfg(feed_cfg)

    def _sabre_beyond(_o, _d, _y=None):
        # The year is an argument so od_source can ask for a second year when it indexes a
        # DOT vintage forward on Sabre's own growth. Default is the run's year, unchanged.
        _yy = year if _y is None else _y
        if _pa:
            import preagg
            return preagg.connecting_market(_pa, _o, _d, _yy, _fac)
        return connecting_market(sabre_db, _o, _d, _yy, _fac)

    # US-market credibility rule. od_source leads with DOT DB1B on the all-US pairs of the
    # scope and leaves the rest on Sabre, so a US airport sees its own domestic feed measured
    # on the government figure it validates against. Off unless AVIA_OD_SOURCE is set.
    import od_source as _OS
    market, _src, _dot_share = _OS.feed_market(_sabre_beyond, origin_airports, scope, year,
                                               factor_indirect=_fac, group="dest")
    if feed_cfg is not None:
        feed_cfg["_beyond_source"] = _src
        feed_cfg["_beyond_dot_share"] = _dot_share
    # OPT-IN Engine V2 (feed_cfg['qsi_feed']): the schedule-quality QSI feed. Scores the new
    # route's connection quality per onward market and competes for share against rival one-stops
    # (qsi_feed.beyond_capture, the frozen analyst QSI). REPLACES flat capture x conn_coeff (the
    # alliance term lives inside the itinerary score); k = qsi_k re-levels to outturn. Needs the
    # proposed schedule in feed_cfg (dep_time_mins / flying_mins / route_freq); without a dep time
    # it falls through to V1 and counts the fallback, so an A/B can see how often that happened.
    if feed_cfg and feed_cfg.get("qsi_feed") and feed_cfg.get("dep_time_mins") is not None:
        try:
            import qsi_feed as QF
            boards = feed_cfg.get("_boards")
            if boards is None:
                from wave_cache import CacheBoards, OagBoards
                wc = feed_cfg.get("wave_cache")
                boards = CacheBoards(wc) if (wc and os.path.exists(wc)) else OagBoards(oag_db)
                feed_cfg["_boards"] = boards
            mctm = feed_cfg.get("_mct_master")
            if mctm is None:
                import mct_bank as MB
                mctm = MB.load_mct()
                feed_cfg["_mct_master"] = mctm
            qshare = QF.beyond_capture(boards, week, origin_airports, hub, list(market.keys()),
                                       airline, feed_cfg["dep_time_mins"],
                                       feed_cfg.get("flying_mins") or 540,
                                       feed_cfg.get("route_freq", 7), mct=mctm, cfg=feed_cfg)
            k = feed_cfg.get("qsi_k", 0.06)
            captured = {city: pax * k * qshare.get(city, 0.0) for city, pax in market.items()}
            total = sum(captured.values())
            pdew = {city: round(v / WORK_DAYS / 2.0, 1) for city, v in sorted(
                captured.items(), key=lambda kv: -kv[1])}
            if detail:
                dmap = {city: {"base": market[city], "share": k * qshare.get(city, 0.0),
                               "captured": captured.get(city, 0.0),
                               "pdew": round(captured.get(city, 0.0) / WORK_DAYS / 2.0, 1)}
                        for city in sorted(market, key=lambda c: -captured.get(c, 0.0))}
                return total, pdew, dmap
            return total, pdew
        except Exception:
            feed_cfg["_qsi_fallbacks"] = feed_cfg.get("_qsi_fallbacks", 0) + 1
    onward = hub_onward_carriers(oag_db, week, hub) if airline else {}
    dom = hub_dominance(oag_db, week, hub, airline) if feed_cfg else 0.0
    cap = _cap_eff(capture, dom, feed_cfg)
    # OPT-IN schedule banking: weight each onward market by the share of its frequency that is
    # genuinely connectable within MCT of the (optimised) hub arrival. Off by default; back-test first.
    sched = {}
    if feed_cfg and feed_cfg.get("mct_banking"):
        try:
            import mct_bank as MB
            _mct = feed_cfg.get("_mct")
            if _mct is None:
                _mct = MB.load_mct(); feed_cfg["_mct"] = _mct
            bank = MB.hub_bank(oag_db, week, hub)
            best_arr, sched = MB.optimise(bank, _mct, hub, market=market)
            feed_cfg["_best_arr_beyond"] = best_arr
        except Exception:
            sched = {}
    captured = {city: pax * cap * conn_coeff(airline, onward.get(city, set()), feed_cfg)
                * (sched.get(city, 1.0) if sched else 1.0)
                for city, pax in market.items()}
    total = sum(captured.values())
    pdew = {city: round(v / WORK_DAYS / 2.0, 1) for city, v in sorted(
        captured.items(), key=lambda kv: -kv[1])}
    if detail:
        dmap = {}
        for city in sorted(market, key=lambda c: -captured.get(c, 0.0)):
            cv = captured.get(city, 0.0)
            dmap[city] = {"base": market[city], "share": cap * conn_coeff(airline, onward.get(city, set()), feed_cfg),
                          "captured": cv, "pdew": round(cv / WORK_DAYS / 2.0, 1)}
        return total, pdew, dmap
    return total, pdew


def _centroid(airports):
    pts = [c for c in (_coords(x) for x in airports) if c]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts)) if pts else None


def feeders_to(oag_db, week, origins):
    """Airports that fly INTO the origin that week (the behind scope), from OAG."""
    ph = ",".join("?" * len(origins))
    con = _con(oag_db)
    try:
        return [r[0] for r in con.execute(
            f"SELECT DISTINCT dep_airport FROM oag WHERE week=? AND arr_airport IN ({ph})",
            [week] + list(origins)).fetchall()]
    finally:
        con.close()


def inbound_carriers(oag_db, week, origins):
    """{feeder airport: set(carriers on feeder->origin)} - to price the inbound leg's alliance match."""
    ph = ",".join("?" * len(origins))
    con = _con(oag_db)
    try:
        out = {}
        for dep, car in con.execute(
                f"SELECT dep_airport, carrier FROM oag WHERE week=? AND arr_airport IN ({ph}) "
                f"GROUP BY dep_airport, carrier", [week] + list(origins)).fetchall():
            out.setdefault(dep, set()).add((car or "").upper())
        return out
    finally:
        con.close()


def behind_market(sabre_db, feeders, dest_airports, year, factor_indirect=1.044):
    """Measured connecting O&D from each feeder to the route DESTINATION (feeder -> ... -> dest), the
    market that could route feeder->origin->dest. Keyed by feeder airport."""
    if not feeders or not dest_airports:
        return {}
    fa = ",".join("?" * len(feeders)); da = ",".join("?" * len(dest_airports))
    sql = (f"SELECT origin_airport oy, SUM(passengers * {factor_indirect}) p FROM sabre WHERE source_year=? "
           f"AND origin_airport IN ({fa}) AND destination_airport IN ({da}) "
           f"AND connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL GROUP BY 1")
    con = _con(sabre_db)
    try:
        return {r[0]: float(r[1] or 0) for r in con.execute(
            sql, [year] + list(feeders) + list(dest_airports)).fetchall()}
    finally:
        con.close()


def behind_feed(sabre_db, oag_db, week, origin_airports, dest_airports, year, capture=DEFAULT_CONN_CAPTURE,
                factor_indirect=1.044, airline=None, circuity=1.35, feed_cfg=None, detail=False):
    """BEHIND-origin feed: points that feed the origin, connecting there onto the O-D flight. Feeder ->
    origin -> destination. Alliance coefficient on the inbound feeder->origin leg. Returns (total, pdew).
    feed_cfg (the fix): zero for point-to-point carriers; use the (higher) behind base rate; and scale by
    the airline's dominance at the ORIGIN - a carrier at its own fortress scoops most of its behind bank."""
    if feed_cfg and airline and airline.upper() in P2P_CARRIERS:
        return (0.0, {}, {}) if detail else (0.0, {})
    _circ = (feed_cfg or {}).get("circuity", circuity)
    _fac = (feed_cfg or {}).get("factor_indirect", factor_indirect)
    ocen, dcen = _centroid(origin_airports), _centroid(dest_airports)
    od = _gc(ocen, dcen) or 0
    feeders = [y for y in feeders_to(oag_db, week, origin_airports)
               if y not in origin_airports and y not in dest_airports]
    if ocen and dcen:
        kept = []
        for y in feeders:
            yc = _coords(y)
            if not yc:
                continue
            yd = _gc(yc, dcen)
            if yd and yd > 100 and ((_gc(yc, ocen) or 0) + od) <= _circ * yd:   # Y->O->D on the way
                kept.append(y)
        feeders = kept
    _pa = _preagg_from_cfg(feed_cfg)

    def _sabre_behind(_o, _d, _y=None):
        _yy = year if _y is None else _y
        if _pa:
            import preagg
            return preagg.behind_market(_pa, _o, _d, _yy, _fac)
        return behind_market(sabre_db, _o, _d, _yy, _fac)

    # The behind side is the one a US airport cares most about, being its own domestic
    # catchment feeding the new route. Grouped by feeder, so the FEEDERS are partitioned.
    import od_source as _OS
    market, _src, _dot_share = _OS.feed_market(_sabre_behind, feeders, dest_airports, year,
                                               factor_indirect=_fac, group="origin")
    if feed_cfg is not None:
        feed_cfg["_behind_source"] = _src
        feed_cfg["_behind_dot_share"] = _dot_share
    # OPT-IN Engine V2: the mirror of feed_side's QSI branch - feeder arrivals at the ORIGIN
    # compete for the feeder->destination markets against one-stops over rival hubs.
    if feed_cfg and feed_cfg.get("qsi_feed") and feed_cfg.get("dep_time_mins") is not None:
        try:
            import qsi_feed as QF
            boards = feed_cfg.get("_boards")
            if boards is None:
                from wave_cache import CacheBoards, OagBoards
                wc = feed_cfg.get("wave_cache")
                boards = CacheBoards(wc) if (wc and os.path.exists(wc)) else OagBoards(oag_db)
                feed_cfg["_boards"] = boards
            mctm = feed_cfg.get("_mct_master")
            if mctm is None:
                import mct_bank as MB
                mctm = MB.load_mct()
                feed_cfg["_mct_master"] = mctm
            cfgq = dict(feed_cfg)
            cfgq.setdefault("route_flying_mins", feed_cfg.get("flying_mins"))
            qshare = QF.behind_capture(boards, week, origin_airports, dest_airports,
                                       list(market.keys()), airline,
                                       feed_cfg["dep_time_mins"], mct=mctm, cfg=cfgq)
            k = feed_cfg.get("qsi_k_behind", feed_cfg.get("qsi_k", 0.06))
            captured = {y: pax * k * qshare.get(y, 0.0) for y, pax in market.items()}
            total = sum(captured.values())
            pdew = {y: round(v / WORK_DAYS / 2.0, 1) for y, v in sorted(
                captured.items(), key=lambda kv: -kv[1])}
            if detail:
                dmap = {y: {"base": market[y], "share": k * qshare.get(y, 0.0),
                            "captured": captured.get(y, 0.0),
                            "pdew": round(captured.get(y, 0.0) / WORK_DAYS / 2.0, 1)}
                        for y in sorted(market, key=lambda c: -captured.get(c, 0.0))}
                return total, pdew, dmap
            return total, pdew
        except Exception:
            feed_cfg["_qsi_fallbacks"] = feed_cfg.get("_qsi_fallbacks", 0) + 1
    onward = inbound_carriers(oag_db, week, origin_airports) if airline else {}
    base = (feed_cfg.get("behind_cap", capture) if feed_cfg else capture)
    dom = hub_dominance(oag_db, week, (origin_airports[0] if origin_airports else None), airline) if feed_cfg else 0.0
    cap = _cap_eff(base, dom, feed_cfg)
    captured = {y: pax * cap * conn_coeff(airline, onward.get(y, set()), feed_cfg) for y, pax in market.items()}
    total = sum(captured.values())
    pdew = {y: round(v / WORK_DAYS / 2.0, 1) for y, v in sorted(captured.items(), key=lambda kv: -kv[1])}
    if detail:
        dmap = {}
        for y in sorted(market, key=lambda c: -captured.get(c, 0.0)):
            cv = captured.get(y, 0.0)
            dmap[y] = {"base": market[y], "share": cap * conn_coeff(airline, onward.get(y, set()), feed_cfg),
                       "captured": cv, "pdew": round(cv / WORK_DAYS / 2.0, 1)}
        return total, pdew, dmap
    return total, pdew


# TURNAROUND BY FLIGHT TYPE, John's ruling of 14 August. An aircraft that departs the origin at T
# ARRIVED at T minus the turnaround: the two movements are one rotation and are tied together. The
# time it takes is not one number. A widebody off a thirteen-hour sector needs deep cleaning, full
# catering, a crew change and a fuel uplift; a domestic narrowbody turns in under an hour. The
# three cases John named are domestic, continental international, and intercontinental.
#
# THESE ARE PLANNING AVERAGES AND NOT MEASUREMENTS. They are stated here so they can be argued
# with and overridden per case, which is the treatment any figure without a source gets.
TURNAROUND_MIN = {"domestic": 60, "continental": 90, "intercontinental": 180}
CONTINENTAL_MAX_KM = 3000.0


_TURN_TABLE = {}


TURN_HAUL_BANDS = ((1500.0, "under1500"), (3000.0, "1500-3000"), (6000.0, "3000-6000"))


def _turn_band(gcd_km):
    for limit, name in TURN_HAUL_BANDS:
        if (gcd_km or 0) <= limit:
            return name
    return "over6000"


def _measured_turn(aircraft_code, gcd_km=None):
    """The measured turnaround for this aircraft type ON THIS SECTOR LENGTH, or None.

    Built by build_turnarounds.py from OAG on unambiguous single-arrival single-departure
    station-days, which is the only pairing OAG supports without tail numbers.

    KEYED ON TYPE AND HAUL, not type alone. The first table measured an A330-300 at 60 minutes
    and a 777-300ER at 70, which are credible for a short-haul widebody rotation and not for the
    same aeroplane off a thirteen-hour sector. One type covers both operations and a low
    percentile then selects the short-haul end of it.

    p10 within the band rather than the median: a turnaround is the time the aeroplane NEEDS, and
    the median mixes in stations that simply had a long gap. A cell measured on too few
    station-days is marked unusable in the file and is not read; the type's all-haul cell is the
    fallback before the flight-type bands.
    """
    if not aircraft_code:
        return None
    if not _TURN_TABLE:
        path = os.environ.get("AVIA_TURNAROUNDS")
        if not path:
            try:
                import config
                path = os.path.join(str(config.LOCAL_CACHE), "turnarounds_2025.json")
            except Exception:
                path = None
        _TURN_TABLE["_loaded"] = True
        if path and os.path.exists(path):
            try:
                import json
                with open(path, encoding="utf-8") as fh:
                    _TURN_TABLE.update((json.load(fh) or {}).get("types") or {})
            except Exception:
                pass
    row = _TURN_TABLE.get(str(aircraft_code).upper())
    bands = (row or {}).get("bands") if isinstance(row, dict) else None
    if not isinstance(bands, dict):
        return None
    for key in (_turn_band(gcd_km) if gcd_km else None, "any"):
        cell = bands.get(key) if key else None
        if isinstance(cell, dict) and cell.get("usable") and cell.get("p10"):
            return int(cell["p10"])
    return None


def turnaround_mins(origin_country, dest_country, gcd_km, cfg=None, aircraft_code=None):
    """Minutes on stand between arrival and the next departure.

    MEASURED FIRST. Where build_turnarounds.py has a usable figure for this aircraft type it is
    used, because the aeroplane sets the stand time and region only proxies for it. The flight
    type bands below are the fallback and are PLANNING AVERAGES WITH NO SOURCE: same country is
    domestic, different countries within CONTINENTAL_MAX_KM is continental international, which
    is the LATAM and intra-Europe case, and anything longer is intercontinental. A case may
    override either with feed_cfg["turnaround_mins"].
    """
    if cfg and cfg.get("turnaround_mins"):
        return int(cfg["turnaround_mins"])
    measured = _measured_turn(aircraft_code or (cfg or {}).get("aircraft_code"), gcd_km)
    if measured:
        return measured
    oc = (origin_country or "").upper()
    dc = (dest_country or "").upper()
    if oc and dc and oc == dc:
        kind = "domestic"
    elif (gcd_km or 0) <= CONTINENTAL_MAX_KM:
        kind = "continental"
    else:
        kind = "intercontinental"
    return TURNAROUND_MIN[kind]


def parse_windows(spec):
    """Restricted-hours windows as minutes past local midnight: [(start, end), ...].

    Accepts "23:00-06:00", "2300-0600", a comma-separated list of either, or a list of pairs already
    in minutes. A window that crosses midnight is kept as given and handled by in_window.
    """
    if not spec:
        return []
    if isinstance(spec, (list, tuple)) and spec and isinstance(spec[0], (list, tuple)):
        return [(int(a) % 1440, int(b) % 1440) for a, b in spec]

    def _m(t):
        t = str(t).strip()
        if ":" in t:
            h, m = t.split(":")[:2]
        elif len(t) == 4:
            h, m = t[:2], t[2:]
        else:
            h, m = t, "0"
        return (int(h) * 60 + int(m)) % 1440

    # SEPARATORS AS PEOPLE WRITE THEM. A curfew typed as "23:00 to 06:00" raised an unpack error
    # on 14 August, the optimiser fell back to the 11:00 placeholder, and two SJC-TPE runs came
    # back at 11:00 with the curfew silently absent. A restriction that fails to parse must never
    # cost the run its optimiser over punctuation: an airport's night hours are a fact, and the
    # form they were typed in is not one.
    text = str(spec)
    for sep in (" to ", " until ", " till ", "–", "—", " - ", "/"):
        text = text.replace(sep, "-")
    out = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        bits = [b for b in part.split("-") if b.strip()]
        if len(bits) < 2:
            # Named rather than raised as "not enough values to unpack", which tells the person
            # reading the page nothing about what they typed or what was wanted.
            raise ValueError("cannot read the restricted hours %r: expected a window such as "
                             "23:00-06:00, or a comma-separated list of them" % part)
        out.append((_m(bits[0]), _m(bits[1])))
    return out


def in_window(mins, windows):
    """Is this local clock time inside any restricted window? Midnight-crossing handled."""
    m = int(mins) % 1440
    for a, b in windows or []:
        if a == b:
            continue
        if (a < b and a <= m < b) or (a > b and (m >= a or m < b)):
            return True
    return False


def optimise_departure(sabre_db, oag_db, week, origin_airports, origin, hub, dest_airports, year,
                       airline, flying_mins, freq=7, feed_cfg=None, step=60, refine=15,
                       restricted=None, restricted_dest=None, turn_mins=120, check_return=True):
    """Choose the outbound departure time that maximises the connecting traffic the route wins.

    WHY THIS EXISTS. The departure time drives BOTH feed sides and it drives them against each other:
    the time the aircraft leaves the origin sets which behind-origin feeders can make it, and that
    same time plus the block sets the arrival at the hub, which sets which beyond-hub bank it
    connects into. It is also carrier-specific, because an airline connects online onto its own
    onward legs and only interlines onto everyone else's, so the best time for China Airlines at
    Taipei is not the best time for a Star carrier. Until now no departure time existed in the demand
    path at all: cortex_app._schedule_times placed the outbound at 11:00 by default, ran AFTER the
    forecast, and only decorated the payload. Measured across the day on SJC-TPE the beyond capture
    runs 0.98% to 5.43% and the behind capture 0.31% to 2.17%, so the placeholder was choosing the
    answer.

    The objective is connecting passengers, demand-weighted across both sides. Point to point does
    not move with departure time in this engine, so maximising connecting and maximising total demand
    are the same search.

    Both markets are built ONCE and held across the sweep, because the Sabre queries behind them are
    the expensive part and they do not depend on the time of day.

    RESTRICTED HOURS. Many airports cannot take a movement at night, and the best connecting time is
    very often exactly the time they cannot take. San Jose is the case in point: the whole Taipei
    market departs the west coast between midnight and two in the morning, which is inside a night
    restriction. A route is usually constrained at BOTH ends, and the 2025 analyst's schedule note
    says so in as many words: it "seeks to mitigate night curfew restrictions at SJC and capacity
    constraints at TPE".

    `restricted` is one or more windows in the ORIGIN's local time, "23:00-06:00" or a list of them.
    `restricted_dest` is the same in the DESTINATION's local time. BOTH DEFAULT TO NOTHING, because a
    curfew is a fact about an airport that somebody has to know. The tool must not invent one: an
    assumed restriction would move a forecast with no source behind it, which is worse than no
    restriction at all. They are entered when they are known.

    Both screen MOVEMENTS rather than departures, since a curfew stops the aircraft coming back as
    surely as it stops it leaving. At the origin that means the outbound departure and the return
    arrival, which falls out as dep + 2 x block + turnaround because the timezone shift cancels
    between the two legs. At the destination it means the arrival and the return departure, both
    taken off the hub arrival, which carries the shift. check_return turns the second movement off at
    both ends.

    The unrestricted optimum is always computed and returned beside the permitted one, so the cost of
    the restriction can be quoted rather than hidden. That figure is the argument an airport takes to
    a curfew review, and it is worth more than the forecast it comes from.

    Coarse grid at `step` minutes, then a refinement at `refine` minutes either side of the winner.
    Returns (best_dep_mins, {"beyond", "behind", "score", "tried", "restricted",
    "unrestricted_dep", "unrestricted_score", "cost_pax", "return_arrival"}).
    """
    step, refine = max(int(step), 5), max(int(refine or 0), 0)
    cfg = dict(feed_cfg or {})
    cfg.setdefault("route_origin", origin)
    cfg.setdefault("route_flying_mins", flying_mins)
    cfg.setdefault("route_freq", freq)
    _fac = cfg.get("factor_indirect", 1.044)
    _circ = cfg.get("circuity", 1.35)

    # BEYOND market: the catchment's already-connecting demand to everything the hub serves.
    scope = [x for x in hub_served(oag_db, week, hub) if x not in origin_airports]
    scope = on_the_way(origin_airports, hub, scope, circuity=_circ)
    b_mkt = connecting_market(sabre_db, origin_airports, scope, year, _fac)

    # BEHIND market: the feeders' already-connecting demand to the route destination. The specific
    # route origin, not the catchment, because feeders physically connect at the airport being flown.
    feeders = [y for y in feeders_to(oag_db, week, [origin])
               if y not in (origin,) and y not in dest_airports]
    ocen, dcen = _centroid([origin]), _centroid(dest_airports)
    od = _gc(ocen, dcen) or 0
    if ocen and dcen:
        kept = []
        for y in feeders:
            yc = _coords(y)
            if not yc:
                continue
            yd = _gc(yc, dcen)
            if yd and yd > 100 and ((_gc(yc, ocen) or 0) + od) <= _circ * yd:
                kept.append(y)
        feeders = kept
    h_mkt = behind_market(sabre_db, feeders, dest_airports, year, _fac)

    if not b_mkt and not h_mkt:
        return None, {"beyond": 0.0, "behind": 0.0, "score": 0.0, "tried": 0}

    import qsi_feed as QF
    from wave_cache import CacheBoards, OagBoards
    wc = cfg.get("wave_cache")
    boards = cfg.get("_boards") or (CacheBoards(wc) if (wc and os.path.exists(wc)) else OagBoards(oag_db))
    cfg["_boards"] = boards                      # the board grouping memoises here, so hold it
    mctm = cfg.get("_mct_master")
    if mctm is None:
        import mct_bank as MB
        mctm = MB.load_mct()
        cfg["_mct_master"] = mctm

    b_keys, h_keys = list(b_mkt.keys()), list(h_mkt.keys())

    def score(dep):
        """Connecting passengers won at this departure time, both sides, before any capture scaling."""
        bs = QF.beyond_capture(boards, week, origin_airports, hub, b_keys, airline,
                               dep, flying_mins, freq, mct=mctm, cfg=cfg) if b_keys else {}
        hs = QF.behind_capture(boards, week, [origin], dest_airports, h_keys, airline,
                               dep, mct=mctm, cfg=cfg) if h_keys else {}
        b_pax = sum(b_mkt[m] * bs.get(m, 0.0) for m in b_mkt)
        h_pax = sum(h_mkt[y] * hs.get(y, 0.0) for y in h_mkt)
        return b_pax + h_pax, b_pax, h_pax

    windows = parse_windows(restricted)
    windows_d = parse_windows(restricted_dest)

    def permitted(dep):
        """The two movements THIS departure commits: it leaves the origin, and it lands at the hub.

        A CURFEW BLOCKS EVERY MOVEMENT IN ITS WINDOW, arrivals and departures alike, and John
        confirmed that on 14 August. What it does not do is tie the return to the outbound. The
        aircraft does not shuttle: it flies another route from the hub and comes back, so the
        return departure is a FREE VARIABLE and its arrival at the origin is not dep + 2 x block
        + turn. Screening the outbound on a derived return arrival blocked departures that are
        perfectly legal, because a return time exists that lands outside the window whatever the
        outbound does. On SJC-TPE against a 23:00-06:00 origin curfew the derived test alone
        blocked 17:30 through 04:00, which is most of the evening, for a rotation nobody flies.

        The return's own two movements, its departure from the hub and its arrival at the origin,
        are screened where the return is timed, in cortex_app._schedule_times. Both legs are
        curfew-legal; neither is derived from the other.
        """
        if in_window(dep, windows):
            return False
        # THE AIRCRAFT ARRIVED BEFORE IT DEPARTED. A departure at T implies an arrival at
        # T minus the turnaround, and that arrival is a movement at the origin like any other.
        # Without this the optimiser picks departures nobody can fly: on SJC-TPE against a
        # 21:00-06:00 curfew it chose 06:30, which needs an aircraft on stand from 03:30, three
        # and a half hours inside the restriction.
        if in_window(dep - int(turn_mins), windows):
            return False
        if windows_d:
            import qsi_feed as _QF
            arr_hub = _QF._hub_arrival_mins(origin, hub, dep, flying_mins, cfg)
            if in_window(arr_hub, windows_d):
                return False
            # And that inbound aircraft left the hub: its departure is a movement there too.
            # Timezone cancels across the pair, so it left the hub `block` before it landed here.
            if in_window(dep - int(turn_mins) - int(flying_mins), windows_d):
                return False
        return True

    tried = {}
    for dep in range(0, 1440, step):
        tried[dep] = score(dep)
    # An optimum against a constraint lies ON the constraint: an airline schedules right up against a
    # curfew, not near it. Test the boundaries explicitly rather than hope the grid lands on them.
    # Both the moment the restriction lifts and the last minute before it bites, on the outbound and
    # on the return, since either movement can be the binding one.
    _bound = []
    for a, b in windows:                          # origin: the departure and the return arrival
        _bound += [b, a - 1,
                   b - 2 * int(flying_mins) - int(turn_mins),
                   a - 1 - 2 * int(flying_mins) - int(turn_mins)]
    if windows_d:                                 # destination: the arrival and the return departure
        _shift = 0
        try:
            import qsi_feed as _QF
            _shift = (_QF._utc_offset_h(hub) - _QF._utc_offset_h(origin)) * 60
        except Exception:
            pass
        for a, b in windows_d:
            _bound += [b - int(flying_mins) - _shift, a - 1 - int(flying_mins) - _shift,
                       b - int(flying_mins) - _shift - int(turn_mins),
                       a - 1 - int(flying_mins) - _shift - int(turn_mins)]
    for cand in _bound:
        c = int(cand) % 1440
        if c not in tried:
            tried[c] = score(c)

    def pick(only_permitted):
        pool = [d for d in tried if (permitted(d) if only_permitted else True)]
        return max(pool, key=lambda d: tried[d][0]) if pool else None

    best, free_best = pick(True), pick(False)
    if refine and refine < step:                 # walk the neighbourhood of each winner
        for anchor in {b for b in (best, free_best) if b is not None}:
            for dep in range(anchor - step + refine, anchor + step, refine):
                d = dep % 1440
                if d not in tried:
                    tried[d] = score(d)
        best, free_best = pick(True), pick(False)
    _fmt = lambda ws: [f"{a // 60:02d}:{a % 60:02d}-{b // 60:02d}:{b % 60:02d}" for a, b in ws]
    if best is None:                             # every hour of the day is restricted
        return None, {"beyond": 0.0, "behind": 0.0, "score": 0.0, "tried": len(tried),
                      "restricted": _fmt(windows), "restricted_dest": _fmt(windows_d),
                      "error": "the restrictions leave no permitted departure time in the day"}

    tot, b_pax, h_pax = tried[best]
    b_base, h_base = sum(b_mkt.values()) or 1.0, sum(h_mkt.values()) or 1.0
    # THE ARRIVAL THAT FEEDS THIS DEPARTURE, not a closed-loop return. It was best + 2 x block +
    # turn, which is where the aircraft would land if it shuttled. It does not: it turns here, so
    # the inbound landed one turnaround before this departure.
    ret = (best - int(turn_mins)) % 1440
    # THE WHOLE CURVE, not just its maximum. Every candidate departure is already scored and all
    # but one was thrown away. An airport asking "we would prefer a slot between 10:00 and 14:00,
    # what does that cost us" is asking to read this curve, and it costs nothing to return it.
    #
    # WHAT IT IS: connecting demand won at each departure time, each way, before capture scaling
    # and before the capacity cap. LOCAL DEMAND DOES NOT VARY WITH DEPARTURE TIME anywhere in the
    # engine, which WEIGHT-IS-A-NULL-TEST established on 14 August, so the total moves one for one
    # with this curve until the aircraft fills. That is what makes it readable as a total.
    curve = [{"dep": d, "hhmm": f"{d // 60:02d}:{d % 60:02d}",
              "total": round(tried[d][0]), "beyond": round(tried[d][1]),
              "behind": round(tried[d][2]), "permitted": bool(permitted(d))}
             for d in sorted(tried)]
    info = {"beyond": b_pax / b_base, "behind": h_pax / h_base, "score": tot, "tried": len(tried),
            "restricted": _fmt(windows), "restricted_dest": _fmt(windows_d),
            "turnaround_mins": int(turn_mins), "curve": curve,
            "return_arrival": f"{ret // 60:02d}:{ret % 60:02d}"}
    if (windows or windows_d) and free_best is not None:
        info["unrestricted_dep"] = f"{free_best // 60:02d}:{free_best % 60:02d}"
        info["unrestricted_score"] = tried[free_best][0]
        info["cost_pax"] = tried[free_best][0] - tot        # each way, what the restriction costs
    return best, info


def route_feed(sabre_db, oag_db, week, origin_airports, hub, year, capture=DEFAULT_CONN_CAPTURE,
               factor_indirect=1.044, airline=None):
    """Both feed sides for a route from the origin catchment over hub H, for a NAMED airline."""
    b_tot, b_pdew = feed_side(sabre_db, oag_db, week, origin_airports, hub, year, capture,
                              factor_indirect, beyond=True, airline=airline)
    be_tot, be_pdew = behind_feed(sabre_db, oag_db, week, origin_airports, [hub], year, capture,
                                  factor_indirect, airline=airline)
    return {"beyond_total": round(b_tot), "beyond_pdew_top": dict(list(b_pdew.items())[:15]),
            "behind_total": round(be_tot), "behind_pdew_top": dict(list(be_pdew.items())[:10]),
            "capture": capture, "airline": airline}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--origin", default="SFO,LAX,SAN", help="origin catchment airports")
    ap.add_argument("--hub", default="LHR")
    ap.add_argument("--year", type=int, default=2013)
    ap.add_argument("--week", default=None)
    ap.add_argument("--airline", default=None, help="operating carrier (e.g. BA) - alliance-weights the feed")
    ap.add_argument("--capture", type=float, default=DEFAULT_CONN_CAPTURE)
    a = ap.parse_args()
    if not (os.path.exists(a.oag) and os.path.exists(a.sabre)):
        print("need both stores"); return
    import oag_served as OAS
    weeks = OAS.list_weeks(a.oag)
    week = a.week or ([w for w in sorted(weeks) if w[5:7] == "05"] or sorted(weeks))[-1]
    origin = [x.strip() for x in a.origin.split(",")]
    # alliance-weighted base (market x connection coefficient) - the denominator the capture calibrates on
    scope = [x for x in hub_served(a.oag, week, a.hub) if x not in origin]
    scope = on_the_way(origin, a.hub, scope)
    market = connecting_market(a.sabre, origin, scope, a.year)
    onward = hub_onward_carriers(a.oag, week, a.hub) if a.airline else {}
    weighted = sum(pax * conn_coeff(a.airline, onward.get(c, set())) for c, pax in market.items())
    r = route_feed(a.sabre, a.oag, week, origin, a.hub, a.year, a.capture, airline=a.airline)
    print(f"OAG week {week}; catchment {origin} -> beyond {a.hub}; year {a.year}; airline {a.airline or 'ANY'}")
    print(f"  beyond scope: {len(scope)} destinations; raw connecting market {sum(market.values()):,.0f}; "
          f"alliance-weighted base {weighted:,.0f}")
    print(f"  BEYOND-{a.hub} FEED (capture {a.capture}): {r['beyond_total']:,}  [analyst reference = 48,115]")
    print(f"  implied capture to hit 48,115: {48115/weighted:.3f}" if weighted else "")
    print("  top beyond cities (PDEW):")
    for c, p in r["beyond_pdew_top"].items():
        print(f"    {c:6} {p}")
    print(f"  BEHIND feed (points feeding into {origin} onto the flight): {r['behind_total']:,}")
    for c, p in list(r["behind_pdew_top"].items())[:8]:
        print(f"    <-{c:6} {p}")


if __name__ == "__main__":
    main()
