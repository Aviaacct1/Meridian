"""Fare basis check for the long-haul margin flag (W1, 27 Sep 2026).

The P&L prices every economy seat at the Sabre ALL-CABIN average TOTAL fare (taxes included) and then
prices the business cabin again at a fixed 1,400 USD. This script measures, per pair, what that
choice does: all-cabin total fare against economy-only and premium-only fares, total against base
(taxes and charges out), and the premium share of passengers. Read-only; nothing is changed.

    Workstation, a normal window:
      cd C:\\src\\meridian
      $env:PYTHONNOUSERSITE = "1"
      py -3.12 tools\\fare_check.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

import duckdb

DB = os.environ.get("AVIA_SABRE") or r"E:\Avia\sabre.duckdb"
PAIRS = ["EDI-BOS", "EDI-JFK", "EDI-ATL", "EDI-HKG", "EDI-PVG", "BLQ-JFK", "SJC-TPE", "SFO-TPE",
         "SOU-JFK", "LHR-JFK", "TIF-AUH", "AHB-DXB", "NOC-FRA"]

PREM = ("upper(cabin_class) LIKE '%BUSINESS%' OR upper(cabin_class) LIKE '%FIRST%' "
        "OR upper(cabin_class) LIKE '%PREMIUM%'")

con = duckdb.connect(DB, read_only=True)
con.execute("SET memory_limit='4GB'; SET threads=4")
year = con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
print("Sabre store %s, year %s. Fares in USD per passenger as Sabre states them." % (DB, year))
print("%-8s %9s %6s %9s %9s %9s %9s %9s %9s" % ("pair", "pax", "prem%", "all_tot", "all_base",
                                              "econ_tot", "econ_base", "prem_tot", "prem_base"))
for p in PAIRS:
    a, b = p.split("-")
    q = """
      SELECT SUM(passengers),
             SUM(CASE WHEN {prem} THEN passengers ELSE 0 END),
             SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),
             SUM(passengers*avg_base_fare_usd)/NULLIF(SUM(passengers),0),
             SUM(CASE WHEN NOT ({prem}) THEN passengers*avg_total_fare_usd END)/NULLIF(SUM(CASE WHEN NOT ({prem}) THEN passengers END),0),
             SUM(CASE WHEN NOT ({prem}) THEN passengers*avg_base_fare_usd END)/NULLIF(SUM(CASE WHEN NOT ({prem}) THEN passengers END),0),
             SUM(CASE WHEN {prem} THEN passengers*avg_total_fare_usd END)/NULLIF(SUM(CASE WHEN {prem} THEN passengers END),0),
             SUM(CASE WHEN {prem} THEN passengers*avg_base_fare_usd END)/NULLIF(SUM(CASE WHEN {prem} THEN passengers END),0)
      FROM sabre WHERE source_year=? AND least(origin_airport,destination_airport)=? AND greatest(origin_airport,destination_airport)=?
    """.format(prem=PREM)
    r = con.execute(q, [year, min(a, b), max(a, b)]).fetchone()
    if not r or not r[0]:
        print("%-8s no Sabre traffic" % p)
        continue
    f = lambda v: ("%9.0f" % v) if v is not None else "%9s" % "-"
    print("%-8s %9.0f %5.1f%% %s %s %s %s %s %s" % (p, r[0], 100.0 * (r[1] or 0) / r[0],
          f(r[2]), f(r[3]), f(r[4]), f(r[5]), f(r[6]), f(r[7])))
cols = [c[0] for c in con.execute("DESCRIBE sabre").fetchall()]
print("cabin column present:", "cabin_class" in cols, "| directionality values:",
      con.execute("SELECT list(DISTINCT directionality) FROM sabre WHERE source_year=?", [year]).fetchone()[0])
