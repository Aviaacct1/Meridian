#!/usr/bin/env python3
"""Avia Solutions - BT2: carrier base strength at endpoints, pre-launch month.
For each cohort: carrier x dep_airport x month departing seats (region-deduped by max),
restricted to the cohort's pre-launch months and endpoint airports.
Writes base_strength_L.json. One cohort per call: python3 bt2_base.py 2017
"""
import csv, duckdb, json, sys

# PATHS. Rewritten 9 August 2026, see bt2_paths.py. The two constants here were hardcoded Cowork
# session mounts that resolve on neither the Dev PC nor the workstation, so this stage could not run.
from bt2_paths import BT2, OAG, require
require(OAG=OAG)

def run(L):
    prof = list(csv.DictReader(open(f"{BT2}/launch_profile_{L}.csv")))
    months = sorted({r["pre_month"] for r in prof})
    aps = sorted({r["a"] for r in prof} | {r["b"] for r in prof})
    con = duckdb.connect(OAG, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=4")
    ms = "(" + ",".join(f"'{m}'" for m in months) + ")"
    s = "(" + ",".join(f"'{a}'" for a in aps) + ")"
    rows = con.execute(f"""
      SELECT carrier, dep_airport, week, max(cnt) FROM (
        SELECT carrier, dep_airport, week, region, sum(try_cast(seats_total as bigint)) cnt
        FROM oag WHERE service_type='J' AND week IN {ms} AND dep_airport IN {s}
        GROUP BY 1,2,3,4) GROUP BY 1,2,3""").fetchall()
    d = {}
    for car, ap_, wk, v in rows:
        d[f"{car}|{ap_}|{wk}"] = int(v or 0)
    json.dump(d, open(f"{BT2}/base_strength_{L}.json", "w"))
    print(f"{L}: {len(d)} carrier-airport-month base cells")

if __name__ == "__main__":
    for L in [int(x) for x in sys.argv[1:]]:
        run(L)
