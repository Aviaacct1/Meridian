#!/usr/bin/env python3
"""
Avia Solutions - GeoNames population loader (offline catchment population layer).
================================================================================
Turns a free GeoNames dump into the catchment engine's Locale objects, so a
population-weighted catchment runs fully offline, no internet at run time.

Data source (one-off download, then offline forever):
    https://download.geonames.org/export/dump/cities15000.zip   (>15k pop)
    https://download.geonames.org/export/dump/cities5000.zip     (>5k pop, denser)
    https://download.geonames.org/export/dump/cities500.zip      (>500 pop, villages)
    https://download.geonames.org/export/dump/<CC>.zip           (one country, all places)
Licence: CC-BY 4.0 (credit GeoNames). Unzip to a .txt; pass that path here.

Format: tab-delimited, no header, 19 columns. We read name, lat, lon, population,
country and admin codes; everything else is ignored.

PROPENSITY: GeoNames gives population only. Trip-propensity (annual air trips per
head, business share) is NOT in the data - you supply it (CAA/Sabre trip-rate per
head, or a flat assumption), via `propensity` / `business_share` here or by editing
the returned Locale objects.

FUTURE (pre-final-product): city-centroid population is a proxy. Before launch,
switch to isochrone-summed population from a raster/H3 source (GHS-POP 100m, or
Kontur 400m H3 hexagons) so catchment population is summed within real drive-time
bands rather than snapped to city points. See the handover note. This loader is the
offline POC/beta path; the gridded path is the production upgrade.
"""
import csv, math
from typing import List, Optional, Iterable, Callable, Tuple
from catchment import Locale

# GeoNames "geoname" dump column order (0-indexed).
_NAME, _LAT, _LON, _FEATCODE, _CC, _ADMIN1, _ADMIN2, _POP = 1, 4, 5, 7, 8, 10, 11, 14


def _gc_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def load_geonames(path: str,
                  countries: Optional[Iterable[str]] = None,
                  bbox: Optional[Tuple[float, float, float, float]] = None,
                  min_pop: float = 0.0,
                  propensity: float = 1.0,
                  business_share: float = 0.30,
                  propensity_fn: Optional[Callable[[dict], float]] = None,
                  feature_codes: Optional[Iterable[str]] = None) -> List[Locale]:
    """Read a GeoNames dump into Locale objects.

    countries     : ISO-2 codes to keep, e.g. {"GB","IE"} (None = all).
    bbox          : (lat_min, lat_max, lon_min, lon_max) to keep (None = all).
    min_pop       : drop places below this population.
    propensity    : flat air-trips-per-head applied to every locale (override per
                    locale later, or use propensity_fn).
    business_share: flat business proportion (same caveat).
    propensity_fn : optional callable(row_dict) -> propensity for per-place trip rates
                    (row_dict has name, cc, admin1, admin2, population, lat, lon).
    feature_codes : restrict to GeoNames feature codes (e.g. {"PPLA","PPLC"}); None = all populated places.
    """
    cset = {c.upper() for c in countries} if countries else None
    fset = {f.upper() for f in feature_codes} if feature_codes else None
    out: List[Locale] = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 15:
                continue
            try:
                lat, lon = float(row[_LAT]), float(row[_LON])
                pop = float(row[_POP] or 0)
            except ValueError:
                continue
            if pop < min_pop:
                continue
            if cset and row[_CC].upper() not in cset:
                continue
            if fset and row[_FEATCODE].upper() not in fset:
                continue
            if bbox and not (bbox[0] <= lat <= bbox[1] and bbox[2] <= lon <= bbox[3]):
                continue
            rec = {"name": row[_NAME], "cc": row[_CC], "admin1": row[_ADMIN1],
                   "admin2": row[_ADMIN2], "population": pop, "lat": lat, "lon": lon}
            prop = propensity_fn(rec) if propensity_fn else propensity
            out.append(Locale(name=row[_NAME], population=pop, propensity=prop,
                              business_share=business_share, lat=lat, lon=lon))
    return out


def near_point(path: str, lat: float, lon: float, radius_km: float, **kw) -> List[Locale]:
    """All populated places within radius_km of a point (e.g. a candidate airport).
    A quick bbox pre-filter then an exact great-circle cut. Accepts the same kwargs
    as load_geonames (countries, min_pop, propensity, business_share, propensity_fn)."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    locs = load_geonames(path, bbox=(lat - dlat, lat + dlat, lon - dlon, lon + dlon), **kw)
    return [l for l in locs if _gc_km(lat, lon, l.lat, l.lon) <= radius_km]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Load a GeoNames dump into catchment Locales.")
    ap.add_argument("path", help="path to an unzipped GeoNames .txt (e.g. cities15000.txt)")
    ap.add_argument("--countries", help="comma ISO-2 list, e.g. GB,IE")
    ap.add_argument("--min-pop", type=float, default=0.0)
    ap.add_argument("--near", help="lat,lon,radius_km - keep places within radius of a point")
    a = ap.parse_args()
    kw = dict(min_pop=a.min_pop)
    if a.countries:
        kw["countries"] = a.countries.split(",")
    if a.near:
        la, lo, r = (float(x) for x in a.near.split(","))
        locs = near_point(a.path, la, lo, r, **kw)
    else:
        locs = load_geonames(a.path, **kw)
    locs.sort(key=lambda l: l.population, reverse=True)
    print(f"{len(locs):,} locales, total population {sum(l.population for l in locs):,.0f}")
    for l in locs[:15]:
        print(f"  {l.name:<24} pop {l.population:>12,.0f}  ({l.lat:.3f},{l.lon:.3f})")
