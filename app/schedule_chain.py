#!/usr/bin/env python3
"""
Avia Solutions - Schedule Chain (Module III bridge)
===================================================
Drives the Connection Builder from a RAW OAG schedules export (the format Jess
pulls from OAG Analyser: one row per flight, standard OAG columns). Splits each
hub's flights into arrivals/departures, builds the viable single-connection
itineraries over each hub, derives the served destination scope, and applies a
TUNABLE circuity filter and pareto hub cut.

Replaces the need for the analyst's pre-split Leg 1.1/2.1 sheets: the tool now
goes straight from a raw OAG export to connections.

Pipeline: OAG Parser / load_oag_legs -> [this] -> QSI Scorer
"""
import math
from collections import defaultdict
from connection_builder import (
    load_oag_legs, build_connections, load_mct_data, load_alliance_data,
    load_lcc_list,
)

DEFAULT_CUTS = (0.75, 0.80, 0.85)   # report hub-cut sensitivity at these thresholds
DEFAULT_CIRCUITY_CUT = 1.25         # routed GCD / direct GCD; ~ Ollie's IN/OUT scope threshold


# ----------------------------------------------------------------------------
# Data-driven alliance + LCC (from the OAG columns, not hardcoded lists)
# ----------------------------------------------------------------------------
def alliances_from_legs(legs):
    """Build alliance carrier-sets from the OAG 'alliance' column."""
    groups = defaultdict(set)
    for l in legs:
        a = (l.get('alliance') or '').strip()
        c = l.get('carrier')
        if c and a and a.lower() not in ('', 'none', '0', 'nan'):
            groups[a].add(c)
    return [s for s in groups.values() if s]


def lcc_from_legs(legs):
    """Build the LCC exclusion set from the OAG carrier-category column."""
    lcc = set()
    for l in legs:
        cat = (l.get('carrier_category') or '').strip().upper()
        if cat in ('L', 'LCC', 'LOW COST', 'LOW-COST') and l.get('carrier'):
            lcc.add(l['carrier'])
    return lcc


# ----------------------------------------------------------------------------
# Circuity (uses great-circle distance + airport coordinates)
# ----------------------------------------------------------------------------
def load_airport_coords():
    """IATA airport coordinates for circuity. Uses the offline airportsdata
    package if available; returns {} if not (circuity then disabled)."""
    try:
        import airportsdata
        return {k: (v['lat'], v['lon']) for k, v in airportsdata.load('IATA').items()}
    except Exception:
        return {}


def _gc_km(a, b, coords):
    ca, cb = coords.get(a), coords.get(b)
    if not ca or not cb:
        return None
    (la1, lo1), (la2, lo2) = ca, cb
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def circuity_of(origin, hub, dest, coords):
    """Routed-via-hub GCD / direct GCD. >1 = detour; None if coords missing."""
    d1 = _gc_km(origin, hub, coords)
    d2 = _gc_km(hub, dest, coords)
    d0 = _gc_km(origin, dest, coords)
    if d1 is None or d2 is None or not d0:
        return None
    return (d1 + d2) / d0


def circuity_filter(connections, coords, cut=DEFAULT_CIRCUITY_CUT):
    """Drop connections whose routing is more circuitous than `cut`.
    Stamps each connection with 'circuity'; keeps connections whose circuity
    can't be computed (missing coordinates) rather than silently dropping them."""
    out = []
    for c in connections:
        cir = circuity_of(c['dep_airport'], c['cnx_airport'], c['arr_airport'], coords)
        c['circuity'] = cir
        if cir is None or cir <= cut:
            out.append(c)
    return out


# ----------------------------------------------------------------------------
# Connection building
# ----------------------------------------------------------------------------
def split_legs_at_hub(legs, hub):
    """From all flights touching a hub, split into arrivals and departures there."""
    arrivals = [l for l in legs if l.get('arr_airport') == hub]
    departures = [l for l in legs if l.get('dep_airport') == hub]
    return arrivals, departures


