#!/usr/bin/env python3
r"""
Avia Solutions - Sabre pre-aggregation lookups (REVIEW_QSI_for_Opus_05Jul2026, fix R1).
=========================================================================================
Point-lookup replacements for the four per-route full scans of the Sabre store, backed by the small
derived tables from build_preagg.py. Each function reproduces its live query to the penny; the engine
uses these only when a preagg store is configured (--preagg), and falls back to the full scan
otherwise, so the default path is unchanged until an identity check confirms the swap.

`store` is a preagg .duckdb path. Connections come from the R3 registry (one read-only base per path,
cursor per call), so these are cheap point lookups, not fresh opens.
"""
import os

_TABLES = {}       # store path -> set of table names present (cached)


def _tables(store):
    if store in _TABLES:
        return _TABLES[store]
    have = set()
    if store and os.path.exists(store):
        try:
            from db_registry import con_ro
            con = con_ro(store)
            try:
                have = {r[0] for r in con.execute(
                    "SELECT table_name FROM information_schema.tables").fetchall()}
            finally:
                con.close()
        except Exception:
            have = set()
    _TABLES[store] = have
    return have


def available(store):
    """True if `store` holds the CORE tables (od_p2p + od_single). These cover p2p_traffic and both
    feed markets - the bulk of the per-route Sabre scans. sector_adj is optional (see has_sector)."""
    if not store:
        return False
    return {"od_p2p", "od_single"}.issubset(_tables(store))


def has_sector(store):
    """True if the optional leg-exploded adjacency table is present (for sector_traffic)."""
    return bool(store) and "sector_adj" in _tables(store)


def _con(store):
    from db_registry import con_ro
    return con_ro(store)


def p2p_traffic(store, a, b, year):
    """Pure P2P both directions = od_p2p[a,b] + od_p2p[b,a]. Identical to backtest.p2p_traffic."""
    con = _con(store)
    try:
        r = con.execute(
            "SELECT COALESCE(SUM(pax),0) FROM od_p2p WHERE year=? AND "
            "((o=? AND d=?) OR (o=? AND d=?))", [int(year), a, b, b, a]).fetchone()
        return float(r[0] or 0)
    finally:
        con.close()


def sector_traffic(store, a, b, year):
    """Sector total (P2P + all connecting feed, both directions) = sector_adj for the unordered pair.
    Identical to backtest.sector_traffic."""
    u, v = (a, b) if a <= b else (b, a)
    con = _con(store)
    try:
        r = con.execute(
            "SELECT COALESCE(SUM(pax),0) FROM sector_adj WHERE year=? AND u=? AND v=?",
            [int(year), u, v]).fetchone()
        return float(r[0] or 0)
    finally:
        con.close()


def connecting_market(store, origin_airports, beyond_airports, year, factor_indirect=1.044):
    """Single-connection O&D from the origin catchment to each beyond dest, grouped by dest.
    Identical to route_feed.connecting_market ({dest: pax})."""
    if not origin_airports or not beyond_airports:
        return {}
    oa = ",".join("?" * len(origin_airports)); ba = ",".join("?" * len(beyond_airports))
    con = _con(store)
    try:
        rows = con.execute(
            f"SELECT d, SUM(pax) FROM od_single WHERE year=? AND o IN ({oa}) AND d IN ({ba}) GROUP BY d",
            [int(year)] + list(origin_airports) + list(beyond_airports)).fetchall()
        return {r[0]: float(r[1] or 0) * factor_indirect for r in rows}
    finally:
        con.close()


def behind_market(store, feeders, dest_airports, year, factor_indirect=1.044):
    """Single-connection O&D from each feeder to the route dest(s), grouped by feeder.
    Identical to route_feed.behind_market ({feeder: pax})."""
    if not feeders or not dest_airports:
        return {}
    fa = ",".join("?" * len(feeders)); da = ",".join("?" * len(dest_airports))
    con = _con(store)
    try:
        rows = con.execute(
            f"SELECT o, SUM(pax) FROM od_single WHERE year=? AND o IN ({fa}) AND d IN ({da}) GROUP BY o",
            [int(year)] + list(feeders) + list(dest_airports)).fetchall()
        return {r[0]: float(r[1] or 0) * factor_indirect for r in rows}
    finally:
        con.close()
