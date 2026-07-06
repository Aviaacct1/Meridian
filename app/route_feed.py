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
        rows = con.execute("SELECT carrier, COUNT(*) FROM oag WHERE week=? AND dep_airport=? "
                           "GROUP BY carrier", [week, airport]).fetchall()
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
    if _pa:
        import preagg
        market = preagg.connecting_market(_pa, origin_airports, scope, year, _fac)
    else:
        market = connecting_market(sabre_db, origin_airports, scope, year, _fac)
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
    if _pa:
        import preagg
        market = preagg.behind_market(_pa, feeders, dest_airports, year, _fac)
    else:
        market = behind_market(sabre_db, feeders, dest_airports, year, _fac)
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
