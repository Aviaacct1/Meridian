#!/usr/bin/env python3
"""Avia Solutions - verification of the departure-time optimiser, 11 August 2026.

Four things have to be true before this is safe to leave switched on, and each is checked rather
than assumed:

  1. A caller who names a departure time gets that time, and the QSI feed is scored against it.
  2. A caller who names an airline and no time gets a time chosen for that airline.
  3. Different airlines get different times, because connection strength is carrier-specific. If two
     carriers came back with the same answer the optimiser would not be doing what it claims.
  4. A route with no airline is untouched: the feed is carrier-specific and does not run without one.

It also prints the schedule the page now shows beside the departure times the same carriers actually
operate to Taipei from the west coast, because a schedule the market does not fly is the failure this
work exists to correct.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import duckdb                                    # noqa: E402
import cortex_app as CA                          # noqa: E402

ARGS = dict(carrier_type="FSC", aircraft="A359", seats=306, freq=4)


def run(label, **kw):
    r = CA.calibrated_forecast("SJC", "TPE", **dict(ARGS, **kw))
    if not r.get("ok"):
        print(f"{label}: FAILED {r.get('error')}")
        return None
    d, s = r["demand"], r["schedule"]
    print(f"{label}")
    print(f"  departure {s['outbound']['dep']}  arrival {s['outbound']['arr']}  ({s['basis']})")
    print(f"  beyond two-way {2 * d['feed_beyond']:>9,.0f}   behind two-way {2 * d['feed_behind']:>8,.0f}"
          f"   total two-way {2 * d['total']:>9,.0f}")
    return r


def main():
    # One part per process: the optimiser is a minute a carrier on a cold cache and the whole set
    # runs past the session cap. A run killed part way through is worse than four that each finish.
    part = sys.argv[1] if len(sys.argv) > 1 else "all"

    if part in ("all", "fixed"):
        print("=== 1. caller names the time: it must be honoured\n")
        run("  11:00, the old placeholder", dep_time_mins=660, airline="CI")
        run("  01:05, what China Airlines actually flies from SFO", dep_time_mins=65, airline="CI")

        print("\n=== 4. no airline: the feed does not run and nothing is optimised\n")
        r = CA.calibrated_forecast("SJC", "TPE", **ARGS)
        if r.get("ok"):
            d = r["demand"]
            print(f"  departure {r['schedule']['outbound']['dep']} ({r['schedule']['basis']}), "
                  f"beyond {d['feed_beyond']:,.0f}, behind {d['feed_behind']:,.0f}")

    if part in ("all", "opt") or part in ("CI", "BR", "UA"):
        print("\n=== 2 and 3. no time given: optimised, and carrier-specific\n")
        for al in (["CI", "BR", "UA"] if part in ("all", "opt") else [part]):
            run(f"  {al}, optimised", airline=al)

    if part not in ("all", "fixed", "opt"):
        return
    print("\n=== what these carriers actually fly to Taipei from the west coast\n")
    c = duckdb.connect(os.environ["AVIA_OAG"], read_only=True)
    w = c.execute("SELECT max(week) FROM oag").fetchone()[0]
    q = ("SELECT dep_airport, carrier, local_dep_time, local_arr_time FROM oag "
         "WHERE week=? AND arr_airport='TPE' AND dep_airport IN ('SFO','LAX') "
         "AND carrier IN ('CI','BR','UA') GROUP BY 1,2,3,4 ORDER BY 2,1,3")
    for dep_ap, car, dt, at in c.execute(q, [w]).fetchall():
        print(f"  {car} {dep_ap}-TPE  dep {str(dt).zfill(4)}  arr {str(at).zfill(4)}")
    c.close()


if __name__ == "__main__":
    main()
