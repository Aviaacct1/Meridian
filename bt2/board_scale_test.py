"""Is qshare on one scale across the back-test path and the live path?

THE QUESTION, and why it is not the one asked yesterday. route_feed line 261 is
captured = pax x k x qshare, so k is a straight multiplier on the connecting capture. The
back-test runs k=0.06 and the live path runs k=1.0, and on 13 August that difference was
read as a level fault. It is not. FEED-LEVELS of 11 August measured the live path at k=1.0
against the 2025 analyst before split_share: connecting 24,080 two-way against his 25,999,
which is 0.93x, and ANALYST-LEG-MATCH and the frequency ladder agree with him to within
seven per cent on the same setting. A live level ten times too high cannot produce that.

So each k is calibrated to its own qshare and the two qshare figures are on different
scales. THIS SCRIPT MEASURES THAT SCALE, which is the only thing that makes the two k
values comparable, and which decides what a back-test of the shipped feed would even mean.

WHAT IT DOES. It calls route_feed.feed_side twice on the same route with every argument
identical except the boards object: CacheBoards on the pin wave cache, which is what every
arm of 11 and 12 August read, against OagBoards on the live OAG store, which is what the
portal reads. feed_side builds its own market from Sabre and OAG, so market, week,
departure time, block, frequency, airline and the alliance weights are common to both and
the ratio of the two totals IS the ratio of the pax-weighted qshare. Nothing is
reimplemented: it is the shipped function, called twice.

k IS HELD AT 1.0 IN BOTH CALLS. Running one path at two values of k returns their ratio by
construction, which is arithmetic rather than a measurement. That trap is what this script
exists to avoid, and setting k differently between the two calls would walk straight back
into it.

HOW TO READ IT. If the median ratio comes back near 16.67, the cache and the store return
qshare on scales that differ by the same factor as the two k values, so the two levels are
calibrated to one underlying quantity and are consistent rather than in conflict. If it
comes back near 1.0, the boards agree, and a factor of 16.67 between the two k values is
real and unexplained, which is a worse finding and a different piece of work. Anything in
between is the honest answer and the distribution matters more than the median, so every
route is written out.

The board counts beside each route are there so a difference in qshare has a named cause
rather than an inferred one: the cache holds sliced weeks for the pinned routes and the
store holds everything, so a thinner board is the first thing to check.

WHAT IT DOES NOT DO. It runs no forecast and grades nothing against outturn. It does not
test whether the shipped feed is accurate, which needs an arm run at the live
configuration and is not attempted here. Routes whose operating carrier is in
P2P_CARRIERS return zero from feed_side on both sides by design and are counted and
skipped, not scored.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)


def parse_args():
    p = argparse.ArgumentParser(description="Compare qshare across CacheBoards and OagBoards.")
    p.add_argument("--cache", required=True, help="the pin wave cache, e.g. qsi_wave_cache_pin_12Aug2026.duckdb")
    p.add_argument("--oag", default=os.environ.get("AVIA_OAG"), help="the live OAG store")
    p.add_argument("--sabre", default=os.environ.get("AVIA_SABRE"), help="the Sabre store")
    p.add_argument("--n", type=int, default=40, help="routes to sample, default 40")
    p.add_argument("--seed", type=int, default=13, help="sample seed, so a rerun is the same sample")
    p.add_argument("--side", choices=("beyond", "behind", "both"), default="beyond")
    p.add_argument("--out", default=None, help="write the per-route rows to this CSV")
    return p.parse_args()


def _pct(vals, q):
    """A percentile with no numpy. vals must be sorted and non-empty."""
    if not vals:
        return None
    i = min(int(q * (len(vals) - 1) + 0.5), len(vals) - 1)
    return vals[i]


def main():
    a = parse_args()
    for name, path in (("--cache", a.cache), ("--oag", a.oag), ("--sabre", a.sabre)):
        if not path or not os.path.exists(path):
            sys.exit(f"{name} not found: {path!r}. Set AVIA_OAG and AVIA_SABRE, or pass the paths.")

    import route_engine as RE
    import route_feed as RF
    import route_forecast as RFC
    from wave_cache import CacheBoards, OagBoards

    cache = CacheBoards(a.cache)
    store = OagBoards(a.oag)
    airports = RE._airports()

    routes = cache.routes()
    random.Random(a.seed).shuffle(routes)

    print(f"cache {os.path.basename(a.cache)}: {len(routes)} routes, sampling {a.n} at seed {a.seed}")
    print("k is held at 1.0 in BOTH calls. Only the boards object differs.\n")

    rows, skipped = [], {"no_flown": 0, "p2p_carrier": 0, "no_coords": 0, "zero_both": 0, "error": 0}
    for r in routes:
        if len(rows) >= a.n:
            break
        dep, arr, year, carrier = r["dep"], r["arr"], int(r["year"]), (r["carrier"] or "")
        week = r.get("asif_week")
        if not week:
            skipped["no_flown"] += 1
            continue
        if carrier.upper() in RF.P2P_CARRIERS:
            # feed_side returns zero for these on both sides by design, so there is no ratio to read.
            skipped["p2p_carrier"] += 1
            continue
        fl = cache.flown(dep, arr, year, carrier)
        if not fl or fl.get("dep_mins") is None:
            skipped["no_flown"] += 1
            continue
        o, d = airports.get(dep), airports.get(arr)
        if not o or not d:
            skipped["no_coords"] += 1
            continue

        # The catchment is built the way backtest.py line 428 builds it, so a route here and the
        # same route in an arm carry the same origin set. It is identical across the two calls in
        # any case, so it cannot move the ratio; it is matched so the LEVELS are readable too.
        gcd = RE.gc_km(o["lat"], o["lon"], d["lat"], d["lon"])
        rad = RFC.haul_radius_km(gcd) if gcd else 220.0
        origins = [x["iata"] for x in RE.competing_airports(o, rad, None, True)]

        base = dict(behind_cap=0.10, dom_gain=1.0, dom_floor=1.0,
                    cnx_online=1.0, cnx_alliance=0.615, cnx_interline=0.25,
                    circuity=1.35, factor_indirect=1.044, mct_banking=False,
                    qsi_feed=True, dep_time_mins=fl["dep_mins"],
                    flying_mins=fl.get("flying") or 540, route_freq=fl.get("freq") or 7,
                    route_origin=dep, qsi_k=1.0)

        # EACH SIDE THROUGH THE FUNCTION THE ENGINE ACTUALLY USES. feed_side takes a beyond=False
        # argument and nothing calls it: route_forecast line 608 and every diagnostic in bt2 send
        # the behind side to behind_feed, which takes [origin] and [dest] rather than a catchment
        # and a hub. Reading the behind side off feed_side(beyond=False) would exercise a path the
        # engine does not run and return a number nobody could hold against anything.
        def one(boards, beyond):
            cfg = dict(base)
            cfg["_boards"] = boards          # the ONLY difference between the two calls
            if beyond:
                total, _ = RF.feed_side(a.sabre, a.oag, week, origins, arr, year,
                                        beyond=True, airline=(carrier or None), feed_cfg=cfg)
            else:
                total, _ = RF.behind_feed(a.sabre, a.oag, week, [dep], [arr], year,
                                          airline=(carrier or None), feed_cfg=cfg)
            return float(total or 0.0), cfg

        try:
            row = {"route": f"{dep}-{arr}", "year": year, "carrier": carrier, "week": week,
                   "dep_mins": fl["dep_mins"], "freq": fl.get("freq"), "gcd_km": round(gcd)}
            for side, beyond in (("beyond", True), ("behind", False)):
                if a.side not in (side, "both"):
                    continue
                c_tot, c_cfg = one(cache, beyond)
                s_tot, s_cfg = one(store, beyond)
                row[f"{side}_cache"] = round(c_tot, 1)
                row[f"{side}_store"] = round(s_tot, 1)
                # store over cache: the factor the LIVE path's qshare runs above the arm's.
                row[f"{side}_ratio"] = round(s_tot / c_tot, 4) if c_tot > 0 else None
                # A fallback inside feed_side means the QSI branch threw and the flat feed answered,
                # which is not a qshare reading at all. Counted rather than averaged into the result.
                row[f"{side}_fallback"] = int(bool(c_cfg.get("_qsi_fallbacks")
                                                   or s_cfg.get("_qsi_fallbacks")))
            # Board coverage at the hub for the same week, so a ratio has a named cause.
            row["hub_legs_cache"] = len(cache.dep_rows(week, arr))
            row["hub_legs_store"] = len(store.dep_rows(week, arr))
            row["hub_freq_cache"] = round(sum(x.get("freq") or 0 for x in cache.dep_rows(week, arr)), 1)
            row["hub_freq_store"] = round(sum(x.get("freq") or 0 for x in store.dep_rows(week, arr)), 1)
        except Exception as exc:
            skipped["error"] += 1
            print(f"  {dep}-{arr} {year}: {type(exc).__name__} {exc}")
            continue

        if not any(row.get(f"{s}_cache") or row.get(f"{s}_store") for s in ("beyond", "behind")):
            skipped["zero_both"] += 1
            continue
        rows.append(row)
        print(f"  {row['route']} {year} {carrier:<3} "
              + "  ".join(f"{s}: cache {row.get(s + '_cache')} store {row.get(s + '_store')} "
                          f"x{row.get(s + '_ratio')}"
                          for s in ("beyond", "behind") if f"{s}_ratio" in row))

    print(f"\nscored {len(rows)} routes | skipped: "
          + ", ".join(f"{k}={v}" for k, v in sorted(skipped.items()) if v))

    for side in ("beyond", "behind"):
        vals = sorted(x[f"{side}_ratio"] for x in rows
                      if x.get(f"{side}_ratio") and not x.get(f"{side}_fallback"))
        if not vals:
            continue
        print(f"\n{side.upper()}, store over cache, n={len(vals)}")
        print(f"  median {statistics.median(vals):.3f}  p25 {_pct(vals, 0.25):.3f}  "
              f"p75 {_pct(vals, 0.75):.3f}  min {vals[0]:.3f}  max {vals[-1]:.3f}")
        print("  16.67 would mean the two k values are calibrated to one quantity on two scales.")
        print("  1.00 would mean the boards agree and the k difference is real and unexplained.")

    cl = [x["hub_legs_cache"] for x in rows if x.get("hub_legs_store")]
    st = [x["hub_legs_store"] for x in rows if x.get("hub_legs_store")]
    if cl:
        print(f"\nHUB DEPARTURE BOARD, distinct legs after dedupe, same week both readers")
        print(f"  cache median {statistics.median(cl):.0f}, store median {statistics.median(st):.0f}")
        print("  A thinner cache board is the first candidate cause of any ratio above 1.")

    if a.out and rows:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {a.out}")

    cache.close()
    store.close()


if __name__ == "__main__":
    main()
