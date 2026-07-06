#!/usr/bin/env python3
"""
Avia Solutions - OAG served-airport index.
==============================================================================
The shared data dependency for the general route engine's two airport-selection
fixes. From the local OAG schedule store (oag.duckdb, table 'oag') it builds, for
one representative week, the set of airports that actually hold scheduled
passenger service, each with:

  dep_freq   weekly departing frequency (sum of Frequency over departing legs)
  dest_count distinct departure destinations served
  ann_seats  annual departing seats  = sum(seats_total * frequency) * 52
  size_m     a size proxy on the SAME SCALE as the Genoa calibration's
             size_pull_m (annual passengers in millions, both directions):
             ann_seats * 2 directions * LOAD_PROXY / 1e6

Why size_m matters: the catchment choice model weights each airport by
attractiveness ** att_exponent, and the Genoa parameters (att_exponent 0.75,
logit_scale 0.008) were calibrated with attractiveness = annual pax in millions
(GOA 1.2, MXP 28.5, ...). Feeding raw weekly frequency would be a different unit
and would silently change the allocation even though the parameters are untouched.
size_m keeps the attractiveness on the calibrated scale, derived from data.

The index is cacheable to JSON so the engine runs OFFLINE (laptop / World Routes)
against a stored snapshot, the store only being needed to refresh it. Build it on
the machine that holds oag.duckdb; ship the JSON.

  from oag_served import build_served_index, save_index, load_index
  idx = build_served_index("oag.duckdb", "2025-05-26")
  save_index(idx, "served_2025-05-26.json")
  # offline thereafter:
  idx = load_index("served_2025-05-26.json")
"""
import json

# Annual departing seats -> annual passengers (both directions), in millions.
# 0.80 representative load; x2 for both directions so size_m matches the Genoa
# size_pull_m convention (total annual pax through the airport, both ways).
LOAD_PROXY = 0.80
DIRECTIONS = 2

# Service types we treat as bookable scheduled passenger service. The Avia OAG
# pull is already "published / passenger-available" (Jess, 26 June), so this is a
# light guard, not the main filter. 'J' scheduled passenger, 'S'/'U' charter/shuttle.
PAX_SERVICE_TYPES = {"J", "S", "U", "A", "E", "G", "B"}


def _connect(db, read_only=True):
    try:
        import duckdb
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("duckdb not installed; pip install duckdb") from e
    con = duckdb.connect(db, read_only=read_only)
    # This module opens outside db_registry, so route through the shared limiter: it applies the memory
    # cap (or 8 workers x 80%-of-RAM default OOM the machine), the named temp dir, and threads=1 (the
    # served-index SUM must reduce single-threaded or an airport near min_weekly_freq flips run-to-run).
    try:
        from db_registry import apply_limits
        apply_limits(con)
    except Exception:
        pass
    return con


def list_weeks(db):
    """Distinct week strings held in the store (for choosing the snapshot week)."""
    con = _connect(db)
    try:
        return [r[0] for r in con.execute(
            "SELECT DISTINCT week FROM oag ORDER BY week").fetchall()]
    finally:
        con.close()


def _service_filter(con):
    """Return a SQL predicate restricting to passenger service IF the store has a
    usable service_type column, else an always-true predicate (the pull is already
    passenger-only). Defensive: some pulls leave service_type blank."""
    try:
        vals = {(_r[0] or "").strip().upper()
                for _r in con.execute(
                    "SELECT DISTINCT service_type FROM oag").fetchall()}
    except Exception:
        return "1=1"
    vals.discard("")
    if not vals:
        return "1=1"
    keep = vals & PAX_SERVICE_TYPES
    if not keep:                       # unknown coding scheme -> don't over-filter
        return "1=1"
    inlist = ",".join("'" + v.replace("'", "''") + "'" for v in sorted(keep))
    return ("(service_type IS NULL OR TRIM(UPPER(service_type)) = '' "
            f"OR TRIM(UPPER(service_type)) IN ({inlist}))")


def build_served_index(db, week, min_weekly_freq=1.0):
    """Build the served-airport index for one week from oag.duckdb.

    db              : path to the store
    week            : REQUIRED week string (e.g. '2025-05-26'); store holds several
    min_weekly_freq : drop airports with less than this many weekly departures
                      (keeps the genuine commercial field, not a stray ferry leg)

    Returns {'week': week, 'airports': {IATA: {dep_freq, dest_count, ann_seats,
    size_m, city, country}}}.
    """
    if not week:
        raise ValueError("week is required; see oag_served.list_weeks(db)")
    con = _connect(db)
    try:
        svc = _service_filter(con)
        rows = con.execute(f"""
            SELECT dep_airport,
                   SUM(COALESCE(TRY_CAST(frequency AS DOUBLE), 1.0))                       AS dep_freq,
                   COUNT(DISTINCT arr_airport)                                             AS dest_count,
                   SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE),
                                TRY_CAST(seats AS DOUBLE), 0.0)
                       * COALESCE(TRY_CAST(frequency AS DOUBLE), 1.0))                     AS weekly_seats,
                   MIN(dep_city)                                                          AS city,
                   MIN(dep_country)                                                        AS country
            FROM oag
            WHERE week = ? AND dep_airport IS NOT NULL AND TRIM(dep_airport) <> ''
              AND {svc}
            GROUP BY dep_airport
        """, [week]).fetchall()
    finally:
        con.close()
    airports = {}
    for dep, dep_freq, dest_count, weekly_seats, city, country in rows:
        code = (dep or "").strip().upper()
        if not code or (dep_freq or 0) < min_weekly_freq:
            continue
        ann_seats = float(weekly_seats or 0.0) * 52.0
        size_m = ann_seats * DIRECTIONS * LOAD_PROXY / 1e6
        airports[code] = {
            "dep_freq": round(float(dep_freq or 0.0), 1),
            "dest_count": int(dest_count or 0),
            "ann_seats": round(ann_seats),
            "size_m": round(size_m, 3),
            "city": (city or "").strip().upper(),
            "country": (country or "").strip().upper(),
        }
    return {"week": week, "airports": airports}


# ---------------------------------------------------------------- cache + queries
def save_index(index, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
    return path


def load_index(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def served_set(index, min_weekly_freq=1.0):
    """The set of IATA codes with real scheduled service (the fix-1 filter)."""
    return {c for c, a in index["airports"].items()
            if a.get("dep_freq", 0.0) >= min_weekly_freq}


def size_m(index, code, default=0.5):
    """Size proxy (annual pax, millions) for the catchment attractiveness term.
    default is a small non-zero pull for a served airport missing seat data."""
    a = index["airports"].get((code or "").strip().upper())
    return a["size_m"] if a and a.get("size_m") else default
