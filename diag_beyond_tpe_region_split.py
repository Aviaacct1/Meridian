#!/usr/bin/env python3
"""Avia Solutions - Jol's 21 August ask: 2-way connecting O&D demand beyond Taipei,
grouped China (incl. Hong Kong) vs SE Asia, for CI/BR/JX on SJC-TPE.

WHY THIS IS A SEPARATE PULL, not a re-read of the packs. The Excel/PPTX outputs cap
the beyond-TPE city list at fifteen (AVIA_FEED_TOP's default), ranked by each
airline's OWN capture, not by market size. Starlux doesn't serve Beijing or
Guangzhou well, so those cities fall out of Starlux's top fifteen and disappear into
an unnamed "All other" tail - which makes a region total built from the packs
airline-dependent, when the underlying market is not: China and SE Asia demand
beyond Taipei is a property of the market, the same regardless of which airline is
asking, exactly like the 719,486 total connecting-beyond-TPE figure already is
identical across all three. Confirmed by running the packs' own top-15 lists through
this same region split first: Starlux's China figure came out at 160,062 two-way
against CI/BR's 271,890, an artefact of whose top-15 happened to keep Beijing and
Guangzhou visible, not a real difference in the China market.

THE FIX. AVIA_FEED_TOP, set high, returns cortex_app.calibrated_forecast()'s
beyond_pdew/behind_pdew lists UNTRUNCATED (see cortex_app.py's own comment: "Set in a
shell session before deck_from_cases when a piece of work needs the full beyond/
behind market list, e.g. the SJC research deck's top-15-to-China chart" - this is
that exact use case). growth/growth_years default to 0.0/0, so with no forecast_year
passed the run returns the BASE YEAR (2025) figures directly, matching Jol's
definition ("O&D demand Jan-Dec 2025 Sabre MI data") with no back-calculation needed.
"base" in the per-city detail is the market's own O&D size, airline-invariant (it is
the airline's CAPTURE that varies, not the market), so one run (any of the three
airlines) is sufficient for the market-level regional totals; run twice as a check.

    set AVIA_FEED_TOP=999
    py -3.12 diag_beyond_tpe_region_split.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")
os.environ.setdefault("AVIA_FEED_TOP", "999")

import cortex_app as CA

CHINA_HK = {"CN", "HK"}
SE_ASIA = {"PH", "VN", "TH", "SG", "ID", "MY"}


def region_split(airline, label):
    fc = CA.calibrated_forecast("SJC", "TPE", airline=airline, carrier_type="FSC",
                                 aircraft="A359", freq=5)
    if not fc.get("ok"):
        print(f"{label}: forecast failed: {fc.get('error')}")
        return None
    dem = fc["demand"]
    beyond = dem.get("beyond_pdew") or []
    print(f"\n{label}: {len(beyond)} cities returned beyond TPE "
          f"(AVIA_FEED_TOP={os.environ.get('AVIA_FEED_TOP')}; expect ~15 if the env "
          f"var did not take)")
    china_ew = se_ew = other_ew = 0.0
    other_names = []
    for row in beyond:
        base = float(row.get("base") or 0)
        country = (row.get("country") or "").upper()
        if country in CHINA_HK:
            china_ew += base
        elif country in SE_ASIA:
            se_ew += base
        else:
            other_ew += base
            if base > 5000:
                other_names.append((row.get("name") or row.get("code"), country, round(base)))
    print(f"  China (incl. HK): each-way {china_ew:,.0f}  two-way {china_ew*2:,.0f}")
    print(f"  SE Asia:          each-way {se_ew:,.0f}  two-way {se_ew*2:,.0f}")
    print(f"  Other (Korea, Japan, etc.): each-way {other_ew:,.0f}  two-way {other_ew*2:,.0f}")
    if other_names:
        print("  Largest 'other' markets, for reference:")
        for n, c, v in sorted(other_names, key=lambda x: -x[2])[:8]:
            print(f"    {n} ({c}): {v:,}")
    return china_ew, se_ew


if __name__ == "__main__":
    print("Base year (no growth/forecast_year passed), each figure doubled for two-way.")
    print("Defined as: O&D demand Jan-Dec 2025, Sabre MI data, 2-way, SJC catchment.\n")
    results = {}
    for al in ("CI", "BR", "JX"):
        r = region_split(al, al)
        if r:
            results[al] = r
    if len(set(results.values())) > 1:
        print("\nWARNING: the three airlines did NOT return the same market totals. "
              "That should not happen for a market-level (not capture-level) figure - "
              "check the run before sending this to Jol.")
    elif results:
        china_ew, se_ew = next(iter(results.values()))
        print(f"\nOne market figure, all three airlines agree: "
              f"China (incl. HK) {china_ew*2:,.0f} two-way, SE Asia {se_ew*2:,.0f} two-way.")
