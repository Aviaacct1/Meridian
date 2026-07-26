#!/usr/bin/env python3
r"""
Avia Solutions - raw per-airport-per-year feature pull from the Sabre + OAG stores (for the master backtest).
====================================================================================================
Runs through DuckDB (read-only), self-inspects the columns, and writes two CSVs the master builder folds in:
  airport_transfer_by_year.csv  - raw Sabre transfer share (John's clean measure, straight counts)
  airport_network_by_year.csv   - OAG network scale + competition per airport per year

    py -3.12 pull_airport_features.py

If a column name differs from what the store actually has, it PRINTS the schema and the error instead of
crashing, so paste that back and I'll adjust the query. Nothing here is modelled - direct counts only.
"""
import duckdb, csv, os

OAG = r"C:\Avia\oag.duckdb"
SAB = r"C:\Avia\sabre.duckdb"


def cols(con, tab):
    return [c[1] for c in con.execute(f"PRAGMA table_info('{tab}')").fetchall()]


def write_csv(path, names, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(names); w.writerows(rows)
    print(f"  wrote {path}: {len(rows)} rows, cols={names}")
    for r in rows[:2]:
        print("   sample:", dict(zip(names, r)))


# ---------- SABRE: raw transfer share by airport-year ----------
print("=== SABRE ===")
try:
    sc = duckdb.connect(SAB, read_only=True); sc.execute("SET memory_limit='8GB'")
    scols = cols(sc, "sabre"); print("sabre columns:", scols)
    conns = [c for c in ("connecting_airport1", "connecting_airport2") if c in scols]
    parts = ["SELECT origin_airport AS apt, source_year AS yr, passengers AS loc, 0 AS cn FROM sabre WHERE origin_airport IS NOT NULL",
             "SELECT destination_airport, source_year, passengers, 0 FROM sabre WHERE destination_airport IS NOT NULL"]
    for cc in conns:
        parts.append(f"SELECT {cc}, source_year, 0, passengers FROM sabre WHERE {cc} IS NOT NULL AND TRIM({cc})<>''")
    sql = ("SELECT apt AS airport, yr AS year, SUM(loc) AS local_pax, SUM(cn) AS conn_pax, "
           "ROUND(SUM(cn)*1.0/NULLIF(SUM(loc)+SUM(cn),0),4) AS raw_transfer_pct FROM (\n  "
           + "\n  UNION ALL\n  ".join(parts)
           + "\n) WHERE apt IS NOT NULL AND TRIM(apt)<>'' GROUP BY apt, yr")
    cur = sc.execute(sql); rows = cur.fetchall(); names = [d[0] for d in cur.description]
    write_csv("airport_transfer_by_year.csv", names, rows)
    sc.close()
except Exception as e:
    print("SABRE pull FAILED:", e)

# ---------- OAG: network scale + competition by airport-year ----------
print("\n=== OAG ===")
try:
    oc = duckdb.connect(OAG, read_only=True); oc.execute("SET memory_limit='8GB'")
    ocols = cols(oc, "oag"); print("oag columns:", ocols)
    yexpr = "TRY_CAST(SUBSTR(CAST(week AS VARCHAR),1,4) AS INTEGER)"
    F = "COALESCE(TRY_CAST(frequency AS DOUBLE),1.0)"
    sel = ["dep_airport AS airport", f"{yexpr} AS year",
           "COUNT(DISTINCT carrier) AS n_airlines",
           "COUNT(DISTINCT arr_airport) AS n_destinations",
           f"ROUND(SUM({F}),0) AS total_freq"]
    seatcol = next((c for c in ocols if c.lower() in ("seats", "seat", "total_seats", "seats_total")), None)
    if seatcol:
        sel.append(f"ROUND(SUM(COALESCE(TRY_CAST({seatcol} AS DOUBLE),0)),0) AS seats_on_offer")
    if "carrier_category" in ocols:
        sel.append(f"ROUND(SUM(CASE WHEN lower(carrier_category) LIKE '%low%' OR lower(carrier_category) LIKE '%ulcc%' "
                   f"THEN {F} ELSE 0 END)*1.0/NULLIF(SUM({F}),0),4) AS lcc_freq_share")
    sql = f"SELECT {', '.join(sel)} FROM oag WHERE dep_airport IS NOT NULL AND {yexpr} IS NOT NULL GROUP BY dep_airport, {yexpr}"
    cur = oc.execute(sql); rows = cur.fetchall(); names = [d[0] for d in cur.description]
    write_csv("airport_network_by_year.csv", names, rows)
    if not seatcol:
        print("  NOTE: no seats column found in oag -> seats_on_offer deferred (needs an equipment->seats map).")
    oc.close()
except Exception as e:
    print("OAG pull FAILED:", e)
