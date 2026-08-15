#!/usr/bin/env python3
"""
Avia Solutions - Route Watch: the monitoring view, from the stores we hold.
===========================================================================
WHAT THIS IS. The skeleton of the monitoring option (the +5k tier in the 15 August
pricing note): capacity moves at an airport, competitor moves beside them, and the
demand trend, every figure wearing its vintage. An ASD team opens it weekly; a case
tool gets opened when there is a case.

WHAT IT IS NOT, stated because a silent shortfall here would be the recorded shape:
the OAG store is a STATIC EXTRACT, not a live feed. Version one therefore compares
the latest loaded weekly snapshot against the nearest snapshot circa a year earlier
and says so on every block. Continuous weekly monitoring is a data subscription
decision, not a code change. Demand runs on annual Sabre vintages until the monthly
pull lands, and is labelled with its year for the same reason.

Week labels: the store mixes label forms (single week, month, half-year; see
OAG-WEEK, 11 August). Only the YYYY-MM-DD weekly form is used here, chosen by DATE
rather than string order, which is the trap the log records.
"""
import datetime as _dt
import os

import duckdb


# A schedule change smaller than this share is noise between two snapshots a year
# apart (equipment swaps week to week); at or above it, it is a decision.
CHANGE_SHARE = 0.10


def _con(db):
    return duckdb.connect(db, read_only=True)


def _weekly_labels(con):
    """The YYYY-MM-DD week labels, as dates, ascending. Other label forms excluded."""
    rows = con.execute("SELECT DISTINCT week FROM oag").fetchall()
    out = []
    for (w,) in rows:
        w = str(w or "").strip()
        if len(w) == 10:
            try:
                out.append((_dt.date.fromisoformat(w), w))
            except ValueError:
                continue
    return sorted(out)


def pick_weeks(con):
    """(current_label, prior_label, gap_note). Current = latest weekly snapshot; prior =
    the snapshot nearest 364 days before it. The gap is REPORTED rather than assumed
    healthy: a store with only two adjacent weeks returns them and says so."""
    weeks = _weekly_labels(con)
    if not weeks:
        return None, None, "no weekly-form snapshots in the store"
    cur_d, cur = weeks[-1]
    target = cur_d - _dt.timedelta(days=364)
    prior_d, prior = min(weeks[:-1] or weeks, key=lambda t: abs((t[0] - target).days))
    gap = abs((prior_d - target).days)
    note = None
    if prior == cur:
        note = "only one weekly snapshot is loaded; no comparison possible"
    elif gap > 42:
        note = ("nearest prior snapshot is %s, %d days from a clean year-on-year; read "
                "the deltas as indicative" % (prior, gap))
    return cur, prior, note


def _svc_filter(con):
    """Scheduled passenger service only, matching oag_served's rule so the two views
    cannot disagree about what counts as service."""
    try:
        import oag_served as OS
        return OS._service_filter(con)
    except Exception:
        return "1=1"


def _routes(con, airport, week, svc):
    """{(carrier, other_airport, direction): {freq, seats}} for one snapshot week."""
    out = {}
    for dep, arr, direction in ((airport, None, "out"), (None, airport, "in")):
        cond = "dep_airport = ?" if direction == "out" else "arr_airport = ?"
        rows = con.execute(
            f"SELECT carrier, {'arr_airport' if direction == 'out' else 'dep_airport'}, "
            f"       SUM(COALESCE(TRY_CAST(frequency AS DOUBLE), 1.0)), "
            f"       SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE), 0.0) "
            f"           * COALESCE(TRY_CAST(frequency AS DOUBLE), 1.0)) "
            f"FROM oag WHERE week = ? AND {cond} AND {svc} "
            f"GROUP BY 1, 2", [week, airport]).fetchall()
        for carrier, other, freq, seats in rows:
            c, o = (carrier or "").strip().upper(), (other or "").strip().upper()
            if not c or not o:
                continue
            key = (c, o, direction)
            out[key] = {"freq": float(freq or 0), "seats": float(seats or 0)}
    return out


def capacity_moves(db, airport, competitors=None):
    """New, dropped and changed services at an airport (and optionally beside its
    competitors), latest weekly snapshot against the nearest year-earlier one."""
    airport = (airport or "").strip().upper()
    con = _con(db)
    try:
        cur, prior, note = pick_weeks(con)
        if not cur or prior == cur:
            return {"ok": False, "error": note or "no comparable snapshots"}
        svc = _svc_filter(con)

        def one(iata):
            now, then = _routes(con, iata, cur, svc), _routes(con, iata, prior, svc)
            new, dropped, changed = [], [], []
            for k, v in now.items():
                if k not in then:
                    new.append({"carrier": k[0], "airport": k[1], "direction": k[2],
                                "weekly_freq": round(v["freq"], 1),
                                "weekly_seats": round(v["seats"])})
                else:
                    f0, f1 = then[k]["freq"], v["freq"]
                    s0, s1 = then[k]["seats"], v["seats"]
                    if f0 and abs(f1 - f0) / f0 >= CHANGE_SHARE or \
                       s0 and abs(s1 - s0) / s0 >= CHANGE_SHARE:
                        changed.append({"carrier": k[0], "airport": k[1], "direction": k[2],
                                        "freq": [round(f0, 1), round(f1, 1)],
                                        "seats": [round(s0), round(s1)]})
            for k, v in then.items():
                if k not in now:
                    dropped.append({"carrier": k[0], "airport": k[1], "direction": k[2],
                                    "weekly_freq": round(v["freq"], 1)})
            srt = lambda rows, key: sorted(rows, key=lambda r: -(r.get(key) or 0))
            return {"new": srt(new, "weekly_seats")[:40],
                    "dropped": srt(dropped, "weekly_freq")[:40],
                    "changed": sorted(changed, key=lambda r: -(r["seats"][1] or 0))[:40]}

        out = {"ok": True, "airport": airport, "week": cur, "prior_week": prior,
               "basis": ("OAG scheduled passenger service, weekly snapshot %s against %s. "
                         "Static extract, not a live feed." % (cur, prior)),
               "moves": one(airport), "competitors": {}}
        if note:
            out["vintage_note"] = note
        for c in (competitors or [])[:4]:
            c = (c or "").strip().upper()
            if c and c != airport:
                out["competitors"][c] = one(c)
        return out
    finally:
        con.close()


def demand_trend(db, airport, n_years=6):
    """Two-way O&D passengers touching the airport, by Sabre vintage, latest n years.
    Annual and labelled as such: the monthly pull is a data job, not this module's."""
    airport = (airport or "").strip().upper()
    con = _con(db)
    try:
        rows = con.execute(
            "SELECT source_year, SUM(passengers) FROM sabre "
            "WHERE origin_airport = ? OR destination_airport = ? "
            "GROUP BY 1 ORDER BY 1 DESC LIMIT ?", [airport, airport, n_years]).fetchall()
    finally:
        con.close()
    series = [{"year": int(y), "pax": round(float(p or 0))} for y, p in sorted(rows)]
    return {"ok": bool(series), "airport": airport, "series": series,
            "basis": ("Sabre O&D, two-way passengers touching %s, by data vintage. 2021 "
                      "mixes 2020 and 2021 travel (SOURCE-YEAR-2021); read it accordingly."
                      % airport)}
