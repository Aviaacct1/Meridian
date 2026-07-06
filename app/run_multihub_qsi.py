#!/usr/bin/env python3
"""
Avia Solutions - Multi-hub QSI runner
=====================================
One command from a multi-hub OAG schedules pull to a QSI capture for a proposed
service against full hub competition.

  load (calamine, fast) -> data-driven alliances/LCC -> build connections over
  every competing hub into the catchment -> inject the proposed service ->
  real MCT (config.MCT_MASTER) -> circuity cut -> QSI score -> capture per market.

Requires: python-calamine and airportsdata (pip install python-calamine airportsdata).
Run from the app directory so connection_builder, schedule_chain and config import.

Example:
  py -3.12 run_multihub_qsi.py --oag "Hub Airports.xlsx" \
     --catchment SFO,LAX,SJC,SAN,OAK \
     --proposed BA,LHR,SJC,1700,2000,645 --circuity 1.25 --out sjc_capture.csv
"""
import argparse, csv, glob, os
from collections import defaultdict
from connection_builder import load_oag_legs, load_mct_data, build_connections
from qsi_score import itinerary_qsi   # single source of truth for the QSI coefficients/formula
import schedule_chain as SC


def load_legs_any(oag):
    """Load and combine legs from one file, a comma-list, a glob, or a folder of
    OAG files. Lets the runner take the seven regional files for a date at once."""
    if isinstance(oag, (list, tuple)):
        files = list(oag)
    elif os.path.isdir(oag):
        files = sorted(glob.glob(os.path.join(oag, "*.xls*")))
    elif any(c in oag for c in "*?"):
        files = sorted(glob.glob(oag))
    elif "," in oag:
        files = [f.strip() for f in oag.split(",")]
    else:
        files = [oag]
    legs = []
    for f in files:
        legs.extend(load_oag_legs(f))
    return legs, files

def _proposed_leg(spec):
    """spec = carrier,dep,arr,deptime(HHMM),arrtime(HHMM),flyingmins"""
    car, dep, arr, dt, at, fly = spec.split(",")
    dh = int(dt[:2]) * 60 + int(dt[2:])
    ah = int(at[:2]) * 60 + int(at[2:])
    return {'carrier': car, 'flight_no': 'NEW', 'id': -1, 'dep_airport': dep, 'arr_airport': arr,
            'dep_terminal': '', 'arr_terminal': '', 'dep_time_mins': dh, 'arr_time_mins': ah,
            'flying_mins': int(fly), 'dep_day_set': set(range(1, 8)), 'arr_day_set': set(range(1, 8)),
            'dom_int': 'INT', 'arr_city': '', 'alliance': '', 'carrier_category': 'M', 'is_proposed': True}


def _build_over_hubs(arr_by, dep_by, alliances, mct, lcc, coords,
                     min_connect, max_connect, default_mct, circuity_cut):
    """Build single-connections over every hub common to arr_by/dep_by, with circuity cut."""
    conns = []
    for hub in dep_by:
        arr, dep = arr_by.get(hub, []), dep_by.get(hub, [])
        if not arr or not dep:
            continue
        v, _ = build_connections(arr, dep, alliances, mct, lcc,
                                 min_connect, max_connect, default_mct, hub_airport=hub)
        conns.extend(v)
    if circuity_cut:
        conns = SC.circuity_filter(conns, coords, circuity_cut)
    return conns


def _capture(conns, market_key, prop_key):
    """Per-market QSI total, proposed QSI and competing-hub set, keyed by market_key
    (the beyond point). Excess time is relative to the market's minimum-elapsed routing."""
    mn = defaultdict(lambda: 10 ** 9)
    for c in conns:
        if c['elapsed_time'] < mn[c[market_key]]:
            mn[c[market_key]] = c['elapsed_time']
    tot = defaultdict(float); prop = defaultdict(float); hubs = defaultdict(set)
    for c in conns:
        q = itinerary_qsi(c['frequency'], c['elapsed_time'], mn[c[market_key]],
                          c['cnx_type'], n_stops=c.get('n_stops', 1))
        tot[c[market_key]] += q
        if c.get('cnx_airport'):
            hubs[c[market_key]].add(c['cnx_airport'])
        if c.get(prop_key):
            prop[c[market_key]] += q
    return tot, prop, hubs


