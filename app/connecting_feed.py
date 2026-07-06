#!/usr/bin/env python3
"""
Avia Solutions - connecting-feed layer.
==============================================================================
The point-to-point model sizes catchment<->destination O&D only. For a hub
destination (FRA, LHR, ICN...) the route ALSO carries passengers travelling
catchment<->beyond-the-hub, routed over the new service. The validation showed
this is the model's one real gap: Lufthansa SJC-FRA carried 74,598 but the P2P
model read only 35,648, because half the route was India/Europe feed over FRA
that point-to-point cannot see. BA-London and Air China-Beijing matched on P2P
alone (within ~8%), so the feed must be LARGE for FRA and SMALL for those - which
is exactly what a QSI fair-share over the hub produces, because FRA's onward
markets (India especially) had poor Bay Area nonstop alternatives while London's
and Beijing's were better served.

METHOD (reuses the existing engine, no new QSI maths):
  feed = SUM over beyond-markets m of:  O&D(catchment <-> m)  x  QSI_capture(m)  x  stim_feed
where
  QSI_capture(m) = the proposed SJC-hub service's QSI fair share of market m against
                   ALL competing hubs, from run_multihub_qsi.run(..., qsi2=True). This
                   is the share of the EXISTING catchment<->m demand the new routing wins.
  O&D(catchment<->m) = the true catchment<->m market size from Sabre (however routed
                   today); the QSI share is what the new service captures of it.
  stim_feed = stimulation on connecting traffic (default 1.0: re-routed existing demand,
                   not newly created; expose it, don't bake it).

No double-count with P2P: the beyond markets m exclude the hub itself and the catchment,
so catchment<->hub (the P2P leg) is never in the feed sum.

The QSI half needs the OAG store (oag.duckdb); the demand half needs Sabre
(sabre.duckdb). Both live on John's machine, so run this there. The combiner
(feed_from_parts) is pure and unit-tested offline.

RUN (standalone):
  py -3.12 connecting_feed.py --oag-db "C:\\Avia\\oag.duckdb" --week 2025-05-26 \\
     --sabre "C:\\Avia\\sabre.duckdb" --catchment SFO,SJC,OAK \\
     --proposed LH,FRA,SJC,1300,0800,660 --base-yr 2018 --stim-feed 1.0
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def demand_by_market(sabre_db, catchment, year):
    """Catchment<->everywhere O&D for one travel year, grouped by the OTHER endpoint
    (the market). Both directions. Returns {market_airport: passengers}. This is the
    true market size the feed competes for; the QSI share decides what the new routing
    wins. Non-directional years record each market once (no double-count); directional
    years sum both ways, which is also correct for a market size."""
    import duckdb
    cat = [c.strip().upper() for c in catchment]
    oph = ",".join("?" * len(cat))
    con = duckdb.connect(sabre_db, read_only=True)
    try:
        # market = the non-catchment endpoint; sum both directions onto it
        sql = (
            f"SELECT m, SUM(p) FROM ("
            f"  SELECT destination_airport AS m, passengers AS p FROM sabre "
            f"    WHERE source_year = ? AND origin_airport IN ({oph}) AND destination_airport NOT IN ({oph}) "
            f"  UNION ALL "
            f"  SELECT origin_airport AS m, passengers AS p FROM sabre "
            f"    WHERE source_year = ? AND destination_airport IN ({oph}) AND origin_airport NOT IN ({oph}) "
            f") GROUP BY m")
        params = [year, *cat, *cat, year, *cat, *cat]
        return {r[0]: float(r[1] or 0) for r in con.execute(sql, params).fetchall()}
    finally:
        con.close()


def feed_from_parts(qsi_rows, od_by_market, stim_feed=1.0, hub=None, catchment=None):
    """Pure combiner (unit-tested offline). qsi_rows = run_multihub_qsi rows
    [{'market','proposed_capture',...}]; od_by_market = {market: O&D}. Returns
    (total_feed, breakdown_rows). Skips the hub itself and the catchment (no P2P
    double-count) and any market with no demand or no capture."""
    skip = set([hub] if hub else []) | set(c.strip().upper() for c in (catchment or []))
    rows = []
    total = 0.0
    for r in qsi_rows:
        m = r["market"]
        if m in skip:
            continue
        cap = r.get("proposed_capture") or 0.0
        d = od_by_market.get(m, 0.0)
        f = d * cap * stim_feed
        if f <= 0:
            continue
        rows.append({"market": m, "demand": round(d), "capture": round(cap, 4), "feed": round(f)})
        total += f
    rows.sort(key=lambda x: -x["feed"])
    return total, rows


def feed_forecast(oag_db, week, sabre_db, catchment, proposed_spec, base_yr,
                  stim_feed=1.0, circuity=1.25):
    """Full feed = QSI shares (OAG store) x beyond-market demand (Sabre). Needs both
    stores. proposed_spec = 'carrier,hub,catchment_airport,deptime,arrtime,flyingmins'
    (the hub->catchment leg, same shape run_multihub_qsi expects)."""
    import run_multihub_qsi as MQ
    prop = MQ._proposed_leg(proposed_spec)
    hub = prop["dep_airport"]
    res = MQ.run(None, [c.strip().upper() for c in catchment], proposed=prop,
                 circuity_cut=circuity, db=oag_db, week=week, qsi2=True)
    od = demand_by_market(sabre_db, catchment, base_yr)
    total, rows = feed_from_parts(res["rows"], od, stim_feed=stim_feed,
                                  hub=hub, catchment=catchment)
    return {"feed_total": total, "markets": len(rows), "rows": rows,
            "qsi_markets": res["markets"], "hub": hub}


def main():
    ap = argparse.ArgumentParser(description="Connecting feed over the destination hub.")
    ap.add_argument("--oag-db", required=True, help="oag.duckdb (QSI shares)")
    ap.add_argument("--week", required=True, help="OAG week string, e.g. 2025-05-26")
    ap.add_argument("--sabre", required=True, help="sabre.duckdb (beyond-market demand)")
    ap.add_argument("--catchment", required=True, help="comma list, e.g. SFO,SJC,OAK")
    ap.add_argument("--proposed", required=True,
                    help="carrier,hub,catchment_airport,deptime,arrtime,flyingmins  e.g. LH,FRA,SJC,1300,0800,660")
    ap.add_argument("--base-yr", type=int, required=True, help="Sabre travel year for demand")
    ap.add_argument("--stim-feed", type=float, default=1.0, help="stimulation on feed (default 1.0)")
    ap.add_argument("--circuity", type=float, default=1.25)
    ap.add_argument("--top", type=int, default=20, help="show top N feed markets")
    a = ap.parse_args()
    for p in (a.oag_db, a.sabre):
        if not os.path.exists(p):
            sys.exit(f"store not found: {p}")
    r = feed_forecast(a.oag_db, a.week, a.sabre, a.catchment.split(","),
                      a.proposed, a.base_yr, stim_feed=a.stim_feed, circuity=a.circuity)
    print(f"hub {r['hub']}  feed markets {r['markets']} of {r['qsi_markets']} QSI markets")
    print(f"{'market':>8} {'demand':>10} {'capture':>8} {'feed':>10}")
    print("-" * 40)
    for row in r["rows"][:a.top]:
        print(f"{row['market']:>8} {row['demand']:>10,} {row['capture']:>8.1%} {row['feed']:>10,}")
    print("-" * 40)
    print(f"TOTAL CONNECTING FEED (both directions): {r['feed_total']:,.0f}")


if __name__ == "__main__":
    main()
