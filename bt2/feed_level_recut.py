"""What level would the connecting feed need, and does one level fit every route?

THE QUESTION. BOARDS-ARE-IDENTICAL of 13 August closed the confound: CacheBoards and OagBoards
return the same qshare on every one of 40 pin routes, median 1.000 with min and max also 1.000, so
qsi_k is directly comparable across the back-test and the live path. The back-test ran k=0.06 and
the shipped path runs k=1.0, and route_feed line 261 is captured = pax x k x qshare, so the two
differ by a factor of 16.67 in one quantity rather than in two incomparable ones.

That leaves two measurements standing against each other. LEVEL-VS-SHAPE has the arm at k=0.06
needing x1.62 to reach actual connecting, which re-levels to an over-read of circa 10x at k=1.0.
FEED-LEVELS has the live path at k=1.0 reading 0.93x of the 2025 analyst on SJC-TPE. Both are real.
FLOOR-EVIDENCED offers the shape that might reconcile them: Sabre under-counts transfer traffic by
2.07x on routes touching a major Asian hub and 2.50x on long haul over 6,000km, and SJC-TPE is both.

SO THIS ASKS WHETHER THE OVER-READ HAS THAT SHAPE. It reports, per cut, the multiplier the feed
still needs and the k that would reach outturn. If the required k rises towards 1.0 on long-haul and
Asian-hub routes and sits near 0.06 on short-haul European ones, the shipped level is right for the
case it was tuned on and wrong elsewhere, and one global k is the wrong instrument. If the required
k is flat and low everywhere, the shipped level is simply too high and SJC-TPE agrees with the
analyst for some other reason.

IT COSTS NO RUN. k is a pure multiplier, so every figure here is arithmetic on the arm CSV that is
already written. No engine, no store scan, no refit.

WHAT IT CANNOT SAY, and this is the basis caveat that belongs beside every number it prints. The arm
built its feed at the route's ACTUAL FLOWN departure time, block and frequency from the pin wave
cache. The live path builds it at the time the optimiser picks, which maximises connecting
passengers, with a modelled block from GCD and the requested frequency. So this measures what the
ARM's feed would read at k=1.0. It does not measure the live path's feed, and the optimiser's choice
biases the live figure upward by construction. Read it as the shape of the error, not as the level
the portal produces.

Grading quantity: actual connecting is outturn_pax less p2p_outturn, which RULER-SOUND checked on
3,072 routes, zero of them negative and 635 exactly zero. Those 635 carry no connecting traffic and
are reported separately rather than averaged in, because a ratio against zero is not a number.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import math
import os
import statistics
import sys


# Routes touching one of these as the destination are the case FLOOR-EVIDENCED measured at 2.07x.
# Named here rather than inferred from a region code, because "Asia" in the OAG partitioning covers
# Almaty and Auckland as readily as Singapore, and the finding was about big transfer hubs.
ASIAN_HUBS = {"HKG", "SIN", "ICN", "NRT", "HND", "TPE", "BKK", "KUL", "PVG", "PEK", "PKX",
              "CAN", "DOH", "DXB", "AUH", "IST", "DEL", "BOM", "CGK", "MNL", "SGN", "HAN"}


def parse_args():
    p = argparse.ArgumentParser(description="Re-level the arm's connecting feed and cut the error.")
    p.add_argument("--arm", required=True, help="a backtest.py arm CSV run with --qsi-feed")
    p.add_argument("--k-arm", type=float, default=0.06, help="the level the arm ran, default 0.06")
    p.add_argument("--k-live", type=float, default=1.0, help="the shipped level, default 1.0")
    p.add_argument("--band", type=float, default=0.20, help="the accuracy band, default +-20%%")
    p.add_argument("--out", default=None, help="write the per-route rows to this CSV")
    return p.parse_args()


def _f(row, name):
    try:
        return float(row.get(name) or 0)
    except (TypeError, ValueError):
        return 0.0


def _pct(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    return v[min(int(q * (len(v) - 1) + 0.5), len(v) - 1)]


def _cut(rows, name, key):
    """One cut of the population. Returns rows of (label, n, median ratio, IQR, implied k, in band)."""
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    out = []
    for label in sorted(groups, key=lambda x: str(x)):
        g = groups[label]
        ratios = [r["_ratio"] for r in g]
        med = statistics.median(ratios)
        lo, hi = _pct(ratios, 0.25), _pct(ratios, 0.75)
        # The k that would put the median route on the nose. k scales the feed linearly and the
        # ratio is actual over feed, so the level that reaches outturn is the live k times the
        # median shortfall. A median ratio of 1.0 means the level is already right for this cut.
        k_needed = None
        if med:
            k_needed = g[0]["_k_live"] * med
        hit = sum(1 for x in ratios if abs(x - 1.0) <= g[0]["_band"])
        out.append((label, len(g), med, (lo, hi), k_needed, 100.0 * hit / len(g)))
    print("\n%s" % name)
    print("   %-22s %6s %9s %19s %9s %8s"
          % ("cut", "n", "median", "IQR of actual/feed", "k needed", "in band"))
    for label, n, med, (lo, hi), k, pc in out:
        print("   %-22s %6d %9.3f %8.3f to %8.3f %9.3f %7.1f%%"
              % (str(label), n, med, lo, hi, (k if k is not None else float("nan")), pc))
    return out


def main():
    a = parse_args()
    if not os.path.exists(a.arm):
        sys.exit("arm CSV not found: %r" % a.arm)

    with open(a.arm, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    rows, skip = [], {"no_connecting_traffic": 0, "feed_is_zero": 0, "negative_actual": 0}
    scale = a.k_live / a.k_arm
    for r in raw:
        actual = _f(r, "outturn_pax") - _f(r, "p2p_outturn")
        feed_arm = _f(r, "feed_beyond") + _f(r, "feed_behind")
        if actual < 0:
            skip["negative_actual"] += 1
            continue
        if actual == 0:
            # RULER-SOUND: 635 of 3,072 routes carry no connecting traffic at all. Legitimate, and
            # not a ratio. Counted, never averaged in.
            skip["no_connecting_traffic"] += 1
            continue
        if feed_arm <= 0:
            # P2P_CARRIERS are zeroed by feed_side before any level is applied, so these say nothing
            # about the level and everything about the carrier list.
            skip["feed_is_zero"] += 1
            continue
        feed_live = feed_arm * scale
        r["_actual"] = actual
        r["_feed_live"] = feed_live
        r["_ratio"] = actual / feed_live
        r["_k_live"] = a.k_live
        r["_band"] = a.band
        rows.append(r)

    print("arm %s" % os.path.basename(a.arm))
    print("re-levelled from k=%.4f to k=%.4f, a factor of %.2f on every feed figure"
          % (a.k_arm, a.k_live, scale))
    print("%d rows read, %d scored | skipped: %s"
          % (len(raw), len(rows), ", ".join("%s=%d" % kv for kv in sorted(skip.items()) if kv[1])))
    if not rows:
        sys.exit("nothing to score.")

    print("\nRATIO IS ACTUAL CONNECTING OVER THE FEED AT THE SHIPPED LEVEL.")
    print("  above 1.0 the feed still UNDER-reads; below 1.0 it OVER-reads.")
    print("  'k needed' is the level that would put the median route of that cut on the nose.")

    all_ratios = [r["_ratio"] for r in rows]
    print("\nALL ROUTES  n=%d  median %.3f  IQR %.3f to %.3f  k needed %.3f"
          % (len(rows), statistics.median(all_ratios), _pct(all_ratios, 0.25),
             _pct(all_ratios, 0.75), a.k_live * statistics.median(all_ratios)))

    def haul(r):
        g = _f(r, "gcd_km")
        return ("1 under 1500km" if g < 1500 else "2 1500-3000" if g < 3000 else
                "3 3000-6000" if g < 6000 else "4 over 6000km")

    _cut(rows, "BY HAUL. FLOOR-EVIDENCED measured 2.50x on long haul over 6,000km.", haul)
    _cut(rows, "BY ASIAN OR GULF HUB DESTINATION. FLOOR-EVIDENCED measured 2.07x on these.",
         lambda r: "hub: %s" % ("yes" if str(r.get("arr", "")).strip().upper() in ASIAN_HUBS
                                else "no"))
    _cut(rows, "BY THE ARM'S OWN hub_dest FLAG, which is a different question from the list above.",
         lambda r: "hub_dest %s" % str(r.get("hub_dest")).strip().lower())
    # THE SJC-TPE CELL. The single cuts each move the level the right way and neither reaches the
    # shipped 1.0, so the question is whether the two together do. SJC-TPE is 10,440km into Taipei,
    # long haul AND an Asian hub, and it is the one route where the live feed at k=1.0 has an
    # independent human comparator. If this cell approaches 1.0 the conflict between the back-test
    # and FEED-LEVELS resolves as a population difference. If it sits with the rest, SJC-TPE agrees
    # with the analyst for a reason that is not the feed level and the agreement carries no weight.
    _cut(rows, "LONG HAUL AND HUB TOGETHER. This is the SJC-TPE cell.",
         lambda r: "%s / %s" % ("over 6000km" if _f(r, "gcd_km") >= 6000 else "under 6000km",
                                "hub" if str(r.get("arr", "")).strip().upper() in ASIAN_HUBS
                                else "not a hub"))
    _cut(rows, "BY CARRIER TYPE.", lambda r: str(r.get("type") or "unknown"))
    _cut(rows, "BY REGION, as the store partitions it.", lambda r: str(r.get("region") or "unknown"))
    _cut(rows, "BY COHORT, to see whether the level drifts with the schedule vintage.",
         lambda r: str(r.get("year") or "unknown"))

    print("\nHOW TO READ THIS. If 'k needed' climbs towards 1.0 on long haul and on the hub list")
    print("while sitting near %.2f on short haul, the shipped level is right for the case it was" % a.k_arm)
    print("tuned on and wrong elsewhere, and ONE GLOBAL k is the wrong instrument. If it is flat")
    print("and low everywhere, the shipped level is too high and the SJC-TPE agreement with the")
    print("analyst needs another explanation. The IQR decides how much either reading is worth:")
    print("FEED-IS-UNINFORMATIVE recorded an IQR of 2.666 in logs, a factor of fourteen across the")
    print("middle half of routes, and a level cannot fix a spread.")

    if a.out:
        cols = ["route", "dep", "arr", "year", "carrier", "type", "region", "gcd_km", "hub_dest",
                "p2p_outturn", "outturn_pax", "feed_beyond", "feed_behind"]
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols + ["actual_connecting", "feed_at_live_k", "actual_over_feed"])
            for r in rows:
                w.writerow([r.get(c, "") for c in cols]
                           + [round(r["_actual"]), round(r["_feed_live"]), round(r["_ratio"], 4)])
        print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
