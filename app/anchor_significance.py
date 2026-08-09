#!/usr/bin/env python3
r"""Is the feature ranking in the accuracy kickoff measurable, or is it one split's luck?

    python3 anchor_significance.py bt_v1_baseline.csv

WHY THIS EXISTS. anchor_features.py scores held-out, which is right, and it prints fitted beside
held-out and the average cell size, which is right. What it does not print is whether the gaps it
reports are larger than the noise on the held-out set it reports them from. Three numbers in the
kickoff of 9 August 2026 sit inside a percentage point of each other: type x haul 48.4%, type x
haul x dom/int 48.3%, and x market 48.3%. On 1,256 held-out routes one percentage point is thirteen
routes. A ranking read off differences that small is a ranking read off noise.

Two checks, both on the same data and neither of them a new run:

  1. McNemar on the paired held-out routes. Every feature set is scored on the SAME routes, so the
     comparison is paired and the question is not "are two proportions different" but "how many
     routes cross the +-20% band in each direction". Only the discordant routes carry information.
     A two-sided exact binomial on those gives the p-value.

  2. The reverse split. Train 2018 and score 2017. It is not a new dataset, but it is an
     independent observation of the same ranking on the same engine output, and a ranking that
     reverses when the cohorts swap was never a ranking.

Avia Solutions Limited. All rights reserved.
"""
import csv
import statistics
import sys
from collections import defaultdict
from math import comb


def _f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except (TypeError, ValueError):
        return None


def haul(r):
    d = _f(r.get("gcd_km")) or 0
    return "<800" if d < 800 else "800-2500" if d < 2500 else "2500-6000" if d < 6000 else ">6000"


def market(r):
    m = _f(r.get("natural")) or 0
    return "<15k" if m < 15000 else "15-50k" if m < 50000 else "50-150k" if m < 150000 else ">150k"


def dom(r):
    return "DOM" if (r.get("dep_country") or "") == (r.get("arr_country") or "") else "INT"


def feed_share(r):
    cap = _f(r.get("capacity")) or 0
    fb = (_f(r.get("feed_beyond")) or 0) + (_f(r.get("feed_behind")) or 0)
    if not cap:
        return "?"
    s = fb / cap
    return "feed<1%" if s < 0.01 else "feed1-5%" if s < 0.05 else "feed5-15%" if s < 0.15 else "feed>15%"


CELLS = {
    "type": lambda r: r.get("type"),
    "haul": haul,
    "market": market,
    "domint": dom,
    "region": lambda r: r.get("region"),
    "feed": feed_share,
}


def hits(tr, te, names, minn=20, tol=0.20):
    """Per held-out route, did the anchor with these weights land within +-20%. Same construction
    as anchor_features.run, returned route by route so the comparison can be paired."""
    keyfn = (lambda r: tuple(CELLS[n](r) for n in names)) if names else (lambda r: "_")
    b = defaultdict(list)
    for r in tr:
        b[keyfn(r)].append(_f(r["outturn_pax"]) / _f(r["capacity"]))
    glob = statistics.median([_f(r["outturn_pax"]) / _f(r["capacity"]) for r in tr])
    corr = {k: statistics.median(v) for k, v in b.items() if len(v) >= minn}
    out = {}
    for r in te:
        ratio = _f(r["capacity"]) * corr.get(keyfn(r), glob) / _f(r["outturn_pax"])
        out[r["route"] + "|" + str(r.get("carrier"))] = abs(ratio - 1) <= tol
    return out


def mcnemar(a, b):
    """Two-sided exact binomial on the discordant routes. Returns b_only, a_only, p."""
    keys = set(a) & set(b)
    n01 = sum(1 for k in keys if not a[k] and b[k])      # b gains
    n10 = sum(1 for k in keys if a[k] and not b[k])      # b loses
    n = n01 + n10
    if n == 0:
        return n01, n10, 1.0
    lo = min(n01, n10)
    p = 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n)
    return n01, n10, min(1.0, p)


SETS = [[], ["type"], ["haul"], ["type", "haul"], ["haul", "feed"],
        ["type", "haul", "domint"], ["type", "haul", "market"]]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "bt_v1_baseline.csv"
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8-sig")))
    ok = [r for r in rows
          if _f(r.get("capacity")) and _f(r.get("outturn_pax")) and _f(r.get("forecast_pax"))]
    by = {y: [r for r in ok if str(r.get("year")) == y] for y in ("2017", "2018")}

    for tr_y, te_y in (("2017", "2018"), ("2018", "2017")):
        tr, te = by[tr_y], by[te_y]
        print("\n=== train %s n=%d, score %s n=%d, min cell 20 ===" % (tr_y, len(tr), te_y, len(te)))
        h = {tuple(s): hits(tr, te, s) for s in SETS}
        base = h[()]
        print("  %-26s %9s   %s" % ("cells", "HELD-OUT", "against the anchor alone: gains, losses, p"))
        for s in SETS:
            hs = h[tuple(s)]
            pct = 100.0 * sum(hs.values()) / len(hs)
            if not s:
                print("  %-26s %8.1f%%" % ("(anchor alone)", pct))
                continue
            g, l, p = mcnemar(base, hs)
            print("  %-26s %8.1f%%   +%-4d -%-4d  p=%.3f%s"
                  % (" x ".join(s), pct, g, l, p, "" if p < 0.05 else "   NOT MEASURABLE"))

        print("\n  head to head, the three the kickoff ranks:")
        for x, y in (( ["type", "haul"], ["haul", "feed"] ),
                     ( ["type", "haul"], ["type", "haul", "domint"] ),
                     ( ["type", "haul"], ["type", "haul", "market"] )):
            g, l, p = mcnemar(h[tuple(x)], h[tuple(y)])
            print("    %-22s vs %-24s +%-3d -%-3d  p=%.3f%s"
                  % (" x ".join(x), " x ".join(y), g, l, p, "" if p < 0.05 else "   NOT MEASURABLE"))


if __name__ == "__main__":
    main()
