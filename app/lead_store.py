#!/usr/bin/env python3
r"""The stand's record of everyone it met, and what happened to them.

Replaces the JSONL demo lead file (John's ruling 15, 19 September 2026) and widens it to
the four kinds of record a stand actually produces (John, 21 September 2026):

    route   someone ran a forecast. The rich record: what they came to look at, the
            questions they asked, what arose, pricing interest, and the exact run shown.
    card    a business card drop. A photograph and two taps. Fifteen seconds.
    note    a remark worth keeping from someone who left no details. Not a lead at all:
            market intelligence, and the least collected thing at any trade stand.
    voice   the host's own dictated impressions, attached to a record or standing alone.

WHY ONE TABLE AND NOT FOUR. They share a spine (who captured it, when, notes, follow-up)
and they all have to leave together as one flat sheet, because the follow-up work after
Routes is sorting and filtering, not joining. Columns that do not apply to a kind stay
null, which costs nothing and keeps the export honest.

WHY AN EVENT LOG BESIDE THE ROWS. The JSONL it replaces was append-only, and that was its
one real virtue: a build that died still left the lead on disk. `leads` holds the current
state and is edited freely, because the useful detail arrives after the visitor walks away.
`lead_events` is append-only and never edited, so what happened to a record stays
answerable even after the record itself has been corrected.

WHY THE PROVIDER'S OWN IDENTIFIER IS A COLUMN. On 21 September 2026 the mail transport
reported three successes for messages the provider never received. Nothing in our own data
could have contradicted it, because we only stored what we believed. `provider_message_id`
and `provider_status` hold what the PROVIDER says, and `reconcile()` exists to go and ask.
A stand that promises a pack within thirty minutes has to be able to tell the difference
between sent and believed-sent.

Path: AVIA_LEAD_STORE, else LOCAL_CACHE/leads.duckdb. Data lives on the workstation, never
in the repo, per the Avia tool standard.

Avia Solutions Limited. All rights reserved.
"""
from __future__ import annotations

import datetime
import json
import os
import threading
import uuid

KINDS = ("route", "card", "note", "voice")
FILE_KINDS = ("card_photo", "voice_note", "pack")

# Statuses a record can hold. 'captured' is the resting state for card/note/voice, which
# promise nobody anything; the rest describe a pack's journey.
STATUSES = ("captured", "pending", "queued", "sent", "failed", "declined", "approved_sent")

_LOCK = threading.Lock()

# The free-mail list moves across from demo_leads unchanged: the stand exists to capture
# airlines and airports, not hotmail.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com", "live.co.uk", "msn.com",
    "yahoo.com", "yahoo.co.uk", "ymail.com", "rocketmail.com",
    "icloud.com", "me.com", "mac.com",
    "aol.com", "gmx.com", "mail.com", "proton.me", "protonmail.com", "pm.me",
}

COLUMNS = [
    ("id", "TEXT"), ("kind", "TEXT"), ("created_at", "TIMESTAMP"),
    ("updated_at", "TIMESTAMP"), ("captured_by", "TEXT"),
    ("name", "TEXT"), ("company", "TEXT"), ("role", "TEXT"),
    ("email", "TEXT"), ("email_domain", "TEXT"), ("phone", "TEXT"),
    ("route", "TEXT"), ("origin", "TEXT"), ("dest", "TEXT"), ("airline", "TEXT"),
    ("run_ref", "TEXT"), ("params", "TEXT"),
    ("pitching_at_routes", "BOOLEAN"), ("buyer", "BOOLEAN"),
    ("interest", "TEXT"), ("wanted", "TEXT"), ("questions", "TEXT"),
    ("arising", "TEXT"), ("pricing_interest", "TEXT"),
    ("consent", "BOOLEAN"), ("consent_at", "TIMESTAMP"),
    ("status", "TEXT"), ("held", "BOOLEAN"), ("reason", "TEXT"), ("approver", "TEXT"),
    ("pack_path", "TEXT"), ("pack_sent_at", "TIMESTAMP"), ("pack_error", "TEXT"),
    ("provider_message_id", "TEXT"), ("provider_status", "TEXT"),
    ("provider_checked_at", "TIMESTAMP"),
    ("follow_up_owner", "TEXT"), ("follow_up_date", "DATE"),
    ("follow_up_done", "BOOLEAN"), ("notes", "TEXT"),
]
COLUMN_NAMES = [c for c, _ in COLUMNS]
# Set by the caller, not by us. id, kind and the timestamps are ours.
WRITABLE = [c for c in COLUMN_NAMES if c not in ("id", "kind", "created_at", "updated_at")]


