#!/usr/bin/env python3
"""
Avia Solutions - assess any route: catchment -> demand -> load factor -> route P&L.
===================================================================================
The general version of genoa_nyc.py. The whole chain on one route, driven by a RouteCase
rather than hard-coded Genoa constants, so it runs ANY origin-destination by swapping --case:

  1. load the calibrated catchment params + real road times for the case,
  2. read the OBSERVED destination O&D split + fare (Sabre live, or an offline cache),
  3. calibrate each airport's destination service constant to that observed split
     (baseline now reproduces reality),
  4. take the DEFENSIBLE bounded repatriation (home's own leaked catchment x a capture rate),
  5. turn repatriated pax into an implied load factor for the case aircraft and frequency,
  6. run the route + annual P&L (aircraft_economics).

RUN (offline, from a cached observed split):
    py -3.12 assess.py genoa_nyc cities5000.txt
RUN (live Sabre):
    py -3.12 assess.py genoa_nyc cities5000.txt --sabre "C:\\Avia\\sabre.duckdb"
Every case default is overridable: --capture --freq --econ-share --bus-fare --fare-basis
--plan-lf --econ-fare --incentive --ppt.
"""
import argparse, json, os, sys


def _load_observed(case, base_dir, args, here, codes):
    """Return (observed_split, total, avg_fare). Prefer a live Sabre query when --sabre is given
    and the store exists; otherwise read the case's offline observed cache. This is the
    offline-must-work path: a laptop / World Routes run needs no Sabre connection."""
    sabre = args.sabre
    if sabre and os.path.exists(sabre):
        import sabre_catchment as S
        if args.year is None:
            print("  WARNING: live Sabre pull with no --year sums ALL years (mixes directional "
                  "POO and non-directional ND data). Pass --year (e.g. --year 2024) for a clean pull.")
        observed, total, avg_fare = S.destination_market_split(
            sabre, codes, case.dest_airports, year=args.year)
        # refresh the offline cache so later runs work without Sabre
        cache_path = args.observed_cache or case.resolve("observed_cache", base_dir) \
            or os.path.join(base_dir, f"{case.case_id}_observed.json")
        try:
            json.dump({"dest_name": case.dest_name, "dest_airports": case.dest_airports,
                       "observed_split": observed, "total": total, "avg_fare": avg_fare,
                       "source": "Sabre ODPOO via destination_market_split"},
                      open(cache_path, "w"), indent=2)
            print(f"(refreshed observed cache: {os.path.basename(cache_path)})")
        except OSError:
            pass
        return observed, total, avg_fare
    # offline
    cache_path = args.observed_cache or case.resolve_existing("observed_cache", base_dir, [here])
    if not cache_path or not os.path.exists(cache_path):
        sys.exit(f"ERROR: no Sabre store and no observed cache found. Pass --sabre <db> to query "
                 f"live, or provide an observed cache (case.observed_cache / --observed-cache).")
    obs = json.load(open(cache_path))
    observed = {c: float(obs["observed_split"].get(c, 0.0)) for c in codes}
    total = float(obs.get("total") or sum(observed.values()))
    avg_fare = float(obs.get("avg_fare") or 0.0)
    print(f"(observed split from offline cache: {os.path.basename(cache_path)})")
    return observed, total, avg_fare


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G, routing as R, route_demand as RD
    from catchment import Airport, CatchmentParams
    from route_case import RouteCase

    ap = argparse.ArgumentParser(description="Assess any route case end to end.")
    ap.add_argument("case", help="route case id (e.g. genoa_nyc) or path to a case JSON")
    ap.add_argument("geonames_txt")
    ap.add_argument("--sabre", default=None, help="sabre.duckdb for a live observed split (else offline cache)")
    ap.add_argument("--observed-cache", default=None, help="override the offline observed-split JSON")
    ap.add_argument("--cache", default=None, help="override the drive-time cache path")
    ap.add_argument("--params", default=None, help="override the fitted-params JSON path")
    ap.add_argument("--radius-km", type=float, default=None)
    ap.add_argument("--min-pop", type=float, default=None)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--capture", type=float, default=None)
    ap.add_argument("--freq", type=int, default=None)
    ap.add_argument("--econ-share", type=float, default=None)
    ap.add_argument("--econ-fare", type=float, default=None)
    ap.add_argument("--bus-fare", type=float, default=None)
    ap.add_argument("--fuel-price", type=float, default=None, help="planning jet fuel $/kg (else case/0.68)")
    ap.add_argument("--market", type=float, default=None, help="demand multiplier (1.0 neutral; 0.86 = -14% soft market)")
    ap.add_argument("--fare-basis", choices=["rt", "ow"], default=None)
    ap.add_argument("--plan-lf", type=float, default=None)
    ap.add_argument("--incentive", action="store_true")
    ap.add_argument("--ppt", action="store_true", help="render the forecast + P&L deck")
    ap.add_argument("--deck-out", default=None)
    ap.add_argument("--out", default=None, help="output case JSON (default <case_id>_case.json)")
    a = ap.parse_args()

    case, base_dir = RouteCase.load_with_dir(a.case)
    # CLI overrides win over case defaults
    capture = a.capture if a.capture is not None else case.capture
    freq = a.freq if a.freq is not None else case.frequency
    econ_share = a.econ_share if a.econ_share is not None else case.econ_share
    bus_fare = a.bus_fare if a.bus_fare is not None else case.bus_fare_ow
    fare_basis = a.fare_basis or case.fare_basis
    plan_lf = a.plan_lf if a.plan_lf is not None else case.plan_lf
    fuel_price = a.fuel_price if a.fuel_price is not None else case.fuel_price_usd_kg
    market_factor = a.market if a.market is not None else (case.market_factor if case.market_factor is not None else 1.0)
    radius_km = a.radius_km if a.radius_km is not None else case.radius_km
    min_pop = a.min_pop if a.min_pop is not None else case.min_pop

    cache = a.cache or case.resolve_existing("drive_cache", base_dir, [here], f"{case.case_id}_drive.json")
    params_path = a.params or case.resolve_existing("params_file", base_dir, [here], f"{case.case_id}_catchment_params.json")
    if not os.path.exists(params_path):
        sys.exit(f"ERROR: fitted params not found: {params_path}. Run calibrate_catchment.py first.")
    fit = json.load(open(params_path))

    # 1. locales + real road times
    locs = G.near_point(a.geonames_txt, case.centre_lat, case.centre_lon, radius_km,
                        countries=case.countries, min_pop=min_pop, propensity=1.0)
    R.load_drive_time_matrix(locs, cache)
    pop = sum(l.population for l in locs)
    airports = case.to_airport_objs("catchment")               # neutral attractiveness
    codes = case.airport_codes("catchment")
    params = CatchmentParams(method="gencost", logit_scale=fit['logit_scale'],
                             value_of_time_per_hr=fit['value_of_time_per_hr'])

    # 2. observed destination O&D split + fare (Sabre live, or offline cache)
    observed, total_dest, avg_fare = _load_observed(case, base_dir, a, here, codes)
    propensity = total_dest / pop if pop else 0.0
    print(f"catchment pop {pop:,.0f}; {case.dest_name} O&D {total_dest:,.0f}; "
          f"propensity {propensity:.4f}; avg fare ${avg_fare:,.0f}")

    # 3. calibrate the destination service constants to the observed split
    sv, mod = RD.calibrate_service_values(locs, airports, params, propensity, observed, home=None)
    base = RD.market_allocation(locs, airports, params, propensity, sv, home=case.home)
    print("\nbaseline (calibrated) vs observed - leakage structure:")
    for c in sorted(observed, key=lambda k: -observed[k]):
        share = observed[c] / total_dest if total_dest else 0.0
        print(f"   {c}  model {mod[c]:5.1%}  obs {share:5.1%}")

    # 4. DEFENSIBLE bounded repatriation
    natural = base['home_natural']
    if case.natural_override is not None:
        print(f"  natural override: catchment model gave {natural:,.0f}; using residence-based "
              f"{case.natural_override:,.0f} (POS-scoped, not departure-airport)")
        natural = case.natural_override
    current = observed.get(case.home, 0.0)
    b = RD.bounded_repatriation(natural, current, capture=capture)
    print(f"\n{case.home} {case.dest_name} catchment (natural) {natural:,.0f}; carries today "
          f"{current:,.0f}; leaked pool {b['leaked_pool']:,.0f}")
    print(f"DEFENSIBLE repatriation @ capture {capture:.0%}: {b['repatriated']:,.0f} pax/yr (directional)")
    print(f"{case.home}-{case.dest_name} directional demand with a nonstop: {b['home_total']:,.0f} pax/yr each way")

    # 5. implied load factor for the case aircraft at the chosen frequency
    from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL, Incentive, DISCLAIMER_SHORT
    ac = AIRCRAFT[case.aircraft]
    each_way = b['home_total'] * market_factor          # demand shock / uplift (1.0 = neutral)
    if market_factor != 1.0:
        print(f"  market adjustment x{market_factor:.2f}: directional demand -> {each_way:,.0f}/yr each way")
    econ_seats_yr = ac['econ_seats'] * freq * 52
    bus_seats_yr = ac['bus_seats'] * freq * 52
    econ_lf = (each_way * econ_share) / econ_seats_yr if econ_seats_yr else 0
    bus_lf = (each_way * (1 - econ_share)) / bus_seats_yr if bus_seats_yr else 0
    plan_econ, plan_bus = min(econ_lf, plan_lf), min(bus_lf, plan_lf)
    served = (plan_econ * econ_seats_yr + plan_bus * bus_seats_yr)
    spilled = max(each_way - served, 0.0)
    print(f"\n{case.aircraft} at {freq}x/week: demand-implied econ LF {econ_lf:.0%}, bus LF {bus_lf:.0%}")
    print(f"  planned at LF cap {plan_lf:.0%}: econ {plan_econ:.0%}, bus {plan_bus:.0%}; "
          f"spilled demand {spilled:,.0f}/yr" + (" (raise frequency or upsize)" if spilled > 0 else ""))
    econ_lf, bus_lf = plan_econ, plan_bus

    # Sabre avg_total_fare is round-trip on these records -> halve to one-way by default
    one_way = (avg_fare / 2.0) if fare_basis == "rt" else avg_fare
    if a.econ_fare is not None:
        fare = a.econ_fare                      # CLI override wins
    elif case.econ_fare_ow is not None:
        fare = case.econ_fare_ow                # pinned entrant yield from the case
    else:
        fare = round(one_way or 360)            # else derive from the Sabre average
    fuel_kw = {"fuel_price_usd_kg": fuel_price} if fuel_price is not None else {}
    inc = Incentive(home=case.home, waiver_pct=case.incentive_waiver_pct,
                    support_per_turn=case.incentive_support_per_turn) if a.incentive else None
    rp = RoutePnL("New entrant", case.aircraft, case.home, case.primary_dest,
                  case.sector_nm, case.block_min,
                  econ_lf=econ_lf, bus_lf=bus_lf, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                  airspace=dict(case.airspace),
                  airline_type=case.airline_type, aircraft_age=case.aircraft_age, incentive=inc, **fuel_kw)
    y = rp.compute()
    annual = AnnualRoutePnL(rp, freq, 52).compute()
    print(f"\nROUTE P&L (per turn, econ fare ${fare}):  profit {y['profit']:,.0f}  "
          f"margin {y['margin']:.1%}  breakeven LF {y['breakeven_lf']:.0%}")
    if inc:
        print(f"  with {case.home} incentive: profit {y['profit_with_incentive']:,.0f}  "
              f"margin {y['margin_with_incentive']:.1%}")
    pk = 'annual_profit' if 'annual_profit' in annual else 'profit'
    print(f"ANNUAL ({freq}x/week): profit {annual.get(pk, 0):,.0f}")

    if a.ppt:
        from route_deck import build_deck
        ann_profit = annual.get(pk, 0)
        rp2 = RoutePnL("New entrant", case.aircraft, case.home, case.primary_dest,
                       case.sector_nm, case.block_min, econ_lf=econ_lf, bus_lf=bus_lf,
                       econ_fare_ow=fare, bus_fare_ow=case.premium_fare_ow,
                       airspace=dict(case.airspace), airline_type=case.airline_type,
                       aircraft_age=case.aircraft_age, incentive=inc, **fuel_kw)
        y2 = rp2.compute(); annual2 = AnnualRoutePnL(rp2, freq, 52).compute()
        names = case.names()
        home_name = names.get(case.home, case.home)
        split = sorted(((names.get(c, c), observed[c] / total_dest) for c in observed),
                       key=lambda kv: -kv[1])
        forecast = dict(
            pop=f"{pop/1e6:.1f}m", nyc_od=f"{total_dest:,.0f}",
            leaked=f"{b['leaked_pool']:,.0f}", repatriated=f"{b['repatriated']:,.0f}",
            home_label=home_name,
            subtitle=f"{home_name}'s {case.dest_name} travellers leak to the incumbent gateway today; "
                     f"a {home_name} nonstop repatriates its own catchment",
            split=split,
            fit_lines=[f"{home_name}'s {case.dest_name} catchment: {natural:,.0f} / year",
                       f"Carried by {home_name} today: {current:,.0f}",
                       f"Leaking to competitors: {b['leaked_pool']:,.0f}",
                       f"Repatriated at {capture:.0%} capture: {b['repatriated']:,.0f} each way",
                       f"Directional demand with a nonstop: {b['home_total']:,.0f}",
                       f"Fills a {freq}x/week {case.aircraft} at {plan_lf:.0%} load (~{spilled:,.0f} spilled)"])
        meta = dict(
            title=case.title or f"{home_name} - {case.dest_name}",
            subtitle=f"{case.aircraft} route assessment: catchment, demand and economics",
            origin=case.home, origin_name=home_name, dest=case.dest_name, aircraft=case.aircraft,
            sector_nm=case.sector_nm, fare_ow=fare, plan_lf=plan_lf, frequency=freq,
            annual_profit=ann_profit, maint_basis=y['maint_basis'], own_basis=y['own_basis'],
            pnl_subtitle=f"{freq}x/week, one-way economy fare ${fare}, planned load factor {plan_lf:.0%}",
            disclaimer=DISCLAIMER_SHORT,
            sensitivity=[("Realistic premium", y['margin'], ann_profit),
                         ("Full business cabin", y2['margin'], annual2.get(pk, 0))])
        deck = a.deck_out or os.path.join(base_dir, f"{case.case_id}_forecast_and_PnL.pptx")
        build_deck(deck, forecast, y, meta)
        print(f"deck saved: {deck}")

    out_path = a.out or os.path.join(base_dir, f"{case.case_id}_case.json")
    json.dump({"case_id": case.case_id, "population": pop, "dest_od_total": total_dest,
               "propensity": propensity, "avg_fare": avg_fare, "observed_split": observed,
               "service_constants": sv, "natural": natural, "current": current, "capture": capture,
               "repatriated": b['repatriated'], "directional_demand": each_way,
               "frequency": freq, "econ_lf": econ_lf, "bus_lf": bus_lf,
               "route_pnl": y, "annual_pnl": annual},
              open(out_path, "w"), indent=2, default=float)
    print(f"\nsaved {os.path.basename(out_path)}  |  catchment -> demand -> LF -> P&L on one route")


if __name__ == "__main__":
    main()
