#!/usr/bin/env python3
r"""
Avia Solutions - REGION-WEIGHTED hub connectivity from Sabre (the directional measure, John's idea).
==================================================================================================
An airport's AVERAGE transfer share under-credits long-haul into a hub: TPE's overall transfer is diluted by
Taipei's big local market, but a US->TPE route connects hard onward to South-East Asia. So measure the transfer
share at each hub BY PARTNER REGION: of the traffic that touches hub X and whose OTHER end is in region R, what
fraction connects through X rather than starting/ending there.

    transfer_share[X][R] = pax connecting at X involving region R / (that + pax with an endpoint at X, other end in R)
    localness[X][R]      = 1 - transfer_share[X][R]

For a route o->d the P2P share is then  local_o[region_of_d] x local_d[region_of_o]  - each hub scored for the
traffic direction that actually flows. A single long Sabre run builds the rules for every airport. Writes
region_localness.json (region table + an airport-average fallback + global fallback), consumed by split_share.py.

    py -3.12 build_hub_connectivity_region.py --sabre C:\Avia\sabre.duckdb --temp-dir E:\Avia\QSI\duckdb_tmp \
        --out region_localness.json

10-year run; memory-capped for the 16GB box. Reads Sabre read-only.
"""
import argparse, os, json

# country -> region (same map the engine's route_region uses, so the table matches the rest of the tool)
REGION = {
    "GB": "EU", "IE": "EU", "FR": "EU", "DE": "EU", "ES": "EU", "IT": "EU", "NL": "EU", "BE": "EU",
    "CH": "EU", "AT": "EU", "PT": "EU", "SE": "EU", "NO": "EU", "DK": "EU", "FI": "EU", "PL": "EU",
    "CZ": "EU", "GR": "EU", "RO": "EU", "HU": "EU", "HR": "EU", "RS": "EU", "BG": "EU", "SK": "EU",
    "UA": "EU", "IS": "EU", "LU": "EU", "EE": "EU", "LV": "EU", "LT": "EU", "CY": "EU", "MT": "EU",
    "US": "NA", "CA": "NA",
    "MX": "LATAM", "BR": "LATAM", "AR": "LATAM", "CL": "LATAM", "CO": "LATAM", "PE": "LATAM",
    "EC": "LATAM", "BO": "LATAM", "PY": "LATAM", "UY": "LATAM", "VE": "LATAM", "PA": "LATAM",
    "CR": "LATAM", "GT": "LATAM", "DO": "LATAM", "CU": "LATAM", "JM": "LATAM", "BZ": "LATAM",
    "HN": "LATAM", "NI": "LATAM", "SV": "LATAM", "TT": "LATAM",
    "AE": "MEA", "SA": "MEA", "QA": "MEA", "IL": "MEA", "TR": "MEA", "JO": "MEA", "KW": "MEA",
    "OM": "MEA", "BH": "MEA", "LB": "MEA", "EG": "MEA",
    "ZA": "AFR", "KE": "AFR", "NG": "AFR", "ET": "AFR", "MA": "AFR", "TN": "AFR", "GH": "AFR",
    "TZ": "AFR", "MU": "AFR",
    "JP": "APAC", "KR": "APAC", "AU": "APAC", "NZ": "APAC", "SG": "APAC", "HK": "APAC", "TW": "APAC",
    "TH": "APAC", "MY": "APAC",
    "CN": "CN", "IN": "IN", "ID": "ID", "VN": "VN",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--years", default=None, help="comma list of source_year (default all years)")
    ap.add_argument("--min-pax", type=float, default=8000.0, help="min pax in a (hub,region) cell to score it")
    ap.add_argument("--min-airport-pax", type=float, default=25000.0, help="min total pax to score an airport at all")
    ap.add_argument("--temp-dir", default=None)
    ap.add_argument("--mem-reserve", type=float, default=8.0, help="GB to leave the OS")
    ap.add_argument("--out", default="region_localness.json")
    a = ap.parse_args()
    import duckdb, airportsdata
    if not os.path.exists(a.sabre):
        print(f"Sabre store not found: {a.sabre}"); return
    apts = airportsdata.load("IATA")

    con = duckdb.connect(a.sabre, read_only=True)
    if a.temp_dir:
        os.makedirs(a.temp_dir, exist_ok=True)
        con.execute(f"PRAGMA temp_directory='{a.temp_dir}'")
    try:
        import psutil
        total_gb = psutil.virtual_memory().total / 1e9
        con.execute(f"PRAGMA memory_limit='{max(2.0, total_gb - a.mem_reserve):.0f}GB'")
    except Exception:
        con.execute("PRAGMA memory_limit='6GB'")

    # region-map temp table (airport -> region) to JOIN on the PARTNER end
    con.execute("CREATE TEMP TABLE regmap(apt VARCHAR, region VARCHAR)")
    con.executemany("INSERT INTO regmap VALUES (?,?)",
                    [(code, REGION.get((r.get("country") or ""), "OTH")) for code, r in apts.items()])
    cols = {r[1] for r in con.execute("PRAGMA table_info('sabre')").fetchall()}
    yr = ""
    params = []
    if a.years:
        ys = [int(y) for y in a.years.split(",")]
        yr = " AND source_year IN (" + ",".join("?" * len(ys)) + ")"
        params = ys
    # hub touches, tagged endpoint/transfer, with the PARTNER airport (whose region we join)
    unions = [
        f"SELECT origin_airport AS hub, destination_airport AS partner, passengers AS pax, 0 AS tr FROM sabre WHERE origin_airport IS NOT NULL{yr}",
        f"SELECT destination_airport, origin_airport, passengers, 0 FROM sabre WHERE destination_airport IS NOT NULL{yr}",
    ]
    for cc in ("connecting_airport1", "connecting_airport2"):
        if cc in cols:
            unions.append(f"SELECT {cc}, origin_airport, passengers, 1 FROM sabre WHERE {cc} IS NOT NULL AND TRIM({cc})<>''{yr}")
            unions.append(f"SELECT {cc}, destination_airport, passengers, 1 FROM sabre WHERE {cc} IS NOT NULL AND TRIM({cc})<>''{yr}")
    sql = ("SELECT t.hub, rm.region AS pr, "
           "SUM(CASE WHEN t.tr=0 THEN t.pax ELSE 0 END) AS ep, "
           "SUM(CASE WHEN t.tr=1 THEN t.pax ELSE 0 END) AS trf "
           "FROM (\n  " + "\n  UNION ALL\n  ".join(unions) + "\n) t "
           "JOIN regmap rm ON UPPER(TRIM(t.partner)) = rm.apt "
           "WHERE t.hub IS NOT NULL AND TRIM(t.hub)<>'' GROUP BY t.hub, rm.region")
    print("running the region aggregation (long)...")
    rows = con.execute(sql, params * len(unions)).fetchall()
    con.close()

    # assemble: region[hub][region] = localness, plus an airport-average fallback per hub
    reg = {}
    tot_ep = {}; tot_tr = {}
    for hub, pr, ep, trf in rows:
        h = (hub or "").strip().upper()
        if h not in apts:                                   # airports only (drop rail/ground codes)
            continue
        ep = float(ep or 0); trf = float(trf or 0)
        tot_ep[h] = tot_ep.get(h, 0.0) + ep
        tot_tr[h] = tot_tr.get(h, 0.0) + trf
        if ep + trf >= a.min_pax:
            reg.setdefault(h, {})[pr] = round(max(0.02, min(1.0, 1.0 - trf / (ep + trf))), 4)
    airport = {}
    for h in tot_ep:
        t = tot_ep[h] + tot_tr[h]
        if t >= a.min_airport_pax:
            airport[h] = round(max(0.02, min(1.0, 1.0 - tot_tr[h] / t)), 4)
    g = sorted(airport.values())[len(airport) // 2] if airport else 0.9
    json.dump({"meta": {"source": "sabre region-weighted transfer share", "years": a.years or "all",
                        "n_airports": len(airport), "n_region_cells": sum(len(v) for v in reg.values()),
                        "global_localness": round(g, 4), "model": "p2p_share=local_o[reg_d]*local_d[reg_o]"},
               "global_localness": round(g, 4), "region": reg, "local": airport},
              open(a.out, "w"), indent=0)
    print(f"wrote {a.out}: {len(airport)} airports, {sum(len(v) for v in reg.values())} (hub,region) cells, global {g:.2f}")
    # face-validity: for the biggest hubs, show transfer share BY region
    big = sorted(airport.items(), key=lambda kv: kv[1])[:8]
    for h, lv in big:
        cells = ", ".join(f"{r} {1-v:.0%}" for r, v in sorted(reg.get(h, {}).items(), key=lambda kv: kv[1])[:5])
        print(f"  {h} (avg {1-lv:.0%} transfer): by region -> {cells}")


if __name__ == "__main__":
    main()
