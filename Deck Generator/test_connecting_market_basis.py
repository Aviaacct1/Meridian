#!/usr/bin/env python3
"""Regression test for the connecting-leg basis defect Jol caught on the SJC-TPE
packs, 20 August 2026 ("connecting market over Taipei 719,500 both directions...
but this says each way", "there's definitely a mix in there").

build_contract() doubles natural, p2p_carried, cnx_carried and p2p_demand to a
two-way basis throughout - EXCEPT cnx["hub_market"]/["dest_market"], which arrive
each way from connecting_from_forecast (dem["feed_beyond_base"]/["feed_behind_base"],
the figure verify_connecting_build.py itself names "each way") and were used
undoubled. Two measured consequences, both checked here: the process-visual chart's
"both directions" caption sat over an each-way number, and the connecting legs'
capture rate divided a two-way carried figure by an each-way market, reading
roughly double the true rate.

    py -3.12 test_connecting_market_basis.py

Every figure here is a TEST FIXTURE, built loosely on the CI SJC-TPE case; it is
not required to reconcile in the way a real run's cross-checked outputs would.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck_contract import build_contract

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-66s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    case = {"airline_name": "China Airlines", "airline_iata": "CI", "home": "SJC",
            "primary_dest": "TPE", "hub_airport": "TPE", "aircraft": "A359",
            "sector_nm": 5637, "service_year": 2027, "frequency": 5}
    # hub_market/dest_market here are the EACH-WAY figures as connecting_from_forecast
    # hands them over (dem["feed_beyond_base"]/["feed_behind_base"]); this is the one
    # input to build_contract() that is NOT already two-way, unlike everything in
    # `outputs` below.
    outputs = {"natural": 160915, "directional_demand": 160915, "capture": 0.1429,
               "frequency": 5, "route_pnl": {"load_factor": 0.875},
               "annual_pnl": {"annual_pax": 69615},
               "p2p_carried_ew": 31293, "connecting_carried_ew": 38322,
               "p2p_demand_ew": 109477,
               "feed_beyond_ew": 29063, "feed_behind_ew": 9259}
    connecting = {"hub_cities": [{"city_code": "MNL", "annual_forecast": 3635}],
                  "dest_cities": [{"city_code": "LAX", "annual_forecast": 1468}],
                  "hub_market": 719486, "dest_market": 185485}
    c = build_contract(case, outputs, connecting=connecting)
    ss = c["segment_forecast"]["summary"]
    ch = c["route_metadata"]["catchment_headline"]
    sas = c["summary_and_schedule"]
    hub, dst = ss["connecting_at_hub_total"], ss["connecting_at_destination_total"]

    check("hub market doubled to two-way in catchment_headline",
          ch["connecting_market_over_hub"] == 719486 * 2, ch["connecting_market_over_hub"])
    check("dest market doubled to two-way in catchment_headline",
          ch["connecting_market_over_destination"] == 185485 * 2,
          ch["connecting_market_over_destination"])
    check("summary_and_schedule mirrors the same doubled figures (the process-visual "
          "chart's own source)",
          sas["connecting_market_over_hub"] == ch["connecting_market_over_hub"]
          and sas["connecting_market_over_destination"] == ch["connecting_market_over_destination"])
    check("hub leg's demand fields are the doubled figure, not the each-way input",
          hub["base_annual_demand"] == 719486 * 2
          and hub["demand_at_service_year"] == 719486 * 2
          and hub["demand_after_stimulation"] == 719486 * 2)
    check("dest leg now carries demand fields at all (previously absent entirely)",
          dst.get("base_annual_demand") == 185485 * 2
          and dst.get("demand_at_service_year") == 185485 * 2)

    # THE CAPTURE-RATE CONSEQUENCE: forecast (two-way, unchanged by this fix) divided
    # by an each-way market read double the true rate. Divided by the now-doubled
    # market, it halves back to the true figure.
    true_hub_rate = round(hub["forecast"] / (719486 * 2), 4)
    old_buggy_rate = round(hub["forecast"] / 719486, 4)
    check("hub capture rate is the true rate, not the old each-way-denominator figure",
          hub["capture_rate"] == true_hub_rate
          and abs(hub["capture_rate"] * 2 - old_buggy_rate) < 0.001,
          "true=%.4f old(buggy)=%.4f stored=%.4f" % (true_hub_rate, old_buggy_rate, hub["capture_rate"]))
    check("dest leg has a capture rate at all now (previously None: no denominator)",
          dst.get("capture_rate") is not None)

    # THE BA REFERENCE (the acceptance test's own hand-curated numbers) must be
    # untouched - this fix only changes the generic, model-driven build_contract()
    # path, never the validated 2015 deck's fixed figures.
    from deck_contract import ba_lhr_sjc_reference
    ba = ba_lhr_sjc_reference()
    ba_hub = ba["segment_forecast"]["summary"]["connecting_at_hub_total"]
    check("BA LHR-SJC acceptance reference unchanged (904,500, capture 0.045)",
          ba_hub["base_annual_demand"] == 904500 and ba_hub["capture_rate"] == 0.045)

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
