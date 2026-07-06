#!/usr/bin/env python3
"""
Avia Solutions - water-boundary check for the catchment engine.
================================================================
The catchment's offline default estimates drive time from great-circle distance x road
factor, which happily drives across the sea: STT (US Virgin Islands, pop ~80k) pulled a
2m catchment because Puerto Rico is 60km away over open water; IBZ pulled the Spanish
mainland (Jessica Rowden, 3 Jul 2026). That inflates the island airport's P2P market and
distorts the airport-choice allocation.

Fix: before trusting a great-circle drive-time ESTIMATE, sample the straight line between
locale and airport against a land/sea mask and measure the LONGEST CONTIGUOUS WATER GAP.
If it exceeds a bridge-scale threshold (default 20 km: allows the Oresund and Storebaelt
crossings, Confederation Bridge, causeways, estuaries and rivers; excludes true island
separations like STT-Puerto Rico ~60 km and IBZ-mainland ~85 km) the pair is unreachable
by road and is excluded from the catchment. Uploaded drive-time matrices are NEVER
second-guessed: a real matrix already knows about roads, bridges and ferries.

Depends on `global-land-mask` (pip install global-land-mask; a small offline 1-km land
grid). FAILS OPEN: if the package is missing, behaviour is exactly as before and a
one-time warning is printed, so nothing breaks on machines without it.
"""
import math
import os
from functools import lru_cache

_MASK = None          # 0 = not tried, None-after-fail handled via _MASK_FAILED
_MASK_FAILED = False
_WARNED = False


def _globe():
    """Lazy import of the land mask; fail open (None) if unavailable.

    AVIA_WATER_CHECK=0 (or false/off/no) forces the check OFF regardless of whether the mask is
    installed. Use it to reproduce a run made before global-land-mask was installed - e.g. the
    bt_v1_6yr.csv baseline was generated fail-open, so an identity check against it must set this."""
    global _MASK, _MASK_FAILED, _WARNED
    if os.environ.get("AVIA_WATER_CHECK", "1").strip().lower() in ("0", "false", "off", "no"):
        if not _WARNED:
            print("water_check: AVIA_WATER_CHECK=0 - water-boundary check forced OFF (fail-open)")
            _WARNED = True
        _MASK_FAILED = True
        return None
    if _MASK is not None:
        return _MASK
    if _MASK_FAILED:
        return None
    try:
        from global_land_mask import globe
        _MASK = globe
        return _MASK
    except Exception:
        _MASK_FAILED = True
        if not _WARNED:
            print("water_check: global-land-mask not installed - water-boundary check OFF "
                  "(pip install global-land-mask to enable; island catchments will over-read)")
            _WARNED = True
        return None


def _gc_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def max_water_gap_km(lat1, lon1, lat2, lon2, step_km=2.0):
    """Longest contiguous stretch of open water (km) on the straight line between two points,
    sampled every ~step_km. Returns None when the land mask is unavailable (caller fails open).
    Endpoints are forced to 'land' so a coastal locale/airport pixel on water doesn't count."""
    globe = _globe()
    if globe is None:
        return None
    dist = _gc_km(lat1, lon1, lat2, lon2)
    if dist <= step_km:
        return 0.0
    n = max(int(dist / step_km), 2)
    # PERF: sample all interior points in one vectorised is_land call (was a per-point Python loop,
    # ~50s/route in the catchment). Same points, same booleans, so gaps are identical - pure speed.
    try:
        import numpy as np
        f = np.arange(1, n) / n                                     # interior points only
        lats = lat1 + (lat2 - lat1) * f
        lons = lon1 + (lon2 - lon1) * f                             # fine for catchment-scale distances
        on_land = np.asarray(globe.is_land(lats, lons), dtype=bool)
    except Exception:
        return None
    seg = dist / n                             # km spanned by each interior step
    worst = run = 0.0
    for water in on_land == False:             # longest contiguous water run; array ops only, no is_land
        if water:
            run += seg
            if run > worst:
                worst = run
        else:
            run = 0.0
    return worst


@lru_cache(maxsize=200000)
def _cached_gap(lat1, lon1, lat2, lon2):
    return max_water_gap_km(lat1, lon1, lat2, lon2)


def road_reachable(lat1, lon1, lat2, lon2, max_gap_km=20.0):
    """True if the pair is plausibly connected by road: no water gap beyond bridge scale.
    Fails open (True) when the mask is unavailable. Coordinates are rounded to ~100 m for
    the cache, which is far finer than locale centroids."""
    if None in (lat1, lon1, lat2, lon2):
        return True
    gap = _cached_gap(round(lat1, 3), round(lon1, 3), round(lat2, 3), round(lon2, 3))
    if gap is None:
        return True
    return gap <= max_gap_km


if __name__ == "__main__":
    # the reported cases + bridge-scale controls
    cases = [
        ("STT (St Thomas) <- San Juan PR", 18.337, -64.973, 18.44, -66.00),
        ("IBZ (Ibiza) <- Valencia mainland", 38.873, 1.373, 39.47, -0.38),
        ("IBZ <- Ibiza town (same island)", 38.873, 1.373, 38.907, 1.42),
        ("CPH area <- Malmo (Oresund bridge)", 55.63, 12.65, 55.60, 13.00),
        ("LHR <- Reading (all land)", 51.470, -0.454, 51.454, -0.978),
    ]
    for name, a, b, c, d in cases:
        gap = max_water_gap_km(a, b, c, d)
        ok = road_reachable(a, b, c, d)
        print(f"{name:42} water gap {('%.1f km' % gap) if gap is not None else 'n/a':>10}  "
              f"reachable(20km): {ok}")