class LeadStoreError(RuntimeError):
    """Raised with the reason stated, never swallowed."""


def store_path():
    p = os.environ.get("AVIA_LEAD_STORE", "").strip()
    if p:
        return p
    try:
        from config import LOCAL_CACHE
        return os.path.join(str(LOCAL_CACHE), "leads.duckdb")
    except Exception as e:                                       # noqa: BLE001
        raise LeadStoreError("no lead store path: config did not load (%s: %s) and "
                             "AVIA_LEAD_STORE is not set" % (type(e).__name__, e))


def now():
    return datetime.datetime.now()


def new_id():
    return uuid.uuid4().hex[:12]


def normalise_email(email):
    return (email or "").strip().lower()


def email_domain(email):
    e = normalise_email(email)
    return e.rsplit("@", 1)[-1] if "@" in e else ""


def email_refusal(email):
    """None if the address is usable, else the reason in words a host can read aloud."""
    e = normalise_email(email)
    if not e:
        return "an email address is needed to send a pack"
    if "@" not in e or e.startswith("@") or e.endswith("@"):
        return "that does not look like an email address"
    d = email_domain(e)
    if "." not in d:
        return "that email domain does not look complete"
    if d in FREE_MAIL_DOMAINS:
        return ("a work email address is needed, because the pack goes to the airline or "
                "airport rather than to a personal account")
    return None


def route_key(origin, dest):
    o, d = (origin or "").strip().upper(), (dest or "").strip().upper()
    return "%s-%s" % (o, d) if o and d else ""


def connect(path=None, read_only=False):
    import duckdb
    p = path or store_path()
    folder = os.path.dirname(p)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    con = duckdb.connect(p, read_only=read_only)
    if not read_only:
        init_schema(con)
    return con


def init_schema(con):
    cols = ", ".join("%s %s" % (n, t) for n, t in COLUMNS)
    con.execute("CREATE TABLE IF NOT EXISTS leads (%s, PRIMARY KEY (id))" % cols)
    con.execute("CREATE SEQUENCE IF NOT EXISTS lead_event_seq START 1")
    con.execute("""CREATE TABLE IF NOT EXISTS lead_events (
                       seq BIGINT PRIMARY KEY, lead_id TEXT, occurred_at TIMESTAMP,
                       event TEXT, detail TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS lead_files (
                       id TEXT PRIMARY KEY, lead_id TEXT, kind TEXT, path TEXT,
                       added_at TIMESTAMP, note TEXT)""")


def _event(con, lead_id, event, detail=None):
    con.execute("INSERT INTO lead_events VALUES (nextval('lead_event_seq'), ?, ?, ?, ?)",
                [lead_id, now(), event, detail])


def capture(kind, con=None, path=None, **fields):
    """Write a record and return its id. The record exists from this moment, whatever
    happens to any pack afterwards: that separation is the point."""
    if kind not in KINDS:
        raise LeadStoreError("kind must be one of %s, not %r" % (", ".join(KINDS), kind))
    unknown = [k for k in fields if k not in WRITABLE]
    if unknown:
        raise LeadStoreError("no such field(s) on a lead: %s" % ", ".join(sorted(unknown)))
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        with _LOCK:
            lead_id = new_id()
            rec = {k: None for k in COLUMN_NAMES}
            rec.update(fields)
            rec["id"], rec["kind"] = lead_id, kind
            rec["created_at"] = rec["updated_at"] = now()
            if rec.get("email"):
                rec["email"] = normalise_email(rec["email"])
                rec["email_domain"] = email_domain(rec["email"])
            if rec.get("origin") or rec.get("dest"):
                rec["route"] = rec.get("route") or route_key(rec.get("origin"), rec.get("dest"))
            if isinstance(rec.get("params"), dict):
                rec["params"] = json.dumps(rec["params"], sort_keys=True)
            if not rec.get("status"):
                rec["status"] = "pending" if kind == "route" else "captured"
            own.execute("INSERT INTO leads VALUES (%s)" % ", ".join("?" * len(COLUMN_NAMES)),
                        [rec[c] for c in COLUMN_NAMES])
            _event(own, lead_id, "captured", kind)
            return lead_id
    finally:
        if close:
            own.close()


