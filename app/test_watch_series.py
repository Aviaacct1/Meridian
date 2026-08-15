#!/usr/bin/env python3
"""Offline test of the Watch page's chart series: the daily-seats dedupe and the two
monthly readers. Builds real DuckDB fixtures carrying the stores' own traps, so the
queries are exercised rather than mocked.

    py -3.12 test_watch_series.py

The fixtures reproduce, deliberately:
  * the REGION-DUPLICATE trap: the store repeats one schedule record per region
    label, so a straight sum multiplies every flight by the regions that see it
    (frequency_frame's documented trap; United SFO-TPE read 420 weekly)
  * a days_of_op mask with dots for non-operating days
  * a record with NO operating-day mask, which must be counted out, never spread
  * an arrival-only record, which a DEPARTING series must not count
  * a freighter row (service_type F), outside scheduled passenger service
  * the T-100 store's twin-table trap: `seg` parsed beside `t100` unparsed
  * T-100 charter (class L) beside scheduled (class F)
  * an ACI month the airport did not file, which is a gap and never a zero

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import airport_profile as AP
import route_watch as RW

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def build_oag(path):
    import duckdb
    con = duckdb.connect(path)
    con.execute("""CREATE TABLE oag(
        week VARCHAR, carrier VARCHAR, flight_no VARCHAR,
        dep_airport VARCHAR, arr_airport VARCHAR, local_dep_time VARCHAR,
        days_of_op VARCHAR, seats_total DOUBLE, frequency DOUBLE,
        service_type VARCHAR)""")
    rows = []

    def add(week, car, fno, dep, arr, t, mask, seats, svc="J", n=1):
        for _ in range(n):
            rows.append((week, car, fno, dep, arr, t, mask, seats, 7.0, svc))

    CUR, PRI = "2026-05-25", "2025-05-26"   # 364 days apart, a clean year-on-year
    # THE REGION DUPLICATE: one daily record three times. Counts once.
    add(CUR, "XX", "100", "TST", "AAA", "08:00", "1234567", 180, n=3)
    # dotted mask: Mon, Wed, Fri only
    add(CUR, "XX", "102", "TST", "BBB", "09:00", "1.3.5..", 150)
    # weekend-only second carrier
    add(CUR, "YY", "200", "TST", "AAA", "10:00", "67", 100)
    # no mask at all: must be left out and counted, never spread across the week
    add(CUR, "ZZ", "300", "TST", "CCC", "11:00", "", 999)
    # arrival only: a departing series must not count it
    add(CUR, "QQ", "400", "AAA", "TST", "12:00", "1234567", 500)
    # freighter: outside scheduled passenger service
    add(CUR, "FF", "500", "TST", "AAA", "13:00", "1234567", 400, svc="F")
    # prior snapshot: one daily flight at a smaller gauge
    add(PRI, "XX", "100", "TST", "AAA", "08:00", "1234567", 160)
    con.executemany("INSERT INTO oag VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.close()
    return CUR, PRI


def test_daily_seats(tmp):
    db = os.path.join(tmp, "oag.duckdb")
    cur, pri = build_oag(db)
    out = RW.daily_seats(db, "tst")
    check("daily_seats answers", bool(out.get("ok")), out.get("error", ""))
    if not out.get("ok"):
        return
    check("current week picked by date", out.get("week") == cur, out.get("week"))
    check("prior week is the year-earlier label", out.get("prior_week") == pri,
          out.get("prior_week"))
    curd = out.get("current") or []
    # Mon 180+150, Tue 180, Wed 330, Thu 180, Fri 330, Sat 180+100, Sun 280.
    want = [330, 180, 330, 180, 330, 280, 280]
    check("region duplicate counted once, masks placed",
          curd == want, "%s v %s" % (curd, want))
    check("prior series present", (out.get("prior") or []) == [160] * 7,
          out.get("prior"))
    notes = " ".join(out.get("notes") or [])
    check("maskless record counted out, not spread", "no operating-day mask" in notes,
          notes[:80])
    check("basis states departing and the dedupe",
          "departing" in out.get("basis", "").lower()
          and "dedup" in out.get("basis", "").lower(), out.get("basis", "")[:80])
    check("human date on the display label",
          out.get("week_display") == "25 May 2026", out.get("week_display"))


def test_daily_seats_no_prior(tmp):
    import duckdb
    db = os.path.join(tmp, "oag_single.duckdb")
    con = duckdb.connect(db)
    con.execute("""CREATE TABLE oag(week VARCHAR, carrier VARCHAR, flight_no VARCHAR,
        dep_airport VARCHAR, arr_airport VARCHAR, local_dep_time VARCHAR,
        days_of_op VARCHAR, seats_total DOUBLE, frequency DOUBLE, service_type VARCHAR)""")
    con.execute("INSERT INTO oag VALUES ('2026-05-25','XX','100','SOL','AAA','08:00',"
                "'1234567',100,7.0,'J')")
    con.close()
    out = RW.daily_seats(db, "SOL")
    check("single snapshot still charts", bool(out.get("ok")), out.get("error", ""))
    check("absent comparator is absent, not zero", "prior" not in out,
          str(out.get("prior"))[:40])
    notes = " ".join(out.get("notes") or [])
    check("absence of comparator is named", "absent, not zero" in notes, notes[:80])


def test_t100_monthly(tmp):
    import duckdb
    db = os.path.join(tmp, "t100.duckdb")
    con = duckdb.connect(db)
    # the twin-table trap: the unparsed copy sits beside the parsed one
    con.execute("CREATE TABLE t100(column00 VARCHAR)")
    con.execute("""CREATE TABLE seg(origin VARCHAR, class VARCHAR,
        year INTEGER, month INTEGER, passengers DOUBLE)""")
    rows = []
    for m in range(1, 13):
        rows.append(("TUS", "F", 2024, m, 1000.0 * m))
        rows.append(("TUS", "L", 2024, m, 5000.0))      # charter, excluded
    for m in range(1, 7):                                # 2025 published to June
        rows.append(("TUS", "F", 2025, m, 1100.0 * m))
    con.executemany("INSERT INTO seg VALUES (?,?,?,?,?)", rows)
    con.close()
    series, note = AP.read_t100_monthly(db, "tus")
    check("t100 monthly answers", bool(series), note)
    got = {(y, m): p for y, m, p in series}
    check("t100 charter class excluded", got.get((2024, 3)) == 3000.0,
          got.get((2024, 3)))
    check("t100 arrears months absent, not zero", (2025, 7) not in got, "")
    check("t100 note names scheduled class", "class F" in note, note[:60])
    # a store whose seg table is missing must refuse, not probe the unparsed copy
    db2 = os.path.join(tmp, "t100_bad.duckdb")
    con = duckdb.connect(db2)
    con.execute("CREATE TABLE t100(column00 VARCHAR)")
    con.close()
    series2, note2 = AP.read_t100_monthly(db2, "TUS")
    check("t100 refuses without the seg table",
          series2 == [] and "no 'seg' table" in note2, note2[:60])


def test_aci_monthly(tmp):
    import duckdb
    db = os.path.join(tmp, "aci.duckdb")
    con = duckdb.connect(db)
    con.execute("""CREATE TABLE aci_monthly(iata VARCHAR, airport VARCHAR,
        country VARCHAR, ym VARCHAR, year INTEGER, month INTEGER, passengers DOUBLE)""")
    rows = []
    for m in range(1, 13):
        if m == 4:
            continue                                     # April never filed: a gap
        rows.append(("EDI", "Edinburgh", "United Kingdom",
                     "2025-%02d" % m, 2025, m, 900000.0 + m))
    con.executemany("INSERT INTO aci_monthly VALUES (?,?,?,?,?,?,?)", rows)
    con.close()
    series, note = AP.read_aci_monthly(db, "edi")
    got = {(y, m): p for y, m, p in series}
    check("aci monthly answers", bool(series), note)
    check("aci unfiled month is a gap, not a zero", (2025, 4) not in got, "")
    check("aci note says a gap is not a zero", "not a zero" in note, note[:60])
    series3, note3 = AP.read_aci_monthly(db, "ZZZ")
    check("aci unknown airport refuses by name", series3 == [] and "ZZZ" in note3,
          note3[:60])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_daily_seats(tmp)
        test_daily_seats_no_prior(tmp)
        test_t100_monthly(tmp)
        test_aci_monthly(tmp)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
