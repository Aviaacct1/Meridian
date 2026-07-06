#!/usr/bin/env python3
"""
Avia Solutions - one-command drive-time cache builder for any route case.
=========================================================================
The general version of build_genoa_cache.py. Builds the cached road drive-time matrix for a
case's catchment ONCE, from a GeoNames dump + a routing service, and writes it to the case's
drive cache. After that the catchment runs fully offline against the cache (see routing.py).

RUN (on a machine with internet + the GeoNames dump):
    py -3.12 build_cache.py genoa_nyc cities5000.txt                 # OSRM public demo (no key)
    py -3.12 build_cache.py genoa_nyc cities5000.txt --ors-key KEY   # OpenRouteService (free key)
    py -3.12 build_cache.py genoa_nyc cities5000.txt --osrm http://localhost:5000   # self-hosted
    py -3.12 build_cache.py genoa_nyc cities5000.txt --proxy         # offline great-circle (testing)

The cache keys each entry to a locale's coordinates, so build it from the SAME GeoNames dump you
run the catchment with. Missing pairs fall back to the great-circle proxy automatically. The
cache covers EVERY case airport, including cache-only cross-border competitors (e.g. Nice).
"""
import argparse, os, sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G
    import routing as R
    from route_case import RouteCase

    ap = argparse.ArgumentParser(description="Build a route case's drive-time cache once.")
    ap.add_argument("case", help="route case id or path to a case JSON")
    ap.add_argument("geonames_txt", help="path to an unzipped GeoNames dump (cities5000.txt or IT.txt)")
    ap.add_argument("--out", default=None, help="cache output (default: the case's drive_cache)")
    ap.add_argument("--radius-km", type=float, default=None)
    ap.add_argument("--min-pop", type=float, default=None)
    ap.add_argument("--osrm", default="https://router.project-osrm.org")
    ap.add_argument("--ors-key", default=None)
    ap.add_argument("--proxy", action="store_true", help="offline great-circle cache (testing only)")
    a = ap.parse_args()

    case, base_dir = RouteCase.load_with_dir(a.case)
    radius_km = a.radius_km if a.radius_km is not None else case.radius_km
    min_pop = a.min_pop if a.min_pop is not None else case.min_pop
    out = a.out or case.resolve_existing("drive_cache", base_dir, [here], f"{case.case_id}_drive.json")

    if not os.path.exists(a.geonames_txt):
        print(f"ERROR: GeoNames dump not found: {a.geonames_txt}\n"
              f"Download from https://download.geonames.org/export/dump/ (cities5000.zip or IT.zip), "
              f"unzip, and pass the .txt.")
        sys.exit(1)

    airports = case.to_airport_objs("cache")               # includes cache-only competitors
    locs = G.near_point(a.geonames_txt, case.centre_lat, case.centre_lon, radius_km,
                        countries=case.countries, min_pop=min_pop)
    if not locs:
        print("ERROR: no locales found in range - check the dump path / radius / min-pop.")
        sys.exit(1)
    pairs = len(locs) * len(airports)
    print(f"{len(locs):,} locales within {radius_km:.0f} km of {case.title or case.case_id} "
          f"x {len(airports)} airports = {pairs:,} pairs")

    if a.proxy:
        provider, kw, label = R.gc_matrix, {}, "great-circle PROXY (offline, testing only)"
    elif a.ors_key:
        provider, kw, label = R.ors_matrix, {"api_key": a.ors_key}, "OpenRouteService"
    else:
        provider, kw, label = R.osrm_table, {"base_url": a.osrm}, f"OSRM ({a.osrm})"
    print(f"routing via {label} ...")

    R.build_drive_time_matrix(locs, airports, provider, cache_path=out, **kw)
    n = len(R._read_cache(out))
    print(f"DONE - wrote {n:,} drive-time pairs to {out}")
    print(f"Load it offline with routing.load_drive_time_matrix(locales, '{os.path.basename(out)}').")


if __name__ == "__main__":
    main()
