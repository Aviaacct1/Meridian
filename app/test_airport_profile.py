#!/usr/bin/env python3
"""Offline test of the airport profile. Builds a real DuckDB with the store's
own traps in it, so the queries are exercised rather than mocked.

    py -3.12 test_airport_profile.py

The fixture reproduces, deliberately:
  * the SAME year present at monthly, annual, half-year and weekly granularity,
    which is the double-count trap the spine rule exists for
  * the 2020 to 2022 pandemic hole
  * a North American airport with no monthly labels before 2019
  * a part year
  * service_type rows that are not 'J'

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import airport_profile as AP

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def build(path):
    import duckdb
    con = duckdb.connect(path)
    con.execute("""CREATE TABLE oag(
        week VARCHAR, dep_airport VARCHAR, arr_airport VARCHAR,
        dep_country VARCHAR, arr_country VARCHAR, carrier VARCHAR,
        seats_total DOUBLE, frequency DOUBLE, service_type VARCHAR)""")
    rows = []

    def add(week, dep, arr, depc, arrc, car, seats, svc="J"):
        rows.append((week, dep, arr, depc, arrc, car, seats, 30.0, svc))

    # EDI: full monthly 2017-2019, hole 2020-2022, monthly 2023-2025.
    # 2019 deliberately part year (9 months) to prove part years are named.
    for year, months in ((2017, 12), (2018, 12), (2019, 9),
                         (2023, 12), (2024, 12), (2025, 12)):
        for m in range(1, months + 1):
            w = "%d-%02d" % (year, m)
            add(w, "EDI", "LHR", "GB", "GB", "BA", 10000)     # domestic
            add(w, "EDI", "AMS", "GB", "NL", "KL", 6000)      # international
            add(w, "EDI", "JFK", "GB", "US", "DL", 2000)      # international
    # THE DOUBLE-COUNT TRAP: the same 2018 flights again at three other
    # granularities. A reader that does not filter to monthly labels sees ~4x.
    add("2018", "EDI", "LHR", "GB", "GB", "BA", 120000)                 # annual
    add("2018-H1", "EDI", "LHR", "GB", "GB", "BA", 60000)               # half year
    add("2018-05-26", "EDI", "LHR", "GB", "GB", "BA", 2300)             # weekly snap
    # a freighter row, which must never reach a passenger seat count
    add("2024-06", "EDI", "CVG", "GB", "US", "FX", 999999, svc="F")
    # AUS: North America, so NO monthly labels before 2019
    for year in (2019, 2023, 2024, 2025):
        for m in range(1, 13):
            add("%d-%02d" % (year, m), "AUS", "DFW", "US", "US", "AA", 8000)
    add("2017", "AUS", "DFW", "US", "US", "AA", 90000)   # annual only, unusable
    con.executemany("INSERT INTO oag VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.close()


tmp = os.path.join(tempfile.gettempdir(), "avia_test_oag.duckdb")
if os.path.exists(tmp):
    os.remove(tmp)
build(tmp)

# --- 1. the spine rule: monthly only, no double count ------------------------
p = AP.profile(tmp, "EDI", home_country="GB")
check("profile reads", p["ok"], p["notes"])
seats = dict(p["seats"])
# 12 months x (10000 + 6000 + 2000) = 216,000. Anything near 336,000 means the
# annual / half-year / weekly rows were summed in as well.
check("2018 seats are the monthly sum only", seats.get(2018) == 216000,
      "{:,.0f}".format(seats.get(2018, 0)))
check("the freighter row is excluded", seats.get(2024) == 216000,
      "{:,.0f}".format(seats.get(2024, 0)))
check("frequency is not multiplied in again", seats.get(2017) == 216000,
      "{:,.0f}".format(seats.get(2017, 0)))

# --- 2. gaps are named, never filled -----------------------------------------
years = [y for y, _m in p["years"]]
check("the pandemic years are absent from the series",
      not any(y in years for y in (2020, 2021, 2022)), years)
notes = " ".join(p["notes"])
check("and the deck is told why", "pandemic" in notes and "2020" in notes)
check("a thin year is named as thin, not as absent",
      "2019 has 9 months" in notes and "too partial to plot" in notes,
      [n for n in p["notes"] if "2019" in n])
check("and it is NOT reported as absent",
      "2019 absent" not in notes, [n for n in p["notes"] if "absent" in n])
check("2019 is excluded at the default threshold", 2019 not in years, years)

# --- 3. the North American coverage gap --------------------------------------
a = AP.profile(tmp, "AUS", home_country="US")
ay = [y for y, _m in a["years"]]
check("AUS has no monthly years before 2019", min(ay) >= 2019, ay)
check("its annual-only 2017 is not silently used", 2017 not in ay, ay)

# --- 4. the splits ------------------------------------------------------------
h = p["haul"]
check("domestic and international split", h and h[2018]["Domestic"] == 120000
      and h[2018]["International"] == 96000,
      h[2018] if h else None)
al = p["airlines"]
check("airlines ranked by seats", al and al[0][0] == "BA", al)
check("and their route counts come with them", al and al[0][2] == 1, al)
check("the freighter carrier is not in the airline list",
      al and "FX" not in [c for c, _s, _r in al], al)

# --- 5. growth ----------------------------------------------------------------
g = AP.cagr(p["seats"])
check("cagr returns its own span, not a bare rate", g and len(g) == 3, g)
check("a flat series is 0%", abs(AP.cagr([(2017, 100.0), (2020, 100.0)])[0]) < 1e-9)
check("a doubling over 3 years is circa 26%",
      abs(AP.cagr([(2017, 100.0), (2020, 200.0)])[0] - 0.2599) < 0.001)
check("one point cannot give a rate", AP.cagr([(2019, 100.0)]) is None)

# --- 5b. seats are not passengers, and O&D is not onboard --------------------
check("a US airport is graded on DOT", AP.pax_source("US")[0] == "dot",
      AP.pax_source("US")[:2])
check("elsewhere prefers ACI", AP.pax_source("GB")[0] == "aci",
      AP.pax_source("GB")[:2])
check("and falls back to Sabre where ACI is absent",
      AP.pax_source("GB", aci_available=False)[0] == "sabre",
      AP.pax_source("GB", aci_available=False)[:2])
check("the US is NEVER given a non-DOT source",
      AP.pax_source("US", aci_available=True)[0] == "dot")

# ACI throughput must be halved before it meets departing seats
tp = [(2024, 2000.0)]
check("throughput halves to a departing count",
      AP.throughput_to_departing(tp) == [(2024, 1000.0)],
      AP.throughput_to_departing(tp))
lf_tp, n_tp = AP.effective_load_factor([(2024, 1250.0)], tp, "throughput")
check("throughput gives a sane load factor, not double",
      lf_tp and abs(lf_tp[0][1] - 0.80) < 1e-9, lf_tp)
check("and the halving is disclosed, not buried",
      "halved" in n_tp and "approximation" in n_tp, n_tp[:60])
lf_bad, n_bad = AP.effective_load_factor([(2024, 1000.0)], [(2024, 1900.0)], "onboard")
check("an implausible load factor is flagged as a unit error",
      "CHECK THE UNITS" in n_bad, n_bad[:70])

# the pax readers are not wired yet and must say so
pb = AP.pax_by_year("EDI", "GB", stores={"aci": "/no/such/aci.duckdb"})
check("a missing ACI store is named", pb["series"] == []
      and "not at" in " ".join(pb["notes"]), pb["notes"])
pu = AP.pax_by_year("AUS", "US", stores={"t100": ""})
check("a US airport with no DOT store refuses to substitute Sabre",
      pu["series"] == [] and "graded on DOT" in " ".join(pu["notes"]),
      pu["notes"])
seats_s = [(2023, 1000.0), (2024, 1000.0)]
pax_s = [(2023, 800.0), (2024, 850.0)]
lf, note = AP.effective_load_factor(seats_s, pax_s, "onboard")
check("onboard data gives a real load factor",
      lf and abs(lf[0][1] - 0.80) < 1e-9, lf)
lf2, note2 = AP.effective_load_factor(seats_s, pax_s, "od")
check("O&D data REFUSES to give a load factor", lf2 == [], lf2)
check("and says why, naming onboard as what it needs",
      "onboard" in note2 and "not a load factor" in note2, note2)
lf3, note3 = AP.effective_load_factor([(2023, 1000.0)], [(2019, 800.0)], "onboard")
check("no shared year is reported, not silently empty",
      lf3 == [] and "do not share" in note3, note3)

# --- 6. failure reports rather than returning a confident zero ---------------
miss = AP.profile("/no/such/store.duckdb", "EDI")
check("a missing store is reported", not miss["ok"] and "not at" in " ".join(miss["notes"]))
none = AP.profile(tmp, "ZZZ")
check("an airport with no coverage is reported, not zeroed",
      not none["ok"] and "monthly OAG coverage" in " ".join(none["notes"]))
check("and it never returns a fabricated series", none["seats"] == [])

os.remove(tmp)
print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
