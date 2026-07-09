#!/usr/bin/env python3
r"""
Avia Solutions - airport connectivity table from Sabre TRANSFER SHARE (John's measure, the clean one).
==================================================================================================
An airport's hub character = the share of its Sabre passengers that are CONNECTING through it rather than
starting or ending there. Straight from the itineraries: a record O -> C1 -> D counts its pax as ENDPOINT at
O and D and as TRANSFER at C1 (connecting_airport1). Both sides of the ratio come from the SAME source, so
the GDS coverage bias largely cancels - and Southwest barely sells connections through GDS, so MDW reads as
local, not a hub, with no hacks.

    transfer_share[X] = pax where X is a connecting point / (that + pax where X is an origin or destination)
    localness[X]      = 1 - transfer_share[X]          (1 = pure O&D spoke, low = big connecting hub)

Writes hub_localness.json (the table the engine's split_share.py consumes). The route split is then
p2p_share(o,d) = localness_o x localness_d (a true point-to-point pax is local at BOTH ends).

    py -3.12 build_hub_connectivity.py --sabre C:\Avia\sabre.duckdb --out hub_localness.json
    py -3.12 build_hub_connectivity.py --years 2023,2024,2025 --min-pax 5000

Reads the Sabre store read-only. Validate the table against the back-test with:
    py -3.12 calib_split_share.py bt_v2_6yr.csv --load-table hub_localness.json
"""
import argparse, os, json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--years", default=None, help="comma list of source_year to include (default all years)")
    ap.add_argument("--min-pax", type=float, default=25000.0, help="min total pax touching an airport to score it (a fraction on thin volume is noise)")
    ap.add_argument("--out", default="hub_localness.json")
    a = ap.parse_args()
    import duckdb
    if not os.path.exists(a.sabre):
        print(f"Sabre store not found: {a.sabre}"); return
    con = duckdb.connect(a.sabre, read_only=True)
    try:
        from db_registry import apply_limits; apply_limits(con)
    except Exception:
        pass
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info('sabre')").fetchall()}
        yr = ""
        params = []
        if a.years:
            ys = [int(y) for y in a.years.split(",")]
            yr = " AND source_year IN (" + ",".join("?" * len(ys)) + ")"
            params = ys
        # each pax record: ENDPOINT at origin + destination, TRANSFER at each connecting point present
        parts = [f"SELECT origin_airport AS apt, passengers AS loc, 0 AS cn FROM sabre WHERE origin_airport IS NOT NULL{yr}",
                 f"SELECT destination_airport, passengers, 0 FROM sabre WHERE destination_airport IS NOT NULL{yr}"]
        for cc in ("connecting_airport1", "connecting_airport2"):
            if cc in cols:
                parts.append(f"SELECT {cc}, 0, passengers FROM sabre "
                             f"WHERE {cc} IS NOT NULL AND TRIM({cc})<>''{yr}")
        pr = params * len(parts)
        sql = ("SELECT apt, SUM(loc) AS local_pax, SUM(cn) AS conn_pax FROM (\n  "
               + "\n  UNION ALL\n  ".join(parts)
               + "\n) WHERE apt IS NOT NULL AND TRIM(apt)<>'' GROUP BY apt")
        rows = con.execute(sql, pr).fetchall()
    finally:
        con.close()

    try:
        import airportsdata
        _APT = set(airportsdata.load("IATA").keys())
    except Exception:
        _APT = None
    local = {}; conn_vol = {}
    skipped_nonapt = 0
    for apt, loc, cn in rows:
        code = (apt or "").strip().upper()
        if _APT is not None and code not in _APT:    # drop rail / bus / ground codes (e.g. X-prefixed rail)
            skipped_nonapt += 1; continue
        loc = float(loc or 0); cn = float(cn or 0); tot = loc + cn
        if tot < a.min_pax:                          # a transfer fraction on thin volume is noise
            continue
        local[code] = max(0.02, min(1.0, 1.0 - cn / tot))
        conn_vol[code] = cn
    if not local:
        print("No airports scored - check the store/columns."); return
    g = sorted(local.values())[len(local) // 2]      # median localness = fallback for unknown airports
    json.dump({"meta": {"source": "sabre transfer share", "years": a.years or "all",
                        "n_airports": len(local), "global_localness": round(g, 4),
                        "model": "p2p_share(o,d)=local_o*local_d"},
               "global_localness": round(g, 4),
               "local": {k: round(v, 4) for k, v in local.items()}},
              open(a.out, "w"), indent=0)
    # rank the DISPLAY by transfer VOLUME (how many people actually transfer there) so the real big hubs show,
    # not tiny points that happen to be 98% connections; print each one's transfer SHARE (what the model uses).
    top = sorted(conn_vol.items(), key=lambda kv: -kv[1])[:24]
    print(f"wrote {a.out}: {len(local)} airports scored (>= {a.min_pax:.0f} pax; dropped {skipped_nonapt} non-airport codes), global localness {g:.2f}")
    print("  biggest connecting hubs (by transfer volume; transfer share in brackets):")
    print("    " + ", ".join(f"{k} {1-local[k]:.0%}" for k, _ in top))


if __name__ == "__main__":
    main()
