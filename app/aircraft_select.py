#!/usr/bin/env python3
"""
Avia Solutions - aircraft selection (range-feasible, best-fit-for-profit).
==============================================================================
Two ways to set the route's aircraft:
  1. EXPLICIT - the RouteCase names an AIRCRAFT code (and optionally a cabin config).
  2. AUTO     - the model chooses the aircraft that CAN fly the route (range) and best
                fits the demand to MAXIMISE the airline's profit.

AUTO is a profit search, not a rule of thumb: for every range-feasible candidate it runs
the SAME validated route economics the rest of the model uses (aircraft_economics.RoutePnL),
fills it from the route's demand at the planned frequency (capped at the load-factor ceiling,
so an over-large gauge shows a weak load factor and an under-size gauge spills demand), and
ranks by annual profit. The winner is the gauge whose economics the demand supports best -
the closest fit by construction, because too small spills revenue and too big flies empty.

When an airline is named, the candidate set is restricted to its plausible fleet (FLEET_BY_AIRLINE
or RouteCase.fleet); agnostic runs consider every in-range type. This does NOT change any
forecast number; it sets the equipment the economics and the deck then use.
"""
from __future__ import annotations

# Long-haul-capable fleets by airline (IATA). Extend from Egnyte fleet data as needed; an
# unknown airline falls back to all in-range types. Codes are AIRCRAFT keys in aircraft_economics.
FLEET_BY_AIRLINE = {
    "BA": ["B788", "B789", "A359", "B77W"],
    "LH": ["A359", "B789", "A333", "A339"],
    "KE": ["B789", "A359", "B77W"],
    "CI": ["A359", "B789"],
    "BR": ["B789", "B77W", "A359"],
    "CA": ["A359", "B789", "B77W"],
    "NH": ["B788", "B789", "B77W"],
}


def _seats(ac):
    return ac["econ_seats"] + ac["bus_seats"]


def candidates(distance_km, fleet=None, airline_iata=None, margin=1.03):
    """Range-feasible AIRCRAFT codes. Order of preference for the candidate set:
    explicit fleet -> airline fleet -> all in-range. margin keeps a small range cushion."""
    from aircraft_economics import AIRCRAFT
    pool = fleet or (FLEET_BY_AIRLINE.get((airline_iata or "").upper()) if airline_iata else None) or list(AIRCRAFT)
    inrange = [c for c in pool if c in AIRCRAFT and AIRCRAFT[c]["range_km"] >= distance_km * margin]
    # SECTOR REALISM: a widebody has no commercial place on a short/medium sector a narrowbody can fly, however
    # much profit a profit-max search claims from big demand (a 777 on San Jose-Boston is not a real option).
    # Only offer widebodies on genuine long-haul (>~6500 km), or when nothing narrower is range-feasible.
    if distance_km < 6500:
        narrow = [c for c in inrange if "Widebody" not in (AIRCRAFT[c].get("category") or "")]
        if narrow:
            return narrow
    return inrange


def evaluate(code, distance_nm, demand_each_way, freq, plan_lf=0.85, econ_share=0.85,
             econ_fare_ow=360.0, bus_fare_ow=1300.0, airspace=None, airline_type="FSC",
             aircraft_age=5, block_min=None, fuel_price_usd_kg=None, weeks=52.0):
    """Run the validated economics for one aircraft on this route+demand. Returns the annual
    profit and the fill detail, so the selector can rank by profit. weeks<52 = a seasonal service
    (demand and supply both over the season's operating weeks)."""
    from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
    ac = AIRCRAFT[code]
    econ_seats_yr = ac["econ_seats"] * freq * weeks
    bus_seats_yr = ac["bus_seats"] * freq * weeks
    econ_lf = (demand_each_way * econ_share) / econ_seats_yr if econ_seats_yr else 0.0
    bus_lf = (demand_each_way * (1 - econ_share)) / bus_seats_yr if bus_seats_yr else 0.0
    if ac["bus_seats"] == 0:   # single class: all demand into econ
        econ_lf = demand_each_way / econ_seats_yr if econ_seats_yr else 0.0
        bus_lf = 0.0
    plan_econ, plan_bus = min(econ_lf, plan_lf), min(bus_lf, plan_lf)
    served = plan_econ * econ_seats_yr + plan_bus * bus_seats_yr
    spilled = max(demand_each_way - served, 0.0)
    bm = block_min if block_min is not None else _block_min_for(distance_nm)
    fuel_kw = {"fuel_price_usd_kg": fuel_price_usd_kg} if fuel_price_usd_kg is not None else {}
    _chg = dict(landing_per_turn=2000.0, pax_charge_per_pax=20.0,
                recovery_per_pax=0.0, ground_handling_per_turn=1500.0)
    rp = RoutePnL("New entrant", code, "ORG", "DST", distance_nm, bm,
                  econ_lf=plan_econ, bus_lf=plan_bus, econ_fare_ow=econ_fare_ow, bus_fare_ow=bus_fare_ow,
                  airspace=dict(airspace or {}), airline_type=airline_type, aircraft_age=aircraft_age,
                  origin_charges=_chg, dest_charges=_chg, **fuel_kw)
    y = rp.compute()
    annual = AnnualRoutePnL(rp, freq, weeks).compute()
    ann_profit = annual.get("annual_profit", annual.get("profit", 0.0))
    return {"aircraft": code, "seats": _seats(ac), "range_km": ac["range_km"], "category": ac["category"],
            "econ_lf": plan_econ, "bus_lf": plan_bus, "total_lf": y.get("load_factor"),
            "served_each_way": round(served), "spilled_each_way": round(spilled),
            "margin": y.get("margin"), "annual_profit": round(ann_profit),
            "breakeven_lf": y.get("breakeven_lf")}


