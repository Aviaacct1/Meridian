#!/usr/bin/env python3
"""
Avia Solutions - QSI catchment master build for the Global Forecast (GAF).
===========================================================================
Produces `catchments_qsi.json`: per airport, the receivers that could absorb demand the airport
cannot serve, in TWO layers, because spill does not travel by one mechanism.

  SURFACE substitution  - a local origin-and-destination passenger drives somewhere else.
                          Receivers overlap this airport's drive-time catchment (LHR -> LGW, STN).
                          Built from catchment.py in gencost mode with the SIZE PULL AND SERVICE
                          TERM SWITCHED OFF (att_exponent 0, service_value 0), so the weights are
                          independent of today's schedules, which is what the GAF asked for.
                          Real road minutes from the motorised friction surface (drive_times.py),
                          water-gap rule applied (water_check.py) so islands do not pull mainlands.

  NETWORK substitution  - a passenger reroutes over a different hub (LHR -> CDG, AMS, over a
                          connection). Receivers are hubs carrying the onward service and the
                          weight IS schedule-conditioned, because for rerouting the schedule is the
                          mechanism. Built from route_qsi.airport_qsi_to_dest over the airport's
                          own destination portfolio.

`od_share` (Sabre) tells the GAF how much of the spill each layer applies to. Weights sum to 1.0
WITHIN each layer; suppression is the GAF's, applied to the penalty fields through its own demand
elasticities (agreed 7 August 2026). Capability is emitted as a SEPARATE field, never baked into
the weight, so the GAF's extract can show why a receiver was excluded.

NAMING RULE (binding, agreed with the GAF thread): this output is DRIVE-TIME ACCESS ALLOCATION.
It is never described as QSI capture shares in any extract or client-facing text: the calibrated
forecast configuration (att_exponent 0.50-0.55, service_value from the route QSI) is NOT the
configuration used here, so the QSI accuracy record does not transfer to this file.

Run (workstation, where the stores and the friction raster live):

    py -3.12 catchment_master.py --pilot                     # the 51-airport pilot
    py -3.12 catchment_master.py --all                       # the full run
    py -3.12 catchment_master.py --self-test                 # logic proof, no external data

Data comes from config.py / environment, never hardcoded here (Avia tool standard, rule 4).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# --------------------------------------------------------------------------- version and params
VERSION = "QSI-CATCH-2026.1"

# Surface layer. att_exponent 0 and service_value 0 are the whole point: no size pull, no schedule
# term, so the weight answers "if this airport cannot serve you, where else could you drive to".
SURFACE_RADIUS_KM   = 220.0    # catchment radius round the target airport (the calibrated radius)
MEMBER_MAX_KM       = 350.0    # great-circle prefilter for candidate members
MEMBER_MAX_DRIVE_MIN = 240.0   # a member beyond four hours' drive is not a surface substitute
MIN_LOCALE_POP      = 5000.0   # GeoNames cities5000
LOGIT_SCALE         = 0.008    # calibrated (genoa_catchment_params.json). NOT used here: kept as
                               # the reference value so the two are visibly different constants.

# Sharpness of the access term with the size pull OFF. The calibrated 0.008 is right in the
# FORECAST configuration, where attractiveness (airport size) does the discriminating. With
# att_exponent 0, which is what the GAF asked for, nothing else discriminates and 0.008 leaves an
# airport an hour further away taking half the traffic: the 7 August pilot gave Bristol 0.078
# against Luton 0.155 as receivers of Heathrow spill, a ratio of 0.50 for a 97-minute difference.
#
# 0.02 is derived from the house tier definitions (John, 2 July): CONTESTED means a competitor at a
# similar drive time, PRIMARY means this airport is the obvious choice within roughly 60 minutes.
# At value of time 60, a competitor 15 minutes further takes 0.63 (genuinely shared, the contested
# band) and one 60 minutes further takes 0.16 (clearly secondary). 0.03 would give 0.50 and 0.06,
# which cuts marginal receivers; 0.02 keeps them alive and flagged, consistent with the admit-and-
# flag principle both threads settled on.
#
# WORKING ASSUMPTION, not a fitted value. The proper calibration target is an observed diversion
# event (Gatwick 2018 closure, the Dublin passenger cap, the Schiphol cap). Declared as such in the
# file meta so the GAF can carry a config switch, as it does for the border flag.
SURFACE_LOGIT_SCALE = 0.02
VOT_BY_PURPOSE      = {"business": 60.0, "leisure": 20.0}
ATT_EXPONENT        = 0.0
SERVICE_VALUE       = 0.0
WATER_GAP_KM        = 20.0
MIN_MEMBER_WEIGHT   = 0.005    # drop receivers below 0.5% - noise, and they clutter the audit

# Network layer.
NET_TOP_DESTS       = 25       # the airport's destination portfolio, by seats
NET_MAX_HUB_KM      = 2500.0   # an alternative hub within this range of the airport
NET_MIN_HUB_SIZE_M  = 5.0      # size_m from the OAG served index; below this it is not a rerouting hub
NET_MIN_DEST_COVER  = 0.20     # a candidate hub must reach at least this share of the portfolio
CRUISE_KMH          = 800.0    # for the journey-detour proxy
ASSUMED_MCT_MIN     = 75.0     # connection time added to a rerouted itinerary

# Capability screen (emitted separately, applied by the GAF). GAF v1 zeroes a surface member only
# where its A320neo figure is KNOWN and below 500 km; the A321XLR and B789 figures ride along as
# extract flags until their spill is sector-typed. UNKNOWN admits, flagged. So the A320neo number
# is the one that actually drives an exclusion today: do not let it go silently missing.
CAPABILITY_TYPES    = ("A320neo", "A321XLR", "B789")
CAPABILITY_DRIVER   = "A320neo"

# Sabre year for od_share. Fixed at 2024 to match the GAF's connecting share (their
# build_connecting_sabre.py, ACI-2024 anchored), so their 10-point divergence flag fires on METHOD
# and not on vintage. Both products move year together or the check stops being a check.
SABRE_YEAR          = int(os.environ.get("AVIA_SABRE_YEAR", "2024"))

PILOT_AIRPORTS = [
    # London and the UK system
    "LHR", "LGW", "STN", "LTN", "LCY", "SEN", "BHX", "SOU", "BRS",
    # Milan and northern Italy (the Genoa anchor case)
    "MXP", "LIN", "BGY", "GOA", "TRN", "BLQ",
    # Bay Area and southern California (the domestic share calibration basket)
    "SFO", "SJC", "OAK", "SMF", "LAX", "BUR", "SNA", "ONT",
    # New York system
    "JFK", "EWR", "LGA", "HPN", "ISP",
    # bi-national cases (the border-penalty question, still open)
    "BSL", "GVA", "LUX", "MST", "LGG", "NCE",
    # single-airport controls, no realistic receiver
    "PER", "REK", "ANC", "HNL",
    # island cases, where the water rule must bite
    "STT", "STX", "SJU", "IBZ", "PMI", "MAH", "JER", "IOM",
    # the GAF's live overrun case, added at their request 7 August 2026
    "NTE", "RNS", "ANG",
]


# --------------------------------------------------------------------------- small helpers
def gc_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------- the airport universe
def load_screen_list(path):
    """The GAF's 3,303-airport screen list. Fails loudly if absent: we reconcile against THEIR
    list, never against our reading of it."""
    import csv
    if not path or not os.path.exists(path):
        raise FileNotFoundError(
            f"GAF screen list not found: {path!r}. It was expected in the project folder as "
            f"'GAF Screen List for QSI Reconciliation - 7 August 2026.csv'. Ask for it rather "
            f"than substituting our own airport set: the reconciliation is the deliverable.")
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("iata") or row.get("airport") or row.get("code") or "").strip().upper()
            if code:
                out[code] = row
    return out


def build_universe(screen, served_index, coords):
    """Reconcile both ways, as agreed. Returns (run_set, reconciliation)."""
    served = set(served_index.get("airports", {}))
    screened = set(screen or ())
    have_coords = {c for c in served if c in coords and coords[c].get("lat") is not None}
    run_set = sorted((screened & have_coords) if screened else have_coords)
    rec = {
        "screened_by_gaf": len(screened),
        "in_our_served_index": len(served),
        "covered_both": len(run_set),
        "screened_not_served_by_us": sorted(screened - served)[:500],
        "served_by_us_not_screened": sorted(served - screened)[:500],
        "served_without_coordinates": sorted(served - have_coords)[:500],
    }
    return run_set, rec


# --------------------------------------------------------------------------- drive-time sourcing
class DriveSource:
    """One least-cost accumulation per SOURCE airport, reused across every catchment that airport
    appears in. This is what makes the full run linear in airports rather than in airport-by-member
    pairs: the accumulation from LGW serves LGW's own catchment and its membership of LHR's, STN's
    and LTN's. Results cache to disk so a long run resumes."""

    def __init__(self, friction_path, cache_dir=None):
        from drive_times import DriveTimes
        self.dt = DriveTimes(friction_path) if friction_path else None
        self.cache_dir = cache_dir
        self.mem = {}
        self.proxy_used = set()
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def available(self):
        return bool(self.dt and self.dt.available())

    def _cache_path(self, code):
        return os.path.join(self.cache_dir, f"dt_{code}.json") if self.cache_dir else None

    def times(self, code, lat, lon, points):
        """{point_key: minutes} from `code` to each (lat, lon). point_key is rounded coordinates,
        so a later catchment asking for the same place hits the cache."""
        keys = [self._key(la, lo) for la, lo in points]
        have = self.mem.get(code)
        if have is None:
            have = {}
            p = self._cache_path(code)
            if p and os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as fh:
                        have = json.load(fh)
                except Exception:
                    have = {}
            self.mem[code] = have
        missing = [(k, pt) for k, pt in zip(keys, points) if k not in have]
        if missing:
            mins = None
            if self.available():
                mins = self.dt.times_from(code, lat, lon, [pt for _, pt in missing])
            if mins is None:
                # No raster (or outside its 85N-60S coverage): great-circle proxy, and SAY SO.
                self.proxy_used.add(code)
                mins = [gc_km(lat, lon, la, lo) / 70.0 * 60.0 for _, (la, lo) in missing]
            for (k, _), m in zip(missing, mins):
                have[k] = float(m)
            p = self._cache_path(code)
            if p:
                tmp = p + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(have, fh)
                os.replace(tmp, p)
        return {k: have[k] for k in keys}

    @staticmethod
    def _key(lat, lon):
        return f"{round(float(lat), 4)},{round(float(lon), 4)}"


