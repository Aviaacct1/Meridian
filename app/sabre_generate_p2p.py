#!/usr/bin/env python3
"""
Avia Solutions - P2P market generator.
Builds the point-to-point O&D market between the route's catchment and its hub
city (e.g. California <-> London), the demand a new direct service competes for.
Splits it the way the analyst P2P sheet does: by traveller origin (Residents =
catchment-origin, Visitors = hub-origin) and by cabin tier (premium vs economy),
with the same split market weighting applied.

This auto-generates the P2P MARKET SIZE and SPLIT. The business/leisure capture
rates and the catchment apportionment remain analyst settings for now (these are
what the cross-route backtest will codify); the pipeline's convergence absorbs
the level for back-tests.

Run: py -3.12 "C:\\Avia\\sabre_generate_p2p.py" --catchment SFO,LAX,SAN --hub LHR,LGW,LON,STN,LCY --year 2013 --combine-directions
"""
import sys, subprocess, argparse
try:
    import duckdb
except ImportError:
    subprocess.check_call([sys.executable,"-m","pip","install","--quiet","duckdb"]); import duckdb
def L(t): return "("+",".join("'"+str(x).strip()+"'" for x in t)+")"

PREMIUM = ("BUSINESS","FIRST","PREMIUM COACH")  # store cabin tiers treated as premium

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--catchment", default="SFO,LAX,SAN")
    ap.add_argument("--hub", default="LHR,LGW,LON,STN,LCY")
    ap.add_argument("--year", type=int, default=2013)
    ap.add_argument("--factor-direct", type=float, default=1.166)
    ap.add_argument("--factor-indirect", type=float, default=1.044)
    ap.add_argument("--combine-directions", action="store_true")
    a=ap.parse_args()
    catch=tuple(x.strip() for x in a.catchment.split(","))
    hub=tuple(x.strip() for x in a.hub.split(","))
    fexpr=f"CASE WHEN itinerary='NON-STOP' THEN {a.factor_direct} ELSE {a.factor_indirect} END"
    # the catchment<->hub O&D market, both ends
    w=f"""source_year={a.year} AND (
        (origin_airport IN {L(catch)} AND destination_airport IN {L(hub)})
        OR (origin_airport IN {L(hub)} AND destination_airport IN {L(catch)}) )"""
    con=duckdb.connect(a.db, read_only=True)
    q=f"""
      SELECT
        CASE WHEN origin_airport IN {L(catch)} THEN 'Residents (catchment-origin)'
             ELSE 'Visitors (hub-origin)' END AS traveller,
        CASE WHEN cabin_class IN {L(PREMIUM)} THEN 'Premium' ELSE 'Economy' END AS tier,
        round(sum(passengers * {fexpr})) AS pax,
        round(sum(total_revenue_usd * {fexpr})) AS rev
      FROM sabre WHERE {w}
      GROUP BY 1,2 ORDER BY 1,2
    """
    rows=con.execute(q).fetchall()
    tot=con.execute(f"SELECT round(sum(passengers * {fexpr})) FROM sabre WHERE {w}").fetchone()[0]
    print(f"P2P market: {a.catchment} <-> {a.hub}  year {a.year}  (split weighting)")
    print(f"  {'traveller':<30} {'tier':<8} {'pax':>12} {'rev USD':>16}")
    grp={}
    for tr,ti,p,r in rows:
        print(f"  {tr:<30} {ti:<8} {p:>12,.0f} {r:>16,.0f}"); grp[tr]=grp.get(tr,0)+p
    print(f"  {'-'*30}")
    for tr,p in grp.items(): print(f"  {tr:<30} {'TOTAL':<8} {p:>12,.0f}")
    print(f"  {'P2P MARKET TOTAL':<39} {tot:>12,.0f}")
    con.close()

if __name__=="__main__":
    main()
