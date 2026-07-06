#!/usr/bin/env python3
"""
Avia Solutions - road drive-time provider for the catchment engine ("half one").
================================================================================
Replaces the great-circle x road-factor PROXY with real road travel times to each
candidate airport, then CACHES the matrix to disk so it is derived once with internet
and run offline thereafter (laptop / World Routes). The fuller raster-isochrone
population-summing step ("half two", GHS-POP / Kontur) is deliberately deferred until a
real calibration case shows the centroid proxy costs accuracy - see the handover note.

Two routing back-ends, both via stdlib urllib (nothing to pip-install):
  - OSRM   : a public demo server or a self-hosted instance (no key). /table service.
  - ORS    : OpenRouteService matrix (free API key, sign up at openrouteservice.org).

Typical use (online, once):
    locales  = geonames.near_point("cities5000.txt", lat, lon, 120, propensity=0.04)
    airports = [Airport("GOA", lat=44.413, lon=8.838), Airport("MXP", lat=45.630, lon=8.723)]
    build_drive_time_matrix(locales, airports, provider=osrm_table, cache_path="goa_drive.json")

Then offline (every run after):
    load_drive_time_matrix(locales, "goa_drive.json")     # fills loc.drive_min
    run_catchment(locales, airports, CatchmentParams(method="gencost"), home="GOA")

If no cache and no internet, the catchment engine falls back to its great-circle proxy
automatically (drive_min stays empty). A great-circle PROVIDER is also given so the
pluggable hook can be exercised offline.
"""
import json, math, os, time, urllib.request, urllib.parse, urllib.error
from typing import List, Callable, Optional


# ----------------------------------------------------------------- cache keying
def _key(lat: float, lon: float, code: str) -> str:
    """Stable cache key for a (locale point, airport) pair. Rounded to ~11 m so tiny
    coordinate jitter still hits the cache."""
    return f"{round(lat, 4)},{round(lon, 4)}|{code}"


# ----------------------------------------------------------------- HTTP helper
def _get_json(url: str, data: bytes = None, headers: dict = None, timeout: float = 30.0,
              retries: int = 3, pause: float = 1.5) -> dict:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"routing request failed after {retries} tries: {last}")


# ----------------------------------------------------------------- OSRM /table
def osrm_table(locales: List, airports: List, base_url: str = "https://router.project-osrm.org",
               profile: str = "driving", batch: int = 80, pause: float = 1.0) -> dict:
    """Real road minutes via an OSRM /table server. Returns {cache_key: minutes}.
    Batches locales (the public demo limits coordinates per request); all airports ride in
    every batch as the table destinations. Self-host OSRM for production / large runs."""
    aps = [a for a in airports if a.lat is not None and a.lon is not None]
    locs = [l for l in locales if l.lat is not None and l.lon is not None]
    out = {}
    for i in range(0, len(locs), batch):
        chunk = locs[i:i + batch]
        coords = [(l.lon, l.lat) for l in chunk] + [(a.lon, a.lat) for a in aps]
        coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
        src = ";".join(str(j) for j in range(len(chunk)))
        dst = ";".join(str(len(chunk) + j) for j in range(len(aps)))
        url = (f"{base_url}/table/v1/{profile}/{coord_str}"
               f"?sources={src}&destinations={dst}&annotations=duration")
        js = _get_json(url)
        if js.get("code") != "Ok":
            raise RuntimeError(f"OSRM table error: {js.get('code')} {js.get('message','')}")
        durations = js["durations"]   # seconds, [len(chunk)][len(aps)]
        for r, l in enumerate(chunk):
            for c, a in enumerate(aps):
                sec = durations[r][c]
                if sec is not None:
                    out[_key(l.lat, l.lon, a.code)] = sec / 60.0
        time.sleep(pause)
    return out


# ----------------------------------------------------------------- ORS matrix
def ors_matrix(locales: List, airports: List, api_key: str, profile: str = "driving-car",
               batch: int = 45, pause: float = 1.5) -> dict:
    """Real road minutes via the OpenRouteService matrix API (free key). Returns
    {cache_key: minutes}. Batches locales to stay inside the free-tier matrix size."""
    aps = [a for a in airports if a.lat is not None and a.lon is not None]
    locs = [l for l in locales if l.lat is not None and l.lon is not None]
    url = f"https://api.openrouteservice.org/v2/matrix/{profile}"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    out = {}
    for i in range(0, len(locs), batch):
        chunk = locs[i:i + batch]
        locations = [[l.lon, l.lat] for l in chunk] + [[a.lon, a.lat] for a in aps]
        body = json.dumps({
            "locations": locations,
            "sources": list(range(len(chunk))),
            "destinations": [len(chunk) + j for j in range(len(aps))],
            "metrics": ["duration"],
        }).encode("utf-8")
        js = _get_json(url, data=body, headers=headers)
        durations = js["durations"]   # seconds
        for r, l in enumerate(chunk):
            for c, a in enumerate(aps):
                sec = durations[r][c]
                if sec is not None:
                    out[_key(l.lat, l.lon, a.code)] = sec / 60.0
        time.sleep(pause)
    return out


