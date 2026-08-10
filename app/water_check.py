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


# ---------------------------------------------------------------- land path (added 10 August 2026)
# WHY THIS EXISTS. The straight-line gap above answers "does the direct line cross water", and that
# was read as "is there a road". For an island the two are the same question. For a BAY they are not.
# Measured 10 August 2026: the straight line from San Jose to Monterey crosses 36.3 km of Monterey
# Bay, over the 20 km threshold, so Monterey was cut from the San Jose catchment. US-101 runs the
# whole way on land through Gilroy and Salinas. A real Central Coast competitor was deleted by a rule
# written for St Thomas and Ibiza. Santa Rosa cleared the same test by four kilometres, so the margin
# was luck rather than design.
#
# The fix is to ask the question the rule was always trying to ask: is there a way round. A land path
# is searched on the same mask, and the pair is reachable if one exists without an unreasonable
# detour. Only run when the straight line has ALREADY failed, so the fast path is untouched, and it
# can only ever turn a False into a True. No airport that is in a catchment today can leave it
# because of this change.
LAND_STEP_KM = 3.0        # grid resolution of the path search; a land bridge narrower than this is missed
MAX_DETOUR = 3.0          # a road may be three times the direct distance; beyond that call it unreachable
_MAX_CELLS = 400000       # grid ceiling; coarsen rather than stall


def land_path_km(lat1, lon1, lat2, lon2, step_km=LAND_STEP_KM, max_detour=MAX_DETOUR):
    """Length (km) of the shortest path over LAND between two points, or None if there is none
    within the detour allowance. None also when the mask is unavailable, so the caller decides."""
    globe = _globe()
    if globe is None:
        return None
    try:
        import heapq
        import numpy as np
    except Exception:
        return None
    direct = _gc_km(lat1, lon1, lat2, lon2)
    if direct <= step_km:
        return direct
    # Box padded so a route round an obstacle has room, and coarsened rather than allowed to explode.
    pad_km = max(0.75 * direct, 25.0)
    km_per_deg_lat = 111.32
    mid_lat = math.radians((lat1 + lat2) / 2.0)
    km_per_deg_lon = max(111.32 * math.cos(mid_lat), 1e-6)
    while True:
        lat_lo = min(lat1, lat2) - pad_km / km_per_deg_lat
        lat_hi = max(lat1, lat2) + pad_km / km_per_deg_lat
        lon_lo = min(lon1, lon2) - pad_km / km_per_deg_lon
        lon_hi = max(lon1, lon2) + pad_km / km_per_deg_lon
        n_lat = int((lat_hi - lat_lo) * km_per_deg_lat / step_km) + 1
        n_lon = int((lon_hi - lon_lo) * km_per_deg_lon / step_km) + 1
        if n_lat * n_lon <= _MAX_CELLS or step_km > 50.0:
            break
        step_km *= 2.0
    if n_lat < 2 or n_lon < 2:
        return None
    lats = np.linspace(lat_lo, lat_hi, n_lat)
    lons = np.linspace(lon_lo, lon_hi, n_lon)
    grid_lat, grid_lon = np.meshgrid(lats, lons, indexing="ij")
    try:
        land = np.asarray(globe.is_land(grid_lat, grid_lon), dtype=bool)
    except Exception:
        return None
    cell = lambda la, lo: (int(round((la - lat_lo) / (lat_hi - lat_lo) * (n_lat - 1))),
                           int(round((lo - lon_lo) / (lon_hi - lon_lo) * (n_lon - 1))))
    src, dst = cell(lat1, lon1), cell(lat2, lon2)
    # An airport or a locale centroid can land in a water pixel at 1 km resolution without being at
    # sea, so both endpoints are forced to land rather than the search failing on a rounding.
    land[src] = True
    land[dst] = True
    dy = (lat_hi - lat_lo) / (n_lat - 1) * km_per_deg_lat
    dx = (lon_hi - lon_lo) / (n_lon - 1) * km_per_deg_lon
    steps = [(-1, 0, dy), (1, 0, dy), (0, -1, dx), (0, 1, dx),
             (-1, -1, math.hypot(dy, dx)), (-1, 1, math.hypot(dy, dx)),
             (1, -1, math.hypot(dy, dx)), (1, 1, math.hypot(dy, dx))]
    ceiling = max_detour * direct
    best = {src: 0.0}
    heap = [(0.0, src)]
    while heap:
        d, node = heapq.heappop(heap)
        if node == dst:
            return d
        if d > best.get(node, float("inf")) or d > ceiling:
            continue
        i, j = node
        for di, dj, cost in steps:
            ni, nj = i + di, j + dj
            if not (0 <= ni < n_lat and 0 <= nj < n_lon) or not land[ni, nj]:
                continue
            nd = d + cost
            if nd <= ceiling and nd < best.get((ni, nj), float("inf")):
                best[(ni, nj)] = nd
                heapq.heappush(heap, (nd, (ni, nj)))
    return None


@lru_cache(maxsize=50000)
def _cached_land_path(lat1, lon1, lat2, lon2):
    return land_path_km(lat1, lon1, lat2, lon2)


def road_reachable(lat1, lon1, lat2, lon2, max_gap_km=20.0, max_detour=MAX_DETOUR):
    """True if the pair is plausibly connected by road. A short straight-line water gap settles it
    at once; a long one sends the question to the land-path search, because a line across a bay says
    nothing about the road round it. Fails open (True) when the mask is unavailable. Coordinates are
    rounded to ~100 m for the cache, which is far finer than locale centroids."""
    if None in (lat1, lon1, lat2, lon2):
        return True
    a, b, c, d = round(lat1, 3), round(lon1, 3), round(lat2, 3), round(lon2, 3)
    gap = _cached_gap(a, b, c, d)
    if gap is None:
        return True
    if gap <= max_gap_km:
        return True
    path = _cached_land_path(a, b, c, d)
    if path is None:
        # No land route found, or the search could not run. Either way the pre-existing answer
        # stands, which for a genuine island is the right one and is what this module exists for.
        return False
    return path <= max_detour * max(_gc_km(a, b, c, d), 1.0)


if __name__ == "__main__":
    # the reported cases + bridge-scale controls
    cases = [
        ("STT (St Thomas) <- San Juan PR", 18.337, -64.973, 18.44, -66.00, False),
        ("IBZ (Ibiza) <- Valencia mainland", 38.873, 1.373, 39.47, -0.38, False),
        ("IBZ <- Ibiza town (same island)", 38.873, 1.373, 38.907, 1.42, True),
        ("CPH area <- Malmo (Oresund bridge)", 55.63, 12.65, 55.60, 13.00, True),
        ("LHR <- Reading (all land)", 51.470, -0.454, 51.454, -0.978, True),
        # Added 10 August 2026: the bay case the straight-line rule got wrong.
        ("SJC <- MRY (round Monterey Bay)", 37.363, -121.929, 36.587, -121.843, True),
        ("SJC <- STS (Santa Rosa)", 37.363, -121.929, 38.510, -122.813, True),
    ]
    bad = 0
    for name, a, b, c, d, want in cases:
        gap = max_water_gap_km(a, b, c, d)
        path = land_path_km(a, b, c, d)
        ok = road_reachable(a, b, c, d)
        flag = "" if ok == want else "   <-- EXPECTED %s" % want
        if ok != want:
            bad += 1
        print(f"{name:36} gap {('%.1f km' % gap) if gap is not None else 'n/a':>9}  "
              f"land path {('%.0f km' % path) if path is not None else 'none':>9}  "
              f"reachable: {ok}{flag}")
    print("\n%d of %d as expected" % (len(cases) - bad, len(cases)))
