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
    """REWRITTEN 19 August 2026 with the mapping fix: the old expectations asserted
    the mixed-bases patching (captured-after-stim divided by the factor against the
    two-way market) that printed -80.6% growth on a real contract. The row is now SET
    from the payload on one each-way basis; app/test_contract_p2p_row.py carries the
    full 11-check suite, and this checks the deck-side essentials."""
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
    check("service-year column is the payload's grown market",
          blk["demand_at_service_year"] == 120000, blk["demand_at_service_year"])
    check("the fill clears the need note",
          "_demand_at_service_year_need" not in blk, "")
    check("growth is the payload's cumulative rate, one basis",
          abs(blk["annual_growth_rate"] - 0.2) < 0.001, blk["annual_growth_rate"])
    check("base decomposed from the grown market",
          abs(blk["base_annual_demand"] - 100000) < 100, blk["base_annual_demand"])
    check("the row multiplies through (effective capture)",
          abs(blk["demand_at_service_year"] * blk["stimulation_factor"]
              * blk["capture_rate"] - blk["forecast"]) < 300, blk["capture_rate"])
    cnx = contract["segment_forecast"]["summary"]["connecting_at_hub_total"]
    check("connecting leg carries x1.00, not the p2p factor",
          cnx["stimulation_factor"] == 1.0, cnx["stimulation_factor"])
    check("connecting base decomposed on the same basis",
          abs(cnx["base_annual_demand"] - 750000) < 500, cnx["base_annual_demand"])


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
        spec, _maps = test_build_pack(tmp)
        test_render(spec, tmp)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
