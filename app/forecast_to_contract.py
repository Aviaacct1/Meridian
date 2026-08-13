"""The join between the live forecast and the Observatory deck, which has never existed.

WHAT WAS MISSING. The 40-page Observatory deck is built and the forecast is built, and nothing
connected them. run_observatory_pitch.py says so in its own docstring: "deck_contract.py is not yet
wired into the connector, so the fc handed in here carries route identity and placeholder demand
only. Nothing in the deck reads a number from it." Everything downstream of the contract already
works: deck_contract.build_contract emits it, forecast_spec turns it into slides, and
spec_from_research renders them. The break is at this one join, and deck_contract still expects the
shape assess.py produced in the June chain rather than the payload calibrated_forecast returns.

    from forecast_to_contract import contract_from_forecast
    fc = cortex_app.calibrated_forecast("SJC", "TPE", airline="CI", aircraft="A359", seats=306,
                                        freq=4, forecast_year=2028, growth=0.07,
                                        partner_carriers=["WN"], with_econ=True)
    contract = contract_from_forecast(fc, currency="USD")

NOTHING HERE COMPUTES A FORECAST. Every figure is read from the payload by its own key and mapped
to the contract's own key. A key that is absent produces None rather than a zero, because a zero
reads as a measurement and a None reads as a gap.

THE THREE MAPPINGS THAT ARE NOT OBVIOUS, stated here rather than discovered later. Each of them is
the shape of an error this programme has already paid for.

  CARRIED AGAINST DEMAND. The payload carries BOTH: demand.total is CARRIED each way, after the
  87.5% plan cap, and demand.total_demand is uncapped demand each way. CAPPED-VS-UNCAPPED of 12
  August records a claim quoted for a week that compared one against the other. The contract's
  directional_demand takes the CARRIED figure, because the P&L downstream is built on passengers
  who fly, and the uncapped figure is carried alongside as demand_uncapped_ew so the two can never
  be confused again.

  SEATS. deck_contract._seats_for falls back to the generic AIRCRAFT table, where the A350-900 is
  336 seats. China Airlines flies it at 306. Sizing the deck on the generic figure would overstate
  capacity by 8 to 13% on exactly the carriers in the SJC-TPE set, so the actual seat count from the
  forecast is passed as a cabin_config and the type table's own business fraction is scaled to it.

  EACH WAY AGAINST TWO WAY. The payload is EACH WAY throughout; scenario_runner doubles for its own
  table. The contract takes each-way figures, so nothing is doubled here, and every key this module
  writes ends _ew where it could be mistaken.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# deck_contract lives in the deck generator folder, whose name carries a space. Found by path
# rather than by an import hook, and named loudly if it is not there, because a silent fallback to
# a hand-built contract is how a deck ends up describing a route nobody forecast.
_GEN = os.path.join(os.path.dirname(HERE), "Deck Generator")
if _GEN not in sys.path:
    sys.path.insert(0, _GEN)


def _need(fc):
    """Everything this module reads, checked once and named together rather than failing one at a
    time three frames down. Returns a list of what is missing."""
    miss = []
    if not fc.get("ok"):
        miss.append("the forecast did not succeed: %s" % fc.get("error", "no reason given"))
        return miss
    if not fc.get("economics_ok"):
        miss.append("economics unavailable, so the P&L blocks cannot be built: %s"
                    % fc.get("economics_error", "no reason given"))
    for k in ("demand", "capacity", "origin", "dest", "distance_nm"):
        if k not in fc:
            miss.append("payload has no %r" % k)
    return miss


def case_and_outputs(fc):
    """The two dicts deck_contract.build_contract takes, mapped from the live payload.

    Returned separately from the contract itself so a caller can inspect or override the mapping
    before it is used, and so the mapping can be tested without building a deck.
    """
    dem, cap = fc["demand"], fc["capacity"]
    o, d = fc["origin"], fc["dest"]
    sch = fc.get("schedule") or {}
    ec = fc.get("economics") or {}

    # SEATS: the forecast's own figure, not the type table's. See the docstring.
    seats_total = cap.get("seats")
    cabin_config = None
    if seats_total:
        try:
            from aircraft_economics import AIRCRAFT as _AC
            _t = _AC.get(cap.get("aircraft")) or {}
            _tb, _tc = float(_t.get("bus_seats", 0)), float(_t.get("econ_seats", 0))
            _tt = _tb + _tc
            # The type's business FRACTION applied to the carrier's actual total. The split is the
            # type's and the total is the carrier's, which is the honest combination when the LOPA
            # is not known: it never contradicts the seat count the forecast was run on.
            _b = round(seats_total * (_tb / _tt)) if _tt else 0
            cabin_config = {"business": _b, "premium_coach": 0, "coach": int(seats_total) - _b}
        except Exception:                                    # noqa: BLE001
            cabin_config = {"business": 0, "premium_coach": 0, "coach": int(seats_total)}

    case = {
        "aircraft": cap.get("aircraft"),
        "cabin_config": cabin_config,
        "sector_nm": fc.get("distance_nm"),
        "home": o.get("iata") or o.get("code"),
        "primary_dest": d.get("iata") or d.get("code"),
        "hub_airport": d.get("iata") or d.get("code"),       # the destination IS the hub on a feed route
        "service_year": sch.get("forecast_year") or fc.get("year"),
        "frequency": cap.get("freq"),
        "airline": fc.get("airline"),
        "origin_city": o.get("city"),
        "dest_city": d.get("city"),
    }

    outputs = {
        "natural": dem.get("natural"),
        "current": dem.get("current"),
        "capture": dem.get("qsi_share"),
        # CARRIED, not uncapped. The uncapped figure travels beside it under its own name.
        "directional_demand": dem.get("total"),
        "demand_uncapped_ew": dem.get("total_demand"),
        "p2p_carried_ew": dem.get("p2p_carried"),
        "connecting_carried_ew": dem.get("connecting_carried"),
        "feed_total_ew": dem.get("feed_total"),
        "frequency": cap.get("freq"),
        "econ_lf": ec.get("econ_lf"),
        "bus_lf": ec.get("bus_lf"),
        "route_pnl": {k: ec.get(k) for k in
                      ("revenue", "fuel", "maintenance", "crew", "ownership",
                       "airport_nav_other", "total_cost", "profit", "margin", "breakeven_lf")},
        "annual_pnl": {"profit": ec.get("annual_profit"),
                       "aircraft_required": ec.get("aircraft_required")},
        "observed_split": (fc.get("catchment") or {}).get("observed_share"),
        # PROVENANCE TRAVELS WITH THE NUMBERS. A deck built from a forecast must be able to say
        # which engine produced it and at what connecting level, because from 13 August 2026 those
        # are two different things and the payload reports both.
        "forecast_engine": fc.get("forecast_engine"),
        "feed_level": fc.get("feed_level"),
        "load_factor": cap.get("load"),
        "spill_ew": cap.get("spill"),
    }
    return case, outputs


def contract_from_forecast(fc, currency="USD", growth_rate=None, ancillary_per_pax=None,
                           segment_rows=None, connecting=None):
    """The deck data contract for one live forecast, or a RuntimeError naming what is missing."""
    miss = _need(fc)
    if miss:
        raise RuntimeError("cannot build a contract: " + "; ".join(miss))
    import deck_contract as DC
    case, outputs = case_and_outputs(fc)
    contract = DC.build_contract(case, outputs, connecting=connecting, growth_rate=growth_rate,
                                 ancillary_per_pax=ancillary_per_pax, segment_rows=segment_rows)
    # Currency is NOT inferred, which is forecast_spec's own rule: the contract carries fares and
    # revenues without stating one, so the caller states it and it goes into the column head.
    # Guessing would put the wrong symbol in front of every revenue figure on the page.
    contract["currency"] = currency
    contract["_source_engine"] = (outputs.get("forecast_engine") or {}).get("local_leg")
    return contract


def _selftest():
    """The mapping against a payload shaped like the real one, with known answers.

    Checks the three traps named in the docstring rather than that the code runs: carried against
    uncapped, the carrier's seat count against the type table's, and each way staying each way.
    """
    fc = {"ok": True, "economics_ok": True, "airline": "CI", "distance_nm": 5637,
          "origin": {"iata": "SJC", "city": "San Jose"}, "dest": {"iata": "TPE", "city": "Taipei"},
          "schedule": {"forecast_year": 2028},
          "demand": {"natural": 180000, "current": 120000, "qsi_share": 0.251, "total": 55692,
                     "total_demand": 58724, "p2p_carried": 41704, "connecting_carried": 13988,
                     "feed_total": 13988},
          "capacity": {"aircraft": "A359", "seats": 306, "freq": 4, "load": 0.875, "spill": 3032},
          "economics": {"revenue": 1, "profit": 2, "annual_profit": 3, "econ_lf": 0.9, "bus_lf": 0.7},
          "catchment": {"observed_share": {"SJC": 0.3}},
          "forecast_engine": {"local_leg": "qsi engine"}, "feed_level": {"qsi_k": 1.0}}
    case, out = case_and_outputs(fc)
    ok = True

    def chk(label, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("  %-46s %-12s %s" % (label, got, "OK" if good else "EXPECTED %s" % (want,)))

    chk("directional_demand is CARRIED, not uncapped", out["directional_demand"], 55692)
    chk("the uncapped figure travels separately", out["demand_uncapped_ew"], 58724)
    chk("seats come from the forecast, not the table", case["cabin_config"]["business"]
        + case["cabin_config"]["coach"], 306)
    chk("frequency", case["frequency"], 4)
    chk("service year from the schedule block", case["service_year"], 2028)
    chk("hub is the destination on a feed route", case["hub_airport"], "TPE")
    chk("capture is the qsi share", out["capture"], 0.251)
    print("\n  A359 in the generic table is 336 seats; the contract must carry 306, which is what")
    print("  China Airlines actually flies. That single line is an 8 to 13% capacity error on")
    print("  every carrier in the SJC-TPE set if it is got wrong.")
    return 0 if ok else 1


if __name__ == "__main__":
    print("forecast_to_contract selftest")
    raise SystemExit(_selftest())
