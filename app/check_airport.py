#!/usr/bin/env python3
r"""What the stores actually hold for one airport, year by year. Read only.

    py -3.12 check_airport.py EDI
    py -3.12 check_airport.py EDI --oag C:\Avia\oag.duckdb --aci C:\Avia\aci.duckdb

Answers the question that decides every airport chart in the deck: which years
can this airport be drawn for, and from which store. The two do not agree and
are not expected to. ACI is a monthly return from the airport, so it runs to the
last month published. OAG is a schedules pull, so it holds whatever years have
been loaded at monthly labels, and coverage is heterogeneous by region and year.

A year is only usable at twelve months. A year held with eight is not a thin
year to be plotted short, it is a year the chart must leave out and say so.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iata")
    ap.add_argument("--oag", default="")
    ap.add_argument("--aci", default="")
    ap.add_argument("--t100", default="", help=r"e.g. E:\Avia\Usmarket data\t100.duckdb")
    ap.add_argument("--from", dest="from_year", type=int, default=2015)
    a = ap.parse_args()
    code = a.iata.strip().upper()

    oag_db, aci_db = a.oag, a.aci
    if not (oag_db and aci_db):
        try:
            import config as CFG
            oag_db = oag_db or str(CFG.OAG_DUCKDB)
            aci_db = aci_db or str(CFG.ACI_DUCKDB)
        except Exception as e:
            raise SystemExit("config.py did not load (%s); pass --oag and --aci" % e)

    import airport_profile as AP
    import duckdb

    print("AIRPORT %s" % code)
    print("   OAG  %s%s" % (oag_db, "" if os.path.exists(oag_db) else "   NOT PRESENT"))
    print("   ACI  %s%s" % (aci_db, "" if os.path.exists(aci_db) else "   NOT PRESENT"))

    oag = {}
    if os.path.exists(oag_db):
        con = duckdb.connect(oag_db, read_only=True)
        try:
            oag = {y: m for y, m in AP.airport_years(con, code)}
        finally:
            con.close()

    aci = {}
    if os.path.exists(aci_db):
        con = duckdb.connect(aci_db, read_only=True)
        try:
            aci = {int(y): int(m) for y, m in con.execute(
                "SELECT year, COUNT(DISTINCT ym) FROM aci_monthly "
                "WHERE UPPER(TRIM(iata)) = ? GROUP BY 1", [code]).fetchall()}
        finally:
            con.close()

    if not oag and not aci:
        raise SystemExit("neither store holds %s" % code)

    # THE SOURCE RULE IS APPLIED BEFORE ANYTHING IS REPORTED, not after. ACI
    # holds every US airport, so a report built on store contents alone would
    # say a chart is drawable that the house rule forbids: a US audience checks
    # the number against TranStats, and a figure it cannot reproduce costs more
    # than a missing chart. airport_profile refuses it, and so must this.
    country = AP.aci_country(aci_db, code)
    kind, label, _unit = AP.pax_source(country or "")
    us = (kind == "dot")

    t100_db, t100_note = a.t100, ""
    if us and not t100_db:
        try:
            import config as CFG
            t100_db = str(CFG.T100_DUCKDB)
        except Exception:
            t100_db = ""
    pax_series, pax_who = {}, "ACI"
    if us:
        pax_who = "US DOT T-100"
        if t100_db and os.path.exists(t100_db):
            got, t100_note = AP.read_t100(t100_db, code)
            pax_series = {y: p for y, p in got}
        else:
            t100_note = ("the T-100 store is not at %s. ACI holds this airport "
                         "but is not substituted for a US one."
                         % (t100_db or "any path config knows"))
    else:
        pax_series = {y: m for y, m in aci.items() if m == 12}

    print("\n   country              %s   graded on %s"
          % (country or "not in the ACI store", label))

    years = sorted(set(oag) | set(aci) | set(pax_series))
    years = [y for y in years if y >= a.from_year]
    print("\n   %-6s %-22s %-26s %s"
          % ("year", "OAG months (seats)", "%s (passengers)" % pax_who,
             "chartable"))
    both = []
    for y in years:
        o, c = oag.get(y), aci.get(y)
        pax_ok = y in pax_series
        ok = (o == 12 and pax_ok)
        if ok:
            both.append(y)
        if us:
            # the ACI column is shown for a US airport only to say it is there
            # and not being used, which is a different thing from absent
            pax_txt = ("complete" if pax_ok else
                       ("not held" if c is None
                        else "not usable, ACI only"))
        else:
            pax_txt = ("-" if c is None else
                       ("%d  complete" % c if c == 12 else "%d  PART YEAR" % c))
        print("   %-6d %-22s %-26s %s"
              % (y,
                 "-" if o is None else ("%d  complete" % o if o == 12
                                        else "%d  PART YEAR" % o),
                 pax_txt,
                 "seats + pax" if ok else
                 ("pax only" if pax_ok else
                  ("seats only" if o == 12 else "no"))))

    full_oag = sorted(y for y, m in oag.items() if m == 12 and y >= a.from_year)
    full_pax = sorted(y for y in pax_series if y >= a.from_year)
    print("\n   passengers by year   %s" % (
        _span(full_pax, pax_who) if full_pax
        else "NOT DRAWABLE. %s" % t100_note))
    if full_pax and t100_note:
        print("                        %s" % t100_note)
    print("   seats by market      %s" % _span(full_oag, "OAG"))
    print("   airlines by capacity %s" % (
        "latest complete OAG year, %d" % max(full_oag) if full_oag
        else "NOT DRAWABLE, no complete OAG year"))
    if len(both) >= 3:
        why = ("%d-%d, %d year%s where both stores are complete"
               % (min(both), max(both), len(both), "" if len(both) == 1 else "s"))
    elif us and not full_pax:
        # Naming a coverage shortfall here would be the wrong reason. The seats
        # are present; what is missing is the only passenger source this airport
        # may be graded on.
        why = ("NOT DRAWABLE, and not for want of coverage: the seats are held, "
               "but the load factor needs the DOT passenger count and that store "
               "is not here")
    else:
        why = ("NOT DRAWABLE, the two stores share %d complete year%s and it "
               "needs three" % (len(both), "" if len(both) == 1 else "s"))
    print("   effective load       %s" % why)


def _span(years, who):
    if not years:
        return "NOT DRAWABLE, no complete %s year" % who
    gaps = [y for y in range(min(years), max(years) + 1) if y not in years]
    return "%d-%d from %s, %d complete year%s%s" % (
        min(years), max(years), who, len(years), "" if len(years) == 1 else "s",
        "; gaps at %s" % ", ".join(str(y) for y in gaps) if gaps else "")


if __name__ == "__main__":
    main()
