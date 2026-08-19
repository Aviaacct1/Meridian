"""
Diagnostic, 19 Aug 2026: confirm what OAG data drove conn_coeff to differ on PVG and ICN for
Starlux (JX) beyond TPE, while every other city on that table and every city on the CI/BR
tables came out flat. Prints the OAG week actually resolved (the deliberate rule, not max(week)),
the raw onward-carrier rows at TPE->PVG and TPE->ICN, and conn_coeff's own verdict for CI, BR
and JX so the three tables' behaviour can be read straight off the source data, not inferred.

Run on the workstation, where oag.duckdb actually lives (config.OAG_DUCKDB). Read-only.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

import config
import duckdb
from route_feed import hub_onward_carriers, conn_coeff, ALLIANCE
from cortex_app import resolve_oag_week

oag_path = str(config.OAG_DUCKDB)
print(f"OAG store: {oag_path}")
if not os.path.exists(oag_path):
    print("NOT FOUND on this machine - run this on the workstation, not the dev PC.")
    sys.exit(1)

con = duckdb.connect(oag_path, read_only=True)
week, nregions, why = resolve_oag_week(con)
print(f"Resolved week: {week}  ({nregions} regions)  basis: {why}\n")

onward = hub_onward_carriers(oag_path, week, "TPE")

for city in ("PVG", "ICN"):
    print(f"=== TPE -> {city} ===")
    carriers = onward.get(city, set())
    if not carriers:
        print("  no onward-carrier rows found at all for this week/city")
    else:
        print("  operating carriers this week:", sorted(carriers))
    # raw rows, for the audit trail
    rows = con.execute(
        "SELECT carrier, count(*) n FROM oag WHERE week=? AND dep_airport='TPE' AND arr_airport=? "
        "GROUP BY 1 ORDER BY 2 DESC", [week, city]).fetchall()
    for c, n in rows:
        print(f"    {c}: {n} departures that week")
    for al_name, code in (("China Airlines", "CI"), ("EVA Air", "BR"), ("Starlux", "JX")):
        coeff = conn_coeff(code, carriers, None)
        alliance = ALLIANCE.get(code, "none")
        print(f"  conn_coeff({code}, alliance={alliance}) = {coeff}")
    print()

con.close()
