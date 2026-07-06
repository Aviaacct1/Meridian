#!/usr/bin/env python3
"""
Avia Cortex - Engine V2 wave cache: the per-run accelerator for the QSI feed back-tests.
=========================================================================================
qsi_feed needs, for every launched route in the pinned set, the departure/arrival boards of
its origin, its hub and every competitor hub, at the as-if week (first week of Y-1, matching
backtest.asif_forecast), plus each route's ACTUAL flown dep/arr times from the launch year.
Querying oag.duckdb for those thousands of boards on every back-test run is the cost that
made the mct_bank runs slow; this caches them once.

The cache is deliberately dumb: one `boards` table = the full OAG slice for the needed weeks
(all airports, so competitor hubs and behind feeders are covered without any per-airport
logic), with times parsed to minutes and weekly frequency precomputed, indexed by
(week, dep_airport) and (week, arr_airport); one `flown` table = each pinned route's operated
dep/arr time and weekly frequency in its launch year; one `routes` table = the pinned set with
its as-if and flown weeks. Rebuild whenever the pinned set or the OAG store changes.

BUILD (John's machine, live store; one-off, expect minutes not hours):
  py -3.12 wave_cache.py --oag C:\\Avia\\oag.duckdb --routes-file pinned_global.json \\
      --out qsi_wave_cache.duckdb

USE:
  from wave_cache import CacheBoards, OagBoards
  boards = CacheBoards("qsi_wave_cache.duckdb")     # back-test runs
  boards = OagBoards(r"C:\\Avia\\oag.duckdb")        # live one-off forecasts
Both expose dep_rows(week, airport) / arr_rows(week, airport) -> list of leg dicts with keys
arr/dep, carrier, alliance, dep_mins, arr_mins, flying, freq, dep_country, arr_country.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from mct_bank import _mins, _dow

_BOARD_COLS = ("week, dep_airport, arr_airport, carrier, alliance, carrier_category, "
               "local_dep_time, local_arr_time, flying_time, elapsed_time, days_of_op, "
               "dep_country, arr_country")


def _flying_mins(flying_time, elapsed_time):
    """Flying minutes from the OAG duration columns ('HH:MM[:SS]' or HHMM), elapsed fallback."""
    for v in (flying_time, elapsed_time):
        if v in (None, ""):
            continue
        s = str(v).strip()
        if ":" in s:
            p = s.split(":")
            try:
                return int(p[0]) * 60 + int(p[1])
            except (ValueError, IndexError):
                continue
        try:
            s4 = str(int(float(s))).zfill(4)
            return int(s4[:-2]) * 60 + int(s4[-2:])
        except (ValueError, TypeError):
            continue
    return 0


def _row_to_leg(r):
    (week, dep, arr, carrier, alliance, cat, dt, at, ft, et, days, dc, ac) = r
    return {
        "week": week, "dep": dep, "arr": arr,
        "carrier": str(carrier or "").strip().upper(),
        "alliance": str(alliance or "").strip(),
        "carrier_category": str(cat or "").strip(),
        "dep_mins": _mins(dt), "arr_mins": _mins(at),
        "flying": _flying_mins(ft, et),
        "freq": float(_dow(days)),
        "dep_country": str(dc or "").strip(), "arr_country": str(ac or "").strip(),
    }


class _Boards:
    """Shared board reader with an in-memory (week, airport, side) cache."""
    _TABLE = "oag"

    def __init__(self, db):
        import duckdb
        self._con = duckdb.connect(db, read_only=True)
        try:
            from db_registry import apply_limits; apply_limits(self._con)   # memory cap + temp + threads
        except Exception:
            pass
        self._cache = {}

    def _rows(self, week, airport, side):
        key = (week, airport, side)
        if key not in self._cache:
            col = "dep_airport" if side == "dep" else "arr_airport"
            rows = self._con.execute(
                f"SELECT {_BOARD_COLS} FROM {self._TABLE} WHERE week=? AND {col}=?",
                [week, airport]).fetchall()
            legs = []
            for r in rows:
                leg = _row_to_leg(r)
                if leg["flying"] > 0 and (leg["dep_mins"] is not None
                                          or leg["arr_mins"] is not None):
                    legs.append(leg)
            self._cache[key] = legs
        return self._cache[key]

    def dep_rows(self, week, airport):
        return self._rows(week, airport, "dep")

    def arr_rows(self, week, airport):
        return self._rows(week, airport, "arr")

    def close(self):
        self._con.close()


class OagBoards(_Boards):
    """Boards straight off the live OAG store (one-off forecasts / the portal)."""
    _TABLE = "oag"


class CacheBoards(_Boards):
    """Boards off the pre-built cache (the many back-test runs)."""
    _TABLE = "boards"

    def flown(self, dep, arr, year, carrier=None):
        """The launched route's actual flown schedule: (dep_mins, arr_mins, weekly_freq,
        flying_mins) or None. Busiest carrier's most frequent timing."""
        q = ("SELECT dep_mins, arr_mins, freq, flying FROM flown "
             "WHERE dep=? AND arr=? AND year=?")
        p = [dep, arr, int(year)]
        if carrier:
            q += " AND carrier=?"
            p.append(str(carrier).upper())
        r = self._con.execute(q + " ORDER BY freq DESC LIMIT 1", p).fetchone()
        return None if r is None else {"dep_mins": r[0], "arr_mins": r[1],
                                       "freq": float(r[2] or 0), "flying": int(r[3] or 0)}

    def routes(self):
        rows = self._con.execute(
            "SELECT dep, arr, year, carrier, type, asif_week, flown_week FROM routes").fetchall()
        return [{"dep": r[0], "arr": r[1], "year": int(r[2]), "carrier": r[3], "type": r[4],
                 "asif_week": r[5], "flown_week": r[6]} for r in rows]


