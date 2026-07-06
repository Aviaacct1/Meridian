#!/usr/bin/env python3
"""
Avia Solutions - Genoa input check (fare basis + cabin mix) against the Sabre store.
====================================================================================
Answers the two item-2 questions that need raw Sabre, without touching the DuckDB shell:
  1. FARE BASIS - is avg_total_fare_usd round-trip or one-way? (sample of the busiest rows)
  2. CABIN MIX  - the economy/premium split and the business fare, to set econ_share and the
                  premium fare from data rather than assumption.

It connects read-only, so it cannot change the store.

RUN (from anywhere; defaults to the store on C:\\Avia):
    py -3.12 sabre_genoa_check.py
    py -3.12 sabre_genoa_check.py --db "C:\\Avia\\sabre.duckdb" --year 2024
"""
import argparse
import os
import sys

CATCHMENT = ['GOA', 'MXP', 'LIN', 'BGY', 'TRN', 'BLQ']
NYC = ['JFK', 'EWR', 'LGA']


def main():
    ap = argparse.ArgumentParser(description="Genoa fare-basis + cabin-mix check on the Sabre store.")
    ap.add_argument("--db", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--year", type=int, default=2024, help="source_year to read (default 2024)")
    a = ap.parse_args()

    if not os.path.exists(a.db):
        sys.exit(f"ERROR: Sabre store not found at {a.db}. Pass --db with the right path.")

    import duckdb
    con = duckdb.connect(a.db, read_only=True)
    ap_ph = ",".join("?" * len(CATCHMENT))
    nyc_ph = ",".join("?" * len(NYC))
    params = [*CATCHMENT, *NYC, a.year]

    # ---------------------------------------------------------------- 1. fare basis
    print("=" * 78)
    print(f"1. FARE BASIS  -  busiest {', '.join(CATCHMENT)} -> NYC rows, {a.year}")
    print("   (read the fare magnitude: transatlantic economy ~ $350-450 one-way, ~ $700-900 RT)")
    print("=" * 78)
    rows = con.execute(
        f"""
        SELECT origin_airport, destination_airport, cabin_class,
               ROUND(SUM(passengers), 0)                                           AS pax,
               ROUND(SUM(passengers*avg_base_fare_usd)/NULLIF(SUM(passengers),0),0) AS base_fare,
               ROUND(SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),0) AS total_fare
        FROM sabre
        WHERE origin_airport IN ({ap_ph}) AND destination_airport IN ({nyc_ph})
          AND source_year = ?
        GROUP BY origin_airport, destination_airport, cabin_class
        ORDER BY pax DESC
        LIMIT 20
        """, params).fetchall()
    if not rows:
        print(f"   (no rows for {a.year}; try a different --year, e.g. 2023)")
    else:
        print(f"   {'orig':4} {'dest':4} {'cabin':22} {'pax':>10} {'base$':>8} {'total$':>8}")
        for o, d, c, pax, base, total in rows:
            print(f"   {o:4} {d:4} {str(c):22} {pax:>10,.0f} {(base or 0):>8,.0f} {(total or 0):>8,.0f}")

    # ---------------------------------------------------------------- 2. cabin mix
    print("\n" + "=" * 78)
    print(f"2. CABIN MIX  -  {', '.join(CATCHMENT)} -> NYC by cabin, {a.year}")
    print("=" * 78)
    cab = con.execute(
        f"""
        SELECT cabin_class,
               ROUND(SUM(passengers), 0)                                            AS pax,
               ROUND(SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),0) AS pax_wtd_fare
        FROM sabre
        WHERE origin_airport IN ({ap_ph}) AND destination_airport IN ({nyc_ph})
          AND source_year = ?
        GROUP BY cabin_class
        ORDER BY pax DESC
        """, params).fetchall()
    con.close()

    if not cab:
        print(f"   (no rows for {a.year}; try a different --year)")
        return

    total_pax = sum((r[1] or 0) for r in cab)
    print(f"   {'cabin':24} {'pax':>12} {'share':>7} {'pax_wtd_fare':>13}")
    premium_pax = 0.0
    bus_fare = None
    for c, pax, fare in cab:
        pax = pax or 0
        share = pax / total_pax if total_pax else 0
        label = str(c).upper()
        is_premium = any(k in label for k in ("BUSINESS", "FIRST", "PREMIUM"))
        if is_premium:
            premium_pax += pax
        if "BUSINESS" in label and bus_fare is None:
            bus_fare = fare
        print(f"   {str(c):24} {pax:>12,.0f} {share:>6.1%} {(fare or 0):>13,.0f}")

    econ_share = 1.0 - (premium_pax / total_pax) if total_pax else 0.0
    print("\n   ---- read-off for the assess CLI ----")
    print(f"   total pax {total_pax:,.0f}; premium share {premium_pax/total_pax:.1%} "
          f"-> econ_share ~ {econ_share:.2f}")
    if bus_fare:
        print(f"   business pax-weighted fare ${bus_fare:,.0f}  "
              f"(if round-trip, one-way ~ ${bus_fare/2:,.0f}  -> --bus-fare)")
    print("\n   Then, e.g.:")
    print(f"     py -3.12 assess.py genoa_nyc cities5000.txt --sabre \"{a.db}\" "
          f"--econ-share {econ_share:.2f}" + (f" --bus-fare {round((bus_fare or 1500)/2)}" if bus_fare else ""))


if __name__ == "__main__":
    main()
