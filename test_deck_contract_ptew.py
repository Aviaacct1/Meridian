#!/usr/bin/env python3
"""Avia Solutions - synthetic-fixture check of the deck_contract.py fixes (22 August 2026).

Two live bugs fixed in build_contract(), found while checking route_deck.py/deck_contract.py for
domestic/international basis logic (there was none - separate piece of work):

  1. pdew() divided by a flat 728 (52wk x 7 daily x 2), regardless of the route's real frequency.
     Same defect shape as route_feed.py's PTEW fix earlier the same day. Fixed: freq/weeks now
     thread through every live call site in build_contract() (the ba_lhr_sjc_reference() acceptance
     fixture is daily, freq=7, already sits exactly on the 728 basis, left untouched).
  2. connecting_at_hub/connecting_at_destination's per-city "cities" list and its own "total" were
     built from hub_cities/dest_cities' annual_demand/annual_forecast RAW, each way - the one place
     left out of the "everything doubles in build_contract()" rule the 20 August _hub_mkt2 fix
     established. Fixed: doubled at the same three points these figures reach (the cities list, the
     leg total, and top_markets_beyond_hub).

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


def check(name, cond, detail=""):
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    # A synthetic 5x/week route (CI/SJC-TPE's own frequency), so the flat-728 bug (which assumes
    # daily, 7x/week) would visibly under-read PTEW if the fix had not taken.
    freq = 5
    case = {"frequency": freq, "aircraft": "A359", "sector_nm": 5637, "home": "SJC",
            "primary_dest": "TPE", "hub_airport": "TPE", "service_year": 2027,
            "airline_name": "China Airlines", "airline_iata": "CI"}
    outputs = {
        "frequency": freq,
        "route_pnl": {"load_factor": 0.85, "econ_rev": 100000, "bus_rev": 20000, "cargo_rev": 5000},
        "annual_pnl": {"annual_pax": 40552, "annual_turnarounds": freq * 52,
                       "annual_gross_rev": 5000000},
        "natural": 100000, "directional_demand": 15646, "capture": 0.12,
        "p2p_carried_ew": 15646, "connecting_carried_ew": 4630,
        "p2p_demand_ew": 20000, "feed_beyond_ew": 20000, "feed_behind_ew": 6000,
        "observed_split": {}, "case_id": "TEST-SJC-TPE",
    }
    # top-15 hub/dest cities, each-way forecast figures, EXACTLY the shape connecting_from_forecast
    # hands over (annual_demand/annual_forecast each way, per the 20 August hub_market/dest_market
    # comment: "arrive EACH WAY from connecting_from_forecast").
    hub_cities = [{"city_code": "MNL", "city_name": "Manila", "country": "PH",
                   "annual_demand": 40000, "airline_share": 0.03, "annual_forecast": 1500},
                  {"city_code": "BKK", "city_name": "Bangkok", "country": "TH",
                   "annual_demand": 34000, "airline_share": 0.03, "annual_forecast": 1000}]
    dest_cities = [{"city_code": "PHX", "city_name": "Phoenix", "country": "US",
                    "annual_demand": 18000, "airline_share": 0.025, "annual_forecast": 400}]
    connecting = {"hub_cities": hub_cities, "dest_cities": dest_cities,
                  "hub_market": 200000, "dest_market": 60000}

    c = DC.build_contract(case, outputs, connecting=connecting)
    s = c["segment_forecast"]["summary"]

    print(f"freq={freq}/week -> {freq * 52 * 2:,} scheduled departures/year, two-way "
          f"(the old flat basis assumed {DC.DAYS_2WAY:,})\n")

    # 1. PTEW basis: the leg's own pdew should equal forecast / (freq x 52 x 2), not / 728.
    hub_total = s["connecting_at_hub_total"]
    expected_ptew = round(hub_total["forecast"] / (freq * 52 * 2), 1)
    old_wrong_ptew = round(hub_total["forecast"] / DC.DAYS_2WAY, 1)
    check("hub leg PTEW uses the route's real frequency, not flat 728",
          hub_total["pdew"] == expected_ptew,
          f"got {hub_total['pdew']}, expected {expected_ptew} (old formula would give {old_wrong_ptew})")
    check("PTEW is measurably different from the pre-fix flat-728 figure on this non-daily route",
          abs(hub_total["pdew"] - old_wrong_ptew) > 1,
          f"fixed={hub_total['pdew']}, pre-fix-basis={old_wrong_ptew}")

    # 2. The two "connecting at hub" figures in one contract are now the same order of magnitude,
    # not a factor of ~2 apart (the cities-list total was each-way; the leg total was two-way).
    cities_total = c["connecting_at_hub"]["total"]["annual_forecast"]
    leg_total = hub_total["forecast"]
    ratio = cities_total / leg_total
    check("connecting_at_hub.total and segment_forecast leg total are the same basis (ratio 0.3-1.0, "
          "a top-15 subtotal of a fuller market, not ~0.5x from a stray each-way figure)",
          0.3 <= ratio <= 1.0, f"cities_total={cities_total:,}, leg_total={leg_total:,}, ratio={ratio:.2f}")

    # 3. Per-city figures are plausible two-way numbers (roughly double what was fed in each-way).
    mnl = c["connecting_at_hub"]["cities"][0]
    check("per-city annual_forecast is doubled from the each-way input (Manila)",
          mnl["annual_forecast"] == 1500 * 2, f"got {mnl['annual_forecast']}, expected {1500 * 2}")
    check("per-city annual_demand is doubled from the each-way input (Manila)",
          mnl["annual_demand"] == 40000 * 2, f"got {mnl['annual_demand']}, expected {40000 * 2}")

    # 4. top_markets_beyond_hub carries the same doubled figure, not a third, different one.
    tmb = {m["city_code"]: m["annual_demand"] for m in c["catchment"]["top_markets_beyond_hub"]}
    check("top_markets_beyond_hub matches the cities list (Manila)",
          tmb.get("MNL") == mnl["annual_demand"], f"got {tmb.get('MNL')}, expected {mnl['annual_demand']}")

    # 5. contract_legs_check.py's own invariants still hold: legs sum to the grand total, and the
    # per-city SUBTOTAL never exceeds its own leg (the check this fix makes meaningful for the first
    # time - before the fix, an each-way top-15 subtotal against a two-way leg could never trip it).
    p2p = s["point_to_point_total"]["forecast"]
    hub = s["connecting_at_hub_total"]["forecast"]
    dst = s["connecting_at_destination_total"]["forecast"]
    tot = s["grand_total"]["forecast"]
    check("LEGS SUM: p2p + hub + dest = grand total (untouched by this fix, confirming no regression)",
          abs((p2p + hub + dst) - tot) <= 2, f"{p2p}+{hub}+{dst}={p2p + hub + dst} vs {tot}")
    top_hub = s["connecting_at_hub_total"].get("top_cities_forecast")
    check("SUBTOTAL: hub city-table total does not exceed its own leg",
          top_hub is None or top_hub <= hub + 2, f"top_cities_forecast={top_hub}, leg={hub}")

    print("\n%d checks, %d failed%s" % (5 + 4, len(FAIL), ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
