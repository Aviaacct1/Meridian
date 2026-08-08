#!/usr/bin/env python3
r"""Inspect the US DOT T-100 store before anything reads it. Read only.

    py -3.12 check_t100.py --db "E:\Avia\Usmarket data\t100.duckdb"
    py -3.12 check_t100.py --db "..." --airport AUS

WHY THIS EXISTS, from BT2_BACKTEST_PROGRAMME.md, 5 August 2026: the T-100 store
is DOUBLE-LOADED. 753k rows against 375k distinct, which gave 1,571m onboard
passengers for 2018 against a sane 786m once deduplicated. Every census
comparison run before deduplication overstated onboard by 2x.

So nothing reads this store until it has been asked how many rows it holds and
how many of them are distinct. This reports the ratio, names the key it tested
for distinctness, and prints one airport's series both ways so the size of the
error is visible rather than remembered.

It writes nothing and it does not fix the store. Whether the answer is to rebuild
the store or to deduplicate on read is a decision, not a default.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The columns a T-100 segment table plausibly uses, in the order they are tried.
APT = ("origin", "origin_airport", "apt", "airport", "iata", "origin_code")
PAX = ("passengers", "pax", "onboard", "total_passengers", "transported")
SEATS = ("seats", "seats_available", "capacity")
YEAR = ("year", "yr")
MONTH = ("month", "mon", "period")


def pick(cols, names):
    return next((c for c in names if c in cols), None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="", help="path to t100.duckdb")
    ap.add_argument("--airport", default="AUS")
    a = ap.parse_args()

    db = a.db
    if not db:
        try:
            import config as CFG
            db = str(CFG.T100_DUCKDB)
        except Exception as e:
            raise SystemExit("config.py did not load (%s); pass --db" % e)
    if not os.path.exists(db):
        raise SystemExit("no store at %s" % db)

    import duckdb
    con = duckdb.connect(db, read_only=True)
    print("STORE %s   %.0f MB" % (db, os.path.getsize(db) / 1e6))

    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    print("   tables           %s" % ", ".join(tables))

    for t in tables:
        cols = [(r[1], r[2]) for r in
                con.execute("PRAGMA table_info('%s')" % t).fetchall()]
        names = {c.lower() for c, _ty in cols}
        n = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("\nTABLE %s   %s rows" % (t, "{:,}".format(n)))
        print("   columns          %s" % ", ".join(c for c, _ty in cols))

        # THE DUPLICATION TEST. Distinct across every column: if the store was
        # loaded twice, whole rows repeat, so this is the honest test and it
        # needs no knowledge of what the key is meant to be.
        try:
            d = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM %s)"
                            % t).fetchone()[0]
        except Exception as e:
            print("   distinct rows    could not be counted (%s)" % e)
            continue
        print("   distinct rows    %s" % "{:,}".format(d))
        # A handful of repeated rows in millions is not a double load, and
        # shouting about a "factor of 1.00" reads as a fault where there is
        # none. The alarm is reserved for a factor that would actually
        # misstate a total; anything smaller is reported as what it is.
        factor = (float(n) / d) if d else 1.0
        if factor >= 1.02:
            print("   *** DOUBLE LOADED: %s rows for %s distinct, a factor of "
                  "%.2f. Every passenger and seat total from this table is "
                  "overstated by that factor until it is deduplicated. ***"
                  % ("{:,}".format(n), "{:,}".format(d), factor))
        elif n > d:
            print("   near clean       %s exact duplicate row%s, %.3f%% of the "
                  "table. Not a double load. Worth knowing, not worth a "
                  "correction factor."
                  % ("{:,}".format(n - d), "" if n - d == 1 else "s",
                     100.0 * (n - d) / n))
        elif n:
            print("   clean            every row is distinct")

        apt = pick(names, APT)
        pax = pick(names, PAX)
        seats = pick(names, SEATS)
        yr = pick(names, YEAR)
        if not (apt and pax and yr):
            print("   NOT READABLE as an airport passenger series: found "
                  "airport=%s passengers=%s year=%s" % (apt, pax, yr))
            continue
        print("   reads as         airport=%s passengers=%s seats=%s year=%s"
              % (apt, pax, seats, yr))

        code = a.airport.upper()

        # T-100 segment carries scheduled and non-scheduled service in one
        # table. OAG seats are SCHEDULED, so summing every class against them
        # inflates the load factor by whatever charter the airport does. The
        # codes are printed rather than assumed, because picking a filter from
        # memory is how the wrong one gets shipped.
        if "class" in names:
            print("\n   service class at %s, so the right filter can be chosen"
                  % code)
            cls = con.execute(
                "SELECT class, COUNT(*), SUM(TRY_CAST(%s AS DOUBLE)), "
                "       SUM(TRY_CAST(%s AS DOUBLE)) "
                "FROM %s WHERE UPPER(TRIM(%s)) = ? GROUP BY 1 ORDER BY 3 DESC"
                % (pax, seats or pax, t, apt), [code]).fetchall()
            tot = sum((r[2] or 0) for r in cls) or 1.0
            print("      %-8s %-12s %-16s %-16s %s"
                  % ("class", "rows", "passengers", "seats", "share of pax"))
            for c, nrow, p, s in cls:
                print("      %-8s %-12s %-16s %-16s %.1f%%"
                      % (c, "{:,}".format(nrow), "{:,.0f}".format(p or 0),
                         "{:,.0f}".format(s or 0), 100.0 * (p or 0) / tot))
        raw = con.execute(
            "SELECT %s AS y, SUM(TRY_CAST(%s AS DOUBLE)) FROM %s "
            "WHERE UPPER(TRIM(%s)) = ? GROUP BY 1 ORDER BY 1"
            % (yr, pax, t, apt), [code]).fetchall()
        ded = con.execute(
            "SELECT %s AS y, SUM(TRY_CAST(%s AS DOUBLE)) FROM "
            "(SELECT DISTINCT * FROM %s) WHERE UPPER(TRIM(%s)) = ? "
            "GROUP BY 1 ORDER BY 1" % (yr, pax, t, apt), [code]).fetchall()
        if not raw:
            print("   %s is not in this table" % code)
            continue
        dd = dict(ded)
        print("\n   %s, departing onboard passengers" % code)
        print("      %-6s %-16s %-16s %s" % ("year", "as stored", "deduplicated",
                                             "ratio"))
        for y, v in raw:
            w = dd.get(y)
            print("      %-6s %-16s %-16s %s"
                  % (y, "{:,.0f}".format(v or 0),
                     "{:,.0f}".format(w or 0) if w else "-",
                     "%.2f" % (v / w) if w else "-"))

    con.close()


if __name__ == "__main__":
    main()
