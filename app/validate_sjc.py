#!/usr/bin/env python3
"""
Avia Solutions - SJC forecast validation harness (model vs analyst vs outturn).
================================================================================
The test John set: does the tool reproduce the prepared analyst forecast, and does it track
actual outturn. This runs both tiers against the SJC pitch set (sjc_validation_set.json, the
analyst's own assumptions from the pitches tracker).

For each prepared forecast it reports:
  ANALYST forecast  = seats x freq x 52 x 2 x load_factor          (from the tracker, no data)
  MODEL forecast    = Sabre P2P base (base_yr) x (1+CAGR)^years x stimulation x capture
  OUTTURN           = Sabre P2P actual in the launch year          (launched routes only)
  + a DEMAND CHECK: the analyst's implied P2P demand vs the model's Sabre-derived P2P demand,
    which isolates whether the tool's demand sizing matches the analyst before capture/stim.

The analyst tier needs no data (runs anywhere). The model and outturn tiers query the Sabre
store, so pass --sabre on the machine that holds it. The QSI-capture comparison (the tool's
QSI fair-share vs the analyst's hand-set capture) is the next layer: run run_multihub_qsi per
route against oag.duckdb and drop the capture in via --qsi-captures; left as a hook here.

RUN:
    py -3.12 validate_sjc.py                              # analyst tier only (no data)
    py -3.12 validate_sjc.py --sabre "C:\\Avia\\sabre.duckdb"   # full model vs analyst vs outturn
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def analyst_forecast(r):
    """The analyst's forecast pax/year, both directions = seats x freq x 52 x 2 x LF."""
    return r["seats"] * r["freq"] * 52 * 2 * r["lf"]


def sabre_od(db, origins, dest, year):
    """O&D passengers both directions between a set of origin airports (the catchment) and a
    destination, in a travel year. The analyst's 'Base Demand' is the CATCHMENT market (e.g. the
    Bay Area SFO+SJC+OAK), not the single departure airport - sizing demand from one airport is
    the error this harness exists to catch. Pass [SJC] alone to read what the SJC route carried
    (the outturn). Runs on the Sabre store."""
    import duckdb
    oph = ",".join("?" * len(origins))
    con = duckdb.connect(db, read_only=True)
    try:
        sql = (f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE source_year = ? "
               f"AND ((origin_airport IN ({oph}) AND destination_airport = ?) "
               f"OR (origin_airport = ? AND destination_airport IN ({oph})))")
        params = [year, *origins, dest, dest, *origins]
        return float(con.execute(sql, params).fetchone()[0] or 0)
    finally:
        con.close()


