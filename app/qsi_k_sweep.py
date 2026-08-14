#!/usr/bin/env python3
r"""
Avia Solutions - what k should be, measured rather than argued.
===============================================================
THE PROBLEM IN ONE LINE. The portal runs the Engine V2 QSI feed at qsi_k = 1.0 on every
case with a departure time, because cortex_app line 867 switches it on whenever one is
set. backtest.py's --qsi-feed is OFF by default and its --qsi-k defaults to 0.06. So the
accuracy evidence was gathered on a different feed model from the one the product ships,
and where it was gathered on the same model it was at a level nearly seventeen times
lower.

WHY IT IS OPEN AGAIN. RECUT-RESULT measured the feed over-reading actual connecting
traffic by circa ten times on the median back-test route. The standing objection was that
SJC-TPE read 19% BELOW a human forecast on the same leg and SJC-TPE-IS-INSIDE established
the route is not atypical, so the two could not both be true. BEHIND-MARKET-IDENTIFIED
(15 August) resolved that: the 19% is a market DEFINITION difference, the analyst having
sized the behind leg on the whole US-Taipei market including nonstop traffic. The
objection is withdrawn and the over-read finding stands unopposed.

WHAT THIS RUNS. One back-test arm per k, plus a V1 control with the QSI feed off, all on
identical routes and identical settings so the only thing that varies is the feed. Each
arm writes its own CSV and is scored on the back-test's OWN definition, the share of
graded routes within +/-20%, taken from the fc_over_p2p column so the figures are
comparable with every arm already in the log.

READ IT AS A SHAPE, NOT A WINNER. If the within-20% share rises monotonically as k falls,
the shipped level is simply too high and the back-tested 0.06 is the answer. If it peaks
somewhere in between, that is the calibration. If the V1 control beats every V2 arm, the
schedule-quality feed is not earning its place at any level and SCHEDULE-BANKING's fate
applies to it too.

RUNTIME. Each arm is a full back-test. Size it with --limit first and read the per-arm
timing before committing a night to it. --resume skips an arm whose CSV already exists,
so a stopped run continues rather than restarting.

Usage (workstation), sized first then run properly:
    py -3.12 qsi_k_sweep.py --limit 150 --out-dir E:\Avia\ksweep_probe
    py -3.12 qsi_k_sweep.py --out-dir E:\Avia\ksweep --jobs 4 --resume
"""
import argparse
import csv
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KS = "1.0,0.5,0.25,0.12,0.06"


