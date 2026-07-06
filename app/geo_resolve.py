#!/usr/bin/env python3
"""
Avia Solutions - city / metro airport resolver.
==============================================================================
Fix 2 of the general route engine: turn a user's city string into its MAIN
COMMERCIAL airport(s), so "New York" resolves to JFK / EWR / LGA, not a seaplane
base, and "Genoa" resolves to GOA even though the airport reference files it as
"Genova".

The airportsdata city field is unreliable (it files EWR under "Newark", not "New
York", and GOA under "Genova"), so we do not trust it as the primary key. Instead:

  1. IATA passthrough         - a 3-letter code that exists is taken as given.
  2. Geocode the city name    - against the GeoNames dump (English/ascii names,
                                accent-insensitive, population-ranked), giving a
                                metro centroid and country.
  3. Rank by real service     - the OAG served-airport index decides which fields
                                near that centroid actually have commercial service,
                                ranked by weekly frequency, keeping those above a
                                share of the busiest. New York -> JFK/EWR/LGA;
                                minor fields (NYS, ISP, SWF) drop out by service.

Offline / no OAG index: falls back to the nearest airportsdata airport(s) to the
centroid, which is weaker (no service ranking) and is flagged in the result.

  from geo_resolve import resolve_metro
  m = resolve_metro("New York", served_index=idx, dump="cities5000.txt")
  # -> {'query': 'New York', 'centre': (40.71, -74.01), 'country': 'US',
  #     'airports': ['JFK','EWR','LGA'], 'primary': 'JFK', 'basis': 'oag-served', ...}
"""
import math
import unicodedata


