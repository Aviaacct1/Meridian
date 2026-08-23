#!/usr/bin/env python3
"""
Avia Solutions - Genoa-New York: catchment -> demand -> load factor -> route P&L.
=================================================================================
The whole chain on one real route. It:
  1. loads the calibrated Genoa catchment (genoa_catchment_params.json) + real road times,
  2. calibrates each airport's NYC service constant to the OBSERVED Sabre NYC O&D split,
  3. takes the DEFENSIBLE repatriation (bounded by GOA's own catchment x a capture rate) -
     NOT the free-running logit scenario, which over-reaches into Milan,
  4. turns repatriated pax into an implied load factor for an A321XLR at a chosen frequency,
  5. runs the route + annual P&L (aircraft_economics).

RUN:
    cd "C:\\Users\\Carte\\OneDrive\\Documents\\Claude\\Projects\\Avia QSI Tool\\app"
    py -3.12 genoa_nyc.py cities5000.txt --sabre "C:\\Avia\\sabre.duckdb"
Tune: --capture 0.65  --freq 7  --econ-share 0.90  --incentive
"""
import argparse, json, math, os, sys

NYC = ["JFK", "EWR", "LGA"]
COORD = {"GOA": (44.4133, 8.8375), "MXP": (45.6306, 8.7281), "LIN": (45.4451, 9.2767),
         "BGY": (45.6739, 9.7042), "TRN": (45.2008, 7.6497), "BLQ": (44.5354, 11.2887)}
