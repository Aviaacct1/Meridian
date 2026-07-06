#!/usr/bin/env python3
"""
Avia Solutions - read-only DuckDB connection registry (fix R3 in REVIEW_QSI_for_Opus_05Jul2026).
================================================================================================
The engine opened and closed a fresh DuckDB connection for every query. route_feed alone opened
eight per route (hub_served, hub_fed_by, onward carriers, dominance, markets, feeders, inbound
carriers, behind market); backtest re-opened the sabre store for p2p_traffic and sector_traffic
on every route. Opening a connection to a multi-GB store carries a real fixed cost, paid tens of
thousands of times across a full run.

This registry opens ONE base connection per store path per process, then hands each caller a fresh
DuckDB cursor over that base connection. A cursor is cheap (no file re-open) and has its own
execution state, so:

  - the fixed open cost is paid once per path per process (R3's gain), and
  - concurrent callers (the live server serves requests on threads) never clobber each other's
    in-flight results, which a single shared connection would.

The returned object is a thin proxy whose close() is a no-op at the base level: closing it disposes
the per-call cursor but leaves the long-lived base connection open. Every existing call site keeps
its `con = _con(db) ... finally: con.close()` shape unchanged, so this is a pure performance change:
identical SQL over the same immutable store returns identical results.

Under multiprocessing (fix R2) each worker process builds its own registry on first use; the base
connections are per-process and never shared across the fork, which is correct for DuckDB.
"""
import threading

_LOCK = threading.Lock()
_BASE = {}          # store path -> base read-only DuckDB connection (one per process)


class _CursorProxy:
    """Wraps a per-call DuckDB cursor. close() disposes the cursor only, never the base connection.
    All other attributes (execute, executemany, fetchone, fetchall, fetchdf, ...) delegate through."""
    __slots__ = ("_cur",)

    def __init__(self, cur):
        self._cur = cur

    def close(self):
        try:
            self._cur.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __getattr__(self, name):
        return getattr(self._cur, name)


def con_ro(db):
    """Return a read-only cursor over the process-wide base connection for `db`.

    The base connection is opened on first request and reused for the life of the process. Each call
    gets its own cursor, so results never interleave across callers. close() on the returned proxy is
    safe and cheap (cursor-only).

    AVIA_CONN_REGISTRY=0 (or false/off/no) disables the registry: every call opens a fresh read-only
    connection, i.e. the exact pre-R3 behaviour. This is the A/B switch to isolate whether the registry
    (via any query-order change it introduces) moves a result, versus the pre-existing engine."""
    import os
    if os.environ.get("AVIA_CONN_REGISTRY", "1").strip().lower() in ("0", "false", "off", "no"):
        return _open(db)                                # fresh connection, real close() - pre-R3 path
    base = _BASE.get(db)
    if base is None:
        with _LOCK:
            base = _BASE.get(db)
            if base is None:
                base = _open(db)
                _BASE[db] = base
    return _CursorProxy(base.cursor())


def apply_limits(con):
    """Apply DuckDB session limits from the environment so NO connection can take the machine down.
    Every module that opens a store (here, oag_served, sabre_catchment, wave_cache) must route through
    this, because DuckDB defaults each connection to ~80% of physical RAM - and under the R2 pool eight
    workers each taking 80% over-commits the box and freezes it (the observed 97%/OOM crash).

      AVIA_DUCKDB_MEMORY   -> PRAGMA memory_limit  (e.g. '3GB'; MUST be the total budget / n_workers)
      AVIA_DUCKDB_TEMP     -> PRAGMA temp_directory (a named spill folder on a disk with space)
      AVIA_DUCKDB_THREADS  -> PRAGMA threads        (1 = deterministic; avoids N x M oversubscription)

    Any unset var is left at DuckDB's default. Failures are swallowed (old DuckDB, read-only quirks)."""
    import os
    mem = os.environ.get("AVIA_DUCKDB_MEMORY")
    tmp = os.environ.get("AVIA_DUCKDB_TEMP")
    thr = os.environ.get("AVIA_DUCKDB_THREADS")
    try:
        if mem:
            con.execute(f"PRAGMA memory_limit='{mem}'")
        if tmp:
            con.execute(f"PRAGMA temp_directory='{tmp.replace(chr(92), '/')}'")
        if thr:
            con.execute(f"PRAGMA threads={int(thr)}")
    except Exception:
        pass
    return con


def _open(db):
    """Open a read-only connection with the shared limits applied (memory cap, temp dir, threads)."""
    import duckdb
    return apply_limits(duckdb.connect(db, read_only=True))


def reset():
    """Close every base connection and clear the registry. Call after a store file is replaced
    (e.g. the quarterly OAG/Sabre reload) or before a clean re-open; otherwise cached connections
    would keep pointing at the old file handle. Harmless if the registry is empty."""
    with _LOCK:
        for c in _BASE.values():
            try:
                c.close()
            except Exception:
                pass
        _BASE.clear()
