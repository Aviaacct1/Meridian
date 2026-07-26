#!/usr/bin/env python3
r"""
Avia Solutions - pull the SYD <-> PER O&D from the Sabre store, 2015-2025.
=========================================================================
True origin-destination market (nonstop + connecting itineraries), both directions, by year, with pax-weighted
fares and the nonstop share. Reads the store read-only. Writes syd_per_sabre.csv and prints a summary.

    py -3.12 pull_syd_per.py
"""
import duckdb, csv

SAB = r"C:\Avia\sabre.duckdb"
con = duckdb.connect(SAB, read_only=True)
con.execute("SET memory_limit='8GB'")

# detailed: year x direction x routing
detail_sql = """
SELECT source_year AS year,
       CASE WHEN origin_airport='SYD' THEN 'SYD-PER' ELSE 'PER-SYD' END AS direction,
       CASE WHEN connecting_airport1 IS NULL OR TRIM(connecting_airport1)='' THEN 'nonstop' ELSE 'connecting' END AS routing,
       ROUND(SUM(passengers),0) AS passengers,
       ROUND(SUM(COALESCE(avg_total_fare_usd,0)*passengers)/NULLIF(SUM(passengers),0),1) AS avg_total_fare_usd,
       ROUND(SUM(COALESCE(avg_base_fare_usd,0)*passengers)/NULLIF(SUM(passengers),0),1)  AS avg_base_fare_usd
FROM sabre
WHERE (origin_airport='SYD' AND destination_airport='PER')
   OR (origin_airport='PER' AND destination_airport='SYD')
GROUP BY source_year, direction, routing
ORDER BY year, direction, routing
"""
cur = con.execute(detail_sql); rows = cur.fetchall(); names = [d[0] for d in cur.description]
with open("syd_per_sabre.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(names); w.writerows(rows)
print(f"wrote syd_per_sabre.csv ({len(rows)} rows)\n")

# per-year both-directions summary
summ = con.execute("""
SELECT source_year AS year,
       ROUND(SUM(passengers),0) AS total_od_pax,
       ROUND(SUM(CASE WHEN connecting_airport1 IS NULL OR TRIM(connecting_airport1)='' THEN passengers ELSE 0 END)*100.0
             /NULLIF(SUM(passengers),0),1) AS nonstop_pct,
       ROUND(SUM(COALESCE(avg_total_fare_usd,0)*passengers)/NULLIF(SUM(passengers),0),0) AS avg_fare_usd
FROM sabre
WHERE (origin_airport='SYD' AND destination_airport='PER')
   OR (origin_airport='PER' AND destination_airport='SYD')
GROUP BY source_year ORDER BY year
""").fetchall()
print(f"SYD<->PER O&D by year (both directions):\n{'year':6}{'total O&D pax':>15}{'nonstop %':>11}{'avg fare $':>12}")
for y, pax, ns, fare in summ:
    print(f"{str(y):6}{int(pax or 0):>15,}{(ns if ns is not None else 0):>10.1f}%{('' if fare is None else f'{int(fare):>11,}')}")
con.close()
