#!/usr/bin/env python3
"""Avia Solutions - BT2: pre-launch market growth (Sabre L-2 -> L-1 total pax).
Writes growth_L.csv (a, b, base_mkt_m2). All cohorts, one per call if slow.
"""
import sys
import duckdb

BT2 = "/sessions/wizardly-peaceful-tesla/mnt/Avia/bt2"
SABRE = "/sessions/wizardly-peaceful-tesla/mnt/Avia/sabre.duckdb"

def run(L):
    con = duckdb.connect(SABRE, read_only=True)
    con.execute("SET memory_limit='3GB'")
    con.execute(f"""
    COPY (
      WITH cand AS (SELECT a, b FROM read_csv('{BT2}/launches_{L}.csv', header=true)),
      m2 AS (SELECT least(origin_airport,destination_airport) a,
                    greatest(origin_airport,destination_airport) b, sum(passengers) bm2
             FROM sabre WHERE source_year={L-2} GROUP BY 1,2)
      SELECT cand.a, cand.b, coalesce(m2.bm2, 0) base_mkt_m2
      FROM cand LEFT JOIN m2 ON m2.a=cand.a AND m2.b=cand.b
    ) TO '{BT2}/growth_{L}.csv' (HEADER)""")
    print(f"growth_{L}.csv written")

if __name__ == "__main__":
    for L in [int(x) for x in sys.argv[1:]]:
        run(L)
