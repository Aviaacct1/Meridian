#!/usr/bin/env python3
"""Avia Solutions - John's 21 August ask: does the catchment-widening issue found in
diag_tpe_sjc_catchment_decomp.py actually move the headline P2P/connecting split (the split
route_forecast.py's own comment says "takes P2P from 62% of the carried total to 45%" on this exact
route), or is the split protected from it by the separate connectivity-floor mechanism?

WHY THIS IS A SEPARATE QUESTION FROM THE LAST SCRIPT. The 719,486 catchment-inflated beyond market
does not inflate the route's TOTAL carried passengers - that is capped at the aircraft's seats x load
factor regardless (139,230 two-way on this pitch). What it can do is change how much of that fixed
total gets allocated to P2P versus connecting, via route_forecast.forecast()'s re-split block
(app/route_forecast.py, ~line 852-891):

    _engine_conn   = carried * (feed / total_demand)     # the engine's own split - feed includes the
                                                          # catchment-inflated feed_beyond
    _resplit_conn  = carried * (1.0 - p2p_share(o, d))   # split_share's INDEPENDENT connectivity-table
                                                          # estimate - does not touch feed_side at all
    conn_carried   = max(_engine_conn, _resplit_conn)    # ONLY LIFTS connecting, never cuts it
    p2p_carried    = carried - conn_carried

If _resplit_conn is already the larger of the two, the connectivity floor is what's setting today's
split, and the catchment bug - real as it is - is NOT what produced the 62%->45% move; fixing it
would change nothing about the headline numbers. If _engine_conn is the larger one, the catchment
bug IS what's driving the split, and needs fixing before this is presented.

WHAT THIS SCRIPT DOES. Captures the actual production route_forecast.forecast() call's returned
values (feed_beyond, feed_behind, connecting_feed, total_demand, carried_forecast, p2p_carried,
connecting_carried - all already in its return dict, no new plumbing needed), calls split_share.
p2p_share("SJC","TPE") directly (a static, feed-independent lookup) to get the connectivity-table
share, reconstructs _engine_conn/_resplit_conn from those returned values, and checks which one the
live run actually used by reproducing conn_carried and comparing to the return dict's own connecting_
carried - not guessed, checked. Then re-derives _engine_conn using the SJC-only beyond figure the
last script measured, to see whether the fix would move the winner.

Run on the workstation:
    py -3.12 diag_p2p_connecting_split_check.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")

import route_forecast as RFC          # patch BEFORE cortex_app is imported/called
import route_feed as RFEED
import split_share as SS

_captured_beyond_calls = []
_captured_forecast_return = {}
_orig_feed_side = RFEED.feed_side
_orig_forecast = RFC.forecast
_orig_p2p_share = SS.p2p_share


def _capturing_feed_side(sabre_db, oag_db, week, origin_airports, hub, year, **kw):
    if kw.get("beyond", True):
        _captured_beyond_calls.append(
            dict(sabre_db=sabre_db, oag_db=oag_db, week=week, origin_airports=list(origin_airports),
                 hub=hub, year=year, kw=dict(kw)))
    return _orig_feed_side(sabre_db, oag_db, week, origin_airports, hub, year, **kw)


def _capturing_forecast(*args, **kwargs):
    # Read the return dict directly, keys confirmed by reading app/route_forecast.py's own return
    # statement (~line 905-939) rather than guessed from cortex_app's wrapping - that guess is what
    # cost the last two runs. This is the same proven technique the earlier two scripts used.
    r = _orig_forecast(*args, **kwargs)
    _captured_forecast_return.update(r)
    return r


_captured_share = {}


def _capturing_p2p_share(origin, dest):
    v = _orig_p2p_share(origin, dest)
    _captured_share[(origin, dest)] = v
    return v


RFEED.feed_side = _capturing_feed_side
RFC.forecast = _capturing_forecast
SS.p2p_share = _capturing_p2p_share

import cortex_app as CA                # imports route_forecast -> gets the patched module


def main():
    fc = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC", aircraft="A359", freq=5)
    if not fc.get("ok"):
        print(f"Production call failed: {fc.get('error')}. STOP.")
        return

    d = _captured_forecast_return
    if not d:
        print("STOP: monkeypatch did not capture a route_forecast.forecast() call - import order is "
              "wrong. Do not trust anything below.")
        return

    feed_beyond = d.get("feed_beyond")
    feed_behind = d.get("feed_behind")
    connecting_feed = d.get("connecting_feed")
    total_demand = d.get("total_demand")
    carried_forecast = d.get("carried_forecast")
    p2p_carried_actual = d.get("p2p_carried")
    connecting_carried_actual = d.get("connecting_carried")

    missing = [k for k, v in [("feed_beyond", feed_beyond), ("feed_behind", feed_behind),
                               ("connecting_feed", connecting_feed), ("total_demand", total_demand),
                               ("carried_forecast", carried_forecast),
                               ("p2p_carried", p2p_carried_actual),
                               ("connecting_carried", connecting_carried_actual)] if v is None]
    if missing:
        print(f"STOP: forecast()'s own return dict is missing {missing}. This script's key names no "
              f"longer match the source - do not trust anything below.")
        print(f"Actual keys returned: {sorted(d.keys())}")
        return

    _sh = _captured_share.get(("SJC", "TPE"))
    if _sh is None:
        _sh = _orig_p2p_share("SJC", "TPE")
        print("NOTE: p2p_share('SJC','TPE') was not called during the production run itself (split_"
              "floor may be off, or availability failed) - calling it directly instead. If this route "
              "genuinely never reaches the re-split block, the section below does not apply and the "
              "engine's own feed split is what's live.")

    print(f"Production run returned:")
    print(f"  feed_beyond={feed_beyond:,}  feed_behind={feed_behind:,}  connecting_feed={connecting_feed:,}")
    print(f"  total_demand={total_demand:,}  carried_forecast={carried_forecast:,}")
    print(f"  ACTUAL p2p_carried={p2p_carried_actual:,}  ACTUAL connecting_carried={connecting_carried_actual:,}"
          f"  ({connecting_carried_actual/carried_forecast*100:.1f}% connecting)")
    print(f"  split_share.p2p_share('SJC','TPE') = {_sh:.4f}  (independent connectivity-table estimate, "
          f"{( 1-_sh)*100:.1f}% connecting)\n")

    rawtot = max(total_demand, 1.0)
    engine_conn = carried_forecast * (connecting_feed / rawtot)
    resplit_conn = carried_forecast * (1.0 - _sh)
    winner = "engine (feed-driven - INCLUDES the catchment-inflated beyond feed)" if engine_conn >= resplit_conn \
        else "connectivity floor (split_share - independent of the beyond feed)"

    print("=== SANITY CHECK: reproduce today's actual connecting_carried ===")
    reproduced = max(engine_conn, resplit_conn)
    diff_pct = abs(reproduced - connecting_carried_actual) / connecting_carried_actual * 100
    print(f"  engine_conn (feed-driven):        {engine_conn:,.0f}")
    print(f"  resplit_conn (connectivity-table): {resplit_conn:,.0f}")
    print(f"  max() of the two, reproduced:      {reproduced:,.0f}  vs actual {connecting_carried_actual:,}"
          f"  ({diff_pct:.1f}% difference)")
    if diff_pct > 2:
        print("  MISMATCH > 2%. STOP - this script's reconstruction of the re-split block does not "
              "match production; do not trust the verdict below without finding out why (possible "
              "causes: split_floor is off for this run, bucket_correct or another later adjustment "
              "moved carried_forecast after the re-split, or the reconstruction above is wrong).")
        return
    print(f"  Reproduced cleanly. TODAY'S SPLIT IS SET BY: {winner}\n")

    # ============ WOULD THE FIX CHANGE THE WINNER? ============
    # Uses the SAME wide-vs-SJC-only beyond feed measured in diag_tpe_sjc_catchment_decomp.py's run 2:
    # cell A (wide, grown) 719,486 one-way base -> feed_beyond above is the CAPTURED, grown figure
    # already, so scale it by the same ratio the earlier script measured on the raw base
    # (captured scales with the same market change, holding the capture rate fixed - the capture rate
    # itself is not origin-list-dependent, only the market it's applied to is).
    bcall = _captured_beyond_calls[-1] if _captured_beyond_calls else None
    if not bcall:
        print("Could not capture a feed_side call to measure the SJC-only beyond feed directly - "
              "falling back to the 68.13x catchment ratio already measured in the last script's run 2.")
        feed_beyond_narrow = feed_beyond / 68.13
    else:
        # g derived the same way as the last script: feed_beyond (from forecast()'s return dict) is
        # ALREADY bt_wide_raw * g, where bt_wide_raw is feed_side's own first return value (captured,
        # ungrown) for the wide catchment - so calling feed_side fresh with the SAME wide catchment and
        # dividing gives g cleanly, on a captured-vs-captured basis (not the base-vs-captured mismatch
        # an earlier draft of this script had).
        side_kw = dict(bcall["kw"]); side_kw["detail"] = False
        bt_wide_raw, _ = _orig_feed_side(bcall["sabre_db"], bcall["oag_db"], bcall["week"],
                                          bcall["origin_airports"], bcall["hub"], bcall["year"], **side_kw)
        g = feed_beyond / bt_wide_raw if bt_wide_raw else None
        if not g:
            print("STOP: could not derive g (bt_wide_raw came back 0) - do not trust the section below.")
            return
        bt_narrow_raw, _ = _orig_feed_side(bcall["sabre_db"], bcall["oag_db"], bcall["week"],
                                            ["SJC"], bcall["hub"], bcall["year"], **side_kw)
        feed_beyond_narrow = bt_narrow_raw * g

    connecting_feed_narrow = feed_beyond_narrow + feed_behind
    engine_conn_narrow = carried_forecast * (connecting_feed_narrow / rawtot)

    print("=== IF BEYOND USED SJC-ONLY INSTEAD OF THE WIDE CATCHMENT ===")
    print(f"  feed_beyond: {feed_beyond:,.0f} -> {feed_beyond_narrow:,.0f}")
    print(f"  connecting_feed: {connecting_feed:,.0f} -> {connecting_feed_narrow:,.0f}")
    print(f"  engine_conn: {engine_conn:,.0f} -> {engine_conn_narrow:,.0f}")
    print(f"  resplit_conn (unchanged, does not depend on feed): {resplit_conn:,.0f}")
    new_winner = "engine (still feed-driven)" if engine_conn_narrow >= resplit_conn else "connectivity floor"
    print(f"  New winner: {new_winner}")
    if new_winner != winner:
        new_conn = max(engine_conn_narrow, resplit_conn)
        print(f"\n  THE WINNER CHANGES. Fixing the catchment bug WOULD move the headline split.")
        print(f"  connecting_carried: {connecting_carried_actual:,} -> {new_conn:,.0f}  "
              f"({new_conn/carried_forecast*100:.1f}% connecting, vs today's "
              f"{connecting_carried_actual/carried_forecast*100:.1f}%)")
        print(f"  p2p_carried: {p2p_carried_actual:,} -> {carried_forecast - new_conn:,.0f}")
    else:
        print(f"\n  THE WINNER DOES NOT CHANGE. The connectivity floor was already binding before and "
              f"after - fixing the beyond-side catchment bug would not move today's headline P2P/"
              f"connecting split. It would still change slide 51's Taipei-vs-San Jose breakdown "
              f"WITHIN the connecting total (that split uses feed_beyond/feed_behind directly, not "
              f"gated by this floor), but not the P2P vs connecting total the deck's top-line "
              f"passenger numbers are built from.")


if __name__ == "__main__":
    main()
