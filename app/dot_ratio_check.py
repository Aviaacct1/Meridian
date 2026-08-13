#!/usr/bin/env python3
r"""
Avia Solutions - DOT against Sabre, on all three quantities.
============================================================
THE QUESTION THIS ANSWERS. DEFAULT_CONN_CAPTURE and behind_cap were calibrated against
Sabre-measured markets. od_source now reads DB1B for the all-US pairs of a feed scope,
so the day AVIA_OD_SOURCE moves off sabre the feed forecast moves by the DB1B-to-Sabre
ratio on those pairs, before any method changes at all. That ratio has never been
measured on the CONNECTING quantity, because until 15 August 2026 the connecting
quantity did not exist in the DOT store.

WHAT IT COMPARES, on matched pairs and one year:

    nonstop      DB1B MktCoupons = 1   against Sabre connecting_airport1 IS NULL
    connecting   DB1B MktCoupons = 2   against Sabre c1 IS NOT NULL AND c2 IS NULL
    total        every DB1B coupon     against every Sabre itinerary

The three ratios are the finding. If connecting and nonstop come back close, Sabre's
coverage gap is flat and capture can be re-levelled by one number. If connecting comes
back materially higher, Sabre is under-reading TRANSFER traffic specifically, which is
a different correction and bears on the 19% gap against the 2025 analyst.

BOTH SIDES ARE ON THEIR OWN BASIS AND NEITHER IS ADJUSTED. No factor_indirect, no
capture, no grossing beyond the x10 already in the store. Pairs present in one source
and not the other are counted and reported separately rather than dropped in silence,
because a coverage difference IS the measurement here.

Usage (workstation):
    py -3.12 dot_ratio_check.py --year 2024 --airport SJC
    py -3.12 dot_ratio_check.py --year 2024 --airport SJC,TPA,ORD
    py -3.12 dot_ratio_check.py --year 2024 --airport SJC --top 20
"""
import argparse
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def _paths(args):
    coupons, sabre = args.coupons, args.sabre
    try:
        import config
        coupons = coupons or str(config.DB1B_COUPONS_DUCKDB)
        sabre = sabre or str(config.SABRE_DUCKDB)
    except Exception:
        pass
    return coupons, sabre


def _ratio(dot, sab):
    return (dot / sab) if sab else None


def _fmt_ratio(r):
    return "n/a" if r is None else f"{r:.3f}x"