# --------------------------------------------------------------------------- the surface layer
def blend_purposes(biz, lei, business_share):
    """Combine the business and leisure runs into the headline layer.

    The combined weights must NOT be a third run at some generic value of time. catchment.py's
    default is £30, which is nobody's calibrated figure; the purpose runs use the Avia values of
    60 and 20. Blending the two runs by demand removes the arbitrary parameter rather than adding
    one, and keeps the headline consistent with the segmented values the GAF also consumes.
    """
    if not biz and not lei:
        return None
    if not biz:
        return dict(lei)
    if not lei:
        return dict(biz)
    b = float(business_share)
    codes = set(biz["weights"]) | set(lei["weights"])
    w = {c: b * biz["weights"].get(c, 0.0) + (1 - b) * lei["weights"].get(c, 0.0) for c in codes}
    tot = sum(w.values())
    if tot <= 0:
        return None
    w = {c: round(v / tot, 4) for c, v in w.items() if v / tot >= MIN_MEMBER_WEIGHT}
    tot = sum(w.values())
    w = {c: round(v / tot, 4) for c, v in w.items()}
    pen = {}
    for c in w:
        pb, pl = biz["access_penalty_min"].get(c), lei["access_penalty_min"].get(c)
        vals = [(b, pb), (1 - b, pl)]
        num = sum(s * p for s, p in vals if p is not None)
        den = sum(s for s, p in vals if p is not None)
        pen[c] = round(num / den, 1) if den else None
    out = dict(biz)
    out.update(
        weights=w,
        access_penalty_min=pen,
        access_penalty_mean_min=round(sum(w[c] * (pen.get(c) or 0.0) for c in w), 1),
        members=[target_of(biz)] + sorted(w, key=lambda c: -w[c]) if target_of(biz) else sorted(
            w, key=lambda c: -w[c]),
        basis=f"demand-weighted blend of the purpose runs at business share {b:.2f}",
    )
    return out


def target_of(res):
    """The target code, which surface_layer puts first in members."""
    m = (res or {}).get("members") or []
    return m[0] if m else None


def surface_layer(target, coords, locales, members, drive, purpose=None):
    """Weights for demand that CANNOT be served at `target`.

    Method, in three steps, so it can be argued line by line:
      1. Allocate the target's locales across the target AND its members, on real drive time with
         the size pull and the service term off. Locales whose NEAREST airport is the target are
         the target's natural catchment: that is the demand at risk when the target is full.
      2. Re-allocate ONLY that natural demand with the target REMOVED from the choice set. The
         resulting shares are the weights, and they sum to 1.0 within the layer by construction.
      3. The access penalty is the demand-weighted extra drive time the reallocated passenger
         faces against the drive they would have made to the target.

    Returns None when the target has no reachable member (a true island, or a solo airport).
    """
    import catchment as C

    if not locales or not members:
        return None

    p = C.CatchmentParams(method="gencost", logit_scale=SURFACE_LOGIT_SCALE,
                          value_of_time_per_hr=(VOT_BY_PURPOSE[purpose] if purpose else 30.0),
                          att_exponent=ATT_EXPONENT, max_water_gap_km=WATER_GAP_KM)

    def mk(code):
        return C.Airport(code, lat=coords[code]["lat"], lon=coords[code]["lon"],
                         attractiveness=1.0, service_value=SERVICE_VALUE)

    all_aps = [mk(target)] + [mk(m) for m in members]
    only_members = [mk(m) for m in members]

    # step 1: which locales are the target's own
    natural, t_time = [], {}
    for loc in locales:
        times = {a.code: C._drive_min(loc, a, p) for a in all_aps}
        times = {k: v for k, v in times.items() if v is not None}
        if not times:
            continue
        if min(times, key=times.get) == target:
            natural.append(loc)
            t_time[loc.name] = times[target]
    if not natural:
        return None

    # step 2: reallocate that demand with the target gone
    weights, pen_num, wsum = {}, {}, 0.0
    for loc in natural:
        shares = C.allocate_locale(loc, only_members, p)
        if not shares:
            continue                      # unreachable by road once the target is removed
        d = loc.demand
        for code, sh in shares.items():
            dm = C._drive_min(loc, next(a for a in only_members if a.code == code), p)
            if dm is None or dm > MEMBER_MAX_DRIVE_MIN:
                continue
            weights[code] = weights.get(code, 0.0) + d * sh
            pen_num[code] = pen_num.get(code, 0.0) + d * sh * max(dm - t_time[loc.name], 0.0)
            wsum += d * sh
    if not weights or wsum <= 0:
        return None

    penalty = {c: round(pen_num[c] / weights[c], 1) for c in weights if weights[c] > 0}
    weights = {c: weights[c] / wsum for c in weights}
    weights = {c: w for c, w in weights.items() if w >= MIN_MEMBER_WEIGHT}
    if not weights:
        return None
    tot = sum(weights.values())
    weights = {c: round(w / tot, 4) for c, w in weights.items()}

    tlat, tlon = coords[target]["lat"], coords[target]["lon"]
    drive_min = {}
    for c in weights:
        # No water test on the airport-to-airport figure. The water rule belongs at LOCALE level,
        # where it decides whether demand can reach a receiver at all; by the time a member carries
        # weight, real populated places have already reached it by road, so connectivity is proven.
        # Re-testing the airport pair on a straight line gets coastal geography wrong: Genoa to
        # Nice cuts across the Gulf of Genoa while the road follows the coast, and the first
        # version of this reported null for a receiver that legitimately holds 3% of the spill.
        got = drive.times(c, coords[c]["lat"], coords[c]["lon"], [(tlat, tlon)])
        drive_min[c] = round(list(got.values())[0], 0)

    return {
        "members": [target] + sorted(weights, key=lambda c: -weights[c]),
        "weights": weights,
        "drive_min": drive_min,
        "access_penalty_min": {c: penalty.get(c, 0.0) for c in weights},
        "access_penalty_mean_min": round(
            sum(weights[c] * penalty.get(c, 0.0) for c in weights), 1),
        "natural_demand": round(sum(l.demand for l in natural)),
        "n_locales": len(natural),
    }