def sector_traffic(db, a, b, year):
    """EXACT passengers flown on the a-b sector (both directions) in a travel year: every itinerary
    in which a and b are CONSECUTIVE airports in the routing, at any leg, whatever the true origin
    or destination. Walks the full leg chain origin -> conn1 -> conn2 -> conn3 -> destination; the
    leg INTO the destination uses the last non-empty connection (COALESCE). This is the route's
    real carried traffic - point-to-point plus all connecting feed, inbound and outbound - which is
    what Sabre is for and the right basis to compare a forecast against."""
    import duckdb

    def adj(x, y):
        c1 = "NULLIF(connecting_airport1,'')"; c2 = "NULLIF(connecting_airport2,'')"; c3 = "NULLIF(connecting_airport3,'')"
        return (f"(origin_airport='{x}' AND COALESCE({c1},destination_airport)='{y}')"
                f" OR (connecting_airport1='{x}' AND COALESCE({c2},destination_airport)='{y}')"
                f" OR (connecting_airport2='{x}' AND COALESCE({c3},destination_airport)='{y}')"
                f" OR (connecting_airport3='{x}' AND destination_airport='{y}')")

    con = duckdb.connect(db, read_only=True)
    try:
        where = f"({adj(a, b)}) OR ({adj(b, a)})"
        sql = f"SELECT COALESCE(SUM(passengers),0) FROM sabre WHERE source_year = {int(year)} AND ({where})"
        return float(con.execute(sql).fetchone()[0] or 0)
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(description="Validate the model against prepared SJC forecasts + outturn.")
    ap.add_argument("--set", default=os.path.join(HERE, "sjc_validation_set.json"))
    ap.add_argument("--sabre", default=None, help="sabre.duckdb for the model + outturn tiers")
    ap.add_argument("--catchment", default="SFO,SJC,OAK", help="origin catchment for demand (default Bay Area)")
    ap.add_argument("--outturn-year", type=int, default=2024, help="steady year to read SJC-route outturn (default 2024, avoids COVID)")
    ap.add_argument("--oag-db", default=None, help="oag.duckdb to ADD the connecting-feed layer (P2P + feed)")
    ap.add_argument("--oag-week", default=None, help="OAG week string for the feed layer, e.g. 2025-05-26")
    ap.add_argument("--stim-feed", type=float, default=1.0, help="stimulation on connecting feed (default 1.0)")
    ap.add_argument("--out", default=None, help="optional CSV of the results")
    a = ap.parse_args()
    catchment = [x.strip().upper() for x in a.catchment.split(",")]

    routes = json.load(open(a.set))["routes"]
    have_sabre = a.sabre and os.path.exists(a.sabre)
    if a.sabre and not have_sabre:
        print(f"(sabre store not found at {a.sabre}; analyst tier only)\n")
    feed_on = bool(a.oag_db and os.path.exists(a.oag_db) and have_sabre)
    if a.oag_db and not feed_on:
        print(f"(feed layer off: need both --oag-db (found={os.path.exists(a.oag_db) if a.oag_db else False}) and --sabre)\n")
    if not (feed_on and a.oag_week):
        if feed_on and not a.oag_week:
            print("(feed layer needs --oag-week; running P2P only)\n")
            feed_on = False

    rows = []
    hdr = f"{'route':16} {'capt':>5} {'stim':>5} {'analyst f/c':>12} {'P2P f/c':>12} "
    hdr += (f"{'feed':>10} {'mdl+feed':>12} " if feed_on else "")
    hdr += f"{'outturn':>10} {'mdl/anl':>8} {'mdl/out':>8}"
    print(hdr)
    print("-" * (len(hdr) + 2))
    for r in routes:
        anl = r.get("analyst_forecast_pax") or analyst_forecast(r)   # deck headline if given, else LF x capacity
        model = outturn = feed = None
        if have_sabre:
            cm = [x.strip().upper() for x in r["catchment"].split(",")] if r.get("catchment") else catchment
            base = sabre_od(a.sabre, cm, r["dest"], r["base_yr"])   # catchment market (per-route override)
            grown = base * ((1 + r["cagr"]) ** (r["launch_yr"] - r["base_yr"]))
            model = grown * r["stim"] * r["capture"]               # P2P only
            # outturn = the EXACT traffic the route flew (every itinerary using the orig-dest leg,
            # P2P + all connecting feed inbound and outbound), same basis as the forecast, in the
            # route's year-2 (or the steady-year default).
            oy = r.get("outturn_yr") or a.outturn_year
            outturn = sector_traffic(a.sabre, r["orig"], r["dest"], oy) if r.get("launched") else None
            # connecting feed over the destination hub (catchment <-> beyond), if the OAG store is on
            if feed_on and r.get("fly_min"):
                import connecting_feed as CF
                carrier = r.get("carrier") or r["id"][:2]
                spec = f"{carrier},{r['dest']},{r['orig']},1300,0800,{int(r['fly_min'])}"
                try:
                    fr = CF.feed_forecast(a.oag_db, a.oag_week, a.sabre, cm, spec,
                                          r["base_yr"], stim_feed=a.stim_feed)
                    feed = fr["feed_total"]   # QSI fair share over the hub IS the feed capture; do NOT
                                              # re-apply the P2P capture. --stim-feed (<=1) is the single
                                              # calibration knob if the raw QSI share over-captures.
                except Exception as e:
                    print(f"  (feed failed for {r['id']}: {e})")
        model_feed = (model + feed) if (model is not None and feed is not None) else model
        anl_str = f"{anl:>12,.0f}"
        mdl_str = f"{model:>12,.0f}" if model is not None else f"{'-':>12}"
        out_str = f"{outturn:>10,.0f}" if outturn else f"{'-':>10}"
        cmp_model = model_feed if feed_on else model   # the number compared to analyst/outturn
        ma = f"{cmp_model/anl:>8.2f}" if cmp_model else f"{'-':>8}"
        mo = f"{cmp_model/outturn:>8.2f}" if (cmp_model and outturn) else f"{'-':>8}"
        line = f"{r['id']:16} {r['capture']:>5.0%} {r['stim']:>5.2f} {anl_str} {mdl_str} "
        if feed_on:
            line += f"{(feed if feed is not None else 0):>10,.0f} {(model_feed if model_feed is not None else 0):>12,.0f} "
        line += f"{out_str} {ma} {mo}"
        print(line)
        rows.append({"id": r["id"], "capture": r["capture"], "stim": r["stim"],
                     "analyst_fc": round(anl), "p2p_fc": round(model) if model else "",
                     "feed": round(feed) if feed else "",
                     "model_fc": round(model_feed) if model_feed else "",
                     "outturn": round(outturn) if outturn else "",
                     "model_vs_analyst": round(cmp_model/anl, 3) if cmp_model else "",
                     "model_vs_outturn": round(cmp_model/outturn, 3) if (cmp_model and outturn) else ""})

    print("\nCapture rates used by the analyst (the targets the tool's QSI fair-share is tested against):")
    caps = sorted(set(r["capture"] for r in routes))
    print("  range " + ", ".join(f"{c:.0%}" for c in caps))
    if not have_sabre:
        print("\nAnalyst tier only. Re-run with --sabre on the store for the model + outturn tiers.")
    if a.out:
        import csv
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
