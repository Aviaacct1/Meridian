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
    ap.add_argument("--audit", action="store_true",
                    help="every capture row against the completeness of the label it was built on")
    ap.add_argument("--regions", action="store_true",
                    help="which regions each label actually carries, for two named years")
    ap.add_argument("--coverage", metavar="IATA,IATA",
                    help="departures and distinct flights at named airports, per label. THE TEST "
                         "THAT DECIDES IT: a region count counts download partitions, not the "
                         "world, so ask whether the airports are actually there")
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

    # WHICH REGIONS ARE ACTUALLY MISSING. A count of five says two are absent and does not say
    # which, and the answer decides whether the gap can be closed from the extract or not.
    if a.regions:
        print("\nregions carried, by label:")
        for w in sorted({r[0] for r in rows}):
            got = [x[0] for x in con.execute(
                "SELECT DISTINCT region FROM oag WHERE week = ? ORDER BY 1", [w]).fetchall()]
            print("   %-14s %s" % (w, ", ".join(str(g) for g in got)))

    # IS THE WORLD ACTUALLY MISSING, OR ONLY THE PARTITION. The store holds each record once per
    # region label, which the region duplication has now been found to cause four separate times
    # (bt2_base, FREQ-BUG, the T-100 double load, and the Taipei board on 11 August). So a label
    # carrying five regions where another carries seven may hold exactly the same flights, split
    # into fewer files. The row counts already hint at it: 2017-08 has 3,310,899 rows on five
    # regions and 2018-08 has 3,762,893 on seven, 13.7% more in a year in which schedules did not
    # grow 13.7%.
    #
    # A region count cannot settle that and DISTINCT FLIGHTS AT NAMED AIRPORTS can. If Taipei,
    # Shanghai and Hong Kong carry a normal month of departures in 2017, nothing is missing and the
    # difference is the partitioning.
    if a.coverage:
        aps = [x.strip().upper() for x in a.coverage.replace(";", ",").split(",") if x.strip()]
        print("\ndepartures and DISTINCT flights at %s, by label:" % ", ".join(aps))
        print("   %-14s %s" % ("label", "  ".join("%-22s" % x for x in aps)))
        for w in sorted({r[0] for r in rows}):
            cells = []
            for x in aps:
                n, d = con.execute("""
                  SELECT count(*), count(DISTINCT carrier || flight_no || arr_airport)
                  FROM oag WHERE week = ? AND service_type='J' AND dep_airport = ?""",
                                   [w, x]).fetchone()
                cells.append("%8s rows %6s flts" % ("{:,}".format(n or 0), "{:,}".format(d or 0)))
            print("   %-14s %s" % (w, "  ".join(cells)))
        print("\nRead the DISTINCT flight column, not the rows. Rows carry the region duplication; "
              "distinct flights do not. A normal month at these airports in 2017 means the world is "
              "there and the five-against-seven is the partitioning, and my reading of a coverage "
              "gap is wrong.")

    # THE SIZE OF THE PROBLEM, and it is the number that matters. bt2_input_check compares the two
    # chains and can only ever see a DISAGREEMENT, which happens where the store has changed since
    # the capture was written. Where a label was incomplete then and is incomplete now, both chains
    # read the same missing world and agree perfectly on a wrong number. That is invisible to the
    # comparison and it is the larger fault, so it is counted here instead.
    if a.audit:
        bt2 = a.bt2_dir
        if not bt2 or not os.path.isdir(bt2):
            print("\n--audit needs the BT2 data folder; set AVIA_BT2_DIR or pass --bt2-dir.")
            return
        import csv
        regmap = {str(w): int(reg) for w, reg, _n in rows}
        print("\ncapture rows against the completeness of the label they were built on:")
        gt, gi = 0, 0
        for f in sorted(os.listdir(bt2)):
            if not (f.startswith("capture_") and f.endswith(".csv")):
                continue
            n, inc, labels = 0, 0, {}
            with open(os.path.join(bt2, f), encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    pm = (r.get("pre_month") or "").strip()
                    if not pm:
                        continue
                    n += 1
                    if regmap.get(pm, FULL_REGIONS) < FULL_REGIONS:
                        inc += 1
                        labels[pm] = labels.get(pm, 0) + 1
            gt += n
            gi += inc
            print("   %-22s %5d rows  %5d on an incomplete label  %5.1f%%%s"
                  % (f, n, inc, (100.0 * inc / n) if n else 0.0,
                     "   " + ", ".join("%s(%d)" % (k, v) for k, v in sorted(labels.items()))
                     if labels else ""))
        print("   %-22s %5d rows  %5d on an incomplete label  %5.1f%%"
              % ("ALL COHORTS", gt, gi, (100.0 * gi / gt) if gt else 0.0))
        print("\nThose rows carry a capa, a qcx and a legs_n measured against a world missing at "
              "least one region, and the model is fitted on them. That is not a disagreement "
              "between the two chains and bt2_input_check cannot see it.")

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
