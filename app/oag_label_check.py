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
    ap.add_argument("--month", metavar="YYYY-MM",
                    help="THE FALLBACK TEST. For one month, count distinct flights at the "
                         "--coverage airports in load_legs' own 15th-to-21st window, from the "
                         "monthly label alone, from the half-year label covering that month, and "
                         "from the two together. That is what the leg query sees with the "
                         "fallback off and on")
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
    part = []
    for w, reg, n in rows:
        flag = ""
        if str(w).endswith(("p01", "p16")):
            flag = "  <-- PART LABEL, the fold did not reach it"
            part.append(w)
        print("   %-14s regions %d  rows %12s%s" % (w, reg, "{:,}".format(n), flag))

    # A REGION COUNT IS NOT A COVERAGE TEST. It happens to point the right way here, and it pointed
    # the right way for the wrong reason, so the test that settles it is --coverage and this count
    # is only ever the thing that sends you to run it.
    #
    # WHAT WAS MEASURED, 12 August 2026. 2015 to 2017 monthly labels carry five region names, Asia,
    # Europe, Latin America, North America and Southwest Pacific; 2018 onward carry seven, adding
    # Africa and Middle East. Two readings were proposed and both were wrong. Mine, that two regions
    # of the world are absent. John's, that all regions are present under a five-label taxonomy in
    # which Europe is EMEA. Distinct departing flights in August settle it:
    #
    #        2015    2016    2017    2018    2019
    #   JNB    21      26      24     401     402
    #   CAI    48      49      50     382     337
    #   DXB   356     375     381     639     626
    #   DOH   175     197     220     348     366
    #   TPE   372     423     406     421     451
    #
    # Asia is complete throughout, so the Asian ingest is sound. Africa and the Middle East are not
    # absent either: what survives in 2015-2017 is the flying that had somewhere to live in one of
    # the five loaded partitions. Dubai keeps 60% of its later count because its long-haul into
    # Europe and Asia sits in those files; Johannesburg keeps 6% because nearly all its flying is
    # intra-African. EMEA-as-Europe would have kept Johannesburg whole and did not.
    #
    # SO THE GAP IS SHAPED: intra-Africa and intra-Middle-East schedules are largely missing from
    # 2015, 2016 and 2017, and the long-haul out of both regions is mostly present. Cohorts 2016 and
    # 2017 take every pre-launch month from that range.
    if part:
        print("\n%d part label(s). Those were the Asia split-month labels; "
              "migrate_oag_asia_labels.py folded 53 of them on 11 August 2026." % len(part))
    thin = [w for w, reg, _n in rows if reg < FULL_REGIONS and not str(w).endswith(("p01", "p16"))]
    if thin:
        # NAMED, AND MARKED AS RECORDED RATHER THAN MEASURED HERE. This sentence carried the
        # Johannesburg finding unconditionally, so it would have printed the 2015-2017 result over a
        # thin 2023 label the user was actually asking about. The finding is real and belongs in the
        # tool; reading it across to labels it was not measured on is what had to stop.
        _shown = ", ".join(str(w) for w in thin[:8]) + (" and %d more" % (len(thin) - 8) if len(thin) > 8 else "")
        print("\n%d label(s) carry fewer than %d region names: %s. That is a REASON TO RUN "
              "--coverage and not a finding on its own, because a region count counts download "
              "partitions rather than flights." % (len(thin), FULL_REGIONS, _shown))
        print("RECORDED on the 2015 to 2017 labels and NOT re-measured here: Asia is complete, "
              "intra-Africa and intra-Middle-East flying is largely absent, and Johannesburg runs "
              "24 distinct departures in 2017-08 against 402 in 2019-08. Run --coverage on the "
              "labels above rather than reading that result across to them.")

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
        flts = {}
        for w in sorted({r[0] for r in rows}):
            cells = []
            for x in aps:
                n, d = con.execute("""
                  SELECT count(*), count(DISTINCT carrier || flight_no || arr_airport)
                  FROM oag WHERE week = ? AND service_type='J' AND dep_airport = ?""",
                                   [w, x]).fetchone()
                flts.setdefault(x, {})[w] = int(d or 0)
                cells.append("%8s rows %6s flts" % ("{:,}".format(n or 0), "{:,}".format(d or 0)))
            print("   %-14s %s" % (w, "  ".join(cells)))

        # THE VERDICT IS COMPUTED, NOT PRINTED REGARDLESS. This block previously closed with an
        # unconditional sentence saying a normal month means the world is there and the reading of a
        # coverage gap is wrong. It was written for TPE, PVG and HKG, which do come back normal, and
        # it then printed itself unchanged over DXB, DOH, JNB and CAI, where Johannesburg reads 24
        # distinct departures in 2017-08 against 402 in 2019-08. A label that asserts what the code
        # did not check is the shape this codebase has been caught by five times, and here it told
        # the reader to withdraw a finding its own table supports.
        #
        # THE RULE, stated so it can be argued with: each label is scored against that airport's OWN
        # BEST label, so the comparison is within one airport and needs no external traffic figure.
        # Anything below 75% of its own best is called SHORT. Schedules at these airports did not
        # grow by a quarter in a year, so a quarter missing is not growth.
        print("\nRead the DISTINCT flight column, not the rows. Rows carry the region duplication;"
              " distinct flights do not.")
        print("Each label as a share of that airport's own best label. Below 75% is called SHORT,"
              " because these airports did not grow by a quarter in a year.")
        short = {}
        for x in aps:
            best = max(flts.get(x, {}).values() or [0])
            if not best:
                continue
            marks = []
            for w in sorted(flts[x]):
                sh = flts[x][w] / best
                if sh < 0.75:
                    short.setdefault(x, []).append(w)
                marks.append("%s %3.0f%%%s" % (w, 100 * sh, " SHORT" if sh < 0.75 else ""))
            print("   %-5s best %s flts | %s" % (x, "{:,}".format(best), "  ".join(marks)))
        if short:
            print("\nSHORT LABELS FOUND. A five-against-seven region count is a partition count and"
                  " says nothing on its own, but these airports are missing flights, not files:")
            for x in sorted(short):
                print("   %-5s %s" % (x, ", ".join(short[x])))
            print("Any BT2 capture written against one of these measured connecting competition"
                  " against a world missing those flights.")
        else:
            print("\nNo label falls short of its airport's own best, so on these airports the"
                  " five-against-seven is the partitioning and not a coverage gap.")

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

    if a.month:
        _month_union(a, con)

    if a.pairs:
        bt2 = a.bt2_dir
        if not bt2 or not os.path.isdir(bt2):
            print("\n--pairs needs the BT2 data folder; set AVIA_BT2_DIR or pass --bt2-dir.")
            return
        _pairs_report(a, bt2)


