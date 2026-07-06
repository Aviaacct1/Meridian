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
    import duckdb
    return duckdb.connect(db, read_only=True)


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


def conn_coeff(airline, onward_carriers):
    """How well the operating airline connects onto the onward leg: it flies it itself (online), a
    same-alliance partner flies it, or only unrelated carriers do (interline). 1.0 if no airline given."""
    if not airline:
        return 1.0
    a = airline.upper(); al = ALLIANCE.get(a)
    cs = {c for c in onward_carriers if c}
    if a in cs:
        return CNX_ONLINE
    if al and any(ALLIANCE.get(c) == al for c in cs):
        return CNX_ALLIANCE
    return CNX_INTERLINE


# Point-to-point carriers that do not interline - a route they fly carries no connecting feed. Applied
# only under feed_cfg (the fix), so default behaviour is unchanged. Extend as the carrier set grows.
P2P_CARRIERS = {"FR", "W6", "U2", "G4", "NK", "F9", "VY", "EW", "W9", "DY", "PC", "VF", "HV", "TO",
                "0B", "6E", "QZ", "AK", "JQ", "TR", "5J", "SY", "XY", "LS", "BY", "OR", "XQ", "DP"}


def hub_dominance(oag_db, week, airport, airline):
    """Operating airline's share of departures at 'airport' that week - the proxy for how much of the
    connecting bank it scoops at its own fortress (Lufthansa at Frankfurt scoops; a spoke carr