#!/usr/bin/env python3
"""
Avia Cortex - the same-day pack queue (critical path 2A; controller rulings 26 September 2026).
===============================================================================================
A visitor watches a forecast on the stand, the host types their email at the foot of the run,
and the pack of that run leaves the same day. This module holds the job between those two
moments. It sits on the same DuckDB store as the lead record (app/lead_store.py) and never
replaces it: the LEAD is the person and exists from the moment the host captures it; the JOB is
one pack for one run and a lead may have several.

The three states are John's ruling, 26 September:

  NOW     the host sets it. The job sends as soon as the build passes its own checks. No human
          step. For a visitor who needs it for a meeting today.
  HOLD    the default. The build runs at once, then the job waits the configured hold before it
          sends itself, unless a reviewer pauses it. The wait is visible in the queue.
  PAUSED  a reviewer stops it with a one-line reason, or a failed build check puts it there
          automatically. A paused job never sends by itself. Releasing it starts the hold again.

Two rules that are the whole point and are held by tests rather than by intention:

  A BUILD THAT FAILS ANY CHECK GOES TO PAUSED, NEVER TO SEND. There is no path from a failed
  check to a delivered pack. The checks are the safety net on the jobs nobody looks at.

  A SEND IS NOT A SEND WITHOUT THE PROVIDER'S OWN IDENTIFIER. The 21 September SMTP discard is
  why: three messages reported sent that the provider never received. mark_sent refuses a job
  with no message id.

The hold is a SETTING, in minutes, changeable while the server runs (John, 26 September). Zero
means send on pass. It is read at the moment the build passes, so a change reaches every job
that has not yet had its clock started, and the queue shows what each job is actually waiting.

Avia Solutions Limited. All rights reserved.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta

import lead_store as LS

# The states a job can hold. Anything else is a bug, and set_state says so by name.
STATES = ("queued", "building", "ready", "sending", "sent", "failed", "paused")
MODES = ("now", "hold")

DEFAULT_HOLD_MINUTES = 30

# The settings a reviewer or John changes while the server runs. Kept in the store, not in the
# environment, so a change needs no restart and the queue can show the value in force.
SETTING_KEYS = ("hold_minutes",)

_LOCK = threading.Lock()

COLUMNS = [
    ("id", "TEXT"), ("lead_id", "TEXT"),
    ("created_at", "TIMESTAMP"), ("updated_at", "TIMESTAMP"),
    ("captured_by", "TEXT"),
    ("email", "TEXT"), ("name", "TEXT"), ("company", "TEXT"),
    ("route", "TEXT"), ("origin", "TEXT"), ("dest", "TEXT"), ("airline", "TEXT"),
    # The run's own inputs, verbatim. John's download-fidelity ruling: the pack reproduces the
    # run that was on the screen, so the job carries the query rather than re-deriving it.
    ("run_ref", "TEXT"), ("inputs", "TEXT"),
    ("mode", "TEXT"), ("state", "TEXT"),
    ("hold_minutes", "INTEGER"),
    ("build_started_at", "TIMESTAMP"), ("build_passed_at", "TIMESTAMP"),
    ("send_after", "TIMESTAMP"),
    ("failed_check", "TEXT"), ("error", "TEXT"),
    ("paused_by", "TEXT"), ("pause_reason", "TEXT"),
    ("holding_email_at", "TIMESTAMP"), ("holding_email_id", "TEXT"),
    ("pack_path", "TEXT"), ("preview_path", "TEXT"),
    ("sent_at", "TIMESTAMP"),
    ("provider_message_id", "TEXT"), ("provider_status", "TEXT"),
    ("reviewer_note", "TEXT"),
]
COLUMN_NAMES = [c for c, _ in COLUMNS]


class PackQueueError(RuntimeError):
    """Raised with the reason stated, never swallowed."""


def init_schema(con):
    LS.init_schema(con)
    cols = ", ".join("%s %s" % (n, t) for n, t in COLUMNS)
    con.execute("CREATE TABLE IF NOT EXISTS pack_jobs (%s, PRIMARY KEY (id))" % cols)
    con.execute("CREATE SEQUENCE IF NOT EXISTS pack_event_seq START 1")
    con.execute("""CREATE TABLE IF NOT EXISTS pack_events (
                       seq BIGINT PRIMARY KEY, job_id TEXT, occurred_at TIMESTAMP,
                       event TEXT, detail TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS pack_settings (
                       key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP)""")


def connect(path=None, read_only=False):
    con = LS.connect(path=path, read_only=read_only)
    if not read_only:
        init_schema(con)
    return con


def _with(con, path, fn):
    if con is not None:
        return fn(con)
    with _LOCK:
        c = connect(path)
        try:
            return fn(c)
        finally:
            c.close()


def _event(con, job_id, event, detail=None):
    con.execute("INSERT INTO pack_events VALUES (nextval('pack_event_seq'), ?, ?, ?, ?)",
                [job_id, LS.now(), event, detail])


# --------------------------------------------------------------------------- settings
def hold_minutes(con=None, path=None):
    """The configured hold, in minutes. Zero is a legitimate value and means send on pass; it is
    not the same as unset, so the default is only used when nothing has been stored."""
    def go(c):
        row = c.execute("SELECT value FROM pack_settings WHERE key = 'hold_minutes'").fetchone()
        if row is None or row[0] is None or str(row[0]).strip() == "":
            return DEFAULT_HOLD_MINUTES
        try:
            return max(0, int(float(row[0])))
        except (TypeError, ValueError):
            raise PackQueueError("hold_minutes is stored as %r, which is not a number of minutes"
                                 % (row[0],))
    return _with(con, path, go)


def set_hold_minutes(minutes, con=None, path=None):
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        raise PackQueueError("hold must be a whole number of minutes, not %r" % (minutes,))
    if m < 0:
        raise PackQueueError("hold cannot be negative; zero means send as soon as the build passes")
    def go(c):
        c.execute("DELETE FROM pack_settings WHERE key = 'hold_minutes'")
        c.execute("INSERT INTO pack_settings VALUES ('hold_minutes', ?, ?)", [str(m), LS.now()])
        _event(c, None, "hold_minutes_set", str(m))
        return m
    return _with(con, path, go)


# --------------------------------------------------------------------------- the job
def enqueue(email, mode="hold", con=None, path=None, **fields):
    """Queue one pack for one run. Returns the job id. The job carries the run's own inputs, so
    what is built later is the run the visitor watched, not a fresh forecast."""
    mode = (mode or "hold").strip().lower()
    if mode not in MODES:
        raise PackQueueError("mode must be 'now' or 'hold', not %r" % (mode,))
    refusal = LS.email_refusal(email)
    if refusal:
        raise PackQueueError(refusal)
    unknown = [k for k in fields if k not in COLUMN_NAMES]
    if unknown:
        raise PackQueueError("not columns on a pack job: %s" % ", ".join(sorted(unknown)))
    inputs = fields.get("inputs")
    if isinstance(inputs, (dict, list)):
        fields["inputs"] = json.dumps(inputs, sort_keys=True)
    job_id = LS.new_id()
    stamp = LS.now()

    def go(c):
        row = dict.fromkeys(COLUMN_NAMES)
        row.update(fields)
        row["id"] = job_id
        row["email"] = LS.normalise_email(email)
        row["mode"] = mode
        row["state"] = "queued"
        row["created_at"] = stamp
        row["updated_at"] = stamp
        c.execute("INSERT INTO pack_jobs VALUES (%s)" % ", ".join("?" * len(COLUMN_NAMES)),
                  [row[n] for n in COLUMN_NAMES])
        _event(c, job_id, "queued", "mode=%s route=%s" % (mode, row.get("route")))
        return job_id
    return _with(con, path, go)


def get(job_id, con=None, path=None):
    def go(c):
        row = c.execute("SELECT * FROM pack_jobs WHERE id = ?", [job_id]).fetchone()
        if row is None:
            return None
        return dict(zip(COLUMN_NAMES, row))
    return _with(con, path, go)


def _set(c, job_id, event, detail=None, **fields):
    job = c.execute("SELECT id FROM pack_jobs WHERE id = ?", [job_id]).fetchone()
    if job is None:
        raise PackQueueError("no pack job %r" % (job_id,))
    fields["updated_at"] = LS.now()
    sets = ", ".join("%s = ?" % k for k in fields)
    c.execute("UPDATE pack_jobs SET %s WHERE id = ?" % sets,
              list(fields.values()) + [job_id])
    _event(c, job_id, event, detail)
    return job_id


def mark_building(job_id, con=None, path=None):
    return _with(con, path, lambda c: _set(c, job_id, "building",
                                           state="building", build_started_at=LS.now()))


def mark_built(job_id, ok, pack_path=None, preview_path=None, failed_check=None,
               con=None, path=None):
    """The build reports its own verdict. A pass starts the clock; a failure PAUSES the job and
    names the check that failed. There is no route from a failed check to a send."""
    if not ok and not failed_check:
        raise PackQueueError("a failed build must name the check that failed")

    def go(c):
        if not ok:
            return _set(c, job_id, "build_failed", failed_check,
                        state="paused", failed_check=failed_check,
                        paused_by="build checks",
                        pause_reason="build check failed: %s" % failed_check)
        row = c.execute("SELECT mode FROM pack_jobs WHERE id = ?", [job_id]).fetchone()
        if row is None:
            raise PackQueueError("no pack job %r" % (job_id,))
        mode = row[0]
        passed = LS.now()
        held = 0 if mode == "now" else hold_minutes(con=c)
        return _set(c, job_id, "build_passed", "hold=%d min" % held,
                    state="ready", build_passed_at=passed, hold_minutes=held,
                    pack_path=pack_path, preview_path=preview_path,
                    send_after=passed + timedelta(minutes=held),
                    failed_check=None)
    return _with(con, path, go)


def pause(job_id, reason, by="reviewer", con=None, path=None):
    if not (reason or "").strip():
        raise PackQueueError("a pause needs a one-line reason; the queue shows it to whoever "
                             "picks the job up")
    def go(c):
        row = c.execute("SELECT state FROM pack_jobs WHERE id = ?", [job_id]).fetchone()
        if row is None:
            raise PackQueueError("no pack job %r" % (job_id,))
        if row[0] == "sent":
            raise PackQueueError("job %s has already sent; it cannot be paused" % job_id)
        return _set(c, job_id, "paused", reason.strip(),
                    state="paused", paused_by=by, pause_reason=reason.strip())
    return _with(con, path, go)


def release(job_id, con=None, path=None):
    """Put a paused job back on its clock. The hold restarts from now, on the setting in force at
    this moment, so a released job is never instantly overdue by an hour."""
    def go(c):
        row = c.execute("SELECT state, mode FROM pack_jobs WHERE id = ?", [job_id]).fetchone()
        if row is None:
            raise PackQueueError("no pack job %r" % (job_id,))
        if row[0] != "paused":
            raise PackQueueError("job %s is %s, not paused" % (job_id, row[0]))
        if row[1] == "now":
            held = 0
        else:
            held = hold_minutes(con=c)
        return _set(c, job_id, "released", "hold=%d min" % held,
                    state="ready", hold_minutes=held,
                    send_after=LS.now() + timedelta(minutes=held),
                    paused_by=None, pause_reason=None)
    return _with(con, path, go)


def send_now(job_id, by="reviewer", con=None, path=None):
    """The reviewer's second action: stop waiting. Only a job whose build has passed can be sent,
    because there is nothing to send before that."""
    def go(c):
        row = c.execute("SELECT state, build_passed_at FROM pack_jobs WHERE id = ?",
                        [job_id]).fetchone()
        if row is None:
            raise PackQueueError("no pack job %r" % (job_id,))
        if row[1] is None:
            raise PackQueueError("job %s has no completed build; there is nothing to send yet"
                                 % job_id)
        if row[0] == "sent":
            raise PackQueueError("job %s has already sent" % job_id)
        return _set(c, job_id, "send_now", by, state="ready", send_after=LS.now())
    return _with(con, path, go)


def due(at=None, con=None, path=None, limit=50):
    """Jobs whose hold has run out and which nobody has paused. The sender asks for this and for
    nothing else, so a paused job cannot leave by any route."""
    when = at or LS.now()
    def go(c):
        rows = c.execute("SELECT * FROM pack_jobs WHERE state = 'ready' AND send_after IS NOT NULL "
                         "AND send_after <= ? ORDER BY send_after, id LIMIT %d" % int(limit),
                         [when]).fetchall()
        return [dict(zip(COLUMN_NAMES, r)) for r in rows]
    return _with(con, path, go)


def mark_sending(job_id, con=None, path=None):
    return _with(con, path, lambda c: _set(c, job_id, "sending", state="sending"))


def mark_sent(job_id, message_id, provider_status="accepted", con=None, path=None):
    """The provider's identifier is the evidence. Without one this is not a send, whatever the
    transport returned (21 September: SMTP acknowledged three messages Postmark never received)."""
    if not (message_id or "").strip():
        raise PackQueueError("a send is only recorded against the provider's own message id; "
                             "without one the job stays where it is")
    def go(c):
        return _set(c, job_id, "sent", message_id,
                    state="sent", sent_at=LS.now(),
                    provider_message_id=message_id.strip(),
                    provider_status=provider_status, error=None)
    return _with(con, path, go)


def mark_failed(job_id, error, con=None, path=None):
    if not (error or "").strip():
        raise PackQueueError("a failure has to say what failed")
    return _with(con, path, lambda c: _set(c, job_id, "failed", error.strip(),
                                           state="failed", error=error.strip()))


def record_holding_email(job_id, message_id, con=None, path=None):
    """The short note to the visitor that the pack follows, sent when a job is paused, so nothing
    arrives late in silence (John, 26 September)."""
    if not (message_id or "").strip():
        raise PackQueueError("the holding email is recorded against its provider message id")
    return _with(con, path, lambda c: _set(c, job_id, "holding_email", message_id,
                                           holding_email_at=LS.now(),
                                           holding_email_id=message_id.strip()))


def note(job_id, text, con=None, path=None):
    if not (text or "").strip():
        raise PackQueueError("an empty note is not a note")
    return _with(con, path, lambda c: _set(c, job_id, "reviewer_note", text.strip(),
                                           reviewer_note=text.strip()))


def needs_holding_email(con=None, path=None, limit=50):
    """Paused jobs whose visitor has not been told. Read by the sender; a job appears once."""
    def go(c):
        rows = c.execute("SELECT * FROM pack_jobs WHERE state = 'paused' "
                         "AND holding_email_at IS NULL AND email IS NOT NULL "
                         "ORDER BY updated_at LIMIT %d" % int(limit)).fetchall()
        return [dict(zip(COLUMN_NAMES, r)) for r in rows]
    return _with(con, path, go)


def seconds_to_send(job, at=None):
    """What the queue view shows in the 'time to send' column. None where the question does not
    apply (not ready, or no clock yet); negative means overdue and the sender has not run."""
    if not job or job.get("state") != "ready" or job.get("send_after") is None:
        return None
    when = at or LS.now()
    return (job["send_after"] - when).total_seconds()


def listing(state=None, con=None, path=None, limit=200):
    """Newest first, which is the order the reviewer works in."""
    def go(c):
        sql = "SELECT * FROM pack_jobs"
        args = []
        if state:
            sql += " WHERE state = ?"
            args.append(state)
        sql += " ORDER BY created_at DESC, id DESC LIMIT %d" % int(limit)
        rows = c.execute(sql, args).fetchall()
        out = []
        for r in rows:
            job = dict(zip(COLUMN_NAMES, r))
            job["seconds_to_send"] = seconds_to_send(job)
            out.append(job)
        return out
    return _with(con, path, go)


def events_for(job_id, con=None, path=None):
    def go(c):
        rows = c.execute("SELECT occurred_at, event, detail FROM pack_events WHERE job_id = ? "
                         "ORDER BY seq", [job_id]).fetchall()
        return [{"occurred_at": a, "event": b, "detail": d} for a, b, d in rows]
    return _with(con, path, go)


if __name__ == "__main__":
    p = LS.store_path()
    print("pack queue store: %s" % p)
    print("hold: %d minutes" % hold_minutes())
    for j in listing(limit=20):
        print("  %-10s %-22s %-9s %s" % (j["state"], j["route"] or "-", j["mode"], j["email"]))