# --------------------------------------------------------------------- geocoding
def _norm(s):
    """Lowercase, strip accents and punctuation runs, collapse whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().replace(".", " ").replace("-", " ").split())


def gc_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def geocode_city(name, dump, country=None):
    """Best GeoNames match for a city name. Returns {lat, lon, country, name,
    population} or None. Scores exact name > startswith > contains, tie-broken by
    population. `country` (ISO-2) optionally constrains the search."""
    q = _norm(name)
    if not q:
        return None
    cc = (country or "").strip().upper() or None
    best = None  # (score, population, record)
    with open(dump, encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 15:
                continue
            if cc and f[8].upper() != cc:
                continue
            try:
                pop = int(f[14] or 0)
            except ValueError:
                pop = 0
            for field in (f[1], f[2]):           # name, asciiname
                nf = _norm(field)
                if not nf:
                    continue
                if nf == q:
                    score = 3
                elif nf.startswith(q):
                    score = 2
                elif q in nf:
                    score = 1
                else:
                    continue
                cand = (score, pop, f)
                if best is None or cand[:2] > best[:2]:
                    best = cand
                break
    if not best:
        return None
    f = best[2]
    return {"lat": float(f[4]), "lon": float(f[5]), "country": f[8].upper(),
            "name": f[1], "population": best[1]}


# ------------------------------------------------------------- airport coordinates
_AP = None
def _airports():
    global _AP
    if _AP is None:
        import airportsdata
        _AP = airportsdata.load("IATA")
    return _AP


def _coords(code):
    r = _airports().get((code or "").strip().upper())
    if r and r["lat"] is not None:
        return r["lat"], r["lon"]
    return None


# ----------------------------------------------------------------- metro resolver
def _metro_near(centre, country, served_index, metro_radius_km, min_share, max_airports,
                basis, force_primary=None):
    """Served airports within metro_radius of a centre, ranked by weekly frequency, kept above a
    share of the busiest. force_primary pins the primary (and ensures it's included), e.g. the
    destination airport the user named. Returns the resolve dict, or None if nothing served near."""
    if not served_index:
        return None
    cand = []
    for code, a in served_index["airports"].items():
        c = _coords(code)
        if not c:
            continue
        dist = gc_km(centre[0], centre[1], c[0], c[1])
        if dist <= metro_radius_km:
            cand.append((code, a.get("dep_freq", 0.0), a.get("size_m", 0.0), dist))
    if not cand:
        return None
    top = max(f for _, f, _, _ in cand)
    kept = [x for x in cand if x[1] >= min_share * top] or cand
    kept.sort(key=lambda x: -x[1])
    kept = kept[:max_airports]
    codes = [c for c, _, _, _ in kept]
    primary = force_primary or kept[0][0]
    if force_primary and force_primary not in codes:
        codes = [force_primary] + codes[:max_airports - 1]
    return {"centre": centre, "country": country, "airports": codes, "primary": primary,
            "basis": basis, "detail": {c: {"dep_freq": f, "size_m": s, "dist_km": round(d, 1)}
                                       for c, f, s, d in kept}}


# Territory / common-name aliases resolved BEFORE the IATA short-circuit. "BVI" is the IATA
# code for Birdsville, a dirt strip in outback Queensland - nobody at a route conference means
# that (John, 4 Jul 2026: BVI-JFK resolved to Birdsville and produced a nonsense error).
ALIASES = {
    "BVI": "EIS", "BRITISH VIRGIN ISLANDS": "EIS", "TORTOLA": "EIS",
    "USVI": "STT", "US VIRGIN ISLANDS": "STT",
    "IOM": "IOM",  # Isle of Man IS the IATA code - listed so nobody 'fixes' it into an alias
}


def resolve_metro(token, served_index=None, dump=None, country=None,
                  metro_radius_km=80.0, min_share=0.10, max_airports=4, expand=True):
    """Resolve a city string or IATA code to its main commercial airport(s).

    token         : "New York", "Genoa", or an IATA code like "GOA"
    served_index  : an oag_served index (build/load_index). If given, service
                    decides the airports; if None, falls back to nearest field.
    dump          : GeoNames cities txt (needed for a city name, not for an IATA)
    metro_radius_km: how far from the centroid counts as the same metro
    min_share     : keep airports with weekly freq >= min_share * the busiest
    max_airports  : cap the returned set

    Returns a dict: query, centre (lat,lon), country, airports (ordered list of
    IATA), primary (busiest), basis ('iata' | 'oag-served' | 'nearest-fallback'),
    and per-airport service detail when available.
    """
    ap = _airports()
    t = (token or "").strip()
    t = ALIASES.get(t.upper(), t)          # territory names beat colliding IATA codes
    # (1) IATA code: single airport, or expand to its metro (the destination market)
    if len(t) == 3 and t.upper() in ap:
        code = t.upper()
        c = _coords(code); ctry = ap[code]["country"]
        if expand and served_index and c:
            m = _metro_near(c, ctry, served_index, metro_radius_km, min_share, max_airports,
                            "iata-metro", force_primary=code)
            if m:
                m["query"] = token
                return m
        return {"query": token, "centre": c, "country": ctry,
                "airports": [code], "primary": code, "basis": "iata", "detail": {}}

    # (2) geocode the city
    if not dump:
        raise ValueError("a GeoNames dump is required to resolve a city name "
                         "(pass dump=...), or give an IATA code")
    g = geocode_city(t, dump, country=country)
    if not g:
        raise ValueError(f"could not geocode city '{token}'")
    centre = (g["lat"], g["lon"])

    # (3) rank by real service near the centroid
    m = _metro_near(centre, g["country"], served_index, metro_radius_km, min_share,
                    max_airports, "oag-served")
    if m:
        m["query"] = token
        if not expand:
            m["airports"] = [m["primary"]]
        return m

    # offline fallback: nearest airportsdata airport(s) to the centroid
    near = []
    for code, r in ap.items():
        if r["lat"] is None or not r["iata"]:
            continue
        d = gc_km(centre[0], centre[1], r["lat"], r["lon"])
        if d <= metro_radius_km:
            near.append((code, d))
    near.sort(key=lambda x: x[1])
    near = near[:max_airports] or [(min(ap.items(),
                key=lambda kv: gc_km(centre[0], centre[1], kv[1]["lat"], kv[1]["lon"])
                if kv[1]["lat"] is not None else 9e9)[0], None)]
    return {"query": token, "centre": centre, "country": g["country"],
            "airports": [c for c, _ in near], "primary": near[0][0],
            "basis": "nearest-fallback",
            "detail": {c: {"dist_km": round(d, 1) if d is not None else None} for c, d in near}}
