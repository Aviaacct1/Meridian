#!/usr/bin/env python3
"""
Avia Solutions - per-airport QSI to a destination, as the catchment service-quality term.
==========================================================================================
The proper method (returning to it after the primacy fudge, John 30 June): the capture is NOT a
standalone QSI share - that would ignore ACCESS (a Genoa resident takes a lower-frequency nonstop
15 min away over Milan's huge frequency 2 hours away). QSI is the SCHEDULE-QUALITY term inside the
catchment choice model, balanced against drive time, exactly as the calibrated Genoa model does.

This computes, for each candidate airport, its QSI to the destination from the OAG schedules
(its nonstops + realistic one-stop connections, scored with the frozen qsi_score.itinerary_qsi),
and maps that to a service_value ($-equivalent) that feeds catchment.Airport.service_value. The
proposed origin's QSI includes its new nonstop. run_catchment then balances each locale's drive
time against each airport's service quality and allocates the market; the origin's allocation IS
the forecast (no separate capture multiplier).

  from route_qsi import airport_qsi_to_dest, service_values_from_qsi
  q = airport_qsi_to_dest(db, week, ["JFK","EWR","LGA"], ["GOA","MXP","LIN","BGY","TRN","BLQ"],
                          proposed_origin="GOA", proposed_freq=7, proposed_block_min=540)
  sv = service_values_from_qsi(q, scale=SERVICE_SCALE)   # {airport: $ service_value}
"""
import math
from collections import defaultdict

SERVICE_SCALE = 220.0   # $ per ln-unit of QSI; calibrated so Genoa reproduces (see route_engine)
CONN_FREQ_CAP = 14.0    # cap a connecting route's weekly frequency (2x daily) - avoids the
                        # codeshare / many-flight-pairs explosion that broke the old share calc


def _dedupe_flights(legs):
    """Collapse codeshare duplicates: one physical flight per (dep, arr, local dep time). Counts
    real operated frequency, not the inflated marketing-carrier count (EK MXP-JFK read 98/wk = 14
    real x ~7 codeshare rows)."""
    seen = {}
    for l in legs:
        key = (l.get("dep_airport"), l.get("arr_airport"), l.get("dep_time_mins"))
        if key not in seen:
            seen[key] = l
    return list(seen.values())


