#!/usr/bin/env python3
"""
Avia Solutions - per-carrier CASM/RASM benchmark resolver (Form 41 + T1 + T-100).
Reads casm_benchmark.duckdb (built by build_casm_benchmark.py) and returns a
carrier's filed system CASM and average stage length, so aircraft_economics can
anchor its generic cost to what the carrier actually files. Safe: returns None
if the store or the carrier is absent, so the caller stays on the generic model.
"""
import os

_CACHE = {}


def _store():
    try:
        import config
        p = str(getattr(config, "CASM_BENCHMARK", "") or "")
        if p:
            return p
    except Exception:
        pass
    return os.environ.get("AVIA_CASM_BENCHMARK", r"C:\Avia\casm_benchmark.duckdb")


def carrier_casm(carrier, year=None):
    """Return (casm_cents, avg_stage_km) for a 2-letter carrier code, latest year if
    year is None. None if unavailable (caller then keeps the generic cost)."""
    if not carrier:
        return None
    code = str(carrier).strip().upper()[:2]
    key = (code, year)
    if key in _CACHE:
        return _CACHE[key]
    db = _store()
    if not os.path.exists(db):
        return None
    try:
        from db_registry import con_ro
        con = con_ro(db)
    except Exception:
        import duckdb
        con = duckdb.connect(db, read_only=True)
    try:
        if year is not None:
            row = con.execute(
                "select casm_c, avg_stage_km from casm where carrier=? and year=?",
                [code, int(year)]).fetchone()
        else:
            row = con.execute(
                "select casm_c, avg_stage_km from casm where carrier=? "
                "order by year desc limit 1", [code]).fetchone()
    finally:
        con.close()
    out = (float(row[0]), float(row[1])) if row and row[0] and row[1] else None
    _CACHE[key] = out
    return out
