#!/usr/bin/env python3
r"""US DOT DB1B outturns for US-domestic launches, read directly. Supersedes bt2_db1b.py.

    python3 bt2_db1b_direct.py --cohort 2018
    python3 bt2_db1b_direct.py --cohort 2018 --assemble

WHY A REWRITE RATHER THAN A FIX. bt2_db1b.py streams each 1.8GB quarter through `head`, `tail` and
`/dev/stdin` under `/bin/bash`, which was reasonable inside a Linux session with a 45 second call
cap and runs on neither the Dev PC nor the workstation, both of which are Windows. Repairing its
paths on 9 August made it importable and no more runnable than before. DuckDB reads the CSV itself,
so the split-and-pipe machinery goes away entirely and the stage becomes portable.

WHY IT MATTERS. John's rule, adopted 5 August: an airport is graded against the source it can
verify, so anything US domestic is graded against the DOT, not against Sabre. The relaxed sample
built on 9 August has no DOT outturns because they existed only for the narrower pair list, and a
site that says DOT while the file says Sabre is the kind of drift this programme exists to stop.

WHAT IS AVAILABLE, checked on E: 9 August 2026: DB1B Market quarters run 2000 to 2024 with 2016 Q1
absent and nothing for 2025. So cohorts 2016 (three quarters, scaled and flagged), 2017, 2018, 2019
and 2024 can be graded against DOT, and 2025 cannot until the 2025 release lands.

Nonstop is MktCoupons = 1. DB1B is a ten percent ticket sample, so passengers are multiplied by ten.
Both directions of the unordered pair are summed, matching every other stage.

Resumable: a quarter already written is skipped, so this can be run in as many sittings as it takes.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import glob
import os
import sys

import duckdb

from bt2_paths import BT2, US_MARKET, require

require(US_MARKET=US_MARKET)


def us_pairs(L):
    p = "%s/launch_profile_%d.csv" % (BT2, L)
    if not os.path.exists(p):
        sys.exit("no launch profile for %d at %s" % (L, p))
    out = []
    for r in csv.DictReader(open(p, newline="", encoding="utf-8-sig")):
        if r.get("ctry_a") == "US" and r.get("ctry_b") == "US":
            out.append((r["a"], r["b"]))
    return out


def quarter_csv(L, Q):
    d = os.path.join(US_MARKET, "Origin_and_Destination_Survey_DB1BMarket_%d_%d" % (L, Q))
    hits = glob.glob(os.path.join(d, "*.csv"))
    return hits[0] if hits else None


def run_quarter(L, Q, mem, threads, temp):
    outp = "%s/db1b_qtr_%d_%d.csv" % (BT2, L, Q)
    if os.path.exists(outp) and os.path.getsize(outp) > 20:
        print("  %d Q%d: already done" % (L, Q))
        return
    src = quarter_csv(L, Q)
    if not src:
        # Flagged, never filled. A missing quarter changes the annual total and the assemble step
        # scales for it and says so on every affected row.
        open("%s/db1b_qtr_%d_%d.MISSING" % (BT2, L, Q), "w").write("no DB1B Market extract on the store\n")
        print("  %d Q%d: NO EXTRACT, flagged not filled" % (L, Q))
        return
    aps = sorted({x for p in us_pairs(L) for x in p})
    if not aps:
        print("  %d: no US domestic pairs in the profile" % L)
        return
    s = "(" + ",".join("'%s'" % a for a in aps) + ")"
    con = duckdb.connect()
    con.execute("SET memory_limit='%s'; SET threads=%d; SET temp_directory='%s'" % (mem, threads, temp))
    con.execute("""
      COPY (SELECT least(Origin, Dest) a, greatest(Origin, Dest) b,
                   sum(try_cast(Passengers AS DOUBLE)) pax_sample
            FROM read_csv(?, header=true, ignore_errors=true)
            WHERE try_cast(MktCoupons AS INT) = 1 AND Origin IN %s AND Dest IN %s
            GROUP BY 1,2) TO '%s' (HEADER)""" % (s, s, outp.replace("'", "''")), [src])
    n = sum(1 for _ in open(outp)) - 1
    print("  %d Q%d: %d pairs" % (L, Q, n))


def assemble(L):
    pairs = set(us_pairs(L))
    agg, quarters, miss = {}, set(), []
    for Q in (1, 2, 3, 4):
        p = "%s/db1b_qtr_%d_%d.csv" % (BT2, L, Q)
        if not (os.path.exists(p) and os.path.getsize(p) > 20):
            miss.append(Q)
            continue
        quarters.add(Q)
        for r in csv.DictReader(open(p)):
            k = (r["a"], r["b"])
            if k in pairs:
                agg[k] = agg.get(k, 0.0) + float(r["pax_sample"] or 0)
    nq = len(quarters)
    if not nq:
        print("  %d: no quarters, nothing assembled" % L)
        return
    outp = "%s/db1b_outturn_%d.csv" % (BT2, L)
    with open(outp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["a", "b", "db1b_pax", "quarters", "scaled"])
        for (a, b), v in sorted(agg.items()):
            w.writerow([a, b, round(v * 10 * 4 / nq), nq, nq < 4])
    print("  %d: %d pairs from %d quarters%s" % (L, len(agg), nq,
          (" (missing Q%s, scaled 4/%d and FLAGGED on every row)" % (miss, nq)) if miss else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cohort", type=int, required=True)
    ap.add_argument("--quarter", type=int, help="one quarter only; default is all four")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--mem", default="3GB")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--temp-dir", default="/tmp/avia_db1b_spill")
    a = ap.parse_args()
    os.makedirs(a.temp_dir, exist_ok=True)
    if a.assemble:
        assemble(a.cohort)
        return
    print("cohort %d, %d US domestic pairs" % (a.cohort, len(us_pairs(a.cohort))))
    for Q in ([a.quarter] if a.quarter else (1, 2, 3, 4)):
        run_quarter(a.cohort, Q, a.mem, a.threads, a.temp_dir)


if __name__ == "__main__":
    main()
