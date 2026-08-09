#!/usr/bin/env python3
r"""Test candidate features against the capacity anchor, scored held-out.

    py -3.12 anchor_features.py bt_v1_baseline.csv
    py -3.12 anchor_features.py A.csv --train 2017 --test 2018

WHY THIS EXISTS. On 8 August 2026 the picture became clear and uncomfortable: the shipped engine
scores 17% within +-20% blind, a capacity anchor with ONE number scores 43%, and the same anchor
with twelve visible buckets scores 48% held-out. Pushing past twelve buckets raises the FITTED
number all the way to 100% and drives the held-out number back down to 43%, which is the shape of
the 89% fitted against 51% blind pair.

So the question is no longer "more buckets". It is "which features carry signal that survives to a
route the weights have never seen". That is what this scores, and it always scores held-out,
because a fitted number can be made to say anything.

    train on one cohort, fit a median correction per cell, score on a LATER cohort.

READ THE THREE COLUMNS TOGETHER. Fitted rising while held-out falls is memorisation, and the
average cell size tells you when it started: with 891 cells over 1,343 routes the average cell
holds 1.5 routes, so a "weight" is a record of one or two outcomes rather than a pattern.

WHAT IS NOT YET IN HERE, and both are the point of the exercise (8 August 2026):

  * departure-time quality, the market-weighted QSI share of onward markets at the flown time. It
    is not in BT2's fifteen features and the pre-test found it varies enormously across routes
    (CV 2.41, p90/p10 469x). Computed for 3,179 routes in pretest_qsi.csv. Join it on route and add
    it here. NOTE what this does NOT test: the 8 August A/B asked whether the wave-timed feed
    improves the structural engine's forecast, and it did not. Whether q predicts O&D-per-seat on
    top of the anchor is a different question and is untested.
  * fare. BT2's own conclusion is that the residual sits in "fare and network decisions not visible
    in a pre-launch schedule". Fare is not in the feature set and Sabre carries it. build_od_fare.py
    builds the pull.

A boundary worth holding in view while chasing the last few points: on the 381 US routes where the
outturn can be measured twice, Sabre and DOT agree within +-20% on only 64% of them. Beyond about
60% blind you are measuring against a ruler that disagrees with itself.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import statistics
from collections import defaultdict


def _f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except (TypeError, ValueError):
        return None


def load(path, train_year, test_year):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8-sig")))
    ok = [r for r in rows
          if _f(r.get("capacity")) and _f(r.get("outturn_pax")) and _f(r.get("forecast_pax"))]
    tr = [r for r in ok if str(r.get("year")) == str(train_year)]
    te = [r for r in ok if str(r.get("year")) == str(test_year)]
    return ok, tr, te


# --- candidate cell definitions. Each returns a hashable key. ------------------------------
def haul(r):
    d = _f(r.get("gcd_km")) or 0
    return "<800" if d < 800 else "800-2500" if d < 2500 else "2500-6000" if d < 6000 else ">6000"


def market(r):
    m = _f(r.get("natural")) or 0
    return "<15k" if m < 15000 else "15-50k" if m < 50000 else "50-150k" if m < 150000 else ">150k"


def dom(r):
    return "DOM" if (r.get("dep_country") or "") == (r.get("arr_country") or "") else "INT"


def feed_share(r):
    """The engine's own estimate of how much of the route is connecting, banded. A proxy for the
    departure-time work: if connecting intensity carries signal on the anchor, timing plausibly
    will too, and this is testable with data already on disk."""
    cap = _f(r.get("capacity")) or 0
    fb = (_f(r.get("feed_beyond")) or 0) + (_f(r.get("feed_behind")) or 0)
    if not cap:
        return "?"
    s = fb / cap
    return "feed<1%" if s < 0.01 else "feed1-5%" if s < 0.05 else "feed5-15%" if s < 0.15 else "feed>15%"


def propensity_band(r):
    p = _f(r.get("propensity")) or 0
    return "prop<0.3" if p < 0.3 else "prop0.3-0.6" if p < 0.6 else "prop0.6-0.9" if p < 0.9 else "prop>0.9"


def gauge(r):
    """Seats per departure, banded. Aircraft size is an airline decision and BT2 uses it."""
    cap = _f(r.get("capacity")) or 0
    return "gauge?" if not cap else ("small" if cap < 20000 else "mid" if cap < 60000
                                     else "large" if cap < 150000 else "xl")


CELLS = {
    "type": lambda r: r.get("type"),
    "haul": haul,
    "market": market,
    "domint": dom,
    "region": lambda r: r.get("region"),
    "hub": lambda r: r.get("hub_dest"),
    "feed": feed_share,
    "prop": propensity_band,
    "gauge": gauge,
}


def band(rs, tol=0.20):
    return 100.0 * sum(1 for x in rs if abs(x - 1) <= tol) / len(rs) if rs else 0.0


def run(tr, te, names, minn=20):
    keyfn = (lambda r: tuple(CELLS[n](r) for n in names)) if names else (lambda r: "_")
    b = defaultdict(list)
    for r in tr:
        b[keyfn(r)].append(_f(r["outturn_pax"]) / _f(r["capacity"]))
    glob = statistics.median([_f(r["outturn_pax"]) / _f(r["capacity"]) for r in tr])
    corr = {k: statistics.median(v) for k, v in b.items() if len(v) >= minn}

    def score(rows):
        return band([_f(r["capacity"]) * corr.get(keyfn(r), glob) / _f(r["outturn_pax"])
                     for r in rows])

    return score(tr), score(te), len(corr), (len(tr) / max(1, len(b)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--train", default="2017")
    ap.add_argument("--test", default="2018")
    ap.add_argument("--min-cell", type=int, default=20,
                    help="a cell with fewer routes than this falls back to the global weight, "
                         "which is what stops a two-route cell being called a pattern")
    a = ap.parse_args()

    ok, tr, te = load(a.csv, a.train, a.test)
    print("train %s n=%d   test %s n=%d   min cell %d\n" % (a.train, len(tr), a.test, len(te), a.min_cell))
    print("  %-34s %5s %7s %10s %9s" % ("cells", "used", "avg n", "FITTED", "HELD-OUT"))

    def show(names):
        fit, hold, used, avg = run(tr, te, names, a.min_cell)
        print("  %-34s %5d %7.1f %9.1f%% %8.1f%%" %
              (" x ".join(names) if names else "(anchor alone)", used, avg, fit, hold))
        return hold

    base = show([])
    print()
    singles = sorted(((show([n]), n) for n in CELLS), reverse=True)
    print("\n  best single addition: %s (%+.1f points held-out)\n" % (singles[0][1], singles[0][0] - base))

    best = [singles[0][1]]
    cur = singles[0][0]
    for _ in range(3):                      # greedy: add one at a time, stop when it stops paying
        cand = [(run(tr, te, best + [n], a.min_cell)[1], n) for n in CELLS if n not in best]
        cand.sort(reverse=True)
        if not cand or cand[0][0] <= cur + 0.3:
            break
        cur, nxt = cand[0]
        best.append(nxt)
        show(best)
    print("\n  greedy best: %s at %.1f%% held-out" % (" x ".join(best), cur))
    print("\n  Read fitted against held-out. Where fitted rises and held-out does not, the cells")
    print("  have started recording routes rather than finding patterns; the avg n column says when.")


if __name__ == "__main__":
    main()
