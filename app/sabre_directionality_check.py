#!/usr/bin/env python3
r"""
Avia Solutions - Sabre store directionality check, 15 August 2026.
==================================================================
WHY THIS EXISTS. The SJC-TPE acceptance run reads a catchment O&D market of
264,931 each way where the 11 August payload recorded 321,830 two-way, a 1.65x
inflation with no code change in the market path. The market query
(od_source.market_split -> sabre_catchment.destination_market_split) passes no
directionality filter, and the store carries years in POO or ND form. A
directional pair read means a different thing under each convention; an airport
total is identical under both, which is why the Route Watch trend for TPE looks
clean. This script prints what the store actually holds, so the mechanism is
named from the data rather than argued.

READ-ONLY. Three queries, a few seconds each on the workstation.
  1. Rows and passengers by source_year x directionality: which years hold
     which variant, and whether any year holds both.
  2. The SJC-TPE market as the engine reads it (origin IN service area, dest IN
     Taipei), by source_year x directionality, both directions separately.
     The service area is written out as SJC/SFO/OAK here as a diagnostic
     stand-in for the resolver's set; the point is the yearly shape, not the
     exact catchment.
  3. True-origin split (poo_country) on the pair for the two newest years:
     the US-originating share is what a POO directional read measures and an
     ND read does not, so this is the number that says whether 1.65x is the
     convention shift.

Run on the WORKSTATION (config resolves the store; AVIA_SABRE wins if set):
    cd C:\src\meridian
    py -3.12 app\sabre_directionality_check.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SERVICE_AREA = ("SJC", "SFO", "OAK")
DEST = ("TPE", "TSA")


def main():
    import duckdb
    try:
        import config as CFG
        db = os.environ.get("AVIA_SABRE", str(CFG.SABRE_DUCKDB))
    except Exception as e:
        print("config.py did not load (%s); set AVIA_SABRE to the store path" % e)
        return 1
    if not os.path.exists(db):
        print("Sabre store not at %s" % db)
        return 1
    con = duckdb.connect(db, read_only=True)
    try:
        try:
            from db_registry import apply_limits
            apply_limits(con)
        except Exception:
            pass

        print("=== 1. Store contents by source_year x directionality ===")
        print("%-6s %-6s %14s %16s" % ("year", "dir", "rows", "passengers"))
        for y, d, n, p in con.execute(
                "SELECT source_year, COALESCE(directionality,'?'), COUNT(*), "
                "SUM(passengers) FROM sabre GROUP BY 1,2 ORDER BY 1,2").fetchall():
            print("%-6s %-6s %14s %16s" % (y, d, "{:,}".format(int(n or 0)),
                                           "{:,}".format(int(p or 0))))

        aph = ",".join("?" * len(SERVICE_AREA))
        dph = ",".join("?" * len(DEST))
        print("\n=== 2. Bay Area <-> Taipei pair by year x directionality ===")
        print("(engine's market read is the out direction, unfiltered on dir)")
        print("%-6s %-6s %16s %16s" % ("year", "dir", "out SJC/SFO/OAK", "back from TPE"))
        out_rows = con.execute(
            f"SELECT source_year, COALESCE(directionality,'?'), SUM(passengers) "
            f"FROM sabre WHERE origin_airport IN ({aph}) AND destination_airport IN ({dph}) "
            f"GROUP BY 1,2", [*SERVICE_AREA, *DEST]).fetchall()
        back_rows = con.execute(
            f"SELECT source_year, COALESCE(directionality,'?'), SUM(passengers) "
            f"FROM sabre WHERE origin_airport IN ({dph}) AND destination_airport IN ({aph}) "
            f"GROUP BY 1,2", [*DEST, *SERVICE_AREA]).fetchall()
        back = {(y, d): p for y, d, p in back_rows}
        for y, d, p in sorted(out_rows):
            b = back.get((y, d), 0)
            print("%-6s %-6s %16s %16s" % (y, d, "{:,}".format(int(p or 0)),
                                           "{:,}".format(int(b or 0))))

        print("\n=== 3. True-origin split on the pair, two newest years ===")
        print("(a POO directional read measures the US-originating share; ND reads a flat half)")
        years = [r[0] for r in con.execute(
            "SELECT DISTINCT source_year FROM sabre ORDER BY 1 DESC LIMIT 2").fetchall()]
        for y in years:
            rows = con.execute(
                f"SELECT COALESCE(poo_country,'?'), SUM(passengers) FROM sabre "
                f"WHERE source_year = ? AND ((origin_airport IN ({aph}) AND "
                f"destination_airport IN ({dph})) OR (origin_airport IN ({dph}) AND "
                f"destination_airport IN ({aph}))) GROUP BY 1 ORDER BY 2 DESC LIMIT 6",
                [y, *SERVICE_AREA, *DEST, *DEST, *SERVICE_AREA]).fetchall()
            tot = sum(float(p or 0) for _c, p in rows) or 1.0
            print("  %s:  " % y + "  ".join(
                "%s %s (%.0f%%)" % (c, "{:,}".format(int(p or 0)), 100.0 * float(p or 0) / tot)
                for c, p in rows))
        print("\nSource: the Sabre store at %s, read only, this run." % db)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
