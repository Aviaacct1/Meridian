#!/usr/bin/env python3
"""
Avia Solutions - fleet utilisation & redeployment check for a route case.
=========================================================================
The single-route P&L charges ownership at a FULLY-UTILISED per-block-hour rate (the aircraft's
lease spread over its assumed annual block hours). That rate only recovers the lease if the
aircraft actually flies those hours. A single daily long-haul rarely does: a ~9h each-way sector
needs two aircraft in rotation but only fills part of their year, so each aircraft is under-used
and the route's headline profit quietly assumes the spare time is sold to OTHER routes.

This makes that assumption explicit. From the saved case it computes:
  - aircraft required and per-aircraft utilisation versus the full-util assumption,
  - the ownership-recovery GAP if those aircraft fly this route only (standalone),
  - the standalone-true profit versus the network headline,
  - the spare block hours (and rotation-equivalents) available for redeployment,
  - a network_pnl illustration: sharing the fleet with a complementary route keeps the aircraft
    count down rather than doubling it.

RUN:
    py -3.12 fleet_check.py genoa_nyc
"""
import argparse, json, math, os, sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from route_case import RouteCase
    from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL, network_pnl

    ap = argparse.ArgumentParser(description="Fleet utilisation & redeployment check for a route case.")
    ap.add_argument("case")
    ap.add_argument("geonames_txt", nargs="?", help="unused; CLI symmetry with assess.py")
    a = ap.parse_args()

    case, base_dir = RouteCase.load_with_dir(a.case)
    path = os.path.join(base_dir, f"{case.case_id}_case.json")
    if not os.path.exists(path):
        path = os.path.join(here, f"{case.case_id}_case.json")
    d = json.load(open(path))
    rp, ap_ = d["route_pnl"], d["annual_pnl"]

    util = rp["eff_util"]                                  # full-util assumption in the per-BH rate
    own_bh = rp["ownership"] / rp["block_hours_turn"]      # ownership $/block-hour
    total_bh = ap_["annual_block_hours"]
    frac = ap_["aircraft_required_fractional"]
    ceil = ap_["aircraft_required"]
    modelled_own = ap_["annual_ownership"]
    blended_month = own_bh * util / 12.0                  # implied blended lease per aircraft
    dedicated_own = ceil * blended_month * 12.0           # true ownership if dedicated to this route
    gap = dedicated_own - modelled_own
    per_ac = total_bh / ceil
    spare_bh = ceil * util - total_bh
    bh_turn = rp["block_hours_turn"]
    head = ap_["annual_profit"]

    print(f"FLEET REALITY  -  {case.case_id}: {case.aircraft}, {ap_['annual_turnarounds']:.0f} rotations/yr")
    print(f"  block hours/yr            {total_bh:,.0f}")
    print(f"  aircraft required         {frac:.2f} -> {ceil} physical")
    print(f"  per-aircraft utilisation  {per_ac:,.0f} BH/yr  ({per_ac/util:.0%} of the {util:,.0f} full-util rate)")
    print(f"  spare fleet capacity      {spare_bh:,.0f} BH/yr  (~{spare_bh/bh_turn:,.0f} rotations like this one)")

    print(f"\nOWNERSHIP RECOVERY  -  the per-BH rate assumes the aircraft is fully utilised")
    print(f"  ownership charged in the P&L     ${modelled_own:,.0f}/yr  (full-util rate x hours flown)")
    print(f"  true cost if {ceil} aircraft fly only this route  ${dedicated_own:,.0f}/yr "
          f"(blended lease ${blended_month:,.0f}/mo x {ceil})")
    print(f"  standalone ownership GAP         ${gap:,.0f}/yr")

    print(f"\nWHAT THE HEADLINE ASSUMES")
    print(f"  network headline profit (fleet fully utilised)  ${head:,.0f}")
    print(f"  true STANDALONE profit (this route's fleet only) ${head-gap:,.0f}")
    print(f"  redeployment must fill {spare_bh:,.0f} BH/yr ( ~{spare_bh/bh_turn:,.0f} rotations ) to close the gap")

    # ---- network illustration: share the fleet with a complementary route ----
    # Rebuild this route's AnnualRoutePnL from the case, then add an ILLUSTRATIVE complementary
    # route sized to soak up the spare hours, and show the fleet count with vs without sharing.
    fuel_kw = {"fuel_price_usd_kg": case.fuel_price_usd_kg} if case.fuel_price_usd_kg is not None else {}
    fare = case.econ_fare_ow if case.econ_fare_ow is not None else 360
    g_rp = RoutePnL("New entrant", case.aircraft, case.home, case.primary_dest, case.sector_nm,
                    case.block_min, econ_lf=d["econ_lf"], bus_lf=d["bus_lf"], econ_fare_ow=fare,
                    bus_fare_ow=case.bus_fare_ow, airspace=dict(case.airspace),
                    airline_type=case.airline_type, aircraft_age=case.aircraft_age, **fuel_kw)
    g_ann = AnnualRoutePnL(g_rp, case.frequency, 52)

    # illustrative complementary route: a SECOND long-haul on the same aircraft type and sector
    # length (so the utilisation base matches), at a frequency that fits inside the spare capacity,
    # priced conservatively below the Genoa case. Figures are ILLUSTRATIVE, not a real case.
    comp_freq = max(int(spare_bh / bh_turn / 52), 1)        # frequency that fits within the spare hours
    comp_rp = RoutePnL("Complementary", case.aircraft, case.home, "XXX",
                       case.sector_nm, case.block_min, econ_lf=0.82, bus_lf=0.82,
                       econ_fare_ow=320, bus_fare_ow=1200, airspace=dict(case.airspace),
                       airline_type=case.airline_type, aircraft_age=case.aircraft_age,
                       origin_charges=AIRPORTS_FALLBACK, dest_charges=AIRPORTS_FALLBACK, **fuel_kw)
    comp_ann = AnnualRoutePnL(comp_rp, comp_freq, 52)

    net = network_pnl([g_ann, comp_ann])
    g_ceil = ceil
    c_ceil = math.ceil(comp_ann.compute()["aircraft_required_fractional"])
    saved = g_ceil + c_ceil - net['aircraft_required']
    print(f"\nNETWORK ILLUSTRATION  (a 2nd long-haul, {comp_freq}x/week, fitted to the spare; illustrative)")
    print(f"  fleet if run SEPARATELY     {g_ceil} + {c_ceil} = {g_ceil + c_ceil} aircraft")
    print(f"  fleet SHARED (network_pnl)  {net['aircraft_required']} aircraft")
    print(f"  aircraft saved by sharing   {saved} (~${saved * blended_month * 12:,.0f}/yr of lease not duplicated)")
    print(f"  network annual profit       ${net['annual_profit']:,.0f}  (margin {net['margin']:.1%})")
    print("\n  Read: the route's headline holds when the fleet is busy across the network; as a")
    print("  standalone startup it is the lower number until the spare capacity is sold.")


# minimal indicative charges for the illustrative complementary route's airports
AIRPORTS_FALLBACK = dict(landing_per_turn=1500.0, pax_charge_per_pax=18.0,
                         ground_handling_per_turn=2200.0, recovery_per_pax=0.0)

if __name__ == "__main__":
    main()
