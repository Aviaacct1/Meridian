#!/usr/bin/env python3
"""
Avia Solutions - od_source.feed_market check.
=============================================
The feed legs are where the DOT switch earns the US claim, and where it can do the most
damage if it reads the wrong quantity or silently changes a run that was meant to be
untouched. Six cases on a synthetic coupon store, no real data and no network:

  1. OFF        AVIA_OD_SOURCE unset: the Sabre path is called with the FULL scope and
                its answer is returned unchanged, byte for byte, with the Sabre label.
  2. ALL US     every point in the scope is US: the whole side comes from DB1B, dot
                share 1.0.
  3. MIXED      a US and a foreign point in one scope: the US pairs come from DB1B, the
                foreign one from Sabre, both appear in the market, and the dot share is
                the DB1B pounds over the total.
  4. SHORT YEAR a year whose quarters are not all logged as built is refused and falls
                to Sabre. 2016 is short Q1 on the real store, so this is not theoretical.
  5. FIXED SIDE the far end of the pairs is not US (the SJC-TPE shape): refused, Sabre.
  6. BEHIND     the same partition works grouped by origin rather than by destination.

Case 1 is the one that protects everything else in the engine: it asserts that with the
switch off, feed_market is a pass-through and nothing moves.

Usage:
  py -3.12 bt2/od_source_feed_check.py
"""
import os
import sys
import tempfile
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

YEAR = 2024
FACTOR = 1.044
# Synthetic single-connection market, DB1B side. Values chosen so no two sums coincide.
DOT_ROWS = [
    # origin, dest, coupons, pax
    ("SJC", "AUS", 2, 100000.0),
    ("SJC", "BNA", 2, 50000.0),
    ("SJC", "AUS", 1, 900000.0),      # nonstop, must never be read by the feed
    ("PDX", "AUS", 2, 70000.0),
    ("SEA", "AUS", 2, 30000.0),
]
SABRE_PER_PAIR = 11000.0             # what the stub Sabre returns per requested key


def build_store(path, quarters=(1, 2, 3, 4)):
    import duckdb
    con = duckdb.connect(path)
    try:
        con.execute("CREATE TABLE od_market_coupons (origin VARCHAR, dest VARCHAR, year BIGINT, "
                    "quarter BIGINT, coupons BIGINT, pax DOUBLE, avg_fare DOUBLE)")
        con.executemany("INSERT INTO od_market_coupons VALUES (?,?,?,1,?,?,200.0)",
                        [(o, d, YEAR, c, p) for o, d, c, p in DOT_ROWS])
        con.execute("CREATE TABLE build_log (year BIGINT, quarter BIGINT, status VARCHAR, "
                    "source_file VARCHAR, rows_out BIGINT, pax_grossed DOUBLE, seconds DOUBLE, "
                    "built_at VARCHAR)")
        con.executemany("INSERT INTO build_log VALUES (?,?,'built','',1,1.0,0.1,'')",
                        [(YEAR, q) for q in quarters])
        if len(quarters) < 4:
            missing = [q for q in (1, 2, 3, 4) if q not in quarters]
            con.executemany("INSERT INTO build_log VALUES (?,?,'missing','',0,0.0,0.0,'')",
                            [(YEAR, q) for q in missing])
    finally:
        con.close()


def sabre_stub(calls):
    """Records what it was asked for, so case 1 can assert the FULL scope was passed."""
    def fn(origins, dests):
        calls.append((tuple(origins), tuple(dests)))
        keys = dests if len(dests) >= len(origins) else origins
        return {k: SABRE_PER_PAIR for k in keys}
    return fn


def run():
    import od_source as OS
    tmp = tempfile.mkdtemp(prefix="od_feed_check_")
    full = os.path.join(tmp, "full.duckdb")
    short = os.path.join(tmp, "short.duckdb")
    build_store(full)
    build_store(short, quarters=(2, 3, 4))

    results = []

    def case(name, want_source_kind, want_market, want_share, mode, store,
             origins, dests, group, want_sabre_scope=None):
        os.environ.pop("AVIA_OD_SOURCE", None)
        if mode:
            os.environ["AVIA_OD_SOURCE"] = mode
        OS._YEAR_OK.clear()
        OS._coupons_path = lambda: store
        calls = []
        market, source, share = OS.feed_market(sabre_stub(calls), origins, dests, YEAR,
                                               factor_indirect=FACTOR, group=group)
        kind = ("sabre" if source == OS.SABRE
                else "dot" if source == OS.DB1B else "mixed")
        ok = (kind == want_source_kind
              and all(abs(market.get(k, 0.0) - v) < 0.5 for k, v in want_market.items())
              and set(market) == set(want_market)
              and abs(share - want_share) < 1e-6)
        if want_sabre_scope is not None:
            ok = ok and calls and calls[0][1] == want_sabre_scope
        results.append((name, ok, market, source, share))
        return ok

    # 1. OFF: full scope handed to Sabre, answer returned unchanged.
    case("OFF, pass-through", "sabre",
         {"AUS": SABRE_PER_PAIR, "LHR": SABRE_PER_PAIR}, 0.0,
         None, full, ["SJC"], ["AUS", "LHR"], "dest", want_sabre_scope=("AUS", "LHR"))

    # 2. ALL US: whole side from DB1B, factor applied.
    case("all US", "dot",
         {"AUS": 100000.0 * FACTOR, "BNA": 50000.0 * FACTOR}, 1.0,
         "dot", full, ["SJC"], ["AUS", "BNA"], "dest")

    # 3. MIXED: US from DB1B, foreign from Sabre.
    dot_pax = 100000.0 * FACTOR
    case("mixed scope", "mixed",
         {"AUS": dot_pax, "LHR": SABRE_PER_PAIR}, dot_pax / (dot_pax + SABRE_PER_PAIR),
         "dot", full, ["SJC"], ["AUS", "LHR"], "dest")

    # 4. SHORT YEAR: refused.
    case("short year", "sabre", {"AUS": SABRE_PER_PAIR}, 0.0,
         "dot", short, ["SJC"], ["AUS"], "dest")

    # 5. FIXED SIDE not US: the SJC-TPE shape.
    case("fixed side not US", "sabre", {"PDX": SABRE_PER_PAIR, "SEA": SABRE_PER_PAIR}, 0.0,
         "dot", full, ["PDX", "SEA"], ["TPE"], "origin")

    # 6. BEHIND: grouped by origin.
    case("behind, all US", "dot",
         {"PDX": 70000.0 * FACTOR, "SEA": 30000.0 * FACTOR}, 1.0,
         "dot", full, ["PDX", "SEA"], ["AUS"], "origin")

    failed = 0
    for name, ok, market, source, share in results:
        failed += 0 if ok else 1
        shown = " ".join(f"{k}:{v:,.0f}" for k, v in sorted(market.items()))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {shown} | dot share {share:.3f} | {source}")
    print(f"\n{len(results) - failed} of {len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