def update(lead_id, con=None, path=None, event="updated", **fields):
    """Edit a record after the moment, which is when the useful detail arrives."""
    unknown = [k for k in fields if k not in WRITABLE]
    if unknown:
        raise LeadStoreError("no such field(s) on a lead: %s" % ", ".join(sorted(unknown)))
    if not fields:
        return 0
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        with _LOCK:
            if not own.execute("SELECT 1 FROM leads WHERE id = ?", [lead_id]).fetchone():
                raise LeadStoreError("no lead with id %r" % lead_id)
            if fields.get("email"):
                fields["email"] = normalise_email(fields["email"])
                fields["email_domain"] = email_domain(fields["email"])
            if isinstance(fields.get("params"), dict):
                fields["params"] = json.dumps(fields["params"], sort_keys=True)
            names = sorted(fields)
            own.execute("UPDATE leads SET %s, updated_at = ? WHERE id = ?"
                        % ", ".join("%s = ?" % n for n in names),
                        [fields[n] for n in names] + [now(), lead_id])
            _event(own, lead_id, event, ", ".join(names))
            return 1
    finally:
        if close:
            own.close()


def add_note(lead_id, text, con=None, path=None):
    """Append rather than replace. A second thought does not erase the first."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        row = own.execute("SELECT notes FROM leads WHERE id = ?", [lead_id]).fetchone()
        if row is None:
            raise LeadStoreError("no lead with id %r" % lead_id)
        stamp = now().strftime("%d %b %H:%M")
        merged = ("%s\n[%s] %s" % (row[0], stamp, text)).strip() if row[0] else \
                 "[%s] %s" % (stamp, text)
        return update(lead_id, con=own, event="note_added", notes=merged)
    finally:
        if close:
            own.close()


def add_file(lead_id, kind, path_on_disk, note=None, con=None, path=None):
    if kind not in FILE_KINDS:
        raise LeadStoreError("file kind must be one of %s, not %r"
                             % (", ".join(FILE_KINDS), kind))
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        with _LOCK:
            fid = new_id()
            own.execute("INSERT INTO lead_files VALUES (?, ?, ?, ?, ?, ?)",
                        [fid, lead_id, kind, path_on_disk, now(), note])
            _event(own, lead_id, "file_added", "%s: %s" % (kind, path_on_disk))
            return fid
    finally:
        if close:
            own.close()


def record_send(lead_id, message_id=None, status="sent", error=None, con=None, path=None):
    """What the PROVIDER said, not what we hoped. message_id is its own identifier for the
    message; without one, nothing here should be read as proof that anything was sent."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        fields = {"status": status, "pack_error": error}
        if message_id:
            fields["provider_message_id"] = message_id
            fields["pack_sent_at"] = now()
        update(lead_id, con=own, event="send_%s" % status,
               **{k: v for k, v in fields.items() if v is not None or k == "pack_error"})
        return message_id
    finally:
        if close:
            own.close()


