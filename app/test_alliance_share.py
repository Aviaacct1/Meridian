#!/usr/bin/env python3
"""Offline checks for the alliance seat-share aggregation (workbook Competition
sheet, 18 August 2026). The SQL side reuses route_watch.daily_seats' proven dedupe
and is exercised on the workstation against the real store; what is testable without
a store is the aggregation, so it is a pure function and tested here.

    py -3.12 test_alliance_share.py

Every figure here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alliance_share import _aggregate

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def main():
    amap = {"BR": "*A", "UA": "*A", "CI": "ST", "AA": "OW"}
    rows = [
        ("BR", "1234567", 300.0),   # 2,100 weekly seats, Star
        ("UA", "1.3.5..", 100.0),   # 300 weekly seats, Star
        ("CI", "12.....", 200.0),   # 400 weekly seats, SkyTeam
        ("WN", "1234567", 100.0),   # 700 weekly seats, unaligned
        ("XX", "", 500.0),          # no mask: no weekly frequency, excluded
        ("AA", ".......", 500.0),   # mask with no digits: excluded
        ("ZZ", "1234567", 0.0),     # zero seats: excluded
    ]
    out = _aggregate(rows, amap)
    check("aggregation returns", out is not None)
    d = dict(out["rows"])
    check("weekly seats = seats x operating days", out["weekly_seats"] == 3500)
    check("star share right", abs(d.get("Star Alliance", 0) - 2400 / 3500.0) < 1e-9)
    check("skyteam named and counted", abs(d.get("SkyTeam", 0) - 400 / 3500.0) < 1e-9)
    check("unaligned bucket exists", abs(d.get("Unaligned", 0) - 700 / 3500.0) < 1e-9)
    check("no-mask record excluded, not spread", "oneworld" not in d)
    check("shares sum to one", abs(sum(d.values()) - 1.0) < 1e-9)
    check("sorted largest first", out["rows"][0][0] == "Star Alliance")
    check("all excluded means None, not zeros",
          _aggregate([("XX", "", 100.0)], amap) is None)
    check("empty input means None", _aggregate([], amap) is None)

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
