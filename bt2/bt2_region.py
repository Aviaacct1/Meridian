#!/usr/bin/env python3
r"""Country to region, and each carrier's home country, both from OAG. 9 August 2026.

    python3 bt2_region.py

WHY. The tail analysis of the long-haul international full-service segment named a signature that
none of BT2's features can see. The over-read tail is Chinese and Gulf carriers, MU, HU, CZ, QR, on
China-facing country pairs, AU-CN, CN-FR, CA-CN, QA-US. The under-read tail is North Atlantic,
IE-US, GB-US, IT-US, IL-US, flown by UA, WS, AA, EI. Those are two different industries and BT2 has
no geography at all: its features carry a domestic flag and a carrier identity for carriers with
fifteen or more launches, and nothing else about where in the world any of this is happening.

This writes the two lookups needed to give it geography, both from OAG so they agree with the store
everything else is measured on:

  region_by_country.json   country to region, taken as the region carrying the most seats for that
                           country, because the store labels some services under more than one
  carrier_home.json        carrier to home country and home region, home taken as the country the
                           carrier flies the most departing seats from

Both are structural and slow moving, so they are built once across a reference year rather than per
cohort. The reference year is stated in the file so a later reader knows what it was.

Avia Solutions Limited. All rights reserved.
"""
import json

import duckdb

from bt2_paths import BT2, OAG, require

require(OAG=OAG)

REF = "2018"          # a full pre-COVID year, before the network disruption


def main():
    con = duckdb.connect(OAG, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=4")

    rows = con.execute("""
      SELECT dep_country, region, sum(try_cast(seats_total as bigint)) s
      FROM oag WHERE service_type='J' AND week LIKE '%s-%%'
        AND dep_country IS NOT NULL AND trim(dep_country) <> ''
      GROUP BY 1,2""" % REF).fetchall()
    best = {}
    for ctry, reg, s in rows:
        if reg and (ctry not in best or s > best[ctry][1]):
            best[ctry] = (reg, s)
    reg_by_ctry = {k: v[0] for k, v in best.items()}
    json.dump({"_reference_year": REF, "map": reg_by_ctry},
              open("%s/region_by_country.json" % BT2, "w"))
    print("region_by_country.json: %d countries over %d regions"
          % (len(reg_by_ctry), len(set(reg_by_ctry.values()))))

    rows = con.execute("""
      SELECT carrier, dep_country, sum(try_cast(seats_total as bigint)) s
      FROM oag WHERE service_type='J' AND week LIKE '%s-%%'
        AND dep_country IS NOT NULL AND trim(dep_country) <> ''
      GROUP BY 1,2""" % REF).fetchall()
    home = {}
    for car, ctry, s in rows:
        if car and (car not in home or s > home[car][1]):
            home[car] = (ctry, s)
    out = {c: {"country": v[0], "region": reg_by_ctry.get(v[0], "")} for c, v in home.items()}
    json.dump({"_reference_year": REF, "map": out}, open("%s/carrier_home.json" % BT2, "w"))
    print("carrier_home.json: %d carriers" % len(out))
    for c in ("MU", "HU", "CZ", "QR", "EI", "WS", "UA", "BA"):
        v = out.get(c)
        print("    %-4s %s" % (c, "%s, %s" % (v["country"], v["region"]) if v else "not found"))


if __name__ == "__main__":
    main()