def _block_min_for(distance_nm):
    # cruise ~460 kt + 35 min ground manoeuvre; one-way block minutes from sector nm
    return round(distance_nm / 460.0 * 60 + 35)


def select_aircraft(distance_nm, demand_each_way, freq, plan_lf=0.85, econ_share=0.85,
                    econ_fare_ow=360.0, bus_fare_ow=1300.0, airspace=None, airline_type="FSC",
                    aircraft_age=5, block_min=None, fuel_price_usd_kg=None,
                    fleet=None, airline_iata=None, weeks=52.0):
    """Pick the range-feasible aircraft that maximises annual profit on this route+demand.
    Returns (best_code, ranked_list). Tie-break (within 2% profit): smaller spill, then gauge
    closest to demand. Raises if nothing in the pool can fly the range."""
    distance_km = distance_nm * 1.852
    pool = candidates(distance_km, fleet=fleet, airline_iata=airline_iata)
    if not pool:
        raise ValueError(f"no aircraft in the pool can fly {distance_km:,.0f} km "
                         f"(airline={airline_iata}, fleet={fleet})")
    rows = [evaluate(c, distance_nm, demand_each_way, freq, plan_lf, econ_share, econ_fare_ow,
                     bus_fare_ow, airspace, airline_type, aircraft_age, block_min, fuel_price_usd_kg,
                     weeks=weeks)
            for c in pool]
    target_seats = demand_each_way / (freq * weeks * plan_lf) if (freq and plan_lf) else 0
    rows.sort(key=lambda r: (-r["annual_profit"], r["spilled_each_way"], abs(r["seats"] - target_seats)))
    return rows[0]["aircraft"], rows


def resolve_aircraft(case, demand_each_way, freq=None, plan_lf=None):
    """High-level: honour an explicit RouteCase.aircraft, or AUTO-select. Returns (code, ranked_or_None)."""
    ac = (case.aircraft or "").upper()
    if ac and ac != "AUTO":
        return case.aircraft, None
    f = freq or case.frequency
    lf = plan_lf if plan_lf is not None else case.plan_lf
    code, ranked = select_aircraft(
        case.sector_nm, demand_each_way, f, plan_lf=lf, econ_share=case.econ_share,
        econ_fare_ow=case.econ_fare_ow or 360.0, bus_fare_ow=case.bus_fare_ow,
        airspace=case.airspace, airline_type=case.airline_type, aircraft_age=case.aircraft_age,
        block_min=case.block_min, fuel_price_usd_kg=case.fuel_price_usd_kg,
        fleet=case.fleet, airline_iata=case.airline_iata or None)
    return code, ranked


def gauge_annual_cost(code, distance_nm, total_lf, freq, econ_fare_ow=360.0, bus_fare_ow=1300.0,
                      airspace=None, airline_type="FSC", aircraft_age=5, block_min=None, fuel_price_usd_kg=None):
    """Annual route cost for a gauge at a given load factor (the validated economics). Cost is
    aircraft-level, so it is shared across that gauge's LOPA variants; the variant choice is a
    revenue question, the gauge choice nets revenue against this cost."""
    from aircraft_economics import RoutePnL
    bm = block_min if block_min is not None else _block_min_for(distance_nm)
    fuel_kw = {"fuel_price_usd_kg": fuel_price_usd_kg} if fuel_price_usd_kg is not None else {}
    rp = RoutePnL("New entrant", code, "ORG", "DST", distance_nm, bm, econ_lf=total_lf, bus_lf=total_lf,
                  econ_fare_ow=econ_fare_ow, bus_fare_ow=bus_fare_ow, airspace=dict(airspace or {}),
                  airline_type=airline_type, aircraft_age=aircraft_age, **fuel_kw)
    y = rp.compute()
    return y["total_cost"] * freq * 52 * 2