def _explain_rows(conns, market_key, prop_key, markets):
    """Every routing the engine built for the named markets, with its QSI parts, so we can
    see WHY the proposed hub wins too much (or too little) of a market: the competing hubs,
    their frequency, excess time and connection type, and each routing's QSI contribution
    and share. Read-only diagnostic; does not change scoring."""
    from qsi_score import itinerary_qsi
    from collections import defaultdict as _dd
    mn = _dd(lambda: 10 ** 9)
    for c in conns:
        if c[market_key] in markets and c['elapsed_time'] < mn[c[market_key]]:
            mn[c[market_key]] = c['elapsed_time']
    tot = _dd(float)
    rows = []
    for c in conns:
        m = c[market_key]
        if m not in markets:
            continue
        q = itinerary_qsi(c['frequency'], c['elapsed_time'], mn[m], c['cnx_type'],
                          n_stops=c.get('n_stops', 1))
        tot[m] += q
        rows.append({'market': m, 'hub': c.get('cnx_airport') or 'NONSTOP',
                     'carriers': f"{c.get('leg1_carrier', '')}/{c.get('leg2_carrier', '')}",
                     'freq': c['frequency'], 'elapsed_min': c['elapsed_time'],
                     'excess_min': round(c['elapsed_time'] - mn[m]), 'cnx_type': c['cnx_type'],
                     'qsi': q, 'proposed': bool(c.get(prop_key))})
    for r in rows:
        r['share'] = (r['qsi'] / tot[r['market']]) if tot[r['market']] else 0.0
    rows.sort(key=lambda r: (r['market'], -r['qsi']))
    return rows


def _nonstop_itins(legs_by_market, market_key):
    """The DIRECT catchment services as 0-stop itineraries, keyed by the beyond market, so the
    QSI denominator includes the nonstop competition. This is the proven method's "direct
    competition" lever: a nonstop is minimum-elapsed (ET 1.0), online (1.0) and nonstop service
    (1.0), so it dominates a market's QSI and floors the connecting shares - exactly why the
    decks give well-served markets ~0.3-2% and no-alternative markets ~8%. Excludes the proposed
    service itself (it is scored through the connections, not as competition)."""
    out = []
    for mk, legs in legs_by_market.items():
        for l in legs:
            if l.get('is_proposed'):
                continue
            days = l.get('dep_day_set') or set()
            out.append({market_key: mk,
                        'elapsed_time': l.get('flying_mins') or l.get('elapsed_time') or 10 ** 9,
                        'frequency': len(days) if days else 1,
                        'cnx_type': 'ONLINE', 'cnx_airport': None, 'n_stops': 0})
    return out


def _reverse_proposed(p, turn_min=120):
    """The proposed RETURN leg (catchment->hub) for QSI2. Arrival at the hub is assumed
    turn_min before the outbound hub departure (single-aircraft rotation); a real return
    schedule would refine the timing."""
    arr_hub = int((p['dep_time_mins'] - turn_min) % 1440)
    dep_cat = int((arr_hub - p['flying_mins']) % 1440)
    r = dict(p)
    r.update(dep_airport=p['arr_airport'], arr_airport=p['dep_airport'],
             dep_time_mins=dep_cat, arr_time_mins=arr_hub, is_proposed=True)
    return r


