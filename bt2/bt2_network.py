#!/usr/bin/env python3
r"""Carrier network reach at the launch endpoints' countries, pre-launch month. 9 August 2026.

    python3 bt2_network.py 2016 2017 2018 2019 2024 2025

WHY THIS EXISTS. Carrier base strength was the only feature family that paid on 9 August: adding the
launching carrier's own departing seats at each endpoint, and its share of all seats at that airport
and month, took blind leave-one-cohort-out from 53.5% to 55.6%. Everything else tried that day gave
nothing: fare, departure-time quality, the connection components, a size calibration, recency
weighting. So the next thing to try is more of what worked, and the obvious gap is that base
strength is an AIRPORT measure on a problem whose hard half is long-haul international.

An airline launching into a country it already flies to is doing something different from one
opening a country. Base strength cannot see that: it looks only at the two endpoint airports.

WHAT IS PULLED, all for the pre-launch month so nothing is known that would not be known in advance:

  carrier|country|month     the carrier's departing seats from that country
  ALL|country|month         every carrier's departing seats from that country, for the share
  carrier|SYSTEM|month      the carrier's total departing seats anywhere, its network size

Region duplicates are deduped by max, matching bt2_base, because the OAG store holds the same
service under several region labels and summing them counts it twice.

Writes network_L.json into the BT2 folder. One cohort per argument.

Avia Solutions Limited. All rights reserved.
"""
import csv
import json
import sys

import duckdb

from bt2_paths import BT2, OAG, require

require(OAG=OAG)


def run(L):
    prof = list(csv.DictReader(open("%s/launch_profile_%d.csv" % (BT2, L))))
    months = sorted({r["pre_month"] for r in prof})
    if not months:
        print("%d: no pre-launch months in the profile, nothing pulled" % L)
        return
    con = duckdb.connect(OAG, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=4")
    ms = "(" + ",".join("'%s'" % m for m in months) + ")"

    # Deduped once, then aggregated three ways off the same deduped set, so the country totals and
    # the system totals cannot disagree with each other.
    con.execute("""
      CREATE TEMP TABLE ded AS
      SELECT carrier, dep_country, week, max(cnt) seats FROM (
        SELECT carrier, dep_country, week, region, sum(try_cast(seats_total as bigint)) cnt
        FROM oag WHERE service_type='J' AND week IN %s
          AND dep_country IS NOT NULL AND trim(dep_country) <> ''
        GROUP BY 1,2,3,4) GROUP BY 1,2,3""" % ms)

    d = {}
    for car, ctry, wk, v in con.execute("SELECT carrier, dep_country, week, seats FROM ded").fetchall():
        d["%s|%s|%s" % (car, ctry, wk)] = int(v or 0)
    for ctry, wk, v in con.execute(
            "SELECT dep_country, week, sum(seats) FROM ded GROUP BY 1,2").fetchall():
        d["ALL|%s|%s" % (ctry, wk)] = int(v or 0)
    for car, wk, v in con.execute(
            "SELECT carrier, week, sum(seats) FROM ded GROUP BY 1,2").fetchall():
        d["%s|SYSTEM|%s" % (car, wk)] = int(v or 0)

    json.dump(d, open("%s/network_%d.json" % (BT2, L), "w"))
    print("%d: %d carrier-country-month network cells over %d months" % (L, len(d), len(months)))


if __name__ == "__main__":
    for L in [int(x) for x in sys.argv[1:]]:
        run(L)
