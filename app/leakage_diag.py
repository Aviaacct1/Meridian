#!/usr/bin/env python3
r"""
Avia Solutions - correct the NI leakage measure: identify the traveller by HOME CITY, not just country.
======================================================================================================
poo_country='GB' at Dublin is contaminated: a GB-mainland resident on a London-Dublin round trip carries a GB
point of origin on the RETURN leg too (origin DUB, poo GB), and Dublin-GB is a huge market, so those return legs
masquerade as NI leakage. The giveaway was that the "leaked" destinations were all GB airports. This script:

  1. shows the directionality values (return legs are the contamination) and the poo_city_name mix at Dublin for
     GB-poo passengers - if it's full of London/Manchester/etc., that confirms the contamination;
  2. rebuilds leakage the clean way, poo_city_name restricted to Northern Irish towns, and reprints the year trend
     and the why-split (breadth vs choice) so we can see the TRUE Belfast-vs-Dublin picture.

    py -3.12 leakage_diag.py

Reads read-only.
"""
import duckdb, collections

SAB = r"C:\Avia\sabre.duckdb"
NI = ["BFS", "BHD", "LDY"]; LEAK = "DUB"
# Northern Irish towns/cities (poo_city_name). Belfast + Londonderry carry the bulk; the rest catch the tail.
NI_CITY = ["BELFAST", "LONDONDERRY", "DERRY", "NEWRY", "LISBURN", "COLERAINE", "ENNISKILLEN", "BALLYMENA",
           "CRAIGAVON", "ARMAGH", "OMAGH", "ANTRIM", "LARNE", "STRABANE", "LIMAVADY", "COOKSTOWN", "DUNGANNON",
           "MAGHERAFELT", "BANBRIDGE", "PORTADOWN", "LURGAN", "NEWTOWNARDS", "DOWNPATRICK", "BALLYMONEY",
           "CARRICKFERGUS", "BALLYCLARE", "NEWTOWNABBEY", "WARRENPOINT", "KILKEEL", "BALLYCASTLE", "COMBER"]
MIN_DEST = 300


def main():
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")
    apts = NI + [LEAK]; aph = ",".join(f"'{x}'" for x in apts)

    print("=== directionality values (GB-poo across the 4 airports) - return legs are the contamination ===")
    for v, p in con.execute(f"SELECT directionality, SUM(passengers) p FROM sabre "
                            f"WHERE poo_country='GB' AND origin_airport IN ({aph}) GROUP BY 1 ORDER BY p DESC").fetchall():
        print(f"  {v!r}: {int(p or 0):,}")

    print("\n=== poo_city_name at DUB (GB-poo, 2025): is this NI residents, or GB visitors going home? ===")
    for v, p in con.execute("SELECT poo_city_name, SUM(passengers) p FROM sabre WHERE poo_country='GB' "
                            "AND origin_airport='DUB' AND source_year=2025 GROUP BY 1 ORDER BY p DESC LIMIT 15").fetchall():
        print(f"  {v}: {int(p or 0):,}")
    print("\n=== poo_city_name at BFS (GB-poo, 2025): sanity, should be Northern Irish ===")
    for v, p in con.execute("SELECT poo_city_name, SUM(passengers) p FROM sabre WHERE poo_country='GB' "
                            "AND origin_airport='BFS' AND source_year=2025 GROUP BY 1 ORDER BY p DESC LIMIT 10").fetchall():
        print(f"  {v}: {int(p or 0):,}")

    cityset = ",".join(f"'{c}'" for c in NI_CITY)
    nifilt = f"poo_country='GB' AND UPPER(poo_city_name) IN ({cityset}) AND origin_airport IN ({aph})"

    # corrected trend
    print("\n=== CORRECTED leakage trend (poo_city = Northern Irish towns), by year ===")
    rows = con.execute(f"SELECT source_year yr, origin_airport a, SUM(passengers) p FROM sabre "
                       f"WHERE {nifilt} GROUP BY 1,2 ORDER BY 1").fetchall()
    by = collections.defaultdict(dict); tot = collections.defaultdict(float)
    for y, a, p in rows:
        by[y][a] = p or 0.0; tot[y] += p or 0.0
    print(f"{'yr':6}{'NI pax':>10}   " + "  ".join(f"{x:>6}" for x in NI) + f"   {'DUB(leak)':>10}")
    for y in sorted(by):
        t = tot[y] or 1
        print(f"{y:6}{int(t):>10,}   " + "  ".join(f"{100*by[y].get(x,0)/t:5.1f}%" for x in NI)
              + f"   {100*by[y].get(LEAK,0)/t:9.1f}%")

    # corrected why-split, 2025
    print("\n=== CORRECTED why-split (poo_city = NI, 2025): breadth vs choice ===")
    dr = con.execute(f"""SELECT destination_airport d,
             SUM(CASE WHEN origin_airport='{LEAK}' THEN passengers ELSE 0 END) leak,
             SUM(CASE WHEN origin_airport<>'{LEAK}' THEN passengers ELSE 0 END) bel
        FROM sabre WHERE {nifilt} AND source_year=2025 GROUP BY 1""").fetchall()
    dest = {d: (lk or 0.0, be or 0.0) for d, lk, be in dr}
    tl = sum(lk for lk, be in dest.values())
    only = sum(lk for lk, be in dest.values() if be < MIN_DEST)
    print(f"total Dublin-leaked (NI residents):  {int(tl):>9,}")
    print(f"  DUBLIN-ONLY routes (breadth):      {int(only):>9,}  ({100*only/(tl or 1):.0f}%)")
    print(f"  OVERLAP routes (choice):           {int(tl-only):>9,}  ({100*(tl-only)/(tl or 1):.0f}%)")
    print("\n--- top NI leak destinations (leak vs Belfast pax, Dublin share of NI demand) ---")
    for d, lk, be in sorted(((d, lk, be) for d, (lk, be) in dest.items() if lk >= MIN_DEST), key=lambda x: -x[1])[:25]:
        al = con.execute(f"SELECT marketing_airline, SUM(passengers) p FROM sabre WHERE {nifilt} "
                         f"AND source_year=2025 AND destination_airport='{d}' AND origin_airport='{LEAK}' "
                         f"GROUP BY 1 ORDER BY p DESC LIMIT 2").fetchall()
        tag = "/".join(c for c, _ in al if c)
        print(f"  {d:4}  leak {int(lk):>7,}   BEL {int(be):>7,}   DUBshr {100*lk/((lk+be) or 1):>4.0f}%   DUB:{tag}")
    con.close()


if __name__ == "__main__":
    main()
