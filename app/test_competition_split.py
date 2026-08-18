#!/usr/bin/env python3
"""Offline checks for the competition split arithmetic (18 August 2026). The
engine runs and the OAG classification happen on the workstation; what is testable
without stores is the renormalisation, the flatness refusal and the bucketing.

    py -3.12 test_competition_split.py

Every figure here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from competition_split import renormalise, flatness, bucket

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    # PAYLOAD key names (code/base/forecast), the shape the live rows actually
    # carry; the contract names are checked separately below. The first cut read
    # only the contract names, saw nothing, and printed "flat shares" as though
    # it had measured something. Never again.
    rows = [
        {"code": "MNL", "base": 80000, "forecast": 800},
        {"code": "SGN", "base": 79000, "forecast": 4000},
        {"code": "BKK", "base": 68000, "forecast": 3200},
    ]
    out = renormalise(rows, 4000)
    check("allocation sums to the V1 leg total",
          abs(sum(r["alloc"] for r in out) - 4000) < 1e-6)
    check("shape preserved (SGN five times MNL)",
          abs(out[1]["alloc"] / out[0]["alloc"] - 5.0) < 1e-9)
    check("no forecast to shape with returns None",
          renormalise([{"base": 1, "forecast": 0}], 100) is None)
    check("zero leg total returns None", renormalise(rows, 0) is None)

    flat = [{"code": c, "base": 1000 * (i + 1),
             "forecast": 43.1 * (i + 1)} for i, c in enumerate("ABCDE")]
    check("flat shares detected (cv near zero)", flatness(flat) < 0.001)
    check("differentiated shares detected", flatness(rows) > 0.5)
    check("contract key names read too",
          flatness([{"city_code": "A", "annual_demand": 100, "annual_forecast": 1},
                    {"city_code": "B", "annual_demand": 100, "annual_forecast": 9}]) > 0.5)
    check("unreadable rows REFUSE with None, never zero",
          flatness([{"foo": 1}, {"bar": 2}]) is None)

    b = bucket(out, {"MNL"})
    check("competed bucket holds MNL only", b["competed"]["n"] == 1)
    check("bucket bases split correctly",
          b["competed"]["base"] == 80000 and b["uncompeted"]["base"] == 147000)
    check("bucket allocs sum to the leg",
          abs(b["competed"]["alloc"] + b["uncompeted"]["alloc"] - 4000) < 1e-6)
    check("competed capture below uncompeted here",
          b["competed"]["capture"] < b["uncompeted"]["capture"])
    check("empty bucket capture is None, not zero",
          bucket(out, set())["competed"]["capture"] is None)

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
