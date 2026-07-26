#!/usr/bin/env python3
"""
Water-boundary coverage diagnostic (READ-ONLY - changes nothing in the engine).
==============================================================================
Context (18 Jul 2026): the water-boundary check (water_check.road_reachable, Jessica's STT/Ibiza
fix) is wired into the LOCALE -> AIRPORT layer (catchment.py:_drive_min) but NOT into the
AIRPORT -> COMPETING-AIRPORT-SET layer (route_engine.competing_airports), which is a bare
great-circle radius. For Belfast that pulls Glasgow, Edinburgh, Prestwick and the Hebrides across
the Irish Sea into the "catchment", so their P2P demand is booked as Belfast leakage.

Phase 1 (instant, no SQL): competing set as built today vs the same set with road_reachable applied.
Phase 2 (SQL, one origin):  the opportunity table re-ranked on both bases, so the corrected output
                            can be judged before any engine change is made.

Mainland controls are included deliberately: they should be UNCHANGED. If a mainland control loses
airports the filter is too aggressive and the threshold needs revisiting.

Run:  cd C:\\AviaDev\\app  &&  py -3.12 diag_water_catchment.py
Env:  AVIA_SABRE / AVIA_OAG override the store paths; AVIA_DIAG_YEAR overrides the Sabre year.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

GAP_KM = 20.0          # same threshold catchment.py uses (max_water_gap_km)
RADIUS_KM = 220.0      # same default the engine / opportunity scan uses
TOP_SHOW = 12

SETS_ORIGINS = [
    ("BHD", "Belfast City - the reported case"),
    ("BFS", "Belfast International"),
    ("STT", "St Thomas USVI - Jessica's original case"),
    ("IBZ", "Ibiza - Jessica's second case"),
    ("MAN", "Manchester - MAINLAND CONTROL, expect no change"),
    ("LHR", "London Heathrow - MAINLAND CONTROL, expect no change"),
]
RERANK_ORIGIN = os.environ.get("AVIA_DIAG_ORIGIN", "BHD")


def _group_metros(rows, ap, radius_km=80.0):
    """Copy of cortex_app._group_metros so this script needs no FastAPI import."""
    import route_engine as RE
    clusters = []
    for r in rows:
        a = ap.get(r["dest"], {}); la, lo = a.get("lat"), a.get("lon")
        placed = False
        if la is not None and lo is not None:
            for cl in clusters:
                if cl["lat"] is not None and RE.gc_km(la, lo, cl["lat"], cl["lon"]) <= radius_km:
                    cl["rows"].append(r); placed = True; break
        if not placed:
            clusters.append({"lat": la, "lon": lo, "rows": [r]})
    out = []
    for cl in clusters:
        rs = sorted(cl["rows"], key=lambda x: -x["pax"]); head = rs[0]; a = ap.get(head["dest"], {})
        pax = sum(x["pax"] for x in rs); vh = sum(x["via_home"] for x in rs)
        out.append({"dest": head["dest"], "dest_city": a.get("city") or head["dest"],
                    "airports": [x["dest"] for x in rs], "pax": pax, "via_home": vh,
                    "leakage": pax - vh, "home_share": round(vh / pax, 3) if pax else 0.0})
    out.sort(key=lambda x: -x["leakage"])
    return out


def main():
    import route_engine as RE
    import oag_served as OAS
    import sabre_catchment as SC
    from water_check import road_reachable, max_water_gap_km

    try:
        import global_land_mask  # noqa: F401
        mask = "ON"
    except Exception:
        mask = "OFF  <-- fail-open: expect NO drops below; pip install global-land-mask"
    print(f"land mask: {mask}   water gap threshold: {GAP_KM:.0f} km   radius: {RADIUS_KM:.0f} km")

    sabre_db = os.environ.get("AVIA_SABRE", r"C:\Avia\sabre.duckdb")
    year = int(os.environ.get("AVIA_DIAG_YEAR", "2025"))
    files = sorted(glob.glob(os.path.join(HERE, "served_*.json")))
    idx = OAS.load_index(files[-1]) if files else None
    sset = OAS.served_set(idx) if idx else None
    ap = RE._airports()
    print(f"sabre: {sabre_db}   year: {year}   served index: {os.path.basename(files[-1]) if files else 'none'}")

    def split_set(code):
        o = ap.get(code)
        if not o or o.get("lat") is None:
            return None, None, None, None
        current = [r["iata"] for r in RE.competing_airports(o, RADIUS_KM, sset, True)]
        keep, dropped = [], []
        for c in current:
            r = ap.get(c)
            if c == code or not r or r.get("lat") is None:
                keep.append(c); continue
            try:
                ok = road_reachable(o["lat"], o["lon"], r["lat"], r["lon"], GAP_KM)
                gap = max_water_gap_km(o["lat"], o["lon"], r["lat"], r["lon"])
            except Exception:
                ok, gap = True, float("nan")      # fail open, same as the engine
            (keep.append(c) if ok else dropped.append((c, gap, r.get("city") or "")))
        return o, current, keep, dropped

    print("\n" + "=" * 96)
    print("PHASE 1 - competing-airport set: as built today vs with the water filter applied")
    print("=" * 96)
    for code, note in SETS_ORIGINS:
        o, current, keep, dropped = split_set(code)
        if o is None:
            print(f"\n{code}: not in the airport table"); continue
        print(f"\n{code}  ({note})")
        print(f"  NOW      ({len(current):>2}): {', '.join(current)}")
        print(f"  FILTERED ({len(keep):>2}): {', '.join(keep)}")
        if dropped:
            print("  DROPPED (not road-reachable):")
            for c, gap, city in sorted(dropped, key=lambda x: -(x[1] if x[1] == x[1] else 0)):
                print(f"     {c:<5}{city[:26]:<28}water gap {gap:7.1f} km")
        else:
            print("  DROPPED: none (set unchanged)")

    # ---------------- Phase 2: re-rank the opportunity table -------------------------------
    code = RERANK_ORIGIN
    o, current, keep, dropped = split_set(code)
    if o is None:
        print(f"\nre-rank origin {code} not resolvable"); return
    print("\n" + "=" * 96)
    print(f"PHASE 2 - opportunity table for {code}, today's basis vs the filtered basis")
    print("=" * 96)

    def show(title, origin_set):
        try:
            raw = SC.top_destinations(sabre_db, origin_set, code, year=year, top=60)
        except Exception as e:
            print(f"\n  {title}\n    query failed: {e}"); return
        rows = _group_metros(raw, ap)[:TOP_SHOW]
        oset = set(origin_set)
        print(f"\n  {title}  (origin set {len(origin_set)}: {', '.join(origin_set)})")
        print(f"    {'dest':<6}{'city':<22}{'market(ew)':>13}{'via home':>10}{'leakage':>13}   flag")
        for r in rows:
            grouped = set(r.get("airports") or [r["dest"]])
            flag = "SELF-REFERENTIAL" if (grouped & oset) else ""
            print(f"    {r['dest']:<6}{(r['dest_city'] or '')[:21]:<22}{r['pax']:>13,}"
                  f"{r['home_share']*100:>9.0f}%{r['leakage']:>13,}   {flag}")
        n_self = sum(1 for r in rows if set(r.get("airports") or [r["dest"]]) & oset)
        print(f"    -> {n_self} self-referential row(s); total leakage in top {len(rows)}: "
              f"{sum(r['leakage'] for r in rows):,}")

    show("TODAY", current)
    show("WITH WATER FILTER", keep)
    print("\n" + "=" * 96)
    print("Read-only: no engine file was modified.")


if __name__ == "__main__":
    main()
