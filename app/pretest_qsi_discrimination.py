#!/usr/bin/env python3
"""
Avia Cortex - Engine V2 discrimination pre-test: run BEFORE any wiring or 6-8h back-test.
==========================================================================================
The mct_bank lesson: the haircut fired but discriminated nothing (a near-uniform ~50% cut),
so it could not beat V1 whatever the calibration. This asks the same question of the QSI
feed in minutes, from the wave cache, before any run-time is spent:

  1. CROSS-ROUTE: at each launched route's ACTUAL flown departure time, compute the
     market-weighted mean QSI share of its onward markets (the route's quality index q).
     If q is near-uniform across routes, V2 cannot beat V1 - stop and rethink.
  2. CROSS-TIME: sweep each route's departure over the day. If the flown-vs-optimal gap is
     tiny everywhere, the dep-time lever is dead and Phase 4 face validity will fail.

Market weights: onward weekly frequency by default (self-contained); pass --sabre to weight
by the measured connecting market instead (better, needs the Sabre store).

RUN (John's machine, after wave_cache.py has built the cache):
  py -3.12 pretest_qsi_discrimination.py --cache qsi_wave_cache.duckdb --out pretest_qsi.csv
  py -3.12 pretest_qsi_discrimination.py --cache ... --sweep SJC,TPE,CI,825   (embargo eyeball)

READ-OUT: healthy discrimination looks like cross-route q spanning at least a few-fold
p90/p10 with CV > 0.4, and a material minority of routes showing optimum/flown > 1.2.
Near-uniform q (CV < 0.15) = the mct_bank failure mode; do not proceed to the back-test.
"""
import argparse
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import qsi_feed as QF
import mct_bank as MB
from wave_cache import CacheBoards


def route_quality(boards, route, mct, dep_override=None, cfg=None, min_onward_freq=3.0,
                  weights=None, sabre_db=None):
    """The route's quality index q = weighted mean QSI share over its onward markets at the
    given (or flown) departure time. Returns (q, n_markets, shares) or None if unusable.
    weights: {market: weight}; if None and sabre_db given, the measured connecting market;
    else onward weekly frequency."""
    fl = boards.flown(route["dep"], route["arr"], route["year"], route.get("carrier"))
    if not fl or fl.get("dep_mins") is None or not fl.get("flying"):
        return None
    hub_rows = boards.dep_rows(route["asif_week"], route["arr"])
    freq_by_m = {}
    for r in hub_rows:
        if r.get("arr") and r["arr"] != route["dep"]:
            freq_by_m[r["arr"]] = freq_by_m.get(r["arr"], 0.0) + (r.get("freq") or 0)
    markets = [m for m, f in freq_by_m.items() if f >= min_onward_freq
               and QF._circuity_ok(route["dep"], route["arr"], m,
                                   (cfg or {}).get("circuity", QF.DEFAULT_CIRCUITY))]
    if not markets:
        return None
    dep_mins = fl["dep_mins"] if dep_override is None else dep_override
    shares = QF.beyond_capture(boards, route["asif_week"], [route["dep"]], route["arr"],
                               markets, route.get("carrier"), dep_mins, fl["flying"],
                               fl.get("freq") or 7, mct=mct, cfg=cfg)
    if weights is None and sabre_db:
        try:
            weights = sabre_weights(sabre_db, route, markets)
        except Exception:
            weights = None
    w = weights or freq_by_m
    tw = sum(w.get(m, 0.0) for m in markets)
    if tw <= 0:
        return None
    q = sum(shares[m] * w.get(m, 0.0) for m in markets) / tw
    return q, len(markets), shares


def _stats(xs):
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if not n:
        return {}
    mean = sum(xs) / n
    sd = (sum((x - mean) ** 2 for x in xs) / n) ** 0.5
    pc = lambda p: xs[min(n - 1, int(p * n))]
    return {"n": n, "mean": mean, "cv": (sd / mean if mean else 0.0),
            "p10": pc(0.10), "p50": pc(0.50), "p90": pc(0.90)}


def sabre_weights(sabre_db, route, markets, factor_indirect=1.044):
    """Measured connecting market per onward airport (the proper weights), from Sabre."""
    from route_feed import connecting_market
    return connecting_market(sabre_db, [route["dep"]], markets, route["year"] - 1,
                             factor_indirect)


