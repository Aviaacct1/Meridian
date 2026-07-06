#!/usr/bin/env python3
"""
Avia Solutions - seasonality check for a route case (the flat-year-round assumption).
=====================================================================================
The assess chain runs one annual load factor, i.e. a daily service filling the aircraft every
month. A leisure-led transatlantic route does not behave that way: summer is capacity-limited and
winter is thin. This applies a MONTHLY DEMAND PROFILE to the case's annual directional demand and
compares three operating pictures:

  A. Nominal flat   - the assess headline: every month at the planning load factor (optimistic).
  B. Flat daily     - fly daily all year, but carry only each month's real demand (winter
                      under-fills at full cost; the true cost of holding a daily schedule).
  C. Seasonal sched - trim winter frequency to hold the planning load factor, so winter flies
                      fewer, fuller rotations at lower cost; summer stays daily and capacity-limited.

The monthly profile defaults to a leisure transatlantic shape (peak Jul/Aug, trough Jan-Mar),
anchored on the published European summer/winter seat swing (about 50-65% more August than
February seats; demand swings harder than seats). It is an ASSUMPTION pending a monthly Sabre
pull (the annual ODPOO store has no month column). Override with --profile.

RUN:
    py -3.12 seasonality_check.py genoa_nyc
    py -3.12 seasonality_check.py genoa_nyc --profile 0.6,0.6,0.7,0.85,1.05,1.3,1.5,1.5,1.2,0.95,0.7,1.05
"""
import argparse, math, os, sys

# leisure transatlantic monthly demand index (sum = 12, so the average month = 1.0)
DEFAULT_PROFILE = [0.60, 0.60, 0.70, 0.85, 1.05, 1.30, 1.50, 1.50, 1.20, 0.95, 0.70, 1.05]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from route_case import RouteCase
    from aircraft_economics import AIRCRAFT, RoutePnL

    ap = argparse.ArgumentParser(description="Seasonality check for a route case.")
    ap.add_argument("case")
    ap.add_argument("geonames_txt", nargs="?", help="unused; kept for CLI symmetry with assess.py")
    ap.add_argument("--profile", default=None, help="12 comma monthly demand indices (else leisure default)")
    ap.add_argument("--each-way", type=float, default=None, help="annual directional demand (else from <case>_case.json)")
    ap.add_argument("--winter-floor", type=float, default=0.50, help="min frequency share kept in a trimmed month")
    a = ap.parse_args()

    case, base_dir = RouteCase.load_with_dir(a.case)
    import json
    if a.profile:
        prof = [float(x) for x in a.profile.split(",")]
    elif case.seasonality_profile:
        prof = list(case.seasonality_profile)          # the case's own (real) monthly shape
    else:
        prof = list(DEFAULT_PROFILE)
    assert len(prof) == 12, "profile needs 12 monthly values"
    prof = [p * 12.0 / sum(prof) for p in prof]               # normalise to average 1.0

    # annual directional demand: from the saved case output unless overridden
    if a.each_way is not None:
        each_way = a.each_way
    else:
        path = os.path.join(base_dir, f"{case.case_id}_case.json")
        if not os.path.exists(path):
            path = os.path.join(here, f"{case.case_id}_case.json")
        each_way = json.load(open(path))["directional_demand"]

    ac = AIRCRAFT[case.aircraft]
    seats = ac["econ_seats"] + ac["bus_seats"]
    plan_lf = case.plan_lf
    fuel_kw = {"fuel_price_usd_kg": case.fuel_price_usd_kg} if case.fuel_price_usd_kg is not None else {}
    fare = case.econ_fare_ow if case.econ_fare_ow is not None else 360

    def turn_profit(lf):
        rp = RoutePnL("New entrant", case.aircraft, case.home, case.primary_dest,
                      case.sector_nm, case.block_min, econ_lf=lf, bus_lf=lf,
                      econ_fare_ow=fare, bus_fare_ow=case.bus_fare_ow,
                      airspace=dict(case.airspace), airline_type=case.airline_type,
                      aircraft_age=case.aircraft_age, **fuel_kw)
        return rp.compute()["profit"]

    # monthly demand each way
    annual_share = sum(DAYS)
    dem = [each_way * (DAYS[m] / annual_share) * prof[m] for m in range(12)]   # demand by month

    rowsA = rowsB = rowsC = 0.0
    perB = []; perC = []
    for m in range(12):
        daily_turns = DAYS[m]                                   # 7x/week ~ one rotation/day
        # A. nominal flat: every month at plan LF
        pA = daily_turns * turn_profit(plan_lf)
        # B. flat daily: carry real demand, fly daily regardless
        lfB = min(dem[m] / (seats * daily_turns), plan_lf)
        pB = daily_turns * turn_profit(lfB)
        # C. seasonal schedule: trim frequency to hold ~plan LF in thin months
        need_turns = dem[m] / (seats * plan_lf)
        turnsC = max(min(daily_turns, math.ceil(need_turns)), a.winter_floor * daily_turns)
        lfC = min(dem[m] / (seats * turnsC), plan_lf)
        pC = turnsC * turn_profit(lfC)
        rowsA += pA; rowsB += pB; rowsC += pC
        perB.append((daily_turns, lfB, pB)); perC.append((turnsC, lfC, pC))

    print(f"Case {case.case_id}: {case.aircraft}, daily, annual directional demand {each_way:,.0f} each way")
    print(f"Profile (Aug/Feb demand ratio {prof[7]/prof[1]:.1f}); plan LF cap {plan_lf:.0%}\n")
    print(f"  {'mon':4} {'demand':>8}  {'B LF':>5} {'C turns':>8} {'C LF':>5}")
    for m in range(12):
        print(f"  {MONTHS[m]:4} {dem[m]:>8,.0f}  {perB[m][1]:>5.0%} {perC[m][0]:>8.0f} {perC[m][1]:>5.0%}")
    print("\n  ANNUAL PROFIT:")
    print(f"    A nominal flat (plan LF every month, the assess headline): ${rowsA:>12,.0f}")
    print(f"    B flat daily   (daily all year, real monthly demand):      ${rowsB:>12,.0f}")
    print(f"    C seasonal     (trim winter frequency to hold load):       ${rowsC:>12,.0f}")
    print(f"\n  seasonality drag on a flat daily schedule: ${rowsA-rowsB:,.0f} "
          f"({(rowsA-rowsB)/rowsA:.0%} of the headline)")
    print(f"  recovered by a seasonal schedule: ${rowsC-rowsB:,.0f}  "
          f"(seasonal vs headline: {rowsC/rowsA-1:+.0%})")


if __name__ == "__main__":
    main()