def score(path):
    """The back-test's own measure: median fc/p2p and the share within +/-20%.

    Reads fc_over_p2p, the column backtest.py scores on at line 1117, so these numbers sit
    beside every arm already recorded rather than beside a definition invented here. Rows
    with no ratio are counted as ungraded and never as a miss, which would flatter a k that
    simply graded fewer routes.
    """
    if not os.path.exists(path):
        return None
    vals = []
    ungraded = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("fc_over_p2p") or "").strip()
            if not raw:
                ungraded += 1
                continue
            try:
                vals.append(float(raw))
            except ValueError:
                ungraded += 1
    if not vals:
        return {"n": 0, "ungraded": ungraded}
    vals.sort()
    n = len(vals)
    med = vals[n // 2] if n % 2 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])
    return {"n": n, "ungraded": ungraded, "median": med,
            "within20": sum(1 for x in vals if 0.8 <= x <= 1.2) / n,
            "within40": sum(1 for x in vals if 0.6 <= x <= 1.4) / n,
            "over": sum(1 for x in vals if x > 1.2) / n,
            "under": sum(1 for x in vals if x < 0.8) / n}


def arm(label, extra, args, out_dir):
    """One back-test arm. Returns (label, csv path, seconds) or (label, None, seconds)."""
    out = os.path.join(out_dir, "bt_%s.csv" % label)
    if os.path.exists(out) and args.resume:
        print("  %-10s already present, skipped" % label)
        return label, out, 0.0
    # THE STORE PATHS ARE NOT backtest.py's DEFAULTS. It defaults to C:\Avia\oag.duckdb and
    # C:\Avia\sabre.duckdb, which exist on neither machine: the workstation's data root is
    # E:\Avia. Without these every arm returned in 0s with no rows, and the first version of
    # this tool captured the child's output and printed it only on a non-zero exit, so the
    # reason was swallowed. Both faults are fixed here.
    cmd = [sys.executable, os.path.join(HERE, "backtest.py"), "--out", out,
           "--jobs", str(args.jobs), "--oag", args.oag, "--sabre", args.sabre]
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    if args.years:
        cmd += ["--years", args.years]
    if args.temp_dir:
        cmd += ["--temp-dir", args.temp_dir]
    if args.extra:
        cmd += args.extra.split()
    cmd += extra
    started = time.time()
    print("  %-10s %s" % (label, " ".join(cmd[-6:])))
    r = subprocess.run(cmd, capture_output=True, text=True)
    secs = time.time() - started
    tail = ((r.stdout or "")[-800:] + (r.stderr or "")[-800:]).strip()
    if r.returncode != 0:
        print("  %-10s FAILED after %.0fs\n%s" % (label, secs, tail))
        return label, None, secs
    # A ZERO EXIT IS NOT A RESULT. backtest.py can finish cleanly having graded nothing, and an
    # arm that graded nothing must say why on the spot rather than appear as a dash in a table
    # six lines further down.
    if not os.path.exists(out) or os.path.getsize(out) < 40:
        print("  %-10s exited cleanly in %.0fs but wrote no rows. Its own output:\n%s"
              % (label, secs, tail or "(nothing on stdout or stderr)"))
        return label, None, secs
    print("  %-10s done in %.0fs" % (label, secs))
    return label, out, secs


def main():
    ap = argparse.ArgumentParser(description="Back-test the QSI feed at several levels of k.")
    ap.add_argument("--ks", default=DEFAULT_KS, help="comma-separated k values")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--oag", default=None, help="OAG store; defaults to config.OAG_DUCKDB")
    ap.add_argument("--sabre", default=None, help="Sabre store; defaults to config.SABRE_DUCKDB")
    ap.add_argument("--limit", type=int, default=None, help="cap routes; use to SIZE the run first")
    ap.add_argument("--years", default=None)
    ap.add_argument("--jobs", type=int, default=4, help="4 not 8 on the 16GB workstation")
    ap.add_argument("--temp-dir", default=None)
    ap.add_argument("--extra", default="", help="extra flags passed to every arm, identically")
    ap.add_argument("--no-control", action="store_true", help="skip the V1 arm")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    # The stores come from config, which resolves them per machine, rather than from
    # backtest.py's own defaults, which name a folder that exists on neither.
    if not args.oag or not args.sabre:
        sys.path.insert(0, HERE)
        import config as CFG
        args.oag = args.oag or str(CFG.OAG_DUCKDB)
        args.sabre = args.sabre or str(CFG.SABRE_DUCKDB)
    for label, path in (("OAG", args.oag), ("Sabre", args.sabre)):
        if not os.path.exists(path):
            print("ERROR: %s store not found at %s" % (label, path))
            return 2

    os.makedirs(args.out_dir, exist_ok=True)
    ks = [k.strip() for k in args.ks.split(",") if k.strip()]
    print("QSI feed level sweep. Every arm runs identical routes and settings; only the feed "
          "varies.\nOut: %s\n" % args.out_dir)

    results = []
    if not args.no_control:
        results.append(arm("v1_control", [], args, args.out_dir))
    for k in ks:
        results.append(arm("k%s" % k.replace(".", "p"), ["--qsi-feed", "--qsi-k", k],
                           args, args.out_dir))

    print("\n  %-12s %6s %9s %10s %10s %8s %8s"
          % ("arm", "n", "median", "within20", "within40", "over", "under"))
    for label, path, _s in results:
        s = score(path) if path else None
        if not s or not s.get("n"):
            print("  %-12s %6s  no graded rows" % (label, "-"))
            continue
        print("  %-12s %6d %9.2f %9.1f%% %9.1f%% %7.1f%% %7.1f%%"
              % (label, s["n"], s["median"], 100 * s["within20"], 100 * s["within40"],
                 100 * s["over"], 100 * s["under"]))

    print("\n  The V1 control is the arm to beat. A V2 level that does not beat it is not a "
          "calibration\n  problem, it is a feed that is not earning its place, and "
          "SCHEDULE-BANKING is the precedent.")
    print("  Ungraded routes are reported separately and never counted as misses: a k that "
          "grades\n  fewer routes must not read as a k that gets more of them right.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
