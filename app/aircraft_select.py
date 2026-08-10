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

# SUPERSEDED 10 August 2026 by the OAG measurement in capacity_frame.types_for, and kept only as the
# last fallback for a carrier the schedule store cannot see. It is the SECOND hand-maintained fleet
# table in this codebase: airline_fleets.FLEETS is the other, the two disagreed with each other and
# both disagreed with OAG. CI read A359 and B789 here and A321, A359 and B789 there, while OAG 2025
# on 10,000 km sectors shows China Airlines flying the A350-900 and the 777-300ER and no 787 at all.
# Do not extend this table. Fix the mapping in capacity_frame or the entry in aircraft_economics.
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
    explicit fleet -> what the carrier is OBSERVED to fly at this sector length -> the hand tables ->
    all in-range. margin keeps a small range cushion.

    The observed step was added on 10 August 2026. Before it, this function read a hand table that
    offered China Airlines a 787-9 on a 10,440 km sector, which China Airlines does not fly at that
    length, and withheld the 777-300ER, which it does. Showing an airline the wrong aeroplane is the
    fastest way to lose a room."""
    from aircraft_economics import AIRCRAFT
    pool = fleet
    if pool is None and airline_iata:
        try:
            import airline_fleets as AFL           # OAG first, its own table second
            pool = AFL.fleet_for(airline_iata, list(AIRCRAFT), distance_km)[0] or None
        except Exception:
            pool = None
        if pool is None:
            pool = FLEET_BY_AIRLINE.get((airline_iata or "").upper())
    pool = pool or list(AIRCRAFT)
    inrange = [c for c in pool if c in AIRCRAFT and AIRCRAFT[c]["range_km"] >= distance_km * margin]
    # SECTOR REALISM: a widebody has no commercial place on a short/medium sector a narrowbody can fly, however
    # much profit a profit-max search claims from big demand (a 777 on San Jose-Boston is not a real option).
    # Only offer widebodies on genuine long-haul (>~6500 km), or when nothing narrower is range-feasible.
    if distance_km < 6500:
        narrow = [c for c in inrange if "Widebody" not in (AIRCRAFT[c].get("category") or "")]
        if narrow:
            return narrow
    return inrange


def evaluate(code, distance_nm, demand_each_way, freq, plan_lf=0.875, econ_share=0.85,
             econ_fare_ow=360.0, bus_fare_ow=1300.0, airspace=None, airline_type="FSC",
             aircraft_age=5, block_min=None, fuel_price_usd_kg=None, weeks=52.0,
             seats_override=None):
    """Run the validated economics for one aircraft on this route+demand. Returns the annual
    profit and the fill detail, so the selector can rank by profit. weeks<52 = a seasonal service
    (demand and supply both over the season's operating weeks).

    seats_override is (total, premium) as the OPERATING CARRIER configures this type, measured from
    OAG. It sets the fill, which is what the selection turns on, and the cost side stays on the
    generic type because fuel burn and maintenance are properties of the aeroplane rather than of
    its cabin. Left as None the generic configuration is used and nothing changes."""
    from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
    ac = AIRCRAFT[code]
    _econ, _bus = ac["econ_seats"], ac["bus_seats"]
    if seats_override:
        _tot, _prem = int(seats_override[0]), int(seats_override[1] or 0)
        _bus = min(_prem, _tot)
        _econ = max(_tot - _bus, 0)
    econ_seats_yr = _econ * freq * weeks
    bus_seats_yr = _bus * freq * weeks
    econ_lf = (demand_each_way * econ_share) / econ_seats_yr if econ_seats_yr else 0.0
    bus_lf = (demand_each_way * (1 - econ_share)) / bus_seats_yr if bus_seats_yr else 0.0
    if _bus == 0:              # single class: all demand into econ
        econ_lf = demand_each_way / econ_seats_yr if econ_seats_yr else 0.0
        bus_lf = 0.0
    plan_econ, plan_bus = min(econ_lf, plan_lf), min(bus_lf, plan_lf)
    served = plan_econ * econ_seats_yr + plan_bus * bus_seats_yr
    spilled = max(demand_each_way - served, 0.0)
    # The fill this function reports is seats sold over seats flown, which is what
    # route_forecast reports and what a client reads off a slide. It used to be taken from the P&L's
    # own load_factor, computed on the generic cabin, so the optimiser could select on one fill and
    # the forecast then print another. Two numbers for one quantity is how /api/optimise and
    # /api/forecast drifted apart before.
    seats_yr = econ_seats_yr + bus_seats_yr
    total_lf = (served / seats_yr) if seats_yr else 0.0
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
    return {"aircraft": code, "seats": _econ + _bus, "range_km": ac["range_km"], "category": ac["category"],
            "seats_source": ("carrier configuration, OAG" if seats_override else "generic type table"),
            "econ_lf": plan_econ, "bus_lf": plan_bus, "total_lf": total_lf,
            "pnl_load_factor": y.get("load_factor"),
            "served_each_way": round(served), "spilled_each_way": round(spilled),
            "margin": y.get("margin"), "annual_profit": round(ann_profit),
            "breakeven_lf": y.get("breakeven_lf")}


def _block_min_for(distance_nm):
    # cruise ~460 kt + 35 min ground manoeuvre; one-way block minutes from sector nm
    return round(distance_nm / 460.0 * 60 + 35)


def select_aircraft(distance_nm, demand_each_way, freq, plan_lf=0.875, econ_share=0.85,
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
    # The named carrier's own cabin, measured, so the gauge is chosen on the metal it would actually
    # fly rather than on the generic configuration of the type. Empty when there is no store or no
    # named carrier, and the generic table then stands.
    cfg = {}
    if airline_iata:
        try:
            import capacity_frame as CF
            cfg = CF.config_for(airline_iata, distance_km)
        except Exception:
            cfg = {}
    rows = [evaluate(c, distance_nm, demand_each_way, freq, plan_lf, econ_share, econ_fare_ow,
                     bus_fare_ow, airspace, airline_type, aircraft_age, block_min, fuel_price_usd_kg,
                     weeks=weeks, seats_override=cfg.get(c))
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
                             bus_fare_ow=1300.0, stim=1.0, plan_lf=0.875, airspace=None, airline_type="FSC",
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


# ---------------------------------------------------------------------------
# Range criticality (John, 6 August 2026)
# ---------------------------------------------------------------------------
# The range filter in candidates() is a pass or fail against the type's still-air
# book range with a 3% cushion. That is the right gate, but it says nothing about
# how close to the edge a route that passes actually sits, and a reader looking at
# a recommendation cannot tell a comfortable sector from one that will be payload
# restricted on a bad day. This reports the margin so the page can say so.
#
# Book range is still air at a typical payload. A real mission loses distance to
# routing away from the great circle, to reserves and to the alternate, and the
# westbound North Atlantic and westbound transcontinental legs lose more again to
# the prevailing wind in winter. So the bands are set against book range, and the
# message defers to the operator's payload-range chart rather than asserting a
# penalty this module has no source for.

RANGE_BANDS = [
    (0.95, "AT THE LIMIT"),
    (0.85, "RANGE CRITICAL"),
    (0.75, "RANGE WATCH"),
]


def _westbound(origin_lon, dest_lon, threshold_deg=25.0):
    """True where the sector runs materially west, which is the headwind leg."""
    if origin_lon is None or dest_lon is None:
        return False
    d = dest_lon - origin_lon
    while d > 180:
        d -= 360
    while d < -180:
        d += 360
    return d <= -threshold_deg


def range_margin(code, distance_km, origin_lon=None, dest_lon=None):
    """How close this type sits to its book range on this sector.

    Returns None when the type is unknown or the sector is comfortable, so the
    caller shows nothing. Otherwise a dict with band, the ratio, and a line written
    for the page. Silence is the default: a message on every route trains the
    reader to ignore it.
    """
    from aircraft_economics import AIRCRAFT   # imported here, as candidates() does
    ac = AIRCRAFT.get(code)
    if not ac or not ac.get("range_km") or not distance_km:
        return None
    book = float(ac["range_km"])
    ratio = float(distance_km) / book
    band = None
    for cut, name in RANGE_BANDS:
        if ratio >= cut:
            band = name
            break
    if not band:
        return None

    nm = distance_km / 1.852
    book_nm = book / 1.852
    head = ("The sector is %s nm against a still-air range of %s nm for the %s, "
            "so it uses %.0f%% of book range."
            % (format(int(round(nm)), ","), format(int(round(book_nm)), ","), code, ratio * 100))
    if band == "AT THE LIMIT":
        body = ("At this margin the type is at its published limit on this sector. Expect a "
                "payload restriction in normal winter conditions, and treat a full cabin as "
                "the exception rather than the plan.")
    elif band == "RANGE CRITICAL":
        body = ("A sector this close to book range is flown payload restricted on the days the "
                "wind is against it. Westbound in winter the aircraft would be expected to "
                "carry fewer passengers or less cargo on some rotations."
                if _westbound(origin_lon, dest_lon) else
                "A sector this close to book range is flown payload restricted on the days the "
                "wind is against it, and on a hot day out of a short or high field.")
    else:
        body = ("There is margin here, but not much of it. Routing away from the great circle, "
                "the alternate and the reserve all come out of the same figure.")
    tail = ("Confirm against the operator's payload-range chart for the planned cabin before "
            "the schedule is fixed.")
    return {"band": band, "ratio": round(ratio, 3), "code": code,
            "distance_nm": round(nm), "book_range_nm": round(book_nm),
            "westbound": _westbound(origin_lon, dest_lon),
            "message": "%s %s %s" % (head, body, tail)}