def run(oag, catchment, proposed=None, circuity_cut=1.25, mct_file=None,
        min_connect=20, max_connect=720, default_mct=90, db=None, week=None, qsi2=False,
        explain_markets=None, include_nonstops=False):
    cat = set(catchment)
    if db:
        # SQL leg pull from the OAG DuckDB store (market-scoped on catchment/hubs).
        from oag_store import load_legs_for_market
        proposed_hub = proposed.get('dep_airport') if proposed else None
        legs = load_legs_for_market(db, week, catchment, proposed_hub=proposed_hub,
                                    bidirectional=qsi2)
    else:
        legs, _files = load_legs_any(oag)
    alliances = SC.alliances_from_legs(legs) or []
    lcc = SC.lcc_from_legs(legs)
    if mct_file is None:
        try:
            from config import MCT_MASTER
            mct_file = str(MCT_MASTER)
        except Exception:
            pass
    mct = load_mct_data(mct_file, default_mct)
    coords = SC.load_airport_coords()

    # ---- QSI1: beyond -> hub -> catchment (market = beyond origin = dep_airport) ----
    arr1 = defaultdict(list); dep1 = defaultdict(list)
    for l in legs:
        h = l.get('arr_airport')
        if h and h not in cat and l.get('dep_airport') not in cat:   # beyond -> hub only
            arr1[h].append(l)
        if l.get('dep_airport') not in cat and l.get('arr_airport') in cat:
            dep1[l['dep_airport']].append(l)
    if proposed:
        dep1[proposed['dep_airport']].append(proposed)
    conns1 = _build_over_hubs(arr1, dep1, alliances, mct, lcc, coords,
                              min_connect, max_connect, default_mct, circuity_cut)
    if include_nonstops:
        # dep1 holds the direct beyond->catchment legs; each is the nonstop for ITS market
        # (its dep_airport). Add them after the circuity filter (a nonstop is never circuitous).
        conns1 += _nonstop_itins(dep1, 'dep_airport')
    tot1, prop1, hub1 = _capture(conns1, 'dep_airport', 'leg2_is_proposed')

    # ---- QSI2: catchment -> hub -> beyond (market = beyond dest = arr_airport) ----
    conns2 = []; tot2 = prop2 = hub2 = None
    if qsi2:
        arr2 = defaultdict(list); dep2 = defaultdict(list)
        for l in legs:
            if l['dep_airport'] in cat and l['arr_airport'] not in cat:
                arr2[l['arr_airport']].append(l)      # cat -> hub (arrives at hub)
            elif l['dep_airport'] not in cat and l['arr_airport'] not in cat:
                dep2[l['dep_airport']].append(l)       # hub -> beyond (departs hub)
        if proposed:
            rev = _reverse_proposed(proposed)
            arr2[rev['arr_airport']].append(rev)       # reverse proposed arrives at its hub
        conns2 = _build_over_hubs(arr2, dep2, alliances, mct, lcc, coords,
                                  min_connect, max_connect, default_mct, circuity_cut)
        if include_nonstops:
            # arr2 holds the direct catchment->beyond legs; each is the nonstop for its market.
            conns2 += _nonstop_itins(arr2, 'arr_airport')
        tot2, prop2, hub2 = _capture(conns2, 'arr_airport', 'leg1_is_proposed')

    # ---- per-market capture: average the QSI1 and QSI2 fair shares where each exists ----
    markets = set(tot1) | (set(tot2) if tot2 else set())
    rows = []
    for m in markets:
        fs1 = (prop1[m] / tot1[m]) if tot1.get(m) else None
        fs2 = (prop2[m] / tot2[m]) if (tot2 and tot2.get(m)) else None
        shares = [s for s in (fs1, fs2) if s is not None]
        if not shares:
            continue
        nhubs = len(hub1.get(m, set()) | (hub2.get(m, set()) if hub2 else set()))
        mq = tot1.get(m, 0) + (tot2.get(m, 0) if tot2 else 0)
        rows.append({'market': m, 'proposed_capture': sum(shares) / len(shares),
                     'competing_hubs': nhubs, 'market_qsi': round(mq, 2)})
    rows.sort(key=lambda r: -r['proposed_capture'])
    explain = None
    if explain_markets:
        em = set(explain_markets)
        explain = _explain_rows(conns1, 'dep_airport', 'leg2_is_proposed', em)
        if conns2:
            explain += _explain_rows(conns2, 'arr_airport', 'leg1_is_proposed', em)
    return {'connections': len(conns1) + len(conns2), 'markets': len(rows),
            'rows': rows, 'directions': 2 if qsi2 else 1, 'explain': explain}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", help="OAG xlsx file / folder / glob / comma-list (or use --db)")
    ap.add_argument("--db", help="OAG DuckDB store (oag.duckdb) - SQL leg pull instead of xlsx")
    ap.add_argument("--week", help="week string for --db (e.g. 2025-05-26); the store holds several")
    ap.add_argument("--catchment", required=True, help="comma list, e.g. SFO,LAX,SJC,SAN,OAK")
    ap.add_argument("--proposed", help="carrier,dep,arr,deptime,arrtime,flyingmins  e.g. BA,LHR,SJC,1700,2000,645")
    ap.add_argument("--circuity", type=float, default=1.25)
    ap.add_argument("--mct", default=None)
    ap.add_argument("--qsi2", action="store_true", help="average QSI1 (outbound) + QSI2 (return) per market")
    ap.add_argument("--nonstops", action="store_true",
                    help="CANDIDATE improvement (off by default): add the direct/nonstop competition "
                         "to the QSI denominator. Overcorrects on the single CI route tested - keep as "
                         "a measurable toggle until a wider OAG sample can validate it.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if not a.oag and not a.db:
        ap.error("one of --oag or --db is required")
    prop = _proposed_leg(a.proposed) if a.proposed else None
    res = run(a.oag, a.catchment.split(","), proposed=prop, circuity_cut=a.circuity,
              mct_file=a.mct, db=a.db, week=a.week, qsi2=a.qsi2,
              include_nonstops=a.nonstops)
    import statistics as st
    caps = [r['proposed_capture'] for r in res['rows'] if r['proposed_capture'] > 0]
    print(f"connections {res['connections']:,}  markets {res['markets']}")
    if caps:
        avg_hubs = sum(r['competing_hubs'] for r in res['rows']) / len(res['rows'])
        print(f"proposed capture: median {st.median(caps):.1%}  mean {sum(caps)/len(caps):.1%}  "
              f"(across {len(caps)} markets served; avg {avg_hubs:.0f} competing hubs/market)")
    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=['market', 'proposed_capture', 'competing_hubs', 'market_qsi'])
            w.writeheader(); w.writerows(res['rows'])
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