# ----------------------------------------------------------------- great-circle provider
def make_great_circle_provider(avg_speed_kmh: float = 80.0, road_factor: float = 1.30) -> Callable:
    """A per-pair provider matching the engine's offline proxy, for exercising the
    drive_times_from_provider hook without internet. provider(lat1,lon1,lat2,lon2)->minutes."""
    def provider(lat1, lon1, lat2, lon2):
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        km = 2 * 6371.0 * math.asin(math.sqrt(a)) * road_factor
        return (km / avg_speed_kmh) * 60.0
    return provider


def gc_matrix(locales: List, airports: List, avg_speed_kmh: float = 80.0,
              road_factor: float = 1.30, **kw) -> dict:
    """Great-circle proxy in the matrix SHAPE (same return as osrm_table / ors_matrix), so a
    cache can be built and tested fully offline. Use a real provider for production accuracy."""
    prov = make_great_circle_provider(avg_speed_kmh, road_factor)
    out = {}
    for l in locales:
        if l.lat is None or l.lon is None:
            continue
        for a in airports:
            if a.lat is not None and a.lon is not None:
                out[_key(l.lat, l.lon, a.code)] = prov(l.lat, l.lon, a.lat, a.lon)
    return out


# ----------------------------------------------------------------- build / cache / load
def build_drive_time_matrix(locales: List, airports: List, provider: Callable,
                            cache_path: Optional[str] = None, merge: bool = True, **kw) -> dict:
    """Run a matrix `provider` (osrm_table or ors_matrix), populate each locale's drive_min,
    and write the matrix to cache_path (JSON). Returns the matrix dict. Online step, run once.
    merge=True keeps any existing cache entries (extend a catchment without re-querying)."""
    matrix = provider(locales, airports, **kw)
    if cache_path and merge and os.path.exists(cache_path):
        existing = _read_cache(cache_path)
        existing.update(matrix)
        matrix = existing
    _apply(locales, airports, matrix)
    if cache_path:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(matrix, f)
    return matrix


def _read_cache(cache_path: str) -> dict:
    with open(cache_path, encoding="utf-8") as f:
        return json.load(f)


def load_drive_time_matrix(locales: List, airports_or_path, cache_path: str = None) -> int:
    """Offline step: read a cached matrix and fill each locale's drive_min from it.
    Call as load_drive_time_matrix(locales, "cache.json") or
    load_drive_time_matrix(locales, airports, "cache.json"). Returns the count of pairs filled.
    Pairs missing from the cache are left for the engine's great-circle fallback."""
    if cache_path is None:
        airports, cache_path = None, airports_or_path
    else:
        airports = airports_or_path
    matrix = _read_cache(cache_path)
    return _apply(locales, airports, matrix)


def _apply(locales: List, airports, matrix: dict) -> int:
    """Fill drive_min from a {cache_key: minutes} matrix. If airports is given, only those
    codes are filled; otherwise the code is parsed from the key."""
    codes = {a.code for a in airports} if airports else None
    n = 0
    for l in locales:
        if l.lat is None or l.lon is None:
            continue
        for key, mins in matrix.items():
            pt, code = key.rsplit("|", 1)
            if codes is not None and code not in codes:
                continue
            if key == _key(l.lat, l.lon, code):
                l.drive_min[code] = mins
                n += 1
    return n


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build a cached road drive-time matrix for a catchment.")
    ap.add_argument("geonames_txt"); ap.add_argument("cache_out")
    ap.add_argument("--near", required=True, help="lat,lon,radius_km around the home airport")
    ap.add_argument("--airports", required=True, help="CODE:lat:lon,CODE:lat:lon,...")
    ap.add_argument("--min-pop", type=float, default=5000)
    ap.add_argument("--osrm", default="https://router.project-osrm.org")
    ap.add_argument("--ors-key", default=None)
    a = ap.parse_args()
    import geonames as G
    from catchment import Airport
    la, lo, r = (float(x) for x in a.near.split(","))
    locs = G.near_point(a.geonames_txt, la, lo, r, min_pop=a.min_pop)
    aps = []
    for tok in a.airports.split(","):
        code, plat, plon = tok.split(":")
        aps.append(Airport(code, lat=float(plat), lon=float(plon)))
    if a.ors_key:
        build_drive_time_matrix(locs, aps, ors_matrix, a.cache_out, api_key=a.ors_key)
    else:
        build_drive_time_matrix(locs, aps, osrm_table, a.cache_out, base_url=a.osrm)
    print(f"cached {len(_read_cache(a.cache_out)):,} drive-time pairs to {a.cache_out} "
          f"for {len(locs):,} locales x {len(aps)} airports")
