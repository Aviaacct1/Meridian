#!/usr/bin/env python3
r"""
Avia Solutions - the refresh pickup: what to ingest, decided provably.
======================================================================
The orchestrator for the weekly/monthly data refresh (REFRESH-PIPELINE-NOTE-15Aug2026).
Jess downloads to Egnyte; this scans the pickup folders, classifies every file against
the naming AS IT ACTUALLY IS (case variants tolerated, half-month files routed to their
own spine, Sabre variant tokens ignored in favour of the year), checks the manifest,
and produces a PLAN: ingest, re-ingest (drop-and-reload), hold, refuse, skip. By
default it EXECUTES NOTHING (--plan-only is the default); --execute runs the OAG
monthly loads through oag_ingest_periodic. Sabre annual files are never auto-executed:
a 7GB world load is a deliberate act, and the plan says so rather than doing it.

THE VINTAGE GUARD lives here as a refusal, not a runbook line: a Sabre file for a year
that is not yet complete is planned as HOLD, because the engine takes max(source_year)
as its base year and a partial year must never advance it (SOURCE-YEAR-2021 is what the
absence of this rule looks like).

Run on the WORKSTATION (data root E:\Avia, Egnyte drive Z:):
    py -3.12 refresh_pickup.py --plan-only
    py -3.12 refresh_pickup.py --execute
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FOLDER = os.environ.get(
    "AVIA_PICKUP_DIR", r"Z:\Shared\Company Data\18 Products\QSI\Data Store")
DEFAULT_MANIFEST = os.environ.get(
    "AVIA_REFRESH_MANIFEST", r"E:\Avia\refresh_manifest.json")
DEFAULT_STATUS = os.environ.get(
    "AVIA_REFRESH_STATUS", r"E:\Avia\refresh_status.json")
HASH_LIMIT = 1_000_000_000   # hash files below 1GB; above, size stands in (Sabre CSVs)

# Canonical regions, case-folded. "Latin america" and "MiddlE East" are in the folder
# today; an ingest must never fail on a colleague's shift key.
REGIONS = {"africa": "Africa", "asia": "Asia", "europe": "Europe",
           "latin america": "Latin America", "middle east": "Middle East",
           "north america": "North America", "southwest pacific": "Southwest Pacific"}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

_MONTHLY = re.compile(r"^(?P<region>[A-Za-z ]+?)\s+(?P<mon>[A-Za-z]{3})\s+(?P<year>20\d\d)\.xlsx$", re.I)
_HALF = re.compile(r"^(?P<region>[A-Za-z ]+?)\s+01(?P<m1>[A-Za-z]{3})\s+to\s+15(?P<m2>[A-Za-z]{3})\s+(?P<year>20\d\d)\.xlsx$", re.I)
_SABRE = re.compile(r"^World(?P<year>20\d\d).*\.csv$", re.I)


def classify(name, today=None):
    """One file name -> what it is, or why it is refused. Pure, so it is testable."""
    today = today or _dt.date.today()
    m = _HALF.match(name)
    if m:
        region = REGIONS.get(m.group("region").strip().lower())
        if not region:
            return {"action": "refuse", "name": name,
                    "reason": "unknown region %r" % m.group("region")}
        return {"action": "hold", "name": name, "source": "oag_halfmonth",
                "region": region, "year": int(m.group("year")),
                "reason": "half-month file: belongs to the AVIA_BT2_HALFYEAR spine, "
                          "never the monthly one; load it with that switch, deliberately"}
    m = _MONTHLY.match(name)
    if m:
        region = REGIONS.get(m.group("region").strip().lower())
        mon = MONTHS.get(m.group("mon").strip().lower())
        if not region:
            return {"action": "refuse", "name": name,
                    "reason": "unknown region %r" % m.group("region")}
        if not mon:
            return {"action": "refuse", "name": name,
                    "reason": "unknown month %r" % m.group("mon")}
        year = int(m.group("year"))
        return {"action": "ingest", "name": name, "source": "oag_monthly",
                "region": region, "label": "%04d-%02d" % (year, mon), "year": year}
    m = _SABRE.match(name)
    if m:
        year = int(m.group("year"))
        out = {"name": name, "source": "sabre_annual", "year": year,
               "directionality": "ND" if re.search(r"ND", name) else "POO",
               "label": str(year)}
        if year >= today.year:
            # THE VINTAGE GUARD. The engine's base year is max(source_year); a file for
            # a year still in progress must not advance it. Held, with the reason.
            out.update(action="hold",
                       reason="year %d is not complete; ingesting it would advance the "
                              "engine's base year onto a partial vintage. Load only "
                              "when the year is closed, or under a partial label" % year)
        else:
            # Complete years still do not auto-run: a 7GB world load is deliberate.
            out.update(action="confirm",
                       reason="Sabre annual loads run by hand: py -3.12 sabre_ingest.py "
                              "--csv <file> --year %d --directionality %s"
                              % (year, out["directionality"]))
        return out
    if name.lower().endswith((".py", ".txt")):
        return {"action": "skip", "name": name, "reason": "tooling, not data"}
    return {"action": "refuse", "name": name, "reason": "unrecognised name pattern"}


def _fingerprint(path):
    size = os.path.getsize(path)
    if size >= HASH_LIMIT:
        return "size:%d" % size
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:%s" % h.hexdigest()


def load_manifest(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_manifest(man, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)


def plan(folder, manifest, today=None):
    """Scan one level of the pickup folder (never `old/`; agreed layout is flat) and
    decide per file. Returns the plan dict; changes nothing on disk."""
    out = {"ingest": [], "reingest": [], "hold": [], "confirm": [], "refuse": [], "skip": []}
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            continue
        c = classify(name, today=today)
        if c["action"] in ("refuse", "skip", "hold", "confirm"):
            out[c["action"]].append(c)
            continue
        key = "%s|%s|%s" % (c["source"], c.get("region", "-"), c["label"])
        fp = _fingerprint(path)
        prev = manifest.get(key)
        c["key"], c["fingerprint"], c["path"] = key, fp, path
        if prev is None:
            out["ingest"].append(c)
        elif prev.get("fingerprint") == fp:
            c["reason"] = "already ingested, unchanged"
            out["skip"].append(c)
        else:
            # A re-arrived label is a corrected extract: a deliberate drop-and-reload
            # of that period, never a silent second copy (the T-100 double-load scar).
            c["reason"] = ("label already ingested from %r; this file differs, so the "
                           "period must be dropped and reloaded" % prev.get("name"))
            out["reingest"].append(c)
    return out


def write_status(status_path, source, label, result, detail=""):
    st = {}
    if os.path.exists(status_path):
        try:
            with open(status_path, encoding="utf-8") as fh:
                st = json.load(fh)
        except Exception:
            st = {}
    st[source] = {"label": label, "result": result, "detail": detail[:400],
                  "date": _dt.datetime.now().isoformat(timespec="seconds")}
    os.makedirs(os.path.dirname(status_path) or ".", exist_ok=True)
    with open(status_path, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)


def execute_oag(items, args, manifest):
    """Run the OAG monthly loads through the existing loader, one file at a time so a
    failure names its file. Updates the manifest only on success."""
    ok = fail = 0
    for c in items:
        cmd = [sys.executable, os.path.join(HERE, "oag_ingest_periodic.py"),
               args.folder, args.oag_db, "--only", c["name"]]
        if c.get("_force"):
            cmd.append("--force")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            manifest[c["key"]] = {"name": c["name"], "fingerprint": c["fingerprint"],
                                  "ingested_at": _dt.datetime.now().isoformat(timespec="seconds")}
            save_manifest(manifest, args.manifest)
            ok += 1
        else:
            fail += 1
            print("FAILED %s\n%s" % (c["name"], (r.stdout or "")[-400:] + (r.stderr or "")[-400:]))
            write_status(args.status, "oag_monthly", c["label"], "FAIL", c["name"])
    if ok and not fail:
        write_status(args.status, "oag_monthly", items[-1]["label"], "PASS",
                     "%d file(s) ingested" % ok)
    return ok, fail


def main():
    ap = argparse.ArgumentParser(description="Plan (and optionally run) the data refresh.")
    ap.add_argument("--folder", default=DEFAULT_FOLDER)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--status", default=DEFAULT_STATUS)
    ap.add_argument("--oag-db", default=None, help="defaults to config.OAG_DUCKDB")
    ap.add_argument("--plan-only", action="store_true",
                    help="the explicit form of the default: print the plan, change "
                         "nothing. Accepted because this module's own docstring has "
                         "advertised it since 15 August; the flag not existing cost a "
                         "watched run on 16 August.")
    ap.add_argument("--execute", action="store_true",
                    help="run the OAG monthly loads in the plan. Default is plan-only: "
                         "print the plan and change nothing.")
    ap.add_argument("--allow-reingest", action="store_true",
                    help="also run the drop-and-reload items; off by default so a "
                         "changed historical file is a decision, not an accident")
    args = ap.parse_args()
    if args.plan_only and args.execute:
        ap.error("--plan-only and --execute contradict each other; pass one")
    if not args.oag_db:
        sys.path.insert(0, HERE)
        import config as CFG
        args.oag_db = str(CFG.OAG_DUCKDB)

    manifest = load_manifest(args.manifest)
    p = plan(args.folder, manifest)
    for action in ("ingest", "reingest", "confirm", "hold", "refuse", "skip"):
        items = p[action]
        if not items:
            continue
        print("%s (%d):" % (action.upper(), len(items)))
        for c in items[:200]:
            print("  %-45s %s" % (c["name"], c.get("reason", c.get("label", ""))))
    if not args.execute:
        print("\nPlan only; nothing was changed. --execute runs the INGEST list.")
        return 0
    todo = list(p["ingest"])
    if args.allow_reingest:
        for c in p["reingest"]:
            c["_force"] = True
            todo.append(c)
    ok, fail = execute_oag(todo, args, manifest)
    print("\n%d ingested, %d failed." % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
