#!/usr/bin/env python3
"""Avia Solutions - verify the PTEW fix (22 August 2026, Jol/Mark's SJC-TPE workbook review).

WHAT WAS WRONG. route_feed.py's per-city PTEW (each city's own row in the Connecting feed detail
sheet, and the dashboard's connecting-feed breakdown) was computed as annual passengers / 365 / 2 -
a flat calendar-day average that ignores how often the route actually flies. The Forecast tab's
aggregate PTEW is annual passengers / actual scheduled departures (freq x weeks). On a route that
does not fly daily, like this 5x/week CI service, those two numbers were never going to agree: on
the exported workbook, SJC-behind's per-city figures summed to 13.1 against the Forecast tab's 36;
TPE-beyond's summed to 45.9 against 112.

THE FIX. route_feed.py now has a single _ptew() helper, called from all four places pdew used to be
computed inline (feed_side's QSI and flat-capture branches, behind_feed's same two). It divides by
the route's actual freq x season_weeks when the caller supplies them, and route_forecast.py now
passes its own freq/season_weeks through to both feed_side() and behind_feed() calls, so every
production run uses the real schedule, not a flat 365 days. Falls back to the old 365/2 basis only
when freq is not supplied (callers with no defined route yet) - no production caller should ever
hit that fallback.

WHAT THIS SCRIPT CHECKS. Sums the per-city PTEW for both connecting legs (now fixed) and compares
against the SAME aggregate PTEW the Forecast tab computes (captured / (freq x season_weeks)) - not
exact (15-16 independently-rounded city figures will not sum to the exact rounded aggregate) but
should now be the same ORDER OF MAGNITUDE, not off by a factor of ~2.7-3x as before the fix.

Run on the workstation:
    py -3.12 diag_ptew_fix_check.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")

import route_forecast as RFC          # patch BEFORE cortex_app is imported/called

_captured = {}
_orig_forecast = RFC.forecast


def _capturing_forecast(*args, **kwargs):
    r = _orig_forecast(*args, **kwargs)
    _captured.update(r)
    return r


RFC.forecast = _capturing_forecast

import cortex_app as CA                # imports route_forecast -> gets the patched module


def check_leg(label, detail, feed_total, freq, season_weeks):
    if not detail:
        print(f"{label}: STOP - detail dict is empty, cannot check.")
        return
    per_city_sum = sum((v.get("pdew") or 0) for v in detail.values())
    dep_per_year = freq * season_weeks
    aggregate_ptew = round(feed_total / dep_per_year, 1) if dep_per_year else 0.0
    print(f"{label}:")
    print(f"  sum of per-city PTEW (fixed):  {per_city_sum:.1f}")
    print(f"  aggregate PTEW (feed/{freq:.0f}x{season_weeks:.0f}wk): {aggregate_ptew:.1f}")
    ratio = per_city_sum / aggregate_ptew if aggregate_ptew else None
    if ratio is None:
        print("  cannot compute a ratio (aggregate PTEW is 0)")
    elif 0.85 <= ratio <= 1.15:
        print(f"  ratio {ratio:.2f} - within a normal rounding gap for {len(detail)} independently-"
              f"rounded rows. Fix looks right.")
    else:
        print(f"  ratio {ratio:.2f} - still off by more than rounding noise should explain. "
              f"STOP - do not trust the fix without investigating further.")
    print()


def main():
    fc = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC", aircraft="A359", freq=5)
    if not fc.get("ok"):
        print(f"Production call failed: {fc.get('error')}. STOP.")
        return
    d = _captured
    if not d:
        print("STOP: monkeypatch did not capture a route_forecast.forecast() call.")
        return

    freq = d.get("frequency")
    beyond_detail = d.get("beyond_detail") or {}
    behind_detail = d.get("behind_detail") or {}
    feed_beyond = d.get("feed_beyond")
    feed_behind = d.get("feed_behind")
    season_weeks = 52.0   # route_forecast.py's own default; this run did not override it

    missing = [k for k, v in [("frequency", freq), ("feed_beyond", feed_beyond),
                               ("feed_behind", feed_behind)] if v is None]
    if missing:
        print(f"STOP: forecast()'s return dict is missing {missing}.")
        print(f"Actual keys returned: {sorted(d.keys())}")
        return

    print(f"freq={freq}/week, season_weeks={season_weeks:.0f} -> {freq * season_weeks:.0f} scheduled "
          f"departures/year each way\n")

    check_leg("Connecting behind SJC", behind_detail, feed_behind, freq, season_weeks)
    check_leg("Connecting beyond TPE", beyond_detail, feed_beyond, freq, season_weeks)

    print("Before the fix (from the (28) export, 22 August): SJC per-city sum 13.1 vs aggregate 36 "
          "(ratio 0.36); TPE per-city sum 45.9 vs aggregate 112 (ratio 0.41). Compare the ratios above "
          "against those to see the fix's effect directly.")


if __name__ == "__main__":
    main()
