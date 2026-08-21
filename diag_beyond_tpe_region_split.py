#!/usr/bin/env python3
"""Avia Solutions - Jol's 21 August ask: 2-way connecting O&D demand beyond Taipei,
grouped China (incl. Hong Kong) vs SE Asia, for CI/BR/JX on SJC-TPE.

REWRITE, 21 August, after the first version's own cross-check failed. That version read
fc["demand"]["beyond_pdew"], which is cortex_app._feed_list()'s OUTPUT - even with
AVIA_FEED_TOP=999 removing the top-N truncation, _feed_list() still applies
`if pv <= 0: continue`, silently dropping every city where THIS airline's captured share
is zero or negative. Starlux doesn't capture Beijing or Guangzhou (a capture-level, not a
market-level, fact), so those cities vanished from JX's list while staying in CI/BR's -
which is exactly why the first run's disagreement warning fired (35/33/29 cities,
China two-way 366,460/359,466/329,840). That was my bug, not a real market difference.

THE FIX. route_forecast.forecast() (RF.forecast, called inside cortex_app.calibrated_
forecast()) builds and returns "beyond_detail" and "behind_detail" as raw dicts BEFORE
_feed_list() touches them - keyed by IATA city code, each value {"base": market size,
"share": this airline's capture}. "base" comes from route_feed.feed_side()'s `market`
dict, which is built from scope (hub_served + on_the_way, airport-geometry only) and
_OS.feed_market(...) (Sabre beyond-TPE O&D volume) - neither step takes an `airline`
argument, so "base" should be identical across CI/BR/JX. Confirmed by testing here: this
version reads the raw dict directly and checks all three airlines actually agree before
printing an answer.

calibrated_forecast() does not return beyond_detail/behind_detail to its caller (only the
filtered beyond_pdew/behind_pdew survive to the fc dict), so the raw dicts are captured by
monkeypatching route_forecast.forecast() to record its return value before calibrated_
forecast() reads it. This is import-order dependent: route_forecast must be patched BEFORE
cortex_app.calibrated_forecast() is called, which is why the patch happens at module load,
above the region_split() calls.

growth/growth_years default to 0.0/0, so with no forecast_year passed the run returns the
BASE YEAR (2025) figures directly, matching Jol's definition ("O&D demand Jan-Dec 2025
Sabre MI data") with no back-calculation needed. Country tagging uses route_engine.
_airports() (airportsdata's IATA table), the same lookup Meridian itself uses.

    py -3.12 diag_beyond_tpe_region_split.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")

import route_forecast as RFC          # patch this BEFORE cortex_app is imported/called
import route_engine as RE

_captured = {}
_orig_forecast = RFC.forecast


def _capturing_forecast(*args, **kwargs):
    r = _orig_forecast(*args, **kwargs)
    _captured["beyond_detail"] = r.get("beyond_detail") or {}
    _captured["behind_detail"] = r.get("behind_detail") or {}
    return r


RFC.forecast = _capturing_forecast

import cortex_app as CA               # imports route_forecast as RF -> gets the patched module

AP = RE._airports()
CHINA_HK = {"CN", "HK"}
SE_ASIA = {"PH", "VN", "TH", "SG", "ID", "MY"}


def region_split(airline, label):
    _captured.clear()
    fc = CA.calibrated_forecast("SJC", "TPE", airline=airline, carrier_type="FSC",
                                 aircraft="A359", freq=5)
    if not fc.get("ok"):
        print(f"{label}: forecast failed: {fc.get('error')}")
        return None
    if not _captured.get("beyond_detail"):
        print(f"{label}: monkeypatch did not capture beyond_detail - route_forecast import "
              f"order is wrong, or the return key has changed. STOP, do not trust any total "
              f"below.")
        return None
    beyond = _captured["beyond_detail"]
    print(f"\n{label}: {len(beyond)} cities in the RAW, unfiltered beyond-TPE market map "
          f"(pre-_feed_list, so this should be airline-invariant)")
    china_ew = se_ew = other_ew = 0.0
    other_names = []
    for code, row in beyond.items():
        base = float((row or {}).get("base") or 0)
        rec = AP.get((code or "").strip().upper())
        country = ((rec or {}).get("country") or "").upper()
        if country in CHINA_HK:
            china_ew += base
        elif country in SE_ASIA:
            se_ew += base
        else:
            other_ew += base
            if base > 5000:
                other_names.append((code, country, round(base)))
    print(f"  China (incl. HK): each-way {china_ew:,.0f}  two-way {china_ew * 2:,.0f}")
    print(f"  SE Asia:          each-way {se_ew:,.0f}  two-way {se_ew * 2:,.0f}")
    print(f"  Other (Korea, Japan, etc.): each-way {other_ew:,.0f}  two-way {other_ew * 2:,.0f}")
    if other_names:
        print("  Largest 'other' markets, for reference:")
        for c, ctry, v in sorted(other_names, key=lambda x: -x[2])[:8]:
            print(f"    {c} ({ctry}): {v:,}")
    return round(china_ew), round(se_ew)


if __name__ == "__main__":
    print("Raw, unfiltered beyond-TPE market map - bypasses cortex_app._feed_list()'s "
          "pv<=0 and top-N filters, which drop capture-zero cities per airline and were the "
          "cause of the first run's disagreement. Base year (no growth/forecast_year "
          "passed), each figure doubled for two-way.")
    print("Defined as: O&D demand Jan-Dec 2025, Sabre MI data, 2-way, SJC catchment.\n")
    results = {}
    for al in ("CI", "BR", "JX"):
        r = region_split(al, al)
        if r:
            results[al] = r
    if len(set(results.values())) > 1:
        print("\nWARNING: the three airlines still do NOT agree on the raw, unfiltered map. "
              "That rules out the _feed_list truncation/filter as the cause - something "
              "upstream of beyond_detail (scope, hub_served, on_the_way, or feed_market "
              "itself) is airline-dependent when it should not be. Do not send this to Jol; "
              "the mechanism needs tracing in route_feed.feed_side() before any number is "
              "trustworthy.")
    elif results:
        china_ew, se_ew = next(iter(results.values()))
        print(f"\nOne market figure, all three airlines agree: "
              f"China (incl. HK) {china_ew * 2:,.0f} two-way, SE Asia {se_ew * 2:,.0f} two-way.")
    else:
        print("\nNo results returned - see per-airline errors above.")
