#!/usr/bin/env python3
r"""Do the contract's legs add up to its total, and does its total fit the aeroplane?

WHY THIS EXISTS. On 14 August 2026 the SJC-TPE contract reported a grand total of 123,266 against
an annual capacity of 127,296, which is 96.8% of the aircraft against a plan cap of 87.5%. Nothing
in the pipeline objected, because no stage held the legs and the total against each other. Three
faults were behind it and all three were in the contract layer:

  1. deck_contract wrote the TOTAL carried into point_to_point_total. It was written against
     assess(), where directional_demand was the local leg; cortex_app's payload sets demand.total to
     carried_ew, and route_forecast line 823 computes that as min(captured + feed, capacity x cap),
     so the connecting passengers are already inside it. A deck built off that contract would have
     presented an entire route as local traffic.
  2. grand_total then ADDED the two connecting legs to a figure that already contained them.
  3. connecting_at_hub.total was the sum of the city table, and cortex_app._feed_list takes top=15,
     so it was the fifteen largest cities presented as a leg. Measured: 13,502 against an implied
     26,356.

THE FOUR INVARIANTS, each one a fault above turned into a test that cannot pass by accident:

  LEGS SUM        point to point + connecting at hub + connecting at destination = grand total.
                  Fault 1 and fault 2 both break this and it is the cheapest thing in the file.
  FITS THE METAL  grand total over annual capacity does not exceed the plan cap. A forecast the
                  aircraft cannot carry is not a forecast.
  LEGS DIFFER     point to point is not identical to the grand total on a route with connecting
                  traffic. This is fault 1 on its own, which the legs-sum test would MISS if the
                  connecting legs were also zero.
  SUBTOTAL        top_cities_forecast never exceeds its own leg. Fault 3.

It also reports the load factor three ways, because that is how the fault was found: the total over
capacity, the figure economics_year1 states, and the point to point leg over capacity. Where those
three disagree, one of them is describing a different quantity from the one its name claims.

THIS FILE ASSERTS NOTHING ABOUT WHETHER A FORECAST IS RIGHT. It checks that a contract is internally
consistent, which is a lower bar and was not being cleared.

    Workstation:
    cd C:\src\meridian\app
    py -3.12 contract_legs_check.py E:\Avia\contracts

Avia Solutions Limited. All rights reserved.
"""
import argparse
import glob
import json
import os
import sys

PLAN_CAP = 0.875          # route_forecast.MAX_PLAN_LF
TOL_PAX = 2               # rounding across three doubled each-way figures
TOL_LF = 0.005


def parse_args():
    p = argparse.ArgumentParser(description="Internal consistency of deck data contracts.")
    p.add_argument("folder", help="folder of *_contract.json")
    p.add_argument("--cap", type=float, default=PLAN_CAP,
                   help="plan load factor cap the totals are held to, default %.3f" % PLAN_CAP)
    return p.parse_args()


def check(path, cap):
    """Returns (name, [failures], [notes]). A missing figure is reported and never assumed."""
    with open(path, encoding="utf-8") as f:
        c = json.load(f)
    name = os.path.basename(path).replace("_contract.json", "")
    fails, notes = [], []

    s = ((c.get("segment_forecast") or {}).get("summary") or {})
    p2p = (s.get("point_to_point_total") or {}).get("forecast")
    hub = (s.get("connecting_at_hub_total") or {}).get("forecast")
    dst = (s.get("connecting_at_destination_total") or {}).get("forecast")
    tot = (s.get("grand_total") or {}).get("forecast")
    capacity = ((c.get("revenue_forecast") or {}).get("annual_capacity") or [None])[0]
    stated_lf = (c.get("economics_year1") or {}).get("total_load_factor")

    if tot is None:
        return name, ["no grand total: nothing can be checked"], notes

    # LEGS SUM. Absent legs are named rather than treated as zero, because a zero would let the
    # test pass on a contract that simply lost a leg.
    missing = [n for n, v in (("point to point", p2p), ("connecting at hub", hub),
                              ("connecting at destination", dst)) if v is None]
    if missing:
        notes.append("legs sum NOT CHECKED, absent: %s" % ", ".join(missing))
    else:
        legs = p2p + hub + dst
        if abs(legs - tot) > TOL_PAX:
            fails.append("legs sum to %s against a grand total of %s, a difference of %s"
                         % (f"{legs:,}", f"{tot:,}", f"{legs - tot:,}"))
        # LEGS DIFFER. Catches the total being written into the local leg even when the legs sum.
        if hub or dst:
            if p2p == tot:
                fails.append("point to point is identical to the grand total on a route with "
                             "%s connecting passengers" % f"{(hub or 0) + (dst or 0):,}")

    # FITS THE METAL.
    if capacity:
        lf = tot / capacity
        if lf > cap + TOL_LF:
            fails.append("grand total is %.1f%% of capacity against a plan cap of %.1f%%: %s "
                         "passengers on %s seats"
                         % (100 * lf, 100 * cap, f"{tot:,}", f"{capacity:,}"))
        # THE THREE LOAD FACTORS. Reported always, because their disagreement is the diagnosis.
        line = "load factor: total %.3f" % lf
        if stated_lf is not None:
            line += ", economics_year1 states %.3f" % stated_lf
            if abs(stated_lf - lf) > TOL_LF:
                fails.append("economics_year1 states a load factor of %.3f while the grand total "
                             "over capacity is %.3f; two figures for one quantity"
                             % (stated_lf, lf))
        if p2p:
            line += ", point to point alone %.3f" % (p2p / capacity)
        notes.append(line)
    else:
        notes.append("no annual capacity: the metal check did not run")

    # SUBTOTAL never exceeds its leg.
    for lbl, blk, leg in (("hub", s.get("connecting_at_hub_total") or {}, hub),
                          ("destination", s.get("connecting_at_destination_total") or {}, dst)):
        top = blk.get("top_cities_forecast")
        if top is not None and leg is not None and top > leg + TOL_PAX:
            fails.append("the %s city table sums to %s, above its own leg of %s"
                         % (lbl, f"{top:,}", f"{leg:,}"))
        elif top is not None and leg:
            notes.append("%s city table is %s of the leg, %s of %s"
                         % (lbl, "%.0f%%" % (100.0 * top / leg), f"{top:,}", f"{leg:,}"))
    return name, fails, notes


def main():
    a = parse_args()
    files = sorted(glob.glob(os.path.join(a.folder, "*_contract.json")))
    if not files:
        sys.exit("No *_contract.json in %s. Run deck_from_cases.py --out first." % a.folder)
    print("%d contracts, plan cap %.3f\n" % (len(files), a.cap))
    bad = 0
    for f in files:
        name, fails, notes = check(f, a.cap)
        print("%s  %s" % ("FAIL" if fails else "ok  ", name))
        for n in notes:
            print("        %s" % n)
        for x in fails:
            print("        -> %s" % x)
        if fails:
            bad += 1
    print("\n%d of %d contracts are internally consistent" % (len(files) - bad, len(files)))
    if bad:
        print("A FAILURE HERE IS NOT A FORECASTING ERROR. It is the contract describing one "
              "quantity under two names, which is what put a 96.8% load factor into a deck "
              "contract on 14 August.")
        sys.exit(1)


if __name__ == "__main__":
    main()
