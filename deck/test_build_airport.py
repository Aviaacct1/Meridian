#!/usr/bin/env python3
"""End-to-end test of deck_figures.build_airport against real fixture stores.

    py -3.12 test_build_airport.py

WHY THIS EXISTS. Three separate suites were green while the live build reported

    NOT DRAWN airport_pax  TypeError: airport_pax() missing 1 required
                           keyword-only argument: 'label'

because every one of them tested a layer in isolation: the charts were called
directly, and the spec was handed a dict of paths. Nothing called the function
that calls the charts. This does, with DuckDB stores on disk, so the keyword
contract between deck_figures and avia_charts is exercised rather than assumed.

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck_figures as DF

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


tmp = tempfile.mkdtemp(prefix="avia_bldapt_")
oag_db = os.path.join(tmp, "oag.duckdb")
aci_db = os.path.join(tmp, "aci.duckdb")
t100_db = os.path.join(tmp, "t100.duckdb")
figdir = os.path.join(tmp, "figs")

import duckdb

YEARS = (2015, 2016, 2017, 2018, 2019, 2023, 2024, 2025)

con = duckdb.connect(oag_db)
con.execute("""CREATE TABLE oag(week VARCHAR, dep_airport VARCHAR,
    arr_airport VARCHAR, dep_country VARCHAR, arr_country VARCHAR,
    carrier VARCHAR, seats_total DOUBLE, frequency DOUBLE,
    service_type VARCHAR)""")
rows = []
for apt, home in (("EDI", "GB"), ("AUS", "US")):
    for y in YEARS:
        for m in range(1, 13):
            w = "%d-%02d" % (y, m)
            rows.append((w, apt, "LHR", home, home, "BA", 260000.0, 700.0, "J"))
            rows.append((w, apt, "AMS", home, "NL", "KL", 90000.0, 300.0, "J"))
            rows.append((w, apt, "CDG", home, "FR", "AF", 60000.0, 200.0, "J"))
con.executemany("INSERT INTO oag VALUES (?,?,?,?,?,?,?,?,?)", rows)
con.close()

con = duckdb.connect(aci_db)
con.execute("""CREATE TABLE aci_monthly(iata VARCHAR, airport VARCHAR,
    country VARCHAR, ym VARCHAR, year INTEGER, month INTEGER,
    passengers DOUBLE)""")
arows = []
for apt, nm, ctry in (("EDI", "EDINBURGH, GB", "United Kingdom"),
                      ("AUS", "AUSTIN TX, US", "USA")):
    for y in YEARS:
        for m in range(1, 13):
            arows.append((apt, nm, ctry, "%d-%02d" % (y, m), y, m, 1300000.0))
con.executemany("INSERT INTO aci_monthly VALUES (?,?,?,?,?,?,?)", arows)
con.close()

con = duckdb.connect(t100_db)
con.execute("""CREATE TABLE seg(year INTEGER, month INTEGER, origin VARCHAR,
    dest VARCHAR, carrier VARCHAR, class VARCHAR, distance DOUBLE,
    aircraft_type VARCHAR, dep_performed DOUBLE, seats DOUBLE,
    passengers DOUBLE)""")
con.executemany("INSERT INTO seg VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [(y, m, "AUS", "DFW", "AA", "F", 190.0, "738", 700.0,
                  340000.0, 280000.0)
                 for y in YEARS if y <= 2024 for m in range(1, 13)])
con.close()

FC = {"origin": {"iata": "EDI", "city": "Edinburgh", "country": "GB"},
      "dest": {"iata": "AUS", "city": "Austin", "country": "US"}}
STORES = {"oag": oag_db, "aci": aci_db, "t100": t100_db}

figs, notes, srcs = DF.build_airport(FC, figdir, stores=STORES)

# --- 0. AN IMPOSSIBLE LOAD FACTOR IS NOT DRAWN --------------------------------
# The first version drew it and filed the warning in the audit, so a 159% load
# factor would have reached a client slide with a note nobody reads. The stores
# above give Edinburgh 15.6m annual passengers against 5.0m departing seats,
# which is not a load factor; the chart has to refuse.
check("an implausible load factor is refused, not drawn with a warning",
      "airport_load" not in figs, figs.get("airport_load"))
check("and the reason is the unit mismatch, said out loud",
      "CHECK THE UNITS" in str(notes.get("airport_load", "")),
      str(notes.get("airport_load"))[:80])

# a store pair that DOES produce a sane ratio must still draw
con = duckdb.connect(aci_db)
con.execute("UPDATE aci_monthly SET passengers = 680000.0 WHERE iata = 'EDI'")
con.close()
figs, notes, srcs = DF.build_airport(FC, figdir, stores=STORES)
check("while a plausible one draws normally",
      "airport_load" in figs and "airport_load" not in notes,
      notes.get("airport_load"))

# --- 1. the keyword contract between the two modules --------------------------
check("build_airport returns three things, not two", isinstance(srcs, dict))
check("no chart failed on a TypeError, which is a wiring fault not a data one",
      not [k for k, v in notes.items() if "TypeError" in str(v)],
      {k: v for k, v in notes.items() if "TypeError" in str(v)})
check("all five airport charts drew", sorted(figs) == sorted(DF.AIRPORT_FIGURES),
      {"drawn": sorted(figs), "not": notes})
check("and every one is a real file with something in it",
      all(os.path.getsize(p) > 5000 for p in figs.values()),
      {k: os.path.getsize(v) for k, v in figs.items()})

# --- 2. every drawn chart comes back with its source --------------------------
check("every drawn chart has a source line for its slide",
      sorted(srcs) == sorted(figs), (sorted(srcs), sorted(figs)))
check("and none of them is empty", all(srcs.values()), srcs)
check("the passenger source names ACI, since Edinburgh is not American",
      "ACI" in srcs.get("airport_pax", ""), srcs.get("airport_pax"))
check("the load factor source names BOTH stores",
      "OAG" in srcs.get("airport_load", "")
      and "ACI" in srcs.get("airport_load", ""), srcs.get("airport_load"))
check("the capacity charts are attributed to OAG, which is schedules",
      all("OAG" in srcs.get(k, "")
          for k in ("airport_haul", "airport_airlines")),
      {k: srcs.get(k) for k in ("airport_haul", "airport_airlines")})

# --- 3. THE SOURCE RULE SURVIVES THE ROUND TRIP -------------------------------
# Austin is American, so its chart must be DOT and never ACI, whatever ACI holds.
check("the destination chart is graded on DOT, not ACI",
      "DOT" in srcs.get("dest_pax", "") and "ACI" not in srcs.get("dest_pax", ""),
      srcs.get("dest_pax"))

# --- 4. a missing store is reported, never substituted ------------------------
f2, n2, s2 = DF.build_airport(FC, figdir,
                              stores={"oag": oag_db, "aci": aci_db, "t100": ""})
check("with no DOT store the US destination chart is refused",
      "dest_pax" not in f2, sorted(f2))
check("and the reason names DOT rather than failing silently",
      "DOT" in str(n2.get("dest_pax", "")), n2.get("dest_pax"))
check("while the origin charts are unaffected",
      {"airport_pax", "airport_haul", "airport_airlines"} <= set(f2), sorted(f2))

f3, n3, s3 = DF.build_airport({"origin": {}, "dest": {}}, figdir, stores=STORES)
check("a forecast with no airports draws nothing", not f3, f3)
check("and says so for every slot asked for",
      set(n3) >= {"airport_haul", "airport_airlines", "airport_load"}, sorted(n3))

# --- 4b. airline NAMES, from the tool's own reference --------------------------
# The chart shipped showing U2, FR, LS and RK. app/airline_names.py already held
# every one of them for the dashboard typeahead, so the fix was to use it rather
# than to build a second map that would drift from the first.
nm = DF._carrier_names({})
check("the airline reference is found and is not empty", len(nm) > 100, len(nm))
check("and it holds the carriers Edinburgh actually has",
      [nm.get(c) for c in ("U2", "FR", "LS", "RK", "BA")]
      == ["easyJet", "Ryanair", "Jet2", "Ryanair UK", "British Airways"],
      [nm.get(c) for c in ("U2", "FR", "LS", "RK", "BA")])
check("a caller can still override or extend it",
      DF._carrier_names({"carrier_names": {"BA": "BA plc", "ZZ": "Test Air"}})
      .get("BA") == "BA plc")
check("and an unknown code is left alone rather than guessed at",
      "QQ" not in nm)

# --- 5. TWO MEASURES MUST NEVER SHARE ONE CAPTION -----------------------------
# Edinburgh is ACI throughput (arrivals plus departures plus transit) and Austin
# is DOT departing onboard. Captioned identically, the deck said Edinburgh 17.0m
# against Austin 10.3m and made Edinburgh look the bigger airport. Austin's
# throughput is 21.8m. Nothing on either page betrayed it.
import avia_charts as AC


def caption(**kw):
    got = {}
    real = AC._finish

    def spy(fig, ax, title, sub, ylab, source, path, legend=True):
        got.update({"title": title, "sub": sub or "", "ylab": ylab or ""})
        return real(fig, ax, title, sub, ylab, source, path, legend)

    AC._finish = spy
    try:
        AC.airport_pax(os.path.join(figdir, "cap.png"),
                       series=[(2022, 9e6), (2023, 10e6), (2024, 11e6)],
                       airport="Testville", **kw)
    finally:
        AC._finish = real
    return got


thr = caption(label="ACI airport traffic", measure="throughput")
onb = caption(label="US DOT T-100 segment", measure="onboard")
check("an ACI chart is titled TOTAL passengers",
      thr["title"] == "Testville total passengers", thr["title"])
check("and says the measure includes arrivals and transit",
      "arrivals, departures and transit" in thr["sub"], thr["sub"][:60])
check("a DOT chart is titled DEPARTING passengers",
      onb["title"] == "Testville departing passengers", onb["title"])
check("and its axis says departing, so the two cannot be read as one series",
      onb["ylab"] == "Departing passengers per year"
      and onb["ylab"] != thr["ylab"], (onb["ylab"], thr["ylab"]))
check("and it states that it counts boardings only",
      "boarding at the airport" in onb["sub"], onb["sub"][:60])

shutil.rmtree(tmp, ignore_errors=True)
print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
