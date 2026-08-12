#!/usr/bin/env python3
r"""Avia Solutions - which OAG month labels are complete worlds, and which are not.

    py -3.12 oag_label_check.py                 every label, flagging the incomplete ones
    py -3.12 oag_label_check.py --like 2018-%   one year
    py -3.12 oag_label_check.py --pairs 2018-08 the cohorts whose pre-launch month is a named label

WHY. The three OAG label forms are not interchangeable, per the OAG-WEEK entry of 11 August 2026: a
single-week label carries all seven regions, a monthly label carried six and no Asia, and a
part-month p01 or p16 label carried Asia alone. migrate_oag_asia_labels.py folded 53 of those on
11 August and stamped _store_meta.

WHAT SENT ME HERE. bt2_input_check compared the live assembly against capture_2018.csv on 250
routes of cohort 2018. Failures split by pre-launch month: 2018-08 failed 5 of 9, 2018-10 failed 1
of 29, and ten further months failed 0 of 212. Every 2018-08 failure reads live-HIGH and two run
from a training value of exactly zero in both directions. capture_2018.csv was written on 9 August
and the fold ran on 11 August, so the training file holds connecting competition measured against a
world that was missing a region.

The point of this script is to turn that from an inference about two dates into a list. A label
carrying fewer than seven regions today was never folded, or was folded from a partial source; a
label carrying seven today that the capture was written against before 11 August is one whose
training rows need rebuilding.

IT READS AND REPORTS. It changes nothing.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import os

import duckdb

FULL_REGIONS = 7


def _oag():
    p = os.environ.get("AVIA_OAG") or os.environ.get("AVIA_OAG_DUCKDB")
    if p and os.path.isfile(p):
        return p
    for r in (os.environ.get("AVIA_LOCAL_CACHE"),
              os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")):
        if r and os.path.isfile(os.path.join(r, "oag.duckdb")):
            return os.path.join(r, "oag.duckdb")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--like", default="%", help="a label pattern, for example 2018-%%")
    ap.add_argument("--pairs", help="name a label and list the BT2 pairs whose pre_month is it")
    ap.add_argument("--bt2-dir", default=os.environ.get("AVIA_BT2_DIR"))
    a = ap.parse_args()

    db = _oag()
    if not db:
        raise SystemExit("NOT RUN. No OAG store found. Set AVIA_OAG.")
    con = duckdb.connect(db, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=3")
    print("OAG store %s\n" % db)

    try:
        meta = con.execute("SELECT * FROM _store_meta").fetchall()
        cols = [d[0] for d in con.description]
        print("_store_meta:")
        for row in meta:
            print("   " + ", ".join("%s=%s" % (c, v) for c, v in zip(cols, row)))
    except Exception as exc:                                # noqa: BLE001
        print("_store_meta: not readable (%s)" % exc)

    rows = con.execute("""
      SELECT week, count(DISTINCT region) AS regions, count(*) AS n
      FROM oag WHERE week LIKE ? GROUP BY 1 ORDER BY 1""", [a.like]).fetchall()
    print("\n%d label(s) matching %r. A monthly label is YYYY-MM; anything longer is a single week."
          % (len(rows), a.like))
    part, thin = [], []
    for w, reg, n in rows:
        flag = ""
        if str(w).endswith(("p01", "p16")):
            flag = "  <-- PART LABEL, the fold did not reach it"
            part.append(w)
        elif reg < FULL_REGIONS:
            flag = "  <-- %d regions, NOT a complete world" % reg
            thin.append(w)
        print("   %-14s regions %d  rows %12s%s" % (w, reg, "{:,}".format(n), flag))

    if part or thin:
        print("\n%d part label(s) and %d incomplete label(s). Any BT2 capture written against one "
              "of these measured connecting competition against a world missing a region."
              % (len(part), len(thin)))
    else:
        print("\nEvery label matching %r carries %d regions. So an incomplete world is not the "
              "state of the store TODAY, and a training file that disagrees with the live path was "
              "written against an EARLIER state of it. Compare the capture file's modification date "
              "with the fold, 11 August 2026." % (a.like, FULL_REGIONS))

    # WHICH TRAINING ROWS ARE AFFECTED. The capture file records the pre-launch month it used, so
    # the pairs needing a rebuild can be listed rather than estimated.
    if a.pairs:
        bt2 = a.bt2_dir
        if not bt2 or not os.path.isdir(bt2):
            print("\n--pairs needs the BT2 data folder; set AVIA_BT2_DIR or pass --bt2-dir.")
            return
        import csv
        print("\npairs whose pre-launch month is %s:" % a.pairs)
        total = 0
        for f in sorted(os.listdir(bt2)):
            if not (f.startswith("capture_") and f.endswith(".csv")):
                continue
            with open(os.path.join(bt2, f), encoding="utf-8") as fh:
                hit = [r for r in csv.DictReader(fh) if r.get("pre_month") == a.pairs]
            if hit:
                total += len(hit)
                print("   %-22s %4d of this cohort" % (f, len(hit)))
        print("   %d row(s) in total would be rebuilt." % total)


if __name__ == "__main__":
    main()
