#!/usr/bin/env python3
r"""Does the pre-launch fare predict O&D-per-seat on top of the capacity anchor? Kickoff section 4.2.

    python3 anchor_fare_test.py bt_v1_baseline.csv prelaunch_fare.csv

BT2's own conclusion names the residual as "fare and network decisions not visible in a pre-launch
schedule", and fare is in none of BT2's fifteen features. This tests the fare half of that on the
anchor, held-out, in both split directions, with the paired test that says whether a gap is larger
than the noise on the held-out set it came from.

FOUR CANDIDATE CELLS, and the reason for each.

  market      whether the pair carried ANY Sabre traffic in L-1. 529 of 2,830 baseline pairs carry
              none, and those are the induced routes the engine reads at a tenth of actual. The
              absence of a fare is information before the fare itself is.
  fare        the revenue-weighted pre-launch fare, in bands. Mostly distance, so weak on its own.
  yield       fare divided by great-circle distance. Distance taken out, so this is price level.
  farevshaul  fare divided by the median fare of its own haul band. Whether the market is dear or
              cheap FOR ITS LENGTH, which is the form the hypothesis actually takes: a market
              paying above the going rate for its distance is one a new nonstop can stimulate.

BAND EDGES COME FROM THE TRAINING COHORT ONLY. Quantile edges fitted on all rows would let the
held-out routes choose their own boundaries, which is a quiet way of scoring fitted and calling it
held-out.

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


def dom(r):
    return "DOM" if (r.get("dep_country") or "") == (r.get("arr_country") or "") else "INT"


def feed_share(r):
    cap = _f(r.get("capacity")) or 0
    fb = (_f(r.get("feed_beyond")) or 0) + (_f(r.get("feed_behind")) or 0)
    if not cap:
        return "?"
    s = fb / cap
    return "feed<1%" if s < 0.01 else "feed1-5%" if s < 0.05 else "feed5-15%" if s < 0.15 else "feed>15%"


def quartiles(vals):
    v = sorted(vals)
    if len(v) < 8:
        return []
    return [v[int(len(v) * q)] for q in (0.25, 0.50, 0.75)]


def banded(x, edges, prefix):
    if x is None:
        return prefix + ":none"
    if not edges:
        return prefix + ":all"
    for i, e in enumerate(edges):
        if x < e:
            return "%s:q%d" % (prefix, i + 1)
    return "%s:q%d" % (prefix, len(edges) + 1)


def build_cells(train):
    """Fit band edges on the training cohort only, then return the cell functions."""
    fe = quartiles([r["_fare"] for r in train if r["_fare"]])
    ye = quartiles([r["_yield"] for r in train if r["_yield"]])
    ve = quartiles([r["_fvh"] for r in train if r["_fvh"]])
    return {
        "type": lambda r: r.get("type"),
        "haul": haul,
        "domint": dom,
        "feed": feed_share,
        "market": lambda r: "market" if r["_fare"] else "nomarket",
        "fare": lambda r: banded(r["_fare"], fe, "fare"),
        "yield": lambda r: banded(r["_yield"], ye, "yld"),
        "farevshaul": lambda r: banded(r["_fvh"], ve, "fvh"),
    }


def hits(tr, te, names, cells, minn=20, tol=0.20):
    keyfn = (lambda r: tuple(cells[n](r) for n in names)) if names else (lambda r: "_")
    b = defaultdict(list)
    for r in tr:
        b[keyfn(r)].append(_f(r["outturn_pax"]) / _f(r["capacity"]))
    glob = statistics.median([_f(r["outturn_pax"]) / _f(r["capacity"]) for r in tr])
    corr = {k: statistics.median(v) for k, v in b.items() if len(v) >= minn}
    out = {}
    for r in te:
        ratio = _f(r["capacity"]) * corr.get(keyfn(r), glob) / _f(r["outturn_pax"])
        out[r["route"] + "|" + str(r.get("carrier"))] = abs(ratio - 1) <= tol
    return out, len(corr), len(tr) / max(1, len(b))


def fitted(tr, names, cells, minn=20, tol=0.20):
    h, _, _ = hits(tr, tr, names, cells, minn, tol)
    return 100.0 * sum(h.values()) / len(h)


def mcnemar(a, b):
    keys = set(a) & set(b)
    n01 = sum(1 for k in keys if not a[k] and b[k])
    n10 = sum(1 for k in keys if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def main():
    base_p = sys.argv[1]
    fare_p = sys.argv[2]

    fare = {}
    for r in csv.DictReader(open(fare_p, newline="", encoding="utf-8-sig")):
        fare[(r["a"], r["b"], int(r["pre_year"]))] = r

    rows = list(csv.DictReader(open(base_p, newline="", encoding="utf-8-sig")))
    ok = []
    for r in rows:
        if not (_f(r.get("capacity")) and _f(r.get("outturn_pax")) and _f(r.get("forecast_pax"))):
            continue
        d, x = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
        fr = fare.get((min(d, x), max(d, x), int(r["year"]) - 1))
        f = _f(fr.get("pre_fare_usd")) if fr else None
        g = _f(r.get("gcd_km"))
        r["_fare"] = f
        r["_yield"] = (f / g) if (f and g) else None
        r["_prepax"] = _f(fr.get("pre_pax")) if fr else None
        ok.append(r)

    # fare relative to the median of its own haul band, computed once over all usable rows because
    # it is a property of the market, not of the split. The BAND EDGES on it are still fitted on
    # training rows only, which is where the leak would be.
    med = {}
    for h in {haul(r) for r in ok}:
        vs = [r["_fare"] for r in ok if haul(r) == h and r["_fare"]]
        med[h] = statistics.median(vs) if vs else None
    for r in ok:
        m = med.get(haul(r))
        r["_fvh"] = (r["_fare"] / m) if (r["_fare"] and m) else None

    by = {y: [r for r in ok if str(r.get("year")) == y] for y in ("2017", "2018")}
    have = sum(1 for r in ok if r["_fare"])
    print("usable rows %d, with a pre-launch fare %d (%.1f%%), without %d"
          % (len(ok), have, 100.0 * have / len(ok), len(ok) - have))

    SETS = [[], ["haul"], ["type", "haul"], ["haul", "feed"],
            ["market"], ["haul", "market"], ["type", "haul", "market"],
            ["fare"], ["haul", "fare"], ["yield"], ["haul", "yield"],
            ["farevshaul"], ["haul", "farevshaul"], ["type", "haul", "farevshaul"]]

    for tr_y, te_y in (("2017", "2018"), ("2018", "2017")):
        tr, te = by[tr_y], by[te_y]
        cells = build_cells(tr)
        print("\n=== train %s n=%d, score %s n=%d, min cell 20 ===" % (tr_y, len(tr), te_y, len(te)))
        print("  %-30s %5s %7s %9s %10s   %s"
              % ("cells", "used", "avg n", "FITTED", "HELD-OUT", "against anchor + haul"))
        h = {}
        for s in SETS:
            hs, used, avg = hits(tr, te, s, cells)
            h[tuple(s)] = hs
            pct = 100.0 * sum(hs.values()) / len(hs)
            fit = fitted(tr, s, cells)
            tail = ""
            if s and s != ["haul"]:
                g, l, p = mcnemar(h[("haul",)], hs)
                tail = "+%-4d -%-4d p=%.3f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
            print("  %-30s %5d %7.1f %8.1f%% %9.1f%%   %s"
                  % (" x ".join(s) if s else "(anchor alone)", used, avg, fit, pct, tail))


if __name__ == "__main__":
    main()
