#!/usr/bin/env python3
"""
Avia Solutions - one-command builder for the Genoa drive-time cache.
====================================================================
Generates the cached road drive-time matrix for the Genoa / Milan catchment ONCE,
from a GeoNames dump + a routing service, and writes it to genoa_drive.json. After
that the catchment runs fully offline against the cache (see routing.py).

RUN (on a machine with internet + the GeoNames dump):
    # default: OSRM public demo (no key)
    py -3.12 build_genoa_cache.py cities5000.txt

    # OpenRouteService instead (free key from openrouteservice.org)
    py -3.12 build_genoa_cache.py cities5000.txt --ors-key YOUR_KEY

    # self-hosted OSRM (recommended for production / many locales)
    py -3.12 build_genoa_cache.py cities5000.txt --osrm http://localhost:5000

    # offline proxy cache (no internet; great-circle, for testing only)
    py -3.12 build_genoa_cache.py cities5000.txt --proxy

Get the dump once from https://download.geonames.org/export/dump/ :
    cities5000.zip (places >5,000) or IT.zip (all Italian places) - unzip to a .txt.

The cache keys each entry to a locale's coordinates, so build it from the SAME GeoNames
dump you run the catchment with (matching coordinates), then load_drive_time_matrix fills
the drive times offline. Missing pairs fall back to the great-circle proxy automatically.
"""
import argparse, os, sys

# the Genoa catchment's candidate airports (code, lat, lon) - GOA plus the realistic
# competitors a NW-Italy origin chooses between (Milan, Turin, Bologna, Nice cross-border)
GENOA_AIRPORTS = [
    ("GOA", 44.4133, 8.8375),   # Genoa Cristoforo Colombo
    ("MXP", 45.6306, 8.7281),   # Milan Malpensa
    ("LIN", 45.4451, 9.2767),   # Milan Linate
    ("BGY", 45.6739, 9.7042),   # Milan Bergamo Orio al Serio
    ("TRN", 45.2008, 7.6497),   # Turin Caselle
    ("BLQ", 44.5354, 11.2887),  # Bologna
    ("NCE", 43.6584, 7.2159),   # Nice Cote d'Azur (cross-border, west Liguria)
]
GENOA_CENTRE = (44.4133, 8.8375)   # search centre for the catchment
DEFAULT_RADIUS_KM = 220.0          # covers Liguria, Piemonte, W. Lombardy, W. Emilia
DEFAULT_MIN_POP = 5000.0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G
    import routing as R
    from catchment import Airport

    ap = argparse.ArgumentParser(description="Build the Genoa drive-time cache once.")
    ap.add_argument("geonames_txt", help="path to an unzipped GeoNames dump (cities5000.txt or IT.txt)")
    ap.add_argument("--out", default=os.path.join(here, "genoa_drive.json"))
    ap.add_argument("--radius-km", type=float, default=DEFAULT_RADIUS_KM)
    ap.add_argument("--min-pop", type=float, default=DEFAULT_MIN_POP)
    ap.add_argument("--osrm", default="https://router.project-osrm.org")
    ap.add_argument("--ors-key", default=None)
    ap.add_argument("--proxy", action="store_true", help="offline great-circle cache (testing only)")
    a = ap.parse_args()

    if not os.path.exists(a.geonames_txt):
        print(f"ERROR: GeoNames dump not found: {a.geonames_txt}\n"
              f"Download from https://download.geonames.org/export/dump/ (cities5000.zip or IT.zip), unzip, and pass the .txt.")
        sys.exit(1)

    airports = [Airport(c, lat=la, lon=lo) for c, la, lo in GENOA_AIRPORTS]
    locs = G.near_point(a.geonames_txt, GENOA_CENTRE[0], GENOA_CENTRE[1], a.radius_km,
                        countries=["IT", "FR"], min_pop=a.min_pop)
    if not locs:
        print("ERROR: no locales found in range - check the dump path / radius / min-pop.")
        sys.exit(1)
    pairs = len(locs) * len(airports)
    print(f"{len(locs):,} locales within {a.radius_km:.0f} km of Genoa x {len(airports)} airports = {pairs:,} pairs")

    if a.proxy:
        provider, kw, label = R.gc_matrix, {}, "great-circle PROXY (offline, testing only)"
    elif a.ors_key:
        provider, kw, label = R.ors_matrix, {"api_key": a.ors_key}, "OpenRouteService"
    else:
        provider, kw, label = R.osrm_table, {"base_url": a.osrm}, f"OSRM ({a.osrm})"
    print(f"routing via {label} ...")

    R.build_drive_time_matrix(locs, airports, provider, cache_path=a.out, **kw)
    n = len(R._read_cache(a.out))
    print(f"DONE - wrote {n:,} drive-time pairs to {a.out}")
    print("Load it offline with routing.load_drive_time_matrix(locales, '%s')." % os.path.basename(a.out))


if __name__ == "__main__":
    main()
