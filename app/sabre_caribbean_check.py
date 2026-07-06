#!/usr/bin/env python3
"""
Avia Solutions - Italy-Caribbean O&D pull for the winter-sun redeployment case.
===============================================================================
Replaces the PLACEHOLDER demand in cases/genoa_caribbean_observed.json with the REAL
Sabre split. The Caribbean market is in the existing annual store (no new pull needed),
so this runs against C:\\Avia\\sabre.duckdb and writes the observed cache directly.

It reads, for residents of the Genoa catchment (origin airports GOA + the Milan/Turin/
Bologna set), how many flew to each Caribbean leisure airport, by departure airport, plus
the cabin split and fares. That is exactly what assess.py / calibrate_catchment.py need.

RUN (read-only; cannot change the store):
    py -3.12 sabre_caribbean_check.py
    py -3.12 sabre_caribbean_check.py --year 2024 --dests PUJ,CUN,VRA,HAV,MBJ,POP,SDQ
    py -3.12 sabre_caribbean_check.py --write cases/genoa_caribbean_observed.json

Then paste the printed summary back, or just commit the written observed cache and re-run
  py -3.12 assess.py genoa_caribbean cities5000.txt --sabre "C:\\Avia\\sabre.duckdb"
"""
import argparse, json, os, sys

CATCHMENT = ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"]
# Italy-Caribbean leisure gateways: Dominican Republic (PUJ/POP/SDQ), Mexico (CUN), Cuba (VRA/HAV).
DEFAULT_DESTS = ["PUJ", "CUN", "VRA", "HAV", "MBJ", "POP", "SDQ"]


def main():
    ap = argparse.ArgumentParser(description="Italy-Caribbean O&D split from the Sabre store.")
    ap.add_argument("--db", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--dests", default=",".join(DEFAULT_DESTS), help="comma Caribbean dest airports")
    ap.add_argument("--write", default=None, help="write the observed cache JSON to this path")
    a = ap.parse_args()
    dests = [d.strip().upper() for d in a.dests.split(",") if d.strip()]

    if not os.path.exists(a.db):
        sys.exit(f"ERROR: Sabre store not found at {a.db}. Pass --db with the right path.")
    import duckdb
    con = duckdb.connect(a.db, read_only=True)
    aph = ",".join("?" * len(CATCHMENT)); dph = ",".join("?" * len(dests))
    params = [*CATCHMENT, *dests, a.year]

    split = con.execute(
        f"""SELECT origin_airport, ROUND(SUM(passengers),0) AS pax,
                   ROUND(SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),0) AS fare
            FROM sabre
            WHERE origin_airport IN ({aph}) AND destination_airport IN ({dph}) AND source_year = ?
            GROUP BY origin_airport ORDER BY pax DESC""", params).fetchall()
    cabins = con.execute(
        f"""SELECT cabin_class, ROUND(SUM(passengers),0) AS pax,
                   ROUND(SUM(passengers*avg_total_fare_usd)/NULLIF(SUM(passengers),0),0) AS fare
            FROM sabre
            WHERE origin_airport IN ({aph}) AND destination_airport IN ({dph}) AND source_year = ?
            GROUP BY cabin_class ORDER BY pax DESC""", params).fetchall()
    con.close()

    obs = {c: 0.0 for c in CATCHMENT}
    fare_wt = 0.0; total = 0.0
    for ap_, pax, fare in split:
        if ap_ in obs:
            obs[ap_] = float(pax or 0); total += float(pax or 0); fare_wt += float(pax or 0) * float(fare or 0)
    avg_fare = (fare_wt / total) if total else 0.0

    print("=" * 70)
    print(f"Italy (Genoa catchment) -> Caribbean {dests}, {a.year}")
    print("=" * 70)
    if total == 0:
        print("No rows. Try a different --year or widen --dests (check the airport codes in the store).")
        return
    print(f"  {'airport':8} {'pax':>10} {'share':>7} {'pax_wtd_fare':>13}")
    for c in sorted(obs, key=lambda k: -obs[k]):
        print(f"  {c:8} {obs[c]:>10,.0f} {(obs[c]/total):>6.1%} {'':>13}")
    print(f"  {'TOTAL':8} {total:>10,.0f}   avg fare ${avg_fare:,.0f}")
    print("\n  cabin split:")
    for c, pax, fare in cabins:
        print(f"    {str(c):22} {pax:>10,.0f}  ${(fare or 0):>6,.0f}")

    if a.write:
        cache = {"dest_name": "Caribbean", "dest_airports": dests,
                 "observed_split": obs, "total": total, "avg_fare": avg_fare,
                 "source": f"Sabre ODPOO {a.year} via sabre_caribbean_check.py"}
        json.dump(cache, open(a.write, "w"), indent=2)
        print(f"\n  wrote {a.write}  (now: assess.py genoa_caribbean cities5000.txt --sabre <db>)")
    else:
        print("\n  add --write cases/genoa_caribbean_observed.json to replace the placeholder.")


if __name__ == "__main__":
    main()