# --------------------------------------------------------------------------- the network layer
def network_layer(target, coords, oag_db, week, served_index, top_dests=None):
    """Hubs a passenger could reroute over when the target cannot serve them.

    Weight = the candidate hub's QSI to the target's own destination portfolio (route_qsi, which
    scores nonstops and realistic one-stops with the alliance and connection coefficients). This
    layer IS schedule-conditioned, deliberately: for rerouting, the schedule is the mechanism.

    journey_penalty_min is a PROXY in v1 and is labelled as such in the file: the great-circle
    detour of routing target -> hub -> destination against target -> destination, at cruise speed,
    plus an assumed connection. It is the cost of backhauling through an alternative hub, measured
    from the target. v2 should measure it from the behind-market geography, which is where the
    transfer passenger actually starts.
    """
    import route_qsi as RQ

    aps = served_index.get("airports", {})
    if target not in aps:
        return None
    if not top_dests:
        top_dests = _portfolio(oag_db, week, target, NET_TOP_DESTS)
    if not top_dests:
        return None

    tlat, tlon = coords[target]["lat"], coords[target]["lon"]
    cands = []
    for code, rec in aps.items():
        if code == target or code not in coords or coords[code].get("lat") is None:
            continue
        if float(rec.get("size_m") or 0) < NET_MIN_HUB_SIZE_M:
            continue
        if gc_km(tlat, tlon, coords[code]["lat"], coords[code]["lon"]) > NET_MAX_HUB_KM:
            continue
        cands.append(code)
    if not cands:
        return None
    cands = sorted(cands, key=lambda c: -float(aps[c].get("size_m") or 0))[:40]

    qsi = RQ.airport_qsi_to_dest(oag_db, week, top_dests, cands)
    qsi = {c: v for c, v in qsi.items() if v and v > 0 and c != target}
    if not qsi:
        return None
    tot = sum(qsi.values())
    weights = {c: v / tot for c, v in qsi.items()}
    weights = {c: w for c, w in weights.items() if w >= MIN_MEMBER_WEIGHT}
    if not weights:
        return None
    tot = sum(weights.values())
    weights = {c: round(w / tot, 4) for c, w in weights.items()}

    pen = {}
    for c in weights:
        hl, ho = coords[c]["lat"], coords[c]["lon"]
        extra = []
        for d in top_dests:
            if d not in coords or coords[d].get("lat") is None:
                continue
            dl, do = coords[d]["lat"], coords[d]["lon"]
            direct = gc_km(tlat, tlon, dl, do)
            via = gc_km(tlat, tlon, hl, ho) + gc_km(hl, ho, dl, do)
            extra.append(max(via - direct, 0.0) / CRUISE_KMH * 60.0 + ASSUMED_MCT_MIN)
        pen[c] = round(sum(extra) / len(extra), 1) if extra else None

    return {
        "members": sorted(weights, key=lambda c: -weights[c]),
        "weights": weights,
        "journey_penalty_min": pen,
        "journey_penalty_mean_min": round(
            sum(weights[c] * (pen.get(c) or 0.0) for c in weights), 1),
        "basis": f"QSI of connecting alternatives, alliance-weighted, OAG week {week}",
        "penalty_basis": "PROXY v1: great-circle detour from the target plus assumed connection; "
                         "not measured from the behind-market geography",
        "portfolio_dests": top_dests,
    }


def pick_schedule_label(oag_db):
    """A label the QSI layer can actually read schedules from.

    The served index can be a full-year monthly sum, but route_qsi needs departure times and
    connections, which means flight-level rows under one label. Weekly labels are preferred: the
    QSI scorer caps connecting frequency on a WEEKLY basis (route_qsi.CONN_FREQ_CAP), so feeding
    it a monthly label would compare a month of departures against a weekly cap and distort every
    connecting score. Returns (label, kind) or (None, reason).
    """
    import oag_served as OAS
    try:
        labels = [str(w) for w in OAS.list_weeks(oag_db)]
    except Exception as e:
        return None, f"could not list labels: {type(e).__name__}"
    weekly = sorted(w for w in labels if len(w) == 10 and w[4] == "-" and w[7] == "-")
    if weekly:
        return weekly[-1], "weekly"
    monthly = sorted(w for w in labels if len(w) == 7 and w[4] == "-")
    if monthly:
        return monthly[-1], "monthly"
    return None, f"no weekly or monthly labels found among {len(labels)} labels"


def _portfolio(oag_db, week, code, top):
    """The airport's destination portfolio by weekly seats, from OAG."""
    import duckdb
    con = duckdb.connect(str(oag_db), read_only=True)
    try:
        rows = con.execute("""
            SELECT arr_airport,
                   SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE), TRY_CAST(seats AS DOUBLE), 0.0)
                       * COALESCE(TRY_CAST(frequency AS DOUBLE), 1.0)) AS s
            FROM oag WHERE week = ? AND dep_airport = ?
              AND arr_airport IS NOT NULL AND TRIM(arr_airport) <> ''
            GROUP BY arr_airport ORDER BY s DESC LIMIT ?
        """, [week, code, int(top)]).fetchall()
    finally:
        con.close()
    return [r[0].strip().upper() for r in rows if r[0]]


