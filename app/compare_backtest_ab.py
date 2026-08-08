#!/usr/bin/env python3
r"""Paired comparison of two back-test arms, on common routes only.

    py -3.12 compare_backtest_ab.py CONTROL.csv TEST.csv
    py -3.12 compare_backtest_ab.py A.csv B.csv --by market --by hub --by region

WHY PAIRED. The A/B of 8 August 2026 scored 4,058 routes in the control arm and 4,041 in the test
arm, with 270 and 247 dropped for no outturn or a failure. Comparing the two summaries therefore
compares overlapping but different samples, and a difference of one point in "within +-20%" can be
composition rather than the change under test. backtest.py says so in its own closing note: read
within +-20% on both arms, ON THE SAME ROUTES ONLY. This does that.

WHAT IT REPORTS, and why in this order.

  1. Coverage. How many routes each arm scored, how many are common, and what was lost. If the
     common set is much smaller than either arm, everything below is weaker than it looks.
  2. The headline pair on the common set: within +-20%, within +-10%, and the median ratio.
  3. MOVERS. How many routes improved, worsened, or crossed the +-20% boundary each way. A net gain
     of ten routes made of 200 improving and 190 worsening is a different finding from one made of
     12 improving and 2 worsening, and the summary tables cannot tell them apart.
  4. The same split by any column asked for, so the bucket carrying the change is visible.

The ratio used is fc_over_p2p where present, because that is the like-for-like demand test with the
feed removed, and fc_over_out otherwise. Rows with no ratio in either arm are dropped from the
paired set and counted, never treated as zero.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import statistics

RATIO_COLS = ("fc_over_p2p", "fc_over_out")
KEY_COLS = ("route", "dep", "arr", "carrier", "year")


def _f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except (TypeError, ValueError):
        return None


def load(path):
    """{key: row} plus the ratio column actually used. The key includes carrier and year, because
    the same city pair can launch twice with different operators and must not collide."""
    if not os.path.exists(path):
        raise SystemExit("not found: %s" % path)
    rows, ratio_col = {}, None
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if ratio_col is None:
                for c in RATIO_COLS:
                    if c in r:
                        ratio_col = c
                        break
                if ratio_col is None:
                    raise SystemExit("%s has none of %s" % (path, ", ".join(RATIO_COLS)))
            key = tuple((r.get(c) or "").strip() for c in KEY_COLS if c in r)
            rows[key] = r
    return rows, ratio_col


def band(xs, tol):
    return sum(1 for x in xs if abs(x - 1.0) <= tol)


def pct(n, d):
    return ("%.1f%%" % (100.0 * n / d)) if d else "-"


def report(label, a_vals, b_vals):
    n = len(a_vals)
    print("  %-20s n=%-5d" % (label, n), end="")
    if not n:
        print()
        return
    for tol in (0.20, 0.10):
        na, nb = band(a_vals, tol), band(b_vals, tol)
        print("  +-%d%%: %6s -> %6s (%+d)" % (tol * 100, pct(na, n), pct(nb, n), nb - na), end="")
    ma, mb = statistics.median(a_vals), statistics.median(b_vals)
    print("   median %.2f -> %.2f (%+.2f)" % (ma, mb, mb - ma))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("control")
    ap.add_argument("test")
    ap.add_argument("--by", action="append", default=[],
                    help="split by this column; repeatable (market, hub, region, type, ...)")
    ap.add_argument("--forecastable-only", action="store_true",
                    help="keep only rows where the pre-existing market was at least what the route "
                         "carried, which backtest.py calls the engine's real test")
    a = ap.parse_args()

    ctl, ccol = load(a.control)
    tst, tcol = load(a.test)
    if ccol != tcol:
        print("NOTE: control uses %s, test uses %s. Different measures." % (ccol, tcol))

    common = sorted(set(ctl) & set(tst))
    paired, no_ratio = [], 0
    for k in common:
        x, y = _f(ctl[k].get(ccol)), _f(tst[k].get(tcol))
        if x is None or y is None:
            no_ratio += 1
            continue
        paired.append((k, ctl[k], tst[k], x, y))

    print("=" * 76)
    print("PAIRED A/B on common routes only")
    print("  control %s" % a.control)
    print("  test    %s" % a.test)
    print("=" * 76)
    print("COVERAGE")
    print("  control scored      %d" % len(ctl))
    print("  test scored         %d" % len(tst))
    print("  common              %d" % len(common))
    print("  control only        %d" % len(set(ctl) - set(tst)))
    print("  test only           %d" % len(set(tst) - set(ctl)))
    print("  dropped, no ratio   %d" % no_ratio)
    print("  PAIRED SET          %d" % len(paired))
    if not paired:
        raise SystemExit("nothing to compare.")

    if a.forecastable_only:
        before = len(paired)
        keep = []
        for p in paired:
            nat, p2p = _f(p[1].get("natural")), _f(p[1].get("p2p_outturn"))
            if nat and p2p and nat >= p2p:
                keep.append(p)
        paired = keep
        print("  forecastable only   %d (from %d)" % (len(paired), before))
        if not paired:
            raise SystemExit("nothing left after the forecastable filter.")

    xs = [p[3] for p in paired]
    ys = [p[4] for p in paired]

    print("\nHEADLINE, same routes in both arms")
    report("all paired", xs, ys)

    print("\nMOVERS. A net gain built from many routes moving both ways is a different finding")
    print("from one built from a few, and the summary tables cannot tell them apart.")
    better = sum(1 for x, y in zip(xs, ys) if abs(y - 1) < abs(x - 1))
    worse = sum(1 for x, y in zip(xs, ys) if abs(y - 1) > abs(x - 1))
    into = sum(1 for x, y in zip(xs, ys) if abs(x - 1) > 0.20 >= abs(y - 1))
    out_of = sum(1 for x, y in zip(xs, ys) if abs(y - 1) > 0.20 >= abs(x - 1))
    print("  closer to 1.0       %d" % better)
    print("  further from 1.0    %d" % worse)
    print("  unchanged           %d" % (len(xs) - better - worse))
    print("  crossed INTO +-20%%  %d" % into)
    print("  crossed OUT of      %d   (net %+d)" % (out_of, into - out_of))

    for col in a.by:
        col = {"market": "market", "hub": "hub_dest"}.get(col, col)
        groups = {}
        for k, cr, tr, x, y in paired:
            if col == "market":
                m = _f(cr.get("natural")) or 0
                g = ("<15k" if m < 15000 else "15-50k" if m < 50000
                     else "50-150k" if m < 150000 else ">150k")
            else:
                g = (cr.get(col) or "-").strip() or "-"
            groups.setdefault(g, ([], []))
            groups[g][0].append(x)
            groups[g][1].append(y)
        print("\nBY %s" % col.upper())
        for g in sorted(groups, key=lambda g: -len(groups[g][0])):
            report(g, *groups[g])

    print("\n" + "=" * 76)
    print("READ: the headline says whether the change helped on identical routes. MOVERS says")
    print("whether that is a real shift or churn. The split says which bucket carries it, and")
    print("that bucket is where the refit goes.")


if __name__ == "__main__":
    main()
