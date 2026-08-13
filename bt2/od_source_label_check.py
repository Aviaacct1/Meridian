#!/usr/bin/env python3
"""
Avia Solutions - od_source label check
======================================
The DOT switch earns its claim on the SOURCE LINE, so the label has to be right in
every case, not only in the case it was written for. This builds a synthetic DB1B
store with a known span and asserts the four outcomes:

  1. all-US market, year inside the span, market present  -> DB1B number, DOT label
  2. all-US market, year inside the span, market ABSENT   -> Sabre number, DOT label
     (auto only: DB1B could have seen it and did not, which is the EAS/commuter tail)
  3. all-US market, year OUTSIDE the span                 -> Sabre number, SABRE label
     (DB1B reads nothing for any US market in that year, so the run is a Sabre run)
  4. international market, any year                       -> Sabre number, SABRE label

Case 3 is the one this check was written for. Before 15 August the year case fell
through the market case and kept the DOT label, which would have put "US DOT O&D
Survey (DB1B)" on a slide produced entirely from Sabre, on every market at once.

Runs anywhere: no store and no network. Sabre is stubbed, so the numbers below are
fixtures and mean nothing outside this file.

Usage:
  py -3.12 bt2/od_source_label_check.py
"""
import os
import sys
import tempfile
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

SPAN = (2015, 2024)
SABRE_MARKET = 194550.0          # fixture: what the stub Sabre returns for any market
SABRE_FARE = 156.53              # fixture: the Sabre fare basis the revenue build expects
DB1B_FARE = 210.0                # fixture: the DB1B fare, a DIFFERENT basis, never to be returned
DB1B_MARKET = 250000.0           # fixture: what the synthetic DB1B holds for SJC-AUS


def build_store(path):
    """Synthetic od_market: one all-US market with rows, spanning SPAN."""
    import duckdb
    con = duckdb.connect(path)
    try:
        con.execute("CREATE TABLE od_market (origin VARCHAR, dest VARCHAR, year BIGINT, "
                    "pax DOUBLE, avg_fare DOUBLE)")
        rows = [("SJC", "AUS", y, DB1B_MARKET, DB1B_FARE) for y in range(SPAN[0], SPAN[1] + 1)]
        con.executemany("INSERT INTO od_market VALUES (?, ?, ?, ?, ?)", rows)
    finally:
        con.close()


def stub_sabre():
    """Replace the Sabre reader so the check needs no store and the numbers are known."""
    import sabre_catchment as SC
    SC.destination_market_split = (
        lambda db, airports, dest_airports, **kw:
        ({a: SABRE_MARKET for a in airports}, SABRE_MARKET * len(airports), SABRE_FARE))


def main():
    tmp = tempfile.mkdtemp(prefix="od_source_check_")
    store = os.path.join(tmp, "db1b.duckdb")
    build_store(store)
    os.environ["AVIA_DB1B_DUCKDB"] = store
    os.environ["AVIA_OD_SOURCE"] = "auto"

    stub_sabre()
    import od_source as OS
    OS._YEARS.clear()
    # config may resolve DB1B_DUCKDB to the real store, so pin the module's own reader.
    OS._db1b_path = lambda: store

    cases = [
        ("in span, market present", ["SJC"], ["AUS"], 2024, DB1B_MARKET, OS.DB1B, False),
        ("in span, market absent", ["SJC"], ["BFL"], 2024, SABRE_MARKET, OS.DB1B, False),
        ("outside span, indexing off", ["SJC"], ["AUS"], 2025, SABRE_MARKET, OS.SABRE, False),
        ("international market", ["SJC"], ["TPE"], 2024, SABRE_MARKET, OS.SABRE, False),
        # Vintage indexing on the P2P leg. The stub Sabre returns the same market for every
        # year, so the growth factor is exactly 1.0 and the DOT level comes through unchanged
        # with the vintage in the label. That is the arithmetic being asserted, not the growth.
        ("outside span, indexed", ["SJC"], ["AUS"], 2025, DB1B_MARKET, "vintage", True),
    ]

    failed = 0
    for name, origins, dests, year, want_market, want_source, index_on in cases:
        os.environ["AVIA_OD_INDEX_VINTAGE"] = "1" if index_on else "0"
        split, market, avg_fare, source = OS.market_split(
            "unused_sabre.duckdb", origins, dests, year=year)
        if want_source == "vintage":
            ok = (abs(market - want_market) < 0.5 and OS.is_dot(source)
                  and "2024 vintage, indexed to 2025" in source)
        else:
            ok = (abs(market - want_market) < 0.5) and (source == want_source)
        # THE FARE BASIS NEVER MOVES. DB1B's MktFare excludes taxes and Sabre's total fare
        # includes them, so returning the DB1B fare with a DB1B volume would cut deck revenue
        # by the wedge between them for a reason that has nothing to do with revenue.
        fare_ok = abs(avg_fare - SABRE_FARE) < 0.01
        ok = ok and fare_ok
        failed += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: market {market:,.0f} "
              f"(want {want_market:,.0f}), fare {avg_fare:,.2f} "
              f"({'Sabre basis' if fare_ok else 'WRONG BASIS'}), source {source}")
    os.environ.pop("AVIA_OD_INDEX_VINTAGE", None)

    print(f"\n{len(cases) - failed} of {len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
