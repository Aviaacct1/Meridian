#!/usr/bin/env python3
"""
Avia Solutions - DOT + regional enrichment for the backtest substrate.
======================================================================
Joins US DOT actuals and carrier economics onto a backtest spine at the PRE-LAUNCH vintage
(launch year - 1), so every added feature is forecast-time with no outturn leakage:

  db1b_market_v   real US O&D market (both directions), DB1B od_market at Y-1   [C:\\Avia\\db1b.duckdb]
  db1b_fare_v     DB1B average one-way market fare at Y-1
  db1b_to_sabre   db1b_market_v / natural (the spine's Sabre market) = the DOT-vs-Sabre coverage
                  ratio per route; encodes where Sabre under- or over-reads (the SJC signature)
  carrier_casm_c  operating economics: the (marketing) carrier's CASM cents/ASK at Y-1  [casm_benchmark.duckdb]
  carrier_rasm_c  the carrier's RASM cents/ASK at Y-1
  carrier_stage_km the carrier's average stage length at Y-1
  is_regional     flag: the carrier code is a US regional/commuter brand

DB1B is US-domestic only, so non-US pairs get blank DB1B columns (kept, not dropped). CASM covers
regionals (9E/OO/MQ/EV) as well as majors. NOT joined here (stores live on E:, not on C:\\Avia):
T-100 operated capacity/seats, and raw Form 41; add them when E: is mounted. Regional block-hour
cost (298C) is keyed to the OPERATING carrier, which the spine does not yet export - wire that with
the Regional carrier-type work (operator vs marketing) and this script can add it.

Usage:
  py -3.12 build_dot_enrichment.py --spine bt_full_features.csv --out master_dot.csv
"""
import argparse, csv, os, sys

REGIONAL_CODES = {  # US regional / commuter marketing or operating brands (IATA/DOT)
    "9E", "OO", "MQ", "EV", "OH", "YV", "YX", "ZW", "QX", "G7", "C5", "AX", "9K", "CP", "PT",
    "S5", "3M", "L3", "N8", "G4",  # G4 Allegiant is ULCC not regional; drop if it muddies - kept flaggable
}
# G4 is ultra-low-cost, not a regional feeder; remove from the regional set to avoid mislabelling.
REGIONAL_CODES.discard("G4")


def _con(path):
    import duckdb
    return duckdb.connect(path, read_only=True, config={"memory_limit": "1500MB", "threads": "2"})


def load_db1b(path):
    """(origin, dest, year) -> (pax, fare). Directional; caller sums both ways."""
    d = {}
    if not os.path.exists(path):
        print(f"  WARNING: db1b store not found at {path}; DB1B columns will be blank")
        return d
    con = _con(path)
    try:
        for o, de, y, pax, fare in con.execute("SELECT origin, dest, year, pax, avg_fare FROM od_market").fetchall():
            d[(o, de, int(y))] = (float(pax or 0), float(fare or 0))
    finally:
        con.close()
    print(f"  DB1B: {len(d):,} directional pair-years loaded")
    return d


def load_casm(path):
    """(carrier, year) -> (casm_c, rasm_c, avg_stage_km)."""
    d = {}
    if not os.path.exists(path):
        print(f"  WARNING: casm store not found at {path}; CASM columns will be blank")
        return d
    con = _con(path)
    try:
        for car, y, casm, rasm, stage in con.execute(
                "SELECT carrier, year, casm_c, rasm_c, avg_stage_km FROM casm").fetchall():
            d[(car, int(y))] = (casm, rasm, stage)
    finally:
        con.close()
    print(f"  CASM: {len(d):,} carrier-years loaded")
    return d


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", required=True, help="backtest CSV to enrich (must have dep, arr, year, carrier, natural)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--db1b", default=r"C:\Avia\db1b.duckdb")
    ap.add_argument("--casm", default=r"C:\Avia\casm_benchmark.duckdb")
    ap.add_argument("--lag", type=int, default=1, help="pre-launch vintage: features read at launch year - LAG")
    a = ap.parse_args()

    print("Loading DOT stores...")
    db1b = load_db1b(a.db1b)
    casm = load_casm(a.casm)

    rows = list(csv.DictReader(open(a.spine, newline="")))
    if not rows:
        print("empty spine"); sys.exit(1)
    add_cols = ["db1b_market_v", "db1b_fare_v", "db1b_to_sabre",
                "carrier_casm_c", "carrier_rasm_c", "carrier_stage_km", "is_regional"]
    n_db1b = n_casm = 0
    for r in rows:
        dep, arr, car = r.get("dep"), r.get("arr"), r.get("carrier")
        yr = _f(r.get("year"))
        v = int(yr) - a.lag if yr else None
        # DB1B real US market at Y-lag, both directions
        m_v = f_v = ""
        if v is not None:
            ab = db1b.get((dep, arr, v)); ba = db1b.get((arr, dep, v))
            pax = (ab[0] if ab else 0) + (ba[0] if ba else 0)
            if pax > 0:
                wf = (ab[0] * ab[1] if ab else 0) + (ba[0] * ba[1] if ba else 0)
                m_v = round(pax); f_v = round(wf / pax, 2)
                n_db1b += 1
        r["db1b_market_v"] = m_v
        r["db1b_fare_v"] = f_v
        nat = _f(r.get("natural"))
        r["db1b_to_sabre"] = round(m_v / nat, 3) if (m_v != "" and nat and nat > 0) else ""
        # carrier economics at Y-lag
        cc = casm.get((car, v)) if v is not None else None
        if cc:
            r["carrier_casm_c"] = cc[0]; r["carrier_rasm_c"] = cc[1]; r["carrier_stage_km"] = cc[2]
            n_casm += 1
        else:
            r["carrier_casm_c"] = r["carrier_rasm_c"] = r["carrier_stage_km"] = ""
        r["is_regional"] = 1 if (car in REGIONAL_CODES) else 0

    fieldnames = list(rows[0].keys())
    for c in add_cols:
        if c not in fieldnames:
            fieldnames.append(c)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {a.out}  ({len(rows)} rows)")
    print(f"  DB1B market matched: {n_db1b}/{len(rows)} ({n_db1b/len(rows)*100:.0f}%, US pairs at Y-{a.lag})")
    print(f"  CASM matched:        {n_casm}/{len(rows)} ({n_casm/len(rows)*100:.0f}%)")
    print(f"  regional-flagged:    {sum(1 for r in rows if r['is_regional'])}/{len(rows)}")


if __name__ == "__main__":
    main()
