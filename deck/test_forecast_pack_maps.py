#!/usr/bin/env python3
"""Offline test of the forecast pack's map chain: the catchment ends through the
contract, the per-end pages with their population tables, the route page, the named
dropped-list, and the slide-32 pre-stimulation fill. Draws the real maps when basemap
is installed and skips them with a statement when it is not, because the pages must
degrade exactly the way the pack itself degrades.

    py -3.12 test_forecast_pack_maps.py

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "app"))

import forecast_pack as FP                                   # noqa: E402
from forecast_to_contract import (contract_from_forecast,    # noqa: E402
                                  _fill_forecast_table)

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", str(detail)[:70]))
    if not cond:
        FAIL.append(name)


def fixture_fc():
    return {"ok": True, "economics_ok": True, "airline": "CI", "distance_nm": 5637,
            "origin": {"iata": "SJC", "city": "San Jose"},
            "dest": {"iata": "TPE", "city": "Taipei"},
            "schedule": {"forecast_year": 2028},
            "demand": {"natural": 180000, "current": 120000, "qsi_share": 0.251,
                       "total": 55692, "total_demand": 58724, "p2p_carried": 41704,
                       "connecting_carried": 13988, "feed_total": 13988,
                       "stimulation": 1.15},
            "capacity": {"aircraft": "A359", "seats": 306, "freq": 4, "load": 0.875,
                         "spill": 3032},
            "economics": {"revenue": 1, "profit": 2, "annual_profit": 3,
                          "econ_lf": 0.9, "bus_lf": 0.7},
            "catchment": {"observed_share": {"SJC": 0.3}},
            "forecast_engine": {"local_leg": "qsi engine"},
            "feed_level": {"qsi_k": 1.0}, "year": 2025}


def fixture_profile(code, city, lat, lon, drive=True):
    import random
    rng = random.Random(7)
    locs = []
    for i in range(40):
        locs.append({"lat": lat + rng.uniform(-1.6, 1.6),
                     "lon": lon + rng.uniform(-1.6, 1.6),
                     "pop": rng.choice([8000, 25000, 90000, 400000, 1000000]),
                     "drive": (rng.choice([12, 25, 45, 70, 100, 150, None])
                               if drive else None),
                     "name": "Place %d" % i})
    return {"ok": True,
            "airport": {"code": code, "city": city, "country": "", "name": "",
                        "lat": lat, "lon": lon},
            "radius_km": 220, "total_pop": 8000000, "reach_120_pop": 7000000,
            "bands": {"30": 2000000, "60": 3000000, "90": 1500000, "120": 500000,
                      "999": 1000000},
            "capture": 0.30, "drive_available": drive, "locales": locs}


def test_contract_ends():
    ends = {"origin": fixture_profile("SJC", "San Jose", 37.36, -121.93),
            "destination": {"ok": False, "error": "no drive raster for TW"}}
    c = contract_from_forecast(fixture_fc(), catchment_ends=ends)
    check("good end written into the contract",
          "origin" in (c["catchment"].get("ends") or {}), "")
    check("failed end named, not thinned",
          "no drive raster" in (c["catchment"].get("_ends_partial") or ""),
          c["catchment"].get("_ends_partial"))
    c2 = contract_from_forecast(fixture_fc(), catchment_ends={
        "origin": {"ok": False, "error": "dump missing"},
        "destination": {"ok": False, "error": "dump missing"}})
    check("both ends failed leaves a named need",
          "dump missing" in (c2["catchment"].get("_ends_need") or ""),
          c2["catchment"].get("_ends_need"))
    c3 = contract_from_forecast(fixture_fc())
    check("no profiles passed still names the need",
          "deck_from_cases" in (c3["catchment"].get("_ends_need") or ""),
          c3["catchment"].get("_ends_need"))
    return c


def test_fill_forecast_table():
    """REWRITTEN 19 August 2026, twice. First for the mapping fix (the old expectations
    asserted the mixed-bases patching that printed -80.6% growth), then for the basis
    fix: the p2p row now prints BOTH DIRECTIONS like the connecting legs and the grand
    total around it, because the each-way row failed the sum a network planner does in
    the room (29.5 + 54.5 + 17.7 against 131.2 on the Starlux pack). natural and
    p2p_carried are each-way payload keys, so the row prints at twice each of them.
    app/test_contract_p2p_row.py carries the full suite; this checks the deck side."""
    contract = {"segment_forecast": {"summary": {
        "point_to_point_total": {"base_annual_demand": 100000,
                                 "demand_after_stimulation": 138000,
                                 "demand_at_service_year": None,
                                 "_demand_at_service_year_need": "x",
                                 "forecast": 50000},
        "connecting_at_hub_total": {"base_annual_demand": 900000, "forecast": 15000},
        "grand_total": {"forecast": 65000}}}}
    fc = {"demand": {"stimulation": 1.15, "natural": 120000, "p2p_carried": 50000},
          "schedule": {"growth_rate": 0.0954, "growth_years": 2}}
    _fill_forecast_table(contract, fc)
    blk = contract["segment_forecast"]["summary"]["point_to_point_total"]
    check("service-year column is the grown market, both directions",
          blk["demand_at_service_year"] == 240000, blk["demand_at_service_year"])
    check("the fill clears the need note",
          "_demand_at_service_year_need" not in blk, "")
    check("growth is the payload's cumulative rate, one basis",
          abs(blk["annual_growth_rate"] - 0.2) < 0.001, blk["annual_growth_rate"])
    check("base decomposed from the grown market, both directions",
          abs(blk["base_annual_demand"] - 200000) < 100, blk["base_annual_demand"])
    check("the row multiplies through (effective capture)",
          abs(blk["demand_at_service_year"] * blk["stimulation_factor"]
              * blk["capture_rate"] - blk["forecast"]) < 600, blk["capture_rate"])
    check("forecast is twice the each-way carried figure",
          blk["forecast"] == 100000, blk["forecast"])
    cnx = contract["segment_forecast"]["summary"]["connecting_at_hub_total"]
    check("connecting leg carries x1.00, not the p2p factor",
          cnx["stimulation_factor"] == 1.0, cnx["stimulation_factor"])
    check("connecting base decomposed on the same basis",
          abs(cnx["base_annual_demand"] - 750000) < 500, cnx["base_annual_demand"])


def test_connecting_demand_column_completes():
    """20 August 2026 (John, checking the EVA pack): the demand column's All-other row
    was left blank on the belief that a city's own O&D size does not sum to anything
    meaningful. Checked against the pipeline and it does: catchment_headline's
    connecting_market_over_hub is the full uncapped market, the same source the printed
    cities' own annual_demand figures come from, additive with them.

    Fixture updated same day, later: connecting_market_over_hub is now doubled to two-way
    at the source (Deck Generator/deck_contract.py, the basis fix for Jol's "719,500 both
    directions... but this says each way" catch), so the fixture states it two-way
    (1,438,972 = 719,486 x 2) and _connecting() halves it back to each way before summing
    against the each-way city rows, matching the forecast leg's own /2.0 treatment. The
    expected each-way outputs below are unchanged."""
    contract = {"route_metadata": {"service_year": 2027,
                                    "catchment_headline": {"connecting_market_over_hub": 1438972}},
                "segment_forecast": {"summary": {
                    "connecting_at_hub_total": {"forecast": 58126}}},
                "connecting_at_hub": {"hub": "TPE", "cities": [
                    {"nr": 1, "city_code": "MNL", "city_name": "Manila", "country": "PH",
                     "annual_demand": 80392, "airline_share": 0.0295, "annual_forecast": 3635, "pdew": 5.0},
                    {"nr": 2, "city_code": "SGN", "city_name": "Ho Chi Minh City", "country": "VN",
                     "annual_demand": 78970, "airline_share": 0.0295, "annual_forecast": 3571, "pdew": 4.9},
                ]}}
    tbl = FP._connecting(contract, "connecting_at_hub", "Connecting at TPE (beyond the destination)")
    rows = tbl["table"]["rows"]
    check("all-other demand completes to the market total, each way",
          rows[-2][4] == "560,124", rows[-2][4])   # 719486 - (80392+78970)
    check("total row's demand equals the full market, each way",
          rows[-1][4] == "719,486", rows[-1][4])
    check("forecast column unaffected, still completes to the two-way leg / 2",
          rows[-1][6] == "29,063", rows[-1][6])


def test_connecting_all_other_row():
    """20 August 2026 (Mark Kiehl/SJC): the fifteen printed rows summed to about a third
    of the summary page's carried leg (his own check, page 43 v page 45), because the
    subtitle disclosed the gap in prose but the table itself did not. Mirrors the Excel
    Connecting-feed fix: an All-other row completes the forecast/PDEW columns to the
    carried leg; the demand column stays honestly blank on that row, a market's own
    O&D size not being additive with the leg."""
    contract = {"route_metadata": {"service_year": 2027},
                "segment_forecast": {"summary": {
                    "connecting_at_hub_total": {"forecast": 58126}}},  # two-way, per the contract
                "connecting_at_hub": {"hub": "TPE", "cities": [
                    {"nr": 1, "city_code": "MNL", "city_name": "Manila", "country": "PH",
                     "annual_demand": 80392, "airline_share": 0.0295, "annual_forecast": 3635, "pdew": 5.0},
                    {"nr": 2, "city_code": "SGN", "city_name": "Ho Chi Minh City", "country": "VN",
                     "annual_demand": 78970, "airline_share": 0.0295, "annual_forecast": 3571, "pdew": 4.9},
                ]}}
    tbl = FP._connecting(contract, "connecting_at_hub", "Connecting at TPE (beyond the destination)")
    rows = tbl["table"]["rows"]
    check("all-other row present", rows[-2][2] == "All other connecting markets", rows[-2])
    check("all-other forecast completes the gap",
          rows[-2][6] == "21,857", rows[-2][6])   # 29063 each-way leg - (3635+3571) shown
    check("total row present and bolded", tbl["table"].get("total") is True)
    check("total row's forecast equals the carried leg, each way",
          rows[-1][6] == "29,063", rows[-1][6])
    check("demand column stays honest on the all-other row (never a fabricated sum)",
          rows[-2][4] == "-", rows[-2][4])
    check("subtitle states both the shown figure and the reconciled leg",
          "3,206" not in tbl.get("subtitle", "") and "29,063" in tbl.get("subtitle", ""),
          tbl.get("subtitle"))


def test_process_figure(tmp):
    """The 19 August process page: drawn from the contract's own figures, both
    directions, and dropped rather than drawn when a leg is missing."""
    c = {"segment_forecast": {"summary": {
            "point_to_point_total": {"base_annual_demand": 321833,
                                     "annual_growth_rate": 0.1832,
                                     "demand_at_service_year": 380790,
                                     "stimulation_factor": 1.15,
                                     "demand_after_stimulation": 437909,
                                     "capture_rate": 0.1347, "forecast": 58970},
            "connecting_at_hub_total": {"demand_at_service_year": 719486,
                                        "capture_rate": 0.0758, "forecast": 54518},
            "connecting_at_destination_total": {"forecast": 17698},
            "grand_total": {"forecast": 131186}}},
         "summary_and_schedule": {"connecting_market_over_hub": 719486,
                                  "connecting_market_over_destination": 185485,
                                  "schedule": [{"sector": "TOTAL", "annual_seats": 159120}]},
         "route_metadata": {"base_year": 2025, "service_year": 2027,
                            "origin_airport": "SJC"},
         "connecting_at_hub": {"hub": "TPE"},
         "economics_year1": {"total_load_factor": 0.824}}
    img = FP.render_process(c, os.path.join(tmp, "maps"), codename="proc")
    check("process figure drawn", bool(img) and os.path.exists(img), img)
    pages = FP._method_pages(c, {"process": img})
    subs = [p.get("subtitle") or "" for p in pages]
    check("process page in the methodology set",
          any("How the forecast is built" in s for s in subs), subs[:2])
    c2 = {"segment_forecast": {"summary": {"point_to_point_total": {"forecast": 1}}}}
    check("missing figures drop the page, never invented",
          FP.render_process(c2, os.path.join(tmp, "maps")) is None, "")


def test_build_pack(tmp):
    ends = {"origin": fixture_profile("SJC", "San Jose", 37.36, -121.93),
            "destination": fixture_profile("TPE", "Taipei", 25.08, 121.23, drive=False)}
    c = contract_from_forecast(fixture_fc(), catchment_ends=ends)
    # maps rendered for real when basemap is present; the pack must also build without
    try:
        maps = FP.render_maps(c, os.path.join(tmp, "maps"), codename="testpack")
    except Exception as e:                                   # noqa: BLE001
        maps = {}
        print("   (maps not rendered here: %s)" % e)
    have_basemap = True
    try:
        import mpl_toolkits.basemap                          # noqa: F401
    except Exception:
        have_basemap = False
    if have_basemap:
        check("route map drawn", os.path.exists(maps.get("route", "")), maps.get("route"))
        check("origin catchment map drawn",
              os.path.exists(maps.get("catchment_origin", "")), "")
        check("destination catchment map drawn",
              os.path.exists(maps.get("catchment_destination", "")), "")
    spec, dropped = FP.build_pack(c, codename="Test", prepared_for="Test Client",
                                  maps=maps)
    titles = [s.get("title") or "" for s in spec["slides"]]
    check("catchment page per end",
          any("catchment at SJC" in t for t in titles)
          and any("catchment at TPE" in t for t in titles), titles[-3:])
    if maps.get("route"):
        check("route page present with its map", any(t == "The route" for t in titles), "")
    else:
        check("route page dropped without its map", "the route" in dropped, dropped)
    check("competition dropped by name (no alliance data)",
          "competition" in dropped, dropped)
    check("prior-comparison dropped by name",
          "this forecast against the last" in dropped, dropped)
    # no maps at all: the catchment pages keep their population tables
    spec2, dropped2 = FP.build_pack(c, codename="Test", maps=None)
    t2 = [s.get("title") or "" for s in spec2["slides"]]
    check("population tables survive without maps",
          any("catchment at SJC" in t for t in t2), "")
    check("route page dropped cleanly without maps", "the route" in dropped2, "")
    # a contract with NO ends falls back to the old zones behaviour with the need stated
    c_no = contract_from_forecast(fixture_fc())
    spec3, dropped3 = FP.build_pack(c_no, codename="Test", maps=None)
    t3 = [s.get("title") or "" for s in spec3["slides"]]
    check("no ends falls back to the zones table",
          any(t == "The catchment" for t in t3) or "catchment" in dropped3, t3[-2:])
    import deck_spec as S
    S.paginate(spec)
    return spec, maps


def test_render(spec, tmp):
    """Prove the spec renders to a pptx, safe fonts, no resolver."""
    try:
        import render_pptx as RPX
    except Exception as e:                                   # noqa: BLE001
        print("   (render not tested here: %s)" % e)
        return
    out = os.path.join(tmp, "pack.pptx")
    try:
        RPX.render(spec, out, safe_fonts=True, resolver=None)
        check("pack renders to pptx", os.path.exists(out) and os.path.getsize(out) > 10000,
              os.path.getsize(out) if os.path.exists(out) else "missing")
    except Exception as e:                                   # noqa: BLE001
        check("pack renders to pptx", False, "%s: %s" % (type(e).__name__, e))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_contract_ends()
        test_fill_forecast_table()
        test_connecting_all_other_row()
        test_connecting_demand_column_completes()
        test_process_figure(tmp)
        spec, _maps = test_build_pack(tmp)
        test_render(spec, tmp)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