def select_aircraft_and_lopa(distance_nm, total_demand_each_way, freq, cabin_mix, econ_fare_ow=360.0,
                             bus_fare_ow=1300.0, stim=1.0, plan_lf=0.85, airspace=None, airline_type="FSC",
                             aircraft_age=5, block_min=None, fuel_price_usd_kg=None, fleet=None,
                             airline_iata=None, store=None):
    """Pick the gauge AND the LOPA that maximise annual profit on the route's cabin demand.
    cabin_mix = {first,business,premium_coach,coach} shares - route-current from Sabre, or a default
    from econ_share. Revenue is the cabin model (premium seats earn premium fares only where the
    demand fills them); cost is the gauge economics. Returns ((aircraft, variant), ranked)."""
    from cabin_lopa_select import cabin_demand, fare_ladder, choose_lopa
    distance_km = distance_nm * 1.852
    pool = candidates(distance_km, fleet=fleet, airline_iata=airline_iata)
    if not pool:
        raise ValueError(f"no aircraft can fly {distance_km:,.0f} km")
    dem = cabin_demand(total_demand_each_way, cabin_mix, stim)
    fares = fare_ladder(econ_fare_ow)
    rows = []
    for code in pool:
        best, _ = choose_lopa(code, airline_iata, dem, fares, freq, store=store)
        if not best:
            continue
        cost = gauge_annual_cost(code, distance_nm, min(best["total_lf"], plan_lf), freq, econ_fare_ow,
                                 bus_fare_ow, airspace, airline_type, aircraft_age, block_min, fuel_price_usd_kg)
        rows.append({"aircraft": code, "variant": best["variant"], "seats": best["seats"],
                     "total_lf": best["total_lf"], "revenue": best["revenue_two_way"],
                     "cost": round(cost), "annual_profit": round(best["revenue_two_way"] - cost),
                     "lopa": best["lopa"]})
    rows.sort(key=lambda r: -r["annual_profit"])
    return ((rows[0]["aircraft"], rows[0]["variant"]) if rows else (None, None)), rows


def default_cabin_mix(econ_share):
    """A 4-class mix defaulted from the model's economy share when a Sabre cabin split is not to
    hand: premium = (1 - econ_share), split first/business/premium-economy ~ 0.1/0.6/0.3 of premium."""
    prem = max(1 - econ_share, 0.0)
    return {"first": round(prem * 0.10, 4), "business": round(prem * 0.60, 4),
            "premium_coach": round(prem * 0.30, 4), "coach": round(econ_share, 4)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Select the best-fit-for-profit aircraft for a route.")
    ap.add_argument("--nm", type=float, required=True, help="sector distance, nm")
    ap.add_argument("--demand", type=float, required=True, help="each-way annual demand")
    ap.add_argument("--freq", type=int, default=7)
    ap.add_argument("--plan-lf", type=float, default=0.85)
    ap.add_argument("--econ-share", type=float, default=0.85)
    ap.add_argument("--econ-fare", type=float, default=360.0)
    ap.add_argument("--bus-fare", type=float, default=1300.0)
    ap.add_argument("--airline", default=None, help="IATA, restricts to its fleet")
    ap.add_argument("--fuel-price", type=float, default=None)
    a = ap.parse_args()
    best, ranked = select_aircraft(a.nm, a.demand, a.freq, plan_lf=a.plan_lf, econ_share=a.econ_share,
                                   econ_fare_ow=a.econ_fare, bus_fare_ow=a.bus_fare,
                                   airline_iata=a.airline, fuel_price_usd_kg=a.fuel_price)
    print(f"BEST: {best}\n")
    print(f"{'ac':6}{'seats':>6}{'rng_km':>8}{'tot_lf':>8}{'spill':>9}{'margin':>8}{'ann_profit':>13}")
    for r in ranked:
        print(f"{r['aircraft']:6}{r['seats']:>6}{r['range_km']:>8}{(r['total_lf'] or 0):>8.0%}"
              f"{r['spilled_each_way']:>9,}{(r['margin'] or 0):>8.1%}{r['annual_profit']:>13,}")