def main():
    ap = argparse.ArgumentParser(description="Engine V2 discrimination pre-test (fast, no back-test).")
    ap.add_argument("--cache", default=os.path.join(HERE, "qsi_wave_cache.duckdb"))
    ap.add_argument("--sabre", default=None, help="optional Sabre store for market weights")
    ap.add_argument("--baseline", default=None,
                    help="optional bt_v1_baseline.csv - restricts to its hub-destination routes")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--step", type=int, default=120, help="dep-time sweep grid (minutes)")
    ap.add_argument("--out", default=os.path.join(HERE, "pretest_qsi.csv"))
    ap.add_argument("--sweep", default=None,
                    help="one-off dep sweep 'ORIGIN,HUB,CARRIER,FLYMIN' (e.g. SJC,TPE,CI,825); "
                         "uses the newest cached week for the hub")
    a = ap.parse_args()

    boards = CacheBoards(a.cache)
    mct = MB.load_mct()

    if a.sweep:
        org, hub, car, fly = a.sweep.split(",")
        weeks = sorted({r["asif_week"] for r in boards.routes()})
        week = weeks[-1]
        rows = boards.dep_rows(week, hub)
        markets = sorted({r["arr"] for r in rows if r.get("arr") and r["arr"] != org})
        print(f"SWEEP {org}->{hub} ({car}, {fly} min) week {week}: {len(markets)} onward markets")
        for dep in range(0, 1440, 60):
            shares = QF.beyond_capture(boards, week, [org], hub, markets, car,
                                       dep, int(fly), 7, mct=mct)
            wtot = qtot = 0.0
            for m in markets:
                f = sum(r.get("freq") or 0 for r in rows if r.get("arr") == m)
                qtot += shares.get(m, 0.0) * f
                wtot += f
            arr = (dep + int(fly)) % 1440
            print(f"  dep {dep // 60:02d}:{dep % 60:02d} arr {arr // 60:02d}:{arr % 60:02d}"
                  f"  q {qtot / wtot if wtot else 0.0:.4f}")
        return

    hub_filter = None
    if a.baseline and os.path.exists(a.baseline):
        hub_filter = set()
        with open(a.baseline, newline="") as fh:
            for r in csv.DictReader(fh):
                if str(r.get("hub_dest", "")).strip().lower() in ("true", "1"):
                    hub_filter.add(r["route"])

    routes = boards.routes()
    if a.limit:
        routes = routes[:a.limit]
    out_rows = []
    for i, rt in enumerate(routes):
        label = f"{rt['dep']}-{rt['arr']}"
        if hub_filter is not None and label not in hub_filter and \
                f"{label}-{rt.get('carrier', '')}" not in hub_filter:
            continue
        base = route_quality(boards, rt, mct, sabre_db=a.sabre)
        if base is None:
            continue
        q_flown, n_mkts, _ = base
        q_best, best_dep = q_flown, None
        for dep in range(0, 1440, a.step):
            r2 = route_quality(boards, rt, mct, dep_override=dep, sabre_db=a.sabre)
            if r2 and r2[0] > q_best:
                q_best, best_dep = r2[0], dep
        out_rows.append({"route": label, "carrier": rt.get("carrier"), "year": rt["year"],
                         "n_markets": n_mkts, "q_flown": round(q_flown, 5),
                         "q_best": round(q_best, 5),
                         "opt_over_flown": round(q_best / q_flown, 3) if q_flown else "",
                         "best_dep": best_dep})
        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1}/{len(routes)}")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()) if out_rows else
                           ["route"])
        w.writeheader()
        w.writerows(out_rows)

    qs = [r["q_flown"] for r in out_rows]
    ratios = [r["opt_over_flown"] for r in out_rows if r["opt_over_flown"] != ""]
    s = _stats(qs)
    print(f"\nroutes scored: {len(out_rows)}  ->  {a.out}")
    if s:
        print(f"CROSS-ROUTE q_flown: mean {s['mean']:.4f}  CV {s['cv']:.2f}  "
              f"p10 {s['p10']:.4f}  p50 {s['p50']:.4f}  p90 {s['p90']:.4f}  "
              f"(p90/p10 {s['p90'] / s['p10']:.1f}x)" if s.get("p10") else "")
        lift = sum(1 for r in ratios if r and float(r) > 1.2)
        print(f"CROSS-TIME: {lift}/{len(ratios)} routes with optimum/flown > 1.2")
        verdict = "DISCRIMINATES - proceed to wiring + calibration" \
            if s["cv"] > 0.4 else ("NEAR-UNIFORM - the mct_bank failure mode, stop and rethink"
                                   if s["cv"] < 0.15 else "MARGINAL - inspect the spread by slice")
        print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