CENTRE = (44.4133, 8.8375)
# GOA-JFK sector (matches the aircraft_economics worked example)
DIST_NM, BLOCK_MIN, AIRCRAFT = 3500, 540, "A21X"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G, routing as R, sabre_catchment as S, route_demand as RD
    from catchment import Airport, CatchmentParams

    ap = argparse.ArgumentParser(description="Genoa-NYC: catchment -> demand -> P&L.")
    ap.add_argument("geonames_txt")
    ap.add_argument("--cache", default=os.path.join(here, "genoa_drive.json"))
    ap.add_argument("--params", default=os.path.join(here, "genoa_catchment_params.json"))
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--radius-km", type=float, default=220.0)
    ap.add_argument("--min-pop", type=float, default=5000.0)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--capture", type=float, default=0.65, help="share of GOA's leaked catchment a nonstop wins")
    ap.add_argument("--freq", type=int, default=7, help="flights/week each way")
    ap.add_argument("--econ-share", type=float, default=0.90, help="economy share of demand")
    ap.add_argument("--econ-fare", type=float, default=None, help="one-way economy fare (else Sabre avg)")
    ap.add_argument("--bus-fare", type=float, default=1300.0)
    ap.add_argument("--fare-basis", choices=["rt", "ow"], default="rt",
                    help="Sabre avg_total_fare basis: rt (round-trip, halved to one-way) or ow")
    ap.add_argument("--plan-lf", type=float, default=0.85, help="planning load-factor cap (not 95%)")
    ap.add_argument("--incentive", action="store_true", help="apply a GOA airport incentive package")
    ap.add_argument("--ppt", action="store_true", help="render the forecast + P&L deck (Avia house style)")
    ap.add_argument("--deck-out", default=None, help="deck output path")
    a = ap.parse_args()

    fit = json.load(open(a.params))
    locs = G.near_point(a.geonames_txt, CENTRE[0], CENTRE[1], a.radius_km,
                        countries=["IT", "FR"], min_pop=a.min_pop, propensity=1.0)
    R.load_drive_time_matrix(locs, a.cache)
    pop = sum(l.population for l in locs)
    airports = [Airport(c, lat=la, lon=lo) for c, (la, lo) in COORD.items()]
    params = CatchmentParams(method="gencost", logit_scale=fit['logit_scale'],
                             value_of_time_per_hr=fit['value_of_time_per_hr'])

    # observed NYC O&D + fare from Sabre
    observed, total_nyc, avg_fare = S.destination_market_split(a.sabre, list(COORD), NYC, year=a.year)
    propensity = total_nyc / pop if pop else 0.0
    print(f"catchment pop {pop:,.0f}; Sabre NYC O&D {total_nyc:,.0f}; propensity {propensity:.4f}; avg fare ${avg_fare:,.0f}")

    # calibrate NYC service constants to the observed split (baseline now reproduces reality)
    sv, mod = RD.calibrate_service_values(locs, airports, params, propensity, observed, home=None)
    base = RD.market_allocation(locs, airports, params, propensity, sv, home="GOA")
    print("\nbaseline (calibrated) vs observed - leakage structure:")
    for c in sorted(observed, key=lambda k: -observed[k]):
        print(f"   {c}  model {mod[c]:5.1%}  obs {observed[c]/total_nyc:5.1%}")

    # DEFENSIBLE bounded repatriation (not the over-reaching free logit)
    natural = base['home_natural']
    current = observed.get("GOA", 0.0)
    b = RD.bounded_repatriation(natural, current, capture=a.capture)
    print(f"\nGOA NYC catchment (natural) {natural:,.0f}; carries today {current:,.0f}; leaked pool {b['leaked_pool']:,.0f}")
    print(f"DEFENSIBLE repatriation @ capture {a.capture:.0%}: {b['repatriated']:,.0f} pax/yr (directional)")
    print(f"GOA-NYC directional demand with a nonstop: {b['home_total']:,.0f} pax/yr each way")

    # implied load factor for an A321XLR at the chosen frequency
    sys.path.insert(0, here)
    from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL, Incentive, DISCLAIMER_SHORT
    ac = AIRCRAFT["A21X"]
    each_way = b['home_total']
    econ_seats_yr = ac['econ_seats'] * a.freq * 52
    bus_seats_yr = ac['bus_seats'] * a.freq * 52
    econ_lf = (each_way * a.econ_share) / econ_seats_yr if econ_seats_yr else 0
    bus_lf = (each_way * (1 - a.econ_share)) / bus_seats_yr if bus_seats_yr else 0
    # cap at a realistic PLANNING load factor (no route runs 95% year-round); demand above the
    # cap is spilled (or justifies more frequency / a larger gauge), it does not lift revenue.
    plan_econ, plan_bus = min(econ_lf, a.plan_lf), min(bus_lf, a.plan_lf)
    served = (plan_econ * econ_seats_yr + plan_bus * bus_seats_yr)
    spilled = max(each_way - served, 0.0)
    print(f"\nA321XLR at {a.freq}x/week: demand-implied econ LF {econ_lf:.0%}, bus LF {bus_lf:.0%}")
    print(f"  planned at LF cap {a.plan_lf:.0%}: econ {plan_econ:.0%}, bus {plan_bus:.0%}; "
          f"spilled demand {spilled:,.0f}/yr" + (" (raise frequency or upsize)" if spilled > 0 else ""))
    econ_lf, bus_lf = plan_econ, plan_bus

    # Sabre avg_total_fare is round-trip on these records -> halve to a one-way fare by default
    one_way = (avg_fare / 2.0) if a.fare_basis == "rt" else avg_fare
    fare = a.econ_fare if a.econ_fare is not None else round(one_way or 360)
    inc = Incentive(home="GOA", waiver_pct=0.50, support_per_turn=1500) if a.incentive else None
    rp = RoutePnL("New entrant", "A21X", "GOA", "JFK", DIST_NM, BLOCK_MIN,
                  econ_lf=econ_lf, bus_lf=bus_lf, econ_fare_ow=fare, bus_fare_ow=a.bus_fare,
                  airspace={"Italy": 0.10, "France": 0.05, "US": 0.05},
                  airline_type="LCC", aircraft_age=2, incentive=inc)
    y = rp.compute()
    annual = AnnualRoutePnL(rp, a.freq, 52).compute()
    print(f"\nROUTE P&L (per turn, econ fare ${fare}):  profit {y['profit']:,.0f}  margin {y['margin']:.1%}  breakeven LF {y['breakeven_lf']:.0%}")
    if inc:
        print(f"  with GOA incentive: profit {y['profit_with_incentive']:,.0f}  margin {y['margin_with_incentive']:.1%}")
    pk = 'annual_profit' if 'annual_profit' in annual else 'profit'
    print(f"ANNUAL ({a.freq}x/week): profit {annual.get(pk, 0):,.0f}")

    if a.ppt:
        from route_deck import build_deck
        ann_profit = annual.get(pk, 0)
        # full-business-cabin sensitivity variant (same load, premium fare $1,300)
        rp2 = RoutePnL("New entrant", "A21X", "GOA", "JFK", DIST_NM, BLOCK_MIN,
                       econ_lf=econ_lf, bus_lf=bus_lf, econ_fare_ow=fare, bus_fare_ow=1300,
                       airspace={"Italy": 0.10, "France": 0.05, "US": 0.05},
                       airline_type="LCC", aircraft_age=2, incentive=inc)
        y2 = rp2.compute(); annual2 = AnnualRoutePnL(rp2, a.freq, 52).compute()
        NAMES = {"GOA": "Genoa", "MXP": "Milan MXP", "LIN": "Milan Linate",
                 "BGY": "Bergamo", "TRN": "Turin", "BLQ": "Bologna"}
        split = sorted(((NAMES.get(c, c), observed[c] / total_nyc) for c in observed), key=lambda kv: -kv[1])
        # THE STALE SHAPE (23 August 2026): build_deck()'s forecast-slide stats (route_deck.py
        # line ~107-114) read forecast['market'], ['captured'], ['feed'] and ['total'] directly,
        # with no .get() fallback - a KeyError this script has thrown since build_deck moved onto
        # that shape (this module's own docstring still names the OLD dict shape, pop/nyc_od/
        # leaked/repatriated/directional, which predates the change). Genoa-NYC has no airline
        # connections modelled (it is a repatriation case, not the full engine), so feed is
        # genuinely zero here and captured/total are both the same directional figure.
        forecast = dict(
            pop=f"{pop/1e6:.1f}m", nyc_od=f"{total_nyc:,.0f}",
            leaked=f"{b['leaked_pool']:,.0f}", repatriated=f"{b['repatriated']:,.0f}",
            market=f"{natural:,.0f}", captured=f"{each_way:,.0f}",
            feed="0", total=f"{each_way:,.0f}",
            home_label="Genoa",
            subtitle="Genoa's New York travellers leak to Milan today; a Genoa nonstop repatriates its own catchment",
            split=split,
            fit_lines=[f"Genoa's New York catchment: {natural:,.0f} / year",
                       f"Carried by Genoa today: {current:,.0f}",
                       f"Leaking to Milan: {b['leaked_pool']:,.0f}",
                       f"Repatriated at {a.capture:.0%} capture: {b['repatriated']:,.0f} each way",
                       f"Directional demand with a nonstop: {b['home_total']:,.0f}",
                       f"Fills a {a.freq}x/week A321XLR at {a.plan_lf:.0%} load (~{spilled:,.0f} spilled)"])
        meta = dict(
            title="Genoa - New York", subtitle="A321XLR route assessment: catchment, demand and economics",
            origin="GOA", origin_name="Genoa", dest="New York", aircraft="A321XLR", sector_nm=DIST_NM,
            fare_ow=fare, plan_lf=a.plan_lf, frequency=a.freq, annual_profit=ann_profit,
            maint_basis=y['maint_basis'], own_basis=y['own_basis'],
            pnl_subtitle=f"{a.freq}x/week, one-way economy fare ${fare}, planned load factor {a.plan_lf:.0%}",
            disclaimer=DISCLAIMER_SHORT,
            sensitivity=[("Realistic premium", y['margin'], ann_profit),
                         ("Full business cabin", y2['margin'], annual2.get(pk, 0))])
        deck = a.deck_out or os.path.join(here, "Genoa_NYC_forecast_and_PnL.pptx")
        build_deck(deck, forecast, y, meta)
        print(f"deck saved: {deck}")

    json.dump({"population": pop, "nyc_od_total": total_nyc, "propensity": propensity,
               "avg_fare": avg_fare, "observed_split": observed, "service_constants": sv,
               "natural": natural, "current": current, "capture": a.capture,
               "repatriated": b['repatriated'], "directional_demand": each_way,
               "frequency": a.freq, "econ_lf": econ_lf, "bus_lf": bus_lf,
               "route_pnl": y, "annual_pnl": annual}, open(os.path.join(here, "genoa_nyc_case.json"), "w"), indent=2, default=float)
    print(f"\nsaved genoa_nyc_case.json  |  the whole chain: catchment -> demand -> LF -> P&L on one route")


if __name__ == "__main__":
    main()
