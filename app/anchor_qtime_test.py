#!/usr/bin/env python3
r"""Departure-time quality as a cell on the capacity anchor. Kickoff section 4.1, properly powered.

    python3 anchor_qtime_test.py bt_v1_baseline.csv pretest_qsi_08Aug2026.csv

WHY HERE AND NOT ON BT2. The pretest was computed on the QSI engine's 8 August back-test route set,
and BT2's launch set is a different selection, so only 607 of BT2's 3,700 launches carry a q and
that test is underpowered. The pretest joins to bt_v1_baseline.csv on 2,399 of 2,830 rows, which is
where the question can actually be answered, and it is where the kickoff said to put it.

NOT THE SAME QUESTION AS THE A/B OF 8 AUGUST. That asked whether the wave-timed feed improves the
structural engine, and it did not. This asks whether q predicts O&D-per-seat on top of a capacity
anchor. The prior is weak: connecting share as a cell scores 40.7% held-out against 43.6% for no
features, so the nearest proxy is a mild negative, though feed share is not departure-time quality.

Held-out in both split directions, with the paired test, because a feature ranking read off a
single split and a difference of one percentage point is a ranking read off noise.

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


def feed_share(r):
    cap = _f(r.get("capacity")) or 0
    fb = (_f(r.get("feed_beyond")) or 0) + (_f(r.get("feed_behind")) or 0)
    if not cap:
        return "?"
    s = fb / cap
    return "feed<1%" if s < 0.01 else "feed1-5%" if s < 0.05 else "feed5-15%" if s < 0.15 else "feed>15%"


def quartiles(vals):
    v = sorted(vals)
    return [v[int(len(v) * q)] for q in (0.25, 0.50, 0.75)] if len(v) >= 8 else []


def banded(x, edges, prefix):
    if x is None:
        return prefix + ":none"
    for i, e in enumerate(edges):
        if x < e:
            return "%s:q%d" % (prefix, i + 1)
    return "%s:q%d" % (prefix, len(edges) + 1)


def build_cells(train):
    qe = quartiles([r["_q"] for r in train if r["_q"]])
    oe = quartiles([r["_opt"] for r in train if r["_opt"]])
    ne = quartiles([r["_nm"] for r in train if r["_nm"]])
    return {
        "haul": haul,
        "type": lambda r: r.get("type"),
        "feed": feed_share,
        "q": lambda r: banded(r["_q"], qe, "q"),
        "opt": lambda r: banded(r["_opt"], oe, "opt"),
        "nmkt": lambda r: banded(r["_nm"], ne, "nm"),
        # Time of day in four blocks. A cyclical variable put through quartile edges would cut the
        # day at whatever the training set happened to contain, so the blocks are named, not fitted.
        "dep": lambda r: ("dep:none" if r["_dep"] is None else
                          "dep:early" if r["_dep"] < 480 else
                          "dep:am" if r["_dep"] < 720 else
                          "dep:pm" if r["_dep"] < 1020 else "dep:eve"),
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


def mcnemar(a, b):
    ks = set(a) & set(b)
    n01 = sum(1 for k in ks if not a[k] and b[k])
    n10 = sum(1 for k in ks if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return 0, 0, 1.0
    lo = min(n01, n10)
    return n01, n10, min(1.0, 2.0 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


SETS = [[], ["haul"], ["haul", "feed"],
        ["q"], ["haul", "q"], ["type", "haul", "q"],
        ["opt"], ["haul", "opt"], ["dep"], ["haul", "dep"], ["nmkt"], ["haul", "nmkt"]]


def main():
    q = {}
    for r in csv.DictReader(open(sys.argv[2], newline="", encoding="utf-8-sig")):
        p = (r["route"] or "").split("-")
        if len(p) == 2:
            q[(tuple(sorted(p)), r["year"])] = r

    ok = []
    for r in csv.DictReader(open(sys.argv[1], newline="", encoding="utf-8-sig")):
        if not (_f(r.get("capacity")) and _f(r.get("outturn_pax")) and _f(r.get("forecast_pax"))):
            continue
        p = (r["route"] or "").split("-")
        c = q.get((tuple(sorted(p)), r["year"])) if len(p) == 2 else None
        r["_q"] = _f(c.get("q_flown")) if c else None
        r["_opt"] = _f(c.get("opt_over_flown")) if c else None
        r["_nm"] = _f(c.get("n_markets")) if c else None
        try:
            r["_dep"] = float(c["best_dep"]) if c and c.get("best_dep") else None
        except ValueError:
            r["_dep"] = None
        ok.append(r)

    have = sum(1 for r in ok if r["_q"])
    print("usable rows %d, with a departure-time q %d (%.1f%%)"
          % (len(ok), have, 100.0 * have / len(ok)))

    by = {y: [r for r in ok if str(r.get("year")) == y] for y in ("2017", "2018")}
    for tr_y, te_y in (("2017", "2018"), ("2018", "2017")):
        tr, te = by[tr_y], by[te_y]
        cells = build_cells(tr)
        print("\n=== train %s n=%d, score %s n=%d, min cell 20 ===" % (tr_y, len(tr), te_y, len(te)))
        print("  %-26s %5s %7s %10s   %s" % ("cells", "used", "avg n", "HELD-OUT",
                                             "against anchor + haul"))
        h = {}
        for s in SETS:
            hs, used, avg = hits(tr, te, s, cells)
            h[tuple(s)] = hs
            tail = ""
            if s and s != ["haul"]:
                g, l, p = mcnemar(h[("haul",)], hs)
                tail = "+%-4d -%-4d p=%.3f%s" % (g, l, p, "" if p < 0.05 else "  NOT MEASURABLE")
            print("  %-26s %5d %7.1f %9.1f%%   %s"
                  % (" x ".join(s) if s else "(anchor alone)", used, avg,
                     100.0 * sum(hs.values()) / len(hs), tail))


if __name__ == "__main__":
    main()
