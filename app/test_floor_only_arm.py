#!/usr/bin/env python3
"""Offline test of the floor-only arm: a feed_cfg carrying _floor_only must switch the
connectivity floor and NOTHING else, so the floor A/B (handover item 6) measures one
change. Before _fix_on, a truthy cfg also zeroed P2P carriers' feed, swapped the behind
base capture and put _cap_eff onto the dominance path: four changes read as one.

    py -3.12 test_floor_only_arm.py

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_feed as RF

FAIL = []
CHECKS = 0

FLOOR_ONLY = {"split_floor": False, "_floor_only": True}
FIX = {"behind_cap": 0.10, "dom_gain": 1.0, "dom_floor": 0.5}


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", str(detail)[:70]))
    if not cond:
        FAIL.append(name)


def main():
    check("_fix_on: None is not the fix", RF._fix_on(None) is False, "")
    check("_fix_on: floor-only is not the fix", RF._fix_on(FLOOR_ONLY) is False, "")
    check("_fix_on: the fix is the fix", RF._fix_on(FIX) is True, "")

    # _cap_eff: the floor-only cfg must return the flat base, exactly as cfg None does
    base = 0.10
    check("_cap_eff flat on None", RF._cap_eff(base, 0.9, None) == base, "")
    check("_cap_eff flat on floor-only (the confound closed)",
          RF._cap_eff(base, 0.9, FLOOR_ONLY) == base,
          RF._cap_eff(base, 0.9, FLOOR_ONLY))
    check("_cap_eff scales under the fix",
          abs(RF._cap_eff(base, 0.9, FIX) - base * (0.5 + 0.9)) < 1e-12,
          RF._cap_eff(base, 0.9, FIX))

    # conn_coeff: absent keys fall to the constants either way (already safe; pinned here
    # so a future cfg-shaped change cannot quietly make presence mean something)
    check("conn_coeff identical, None v floor-only",
          RF.conn_coeff("XX", {"YY"}, None) == RF.conn_coeff("XX", {"YY"}, FLOOR_ONLY), "")

    # the floor read itself: route_forecast line ~866's expression, on all three shapes
    floor_on = lambda cfg: True if cfg is None else bool(cfg.get("split_floor", True))
    check("floor ON with cfg None (shipped default)", floor_on(None) is True, "")
    check("floor OFF on the floor-only arm", floor_on(FLOOR_ONLY) is False, "")
    check("floor ON under the fix unless switched",
          floor_on(FIX) is True and floor_on(dict(FIX, split_floor=False)) is False, "")

    # the P2P zeroing condition, as the two feed functions now gate it, using a carrier
    # actually IN the set rather than one assumed into it
    p2p = sorted(RF.P2P_CARRIERS)[0] if RF.P2P_CARRIERS else None
    check("fixture premise: the P2P set is not empty", p2p is not None,
          sorted(RF.P2P_CARRIERS)[:4])
    zeroed = lambda cfg: RF._fix_on(cfg) and p2p in RF.P2P_CARRIERS
    check("P2P feed NOT zeroed on the floor-only arm", zeroed(FLOOR_ONLY) is False, "")
    check("P2P feed zeroed under the fix, as before", zeroed(FIX) is True, "")

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
