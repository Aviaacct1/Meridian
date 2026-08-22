#!/usr/bin/env python3
"""Avia Solutions - synthetic-fixture check of the deck_contract.py fixes (22 August 2026).

Three things fixed in build_contract(), all found while checking route_deck.py/deck_contract.py for
existing domestic/international basis logic (there was none, until this):

  1. pdew() divided by a flat 728 (52wk x 7 daily x 2), regardless of the route's real frequency.
     Same defect shape as route_feed.py's PTEW fix earlier the same day.
  2. connecting_at_hub/connecting_at_destination's per-city "cities" list and its own "total" were
     built from hub_cities/dest_cities' annual_demand/annual_forecast RAW, each way - the one place
     left out of the "everything doubles in build_contract()" rule the 20 August _hub_mkt2 fix
     established.
  3. THE ACTUAL FEATURE: US domestic route traffic is conventionally quoted each way (DOT/T-100
     enplanements); international traffic (SJC-TPE included) is quoted two way. case["domestic"],
     set once by forecast_to_contract.case_and_outputs from the route's own two endpoints, now
     controls a display-only _disp() wrapper applied at the passenger-count summary fields
     (segment_forecast, connecting_at_hub/destination, the catchment/summary market-size headlines).
     Capacity, revenue, schedule and economics are NOT wrapped - deliberately, they are operational
     and financial facts, not a passenger-count convention choice (the same reasoning that held
     cortex_workbook.py's Economics tab out of the EW/2-way pairing the same day).

Needs no Sabre/OAG access - build_contract() takes already-computed case/outputs/connecting dicts,
so this runs anywhere.

    py -3.12 test_deck_contract_ptew.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\Deck Generator")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"/Deck Generator")

import deck_contract as DC

FAIL = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print("%-70s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def make_case(freq, domestic):
    # Destination held CONSTANT between the two scenarios on purpose: this fixture isolates the
    # "domestic" flag as the only variable, so any difference in the output is attributable to that
    # flag alone, not to a second changed input. A real US-domestic case would of course have a US
    # destination (SJC-LAX, say) - that's a fixture-realism question, separate from what this test
    # checks, which is whether build_contract() responds correctly to case["domestic"].
    case = {"frequency": freq, "aircraft": "A359", "sector_nm": 5637, "home": "SJC",
            "primary_dest": "TPE", "hub_airport": "TPE",
            "service_year": 2027, "airline_name": "China Airlines", "airline_iata": "CI",
            "domestic": domestic}
    outputs = {
        "frequency": freq,
        "route_pnl": {"load_factor": 0.85, "econ_rev": 100000, "bus_rev": 20000, "cargo_rev": 5000},
        "annual_pnl": {"annual_pax": 40552, "annual_turnarounds": freq * 52,
                       "annual_gross_rev": 5000000},
        "natural": 100000, "directional_demand": 15646, "capture": 0.12,
        "p2p_carried_ew": 15646, "connecting_carried_ew": 4630,
        "p2p_demand_ew": 20000, "feed_beyond_ew": 20000, "feed_behind_ew": 6000,
        "observed_split": {}, "case_id": "TEST-SJC-ROUTE",
    }
    hub_cities = [{"city_code": "MNL", "city_name": "Manila", "country": "PH",
                   "annual_demand": 40000, "airline_share": 0.03, "annual_forecast": 1500},
                  {"city_code": "BKK", "city_name": "Bangkok", "country": "TH",
                   "annual_demand": 34000, "airline_share": 0.03, "annual_forecast": 1000}]
    dest_cities = [{"city_code": "PHX", "city_name": "Phoenix", "country": "US",
                    "annual_demand": 18000, "airline_share": 0.025, "annual_forecast": 400}]
    connecting = {"hub_cities": hub_cities, "dest_cities": dest_cities,
                  "hub_market": 200000, "dest_market": 60000}
    return case, outputs, connecting


def main():
    freq = 5   # non-daily, so the flat-728/365 bugs would visibly under-read if unfixed
    case_i, out_i, cnx_i = make_case(freq, domestic=False)
    case_d, out_d, cnx_d = make_case(freq, domestic=True)
    ci = DC.build_contract(case_i, out_i, connecting=cnx_i)   # international: two way (unchanged)
    cd = DC.build_contract(case_d, out_d, connecting=cnx_d)   # US domestic: each way (the new bit)
    si, sd = ci["segment_forecast"]["summary"], cd["segment_forecast"]["summary"]

    print(f"freq={freq}/week -> {freq * 52 * 2:,} departures/yr two-way "
          f"(old flat basis assumed {DC.DAYS_2WAY:,})\n")

    # --- 1. PTEW basis (both contracts, freq-based not flat-728) ---------------------------------
    hub_i, hub_d = si["connecting_at_hub_total"], sd["connecting_at_hub_total"]
    expected_ptew_i = round(hub_i["forecast"] / (freq * 52 * 2), 1)
    check("international: PTEW uses real freq, not flat 728",
          hub_i["pdew"] == expected_ptew_i,
          f"got {hub_i['pdew']}, expected {expected_ptew_i}")
    check("PTEW is a RATE: identical on the domestic (each-way) and international (two-way) "
          "contracts for the same underlying route (this is the point of passing mult through pdew)",
          hub_i["pdew"] == hub_d["pdew"], f"international={hub_i['pdew']}, domestic={hub_d['pdew']}")

    # --- 2. cities-list doubling still holds (from the earlier same-day fix) ---------------------
    cities_total = ci["connecting_at_hub"]["total"]["annual_forecast"]
    leg_total = hub_i["forecast"]
    ratio = cities_total / leg_total
    check("connecting_at_hub.total and its own leg total are the same basis (ratio 0.3-1.0)",
          0.3 <= ratio <= 1.0, f"cities_total={cities_total:,}, leg_total={leg_total:,}, ratio={ratio:.2f}")

    # --- 3. THE FEATURE: every passenger-count summary figure on the domestic contract is exactly
    # half its international counterpart, for the SAME underlying route and inputs ------------------
    pairs = [
        ("point_to_point_total.forecast", si["point_to_point_total"]["forecast"], sd["point_to_point_total"]["forecast"]),
        ("point_to_point_total.base_annual_demand", si["point_to_point_total"]["base_annual_demand"], sd["point_to_point_total"]["base_annual_demand"]),
        ("connecting_at_hub_total.forecast", hub_i["forecast"], hub_d["forecast"]),
        ("connecting_at_hub_total.top_cities_forecast", hub_i["top_cities_forecast"], hub_d["top_cities_forecast"]),
        ("connecting_at_destination_total.forecast", si["connecting_at_destination_total"]["forecast"], sd["connecting_at_destination_total"]["forecast"]),
        ("grand_total.forecast", si["grand_total"]["forecast"], sd["grand_total"]["forecast"]),
        ("connecting_at_hub.total.annual_forecast", ci["connecting_at_hub"]["total"]["annual_forecast"], cd["connecting_at_hub"]["total"]["annual_forecast"]),
        ("connecting_at_hub.cities[0].annual_forecast", ci["connecting_at_hub"]["cities"][0]["annual_forecast"], cd["connecting_at_hub"]["cities"][0]["annual_forecast"]),
        ("connecting_at_hub.cities[0].annual_demand", ci["connecting_at_hub"]["cities"][0]["annual_demand"], cd["connecting_at_hub"]["cities"][0]["annual_demand"]),
        ("catchment.top_markets_beyond_hub[0].annual_demand", ci["catchment"]["top_markets_beyond_hub"][0]["annual_demand"], cd["catchment"]["top_markets_beyond_hub"][0]["annual_demand"]),
        ("route_metadata.catchment_headline.point_to_point_market", ci["route_metadata"]["catchment_headline"]["point_to_point_market"], cd["route_metadata"]["catchment_headline"]["point_to_point_market"]),
        ("summary_and_schedule.connecting_market_over_hub", ci["summary_and_schedule"]["connecting_market_over_hub"], cd["summary_and_schedule"]["connecting_market_over_hub"]),
    ]
    for label, intl_v, dom_v in pairs:
        ok = intl_v is not None and dom_v is not None and abs(dom_v - intl_v / 2) <= 1
        check(f"domestic = international / 2: {label}", ok, f"international={intl_v}, domestic={dom_v}")

    # --- 4. capture_rate is a ratio: identical between the two contracts --------------------------
    check("capture_rate unaffected by basis (point_to_point)",
          si["point_to_point_total"]["capture_rate"] == sd["point_to_point_total"]["capture_rate"])
    check("capture_rate unaffected by basis (connecting_at_hub)",
          hub_i["capture_rate"] == hub_d["capture_rate"], f"intl={hub_i['capture_rate']}, dom={hub_d['capture_rate']}")

    # --- 5. Capacity, revenue, schedule and economics DO NOT change with basis - the deliberate
    # carve-out (a rotation's cost, seats and ASK are operational/financial facts, not a passenger-
    # count convention choice) --------------------------------------------------------------------
    check("annual_capacity unchanged by basis",
          ci["revenue_forecast"]["annual_capacity"] == cd["revenue_forecast"]["annual_capacity"])
    check("revenue_forecast.passengers.total unchanged by basis (revenue-context passengers stay two way)",
          ci["revenue_forecast"]["passengers"]["total"] == cd["revenue_forecast"]["passengers"]["total"])
    check("economics_year1.avg_ow_fare_blended unchanged by basis",
          ci["economics_year1"]["avg_ow_fare_blended"] == cd["economics_year1"]["avg_ow_fare_blended"])
    check("summary_and_schedule.schedule (physical timetable) unchanged by basis",
          ci["summary_and_schedule"]["schedule"] == cd["summary_and_schedule"]["schedule"])

    # --- 6. The basis is stated, not left implicit - John's "make it super clear" instruction ------
    check("_demand_basis states each way on the domestic contract", cd["_demand_basis"] == "each way (US domestic)")
    check("_demand_basis states two way on the international contract", ci["_demand_basis"] == "two way")

    # --- 7. contract_legs_check.py's own invariants still hold on BOTH contracts -------------------
    for tag, c, s in (("international", ci, si), ("domestic", cd, sd)):
        p2p, hub, dst, tot = s["point_to_point_total"]["forecast"], s["connecting_at_hub_total"]["forecast"], \
                              s["connecting_at_destination_total"]["forecast"], s["grand_total"]["forecast"]
        check(f"LEGS SUM holds on the {tag} contract", abs((p2p + hub + dst) - tot) <= 2,
              f"{p2p}+{hub}+{dst}={p2p + hub + dst} vs {tot}")
        top_hub = s["connecting_at_hub_total"].get("top_cities_forecast")
        check(f"SUBTOTAL holds on the {tag} contract", top_hub is None or top_hub <= hub + 2,
              f"top_cities_forecast={top_hub}, leg={hub}")

    print("\n%d checks, %d failed%s" % (TOTAL[0], len(FAIL), ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
