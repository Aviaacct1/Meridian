#!/usr/bin/env python3
"""
Avia Solutions - the feed layer's failures are on the record, tested without stores.
====================================================================================
The 15 August review found three silent layers: a failed departure-board read absorbed
into an empty row set (which INFLATES capture to 1.0 on the beyond side at k 1.0, rather
than degrading it), the circuity screen latching itself off for the life of the process
with no record, and the V2-to-V1 fallback counted in a key nothing on the live path read.

Each test here builds the failure by hand and asserts the record it must leave. No store,
no network; runs anywhere in seconds:

    py -3.12 test_feed_provenance.py
"""
import sys


class _BrokenBoards:
    """A boards provider whose reads always fail, standing in for a dead wave cache."""

    def dep_rows(self, week, airport):
        raise RuntimeError("simulated dead board")

    def arr_rows(self, week, airport):
        raise RuntimeError("simulated dead board")


def test_dep_boards_records_the_failure():
    import qsi_feed as QF
    cfg = {}
    out = QF._dep_boards(_BrokenBoards(), "2026-05-25", ["AAA", "BBB"], cfg=cfg)
    assert out == {"AAA": [], "BBB": []}, "rows must still be empty, behaviour unchanged"
    assert cfg["_board_read_fails"] == 2, "every failed read must be counted"
    assert cfg["_board_read_failed"] == ["AAA", "BBB"], "and named"


def test_grouped_board_records_the_failure():
    import qsi_feed as QF
    cfg = {}
    by_arr, country = QF._grouped_dep_board(_BrokenBoards(), "2026-05-25", "CCC", cfg=cfg)
    assert by_arr == {} and country is None
    assert cfg["_board_read_fails"] == 1 and cfg["_board_read_failed"] == ["CCC"]


def test_share_is_one_on_an_empty_competitor_set():
    """Not a fix, a documented hazard: this is WHY an absorbed board read inflates.
    If this behaviour ever changes, the warning wording upstream must change with it."""
    import qsi_feed as QF
    new_itins = [{"frequency": 7.0, "elapsed": 900, "cnx_type": "ONLINE"}]
    assert QF._share(new_itins, [], 1.0) == 1.0


def test_v1_fallback_is_named_not_only_counted():
    """feed_side with qsi_feed requested and a boards object whose reads fail must fall
    back to V1 and record both the counter AND the error text. The market read is stubbed
    (no store on the dev PC); the V1 tail then fails on the missing OAG store, which is
    fine, because the record under test is written before that point."""
    import od_source as OS
    import route_feed as RF
    feed_cfg = {"qsi_feed": True, "dep_time_mins": 30, "flying_mins": 780,
                "route_freq": 4, "route_origin": "AAA", "_boards": _BrokenBoards(),
                "_mct_master": {}}
    saved = (OS.feed_market, RF.hub_served, RF.on_the_way)
    OS.feed_market = lambda *a, **k: ({"XXX": 1000.0}, "Sabre ODPOO", 0.0)
    RF.hub_served = lambda *a, **k: ["XXX"]          # the scope read needs the OAG store
    RF.on_the_way = lambda _o, _h, s, **k: s         # the screen needs coordinates
    try:
        try:
            RF.feed_side(None, None, "2026-05-25", ["AAA"], "HUB", 2025,
                         beyond=True, airline="CI", feed_cfg=feed_cfg)
        except Exception:
            pass
    finally:
        OS.feed_market, RF.hub_served, RF.on_the_way = saved
    assert feed_cfg.get("_qsi_fallbacks", 0) >= 1, "fallback must be counted"
    err = feed_cfg.get("_qsi_fallback_err") or ""
    assert err.startswith("beyond:"), "and named with its side and exception: %r" % err


def test_route_forecast_feed_except_still_writes_the_record():
    """A REGRESSION GUARD ON THE SOURCE, because the clause cannot be reached without the
    stores: forecast() reads Sabre long before the feed block. The 15 August fix made the
    outer feed except write _feed_error to feed_cfg and feed_error to the result; if either
    write is ever removed the crash goes silent again, so their presence is asserted here
    against the file itself."""
    import os
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_forecast.py")
    with open(src_path, encoding="utf-8") as fh:
        src = fh.read()
    assert 'feed_cfg["_feed_error"]' in src, "the except no longer records to feed_cfg"
    assert '"feed_error": _feed_err' in src, "the result no longer carries feed_error"
    bare = "        except Exception:\n            feed_beyond = feed_behind = 0.0"
    assert bare not in src, "the bare silent except is back"


def main():
    here = sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__
                           else __file__.rsplit("/", 1)[0])  # noqa: F841
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS  %s" % name)
            except AssertionError as e:
                fails += 1
                print("FAIL  %s: %s" % (name, e))
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERROR %s: %s: %s" % (name, type(e).__name__, e))
    print("%d failure(s)" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
