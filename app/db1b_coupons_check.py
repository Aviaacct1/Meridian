#!/usr/bin/env python3
r"""
Avia Solutions - DB1B coupon store check.
=========================================
The coupon store is only usable if summing its coupon classes reproduces od_market. If
it does, the two stores share a build convention and the SPLIT can be trusted, because
the only thing that has changed is that a total has been broken down. If it does not,
build_db1b_store.py applied a filter this builder does not, and that filter has to be
found before either store is read as the other's detail.

Four checks:

  TOTAL          summed coupon classes against od_market for the year, in per cent.
  PAIR           the same comparison on named dense and thin pairs, so a total that
                 agrees by offsetting errors is caught.
  SPLIT SANE     every class share between 0 and 1 and summing to 1; the nonstop share
                 on a pair with no nonstop service is at or near zero.
  QUARTERS       four quarters logged as built for the year, and no quarter logged
                 missing or empty. A three-quarter year is not a year.

Nothing here is a forecast and no figure leaves this file. It is a consistency check on
two stores, which is a lower bar than correctness and is the bar that was not cleared
the last four times.

Usage (workstation):
    py -3.12 db1b_coupons_check.py --year 2024
    py -3.12 db1b_coupons_check.py --year 2024 --coupons E:\Avia\db1b_coupons.duckdb
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Dense pairs with heavy nonstop service, and thin pairs with none. The thin ones are the
# test that matters: a nonstop-only build would show them empty.
DENSE = [("LAX", "JFK"), ("SFO", "ORD"), ("SJC", "SEA")]
THIN = [("FAT", "BOS"), ("BIS", "MIA"), ("ROA", "SFO")]
TOLERANCE_PCT = 0.5      # summed classes against od_market


def _paths(args):
    db1b, coupons = args.db1b, args.coupons
    try:
        import config
        db1b = db1b or str(config.DB1B_DUCKDB)
        coupons = coupons or str(config.DB1B_COUPONS_DUCKDB)
    except Exception:
        pass
    return db1b, coupons


def _con(path):
    import duckdb
    return duckdb.connect(path, read_only=True)


def main():
    ap = argparse.ArgumentParser(description="Check the DB1B coupon store against od_market.")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--db1b", default=None)
    ap.add_argument("--coupons", default=None)
    args = ap.parse_args()

    db1b, coupons = _paths(args)
    for label, path in (("db1b", db1b), ("coupons", coupons)):
        if not path or not os.path.exists(path):
            print(f"ERROR: {label} store not found: {path}")
            return 2

    a, b = _con(db1b), _con(coupons)
    failed = 0
    try:
        print(f"od_market:        {db1b}")
        print(f"od_market_coupons:{coupons}")
        print(f"Year:             {args.year}\n")

        # QUARTERS
        rows = b.execute("SELECT status, count(*) FROM build_log WHERE year=? GROUP BY 1",
                         [args.year]).fetchall()
        status = {s: n for s, n in rows}
        ok = status.get("built", 0) == 4 and not status.get("missing") and not status.get("empty")
        failed += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] QUARTERS: {status or 'nothing logged'}")

        # TOTAL
        t_old = a.execute("SELECT SUM(pax) FROM od_market WHERE year=?", [args.year]).fetchone()[0] or 0
        t_new = b.execute("SELECT SUM(pax) FROM od_market_coupons WHERE year=?",
                          [args.year]).fetchone()[0] or 0
        diff = (100.0 * (t_new - t_old) / t_old) if t_old else float("inf")
        ok = abs(diff) <= TOLERANCE_PCT
        failed += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] TOTAL: od_market {t_old:,.0f}, "
              f"coupons summed {t_new:,.0f}, {diff:+.2f}%")

        # PAIR
        for o, d in DENSE + THIN:
            p_old = a.execute("SELECT SUM(pax) FROM od_market WHERE year=? AND origin=? AND dest=?",
                              [args.year, o, d]).fetchone()[0] or 0
            p_new = b.execute("SELECT SUM(pax) FROM od_market_coupons WHERE year=? AND origin=? "
                              "AND dest=?", [args.year, o, d]).fetchone()[0] or 0
            pd = (100.0 * (p_new - p_old) / p_old) if p_old else (0.0 if not p_new else float("inf"))
            ok = abs(pd) <= TOLERANCE_PCT
            failed += 0 if ok else 1
            print(f"  [{'PASS' if ok else 'FAIL'}] PAIR {o}-{d}: {p_old:,.0f} vs {p_new:,.0f}, {pd:+.2f}%")

        # SPLIT SANE
        for o, d in DENSE + THIN:
            rows = b.execute("SELECT coupons, SUM(pax) FROM od_market_coupons WHERE year=? "
                             "AND origin=? AND dest=? GROUP BY 1 ORDER BY 1",
                             [args.year, o, d]).fetchall()
            total = sum(p for _, p in rows) or 0
            if not total:
                print(f"  [FAIL] SPLIT {o}-{d}: no rows")
                failed += 1
                continue
            shares = {int(c): p / total for c, p in rows}
            nonstop = shares.get(1, 0.0)
            thin = (o, d) in THIN
            ok = (abs(sum(shares.values()) - 1.0) < 1e-6
                  and all(0.0 <= s <= 1.0 for s in shares.values())
                  and (nonstop < 0.10 if thin else nonstop > 0.0))
            failed += 0 if ok else 1
            desc = " ".join(f"{c}:{s:.1%}" for c, s in sorted(shares.items()))
            print(f"  [{'PASS' if ok else 'FAIL'}] SPLIT {o}-{d} ({'thin' if thin else 'dense'}): {desc}")
    finally:
        a.close()
        b.close()

    print(f"\n{'ALL CHECKS PASSED' if not failed else str(failed) + ' CHECK(S) FAILED'}")
    if failed:
        print("A failing TOTAL or PAIR means build_db1b_store.py applied a filter this builder "
              "does not. Find the filter before either store is read as the other's detail.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