# --------------------------------------------------------------------------- od_share and capability
def od_share(sabre_db, code, year=None):
    """The airport's local origin-and-destination demand as a share of everything touching it.

    O&D pax  = records where the airport is the origin or the destination endpoint.
    Transfer = records where it appears as a connecting point.

    The GAF cross-checks this against its own connecting share and flags divergences beyond 10
    points. We do NOT calibrate ours to match theirs (their instruction, and the right call: two
    independent reads of the same store is a check, one calibrated to the other is not).
    """
    import duckdb
    con = duckdb.connect(str(sabre_db), read_only=True)
    try:
        try:
            from db_registry import apply_limits
            apply_limits(con)
        except Exception:
            pass
        cols = {r[1].lower() for r in con.execute("PRAGMA table_info('sabre')").fetchall()}
        conn_cols = [c for c in ("connecting_airport1", "connecting_airport2",
                                 "connecting_airport3") if c in cols]
        if not conn_cols:
            # Do not silently return a neutral 1.0: that is the failure shape we keep hitting.
            return None, {"error": "no connecting_airport columns in the sabre table"}
        where, params = "", []
        if year is not None:
            if "source_year" not in cols:
                # Never quietly widen the period: the GAF's divergence flag is calibrated to a
                # like-for-like year and would fire on vintage instead of method.
                return None, {"error": "no source_year column, cannot pin the Sabre year "
                                       f"to {year}; od_share withheld rather than computed "
                                       "over an unknown period"}
            where, params = " AND source_year = ?", [year]
        od = con.execute(
            f"SELECT COALESCE(SUM(passengers),0) FROM sabre "
            f"WHERE (origin_airport = ? OR destination_airport = ?){where}",
            [code, code] + params).fetchone()[0]
        cond = " OR ".join(f"{c} = ?" for c in conn_cols)
        tr = con.execute(
            f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE ({cond}){where}",
            [code] * len(conn_cols) + params).fetchone()[0]
    finally:
        con.close()
    od, tr = float(od or 0), float(tr or 0)
    if od + tr <= 0:
        return None, {"error": "no Sabre records for this airport"}
    return round(od / (od + tr), 4), {"od_pax": round(od), "transfer_pax": round(tr),
                                      "connecting_cols": conn_cols, "sabre_year": year}


def _road_reachable(lat1, lon1, lat2, lon2):
    """Is this pair connected by road, per the land mask and the water-gap threshold. Fails CLOSED
    here (treats an unavailable mask as unreachable would be wrong, so we raise instead): the build
    already refuses to start without the mask, so reaching this with no mask is a logic error."""
    from water_check import road_reachable
    return road_reachable(lat1, lon1, lat2, lon2, WATER_GAP_KM)


def cross_border_members(target, members, coords):
    """Members in a different country from the target. Admitted and flagged, never zeroed here."""
    home = (coords.get(target, {}).get("country") or "").upper()
    return sorted(m for m in members
                  if (coords.get(m, {}).get("country") or "").upper() != home)


def od_share_bulk(sabre_db, year=None, codes=None):
    """{code: (share, meta)} for EVERY airport, in one grouped pass per column.

    The per-airport version scans the store once per airport. At 3,158 airports against a 16 GB
    Sabre store that is 3,158 scans for a quantity that is two GROUP BY queries. Same definition
    as od_share, same year pinning, same refusal to widen the period.
    """
    import duckdb
    con = duckdb.connect(str(sabre_db), read_only=True)
    try:
        try:
            from db_registry import apply_limits
            apply_limits(con)
        except Exception:
            pass
        cols = {r[1].lower() for r in con.execute("PRAGMA table_info('sabre')").fetchall()}
        conn_cols = [c for c in ("connecting_airport1", "connecting_airport2",
                                 "connecting_airport3") if c in cols]
        if not conn_cols:
            return {}, {"error": "no connecting_airport columns in the sabre table"}
        if year is not None and "source_year" not in cols:
            return {}, {"error": f"no source_year column, cannot pin the Sabre year to {year}"}
        where, params = "", []
        if year is not None:
            where, params = "WHERE source_year = ?", [year]

        od, tr = {}, {}
        for col, sink in (("origin_airport", od), ("destination_airport", od),
                          *[(c, tr) for c in conn_cols]):
            rows = con.execute(
                f"SELECT {col} AS a, SUM(passengers) AS p FROM sabre {where} "
                f"WHERE_PLACEHOLDER GROUP BY 1".replace(
                    "WHERE_PLACEHOLDER",
                    ("AND" if where else "WHERE") + f" {col} IS NOT NULL AND TRIM({col}) <> ''"),
                params).fetchall()
            for a, p in rows:
                k = (a or "").strip().upper()
                if k:
                    sink[k] = sink.get(k, 0.0) + float(p or 0.0)
    finally:
        con.close()

    out = {}
    for code in (codes or (set(od) | set(tr))):
        o, t = od.get(code, 0.0), tr.get(code, 0.0)
        if o + t <= 0:
            out[code] = (None, {"error": "no Sabre records for this airport"})
        else:
            out[code] = (round(o / (o + t), 4),
                         {"od_pax": round(o), "transfer_pax": round(t),
                          "connecting_cols": conn_cols, "sabre_year": year, "basis": "bulk"})
    return out, {"airports": len(out), "connecting_cols": conn_cols, "sabre_year": year}


def capability_field(members):
    """Per member, the longest sector it can physically fly for each reference type. The GAF applies
    the zeroing; we never bake it into the weight, so its extract can show WHY a receiver was
    excluded. UNKNOWN never filters (airfield_check fails open on missing runway data)."""
    try:
        import airfield_check as AF
    except Exception:
        return None
    out = {}
    for m in members:
        rec = {}
        for t in CAPABILITY_TYPES:
            try:
                rec[t] = AF.max_sector_km(t, m)
            except Exception:
                rec[t] = None
        out[m] = rec
    return out


