#!/usr/bin/env python3
r"""The demo lead store: who asked for a pack, what they were sent, and the quota.

One JSONL file, one line per event, at AVIA_DEMO_LEADS (default E:\Avia\demo_leads.jsonl).
Data lives on the workstation, never in the repo. The quota check and the admin page's
history both read from this one file, because tracking who got what IS the system: the
stand team must never make packs by hand and forward them around it.

THE QUOTA (John's ruling, 16 August 2026): one pack per email per route, with the FIRST
pack free and automatic. Any further request from the same email is HELD PENDING with the
person's history beside it, and needs a one-tap in-system override before it sends.
One-ever is too inflexible (an airline meeting in twenty minutes, three routes), so the
override is a tap on the admin page, not a workaround. In code that reads:

  * an email with no delivered pack and no held request gets its first pack sent;
  * everything after that is held pending, whether it repeats a route or adds one,
    and the reason names which of the two it is;
  * a FAILED send is not a delivered pack, so a retry after a failure is still free.

An event line carries: id, ts, email, domain, route, run_ref, consent, status, held,
approver, pack, reason, params. Statuses: sent / pending / approved+sent / declined /
failed. Later events for the same id update the earlier ones; the first event of an id
carries the run params so an approval can rebuild the pack without the browser.

Avia Solutions Limited. All rights reserved.
"""
import datetime
import json
import os
import uuid

DEFAULT_LEADS = r"E:\Avia\demo_leads.jsonl"

# The demo exists to capture airlines and airports, not hotmail. A named, editable list;
# matched on the exact domain after the last @. Extend as oddities surface.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com", "live.co.uk", "msn.com",
    "yahoo.com", "yahoo.co.uk", "ymail.com", "rocketmail.com",
    "icloud.com", "me.com", "mac.com",
    "proton.me", "protonmail.com", "pm.me",
    "aol.com", "mail.com", "gmx.com", "gmx.de", "gmx.net", "web.de",
    "yandex.com", "yandex.ru", "zoho.com",
    "qq.com", "163.com", "126.com",
}

VALID_STATUSES = ("sent", "pending", "approved+sent", "declined", "failed")


def leads_path():
    """Resolved at call time, not import time, so a test can point AVIA_DEMO_LEADS at a
    temporary folder after this module is imported."""
    return os.environ.get("AVIA_DEMO_LEADS", "").strip() or DEFAULT_LEADS


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id():
    return uuid.uuid4().hex[:12]


def normalise_email(email):
    return (email or "").strip().lower()


def email_domain(email):
    e = normalise_email(email)
    return e.rpartition("@")[2] if "@" in e else ""


def email_refusal(email):
    """None when the address may proceed, else the polite line to show the visitor."""
    e = normalise_email(email)
    dom = email_domain(e)
    if not e or "@" not in e or "." not in dom or " " in e:
        return "That does not look like an email address. Please check it and try again."
    if dom in FREE_MAIL_DOMAINS:
        return ("Please use your work email address. Demonstration forecasts are sent "
                "to airline and airport addresses rather than personal accounts.")
    return None


def route_key(origin, dest):
    return "%s-%s" % ((origin or "").strip().upper(), (dest or "").strip().upper())


# --- the store --------------------------------------------------------------

def append_event(rec, path=None):
    """One JSON line, appended. The caller supplies the fields; ts is stamped here so
    every line carries one, and the id is minted here when the caller has none."""
    p = path or leads_path()
    rec = dict(rec)
    rec.setdefault("id", new_id())
    rec.setdefault("ts", now_iso())
    if rec.get("status") not in VALID_STATUSES:
        raise ValueError("lead status %r is not one of %s" % (rec.get("status"),
                                                              ", ".join(VALID_STATUSES)))
    d = os.path.dirname(os.path.abspath(p))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    return rec["id"]


def read_events(path=None):
    """Every event line, oldest first. A corrupt line is counted and skipped, never
    guessed at; the count rides back so the admin page can say so."""
    p = path or leads_path()
    events, bad = [], 0
    if not os.path.exists(p):
        return events, bad
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                bad += 1
    return events, bad


def merged(events):
    """id -> one record, later events updating earlier ones. The first event of an id
    keeps its request fields (email, route, params); later events move the status on."""
    out = {}
    for ev in events:
        i = ev.get("id")
        if not i:
            continue
        if i not in out:
            out[i] = dict(ev)
        else:
            for k, v in ev.items():
                if v is not None:
                    out[i][k] = v
    return out


def history_for(email, records):
    """That email's requests, oldest first, from merged records."""
    e = normalise_email(email)
    hist = [r for r in records.values() if normalise_email(r.get("email")) == e]
    hist.sort(key=lambda r: r.get("ts") or "")
    return hist


def quota_decision(email, route, records):
    """("send", None) for the free first pack, else ("pending", reason). The reason names
    what the history holds, because the admin page shows it beside the override."""
    hist = history_for(email, records)
    delivered = [r for r in hist if r.get("status") in ("sent", "approved+sent")]
    held = [r for r in hist if r.get("status") == "pending"]
    same = [r for r in delivered if r.get("route") == route]
    if same:
        return ("pending", "this email already received the %s pack on %s"
                % (route, (same[-1].get("ts") or "an earlier date")[:10]))
    if delivered:
        return ("pending", "a further route for this email; already sent: %s"
                % ", ".join(sorted({r.get("route") or "?" for r in delivered})))
    if held:
        return ("pending", "this email already has a request awaiting approval (%s)"
                % ", ".join(sorted({r.get("route") or "?" for r in held})))
    return ("send", None)


# --- request parameters -----------------------------------------------------

def coerce_params(params, defaults):
    """The dashboard sends the forecast query as strings; calibrated endpoints take typed
    keyword arguments. Each value is cast to the type of the endpoint's own default, and
    a key the endpoint does not take is dropped rather than passed through. Booleans are
    parsed, not truth-tested, because bool("0") is True and that class of bug is silent."""
    out = {}
    for k, v in (params or {}).items():
        if k not in defaults:
            continue
        d = defaults[k]
        try:
            if isinstance(d, bool):
                out[k] = str(v).strip().lower() in ("1", "true", "yes", "on")
            elif isinstance(d, int):
                out[k] = int(float(str(v).strip() or 0))
            elif isinstance(d, float):
                out[k] = float(str(v).strip() or 0.0)
            else:
                out[k] = str(v)
        except (TypeError, ValueError):
            # An unparseable override falls back to the endpoint's default by omission,
            # and the run proceeds; a demo request must not 500 on one stray field.
            continue
    return out
