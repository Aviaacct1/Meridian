#!/usr/bin/env python3
"""Offline test of check_airport.py against stores built for the purpose.

    py -3.12 test_check_airport.py

The reason this exists: the first version of check_airport.py reported that
Austin's passengers could come from ACI. ACI does hold Austin, so the statement
was true about the store and wrong about the tool, which is graded on US DOT for
any US airport. A reporting script that quietly reports around a house rule is
worse than no script, because it will be believed.

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


tmp = tempfile.mkdtemp(prefix="avia_chk_")
oag_db = os.path.join(tmp, "oag.duckdb")
aci_db = os.path.join(tmp, "aci.duckdb")

import duckdb
import airport_profile as AP

# OAG: monthly labels, service_type J. EDI and AUS complete 2017-2019 and
# 2023-2025, with the pandemic absent as the real store has it.
con = duckdb.connect(oag_db)
con.execute("""CREATE TABLE oag(
    week VARCHAR, dep_airport VARCHAR, arr_airport VARCHAR,
    dep_country VARCHAR, arr_country VARCHAR, carrier VARCHAR,
    seats_total DOUBLE, frequency DOUBLE, service_type VARCHAR)""")
rows = []
for apt in ("EDI", "AUS"):
    for year in (2017, 2018, 2019, 2023, 2024, 2025):
        for m in range(1, 13):
            rows.append(("%d-%02d" % (year, m), apt, "LHR", "GB", "GB", "BA",
                         100000.0, 300.0, "J"))
# a part year, which must never be reported as complete
for m in range(1, 8):
    rows.append(("2016-%02d" % m, "EDI", "LHR", "GB", "GB", "BA",
                 100000.0, 300.0, "J"))
con.executemany("INSERT INTO oag VALUES (?,?,?,?,?,?,?,?,?)", rows)
con.close()

# ACI: both airports complete 2017-2025, pandemic included, as the real store is
con = duckdb.connect(aci_db)
con.execute("""CREATE TABLE aci_monthly(
    iata VARCHAR, airport VARCHAR, country VARCHAR, ym VARCHAR,
    year INTEGER, month INTEGER, passengers DOUBLE)""")
arows = []
for apt, name, ctry in (("EDI", "EDINBURGH, GB", "United Kingdom"),
                        ("AUS", "AUSTIN TX, US", "USA")):
    for year in range(2017, 2026):
        for m in range(1, 13):
            arows.append((apt, name, ctry, "%d-%02d" % (year, m), year, m,
                          1000000.0))
con.executemany("INSERT INTO aci_monthly VALUES (?,?,?,?,?,?,?)", arows)
con.execute("""CREATE VIEW aci_coverage AS
    SELECT iata, year, COUNT(*) AS months_reported, SUM(passengers) AS passengers
    FROM aci_monthly GROUP BY iata, year""")
con.close()


# T-100, with the real store's two traps in the fixture:
#   1. the same rows exist twice, parsed as `seg` and unparsed as `t100`
#   2. scheduled and charter share the table under `class`
t100_db = os.path.join(tmp, "t100.duckdb")
con = duckdb.connect(t100_db)
con.execute("""CREATE TABLE seg(year INTEGER, month INTEGER, origin VARCHAR,
    dest VARCHAR, carrier VARCHAR, class VARCHAR, distance DOUBLE,
    aircraft_type VARCHAR, dep_performed DOUBLE, seats DOUBLE,
    passengers DOUBLE)""")
trows = []
for year in (2017, 2018, 2019, 2022, 2023, 2024):
    for m in range(1, 13):
        trows.append((year, m, "AUS", "DFW", "AA", "F", 190.0, "738",
                      300.0, 45000.0, 38000.0))
        trows.append((year, m, "AUS", "CUN", "XX", "L", 1000.0, "320",
                      4.0, 600.0, 500.0))          # charter, must be excluded
        trows.append((year, m, "AUS", "MEM", "FX", "G", 600.0, "757",
                      20.0, 0.0, 0.0))             # freight, no passengers
# 2025 is a part year, as DOT publication in arrears produces
for m in range(1, 5):
    trows.append((2025, m, "AUS", "DFW", "AA", "F", 190.0, "738",
                  300.0, 45000.0, 38000.0))
con.executemany("INSERT INTO seg VALUES (?,?,?,?,?,?,?,?,?,?,?)", trows)
# the raw copy of the very same rows, which a probing reader could take
con.execute("""CREATE TABLE t100(column00 VARCHAR, column01 VARCHAR,
    column02 VARCHAR)""")
con.executemany("INSERT INTO t100 VALUES (?,?,?)",
                [("2024", "AUS", "38000")] * len(trows))
con.close()

NO_STORE = os.path.join(tmp, "there-is-no-t100-here.duckdb")


def run(code, t100=NO_STORE):
    """Always pass --t100 explicitly.

    Without it, check_airport falls back to config, which resolves through
    AVIA_T100_DUCKDB to whatever store this machine happens to have. That made
    four checks pass or fail depending on an environment variable, which is not
    a test of anything.
    """
    r = subprocess.run([sys.executable, os.path.join(HERE, "check_airport.py"),
                        code, "--oag", oag_db, "--aci", aci_db, "--t100", t100],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


edi = run("EDI")
aus = run("AUS")                     # US airport, DOT store absent
aus_dot = run("AUS", t100=t100_db)   # US airport, DOT store present

# --- the UK airport reads from ACI ---------------------------------------------
check("a UK airport gets its passengers from ACI",
      "passengers by year   2017-2025 from ACI" in edi,
      [l for l in edi.splitlines() if "passengers by year" in l])
check("and its country is read from the store, not supplied",
      "United Kingdom" in edi)
check("the pandemic gap in OAG is named, not skipped over",
      "gaps at 2020, 2021, 2022" in edi,
      [l for l in edi.splitlines() if "seats by market" in l])
check("a part year is never counted as complete",
      "2016" in edi and "PART YEAR" in edi,
      [l for l in edi.splitlines() if l.strip().startswith("2016")])

# --- THE ONE THAT MATTERS: the US airport must NOT be served from ACI ----------
check("a US airport is NOT offered ACI passengers",
      "from ACI" not in aus.split("country")[-1],
      [l for l in aus.splitlines() if "passengers by year" in l])
check("and is named as graded on DOT",
      "DOT T-100" in aus, [l for l in aus.splitlines() if "country" in l])
check("and the refusal says the store is absent, rather than failing silently",
      "NOT DRAWABLE" in aus and "not substituted" in aus,
      [l for l in aus.splitlines() if "NOT DRAWABLE" in l])
check("its ACI years are marked unusable in the table, not left to be read as fine",
      "not usable" in aus)
check("and no year is called seats + pax for it",
      "seats + pax" not in aus,
      [l for l in aus.splitlines() if "seats + pax" in l])
check("so the load factor chart is refused for the US airport",
      "effective load" in aus and "NOT DRAWABLE" in aus.split("effective load")[-1],
      aus.split("effective load")[-1][:80])
check("and refused for the RIGHT reason, not for want of coverage",
      "not for want of coverage" in aus.split("effective load")[-1],
      aus.split("effective load")[-1][:100])
check("while the UK airport gets one",
      "NOT DRAWABLE" not in edi.split("effective load")[-1],
      edi.split("effective load")[-1][:80])

# --- the airline chart needs only OAG, so it works for both --------------------
check("airlines by capacity works for both, since it needs only OAG",
      "latest complete OAG year, 2025" in edi
      and "latest complete OAG year, 2025" in aus)

# --- with the DOT store present, the US airport IS drawable -------------------
check("with T-100 present the US airport gets its passengers",
      "from US DOT T-100" in aus_dot,
      [l for l in aus_dot.splitlines() if "passengers by year" in l])
check("and the excluded charter share is stated in the report",
      "scheduled service only" in aus_dot,
      [l for l in aus_dot.splitlines() if "scheduled" in l])
check("and it still is NOT offered ACI",
      "from ACI" not in aus_dot.split("country")[-1])
check("the load factor becomes drawable",
      "NOT DRAWABLE" not in aus_dot.split("effective load")[-1],
      aus_dot.split("effective load")[-1][:70])
check("a year DOT does not publish yet is marked ACI-only, never substituted",
      "not usable, ACI only" in aus_dot,
      [l for l in aus_dot.splitlines() if "not usable" in l])

# --- the T-100 reader itself ---------------------------------------------------
got, note = AP.read_t100(t100_db, "AUS")
check("T-100 gives one figure a year for the complete years",
      [y for y, _p in got] == [2017, 2018, 2019, 2022, 2023, 2024], got)
check("charter is excluded, so the year is scheduled only",
      got and got[0][1] == 12 * 38000.0, got[0] if got else None)
check("and the share left out is reported, not silently dropped",
      "scheduled service only" in note and "%" in note, note[:70])
check("a part year is left out and named",
      "2025 has 4 months" in note, note)
check("T-100 is read from seg, never from the raw twin table",
      AP.read_t100(t100_db, "AUS")[0] == got)

pb = AP.pax_by_year("AUS", "USA", stores={"t100": t100_db, "aci": aci_db})
check("pax_by_year serves a US airport from T-100",
      pb["kind"] == "onboard" and pb["series"] == got, (pb["kind"], pb["series"]))
check("and labels it DOT, not ACI",
      pb["label"] and "DOT" in pb["label"], pb["label"])

# onboard needs NO halving, unlike ACI throughput
lf, lnote = AP.effective_load_factor([(2024, 570000.0)], [(2024, 456000.0)],
                                     "onboard")
check("an onboard count is not halved before meeting seats",
      lf and abs(lf[0][1] - 0.80) < 1e-9, lf)
check("and nothing about halving is claimed", "halved" not in lnote, lnote[:40])

import shutil
shutil.rmtree(tmp, ignore_errors=True)
print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