# --------------------------------------------------------------------------- the build
def build(run_set, coords, geonames_path, friction_path, oag_db, sabre_db, week,
          served_index, cache_dir=None, do_network=True, do_sabre=True, segment=True,
          member_pool=None):
    """member_pool is the universe candidate RECEIVERS are drawn from, and it must not be the run
    set. A pilot builds 51 airports but Heathrow's receivers include Manchester, East Midlands,
    Cardiff and Exeter, none of them in the pilot; drawing members from the run set would hand the
    GAF weights that renormalise over an arbitrary subset and look complete. Default to the run set
    only when nothing wider is available, and record which was used."""
    import geonames as G
    member_pool = sorted(set(member_pool or run_set))

    drive = DriveSource(friction_path, cache_dir)
    if not drive.available():
        _log("WARNING: friction raster not available. Every drive time is a great-circle proxy "
             "and the pilot cannot be used to judge the weights. Fix the raster path first.")

    # The water rule fails OPEN by design, which is right for the forecast tool and wrong here:
    # a silent fail-open would hand the GAF island catchments that pull mainlands, and nothing in
    # the output would say so. Check once, loudly, before spending the run.
    try:
        from water_check import road_reachable
        mask_live = not road_reachable(51.4, -0.4, 50.60, -0.40, WATER_GAP_KM)
    except Exception:
        mask_live = False
    if not mask_live:
        if os.environ.get("AVIA_ALLOW_NO_WATER_CHECK", "0") == "1":
            _log("WATER RULE OFF and overridden by AVIA_ALLOW_NO_WATER_CHECK. Every island record "
                 "in this file is suspect and must be flagged by hand before it goes to the GAF.")
            stats_water = "off_overridden"
        else:
            raise SystemExit(
                "global-land-mask is not installed, so the water-boundary rule is OFF. Island "
                "airports would pull mainland catchments and nothing in the file would say so. "
                "Run `pip install global-land-mask` and rebuild. Override with "
                "AVIA_ALLOW_NO_WATER_CHECK=1 only if you intend to flag every island by hand.")
    else:
        stats_water = "on"

    out, stats = {}, {"proxy_drive_time": 0, "no_receiver": 0, "surface_only": 0,
                      "water_rule": stats_water, "errors": {}}

    # One grouped pass for od_share rather than a scan per airport.
    _od_bulk = None
    if do_sabre and sabre_db and len(run_set) > 25:
        _log(f"od_share: one grouped pass over Sabre {SABRE_YEAR} for {len(run_set)} airports")
        _od_bulk, bulk_meta = od_share_bulk(sabre_db, year=SABRE_YEAR, codes=set(run_set))
        stats["od_share_bulk"] = bulk_meta
        if bulk_meta.get("error"):
            _log(f"od_share bulk pass failed: {bulk_meta['error']}")
            _od_bulk = None
    t0 = time.time()
    for i, code in enumerate(run_set, 1):
        t_start = time.time()
        rec = {"flags": []}
        try:
            lat, lon = coords[code]["lat"], coords[code]["lon"]
            locales = G.near_point(geonames_path, lat, lon, SURFACE_RADIUS_KM,
                                   min_pop=MIN_LOCALE_POP, propensity=1.0)
            members = [c for c in member_pool
                       if c != code and c in coords and coords[c].get("lat") is not None
                       and gc_km(lat, lon, coords[c]["lat"], coords[c]["lon"]) <= MEMBER_MAX_KM]

            # one accumulation per source airport, over the union of points it will ever need
            pts = [(l.lat, l.lon) for l in locales]
            for m in [code] + members:
                got = drive.times(m, coords[m]["lat"], coords[m]["lon"], pts)
                keyed = dict(zip([DriveSource._key(la, lo) for la, lo in pts], got.values()))
                for l in locales:
                    v = keyed.get(DriveSource._key(l.lat, l.lon))
                    if v is None:
                        continue
                    # THE WATER RULE MUST APPLY TO RASTER TIMES TOO. catchment._drive_min only
                    # water-checks an ESTIMATED time, on the reasonable principle that an uploaded
                    # matrix knows about bridges and ferries. The friction surface does NOT: it
                    # gives sea a slow-but-finite cost (NODATA_MIN_PER_M) to keep the least-cost
                    # accumulation finite, so the path simply swims. Unchecked, that gave the Isle
                    # of Man a 436-minute "drive" to Birmingham and Menorca a 273-minute one to
                    # Mallorca in the 7 August pilot. Leaving drive_min unset lets catchment fall
                    # back to its estimate path, where the water rule does run and returns None.
                    if not _road_reachable(l.lat, l.lon, coords[m]["lat"], coords[m]["lon"]):
                        continue
                    l.drive_min[m] = v

            # Weights AND penalties by purpose (GAF, 7 Aug): the suppression step wants them apart
            # because business values access time three times leisure, so a spill population
            # skewed to business suppresses differently from one that drives. The COMBINED layer
            # is the demand-weighted blend of these two, never a third run at a generic value of
            # time: catchment.py's £30 default is not an Avia figure and it was silently setting
            # the headline weights the GAF would consume.
            runs = {pp: surface_layer(code, coords, locales, members, drive, purpose=pp)
                    for pp in ("business", "leisure")}
            bshare = (sum(l.demand * l.business_share for l in locales) /
                      sum(l.demand for l in locales)) if locales else 0.30
            surf = blend_purposes(runs["business"], runs["leisure"], bshare)
            if segment and surf:
                surf["by_purpose"] = {
                    pp: None if not r else {
                        "weights": r["weights"],
                        "access_penalty_min": r["access_penalty_min"],
                        "access_penalty_mean_min": r["access_penalty_mean_min"],
                    } for pp, r in runs.items()}
                surf["business_share"] = round(bshare, 4)
            if surf:
                # Cross-border receivers are admitted and flagged, not zeroed: a visible
                # over-credit beats an invisible missing receiver. Our border penalty is still
                # uncalibrated, so raw drive time over-credits a foreign airport. The GAF's
                # allocator can zero flagged members from config; when the penalty calibrates the
                # flag comes off and nothing else changes.
                cross = cross_border_members(code, list(surf["weights"]), coords)
                if cross:
                    surf["cross_border_members"] = cross
                    surf["cross_border_flag"] = "border_uncalibrated"
                    rec["flags"].append("border_uncalibrated")
                rec["surface"] = surf
                cap = capability_field([m for m in surf["weights"]])
                if cap:
                    rec["capability"] = cap
                    missing = [m for m in cap if cap[m].get(CAPABILITY_DRIVER) is None]
                    if missing:
                        # The A320neo figure is the one the GAF actually zeroes on. Say when it
                        # is absent rather than letting an UNKNOWN pass as a quiet admit.
                        rec["flags"].append("capability_driver_unknown")
                        surf["capability_driver_unknown"] = missing
            else:
                rec["flags"].append("no_road_receiver")
                rec["surface"] = {"members": [code], "weights": {}, "drive_min": {},
                                  "access_penalty_min": {}}
                stats["no_receiver"] += 1

            if do_network and oag_db:
                net = network_layer(code, coords, oag_db, week, served_index)
                if net:
                    rec["network"] = net
                else:
                    rec["flags"].append("no_network_receiver")
                    stats["surface_only"] += 1

            if do_sabre and sabre_db:
                if _od_bulk is not None:
                    sh, meta = _od_bulk.get(code, (None, {"error": "not in the bulk pass"}))
                else:
                    sh, meta = od_share(sabre_db, code, year=SABRE_YEAR)
                rec["od_share"] = sh
                rec["od_share_meta"] = meta
                if sh is None:
                    rec["flags"].append("od_share_unavailable")

            if code in drive.proxy_used:
                rec["flags"].append("proxy_drive_time")
                stats["proxy_drive_time"] += 1
            else:
                rec["flags"].append("road_network_ok")
        except Exception as e:
            rec["flags"].append("build_error")
            rec["error"] = f"{type(e).__name__}: {e}"
            stats["errors"][code] = rec["error"]
        out[code] = rec
        _log(f"{i}/{len(run_set)} {code}  {time.time() - t_start:5.1f}s  "
             f"surface={len(out[code].get('surface', {}).get('weights', {}))} "
             f"network={len(out[code].get('network', {}).get('weights', {}))}")

    elapsed = time.time() - t0
    stats["elapsed_sec"] = round(elapsed, 1)
    stats["sec_per_airport"] = round(elapsed / max(len(run_set), 1), 2)

    # A layer that was asked for and produced nothing ANYWHERE is a fault, not a finding. The
    # 15:10 run on 7 August wrote 48 airports with network=0 and said nothing, because the file
    # looks complete either way. Say it loudly and record it in the file.
    n_net = sum(1 for r in out.values() if r.get("network", {}).get("weights"))
    n_surf = sum(1 for r in out.values() if r.get("surface", {}).get("weights"))
    stats["airports_with_network"] = n_net
    stats["airports_with_surface"] = n_surf
    if do_network and n_net == 0 and run_set:
        stats["network_layer"] = "REQUESTED BUT EMPTY on every airport - do not ship this file"
        _log("=" * 78)
        _log("FAULT: the network layer was requested and produced nothing on ALL "
             f"{len(run_set)} airports. That is a build fault, not a result. Check the schedule "
             "label and the served index before this file goes anywhere.")
        _log("=" * 78)
    elif do_network and n_net < len(run_set) * 0.25 and run_set:
        _log(f"NOTE: only {n_net} of {len(run_set)} airports got network receivers. Expected for "
             f"small and island fields, suspicious if the large hubs are among the empties.")
    if n_surf == 0 and run_set:
        stats["surface_layer"] = "EMPTY on every airport - do not ship this file"
        _log("FAULT: the surface layer is empty on every airport. Check the friction raster, the "
             "population dump and the member radius.")
    return out, stats