def _month_union(a, con):
    """Does reading the half-year label alongside the monthly one recover the missing flying?

    THE POINT. For 2015 to 2017 the store holds five regions on the monthly labels and Africa plus
    the Middle East on SEPARATE HALF-YEAR labels, 2015-H1 through 2017-H2. bt2_capture_core.load_legs
    queries ONE label and builds its window as {mon}-15 to {mon}-21, so on a monthly label it never
    sees the other two regions, and on a half-year label it would build "2017-H1-15", which is not a
    date and returns nothing. The flying is in the store and unreachable from either side.

    This reproduces load_legs' own predicate exactly, on eff_from and eff_to, and reports the same
    airports three ways: the monthly label alone, which is what the training chain read; the
    half-year label alone; and the two together, which is what a fallback would read. The third
    column is the prize and the second says where it comes from.
    """
    y, m = int(a.month[:4]), int(a.month[5:7])
    half = "%d-H%d" % (y, 1 if m <= 6 else 2)
    lo, hi = "%s-15" % a.month, "%s-21" % a.month
    aps = [x.strip().upper() for x in (a.coverage or "").replace(";", ",").split(",") if x.strip()]
    if not aps:
        print("\n--month needs --coverage to name the airports to count.")
        return
    q = ("SELECT count(DISTINCT carrier || flight_no || arr_airport) FROM oag "
         "WHERE week IN %s AND service_type='J' AND dep_airport = ? "
         "AND try_cast(strftime(try_cast(eff_from AS date), '%%d') AS int) IS NOT NULL "
         "AND try_cast(eff_from AS date) <= ?::date AND try_cast(eff_to AS date) >= ?::date")
    print("\nDISTINCT DEPARTING FLIGHTS in the %s to %s window, load_legs' own predicate." % (lo, hi))
    print("monthly label %s, half-year label %s\n" % (a.month, half))
    print("   %-6s %10s %10s %10s   %s" % ("apt", "monthly", "half-year", "together", "what it means"))
    for x in aps:
        n_m = con.execute(q % ("('%s')" % a.month), [x, hi, lo]).fetchone()[0] or 0
        n_h = con.execute(q % ("('%s')" % half), [x, hi, lo]).fetchone()[0] or 0
        n_u = con.execute(q % ("('%s','%s')" % (a.month, half)), [x, hi, lo]).fetchone()[0] or 0
        # An airport served only from the five monthly regions gains nothing and should not: that is
        # the control. One in Africa or the Gulf should gain most of its flying.
        note = ("no change, this airport is in the monthly regions" if n_h == 0 else
                "RECOVERED %s flights, x%.1f" % ("{:,}".format(n_u - n_m), (n_u / n_m) if n_m else 0)
                if n_u > n_m else "half-year label adds nothing")
        print("   %-6s %10s %10s %10s   %s"
              % (x, "{:,}".format(n_m), "{:,}".format(n_h), "{:,}".format(n_u), note))
    print("\nIf 'together' restores an African or Gulf airport to a normal month while leaving the")
    print("monthly-region airports untouched, the fallback is the fix and no data need be bought.")
    print("If the two labels OVERLAP on an airport, together will read below monthly plus half-year")
    print("and that is correct: a flight counted once is the point of counting distinct flights.")


def _pairs_report(a, bt2):
    """The BT2 rows whose pre-launch month is the named label, so a rebuild can be sized."""
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
