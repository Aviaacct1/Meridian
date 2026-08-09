#!/usr/bin/env python3
r"""Pre-launch market fare per route, from Sabre, for the accuracy programme (kickoff section 4.2).

    python3 build_prelaunch_fare.py --baseline app/bt_v1_baseline.csv --out prelaunch_fare.csv

WHY THIS EXISTS. BT2's own conclusion names the residual as "fare and network decisions not visible
in a pre-launch schedule", and fare is in none of BT2's fifteen features. This builds the fare side
of that so it can be tested on the capacity anchor.

THE ONE RULE THAT MATTERS HERE. The fare is read from year L-1, never year L. A launch-year fare is
an outcome, not a forecast input: an airline that fills a route cheaply produces both a low fare and
high traffic, so a launch-year fare would predict the outturn by knowing it. L-1 is what an analyst
sitting before the launch can actually see.

BASIS. All itineraries between the pair, not point-to-point only, because the route is virgin by
construction: whatever market exists before launch is being carried one-stop, and the fare that
matters is what those passengers are paying today. The p2p figure is carried alongside for
comparison but is thin on virgin pairs and is not the feature.

Fares are revenue-weighted, sum(total_revenue_usd) / sum(passengers), never a mean of
avg_total_fare_usd, because the latter averages an average and over-weights small itineraries.

Directions are summed on the unordered pair, matching bt2_growth.py and the rest of the pipeline.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", help="bt_v1_baseline.csv, for the pairs and years")
    ap.add_argument("--profiles", help="BT2 folder holding launch_profile_L.csv, the alternative "
                                       "source of pairs when building for the BT2 cohorts")
    ap.add_argument("--cohorts", default="2016,2017,2018,2019,2025")
    ap.add_argument("--sabre", default=None, help="default: resolved from AVIA_LOCAL_CACHE")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mem", default="4GB")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--temp-dir", default="/tmp/avia_fare_spill",
                    help="DuckDB spill directory; keep it off any synced path")
    a = ap.parse_args()

    sabre = a.sabre
    if not sabre:
        root = os.environ.get("AVIA_LOCAL_CACHE")
        sabre = os.path.join(root, "sabre.duckdb") if root else None
    if not sabre or not os.path.exists(sabre):
        sys.exit("Sabre store not found. Set AVIA_LOCAL_CACHE or pass --sabre.")

    want, nrows = set(), 0
    if a.profiles:
        # BT2 cohorts. launch_profile_L.csv already carries the unordered pair as a and b, and the
        # cohort year L, so the pre-launch year is L-1 exactly as it is for the baseline.
        for L in [int(c) for c in a.cohorts.split(",") if c.strip()]:
            p = os.path.join(a.profiles, "launch_profile_%d.csv" % L)
            if not os.path.exists(p):
                print("  no launch_profile for %d, skipped and reported, not filled" % L)
                continue
            for r in csv.DictReader(open(p, newline="", encoding="utf-8-sig")):
                nrows += 1
                if r.get("a") and r.get("b"):
                    want.add((r["a"].strip(), r["b"].strip(), L - 1))
    else:
        for r in csv.DictReader(open(a.baseline, newline="", encoding="utf-8-sig")):
            nrows += 1
            d, x = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
            y = r.get("year")
            if d and x and y:
                want.add((min(d, x), max(d, x), int(y) - 1))
    years = sorted({w[2] for w in want})
    print("%d source rows, %d distinct pairs, pre-launch years %s"
          % (nrows, len({(w[0], w[1]) for w in want}), years))

    import duckdb
    os.makedirs(a.temp_dir, exist_ok=True)
    con = duckdb.connect(sabre, read_only=True)
    con.execute("SET memory_limit='%s'; SET threads=%d; SET temp_directory='%s'"
                % (a.mem, a.threads, a.temp_dir))

    yl = ",".join(str(y) for y in years)
    q = """
      SELECT least(origin_airport, destination_airport) a,
             greatest(origin_airport, destination_airport) b,
             source_year yr,
             sum(passengers)                                            pax_all,
             sum(total_revenue_usd)                                     rev_all,
             sum(base_revenue_usd)                                      base_rev_all,
             sum(CASE WHEN connecting_airport1 IS NULL
                        OR trim(connecting_airport1)='' THEN passengers END)         pax_p2p,
             sum(CASE WHEN connecting_airport1 IS NULL
                        OR trim(connecting_airport1)='' THEN total_revenue_usd END)  rev_p2p
      FROM sabre
      WHERE source_year IN (%s)
      GROUP BY 1,2,3
    """ % yl
    print("querying Sabre for %s ..." % yl)
    got = {}
    for a_, b_, yr, pax, rev, brev, pax2, rev2 in con.execute(q).fetchall():
        got[(a_, b_, yr)] = (pax or 0.0, rev or 0.0, brev or 0.0, pax2 or 0.0, rev2 or 0.0)
    print("  %d pair-years in Sabre for those years" % len(got))

    hit = miss = nofare = 0
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["a", "b", "pre_year", "pre_pax", "pre_fare_usd", "pre_base_fare_usd",
                    "pre_p2p_pax", "pre_p2p_fare_usd"])
        for key in sorted(want):
            v = got.get(key)
            if not v:
                miss += 1
                continue
            pax, rev, brev, pax2, rev2 = v
            if not pax:
                miss += 1
                continue
            fare = rev / pax if rev else None
            if fare is None:
                nofare += 1
            hit += 1
            w.writerow([key[0], key[1], key[2], round(pax, 1),
                        round(fare, 2) if fare else "",
                        round(brev / pax, 2) if brev else "",
                        round(pax2, 1) if pax2 else "",
                        round(rev2 / pax2, 2) if pax2 and rev2 else ""])

    # Coverage is reported, never assumed. A pair with no pre-launch Sabre row is left out of the
    # file rather than written as a zero fare, per flag rather than fill.
    print("  matched %d pairs, %d with no pre-launch Sabre row (left out, not zero-filled), "
          "%d matched but carrying no revenue" % (hit, miss, nofare))
    print("  written: %s" % a.out)


if __name__ == "__main__":
    main()