def reconcile(fetcher, con=None, path=None, limit=200):
    """Ask the provider what it holds for every message we think we sent, and write the
    answer back. This exists because on 21 September 2026 our own data said three messages
    had been sent and the provider had never heard of them. fetcher takes a message id and
    returns a status string, or None if the provider does not recognise it."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        rows = own.execute("""SELECT id, provider_message_id FROM leads
                              WHERE provider_message_id IS NOT NULL
                              ORDER BY pack_sent_at DESC LIMIT ?""", [limit]).fetchall()
        checked, disagreed = 0, []
        for lead_id, mid in rows:
            state = fetcher(mid)
            checked += 1
            update(lead_id, con=own, event="reconciled",
                   provider_status=state or "unknown to the provider",
                   provider_checked_at=now())
            if not state:
                disagreed.append(lead_id)
        return {"checked": checked, "disagreed": disagreed}
    finally:
        if close:
            own.close()


def get(lead_id, con=None, path=None):
    own, close = (con, False) if con is not None else (connect(path, read_only=False), True)
    try:
        row = own.execute("SELECT * FROM leads WHERE id = ?", [lead_id]).fetchone()
        return dict(zip(COLUMN_NAMES, row)) if row else None
    finally:
        if close:
            own.close()


def events_for(lead_id, con=None, path=None):
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        rows = own.execute("""SELECT seq, occurred_at, event, detail FROM lead_events
                              WHERE lead_id = ? ORDER BY seq""", [lead_id]).fetchall()
        return [dict(zip(("seq", "occurred_at", "event", "detail"), r)) for r in rows]
    finally:
        if close:
            own.close()


def listing(kind=None, status=None, con=None, path=None, limit=500):
    """Newest first, because the stand reads the last hour far more than the first day."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        where, args = [], []
        if kind:
            where.append("kind = ?")
            args.append(kind)
        if status:
            where.append("status = ?")
            args.append(status)
        sql = "SELECT * FROM leads"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        return [dict(zip(COLUMN_NAMES, r)) for r in own.execute(sql, args).fetchall()]
    finally:
        if close:
            own.close()


def quota_decision(email, route, con=None, path=None):
    """John's ruling of 16 August, carried across unchanged: the first pack to an address is
    free and automatic; everything after it is held for a one-tap approval, with the reason
    naming which case it is. A failed send is not a delivered pack, so a retry stays free."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        e = normalise_email(email)
        rows = own.execute("""SELECT route, status, held FROM leads
                              WHERE email = ? AND kind = 'route'""", [e]).fetchall()
        delivered = [r for r in rows if r[1] in ("sent", "approved_sent")]
        held = [r for r in rows if r[1] == "pending" and r[2]]
        if not delivered and not held:
            return "send", "first pack for this address"
        if any(r[0] == route for r in delivered):
            return "pending", "a pack for %s has already gone to this address" % route
        if delivered:
            return "pending", ("this address already has a pack for %s"
                               % ", ".join(sorted({r[0] for r in delivered if r[0]})))
        return "pending", "a request from this address is already waiting for approval"
    finally:
        if close:
            own.close()


def migrate_jsonl(jsonl_path, con=None, path=None):
    """Bring the JSONL demo lead file across and leave it behind, per ruling 15: the two are
    not kept side by side. Returns what happened, including lines that could not be read,
    because a migration that silently drops records is worse than one that refuses."""
    own, close = (con, False) if con is not None else (connect(path), True)
    try:
        if not os.path.exists(jsonl_path):
            return {"read": 0, "written": 0, "unreadable": 0, "note": "no file at that path"}
        records, unreadable = {}, 0
        with open(jsonl_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    unreadable += 1
                    continue
                rid = rec.get("id") or new_id()
                records.setdefault(rid, {}).update(rec)
        written = 0
        for rid, rec in records.items():
            fields = {"name": rec.get("name"), "company": rec.get("company"),
                      "role": rec.get("role"), "email": rec.get("email"),
                      "phone": rec.get("phone"), "route": rec.get("route"),
                      "airline": rec.get("airline"), "run_ref": rec.get("run_ref"),
                      "consent": rec.get("consent"), "status": rec.get("status"),
                      "held": rec.get("held"), "reason": rec.get("reason"),
                      "approver": rec.get("approver"), "pack_path": rec.get("pack"),
                      "notes": rec.get("notes")}
            if rec.get("params"):
                fields["params"] = json.dumps(rec["params"], sort_keys=True)
            fields = {k: v for k, v in fields.items() if v is not None}
            capture("route", con=own, **fields)
            written += 1
        return {"read": len(records), "written": written, "unreadable": unreadable}
    finally:
        if close:
            own.close()


def export_rows(con=None, path=None):
    """One flat sheet, every record, newest first. The follow-up work after Routes is
    sorting and filtering, so nothing here needs joining to be useful."""
    return listing(con=con, path=path, limit=100000)
