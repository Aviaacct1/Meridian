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


def pretty_label(label):
    """A snapshot label for HUMAN text: '25 May 2026' or 'July 2026' (house style,
    DD Month YYYY, no leading zero). ISO stays in machine contexts (payload fields,
    manifests, the mono provenance rail) where the brand guidelines want it. John's
    ruling, 15 August: a heading is for people, and three continents read this page."""
    label = str(label or "").strip()
    try:
        if len(label) == 10:
            d = _dt.date.fromisoformat(label)
            return "%d %s %d" % (d.day, d.strftime("%B"), d.year)
        if len(label) == 7:
            return "%s %d" % (_dt.date(int(label[:4]), int(label[5:7]), 1).strftime("%B"),
                              int(label[:4]))
    except ValueError:
        pass
    return label


def _labels(con, airport=None):
    """The airport's snapshot labels by form: weekly YYYY-MM-DD and monthly YYYY-MM,
    each as (date, label) ascending. Half-month and half-year label forms are excluded
    on purpose; they belong to their own spine and must never mingle with these.

    airport, when given, restricts to labels that actually CONTAIN that airport: with
    REGIONAL pulls (Jess's monthly template, one file per region), the newest label in
    the store may cover one region only, and picking it globally would compare an
    airport against a snapshot that never held it and report every service as dropped."""
    if airport:
        rows = con.execute(
            "SELECT DISTINCT week FROM oag WHERE dep_airport = ? OR arr_airport = ?",
            [airport, airport]).fetchall()
    else:
        rows = con.execute("SELECT DISTINCT week FROM oag").fetchall()
    weekly, monthly = [], []
    for (w,) in rows:
        w = str(w or "").strip()
        try:
            if len(w) == 10:
                weekly.append((_dt.date.fromisoformat(w), w))
            elif len(w) == 7:
                monthly.append((_dt.date(int(w[:4]), int(w[5:7]), 1), w))
        except ValueError:
            continue
    return sorted(weekly), sorted(monthly)


def pick_weeks(con, airport=None):
    """(current_label, prior_label, gap_note, form). Weekly snapshots are preferred
    where the airport has them; otherwise the monthly spine, which is what Jess's
    regional template actually produces (established from the Egnyte Data Store on
    15 August: <Region> <Mon> <YYYY>.xlsx, monthly, seven regions). Current = the
    latest label holding the airport; prior = the label nearest one year before it.
    The gap is REPORTED rather than assumed healthy."""
    weekly, monthly = _labels(con, airport)
    # Prefer the spine that can actually compare. A single weekly label used to fall
    # through to an EMPTY monthly spine and the airport reported "no snapshots" while
    # holding one (caught by the fixture test, 16 August); one label is an answer with
    # a stated no-comparison note, not an absence.
    if len(weekly) >= 2:
        form, labels = "weekly", weekly
    elif len(monthly) >= 2:
        form, labels = "monthly", monthly
    else:
        form, labels = ("weekly", weekly) if weekly else ("monthly", monthly)
    if not labels:
        return None, None, "no weekly or monthly snapshots hold this airport", None
    if len(labels) == 1:
        return labels[0][1], labels[0][1], "only one snapshot holds this airport; no comparison possible", form
    cur_d, cur = labels[-1]
    target = (cur_d - _dt.timedelta(days=364)) if form == "weekly" else \
             _dt.date(cur_d.year - 1, cur_d.month, 1)
    prior_d, prior = min(labels[:-1], key=lambda t: abs((t[0] - target).days))
    gap = abs((prior_d - target).days)
    note = None
    if form == "weekly" and gap > 42:
        note = ("nearest prior snapshot is %s, %d days from a clean year-on-year; read "
                "the deltas as indicative" % (prior, gap))
    elif form == "monthly" and gap > 62:
        note = ("nearest prior month is %s, not the same month a year earlier; seasonal "
                "differences are in the deltas" % prior)
    return cur, prior, note, form


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
        cur, prior, note, form = pick_weeks(con, airport)
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
               "week_display": pretty_label(cur), "prior_week_display": pretty_label(prior),
               "label_form": form,
               "basis": ("OAG scheduled passenger service, %s snapshot %s against %s. "
                         "Static extract, not a live feed."
                         % (form, pretty_label(cur), pretty_label(prior))),
               "moves": one(airport), "competitors": {}}
        if note:
            out["vintage_note"] = note
        for c in (competitors or [])[:4]:
            c = (c or "").strip().upper()
            if not c or c == airport:
                continue
            # A competitor in a region the chosen snapshot does not cover must say so,
            # not report its every service as dropped.
            _cw, _cm = _labels(con, c)
            c_weeks = {w for _, w in (_cw if form == "weekly" else _cm)}
            if cur not in c_weeks:
                out["competitors"][c] = {"error": "not covered by the snapshot of %s; its "
                                                  "region may not be in this pull"
                                                  % pretty_label(cur)}
            else:
                out["competitors"][c] = one(c)
        return out
    finally:
        con.close()


DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def daily_seats(db, airport):
    """Departing seats by day of week, the latest snapshot against the year-earlier one.

    DEPARTING seats, not two-way: a based rotation departs and returns, and summing both
    directions counts the same aircraft twice (John's ruling, 15 August). The basis is
    stated in the payload so the chart can state it.

    THE DEDUPE, and it is the trap frequency_frame documents: days_of_op is a
    seven-character mask (digits 1-7 = operating days, SSIM convention, 1 = Monday) and
    the store repeats one schedule record per REGION label, so a straight sum over rows
    multiplies every flight by the number of regions that see it. One figure per
    (carrier, flight_no, dep, arr, local_dep_time), max(mask) and max(seats) across the
    duplicates (they are copies of one record), BEFORE any summing.

    A record whose mask holds no digit cannot be placed on a day. It is left out and
    COUNTED, never spread evenly: flag rather than fill."""
    airport = (airport or "").strip().upper()
    con = _con(db)
    try:
        cur, prior, note, form = pick_weeks(con, airport)
        if not cur:
            return {"ok": False, "error": note or "no snapshots hold this airport"}
        svc = _svc_filter(con)

        def one(week):
            rows = con.execute(
                f"WITH d AS ("
                f"  SELECT carrier, flight_no, dep_airport, arr_airport, local_dep_time, "
                f"         max(coalesce(days_of_op, '')) AS mask, "
                f"         max(coalesce(TRY_CAST(seats_total AS DOUBLE), 0.0)) AS seats "
                f"  FROM oag WHERE week = ? AND dep_airport = ? AND {svc} "
                f"  GROUP BY 1, 2, 3, 4, 5) "
                f"SELECT mask, seats FROM d", [week, airport]).fetchall()
            days = [0.0] * 7
            unplaced = 0
            for mask, seats in rows:
                hit = False
                for ch in str(mask or ""):
                    if ch in "1234567":
                        days[int(ch) - 1] += float(seats or 0)
                        hit = True
                if not hit:
                    unplaced += 1
            return [round(v) for v in days], unplaced

        cur_days, cur_un = one(cur)
        out = {"ok": True, "airport": airport, "days": list(DAY_NAMES),
               "week": cur, "week_display": pretty_label(cur), "label_form": form,
               "current": cur_days,
               "basis": ("OAG scheduled passenger service, departing seats by day of "
                         "operation at %s (SSIM days, Monday first), deduplicated to one "
                         "record per flight. %s snapshot %s against %s. Static extract, "
                         "not a live feed."
                         % (airport, form.capitalize(), pretty_label(cur),
                            pretty_label(prior)))}
        notes = []
        if prior and prior != cur:
            out["prior_week"], out["prior_week_display"] = prior, pretty_label(prior)
            prior_days, pri_un = one(prior)
            out["prior"] = prior_days
            if pri_un:
                notes.append("%d prior-snapshot record%s carried no operating-day mask "
                             "and %s left out, not spread"
                             % (pri_un, "" if pri_un == 1 else "s",
                                "is" if pri_un == 1 else "are"))
        else:
            notes.append("no year-earlier snapshot holds this airport; the comparator "
                         "series is absent, not zero")
        if cur_un:
            notes.append("%d current-snapshot record%s carried no operating-day mask "
                         "and %s left out, not spread"
                         % (cur_un, "" if cur_un == 1 else "s",
                            "is" if cur_un == 1 else "are"))
        if note:
            notes.append(note)
        if notes:
            out["notes"] = notes
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
