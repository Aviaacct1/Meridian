#!/usr/bin/env python3
r"""
Avia Solutions - why od_source did or did not answer.
=====================================================
A switch that silently declines is the same shape as a silent default, which this
codebase has now been caught by nine times. od_source has five independent guards and
any one of them sends a leg back to Sabre. This reports each verdict separately for a
named year and a named pair, so a nil result names its own cause instead of leaving
five candidates.

    mode          AVIA_OD_SOURCE is dot or auto
    store         the coupon store resolves and exists
    year          all four quarters of the year are logged built
    airports      the airport table loads and the codes resolve as US
    wiring        which call sites actually go through od_source

Usage (workstation):
    py -3.12 od_source_why.py --year 2025 --origin SJC --dest BOS --mode auto
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def main():
    ap = argparse.ArgumentParser(description="Report which od_source guard decided.")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--origin", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--mode", default="auto")
    args = ap.parse_args()

    os.environ["AVIA_OD_SOURCE"] = args.mode
    import od_source as OS
    OS._YEAR_OK.clear()

    print(f"Year {args.year}, {args.origin}-{args.dest}, mode {args.mode}\n")

    print(f"  mode        AVIA_OD_SOURCE={OS._mode()}  "
          f"{'PASS' if OS._mode() in ('dot', 'auto') else 'FAIL, sabre means off'}")

    coupons = OS._coupons_path()
    ok_store = os.path.exists(coupons)
    print(f"  store       {coupons}  {'PASS' if ok_store else 'FAIL, not found'}")

    if ok_store:
        try:
            from db_registry import con_ro
            con = con_ro(coupons)
            try:
                span = con.execute("SELECT MIN(year), MAX(year) FROM od_market_coupons").fetchone()
                log = con.execute("SELECT status, count(*) FROM build_log WHERE year=? GROUP BY 1",
                                  [args.year]).fetchall()
                years = con.execute("SELECT year, count(*) FILTER (WHERE status='built') "
                                    "FROM build_log GROUP BY 1 HAVING count(*) "
                                    "FILTER (WHERE status='built')=4 ORDER BY 1 DESC LIMIT 3"
                                    ).fetchall()
            finally:
                con.close()
            ok_year = OS._year_complete(coupons, args.year)
            print(f"  year        store spans {span[0]}-{span[1]}; build_log for {args.year}: "
                  f"{dict(log) or 'nothing logged'}  {'PASS' if ok_year else 'FAIL'}")
            if not ok_year:
                print(f"              most recent COMPLETE years: "
                      f"{', '.join(str(y) for y, _ in years) or 'none'}")
        except Exception as e:                                     # noqa: BLE001
            print(f"  year        FAIL, could not read the store: {type(e).__name__}: {e}")

    try:
        import airportsdata                                        # noqa: F401
        ok_ad = True
    except Exception as e:                                         # noqa: BLE001
        ok_ad = False
        print(f"  airports    FAIL, airportsdata will not import: {type(e).__name__}: {e}")
    if ok_ad:
        o_us, d_us = OS._us(args.origin.upper()), OS._us(args.dest.upper())
        print(f"  airports    {args.origin} US={o_us}, {args.dest} US={d_us}  "
              f"{'PASS' if (o_us and d_us) else 'FAIL, DB1B holds US domestic only'}")

    print("\n  wiring      feed legs   route_feed.feed_side and behind_feed go through "
          "od_source.feed_market")
    print("              point to point   cortex_app calls "
          "sabre_catchment.destination_market_split DIRECTLY")
    print("                               at lines 776, 946 and 1001. od_source.market_split is "
          "called ONLY")
    print("                               by backtest.py line 462, so the live P2P leg has never "
          "been wired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
