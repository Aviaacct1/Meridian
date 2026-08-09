#!/usr/bin/env python3
r"""What KIND of demand the pre-launch market is: point of sale and cabin mix. 9 August 2026.

    python3 bt2_demand_mix.py --cohorts 2016 --out /tmp/mix_2016.csv

WHY THIS AND NOT ANOTHER FEATURE. The width analysis of the same day is the reason. The blind log
error on the long-haul international full-service segment has a robust sigma of 0.424 against 0.187
on the short-haul segment, and both are already centred, so perfectly centring the hard segment
changes its hit rate by nothing at all. Reaching 50% there needs the spread cut by 36%. Every
mechanism tested on 9 August shifts location: fare, departure time, connection structure, network
reach, region calibration. None of them narrows spread.

Point of sale and cabin mix are the two things in the Sabre store that describe what KIND of demand
exists rather than how much of it. That is the only family left that could plausibly narrow rather
than shift, because it separates markets that behave differently at the same size.

  pos      passengers by point-of-sale country, resolved to three shares: sold at end a, sold at
           end b, sold in a third country. A market sold entirely at one end is a different
           proposition from a balanced one, and a market sold mostly in third countries is
           connecting demand that a new nonstop may not capture at all
  cabin    premium share, BUSINESS plus FIRST plus PREMIUM COACH over all passengers. A thin
           premium-heavy market and a dense leisure market of the same size are not the same route

Read from year L-1 throughout, so nothing here is knowable only after the launch.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

PREMIUM = ("BUSINESS", "FIRST", "PREMIUM COACH")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profiles", default=None, help="BT2 folder; default from bt2_paths")
    ap.add_argument("--cohorts", required=True, help="comma separated, one call per cohort is fine")
    ap.add_argument("--sabre", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mem", default="3GB")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--temp-dir", default="/tmp/avia_mix_spill")
    a = ap.parse_args()

    from bt2_paths import BT2, SABRE
    prof_dir = a.profiles or BT2
    sabre = a.sabre or SABRE
    if not sabre or not os.path.exists(sabre):
        sys.exit("Sabre store not found. Set AVIA_LOCAL_CACHE or pass --sabre.")

    want = {}
    for L in [int(c) for c in a.cohorts.split(",") if c.strip()]:
        p = os.path.join(prof_dir, "launch_profile_%d.csv" % L)
        if not os.path.exists(p):
            print("  no launch_profile for %d, skipped and reported, not filled" % L)
            continue
        for r in csv.DictReader(open(p, newline="", encoding="utf-8-sig")):
            if r.get("a") and r.get("b"):
                want[(r["a"], r["b"], L - 1)] = (r.get("ctry_a", ""), r.get("ctry_b", ""))
    years = sorted({k[2] for k in want})
    print("%d pairs, pre-launch years %s" % (len(want), years))

    import duckdb
    os.makedirs(a.temp_dir, exist_ok=True)
    con = duckdb.connect(sabre, read_only=True)
    con.execute("SET memory_limit='%s'; SET threads=%d; SET temp_directory='%s'"
                % (a.mem, a.threads, a.temp_dir))
    con.execute("CREATE TEMP TABLE want(a VARCHAR, b VARCHAR, yr INTEGER)")
    con.executemany("INSERT INTO want VALUES (?,?,?)", [list(k) for k in want])

    yl = ",".join(str(y) for y in years)
    rows = con.execute("""
      WITH s AS (
        SELECT least(origin_airport, destination_airport) a,
               greatest(origin_airport, destination_airport) b,
               source_year yr, poo_country pos, cabin_class cab, sum(passengers) pax
        FROM sabre WHERE source_year IN (%s) GROUP BY 1,2,3,4,5)
      SELECT s.a, s.b, s.yr, s.pos, s.cab, s.pax
      FROM s JOIN want w ON w.a=s.a AND w.b=s.b AND w.yr=s.yr
    """ % yl).fetchall()
    print("  %d pair-year-pos-cabin rows for the wanted pairs" % len(rows))

    agg = defaultdict(lambda: {"tot": 0.0, "a": 0.0, "b": 0.0, "prem": 0.0})
    for a_, b_, yr, pos, cab, pax in rows:
        k = (a_, b_, yr)
        ca, cb = want.get(k, ("", ""))
        d = agg[k]
        pax = pax or 0.0
        d["tot"] += pax
        if pos and pos == ca:
            d["a"] += pax
        elif pos and pos == cb:
            d["b"] += pax
        if cab in PREMIUM:
            d["prem"] += pax

    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["a", "b", "pre_year", "pre_pax", "pos_share_a", "pos_share_b",
                    "pos_share_third", "pos_imbalance", "premium_share"])
        n = 0
        for k in sorted(want):
            d = agg.get(k)
            # A pair with no pre-launch Sabre row is left out rather than written as zeros. A zero
            # premium share and an absent market are different facts.
            if not d or d["tot"] <= 0:
                continue
            t = d["tot"]
            sa, sb = d["a"] / t, d["b"] / t
            imb = abs(sa - sb) / (sa + sb) if (sa + sb) > 0 else ""
            w.writerow([k[0], k[1], k[2], round(t, 1), round(sa, 4), round(sb, 4),
                        round(1 - sa - sb, 4), (round(imb, 4) if imb != "" else ""),
                        round(d["prem"] / t, 4)])
            n += 1
    print("  written %d pairs to %s (%d had no pre-launch market and are left out)"
          % (n, a.out, len(want) - n))


if __name__ == "__main__":
    main()