def main():
    ap = argparse.ArgumentParser(description="DB1B against Sabre on nonstop, connecting and total.")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--airport", required=True,
                    help="one or more IATA codes; every pair touching them is compared")
    ap.add_argument("--coupons", default=None)
    ap.add_argument("--sabre", default=None)
    ap.add_argument("--top", type=int, default=10, help="worst-divergence pairs to list")
    ap.add_argument("--all-pairs", action="store_true",
                    help="do not restrict to US-to-US pairs. The first run of this tool did not "
                         "restrict, and its 6,031 Sabre-only pairs were mostly international rather "
                         "than a DB1B coverage gap. Kept as a switch, not as the default.")
    ap.add_argument("--memory", default="4GB")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--temp", default=None)
    args = ap.parse_args()

    coupons, sabre = _paths(args)
    for label, path in (("coupons", coupons), ("sabre", sabre)):
        if not path or not os.path.exists(path):
            print(f"ERROR: {label} store not found: {path}")
            return 2

    codes = [c.strip().upper() for c in args.airport.split(",") if c.strip()]
    ph = ",".join("?" * len(codes))

    import duckdb
    cfg = {"memory_limit": args.memory, "threads": str(args.threads)}
    if args.temp:
        os.makedirs(args.temp, exist_ok=True)
        cfg["temp_directory"] = args.temp
    con = duckdb.connect(coupons, read_only=True, config=cfg)
    try:
        con.execute("ATTACH '" + sabre.replace("'", "''") + "' AS sb (READ_ONLY)")

        # A year the coupon store did not build in full cannot be compared.
        built = con.execute("SELECT count(*) FROM build_log WHERE year=? AND status='built'",
                            [args.year]).fetchone()[0]
        if built != 4:
            print(f"REFUSED: {args.year} has {built} of 4 quarters built in the coupon store. "
                  f"A short year read as a full one under-states every market in it.")
            return 2

        dot_sql = f"""
            SELECT origin AS o, dest AS d,
                   SUM(pax) FILTER (WHERE coupons = 1) AS ns,
                   SUM(pax) FILTER (WHERE coupons = 2) AS cx,
                   SUM(pax) AS tot
            FROM od_market_coupons
            WHERE year = ? AND (origin IN ({ph}) OR dest IN ({ph}))
            GROUP BY 1, 2
        """
        sab_sql = f"""
            SELECT origin_airport AS o, destination_airport AS d,
                   SUM(passengers) FILTER (
                       WHERE connecting_airport1 IS NULL OR TRIM(connecting_airport1) = '') AS ns,
                   SUM(passengers) FILTER (
                       WHERE connecting_airport1 IS NOT NULL AND connecting_airport2 IS NULL) AS cx,
                   SUM(passengers) AS tot
            FROM sb.sabre
            WHERE source_year = ? AND (origin_airport IN ({ph}) OR destination_airport IN ({ph}))
            GROUP BY 1, 2
        """
        params = [args.year, *codes, *codes]
        con.execute(f"CREATE TEMP TABLE dot AS {dot_sql}", params)
        con.execute(f"CREATE TEMP TABLE sab AS {sab_sql}", params)

        # DB1B IS DOMESTIC ONLY, so every airport in the coupon store is a US airport and the
        # store is its own US list. Without this the Sabre side carries ORD-LHR and every other
        # international pair, and they present as DB1B blindness when they are out of scope.
        # KNOWN LIMIT, stated because it cuts the wrong way. The US list is "every airport DB1B has
        # ever seen", which by construction EXCLUDES the commuter and EAS tail DB1B is blind to.
        # Those are precisely the pairs od_source's auto mode falls back to Sabre for, so this
        # filter removes some genuine coverage gap along with the international noise and the
        # Sabre-only figure below is a floor rather than the whole of it.
        if not args.all_pairs:
            con.execute("CREATE TEMP TABLE us AS SELECT DISTINCT origin AS a FROM od_market_coupons "
                        "UNION SELECT DISTINCT dest FROM od_market_coupons")
            for t in ("dot", "sab"):
                con.execute(f"DELETE FROM {t} WHERE o NOT IN (SELECT a FROM us) "
                            f"OR d NOT IN (SELECT a FROM us)")

        matched = con.execute("""
            SELECT count(*),
                   SUM(dot.ns), SUM(sab.ns), SUM(dot.cx), SUM(sab.cx), SUM(dot.tot), SUM(sab.tot)
            FROM dot JOIN sab ON dot.o = sab.o AND dot.d = sab.d
        """).fetchone()
        only_dot = con.execute("""
            SELECT count(*), SUM(dot.tot) FROM dot
            LEFT JOIN sab ON dot.o = sab.o AND dot.d = sab.d WHERE sab.o IS NULL
        """).fetchone()
        only_sab = con.execute("""
            SELECT count(*), SUM(sab.tot) FROM sab
            LEFT JOIN dot ON dot.o = sab.o AND dot.d = sab.d WHERE dot.o IS NULL
        """).fetchone()

        n, dns, sns, dcx, scx, dtot, stot = [x or 0 for x in matched]
        print(f"Year {args.year}, pairs touching {', '.join(codes)}")
        print(f"Coupon store: {coupons}")
        print(f"Sabre store:  {sabre}\n")
        print(f"  Matched pairs: {n:,}")
        print(f"  DOT only:      {only_dot[0]:,} pairs, {(only_dot[1] or 0):,.0f} passengers")
        print(f"  Sabre only:    {only_sab[0]:,} pairs, {(only_sab[1] or 0):,.0f} passengers\n")
        print(f"  {'quantity':<12} {'DOT':>16} {'Sabre':>16} {'ratio':>10}")
        for label, dv, sv in (("nonstop", dns, sns), ("connecting", dcx, scx), ("total", dtot, stot)):
            print(f"  {label:<12} {dv:>16,.0f} {sv:>16,.0f} {_fmt_ratio(_ratio(dv, sv)):>10}")

        r_ns, r_cx = _ratio(dns, sns), _ratio(dcx, scx)
        if r_ns and r_cx:
            print(f"\n  Connecting against nonstop: {r_cx / r_ns:.3f}x. Above 1 means Sabre's "
                  f"under-read is concentrated in transfer traffic;\n  near 1 means the coverage "
                  f"gap is flat and capture can be re-levelled by one number.")

        # THE CUT THAT GOVERNS THE FEED. The feed legs read the connecting market on
        # feeder-to-destination pairs, which are pairs people connect over BECAUSE there is little
        # or no nonstop. An aggregate connecting ratio is dominated by dense nonstop pairs and is
        # therefore the wrong statistic for the question, in the same way a median was the wrong
        # statistic for a cap. Nonstop share is taken from DOT, the reference side.
        print("\n  Connecting ratio by how much nonstop service the pair has (DOT nonstop share):")
        print(f"    {'pairs with':<26} {'n':>7} {'DOT conn':>14} {'Sabre conn':>14} {'ratio':>9}")
        cuts = [("no nonstop at all", "d_ns_share = 0"),
                ("under 10% nonstop", "d_ns_share > 0 AND d_ns_share < 0.10"),
                ("10% to 50% nonstop", "d_ns_share >= 0.10 AND d_ns_share < 0.50"),
                ("50% or more nonstop", "d_ns_share >= 0.50")]
        for label, cond in cuts:
            row = con.execute(f"""
                SELECT count(*), SUM(dc), SUM(sc) FROM (
                    SELECT coalesce(dot.cx, 0) AS dc, coalesce(sab.cx, 0) AS sc,
                           coalesce(dot.ns, 0) / nullif(dot.tot, 0) AS d_ns_share
                    FROM dot JOIN sab ON dot.o = sab.o AND dot.d = sab.d)
                WHERE {cond}
            """).fetchone()
            n_c, dv, sv = (row[0] or 0), (row[1] or 0), (row[2] or 0)
            print(f"    {label:<26} {n_c:>7,} {dv:>14,.0f} {sv:>14,.0f} "
                  f"{_fmt_ratio(_ratio(dv, sv)):>9}")

        if args.top:
            print(f"\n  Widest connecting divergence, {args.top} pairs with 5,000+ DOT connecting:")
            rows = con.execute(f"""
                SELECT dot.o, dot.d, dot.cx, sab.cx, dot.cx / nullif(sab.cx, 0) AS r
                FROM dot JOIN sab ON dot.o = sab.o AND dot.d = sab.d
                WHERE dot.cx >= 5000 AND sab.cx > 0
                ORDER BY abs(ln(dot.cx / sab.cx)) DESC LIMIT {int(args.top)}
            """).fetchall()
            for o, d, dc, sc, r in rows:
                print(f"    {o}-{d}: DOT {dc:,.0f}, Sabre {sc:,.0f}, {r:.2f}x")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
