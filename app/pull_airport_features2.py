#!/usr/bin/env python3
r"""
Avia Solutions - master backtest, raw feature pull BLOCK 2 (gauge, premium mix, fare level, LCC fix).
====================================================================================================
Follows pull_airport_features.py. Adds the next describable drivers the store schemas revealed, all per
airport-year, all direct aggregates (the fares are an airport-level PRICE-LEVEL context, joined at pre-launch
vintage - not the route's own outturn fare, which is a leakage outcome and stays out of any model).

    py -3.12 pull_airport_features2.py
"""
import duckdb, csv

OAG = r"C:\Avia\oag.duckdb"
SAB = r"C:\Avia\sabre.duckdb"


def write_csv(path, names, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(names); w.writerows(rows)
    print(f"  wrote {path}: {len(rows)} rows, cols={names}")
    for r in rows[:2]:
        print("   sample:", dict(zip(names, r)))


print("=== OAG block 2 (gauge, premium mix, LCC) ===")
try:
    oc = duckdb.connect(OAG, read_only=True); oc.execute("SET memory_limit='8GB'")
    # first, show the real carrier_category labels so the LCC flag is correct
    cats = oc.execute("SELECT DISTINCT carrier_category FROM oag WHERE carrier_category IS NOT NULL LIMIT 30").fetchall()
    print("  carrier_category values:", [c[0] for c in cats])
    y = "TRY_CAST(SUBSTR(CAST(week AS VARCHAR),1,4) AS INTEGER)"
    F = "COALESCE(TRY_CAST(frequency AS DOUBLE),1.0)"
    sql = f"""SELECT dep_airport AS airport, {y} AS year,
        ROUND(SUM(COALESCE(TRY_CAST(first_seats AS DOUBLE),0)+COALESCE(TRY_CAST(business_seats AS DOUBLE),0))
              /NULLIF(SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE),0)),0),4) AS premium_seat_share,
        ROUND(SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE),0))/NULLIF(SUM({F}),0),1) AS avg_gauge,
        ROUND(SUM(CASE WHEN lower(COALESCE(carrier_category,'')) NOT LIKE '%main%'
                        AND lower(COALESCE(carrier_category,'')) NOT LIKE '%full%'
                        AND COALESCE(carrier_category,'')<>'' THEN {F} ELSE 0 END)*1.0
              /NULLIF(SUM({F}),0),4) AS non_mainline_share
        FROM oag WHERE dep_airport IS NOT NULL AND {y} IS NOT NULL GROUP BY dep_airport, {y}"""
    cur = oc.execute(sql); write_csv("airport_gauge_by_year.csv", [d[0] for d in cur.description], cur.fetchall())
    oc.close()
except Exception as e:
    print("OAG block2 FAILED:", e)

print("\n=== SABRE block 2 (airport price level, as origin) ===")
try:
    sc = duckdb.connect(SAB, read_only=True); sc.execute("SET memory_limit='8GB'")
    sql = """SELECT origin_airport AS airport, source_year AS year,
        ROUND(SUM(COALESCE(avg_total_fare_usd,0)*passengers)/NULLIF(SUM(passengers),0),1) AS avg_fare_out,
        ROUND(SUM(COALESCE(avg_base_fare_usd,0)*passengers)/NULLIF(SUM(passengers),0),1) AS avg_basefare_out
        FROM sabre WHERE origin_airport IS NOT NULL GROUP BY origin_airport, source_year"""
    cur = sc.execute(sql); write_csv("airport_fare_by_year.csv", [d[0] for d in cur.description], cur.fetchall())
    sc.close()
except Exception as e:
    print("SABRE block2 FAILED:", e)