def meta_block(week, geonames_path, friction_path, stats, reconciliation, run_set):
    return {
        "vintage": VERSION,
        "run_date": _now(),
        "produced_by": "Avia Solutions - QSI tool, catchment_master.py",
        "method_version": ("catchment.py gencost, att_exponent 0, service_value 0 (surface); "
                           "route_qsi alliance-weighted (network)"),
        "naming_rule": ("DRIVE-TIME ACCESS ALLOCATION. Not QSI capture shares: the calibrated "
                        "forecast configuration is not the configuration used here, so the QSI "
                        "accuracy record does not transfer to this file."),
        "population_source": os.path.basename(str(geonames_path or "")),
        "drive_time_source": os.path.basename(str(friction_path or "")) or "great-circle proxy",
        "oag_week": week,
        "served_index_basis": globals().get("_SERVED_BASIS", "none"),
        "network_qsi_basis": ("route_qsi is week-keyed and has no full-year equivalent staged: QSI "
                              "needs departure times, connections and MCT, which monthly "
                              "aggregates do not carry. The network layer is therefore a schedule "
                              "SNAPSHOT even where the served index is full-year. Resolving this "
                              "is part of the v2 network work."),
        "sabre_year": SABRE_YEAR,
        "od_share_basis": ("Sabre year {y}: O&D endpoint pax over O&D plus connecting pax. Matched "
                           "to the GAF's connecting share year so their 10-point divergence flag "
                           "tests method, not vintage. Not calibrated to theirs, by agreement."
                           ).format(y=SABRE_YEAR),
        "capability_driver": (f"{CAPABILITY_DRIVER} max sector is the field the GAF v1 zeroes on "
                              f"(known and below 500 km); other types are extract flags. UNKNOWN "
                              f"admits, and is reported per airport as capability_driver_unknown."),
        "cross_border": ("admitted and flagged as border_uncalibrated, never zeroed here; the "
                         "border penalty is not yet calibrated"),
        "water_rule_km": WATER_GAP_KM,
        "surface_logit_scale_status": (
            f"WORKING ASSUMPTION. {SURFACE_LOGIT_SCALE} is derived from Avia's Primary and "
            f"Contested catchment tier definitions, not fitted to observed diversion. With the "
            f"size pull off nothing else discriminates between receivers, so this value sets how "
            f"sharply drive time does. At value of time 60 a competitor 15 minutes further takes "
            f"0.63 and one 60 minutes further takes 0.16. Carry a config switch and sensitivity-"
            f"test it. The engine's calibrated {LOGIT_SCALE} applies to the forecast "
            f"configuration, where airport size discriminates, and does not transfer here."),
        "params": {"surface_logit_scale": SURFACE_LOGIT_SCALE,
                   "engine_logit_scale_not_used": LOGIT_SCALE,
                   "combined_layer": "demand-weighted blend of the business and leisure runs; no "
                                     "generic value of time is used",
                   "vot_business": VOT_BY_PURPOSE["business"],
                   "vot_leisure": VOT_BY_PURPOSE["leisure"], "att_exponent": ATT_EXPONENT,
                   "service_value": SERVICE_VALUE, "surface_radius_km": SURFACE_RADIUS_KM,
                   "member_max_km": MEMBER_MAX_KM, "member_max_drive_min": MEMBER_MAX_DRIVE_MIN,
                   "min_locale_pop": MIN_LOCALE_POP, "min_member_weight": MIN_MEMBER_WEIGHT,
                   "net_top_dests": NET_TOP_DESTS, "net_max_hub_km": NET_MAX_HUB_KM,
                   "net_min_hub_size_m": NET_MIN_HUB_SIZE_M},
        "commit": os.environ.get("AVIA_QSI_COMMIT") or
                  "not pinned: qsi-app not yet in its own repository (platform migration pending)",
        "weights_sum_to_one_within_layer": True,
        "suppression": "not applied here; the GAF converts the penalty fields through its own "
                       "capacity_redistribution elasticity",
        "coverage": {"airports": len(run_set), **{k: v for k, v in stats.items()
                                                  if k != "errors"}},
        "reconciliation": reconciliation,
    }


