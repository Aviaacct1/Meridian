#!/usr/bin/env python3
"""
Avia Solutions - OAG-QSI capture default for the general route engine.
==============================================================================
The capture rate is NOT a free assumption. It is the QSI schedule-quality share of
the catchment's demand for the destination that a new nonstop wins against the
incumbents (the existing nonstop(s) from the nearby hub, plus one-stop connections).
This derives that share from the OAG schedules so the engine's DEFAULT capture is
computed, not hand-set; the capture slider then becomes a manual override on top.

Method = the frozen Avia QSI. It scores EVERY itinerary serving the destination with
the validated qsi_score.itinerary_qsi (frequency x elapsed-time decay x connection-type
x service-level), exactly as run_multihub_qsi._capture does, and takes the proposed
nonstop's share of the market's total QSI:

    capture = QSI(proposed nonstop) / QSI(all itineraries to the destination)

Itineraries: the existing nonstops from each catchment airport, the one-stop connections
over every hub (built with connection_builder.build_connections, the same timing/MCT/
alliance logic and circuity cut as the back-test), and the proposed home nonstop. A daily
nonstop against a multiple-daily incumbent plus its connections takes a share, not all.

build_qsi_capture() needs oag.duckdb (run on the machine that holds it). score/capture
are the validated qsi_score functions.
"""
from collections import defaultdict


def build_itineraries_from_store(db, week, home, dest_codes, catchment_airports,
                                 proposed_freq, proposed_block_min, mct_file=None,
                                 default_mct=90, min_connect=20, max_connect=720,
                                 circuity_cut=1.25):
    """Assemble every itinerary serving the destination market for the catchment, plus the
    proposed home nonstop. Each itinerary = {elapsed, frequency, cnx_type, n_stops, is_proposed,
    label}. Reuses the back-test's connection logic so the QSI denominator is the same."""
    import duckdb
    from oag_store import _COLS, _row_to_leg
    from connection_builder import build_connections, load_mct_data
    import schedule_chain as SC

    cat = [a.strip().upper() for a in catchment_airports]
    dst = [a.strip().upper() for a in dest_codes]
    con = duckdb.connect(db, read_only=True)
    try:
        def q(where, params):
            rows = con.execute(f"SELECT {_COLS} FROM oag WHERE week=? AND {where}",
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

    itins = []
    # one-stop connections catchment -> hub -> destination (validated frequency + cnx_type)
    arr_by_hub = defaultdict(list); dep_by_hub = defaultdict(list)
    for l in cat_hub:
        arr_by_hub[l["arr_airport"]].append(l)
    for l in hub_dest:
        dep_by_hub[l["dep_airport"]].append(l)
    conns = []
    for hub in hubs:
        v, _failed = build_connections(arr_by_hub.get(hub, []), dep_by_hub.get(hub, []),
                                       alliances, mct, lcc, min_connect, max_connect,
                                       default_mct, hub_airport=hub)
        conns.extend(v)
    if circuity_cut:
        try:
            coords = SC.load_airport_coords()
            conns = SC.circuity_filter(conns, coords, circuity_cut)
        except Exception:
            pass
    for c in conns:
        itins.append({"elapsed": c["elapsed_time"], "frequency": c["frequency"],
                      "cnx_type": c["cnx_type"], "n_stops": c.get("n_stops", 1),
                      "is_proposed": False,
                      "label": f"{c.get('dep_airport')}-{c.get('cnx_airport')}-NYC "
                               f"{c.get('leg1_carrier')}/{c.get('leg2_carrier')}"})
    # existing nonstops from the catchment airports (0-stop, online)
    byk = defaultdict(lambda: {"freq": 0, "elapsed": 10 ** 9})
    for l in nonstops:
        days = l.get("dep_day_set") or set()
        k = (l["dep_airport"], l["carrier"])
        byk[k]["freq"] += len(days) if days else 1
        fm = l.get("flying_mins") or 10 ** 9
        byk[k]["elapsed"] = min(byk[k]["elapsed"], fm)
    for (dep, car), v in byk.items():
        itins.append({"elapsed": v["elapsed"], "frequency": v["freq"], "cnx_type": "ONLINE",
                      "n_stops": 0, "is_proposed": False, "label": f"{dep}-NYC {car} nonstop"})
    # the proposed home nonstop
    itins.append({"elapsed": proposed_block_min, "frequency": proposed_freq, "cnx_type": "ONLINE",
                  "n_stops": 0, "is_proposed": True, "label": f"{home}-NYC PROPOSED nonstop"})
    return itins, {"nonstops": len(byk), "connections": len(conns), "hubs": len(hubs)}


def capture_share(itins):
    """The proposed nonstop's QSI share of the destination market (one market, all dest
    airports pooled). Uses the validated qsi_score.itinerary_qsi."""
    from qsi_score import itinerary_qsi
    if not itins:
        return 0.0
    me = min(it["elapsed"] for it in itins)
    tot = prop = 0.0
    for it in itins:
        q = itinerary_qsi(it["frequency"], it["elapsed"], me, it["cnx_type"], it["n_stops"])
        it["qsi"] = q
        tot += q
        if it["is_proposed"]:
            prop += q
    return (prop / tot) if tot else 0.0


def qsi_capture_default(db, week, home, dest_codes, catchment_airports, proposed_freq=7,
                        proposed_block_min=540, mct_file=None, circuity_cut=1.25):
    """The capture default: build the destination's itineraries from OAG and return the proposed
    nonstop's QSI share, with the top itineraries for audit."""
    itins, detail = build_itineraries_from_store(
        db, week, home, dest_codes, catchment_airports, proposed_freq, proposed_block_min,
        mct_file=mct_file, circuity_cut=circuity_cut)
    cap = capture_share(itins)
    itins.sort(key=lambda it: -it.get("qsi", 0.0))
    return {"capture": cap, "n_itineraries": len(itins), "detail": detail,
            "itineraries": itins[:12]}
