#!/usr/bin/env python3
"""
Market background brief (24 August 2026, from Jarek Zych's tester feedback).

Assembles the MEASURED market facts for a route before anything is forecast: what the
O&D market is, how it travels today, who carries it, its cabin mix, the connecting
potential over each end, the nonstop schedule picture, and the origin catchment. The
design rule, agreed on the mockup (MOCKUP-market-background-24Aug2026.html): NO
FORECAST CONTENT appears here, only measured fact from the stores, so this panel can
never disagree with a run. Everything is labelled with its source and period by the
dashboard, per the house chart rules.

FLAG RATHER THAN FILL. Every section is built independently and a section that cannot
be measured says so ({"available": False, "note": ...}) instead of approximating. The
carrier-share section introspects the Sabre schema for a carrier column (same pattern
as leakage_why.py) because the store's column set varies by extract; if the store does
not carry one, the panel says that rather than guessing from schedules.

COST. The heavy queries are the two connecting-market builds (the same Sabre
aggregates optimise_departure pays for). The endpoint in cortex_app caches the whole
brief per (origin, dest, week, year), so the price is paid once per route per store
vintage; the dashboard fires the request in the background and never blocks Run on it.
"""

import os
import duckdb


# ---------------------------------------------------------------- helpers

def _con(db):
    con = duckdb.connect(db, read_only=True)
    try:
        from db_registry import apply_limits
        apply_limits(con)
    except Exception:
        pass
    return con


_SABRE_CARRIER_CANDIDATES = ("marketing_carrier", "operating_carrier", "marketing_airline",
                             "airline", "carrier", "mkt_al", "op_al", "dominant_carrier")


def _sabre_carrier_col(sabre_db):
    """The store's carrier column, if it has one. Introspected, never assumed."""
    con = _con(sabre_db)
    try:
        cols = {r[0].lower() for r in
                con.execute("SELECT column_name FROM information_schema.columns "
                            "WHERE table_name='sabre'").fetchall()}
    finally:
        con.close()
    for c in _SABRE_CARRIER_CANDIDATES:
        if c in cols:
            return c
    return None


def _dow_count(days):
    """days_of_op mask to a weekly count. Same reading as wave_cache._dow."""
    return sum(1 for ch in str(days or "") if ch in "1234567")


# ---------------------------------------------------------------- sections

def p2p_series(sabre_db, competing, dest_codes):
    """Each-way O&D passengers per source year, catchment airports to destination metro.
    All actual; the years are whatever the store holds, read from the rows, never assumed."""
    ph_a = ",".join("?" * len(competing)); ph_d = ",".join("?" * len(dest_codes))
    con = _con(sabre_db)
    try:
        rows = con.execute(
            f"SELECT source_year, COALESCE(SUM(passengers),0) FROM sabre "
            f"WHERE origin_airport IN ({ph_a}) AND destination_airport IN ({ph_d}) "
            f"GROUP BY source_year ORDER BY source_year",
            [*competing, *dest_codes]).fetchall()
    finally:
        con.close()
    return [{"year": int(y), "pax": int(round(float(p or 0)))} for y, p in rows if y]


def carrier_share(sabre_db, competing, dest_codes, year, top=5):
    """Share of the O&D market by carrier, IF the store carries a carrier column."""
    col = _sabre_carrier_col(sabre_db)
    if not col:
        return {"available": False,
                "note": "this Sabre extract holds no carrier column, so the carrier "
                        "split cannot be measured from it"}
    ph_a = ",".join("?" * len(competing)); ph_d = ",".join("?" * len(dest_codes))
    con = _con(sabre_db)
    try:
        rows = con.execute(
            f"SELECT UPPER(TRIM({col})), COALESCE(SUM(passengers),0) p FROM sabre "
            f"WHERE origin_airport IN ({ph_a}) AND destination_airport IN ({ph_d}) "
            f"AND source_year = ? GROUP BY 1 ORDER BY p DESC",
            [*competing, *dest_codes, year]).fetchall()
    finally:
        con.close()
    tot = sum(float(p or 0) for _, p in rows)
    if not tot:
        return {"available": False, "note": "no passengers recorded for this market"}
    head = [{"carrier": c or "?", "share": round(float(p) / tot, 4)} for c, p in rows[:top]]
    other = 1.0 - sum(x["share"] for x in head)
    return {"available": True, "column": col, "total_pax": int(round(tot)),
            "carriers": head, "other_share": round(max(other, 0.0), 4)}


def travels_today(sabre_db, competing, dest_codes, home, year):
    """How the catchment's demand to the destination routes today: via which departure
    airport, and how much of it flies nonstop at all."""
    import sabre_catchment as SC
    split, total, avg_fare = SC.destination_market_split(
        sabre_db, competing, list(dest_codes), year=year)
    ns_share, _ = SC.nonstop_share(sabre_db, competing, list(dest_codes), year=year)
    via = [{"airport": a, "pax": int(round(p)), "share": round(p / total, 4) if total else 0.0}
           for a, p in sorted(split.items(), key=lambda kv: -kv[1]) if p > 0]
    home_pax = split.get(home, 0.0)
    return {"total_pax": int(round(total)), "via": via, "nonstop_share": round(ns_share, 4),
            "home_share": round(home_pax / total, 4) if total else 0.0}


def cabin_mix(sabre_db, competing, dest_codes, year):
    """Measured business+first share on the seat-count definition (front_cabin_share)."""
    import route_forecast as RF
    front = RF.front_cabin_share(sabre_db, competing, list(dest_codes), year=year)
    return {"front_share": round(float(front), 4), "back_share": round(1.0 - float(front), 4)}


