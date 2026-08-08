#!/usr/bin/env python3
r"""Verify aci.duckdb after a build. Reads only, writes nothing.

    py -3.12 check_aci.py
    py -3.12 check_aci.py EDI LHR AUS INV
    py -3.12 check_aci.py --db C:\Avia\aci.duckdb --from 2015

The ACI workbook is maintained by hand and refreshed monthly, so this is run
after every rebuild, not once. What it answers:

  * what the store says about itself: measure, vintage, source file
  * how many airports and months are in it
  * for each named airport, the year, the months actually reported, and the
    total. A year showing fewer than twelve months is NOT a partial airport,
    it is an airport that did not report every month, and the deck must not
    draw it as though it were a whole year.
  * how much of the store is whole years at all, which sets expectations for
    how often a chart will legitimately refuse to draw

It does not judge whether a figure is right. That is an eye check against the
airport's published annual total, which is the point of printing the years.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import os
import sys

DEFAULT_CODES = ["LHR", "EDI", "AUS", "INV", "BHD", "TLL"]


def resolve_db(explicit):
    if explicit:
        return explicit
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import config as CFG
        return str(CFG.ACI_DUCKDB)
    except Exception:
        return "aci.duckdb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("codes", nargs="*", default=[], help="IATA codes to detail")
    ap.add_argument("--db", default="", help="path to aci.duckdb")
    ap.add_argument("--from", dest="from_year", type=int, default=2015)
    a = ap.parse_args()

    db = resolve_db(a.db)
    if not os.path.exists(db):
        raise SystemExit("no store at %s. Build it with load_aci.py first." % db)
    import duckdb
    con = duckdb.connect(db, read_only=True)

    print("STORE %s" % db)
    meta = dict(con.execute("SELECT key, value FROM _store_meta").fetchall())
    for k in ("measure", "source_file", "source_modified", "built"):
        print("   %-16s %s" % (k, meta.get(k, "?")))

    n_apt, n_row, y0, y1 = con.execute(
        "SELECT COUNT(DISTINCT iata), COUNT(*), MIN(year), MAX(year) "
        "FROM aci_monthly").fetchone()
    print("   %-16s %s airports, %s airport-months, %s to %s"
          % ("size", "{:,}".format(n_apt), "{:,}".format(n_row), y0, y1))

    # How much of the store is a whole year. This is the number that decides how
    # often a chart legitimately refuses, so it is better known than discovered.
    whole, total = con.execute(
        "SELECT SUM(CASE WHEN months_reported = 12 THEN 1 ELSE 0 END), COUNT(*) "
        "FROM aci_coverage").fetchone()
    print("   %-16s %s of %s airport-years are complete twelve months (%.0f%%)"
          % ("completeness", "{:,}".format(int(whole)), "{:,}".format(total),
             100.0 * whole / total if total else 0))

    codes = [c.strip().upper() for c in (a.codes or DEFAULT_CODES)]
    # The airport name is printed because it is the chart caption. The first
    # build named every UK airport "United Kingdom", which no test caught and
    # no query complained about; it was visible only by reading it.
    print("\nSUMMARY  (full = years with all twelve months reported)")
    print("   %-6s %-6s %-11s %-6s %-24s %s"
          % ("code", "years", "span", "full", "airport", "country"))
    for code in codes:
        row = con.execute(
            "SELECT COUNT(*), MIN(year), MAX(year), "
            "       SUM(CASE WHEN months_reported = 12 THEN 1 ELSE 0 END) "
            "FROM aci_coverage WHERE iata = ?", [code]).fetchone()
        if not row or not row[0]:
            print("   %-6s not in the store" % code)
            continue
        who = con.execute("SELECT airport, country FROM aci_monthly "
                          "WHERE iata = ? LIMIT 1", [code]).fetchone()
        print("   %-6s %-6s %-11s %-6s %-24s %s"
              % (code, row[0], "%s-%s" % (row[1], row[2]), int(row[3] or 0),
                 (who[0] if who else ""), (who[1] if who else "")))

    for code in codes:
        rows = con.execute(
            "SELECT year, months_reported, passengers FROM aci_coverage "
            "WHERE iata = ? AND year >= ? ORDER BY year",
            [code, a.from_year]).fetchall()
        if not rows:
            continue
        print("\n%s, %d onwards" % (code, a.from_year))
        for year, months, pax in rows:
            flag = "" if months == 12 else "   <- %d months, not a whole year" % months
            print("   %d   %2d months   %6.2fm%s" % (year, months, pax / 1e6, flag))

    con.close()


if __name__ == "__main__":
    main()