# --------------------------------------------------------------------------- self-test
def _self_test():
    """Prove the surface logic on a synthetic geography, no raster, no stores, no network.

    Layout (drive minutes set by hand, so nothing depends on external data):
        HUB     the target, central
        NEAR    30 min from the population, a plain substitute
        FAR     150 min, a weak substitute
        ISLE    reachable only over water, must never receive

    The island case is deliberately placed CLOSE (a short hop over open sea), so that if the water
    rule fails the island would be admitted on distance alone. An earlier version put it far away
    and the test passed on the drive-time cap instead, proving nothing.
    """
    import catchment as C
    ok = True

    # ISLE: mid-Channel open water, circa 90 km from the population, well inside every distance
    # and drive-time limit, so ONLY the water rule can exclude it.
    coords = {"HUB": {"lat": 51.5, "lon": -0.5}, "NEAR": {"lat": 51.2, "lon": -0.2},
              "FAR": {"lat": 52.4, "lon": -1.8}, "ISLE": {"lat": 50.60, "lon": -0.40}}

    def mk_loc(name, pop, hub, near, far):
        l = C.Locale(name, pop, propensity=1.0, lat=51.4, lon=-0.4)
        l.drive_min = {"HUB": hub, "NEAR": near, "FAR": far}   # ISLE deliberately absent
        return l

    locales = [mk_loc("townA", 500_000, 25, 40, 150),
               mk_loc("townB", 300_000, 35, 55, 140),
               mk_loc("townC", 200_000, 20, 60, 165)]

    class _D:
        proxy_used = set()
        def times(self, code, lat, lon, points):
            return {DriveSource._key(la, lo): gc_km(lat, lon, la, lo) / 70.0 * 60.0
                    for la, lo in points}

    res = surface_layer("HUB", coords, locales, ["NEAR", "FAR", "ISLE"], _D())
    print("weights:", res["weights"])
    print("access penalty (min):", res["access_penalty_min"],
          "mean", res["access_penalty_mean_min"])

    s = sum(res["weights"].values())
    print(f"1. weights sum to 1.0 within the layer: {s:.4f}",
          "PASS" if abs(s - 1.0) < 1e-6 else "FAIL")
    ok &= abs(s - 1.0) < 1e-6

    near, far = res["weights"].get("NEAR", 0), res["weights"].get("FAR", 0)
    print(f"2. the nearer substitute takes more: NEAR {near:.3f} > FAR {far:.3f}",
          "PASS" if near > far else "FAIL")
    ok &= near > far

    # Prove the water rule is the thing doing the excluding, not the distance or drive-time cap.
    try:
        from water_check import road_reachable
        mask_live = not road_reachable(51.4, -0.4, 50.60, -0.40, WATER_GAP_KM)
    except Exception:
        mask_live = False
    isle_out = "ISLE" not in res["weights"]
    if not mask_live:
        print("3. the unreachable island never receives: CANNOT TEST - global-land-mask is not "
              "installed, so the water rule is off and the island would be admitted on distance. "
              "Install it before trusting any island catchment. FAIL")
        ok = False
    else:
        d_isle = gc_km(51.4, -0.4, 50.60, -0.40)
        print(f"3. the unreachable island never receives (water rule live, island only "
              f"{d_isle:.0f} km away so distance cannot be doing the work): "
              f"ISLE {'absent' if isle_out else 'PRESENT'}", "PASS" if isle_out else "FAIL")
        ok &= isle_out

    pos = all(v >= 0 for v in res["access_penalty_min"].values())
    print(f"4. access penalty is never negative (the alternative is never nearer): ",
          "PASS" if pos else "FAIL")
    ok &= pos

    solo = surface_layer("HUB", coords, locales, [], _D())
    print(f"5. a solo airport returns no receiver rather than a fabricated one: ",
          "PASS" if solo is None else "FAIL")
    ok &= solo is None

    # the target must be excluded from its own reallocation
    print(f"6. the target does not receive its own spill: ",
          "PASS" if "HUB" not in res["weights"] else "FAIL")
    ok &= "HUB" not in res["weights"]

    # ---- the three behaviours added after the GAF's second reply (7 August)
    b = surface_layer("HUB", coords, locales, ["NEAR", "FAR", "ISLE"], _D(), purpose="business")
    l = surface_layer("HUB", coords, locales, ["NEAR", "FAR", "ISLE"], _D(), purpose="leisure")
    diff = (b["access_penalty_mean_min"] != l["access_penalty_mean_min"]
            or b["weights"] != l["weights"])
    print(f"7. business and leisure segment apart (business {b['access_penalty_mean_min']} min "
          f"vs leisure {l['access_penalty_mean_min']} min): ", "PASS" if diff else "FAIL")
    ok &= diff

    cc = {"HUB": {"country": "GB"}, "NEAR": {"country": "GB"}, "FAR": {"country": "FR"}}
    flagged = cross_border_members("HUB", ["NEAR", "FAR"], cc)
    good = flagged == ["FAR"]
    print(f"8. the foreign receiver is flagged and the domestic one is not: {flagged} ",
          "PASS" if good else "FAIL")
    ok &= good

    # od_share must WITHHOLD rather than compute over an unknown period when the year cannot be
    # pinned; a quietly widened period would make the GAF's divergence flag fire on vintage.
    try:
        import duckdb, tempfile
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "s.duckdb")
            con = duckdb.connect(p)
            con.execute("CREATE TABLE sabre (origin_airport VARCHAR, destination_airport VARCHAR, "
                        "connecting_airport1 VARCHAR, passengers DOUBLE)")
            con.execute("INSERT INTO sabre VALUES ('AAA','BBB',NULL,100), ('CCC','DDD','AAA',25)")
            con.close()
            val, meta = od_share(p, "AAA", year=SABRE_YEAR)
            withheld = val is None and "source_year" in (meta.get("error") or "")
            print(f"9. od_share withholds when the Sabre year cannot be pinned: ",
                  "PASS" if withheld else "FAIL")
            ok &= withheld

            p2 = os.path.join(td, "s2.duckdb")
            con = duckdb.connect(p2)
            con.execute("CREATE TABLE sabre (origin_airport VARCHAR, destination_airport VARCHAR, "
                        "connecting_airport1 VARCHAR, passengers DOUBLE, source_year INTEGER)")
            con.execute(f"INSERT INTO sabre VALUES ('AAA','BBB',NULL,100,{SABRE_YEAR}), "
                        f"('CCC','DDD','AAA',25,{SABRE_YEAR}), "
                        f"('AAA','EEE',NULL,999,{SABRE_YEAR - 1})")
            con.close()
            val2, meta2 = od_share(p2, "AAA", year=SABRE_YEAR)
            # 100 O&D against 25 connecting in the pinned year; the prior year must not leak in
            right = val2 == 0.8 and meta2.get("sabre_year") == SABRE_YEAR
            print(f"10. od_share pins the year and excludes the prior one: {val2} ",
                  "PASS" if right else "FAIL")
            ok &= right
    except ImportError:
        print("9-10. od_share year pinning: CANNOT TEST - duckdb not installed here. FAIL")
        ok = False

    print("\nSELF-TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


# --------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="Build catchments_qsi.json for the Global Forecast.")
    ap.add_argument("--pilot", action="store_true", help="the 51-airport pilot set")
    ap.add_argument("--all", action="store_true", help="the full screened set")
    ap.add_argument("--airports", help="comma list, overrides --pilot/--all")
    ap.add_argument("--self-test", action="store_true", help="logic proof, no external data")
    ap.add_argument("--screen-list",
                    default=os.environ.get("AVIA_GAF_SCREEN_LIST"),
                    help="the GAF's 3,303-airport CSV; defaults to AVIA_GAF_SCREEN_LIST, which "
                         "should point at the shared repo copy "
                         "(avia_forecast_build/data/gaf_screen_list_2026-08-07.csv)")
    ap.add_argument("--geonames", help="GeoNames cities5000.txt")
    ap.add_argument("--friction", help="motorised friction GeoTIFF")
    ap.add_argument("--oag", help="oag.duckdb (default from config)")
    ap.add_argument("--sabre", help="sabre.duckdb (default from config)")
    ap.add_argument("--week", help="OAG week, e.g. 2025-05-26. Single-week basis: carries the x52 "
                                   "annualisation and the seats x frequency double-count. Only "
                                   "use it knowingly; --fy-year is the default where monthly data "
                                   "exists.")
    ap.add_argument("--fy-year", type=int,
                    help="full-year monthly served index for this year (fy_capacity). Defaults to "
                         "the latest year with monthly labels in the store.")
    ap.add_argument("--cache-dir", default=os.path.join(HERE, "_dt_cache"))
    ap.add_argument("--out", default="catchments_qsi.json")
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--no-sabre", action="store_true")
    ap.add_argument("--no-segment", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return _self_test()

    try:
        import config as CFG
        oag_db = a.oag or str(CFG.OAG_DUCKDB)
        sabre_db = a.sabre or str(CFG.SABRE_DUCKDB)
    except Exception:
        oag_db, sabre_db = a.oag, a.sabre

    friction = a.friction or os.environ.get("AVIA_FRICTION_RASTER")
    geonames_path = a.geonames or os.environ.get("AVIA_GEONAMES")
    if not geonames_path:
        # The dump ships next to the code, so default to it rather than making the caller guess.
        local = os.path.join(HERE, "cities5000.txt")
        if os.path.exists(local):
            geonames_path = local
            _log(f"--geonames not given; using the local dump {local}")
        else:
            raise SystemExit("--geonames (or AVIA_GEONAMES) is required: the population layer.")

    # Pre-flight. Name every missing input at once, before opening a store or spending a raster
    # pass, so a wrong path costs a second rather than a traceback part way through a long run.
    missing = []
    if not os.path.exists(geonames_path):
        missing.append(f"  population dump   {geonames_path}\n"
                       f"      the cities5000.txt dump ships in the app folder; try "
                       f"--geonames \"{os.path.join(HERE, 'cities5000.txt')}\"")
    if friction and not os.path.exists(friction):
        missing.append(f"  friction raster   {friction}")
    if not a.no_network and oag_db and not os.path.exists(str(oag_db)):
        missing.append(f"  OAG store         {oag_db}\n"
                       f"      config points at the local cache, which is not populated on this "
                       f"machine; the back-test runs use C:\\Avia\\oag.duckdb. Pass --oag, or "
                       f"--no-network to build the surface layer only.")
    if not a.no_sabre and sabre_db and not os.path.exists(str(sabre_db)):
        missing.append(f"  Sabre store       {sabre_db}\n"
                       f"      pass --sabre, or --no-sabre to omit od_share (the GAF then has no "
                       f"split to apply, so only do that for a shape-only look).")
    if missing:
        raise SystemExit("Inputs not found:\n" + "\n".join(missing) +
                         "\n\nNothing was opened and nothing was written.")

    # Heavy imports only after the paths check out.
    import airportsdata
    import oag_served as OAS

    if not friction:
        _log("no --friction and no AVIA_FRICTION_RASTER: every drive time will be a great-circle "
             "proxy, so the weights cannot be judged. Only useful for a plumbing check.")

    # --no-network means the build never opens the OAG store, so do not touch it here either. The
    # pre-flight already skips the store check under --no-network; asking it for a week list anyway
    # is how the 15:01 run on 7 August died on a store it had been told not to need.
    week, served, basis = a.week, {"airports": {}}, "none"
    if a.no_network:
        if week:
            _log("--no-network: the OAG week is ignored, surface layer only.")
        week = None
    elif oag_db:
        # Prefer the FULL-YEAR served index. fy_capacity.build_served_index_fy is written as a
        # drop-in for oag_served.build_served_index: monthly sum rather than one week x52, and no
        # seats_total x frequency double-count. size_m from the week path is the noisy quantity the
        # 24 July before-and-after measured (median ratio 0.88, p10 0.44 to p90 1.41), and here it
        # screens which hubs qualify as rerouting receivers, so the basis matters.
        if not a.fy_year and not a.week:
            try:
                import fy_capacity as FY
                mby = FY.months_by_year(oag_db)
                if mby:
                    a.fy_year = max(mby)
                    _log(f"full-year months available for {sorted(mby)}; using {a.fy_year}")
            except Exception as e:
                _log(f"fy_capacity unavailable ({type(e).__name__}); falling back to a week.")
        if a.fy_year:
            import fy_capacity as FY
            mby = FY.months_by_year(oag_db)
            months = mby.get(int(a.fy_year))
            if not months:
                raise SystemExit(
                    f"no monthly labels for {a.fy_year} in {oag_db}. Years with monthly data: "
                    f"{sorted(mby) or 'none'}. Pick one with --fy-year, or pass --week to use the "
                    f"single-week basis knowingly.")
            served = FY.build_served_index_fy(oag_db, int(a.fy_year), months)
            basis = f"full-year monthly sum, {a.fy_year}, {len(months)} months"
            # The served index is now full-year, but the NETWORK layer still needs a schedule
            # label. Leaving week as None here is what made the 15:10 run return network=0 on all
            # 48 airports without a word: _portfolio queried week=None and found nothing.
            if not a.no_network:
                week, kind = pick_schedule_label(oag_db)
                if not week:
                    raise SystemExit(
                        f"The served index is full-year, but the network layer needs a schedule "
                        f"label and none was found ({kind}). Pass --week, or --no-network to "
                        f"build the surface layer alone.")
                _log(f"network QSI reads the {kind} label {week} (schedule snapshot); the served "
                     f"index is the {a.fy_year} full year.")
                if kind == "monthly":
                    _log("WARNING: monthly label into a weekly-capped QSI scorer. Connecting "
                         "scores will be distorted. Prefer a weekly label.")
            if len(months) < 12:
                # 2019 is Jan-Jun in this store; build_served_index_fy scales a part year to a
                # full-year equivalent, and H1 carries the spring build-up, so size_m runs high.
                # Flag it rather than papering over it.
                _log(f"WARNING: {a.fy_year} has only {len(months)} months. size_m is scaled to a "
                     f"full-year equivalent and will run high. Flagged in the file meta.")
                basis += " (PART YEAR, scaled, size_m runs high)"
        else:
            if not week:
                weeks = OAS.list_weeks(oag_db)
                week = weeks[-1] if weeks else None
                _log(f"week not given; using the latest in the store: {week}")
            if week:
                served = OAS.build_served_index(oag_db, week)
                basis = (f"single week {week} x52. Carries the seats_total x frequency "
                         f"double-count; use --fy-year where monthly data exists.")
                _log(f"WARNING: single-week served index ({week}). size_m carries the x52 "
                     f"annualisation and the frequency double-count.")
    globals()["_SERVED_BASIS"] = basis

    coords = airportsdata.load("IATA")

    screen = {}
    if a.screen_list:
        screen = load_screen_list(a.screen_list)
    elif a.all:
        raise SystemExit(
            "--all needs --screen-list: the full run reconciles against the GAF's 3,303, and we "
            "do not substitute our own set for theirs.")

    if a.airports:
        run_set = [c.strip().upper() for c in a.airports.split(",") if c.strip()]
        rec = {"note": "explicit airport list, no reconciliation"}
    elif a.pilot:
        run_set = [c for c in PILOT_AIRPORTS if c in coords]
        missing = [c for c in PILOT_AIRPORTS if c not in coords]
        rec = {"note": "pilot set", "pilot_missing_coordinates": missing}
    elif served.get("airports"):
        run_set, rec = build_universe(screen, served, coords)
    elif screen:
        # Surface-only runs never open the OAG store, so there is no served index to intersect.
        # The GAF's screen list is a complete enough universe on its own; say which was used.
        run_set = sorted(c for c in screen if c in coords and coords[c].get("lat") is not None)
        rec = {"note": "universe from the GAF screen list alone (no OAG served index in this run)",
               "screened_by_gaf": len(screen),
               "screened_without_coordinates": sorted(set(screen) - set(run_set))[:500]}
    else:
        raise SystemExit(
            "No airport universe: give --screen-list, or the OAG store, or --pilot, or "
            "--airports with an explicit list.")

    _log(f"building {len(run_set)} airports; week {week}; raster {'yes' if friction else 'no'}")
    # Receivers come from the widest airport universe available, never from the run set: a pilot
    # of 51 must still be able to send Heathrow's spill to Manchester.
    if screen:
        member_pool = sorted(set(screen) & set(coords))
        pool_src = f"GAF screen list ({len(member_pool)} with coordinates)"
    elif served.get("airports"):
        member_pool = sorted(set(served["airports"]) & set(coords))
        pool_src = f"OAG served index ({len(member_pool)} with coordinates)"
    else:
        member_pool = list(run_set)
        pool_src = ("RUN SET ONLY - no screen list and no served index, so receivers are limited "
                    "to the airports being built. Weights renormalise over a subset.")
        _log("WARNING: " + pool_src)
    _log(f"receiver universe: {pool_src}")

    out, stats = build(run_set, coords, geonames_path, friction, oag_db, sabre_db, week, served,
                       cache_dir=a.cache_dir, do_network=not a.no_network,
                       do_sabre=not a.no_sabre, segment=not a.no_segment,
                       member_pool=member_pool)
    stats["member_pool"] = pool_src

    doc = {"meta": meta_block(week, geonames_path, friction, stats, rec, run_set)}
    doc.update(out)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)

    _log(f"wrote {a.out}")
    _log(f"MEASURED RUN COST: {stats['sec_per_airport']}s per airport over {len(run_set)} "
         f"airports ({stats['elapsed_sec']}s total).")
    _log(f"full-set projection at this rate, 4 workers: "
         f"{3303 * stats['sec_per_airport'] / 4 / 3600:.1f} hours")
    if stats["errors"]:
        _log(f"{len(stats['errors'])} airports errored: {list(stats['errors'])[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