def airport_qsi_to_dest(db, week, dest_codes, catchment_airports, proposed_origin=None,
                        proposed_freq=7, proposed_block_min=540, mct_file=None,
                        default_mct=90, min_connect=20, max_connect=720, circuity_cut=1.25,
                        with_diag=False):
    """{airport: QSI to the destination} for every catchment airport. Service-level: nonstops one
    per carrier (codeshares deduped), connections aggregated per (origin, hub, carriers) route with
    a frequency cap. The proposed origin's QSI includes its new nonstop."""
    import duckdb
    from oag_store import _COLS, _row_to_leg
    from connection_builder import build_connections, load_mct_data
    from qsi_score import itinerary_qsi
    import schedule_chain as SC

    cat = [a.strip().upper() for a in catchment_airports]
    dst = [a.strip().upper() for a in dest_codes]
    con = duckdb.connect(db, read_only=True)
    try:
        def q(where, params):
            # ORDER BY ALL is not cosmetic. DuckDB gives no row order without one, and on a parallel
            # scan the order varies run to run. _dedupe_flights below keeps the FIRST row per
            # (dep, arr, local dep time), so a different order keeps a different codeshare row and
            # with it a different carrier and flying time. Measured 10 August 2026: three fresh runs
            # of the same SJC-TPE call returned SFO's QSI as 24.47, 25.11 and 24.46, which moved the
            # capture share by up to 2.7% on an unchanged input. Invisible while the measured airport
            # factor overrides the QSI share; straight into the client number once AVIA_FREQ_SENSITIVE
            # is on. The sort costs circa a second on this route.
            rows = con.execute(f"SELECT {_COLS} FROM oag WHERE week=? AND {where} ORDER BY ALL",
                               [week] + params).fetchall()
            return [_row_to_leg(r, i) for i, r in enumerate(rows)]
        ph_cat = ",".join("?" * len(cat)); ph_dst = ",".join("?" * len(dst))
        nonstops = q(f"dep_airport IN ({ph_cat}) AND arr_airport IN ({ph_dst})", cat + dst)
        hub_dest = q(f"arr_airport IN ({ph_dst}) AND dep_airport NOT IN ({ph_cat}) "
                     f"AND dep_airport NOT IN ({ph_dst})", dst + cat + dst)
        hubs = sorted({l["dep_airport"] for l in hub_dest})
        cat_hub = []
        if hubs:
            ph_hub = ",".join("?" * len(hubs))
            cat_hub = q(f"dep_airport IN ({ph_cat}) AND arr_airport IN ({ph_hub})", cat + hubs)
    finally:
        con.close()

    alliances = SC.alliances_from_legs(nonstops + hub_dest + cat_hub) or []
    lcc = SC.lcc_from_legs(nonstops + hub_dest + cat_hub) or set()
    if mct_file is None:
        try:
            from config import MCT_MASTER
            mct_file = str(MCT_MASTER)
        except Exception:
            mct_file = None
    mct = load_mct_data(mct_file, default_mct)

    # services = list of (origin_airport, freq, elapsed, cnx_type, n_stops)
    services = []
    # nonstops: one service per (origin, carrier), codeshares deduped
    nbyk = defaultdict(lambda: {"freq": 0.0, "elapsed": 10 ** 9})
    for l in _dedupe_flights(nonstops):
        days = l.get("dep_day_set") or set()
        k = (l["dep_airport"], l["carrier"])
        nbyk[k]["freq"] += len(days) if days else 1
        nbyk[k]["elapsed"] = min(nbyk[k]["elapsed"], l.get("flying_mins") or 10 ** 9)
    for (org, _car), v in nbyk.items():
        services.append((org, v["freq"], v["elapsed"], "ONLINE", 0))
    # connections: build per hub, aggregate per (origin, hub, carriers) route, freq capped
    arr_by_hub = defaultdict(list); dep_by_hub = defaultdict(list)
    for l in _dedupe_flights(cat_hub):
        arr_by_hub[l["arr_airport"]].append(l)
    for l in _dedupe_flights(hub_dest):
        dep_by_hub[l["dep_airport"]].append(l)
    conns = []
    for hub in hubs:
        v, _ = build_connections(arr_by_hub.get(hub, []), dep_by_hub.get(hub, []), alliances,
                                 mct, lcc, min_connect, max_connect, default_mct, hub_airport=hub)
        conns.extend(v)
    if circuity_cut:
        try:
            conns = SC.circuity_filter(conns, SC.load_airport_coords(), circuity_cut)
        except Exception:
            pass
    cagg = defaultdict(lambda: {"freq": 0.0, "elapsed": 10 ** 9, "ct": "INTERLINING"})
    for c in conns:
        key = (c.get("dep_airport"), c.get("cnx_airport"), c.get("leg1_carrier"), c.get("leg2_carrier"))
        a = cagg[key]
        a["freq"] += c.get("frequency", 0) or 0
        a["elapsed"] = min(a["elapsed"], c.get("elapsed_time") or 10 ** 9)
        a["ct"] = c.get("cnx_type", "INTERLINING")
    for (org, _hub, _l1, _l2), a in cagg.items():
        services.append((org, min(a["freq"], CONN_FREQ_CAP), a["elapsed"], a["ct"], 1))

    # DIAGNOSTICS OVER THE CONNECTION SET, added 9 August 2026 so the connecting structure this
    # function already builds can leave the function instead of being discarded.
    #
    # BT2 needs two summaries of exactly this work: the count of scheduled legs in play, and the
    # connection-competition strength, which is the frequency of each connection weighted by how far
    # its elapsed time falls behind the best available. bt2_capture computes both by calling
    # build_connections a second time, which was the only reason a second call existed. Returned
    # here, that duplication goes away and both engines read one calculation.
    #
    # The elapsed-time decay is bt2_capture._et, reproduced rather than imported because app must not
    # depend on bt2: bt2 imports the engine, and a cycle between them is worse than one shared
    # formula. If either changes, both change. The weighting of the three connection types belongs to
    # BT2 and is applied on its side, not here.
    _diag = None
    if with_diag:
        def _et(el, mn):
            x = (el - mn) / 60.0
            return 1.0 if x <= 0 else 1.0 / ((int(x / 0.1) + 1) ** 0.8)
        _mn = min([c.get("elapsed_time") or 10 ** 9 for c in conns] or [10 ** 9])
        _S = {"ONLINE": 0.0, "ALLIANCE": 0.0, "INTERLINING": 0.0}
        for c in conns:
            t = c.get("cnx_type", "INTERLINING")
            _S[t] = _S.get(t, 0.0) + (c.get("frequency", 0) or 0) * _et(
                c.get("elapsed_time") or _mn, _mn)
        _diag = {"n_legs": len(nonstops) + len(hub_dest) + len(cat_hub),
                 "n_connections": len(conns),
                 "min_elapsed": (None if _mn >= 10 ** 9 else _mn),
                 "s_online": _S["ONLINE"], "s_alliance": _S["ALLIANCE"],
                 "s_interline": _S["INTERLINING"]}
    # the proposed origin's new nonstop
    if proposed_origin:
        services.append((proposed_origin, float(proposed_freq), float(proposed_block_min), "ONLINE", 0))

    # score: QSI per service vs the market's best routing, summed per origin airport
    me = min((s[2] for s in services), default=0)
    qsi = defaultdict(float)
    for org, freq, elapsed, ct, ns in services:
        qsi[org] += itinerary_qsi(freq, elapsed, me, ct, ns)
    # Default return is unchanged, so every existing caller is untouched.
    return (dict(qsi), _diag) if with_diag else dict(qsi)


def service_values_from_qsi(qsi_dict, scale=SERVICE_SCALE, ln_cap=2.5):
    """Map each airport's QSI to a $-equivalent service_value for the catchment gencost term:
    service_value = scale x ln(qsi / geometric-mean(qsi)), CAPPED at +/- ln_cap. Centred on the
    geomean so an average-served airport sits at 0, a strongly-served one positive (more
    attractive), a weakly served one negative. The cap is the key bound: an airport with the ONLY
    nonstop to a niche destination has a huge qsi/geomean ratio against a weak field, which without
    a cap earns an UNBOUNDED pull and draws population it would never really get (Hannover-Varna).
    A nonstop's advantage over connecting is large but FINITE. ln_cap 2.5 (~12x the geomean) leaves
    Genoa untouched (Milan's NY service keeps GOA's ratio modest) but tames the lone-nonstop draw.
    Airports with no service to the destination get a large negative value."""
    vals = [v for v in qsi_dict.values() if v > 0]
    if not vals:
        return {a: 0.0 for a in qsi_dict}
    gm = math.exp(sum(math.log(v) for v in vals) / len(vals))
    out = {}
    for a, v in qsi_dict.items():
        if v > 0:
            out[a] = scale * max(-ln_cap, min(ln_cap, math.log(v / gm)))
        else:
            out[a] = -scale * 4.0
    return out
