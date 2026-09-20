#!/usr/bin/env python3
r"""
Meridian - warm the on-disk boards for the airports in the Routes register (W1 step 2).
========================================================================================
Reads the airport codes in routes\PREWARM-AIRPORTS.txt, opens the live OAG store through the
same wave_cache.shared() the server uses, and touches the departure and arrival board of each
airport at the server's schedule week. Every board parsed is written to the on-disk copy under
LOCAL_CACHE\boards\<store>-<vintage>, so the server's first Run on that airport reads a pickle
rather than querying and de-duplicating the store. Run it in its own process, before or after
the server starts; the two share the folder, never the memory.

It changes nothing in the engine. It reports, per code: legs on each board, seconds, and
whether the board came from disk or was parsed now. A code with no departures and no arrivals
is printed as EMPTY and counted, never skipped in silence: it is either not in the store for
this week or a wrong code in the list.

    Workstation Actual (or Remote over ssh, with $env:QSI_PASSWORD not needed: no server call):

        cd C:\src\meridian
        py -3.12 app\warm_boards.py                       (list: routes\PREWARM-AIRPORTS.txt)
        py -3.12 app\warm_boards.py --codes SJC,TPE,BRS,EWR
        py -3.12 app\warm_boards.py --week 2026-05-25     (a specific label; default: the server's rule)

Output: printed, and written to WARM-<date>-<time>.md at the repository root for the record.
"""
import argparse
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _read_list(path):
    codes, bad = [], []
    with open(path, encoding="utf-8-sig") as fh:
        for ln in fh:
            t = ln.split("#", 1)[0].strip()
            if not t:
                continue
            code = t.split()[0].upper()
            if len(code) == 3 and code.isalpha():
                if code not in codes:
                    codes.append(code)
            else:
                bad.append(t)
    return codes, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", default=os.path.join(ROOT, "routes", "PREWARM-AIRPORTS.txt"))
    ap.add_argument("--codes", default="", help="comma-separated IATA codes instead of the list file")
    ap.add_argument("--week", default=os.environ.get("AVIA_OAG_WEEK", ""), help="OAG week label; default: the server's rule")
    ap.add_argument("--oag", default="", help="path to oag.duckdb; default: config / AVIA_OAG as the server resolves it")
    a = ap.parse_args()

    if os.environ.get("AVIA_BOARDS_DISK", "1").strip().lower() in ("0", "false", "off", "no"):
        print("AVIA_BOARDS_DISK=0: the on-disk copy is switched off, so this run would warm nothing that outlives it. Stopping.")
        return 2

    import wave_cache as WC
    from cortex_app import _db_paths, resolve_oag_week     # the server's own store and week rules
    import duckdb

    oag = a.oag or _db_paths()[1]
    if not os.path.exists(oag):
        print("OAG store not found: %s" % oag)
        return 2
    con = duckdb.connect(oag, read_only=True)
    week, nreg, why = resolve_oag_week(con, a.week or None)
    con.close()
    if not week:
        print("no usable OAG week: %s" % why)
        return 2

    if a.codes:
        codes = [c.strip().upper() for c in a.codes.split(",") if c.strip()]
        bad = [c for c in codes if not (len(c) == 3 and c.isalpha())]
        codes = [c for c in codes if c not in bad]
    else:
        codes, bad = _read_list(a.list)

    boards = WC.shared(oag)
    d = boards._disk
    print("store   %s" % oag)
    print("week    %s (%s regions; %s)" % (week, nreg, why))
    print("disk    %s" % (d or "OFF: boards stay in memory only (see the [boards] line above)"))
    print("codes   %d from %s%s" % (len(codes), "--codes" if a.codes else a.list,
                                    ("; %d malformed lines skipped" % len(bad)) if bad else ""))
    for b in bad:
        print("  malformed: %s" % b)

    rows, empty = [], []
    t_all = time.time()
    for i, code in enumerate(codes, 1):
        h0 = boards.disk_hits
        t0 = time.time()
        dep = boards.dep_rows(week, code)
        arr = boards.arr_rows(week, code)
        dt = time.time() - t0
        src = "disk" if boards.disk_hits - h0 == 2 else ("mixed" if boards.disk_hits - h0 == 1 else "parsed")
        rows.append((code, len(dep), len(arr), dt, src))
        if not dep and not arr:
            empty.append(code)
        print("  %3d/%d  %s  dep %5d  arr %5d  %6.2fs  %s%s" % (
            i, len(codes), code, len(dep), len(arr), dt, src, "  EMPTY" if not dep and not arr else ""))
    total = time.time() - t_all

    parsed = sum(1 for r in rows if r[4] == "parsed")
    lines = ["# Boards warm-up %s" % datetime.now().strftime("%d %B %Y %H:%M"),
             "",
             "Store %s; week %s (%s regions; %s); disk %s." % (oag, week, nreg, why, d or "OFF"),
             "%d codes; %d parsed now, %d read from disk, %d mixed; %.1fs in total; %d EMPTY." % (
                 len(rows), parsed, sum(1 for r in rows if r[4] == "disk"),
                 sum(1 for r in rows if r[4] == "mixed"), total, len(empty)),
             "",
             "| Code | Dep legs | Arr legs | Seconds | Source |", "|---|---|---|---|---|"]
    lines += ["| %s | %d | %d | %.2f | %s |" % r for r in rows]
    if empty:
        lines += ["", "EMPTY (no board either side at %s; not in the store for this week, or a wrong code): %s"
                  % (week, ", ".join(empty))]
    if bad:
        lines += ["", "Malformed list lines skipped: " + "; ".join(bad)]
    out = os.path.join(ROOT, "WARM-%s.md" % datetime.now().strftime("%Y%m%d-%H%M"))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print()
    print(lines[3])
    if empty:
        print("EMPTY: " + ", ".join(empty))
    print("written %s" % out)
    return 1 if empty else 0


if __name__ == "__main__":
    sys.exit(main())