def _weeks_by_year(con):
    wby = {}
    for (w,) in con.execute("SELECT DISTINCT week FROM oag ORDER BY week").fetchall():
        try:
            wby.setdefault(int(str(w)[:4]), []).append(w)
        except (ValueError, TypeError):
            pass
    return wby


def build_cache(oag_db, routes_file, out_db, min_freq=0.0):
    """One-off build. Slices the OAG store to the union of as-if weeks (Y-1) and flown weeks
    (Y+1, falling back to Y) across the pinned set, and records each route's flown schedule."""
    import duckdb
    routes = json.load(open(routes_file))
    src = duckdb.connect(oag_db, read_only=True)
    wby = _weeks_by_year(src)
    src.close()

    def first_week(y):
        ws = wby.get(y)
        return sorted(ws)[0] if ws else None

    plan = []
    weeks = set()
    for r in routes:
        y = int(r["year"])
        asif = first_week(y - 1) or first_week(y)
        flown_wk = first_week(y + 1) or first_week(y)
        if not asif:
            continue
        plan.append({**r, "asif_week": asif, "flown_week": flown_wk})
        weeks.add(asif)
        if flown_wk:
            weeks.add(flown_wk)
    weeks = sorted(weeks)
    print(f"routes: {len(plan)}; weeks to slice: {len(weeks)}")

    if os.path.exists(out_db):
        os.remove(out_db)
    con = duckdb.connect(out_db)
    ph = ",".join("?" * len(weeks))
    con.execute(f"ATTACH '{oag_db}' AS src (READ_ONLY)")
    con.execute(
        f"CREATE TABLE boards AS SELECT {_BOARD_COLS} FROM src.oag WHERE week IN ({ph})",
        weeks)
    con.execute("CREATE INDEX ix_b_dep ON boards (week, dep_airport)")
    con.execute("CREATE INDEX ix_b_arr ON boards (week, arr_airport)")
    n = con.execute("SELECT COUNT(*) FROM boards").fetchone()[0]
    print(f"boards: {n:,} rows")

    con.execute("CREATE TABLE routes (dep VARCHAR, arr VARCHAR, year INT, carrier VARCHAR, "
                "type VARCHAR, asif_week VARCHAR, flown_week VARCHAR)")
    con.execute("CREATE TABLE flown (dep VARCHAR, arr VARCHAR, year INT, carrier VARCHAR, "
                "dep_mins INT, arr_mins INT, freq DOUBLE, flying INT)")
    n_flown = 0
    for p in plan:
        con.execute("INSERT INTO routes VALUES (?,?,?,?,?,?,?)",
                    [p["dep"], p["arr"], p["year"], p.get("carrier"), p.get("type"),
                     p["asif_week"], p.get("flown_week")])
        if not p.get("flown_week"):
            continue
        rows = con.execute(
            "SELECT local_dep_time, local_arr_time, days_of_op, flying_time, elapsed_time, "
            "carrier FROM src.oag WHERE week=? AND dep_airport=? AND arr_airport=?",
            [p["flown_week"], p["dep"], p["arr"]]).fetchall()
        best = {}
        for dt, at, days, ft, et, car in rows:
            dm, am = _mins(dt), _mins(at)
            if dm is None:
                continue
            car = str(car or "").strip().upper()
            f = float(_dow(days))
            k = (car, dm)
            if k not in best:
                best[k] = [dm, am, 0.0, _flying_mins(ft, et)]
            best[k][2] += f
        for (car, dm), (d, a, f, fl) in best.items():
            if f >= min_freq:
                con.execute("INSERT INTO flown VALUES (?,?,?,?,?,?,?,?)",
                            [p["dep"], p["arr"], p["year"], car, d, a, f, fl])
                n_flown += 1
    print(f"flown schedules: {n_flown}")
    con.execute("DETACH src")
    con.close()
    print(f"cache written: {out_db}")


def main():
    ap = argparse.ArgumentParser(description="Build the Engine V2 wave cache from the OAG store.")
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--routes-file", default=os.path.join(HERE, "pinned_global.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "qsi_wave_cache.duckdb"))
    ap.add_argument("--min-freq", type=float, default=0.0)
    a = ap.parse_args()
    if not os.path.exists(a.oag):
        print(f"OAG store not found: {a.oag}")
        return
    build_cache(a.oag, a.routes_file, a.out, a.min_freq)


if __name__ == "__main__":
    main()
