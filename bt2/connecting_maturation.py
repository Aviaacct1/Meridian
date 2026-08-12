"""Does a route's connecting traffic still be building in its first full year?

THE QUESTION, and it is about the RULER rather than the feed. Meridian forecasts a MATURITY year:
cortex_app's forecast_year defaults to the base data year plus one and every SJC-TPE client case runs
2027 or 2028. The back-test grades at --offset 1, the route's FIRST FULL YEAR, when an airline has
not yet built or sold its connecting itineraries. If connecting traffic matures over two or three
years then outturn_pax less p2p_outturn at L+1 is systematically short of what a maturity-year
forecast should show, and RECUT-RESULT's finding that the shipped feed over-reads by circa ten times
is partly an artefact of grading a mature forecast against an immature year.

That is GRADE-BASIS arriving on the connecting side, and it bears on the P2P leg and on the
published accuracy as much as on the feed, so both legs are reported here.

WHAT IT DOES. It runs NO forecast and NO engine. For each route the arm already graded it reads
Sabre at the launch year plus one, plus two and plus three, through the preagg store's indexed
od_p2p and sector_adj tables, and reports connecting as sector less pure P2P at each horizon. The
question is then one ratio: connecting at Y2 over connecting at Y1 on the same route.

WHAT IT CANNOT COVER, and the sample is stated before any number is read. Sabre stops at 2025 and
2020 to 2022 are unusable, so the horizons available are not the same for every cohort:

    cohort 2016   Y1 2017, Y2 2018, Y3 2019     all three clean
    cohort 2017   Y1 2018, Y2 2019, Y3 2020     Y3 DROPPED, COVID
    cohort 2018   Y1 2019, Y2 2020, Y3 2021     Y2 and Y3 DROPPED, COVID
    cohort 2024   Y1 2025, Y2 2026, Y3 2027     Y2 and Y3 DROPPED, no Sabre

So the maturation ratio can only be measured on cohorts 2016 and 2017, and the three-point series
only on 2016. It says nothing about the 2018 or 2024 cohorts and must not be read across to them:
2024 in particular is a post-COVID cohort with 248 reinstatements, whose connecting traffic may
mature on a quite different curve from a 2016 launch.

A ROUTE IS ONLY COUNTED WHERE BOTH HORIZONS ARE POSITIVE. A route carrying no connecting traffic in
its first year is not a maturation observation, it is a route with no connecting traffic, and
dividing by it is the ratio-against-zero trap this log has already recorded once.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

# Grading years that cannot be used. 2020 to 2022 are COVID and its recovery, which the --years help
# already excludes as launch years; they are excluded here as GRADING years, which is the distinction
# BACKTEST-YEARS of 12 August records the arm getting wrong in the other direction.
BAD_YEARS = {2020, 2021, 2022}
SABRE_LAST = 2025


def parse_args():
    p = argparse.ArgumentParser(description="Connecting traffic at Y+1, Y+2 and Y+3 per route.")
    p.add_argument("--arm", required=True, help="a backtest.py arm CSV, for the route list")
    p.add_argument("--preagg", default=r"E:\Avia\preagg.duckdb", help="the preagg store")
    p.add_argument("--sabre", default=os.environ.get("AVIA_SABRE"),
                   help="the Sabre store, used only if the preagg store lacks a sector table")
    p.add_argument("--min-pax", type=float, default=100.0,
                   help="ignore a horizon whose connecting figure is below this, default 100")
    p.add_argument("--out", default=None, help="write the per-route rows to this CSV")
    return p.parse_args()


def _usable(y):
    return 2015 <= y <= SABRE_LAST and y not in BAD_YEARS


def _sector_by_pair(sabre, rows, usable):
    """Sector traffic for every pinned pair and needed year, ONE GROUPED PASS PER YEAR.

    build_preagg.SQL_SECTOR_ADJ verbatim, including the DISTINCT on (year, rid, pax) that counts an
    itinerary once per distinct pair rather than once per leg occurrence, then joined to the pin
    pairs. Per year rather than all at once because the explosion is up to four rows per itinerary
    and a 16GB box has been caught by that before; a year at a time is bounded and shows progress.
    """
    import time
    import duckdb

    pins, years = set(), set()
    for r in rows:
        dep, arr = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
        try:
            L = int(float(r.get("year")))
        except (TypeError, ValueError):
            continue
        if not dep or not arr:
            continue
        pins.add((min(dep, arr), max(dep, arr)))
        for h in (1, 2, 3):
            if usable(L + h):
                years.add(L + h)
    print("sector leg-explosion: %d pinned pairs over years %s"
          % (len(pins), ", ".join(str(y) for y in sorted(years))))

    con = duckdb.connect(sabre, read_only=True)
    try:
        try:
            from db_registry import apply_limits
            apply_limits(con)          # memory cap and a named temp directory, per the run rules
        except Exception:              # noqa: BLE001
            con.execute("SET memory_limit='8GB'")
        con.execute("CREATE TEMP TABLE pins(u VARCHAR, v VARCHAR)")
        con.executemany("INSERT INTO pins VALUES (?,?)", sorted(pins))
        con.execute("CREATE TEMP TABLE aps AS SELECT u AS a FROM pins UNION SELECT v FROM pins")

        # rowid is only exposed on BASE tables, which build_preagg's own comment records, and it is
        # what makes the DISTINCT count an itinerary once. If sabre is a view in this store the
        # explosion would double-count a two-leg itinerary onto the same pair, so the fallback is
        # named rather than silent.
        try:
            con.execute("SELECT rowid FROM sabre LIMIT 1").fetchone()
            rid = "rowid"
        except Exception:                                  # noqa: BLE001
            rid = "ROW_NUMBER() OVER ()"
            print("   sabre exposes no rowid (a view?), using a window row number instead")

        sql = """
        WITH r AS (
            SELECT source_year AS year, %s AS rid, CAST(passengers AS DOUBLE) AS pax,""" % rid + """
                   origin_airport AS o, destination_airport AS d,
                   NULLIF(connecting_airport1, '') AS c1,
                   NULLIF(connecting_airport2, '') AS c2,
                   NULLIF(connecting_airport3, '') AS c3
            FROM sabre
            WHERE source_year = ?
              AND (origin_airport IN (SELECT a FROM aps)
                OR destination_airport IN (SELECT a FROM aps)
                OR connecting_airport1 IN (SELECT a FROM aps)
                OR connecting_airport2 IN (SELECT a FROM aps)
                OR connecting_airport3 IN (SELECT a FROM aps))
        ),
        legs AS (
            SELECT year, rid, pax, o  AS f, COALESCE(c1, d) AS t FROM r
            UNION ALL
            SELECT year, rid, pax, c1 AS f, COALESCE(c2, d) AS t FROM r WHERE c1 IS NOT NULL
            UNION ALL
            SELECT year, rid, pax, c2 AS f, COALESCE(c3, d) AS t FROM r WHERE c2 IS NOT NULL
            UNION ALL
            SELECT year, rid, pax, c3 AS f, d              AS t FROM r WHERE c3 IS NOT NULL
        ),
        pr AS (
            SELECT DISTINCT year, rid, pax, LEAST(f, t) AS u, GREATEST(f, t) AS v
            FROM legs WHERE f IS NOT NULL AND t IS NOT NULL
        )
        SELECT pr.year, pr.u, pr.v, SUM(pr.pax)
        FROM pr JOIN pins ON pins.u = pr.u AND pins.v = pr.v
        GROUP BY 1, 2, 3"""

        out = {}
        for y in sorted(years):
            t0 = time.time()
            for yr, u, v, pax in con.execute(sql, [y]).fetchall():
                out[(u, v, int(yr))] = float(pax or 0)
            print("   %d: %6.1fs, %d pair rows so far" % (y, time.time() - t0, len(out)))
        return out
    finally:
        con.close()


def _summarise(name, pairs):
    """pairs is a list of (earlier, later). Reports the ratio later/earlier."""
    r = sorted(later / earlier for earlier, later in pairs if earlier > 0 and later > 0)
    if not r:
        print("   %-34s no routes with both horizons positive" % name)
        return None
    def q(p):
        return r[min(int(p * (len(r) - 1) + 0.5), len(r) - 1)]
    print("   %-34s n=%5d  median %5.3f  IQR %5.3f to %5.3f  share rising %4.1f%%"
          % (name, len(r), statistics.median(r), q(0.25), q(0.75),
             100.0 * sum(1 for x in r if x > 1.0) / len(r)))
    return statistics.median(r)


def main():
    a = parse_args()
    if not os.path.exists(a.arm):
        sys.exit("arm CSV not found: %r" % a.arm)

    import preagg
    store = a.preagg if (a.preagg and preagg.available(a.preagg)) else None
    if store is None:
        sys.exit("preagg store not usable: %r. Build it with build_preagg.py rather than "
                 "full-scanning Sabre 9,000 times." % a.preagg)
    # od_p2p is present (preagg.available checks for it), so the local leg is an indexed lookup.
    # sector_adj is optional and this store was built with --skip-sector, so the connecting leg is
    # computed here instead, ONE GROUPED PASS PER YEAR rather than one full scan per route. The
    # explosion is build_preagg's SQL_SECTOR_ADJ verbatim, including its DISTINCT on (year, rid,
    # pax), which counts an itinerary ONCE per distinct pair rather than once per leg occurrence.
    # Reproducing that exactly is the point: a different counting rule here would produce a number
    # that cannot be held against anything else in this programme.
    sector = None if preagg.has_sector(store) else {}

    with open(a.arm, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("arm %s: %d rows" % (os.path.basename(a.arm), len(rows)))
    # SAY WHICH PATH RAN. This line read "sector table present" unconditionally on its first outing,
    # which is the label-asserting-what-the-code-did-not-check fault recorded three times today in
    # other files and once, here, in mine.
    print("preagg %s, sector_adj %s" % (os.path.basename(store),
                                        "present, using it" if sector is None
                                        else "ABSENT, computing the connecting leg here"))

    if sector is not None:
        sector = _sector_by_pair(a.sabre, rows, _usable)

    seen, out = set(), []
    for r in rows:
        dep, arr = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
        try:
            L = int(float(r.get("year")))
        except (TypeError, ValueError):
            continue
        if not dep or not arr or (dep, arr, L) in seen:
            continue
        seen.add((dep, arr, L))
        rec = {"route": r.get("route", "%s-%s" % (dep, arr)), "dep": dep, "arr": arr, "cohort": L,
               "type": r.get("type", ""), "gcd_km": r.get("gcd_km", "")}
        for h in (1, 2, 3):
            y = L + h
            if not _usable(y):
                rec["p2p_y%d" % h] = ""
                rec["cnx_y%d" % h] = ""
                rec["why_y%d" % h] = ("covid" if y in BAD_YEARS else "no sabre")
                continue
            p2p = preagg.p2p_traffic(store, dep, arr, y)
            if sector is None:
                sec = preagg.sector_traffic(store, dep, arr, y)
            else:
                sec = sector.get((min(dep, arr), max(dep, arr), y), 0.0)
            cnx = sec - p2p
            rec["p2p_y%d" % h] = round(p2p)
            # RULER-SOUND checked that total outturn is never below pure P2P on the graded year. It
            # is checked again here rather than assumed, because this reads two further years the
            # earlier check never looked at.
            rec["cnx_y%d" % h] = round(cnx) if cnx >= 0 else ""
            # THE MAGNITUDE IS CARRIED, not just the flag. On the first run 163 route-years of circa
            # 9,216 read sector below pure P2P, which is impossible, and RULER-SOUND found ZERO of
            # 3,072 on the graded year. The difference is that the arm built BOTH quantities from
            # one source while this mixes preagg's od_p2p with the explosion computed here, so a
            # small negative is a rounding difference between two builds and a large one is a basis
            # mismatch. Without the size nobody can tell which, so it is written out.
            rec["why_y%d" % h] = "" if cnx >= 0 else "sector below p2p by %d" % round(-cnx)
        out.append(rec)

    negs = [float(str(r.get("why_y%d" % h)).rsplit(" ", 1)[-1])
            for r in out for h in (1, 2, 3)
            if str(r.get("why_y%d" % h) or "").startswith("sector below p2p")]
    print("%d routes, %d route-years where sector read below pure P2P (impossible, and excluded)"
          % (len(out), len(negs)))
    if negs:
        n = sorted(negs)
        print("   shortfall in passengers: median %d, p90 %d, max %d. A handful of passengers is a"
              % (n[len(n) // 2], n[min(int(0.9 * len(n)), len(n) - 1)], n[-1]))
        print("   rounding difference between two builds; thousands is a basis mismatch between")
        print("   preagg's od_p2p and the explosion computed here, and would need settling first.")

    def pick(r, h):
        v = r.get("cnx_y%d" % h)
        return float(v) if (v not in ("", None) and float(v) >= a.min_pax) else None

    print("\nCONNECTING TRAFFIC, later year over earlier, same route. Above 1.0 it is still building.")
    for label, hs in (("Y2 over Y1, all cohorts", (1, 2)), ("Y3 over Y1, all cohorts", (1, 3)),
                      ("Y3 over Y2, all cohorts", (2, 3))):
        _summarise(label, [(pick(r, hs[0]), pick(r, hs[1])) for r in out
                           if pick(r, hs[0]) and pick(r, hs[1])])

    print("\nBY COHORT, because only 2016 and 2017 can answer this at all.")
    for L in sorted({r["cohort"] for r in out}):
        sub = [r for r in out if r["cohort"] == L]
        _summarise("cohort %d, Y2 over Y1" % L,
                   [(pick(r, 1), pick(r, 2)) for r in sub if pick(r, 1) and pick(r, 2)])

    print("\nTHE P2P LEG ON THE SAME ROUTES, for comparison. GRADE-BASIS lists the grading year as")
    print("one of the three differences worth 33 points, and it applies to the local leg too.")

    def pickp(r, h):
        v = r.get("p2p_y%d" % h)
        return float(v) if (v not in ("", None) and float(v) >= a.min_pax) else None

    for label, hs in (("P2P, Y2 over Y1", (1, 2)), ("P2P, Y3 over Y1", (1, 3))):
        _summarise(label, [(pickp(r, hs[0]), pickp(r, hs[1])) for r in out
                           if pickp(r, hs[0]) and pickp(r, hs[1])])

    print("\nHOW TO READ THIS. If connecting rises materially from Y1 to Y2 while P2P is flat, the")
    print("back-test's grading year is the wrong ruler for the connecting leg specifically, and")
    print("RECUT-RESULT's tenfold over-read is partly an artefact of it. If BOTH legs rise together")
    print("the whole grading basis is early rather than the feed being wrong. If neither rises, the")
    print("ruler is sound and RECUT-RESULT stands as measured.")
    print("A median near 1.0 with a wide IQR is not evidence of stability; it is evidence that")
    print("route-level connecting traffic moves a lot year to year, which is its own finding.")

    if a.out:
        cols = ["route", "dep", "arr", "cohort", "type", "gcd_km"] + [
            "%s_y%d" % (p, h) for h in (1, 2, 3) for p in ("p2p", "cnx", "why")]
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(out)
        print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
