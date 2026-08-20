#!/usr/bin/env python3
"""Fixture test for the contract forecast-table row mapping (the 18 August 2026
defect: mixed bases printed -80.6% growth and a row that did not multiply through).
Relationships are asserted, not hand-rounded constants.

    py -3.12 test_contract_p2p_row.py

Every figure here is a TEST FIXTURE (the CI case's own values, as the payload
carries them).

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forecast_to_contract import _fill_forecast_table

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    fc = {"demand": {"natural": 203400, "p2p_carried": 33300, "captured": 45400,
                     "stimulation": 1.15},
          "schedule": {"growth_rate": 0.0223, "growth_years": 3}}
    contract = {"segment_forecast": {"summary": {
        "point_to_point_total": {"base_annual_demand": 394256,   # the two-way poison
                                 "demand_after_stimulation": 87948,
                                 "forecast": 70094},
        "connecting_at_hub_total": {"base_annual_demand": 744930, "forecast": 31313,
                                    "capture_rate": 0.042},
        "connecting_at_destination_total": {"forecast": 9977,
                                            "stimulation_factor": 1.0},
    }}}
    _fill_forecast_table(contract, fc)
    ss = contract["segment_forecast"]["summary"]
    p, h, d = (ss[k] for k in ("point_to_point_total", "connecting_at_hub_total",
                               "connecting_at_destination_total"))
    cum = 1 + p["annual_growth_rate"]
    # THE ROW IS BOTH DIRECTIONS (19 August 2026): the connecting legs and the grand
    # total arrive two-way, and an each-way p2p row under them failed the sum a network
    # planner does in the room. natural and p2p_carried are each-way in the payload,
    # so every annual figure prints at twice the payload key.
    check("poison base replaced by the decomposition",
          abs(p["base_annual_demand"] - 394256) > 5000)
    check("base grows to the service-year column",
          abs(p["base_annual_demand"] * cum - p["demand_at_service_year"]) < 60)
    check("growth is the payload's, not -80.6%",
          0.05 < p["annual_growth_rate"] < 0.09)
    check("service-year column is the grown market, both directions",
          p["demand_at_service_year"] == 406800)
    prod = (p["demand_at_service_year"] * p["stimulation_factor"] * p["capture_rate"])
    check("the row multiplies through",
          abs(prod - p["forecast"]) / p["forecast"] < 0.005,
          "%.0f v %d" % (prod, p["forecast"]))
    check("forecast is the carried figure, both directions", p["forecast"] == 66600)
    check("basis line states the two-way basis",
          "both directions" in p.get("_basis", "")
          and "multiplies through" in p.get("_basis", ""))
    check("hub base decomposed from its grown figure",
          abs(h["base_annual_demand"] * cum - 744930) < 60)
    check("hub growth stated, same rate", h["annual_growth_rate"] == p["annual_growth_rate"])
    check("connecting stimulation stated as 1.0", h["stimulation_factor"] == 1.0)
    check("a leg with no base keeps its gap, never a zero",
          d.get("base_annual_demand") is None)
    # CAGR, 20 August 2026 (Mark Kiehl/SJC): the deck now displays the per-annum rate,
    # not the cumulative. The fixture's growth_rate (0.0223) IS that rate; cagr must
    # equal it exactly, and must be materially smaller than the cumulative it sits
    # beside, or the two are showing the same number twice under different labels.
    check("cagr is the payload's per-annum rate, not the cumulative",
          abs(p["cagr"] - 0.0223) < 0.0001 and p["cagr"] < p["annual_growth_rate"],
          "cagr=%.4f cumulative=%.4f" % (p["cagr"], p["annual_growth_rate"]))
    check("hub leg carries the same cagr as p2p", h["cagr"] == p["cagr"])
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