def connecting_potential(sabre_db, oag_db, week, competing, home, dest_airport, dest_codes,
                         year, circuity=1.35, factor_indirect=1.044, top=5):
    """The connecting demand REACHABLE over each end: the same beyond/behind market
    builds the optimiser prices, before any capture. Reported as potential, expressly
    not as what a service wins; winning it is the forecast's job."""
    import route_feed as RFD
    scope = [x for x in RFD.hub_served(oag_db, week, dest_airport) if x not in competing]
    scope = RFD.on_the_way(competing, dest_airport, scope, circuity=circuity)
    b_mkt = RFD.connecting_market(sabre_db, competing, scope, year, factor_indirect)
    feeders = [y for y in RFD.feeders_to(oag_db, week, [home])
               if y != home and y not in dest_codes]
    h_mkt = RFD.behind_market(sabre_db, feeders, list(dest_codes), year, factor_indirect)
    b_top = sorted(b_mkt.items(), key=lambda kv: -kv[1])[:top]
    h_top = sorted(h_mkt.items(), key=lambda kv: -kv[1])[:top]
    return {"beyond_pax": int(round(sum(b_mkt.values()))),
            "behind_pax": int(round(sum(h_mkt.values()))),
            "beyond_top": [{"market": m, "pax": int(round(p))} for m, p in b_top],
            "behind_top": [{"market": m, "pax": int(round(p))} for m, p in h_top],
            "circuity": circuity}


def nonstop_services(oag_db, week, competing, dest_codes):
    """The nonstop schedule picture to the destination from every catchment airport,
    deduped the wave_cache way (the store repeats each record once per region label)."""
    ph_o = ",".join("?" * len(competing)); ph_d = ",".join("?" * len(dest_codes))
    con = _con(oag_db)
    try:
        rows = con.execute(
            f"SELECT DISTINCT carrier, dep_airport, arr_airport, local_dep_time, "
            f"aircraft_code, seats, days_of_op FROM oag "
            f"WHERE week=? AND dep_airport IN ({ph_o}) AND arr_airport IN ({ph_d})",
            [week, *competing, *dest_codes]).fetchall()
    finally:
        con.close()
    svc = {}
    for car, dep, arr, dt, ac, seats, days in rows:
        key = (str(car or "").strip().upper(), dep, arr, str(dt or ""), str(ac or ""))
        rec = svc.setdefault(key, {"carrier": key[0], "from": dep, "to": arr,
                                   "dep_local": str(dt or ""), "aircraft": str(ac or ""),
                                   "seats": int(seats or 0), "_days": set()})
        rec["_days"].update(ch for ch in str(days or "") if ch in "1234567")
    out = []
    for rec in svc.values():
        rec["weekly"] = len(rec.pop("_days")) or None   # None = days mask absent, not zero
        out.append(rec)
    out.sort(key=lambda r: (r["from"], r["carrier"], r["dep_local"]))
    return out


def catchment_summary(profile):
    """The strip's catchment numbers from an already-built catchment_profile dict."""
    return {"total_pop": profile.get("total_pop"), "reach_120_pop": profile.get("reach_120_pop"),
            "airport": profile.get("airport", {}).get("code")}


# ---------------------------------------------------------------- assembly

def build_brief(ctx, origin, dest, dump=None, radius_km=220.0, catchment_fn=None):
    """The whole brief. ctx is cortex_app._live_ctx(); catchment_fn is
    cortex_app.catchment_profile, injected so this module owns no drive-engine wiring.
    Sections fail independently: one broken section must not take down the panel."""
    import route_engine as RE, geo_resolve as GEO, oag_served as OAS
    sabre_db, oag_db = ctx["sabre_db"], ctx["oag_db"]
    week, year = ctx["week"], int(ctx["year"] or 0)
    idx = ctx.get("served"); served = OAS.served_set(idx) if idx else None
    om = GEO.resolve_metro(origin, served_index=idx, dump=dump, expand=False)
    dm = GEO.resolve_metro(dest, served_index=idx, dump=dump, expand=True)
    home, dest_airport, dest_codes = om["primary"], dm["primary"], dm["airports"]
    ap = RE._airports(); o = ap.get(home); d = ap.get(dest_airport)
    if not o or not d:
        return {"ok": False, "error": "airport resolution failed for one endpoint"}
    competing = [r["iata"] for r in RE.competing_airports(o, radius_km, served, True)]

    brief = {"ok": True, "origin": {"iata": home, "city": o.get("city") or origin},
             "dest": {"iata": dest_airport, "city": d.get("city") or dest,
                      "airports": list(dest_codes)},
             "competing": competing,
             "basis": {"sabre_year": year, "oag_week": week}}

    def section(name, fn, *a, **k):
        try:
            brief[name] = fn(*a, **k)
        except Exception as e:
            brief[name] = {"available": False, "note": f"could not be measured: {e}"}

    section("series", p2p_series, sabre_db, competing, dest_codes)
    section("carriers", carrier_share, sabre_db, competing, dest_codes, year)
    section("travels", travels_today, sabre_db, competing, dest_codes, home, year)
    section("cabin", cabin_mix, sabre_db, competing, dest_codes, year)
    section("connecting", connecting_potential, sabre_db, oag_db, week, competing,
            home, dest_airport, dest_codes, year)
    section("services", nonstop_services, oag_db, week, competing, dest_codes)
    if catchment_fn is not None:
        try:
            brief["catchment"] = catchment_summary(catchment_fn(origin))
        except Exception as e:
            brief["catchment"] = {"available": False, "note": f"could not be measured: {e}"}
    return brief
