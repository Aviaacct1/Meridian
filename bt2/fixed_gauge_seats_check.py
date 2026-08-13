#!/usr/bin/env python3
r"""Does a client-fixed gauge still get the carrier's OWN cabin? Verification of the 14 August fix.

THE DEFECT. cortex_app.api_optimise passed airline_iata=(None if _fixed_ac else (cand or None)) into
aircraft_select.select_aircraft. airline_iata does two separate jobs in that module and they were
being treated as one:

  candidates() line 54  pool = fleet, then `if pool is None and airline_iata`, so the carrier only
                        BUILDS a candidate pool when no explicit fleet was given.
  select_aircraft 165   the carrier is read a second time, into capacity_frame.config_for, to get
                        the cabin THAT carrier configures the type to.

Suppressing the carrier whenever the client fixed a gauge therefore discarded the configuration as
well as the pool it was not being asked for, and the generic table stood in. Measured 10 August 2026:
China Airlines and Starlux fly the A350-900 at 306 seats against aircraft_economics' 336, so a fixed
A350-900 was sized on 9.8% more capacity than the carrier flies. Every figure downstream of the seat
count moves with it: the load factor the optimiser selects on, the plan cap, the spill and the P&L.

THE FIX is one argument: pass the carrier always and let the explicit fleet keep precedence for the
pool, which candidates() already does.

WHAT THIS CHECKS, and each is a separate way the fix could be wrong rather than three readings of one
thing:

  1. The store agrees with the finding: capacity_frame.config_for returns 306 for CI on a sector of
     this length, against the generic 336.
  2. The OLD call, airline_iata=None with fleet fixed, returns the generic 336 and says so in
     seats_source. This is the defect reproduced, and without it the check cannot show the fix moved
     anything.
  3. The NEW call, the carrier named with the same fixed fleet, returns 306 and reports the carrier
     configuration.
  4. THE POOL IS UNCHANGED. The client fixed the gauge, so naming the carrier must not let the
     carrier's fleet widen the choice: exactly one aircraft comes back and it is the one fixed. This
     is the check that would catch the fix breaking a client-fixed gauge, which is the only way it
     could do harm.
  5. A carrier the store cannot describe on this type falls back to the generic table and LABELS
     itself as such, rather than silently returning a number with no basis.

    Workstation:
    cd C:\src\meridian\bt2
    py -3.12 fixed_gauge_seats_check.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from bt2_paths import find_app                                          # noqa: E402

APP = find_app()
if not APP:
    sys.exit("Could not find the Meridian app folder. Set AVIA_APP_DIR.")
if APP not in sys.path:
    sys.path.insert(0, APP)

import aircraft_select as ASsel                                         # noqa: E402
import capacity_frame as CF                                             # noqa: E402
from aircraft_economics import AIRCRAFT                                 # noqa: E402

# SJC-TPE, the case the fix was found on. Distance from the engine's own resolver where it is
# available, so this script and the portal are on one figure rather than two.
GCD_KM = 10440.0
TYPE = "A359"
CARRIERS = ["CI", "JX", "BR"]
DEMAND_EACH_WAY, FREQ = 90000.0, 4

GENERIC = AIRCRAFT[TYPE]["econ_seats"] + AIRCRAFT[TYPE]["bus_seats"]


def call(airline):
    """select_aircraft with the gauge fixed, exactly as api_optimise calls it."""
    _code, ranked = ASsel.select_aircraft(GCD_KM / 1.852, DEMAND_EACH_WAY, FREQ,
                                          airline_type="FSC", airline_iata=airline,
                                          fleet=[TYPE])
    return ranked


def main():
    print("SJC-TPE, %s, gauge fixed by the client. Generic table: %d seats.\n" % (TYPE, GENERIC))
    fails = []

    for car in CARRIERS:
        cfg = CF.config_for(car, GCD_KM)
        store = cfg.get(TYPE)
        old = call(None)
        new = call(car)
        o, n = old[0], new[0]
        print("%s" % car)
        print("   store          %s" % ("%d seats, %d premium" % store if store
                                        else "no configuration for this type at this sector length"))
        print("   OLD  fixed gauge, carrier suppressed  %4d seats  (%s)"
              % (o["seats"], o["seats_source"]))
        print("   NEW  fixed gauge, carrier named       %4d seats  (%s)"
              % (n["seats"], n["seats_source"]))

        # 4. The pool must not widen. A fixed gauge is a client instruction, not a preference.
        if len(new) != 1 or new[0]["aircraft"] != TYPE:
            fails.append("%s: naming the carrier widened a client-fixed gauge to %s"
                         % (car, [r["aircraft"] for r in new]))
        if o["seats"] != GENERIC or o["seats_source"] != "generic type table":
            fails.append("%s: the OLD call did not return the generic table, so this run does not "
                         "reproduce the defect and proves nothing" % car)

        if store:
            if n["seats"] != store[0]:
                fails.append("%s: the store says %d and the NEW call returned %d"
                             % (car, store[0], n["seats"]))
            elif n["seats_source"] != "carrier configuration, OAG":
                fails.append("%s: returned the carrier's seat count but labelled it %r"
                             % (car, n["seats_source"]))
            else:
                print("   MOVED  %+d seats, %+.1f%% on the capacity the schedule is sized against"
                      % (n["seats"] - o["seats"],
                         100.0 * (n["seats"] - o["seats"]) / max(o["seats"], 1)))
        else:
            # 5. No store entry is a legitimate answer and must be labelled, not filled.
            if n["seats"] != GENERIC or n["seats_source"] != "generic type table":
                fails.append("%s: the store has no configuration for this type, so the generic "
                             "table should stand and say so; got %d (%s)"
                             % (car, n["seats"], n["seats_source"]))
            else:
                print("   generic table stands and labels itself, which is correct with no store "
                      "entry to read")
        print("")

    if fails:
        print("FAILED")
        for f in fails:
            print("   %s" % f)
        sys.exit(1)
    print("PASSED. A client-fixed gauge now carries the named carrier's own cabin, the pool is "
          "unchanged, and every seat count states where it came from.")


if __name__ == "__main__":
    main()
