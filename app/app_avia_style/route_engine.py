#!/usr/bin/env python3
"""
Avia Cortex - general route engine: assess ANY city pair.
=========================================================
Generalises the Genoa-New York chain to any origin/destination. The engine modules
(catchment, route_demand, aircraft_economics) are already route-agnostic; this wires the
INPUTS for any pair, with the fixes that make an arbitrary route trustworthy, all driven
by the OAG store and Sabre rather than hand-set guesses:

  Fix 1  competing airports restricted to those with REAL scheduled service (OAG), each
         weighted by its OAG size so the calibrated catchment parameters see a comparable
         scale, not a blind radius of every airfield. (oag_served.py)
  Fix 2  the city string resolves to its MAIN COMMERCIAL airport(s): "New York" ->
         JFK/EWR/LGA, "Genoa" -> GOA, by geocoding then ranking on OAG service. (geo_resolve.py)
  Fix 3  demand sized by a propensity model: real Sabre O&D / catchment population where the
         pair exists, observed cache offline, else a Genoa-anchored estimate kept beside the
         data figure as a cross-check. (propensity.py)
  Capture the capture rate DEFAULTS to the OAG-QSI schedule-quality share of the destination
         market a new nonstop wins (qsi_capture.py); the capture argument is a manual OVERRIDE
         on top of that default, not the source of truth.

FIDELITY: Genoa-New York is the calibrated benchmark. For an arbitrary pair the catchment
PARAMETERS are transferred from Genoa and (absent Sabre) the propensity is estimated, so the
result is a FIRST-CUT ESTIMATE with real population, geography, schedules and economics. Where
Sabre / observed data exists the propensity and the QSI capture promote it to "validated".

    from route_engine import assess
    r = assess("Genoa", "New York", served_index="served_2025-05-26.json",
               observed_cache="cases/genoa_nyc_observed.json", drive_cache="genoa_drive.json",
               qsi_db="oag.duckdb", qsi_week="2025-05-26")
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import geonames as G, catchment as C, route_demand as RD
import geo_resolve as GEO, oag_served as OAS, propensity as PROP

DUMP = os.path.join(HERE, "cities5000.txt")
CAL = dict(logit_scale=0.008, value_of_time_per_hr=60.0, att_exponent=0.75)
DEFAULT_CHARGES = dict(landing_per_turn=2000.0, pax_charge_per_pax=20.0,
                       recovery_per_pax=0.0, ground_handling_per_turn=1500.0)
DEFAULT_CAPTURE = 0.30          # base leaked-recovery rate (fallback when no OAG-QSI share)
REPAT_PRIMARY = 0.90            # leaked-recovery rate a DOMINANT primary airport reaches

_AP = None
def _airports():
    global _AP
    if _AP is None:
        import airportsdata
        _AP = airportsdata.load("IATA")
    return _AP


def gc_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def competing_airports(origin_rec, radius_km=220.0, served=None, same_country_only=True,
                       restrict=None, max_water_gap_km=20.0):
    """Airports within radius_km of the origin (the competing set). If `served` (codes with real
    service from OAG) is given, restrict to those, dropping tiny airfields and the wrong distant
    hubs. same_country_only drops cross-border airports (the interim border-penalty rule, 29 June:
    a foreign airport is included only via an explicit border penalty, not yet calibrated).
    `restrict` (a set of codes) pins the competitor set, e.g. to the airports a route's drive-time
    cache covers, so every competitor has CONSISTENT road times (mixing real cached times for some
    airports with great-circle estimates for others biases the nearest-airport allocation).

    max_water_gap_km (18 Jul 2026): the radius is a straight line, so it drove across the sea -
    Belfast pulled Glasgow, Prestwick, Edinburgh and the Hebrides (water gaps 48-114 km), STT
    pulled Puerto Rico, IBZ the Spanish mainland. A candidate whose line to the origin crosses
    more than this much contiguous open water is not road-reachable and is dropped. This is the
    SAME threshold and module as the locale-level check in catchment.py, so the two layers finally
    agree: previously the locale check correctly refused to allocate a Belfast locale to Glasgow,
    but Scottish locales inside the straight-line radius stayed in the denominator and took 42% of
    the "Belfast catchment", understating BHD's access share by ~1.7x. Filtering here also fixes
    the locale layer for free: run_catchment skips any locale left with no reachable airport.

    This is SURFACE competition (a drive-based choice model and the 'where does my catchment
    depart from' Sabre queries). Air substitution - a Glasgow passenger flying via Dublin, or
    Caribbean inter-island feed - is connecting traffic and belongs to the feed layer, not here.

    Set None to disable. The check also FAILS OPEN if global-land-mask is missing or
    AVIA_WATER_CHECK=0, which reproduces the pre-fix behaviour exactly (needed to compare against
    baselines such as bt_v1_6yr.csv that were generated before this landed)."""
    ap = _airports()
    reach = None
    if max_water_gap_km is not None:
        try:
            import water_check
            reach = water_check.road_reachable
        except Exception:
            reach = None                      # fail open: behave exactly as before
    out = []
    for r in ap.values():
        if not r["iata"] or r["lat"] is None:
            continue
        if restrict is not None and r["iata"] not in restrict:
            continue
        if served is not None and r["iata"] not in served:
            continue
        if same_country_only and r["country"] != origin_rec["country"]:
            continue
        if gc_km(origin_rec["lat"], origin_rec["lon"], r["lat"], r["lon"]) <= radius_km:
            if (reach is not None and r["iata"] != origin_rec["iata"]
                    and origin_rec["lat"] is not None
                    and not reach(origin_rec["lat"], origin_rec["lon"],
                                  r["lat"], r["lon"], max_water_gap_km)):
                continue                      # across open water: not road-reachable
            out.append(r)
    if origin_rec["iata"] not in {r["iata"] for r in out}:
        out.append(origin_rec)
    return out


def _cache_airport_codes(path):
    """Airport codes a drive-time cache covers (keys look like 'lat,lon|CODE'). These are the
    route's defined competitors, all with real road times - the consistent competitor set."""
    import json
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return {k.split("|")[1] for k in d if "|" in k}
    except Exception:
        return None


def block_min(distance_nm):
    return 20.0 + distance_nm / 7.0


def _load_index(served_index):
    if served_index is None or isinstance(served_index, dict):
        return served_index
    return OAS.load_index(served_index)


def assess(origin, dest, *, served_index=None, dump=DUMP, sabre_db=None, observed_cache=None,
           drive_cache=None, qsi_db=None, qsi_week=None, qsi_mct=None, aircraft="A21X", freq=7,
           capture=None, radius_km=220.0, econ_share=0.80, plan_lf=0.85, econ_fare=None,
           bus_fare=1400.0, fuel_price=None, propensity=None, exclude=None, same_country_only=True,
           economics=True, poo_country=None, year=None, min_pop=5000.0, stimulation=1.0,
           qsi_scale=100.0):
    """Assess a city pair end to end. served_index (OAG) drives fixes 1+2; sabre_db/observed_cache
    drive fix 3; qsi_db/qsi_week drive the capture default; capture (if given) overrides it;
    drive_cache supplies real road times for a calibrated route (else great-circle)."""
    idx = _load_index(served_index)
    served = OAS.served_set(idx) if idx else None
    exclude = {e.strip().upper() for e in (exclude or [])}

    # Fix 2: origin = its single departure airport; destination = its whole METRO (the market the
    # route addresses, e.g. Milan = MXP+LIN+BGY, not just the one field the user named).
    om = GEO.resolve_metro(origin, served_index=idx, dump=dump, expand=False)
    dm = GEO.resolve_metro(dest, served_index=idx, dump=dump, expand=True)
    home = om["primary"]
    ap = _airports()
    o = ap[home]
    d = ap[dm["primary"]]
    dest_codes = dm["airports"]
    dist_nm = gc_km(o["lat"], o["lon"], d["lat"], d["lon"]) / 1.852
    bmin = round(block_min(dist_nm))

    # Fix 1: competing set = served airports in the catchment radius, weighted by OAG size.
    # When a drive cache is given, pin competitors to the airports it covers so every competitor
    # has consistent real road times (a route's cache is its analyst-defined competitor set).
    restrict = _cache_airport_codes(drive_cache) if (drive_cache and os.path.exists(drive_cache)) else None
    cands = [r for r in competing_airports(o, radius_km, served, same_country_only, restrict)
             if r["iata"] not in exclude]
    cand_codes = [r["iata"] for r in cands]
    # QSI service-quality term (the PROPER capture, replacing the primacy fudge): each airport's
    # schedule quality to the destination from OAG (its nonstops + connections, the origin
    # INCLUDING its new nonstop), mapped to a service_value that enters the catchment choice model
    # and is balanced against drive-time access. The origin's resulting allocation IS the forecast.
    svals = {}; qsi_used = False; qsi_err = None
    if qsi_db and qsi_week:
        try:
            import route_qsi as RQ
            qd = RQ.airport_qsi_to_dest(qsi_db, qsi_week, dest_codes, cand_codes,
                                        proposed_origin=home, proposed_freq=freq,
                                        proposed_block_min=bmin, mct_file=qsi_mct)
            svals = RQ.service_values_from_qsi(qd, scale=qsi_scale)
            qsi_used = True
        except Exception as e:
            qsi_err = str(e)
    airports = []
    for r in cands:
        # with real QSI the dest-specific service_value replaces the general SIZE attractiveness
        # (size was only ever a proxy for service quality); neutralise it so the choice is
        # access vs QSI. Without QSI (fallback) keep size as the attractiveness proxy.
        att = 1.0 if qsi_used else (OAS.size_m(idx, r["iata"]) if idx else 1.0)
        airports.append(C.Airport(r["iata"], lat=r["lat"], lon=r["lon"], attractiveness=att,
                                  service_value=svals.get(r["iata"], 0.0)))

    # population catchment
    locs = G.near_point(dump, o["lat"], o["lon"], radius_km, min_pop=min_pop, propensity=1.0)
    pop = sum(l.population for l in locs)

    # Fix 3: size demand by propensity (Sabre-direct -> cache -> estimate), gravity cross-check kept.
    if propensity is not None:
        psize = {"propensity": propensity, "basis": "override", "total_od": None,
                 "avg_fare": 0.0, "observed_split": {}}
    else:
        psize = PROP.size_demand(pop, dest_codes, origin_codes=cand_codes, sabre_db=sabre_db,
                                 observed_cache=observed_cache, origin_centre=(o["lat"], o["lon"]),
                                 dest_centre=(d["lat"], d["lon"]),
                                 dest_size_m=OAS.size_m(idx, dm["primary"], 40.0) if idx else 40.0,
                                 poo_country=poo_country, year=year)
    prop = psize["propensity"]
    for l in locs:
        l.propensity = prop

    # real road times for a calibrated route, else great-circle fallback
    if drive_cache and os.path.exists(drive_cache):
        try:
            from routing import load_drive_time_matrix
            load_drive_time_matrix(locs, drive_cache)
        except Exception:
            pass

    params = C.CatchmentParams(method="gencost", logit_scale=CAL["logit_scale"],
                               value_of_time_per_hr=CAL["value_of_time_per_hr"],
                               att_exponent=CAL["att_exponent"])
    res = C.run_catchment(locs, airports, params, home=home)
    natural = res.get("home_natural", 0.0)
    current = float(psize.get("observed_split", {}).get(home, 0.0) or 0.0)
    # per-airport split for the "where the catchment flies today" bars: observed where we have
    # it (Sabre/cache), else the modelled catchment allocation.
    cat_split = psize.get("observed_split") or res.get("catchment", {})
    tot_split = sum(cat_split.values()) or 1.0
    airport_share = {c: round(cat_split.get(c, 0.0) / tot_split, 4) for c in cand_codes}
    airport_names = {c: (ap[c]["city"] or c) for c in cand_codes}

    # Capture: default = OAG-QSI schedule-quality share; `capture` arg overrides it.
    # cap = the fallback leaked-recovery base rate (only used when there is no OAG store to derive
    # the QSI service quality); with a store the QSI flows through the catchment service_value above.
    if capture is not None:
        cap, cap_basis = capture, "override"
    else:
        cap, cap_basis = DEFAULT_CAPTURE, "base leaked-recovery rate (fallback)"

    # Demand model (reworked 30 June after the back-test showed the flat-capture leakage model
    # under-reads primary-airport routes ~5x). forecast = addressable catchment O&D x the origin's
    # POST-NONSTOP share x stimulation. The post-nonstop share = what the origin retains under its
    # CURRENT service (modelled gencost allocation / its natural drive-time catchment) PLUS the
    # leaked share a nonstop recovers (repat_rate = the old "capture" prior). A primary airport has
    # high retention -> captures most of its market; a secondary airport (Genoa) has low retention
    # -> recovers only a slice. `cap` is now the leaked-recovery RATE, not the whole-market share.
    # retention = the origin's GEOGRAPHIC share of its natural catchment once it has the nonstop,
    # i.e. the demand captive to it by drive-time/size (the modelled gencost allocation), NOT its
    # current suppressed carriage (a no-nonstop airport like Genoa carries far below its potential,
    # everyone drives to the hub; basing the forecast on that is what made the engine read low -
    # John, 30 June, the back-test confirms a systematic under-read). max() so an origin already
    # over-performing its geographic share keeps the higher figure.
    modelled = res.get("catchment", {}).get(home, 0.0)
    sizes = [OAS.size_m(idx, c, 0.0) for c in cand_codes] if idx else [1.0]
    primacy = (OAS.size_m(idx, home, 0.0) / max(sizes)) if (idx and max(sizes) > 0) else 1.0
    if qsi_used:
        # PROPER method: the catchment choice model has already balanced each locale's drive-time
        # access against each airport's QSI service quality (the origin including its new nonstop),
        # so the origin's allocated demand IS the captured market. No separate capture multiplier.
        each_way = modelled * stimulation
        retention = min(modelled / natural, 1.0) if natural else 0.0
        capture_effective = retention
        repat_rate = retention
        repatriated = max(modelled - current, 0.0)
        cap_basis = "qsi-catchment"
    else:
        # FALLBACK (no OAG store): primacy-scaled leaked-recovery on the geographic potential.
        retained = max(current, modelled)
        retention = min(retained / natural, 1.0) if natural else 0.0
        repat_rate = cap + (REPAT_PRIMARY - cap) * (primacy ** 2)
        capture_effective = retention + (1.0 - retention) * repat_rate
        each_way = natural * capture_effective * stimulation
        repatriated = natural * (1.0 - retention) * repat_rate
    if qsi_err:
        cap_basis = f"fallback (qsi failed: {qsi_err[:40]})"
    out = {
        "origin": {"iata": home, "city": o["city"], "country": o["country"],
                   "metro": om["airports"], "resolve_basis": om["basis"]},
        "dest": {"iata": dm["primary"], "city": d["city"], "country": d["country"],
                 "metro": dest_codes, "resolve_basis": dm["basis"]},
        "competing_airports": cand_codes,
        "airport_share": airport_share, "airport_names": airport_names,
        "catchment_population": pop,
        "propensity": prop, "propensity_basis": psize["basis"],
        "propensity_year": psize.get("year"),
        "propensity_crosscheck": psize.get("gravity_crosscheck"),
        "dest_od_total": psize.get("total_od"),
        "natural_catchment_demand": natural,
        "current_home_demand": current,
        "capture": cap, "capture_basis": cap_basis,
        "retention": round(retention, 4), "primacy": round(primacy, 4),
        "repat_rate": round(repat_rate, 4), "capture_effective": round(capture_effective, 4),
        "stimulation": stimulation, "repatriated": repatriated, "directional_demand": each_way,
        "distance_nm": round(dist_nm), "block_min_oneway": bmin,
        "fidelity": ("calibrated" if psize["basis"] in ("sabre-direct", "cache")
                     else "estimate (transferred parameters, propensity %s)" % psize["basis"]),
    }
    if economics:
        try:
            from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
            ac = AIRCRAFT[aircraft]
            e_yr = ac["econ_seats"] * freq * 52; b_yr = ac["bus_seats"] * freq * 52
            e_lf = min((each_way * econ_share) / e_yr if e_yr else 0, plan_lf)
            b_lf = min((each_way * (1 - econ_share)) / b_yr if b_yr else 0, plan_lf)
            fare = econ_fare if econ_fare is not None else max(180, round(dist_nm * 0.11))
            kw = {}
            if fuel_price is not None:
                kw["fuel_price_usd_kg"] = fuel_price
            rp = RoutePnL("New entrant", aircraft, home, dm["primary"], round(dist_nm), bmin,
                          econ_lf=e_lf, bus_lf=b_lf, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                          airline_type="LCC", aircraft_age=2, origin_charges=DEFAULT_CHARGES,
                          dest_charges=DEFAULT_CHARGES, **kw)
            y = rp.compute(); annual = AnnualRoutePnL(rp, freq, 52).compute()
            pk = "annual_profit" if "annual_profit" in annual else "profit"
            implied_e = (each_way * econ_share) / e_yr if e_yr else 0
            spilled = max(each_way - (e_lf * e_yr + b_lf * b_yr), 0.0)
            out["economics"] = {"econ_fare": fare, "econ_lf": e_lf, "bus_lf": b_lf,
                                "implied_econ_lf": implied_e, "spilled": spilled,
                                "seats": ac["econ_seats"] + ac["bus_seats"],
                                "revenue": y["gross_rev"], "fuel": y["fuel"],
                                "maintenance": y["maintenance"], "crew": y["crew"],
                                "ownership": y["ownership"] + y["insurance"],
                                "airport_nav_other": (y["landing"] + y["per_pax"] + y["handling"]
                                                      + y["nav"] + y["catering"] + y["admin"] + y["sales"]),
                                "total_cost": y["total_cost"], "profit": y["profit"],
                                "margin": y["margin"], "breakeven_lf": y["breakeven_lf"],
                                "annual_profit": annual.get(pk, 0),
                                "aircraft_required": annual.get("aircraft_required")}
            out["economics_ok"] = True
        except Exception as e:
            out["economics_ok"] = False; out["economics_error"] = str(e)
    return out
