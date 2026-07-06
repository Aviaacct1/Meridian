#!/usr/bin/env python3
"""
Avia Solutions - OAG store leg loader.
==============================================================================
Pulls timed legs for a market from the local OAG DuckDB store (oag.duckdb, table
'oag') via SQL, instead of loading the regional .xlsx pulls into memory. Returns
legs in the EXACT dict shape build_connections consumes (same parse helpers as
connection_builder.load_oag_legs), so the connection builder and the multi-hub QSI
run sit unchanged on top of the store.

Market-scoped two-query pull (so a Genoa-NYC / SJC run touches only the relevant
hubs, not the whole 3m-flight store):
  (1) legs INTO the catchment            -> their dep_airports are the candidate hubs
  (2) arrivals AT those hubs (+ the proposed service's hub) -> the beyond->hub legs
The union is exactly the leg set run_multihub_qsi.run() needs to populate arr_by /
dep_by. week is REQUIRED, as the store holds several region-weeks.
"""
from connection_builder import (parse_time_hhmm, _parse_duration_mins,
                                parse_days_string, get_dom_int)

# Store columns in the order _row_to_leg unpacks them.
_COLS = ("carrier, flight_no, dep_airport, arr_airport, dep_terminal, arr_terminal, "
         "dep_country, arr_country, dep_city, arr_city, local_dep_time, local_arr_time, "
         "flying_time, elapsed_time, days_of_op, arr_days_of_op, alliance, carrier_category, "
         "dup_marker, pass_class, gcd_km")


def _connect(db, read_only=True):
    try:
        import duckdb
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("duckdb not installed; pip install duckdb") from e
    return duckdb.connect(db, read_only=read_only)


def _s(v):
    return str(v).strip() if v is not None else ''


def _row_to_leg(row, idx):
    """Map one store row to the leg-dict shape build_connections expects."""
    (carrier, flight_no, dep_airport, arr_airport, dep_terminal, arr_terminal,
     dep_country, arr_country, dep_city, arr_city, local_dep_time, local_arr_time,
     flying_time, elapsed_time, days_of_op, arr_days_of_op, alliance, carrier_category,
     dup_marker, pass_class, gcd_km) = row
    rec = {
        'carrier': _s(carrier), 'flight_no': _s(flight_no),
        'dep_airport': _s(dep_airport), 'arr_airport': _s(arr_airport),
        'dep_terminal': _s(dep_terminal), 'arr_terminal': _s(arr_terminal),
        'dep_country': _s(dep_country), 'arr_country': _s(arr_country),
        'dep_city': _s(dep_city), 'arr_city': _s(arr_city),
        'arr_time_mins': parse_time_hhmm(local_arr_time),
        'dep_time_mins': parse_time_hhmm(local_dep_time),
        'flying_mins': _parse_duration_mins(flying_time or elapsed_time),
        'dep_day_set': parse_days_string(days_of_op),
        'arr_day_set': parse_days_string(arr_days_of_op),
        'id': idx,
        'alliance': _s(alliance), 'carrier_category': _s(carrier_category),
        'dup_marker': _s(dup_marker), 'pass_class': _s(pass_class),
    }
    rec['dom_int'] = get_dom_int(rec['dep_country'], rec['arr_country'])
    try:
        rec['gcd_km'] = float(gcd_km) if gcd_km not in (None, '') else None
    except (ValueError, TypeError):
        rec['gcd_km'] = None
    return rec


def _ph(n):
    return ",".join(["?"] * n)


def list_weeks(db):
    """Distinct week strings held in the store (for choosing --week)."""
    con = _connect(db)
    try:
        return [r[0] for r in con.execute("SELECT DISTINCT week FROM oag ORDER BY week").fetchall()]
    finally:
        con.close()


def _dedupe(rows):
    """Drop duplicate store rows (a cat->hub leg can satisfy two WHERE clauses)."""
    seen = {}
    for r in rows:
        key = (r[0], r[1], r[2], r[3], r[10])   # carrier, flight_no, dep, arr, local_dep_time
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def load_legs_for_market(db, week, catchment, proposed_hub=None, bidirectional=False):
    """Market-scoped leg pull for run_multihub_qsi.

    db          : path to oag.duckdb
    week        : REQUIRED week string (e.g. '2025-05-26'); the store holds several
    catchment   : iterable of catchment airport codes (the destination region)
    proposed_hub: optional hub of a proposed new service, so its beyond->hub legs are
                  pulled even if no carrier yet flies hub->catchment in the schedule.
    bidirectional: also pull the RETURN direction (catchment->hub and hub->beyond) so
                  run() can score QSI2; default False = QSI1 (outbound) legs only.
    """
    if not week:
        raise ValueError("week is required (the store holds several region-weeks); "
                         "pass week=... (see oag_store.list_weeks(db))")
    cat = [c.strip() for c in catchment]
    cat_set = set(cat)
    con = _connect(db)
    try:
        # (1) legs INTO the catchment (hub->cat) -> their dep_airports are the candidate hubs
        rows = con.execute(
            f"SELECT {_COLS} FROM oag WHERE week=? AND arr_airport IN ({_ph(len(cat))})",
            [week] + cat).fetchall()
        hubs = {r[2] for r in rows if r[2] and r[2] not in cat_set}   # r[2]=dep_airport
        if bidirectional:
            # (1b) legs OUT of the catchment (cat->hub) -> their arr_airports are hubs too
            cat_out = con.execute(
                f"SELECT {_COLS} FROM oag WHERE week=? AND dep_airport IN ({_ph(len(cat))})",
                [week] + cat).fetchall()
            hubs |= {r[3] for r in cat_out if r[3] and r[3] not in cat_set}  # r[3]=arr_airport
            rows += cat_out
        if proposed_hub:
            hubs.add(proposed_hub)
        hubs = sorted(hubs)
        if hubs:
            # (2) arrivals AT the hubs (beyond->hub) -> the QSI1 beyond legs
            hub_in = con.execute(
                f"SELECT {_COLS} FROM oag WHERE week=? AND arr_airport IN ({_ph(len(hubs))})",
                [week] + hubs).fetchall()
            rows += hub_in
            if bidirectional:
                # (3) hub->beyond departures to those same beyond points (QSI2 leg2)
                beyonds = sorted({r[2] for r in hub_in
                                  if r[2] and r[2] not in cat_set and r[2] not in set(hubs)})
                if beyonds:
                    rows += con.execute(
                        f"SELECT {_COLS} FROM oag WHERE week=? AND dep_airport IN ({_ph(len(hubs))}) "
                        f"AND arr_airport IN ({_ph(len(beyonds))})",
                        [week] + hubs + beyonds).fetchall()
    finally:
        con.close()
    rows = _dedupe(rows)
    return [_row_to_leg(r, i) for i, r in enumerate(rows)]
