#!/usr/bin/env python3
r"""
Avia Solutions - does directionality decide it? ND vs POO for the Dublin leakage measure.
=========================================================================================
Two readings are in conflict. If the GB-origin Dublin count is genuine NI leakage, it should HOLD when we keep only
point-of-origin-directional records (POO), because a London resident's journey is then oriented London->Dublin and
never shows as a Dublin departure. If it is British return-leg contamination, it lives in the ND records and
COLLAPSES under POO. This prints, for 2025, the GB-origin Dublin count and its point-of-origin-city mix under each
directionality separately, plus the NI-city count, so we can see which reading the data supports.

    py -3.12 dir_split.py

Reads read-only.
"""
import duckdb

SAB = r"C:\Avia\sabre.duckdb"
NI = ["BFS", "BHD", "LDY"]; LEAK = "DUB"
NI_CITY = ["BELFAST", "LONDONDERRY", "DERRY", "NEWRY", "LISBURN", "COLERAINE", "ENNISKILLEN", "BALLYMENA",
           "CRAIGAVON", "ARMAGH", "OMAGH", "ANTRIM", "LARNE", "STRABANE", "LIMAVADY", "COOKSTOWN", "DUNGANNON",
           "MAGHERAFELT", "BANBRIDGE", "PORTADOWN", "LURGAN", "NEWTOWNARDS", "DOWNPATRICK", "BALLYMONEY",
           "CARRICKFERGUS", "BALLYCLARE", "NEWTOWNABBEY", "WARRENPOINT", "KILKEEL", "BALLYCASTLE", "COMBER"]
YR = 2025


def main():
    con = duckdb.connect(SAB, read_only=True); con.execute("SET memory_limit='8GB'")
    aph = ",".join(f"'{x}'" for x in NI + [LEAK])
    cityset = ",".join(f"'{c}'" for c in NI_CITY)

    for d in ("ND", "POO"):
        print(f"\n================  directionality = {d}  ({YR})  ================")
        # GB-origin count at each airport + Dublin share of the 4-airport GB-poo split
        rows = con.execute(f"""SELECT origin_airport a, SUM(passengers) p FROM sabre
            WHERE poo_country='GB' AND origin_airport IN ({aph}) AND source_year={YR} AND directionality='{d}'
            GROUP BY 1""").fetchall()
        m = {a: p or 0 for a, p in rows}; t = sum(m.values()) or 1
        print(f"GB-poo split:  " + "  ".join(f"{a} {int(m.get(a,0)):,} ({100*m.get(a,0)/t:.1f}%)" for a in NI+[LEAK]))
        print(f"  => Dublin share of GB-poo 4-airport total: {100*m.get(LEAK,0)/t:.1f}%")

        # who are the GB-poo people AT Dublin, by home city
        print(f"GB-poo at DUB by point-of-origin city:")
        for v, p in con.execute(f"""SELECT poo_city_name, SUM(passengers) p FROM sabre
            WHERE poo_country='GB' AND origin_airport='{LEAK}' AND source_year={YR} AND directionality='{d}'
            GROUP BY 1 ORDER BY p DESC LIMIT 8""").fetchall():
            print(f"    {v}: {int(p or 0):,}")

        # NI-resident (by city) departures from Dublin under this directionality
        ni = con.execute(f"""SELECT SUM(passengers) FROM sabre WHERE poo_country='GB'
            AND UPPER(poo_city_name) IN ({cityset}) AND origin_airport='{LEAK}'
            AND source_year={YR} AND directionality='{d}'""").fetchone()[0] or 0
        print(f"NI-city residents departing DUB: {int(ni):,}")
    con.close()
    print("\nRead: if POO keeps the Dublin count high AND it is Belfast/NI cities -> genuine leakage, the tender "
          "measure stands. If POO collapses the Dublin count, or it stays London/Manchester -> ND return-leg "
          "contamination, the 1.96m is British visitors going home.")


if __name__ == "__main__":
    main()