def build_over_hubs(legs, hubs, alliances, mct, lcc,
                    min_connect=20, max_connect=720, default_mct=90,
                    origins=None, dests=None):
    """Run the Connection Builder at each hub. Returns {hub: {valid, failed}}.

    origins / dests (optional sets) scope the build to a market: leg1 (arrivals)
    restricted to dep_airport in origins, leg2 (departures) to arr_airport in
    dests. Without them every arrival is paired with every departure at the hub,
    which is fine for a small file but explodes on a full single-hub pull.
    """
    by_hub = {}
    for hub in hubs:
        arr, dep = split_legs_at_hub(legs, hub)
        if origins:
            arr = [l for l in arr if l.get('dep_airport') in origins]
        if dests:
            dep = [l for l in dep if l.get('arr_airport') in dests]
        if not arr or not dep:
            continue
        valid, failed = build_connections(arr, dep, alliances, mct, lcc,
                                          min_connect, max_connect, default_mct,
                                          hub_airport=hub)
        by_hub[hub] = {'valid': valid, 'failed': failed}
    return by_hub


def flatten(by_hub):
    out = []
    for d in by_hub.values():
        out.extend(d['valid'])
    return out


def derive_scope(by_hub):
    """Served destination scope = beyond destinations reached by >=1 valid connection."""
    dests = set()
    for d in by_hub.values():
        for c in d['valid']:
            dests.add(c['arr_airport'])
    return dests


def hub_cut(connections, pct):
    """
    Per-market pareto hub cut. For each O&D market (origin->final dest), rank the
    hubs that serve it by weekly frequency (traffic proxy) and keep the set
    covering the top `pct` of that market's frequency. Tie-break by lower elapsed
    time (less circuitous). Returns the retained connections.
    """
    by_market = defaultdict(lambda: defaultdict(float))      # (o,d) -> hub -> freq
    elapsed = defaultdict(lambda: defaultdict(list))         # for tie-break
    for c in connections:
        mkt = (c['dep_airport'], c['arr_airport'])
        by_market[mkt][c['cnx_airport']] += c.get('frequency', 0)
        elapsed[mkt][c['cnx_airport']].append(c.get('elapsed_time', 0))

    keep = {}
    for mkt, hubfreq in by_market.items():
        total = sum(hubfreq.values())
        ranked = sorted(hubfreq.items(),
                        key=lambda x: (-x[1], _median(elapsed[mkt][x[0]])))
        kept, cum = set(), 0.0
        for hub, f in ranked:
            kept.add(hub); cum += f
            if total and cum / total >= pct:
                break
        keep[mkt] = kept

    return [c for c in connections
            if c['cnx_airport'] in keep[(c['dep_airport'], c['arr_airport'])]]


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return 0 if n == 0 else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def cut_sensitivity(connections, cuts=DEFAULT_CUTS):
    """Report how many connections survive at each hub-cut threshold."""
    base = len(connections)
    return [(pct, len(hub_cut(connections, pct)), base) for pct in cuts]


def run(oag_export_path, hubs, sheet=None,
        mct_file=None, alliance_file=None, lcc_file=None,
        min_connect=20, max_connect=720, default_mct=90,
        origins=None, dests=None, circuity_cut=None, coords=None):
    """End-to-end from a raw OAG export.

    - sheet defaults to auto-detect (OAG names sheets by job id).
    - mct_file defaults to the maintained MCT master (config.MCT_MASTER).
    - alliance and LCC come from the OAG data when present (alliance /
      carrier-category columns), else from the bundled defaults.
    - origins / dests scope the build to a market (see build_over_hubs).
    - circuity_cut (e.g. 1.25): if set, also return a circuity-filtered set.
    """
    if mct_file is None:
        try:
            from config import MCT_MASTER
            mct_file = str(MCT_MASTER)
        except Exception:
            pass
    legs = load_oag_legs(oag_export_path, sheet)
    alliances = alliances_from_legs(legs) or load_alliance_data(alliance_file)
    lcc = lcc_from_legs(legs) or load_lcc_list(lcc_file)
    mct = load_mct_data(mct_file, default_mct)
    by_hub = build_over_hubs(legs, hubs, alliances, mct, lcc,
                             min_connect, max_connect, default_mct,
                             origins=origins, dests=dests)
    conns = flatten(by_hub)
    result = {
        'legs': len(legs),
        'by_hub': by_hub,
        'connections': conns,
        'scope': derive_scope(by_hub),
        'cut_sensitivity': cut_sensitivity(conns),
        'alliance_groups': len(alliances),
        'lcc_excluded': len(lcc),
    }
    if circuity_cut is not None:
        if coords is None:
            coords = load_airport_coords()
        kept = circuity_filter(conns, coords, circuity_cut)
        result['circuity_cut'] = circuity_cut
        result['connections_after_circuity'] = kept
        result['scope_after_circuity'] = {c['arr_airport'] for c in kept}
    return result
