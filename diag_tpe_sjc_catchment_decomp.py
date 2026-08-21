#!/usr/bin/env python3
"""Avia Solutions - John's 21 August ask, after reviewing slide 51: is the asymmetry between the
Taipei-side connecting market (+31% on 2025) and the San Jose-side connecting market (-67% on 2025)
a genuine, defensible design choice, or a logic error inflating one side?

WHAT THIS TESTS. Two refinements moved between the 2025 and 2026 builds of this pitch:
  (1) catchment widening - route_forecast.py passes route_feed.feed_side() the WHOLE catchment
      (competing_airports, several Bay Area airports) as the origin for the BEYOND/Taipei-side
      market, but passes route_feed.behind_feed() only [origin] (SJC alone) for the BEHIND/San
      Jose-side market. The code comment says this is deliberate, "else a route into a small
      airport wrongly inherits a big neighbour's feed bank" - but that comment was never tested
      against real numbers before today.
  (2) the realistic-connection filter - connecting_market()/behind_market() both restrict to Sabre
      itineraries with exactly one connecting airport (excludes both nonstop and double-connection
      journeys). Symmetric between the two sides at the SQL level.

This script re-runs the SAME production call (cortex_app.calibrated_forecast, CI, SJC-TPE) with the
real feed_side/behind_feed calls monkeypatched to CAPTURE their actual arguments (sabre_db, oag_db,
week, year, the real competing_airports list, the real feed_cfg), then re-runs feed_side four ways
and connecting_market's underlying query four ways, varying ONLY the one thing being tested each
time and holding everything else - week, year, factor_indirect, the scope-of-destinations logic -
exactly as production used it. It does NOT touch preagg (deliberately stripped from feed_cfg for
every cell here) so every number below comes from a fresh, identical-basis Sabre pull, not a cache
that may only hold the single-connection aggregate.

SANITY CHECK, non-negotiable: cell A below (wide catchment, single-connection filter, GROWN by the
same factor g that route_forecast.forecast() applies base-year to service-year) must reproduce the
contract's known one-way hub_market figure (719,486, from
PITCH_SJC-TPE_CI_A359_306_5x_2027_contract.json) before any other cell is trusted. If it doesn't
match, STOP - something about the captured arguments is wrong and nothing below is safe to read.

FIRST RUN, 21 August, failed this check by exactly the missing g: 608,084 vs 719,486 (15.5% short).
The gap matched the contract's own growth note - "+18.3% over 2yr from 2025" - to three decimal
places, so this was g never having been applied, not a real mismatch. Fixed by capturing
route_forecast.forecast()'s own (already-grown) beyond_detail alongside the raw feed_side call, and
deriving g as the ratio between them - see _capturing_forecast below.

CELLS, beyond (Taipei) side:
  A = wide catchment  + single-connection filter   (= today's production figure)
  B = SJC only        + single-connection filter   (isolates the catchment effect, filter held fixed)
  C = wide catchment  + any connection count        (isolates the filter effect, catchment held fixed)
  D = SJC only        + any connection count        (both effects removed - closest proxy to what an
                                                       unrefined, narrow-catchment "total potential"
                                                       basis would have shown)

CELLS, behind (San Jose) side:
  A' = SJC-fed feeders + single-connection filter   (= today's production figure, behind_feed's own
                                                       physical-feeder logic, unchanged)
  B' = wide catchment  + single-connection filter   (the SYMMETRIC test: what would San Jose's
                                                       connecting market be if it used the same
                                                       population-catchment logic as Taipei's, instead
                                                       of "who physically flies into SJC")

Run on the workstation (needs sabre.duckdb/oag.duckdb):
    py -3.12 diag_tpe_sjc_catchment_decomp.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\app")

import route_forecast as RFC          # patch BEFORE cortex_app is imported/called
import route_feed as RFEED

_captured_beyond = {}
_captured_behind = {}
_captured_forecast = {}
_orig_feed_side = RFEED.feed_side
_orig_behind_feed = RFEED.behind_feed
_orig_forecast = RFC.forecast


def _capturing_feed_side(sabre_db, oag_db, week, origin_airports, hub, year, **kw):
    if kw.get("beyond", True):
        _captured_beyond.setdefault("calls", []).append(
            dict(sabre_db=sabre_db, oag_db=oag_db, week=week, origin_airports=list(origin_airports),
                 hub=hub, year=year, kw=dict(kw)))
    return _orig_feed_side(sabre_db, oag_db, week, origin_airports, hub, year, **kw)


def _capturing_behind_feed(sabre_db, oag_db, week, origin_airports, dest_airports, year, **kw):
    _captured_behind.setdefault("calls", []).append(
        dict(sabre_db=sabre_db, oag_db=oag_db, week=week, origin_airports=list(origin_airports),
             dest_airports=list(dest_airports), year=year, kw=dict(kw)))
    return _orig_behind_feed(sabre_db, oag_db, week, origin_airports, dest_airports, year, **kw)


def _capturing_forecast(*args, **kwargs):
    # route_forecast.forecast() multiplies feed_side/behind_feed's raw "base" by a growth factor g
    # AFTER calling them (base year -> service year), so a bare feed_side() call - which is all cells
    # A-D below can do, since C/D have no feed_side equivalent anyway - comes out g-times too small.
    # This captures forecast()'s OWN beyond_detail/behind_detail, which already have g baked in, so g
    # can be derived empirically (captured total / raw feed_side total) rather than guessed at from
    # growth/growth_years internals this script has no other way to reach.
    r = _orig_forecast(*args, **kwargs)
    _captured_forecast["beyond_detail"] = r.get("beyond_detail") or {}
    _captured_forecast["behind_detail"] = r.get("behind_detail") or {}
    return r


RFEED.feed_side = _capturing_feed_side
RFEED.behind_feed = _capturing_behind_feed
RFC.forecast = _capturing_forecast

import cortex_app as CA                # imports route_forecast -> gets the patched module


def _strip_preagg(feed_cfg):
    """Every cell in this script must read raw Sabre, not the od_single cache (which has no
    'any connection count' table to answer cell C/D with) - copy feed_cfg and drop 'preagg'."""
    fc = dict(feed_cfg or {})
    fc.pop("preagg", None)
    return fc


def _connecting_market_any(sabre_db, origin_airports, beyond_airports, year, factor_indirect):
    """Same query as route_feed.connecting_market(), except it does NOT require
    connecting_airport2 IS NULL - so double-connection itineraries are included too. Still excludes
    nonstop (connecting_airport1 IS NOT NULL stays), because that exclusion is not the refinement
    under test: a nonstop flyer was never going to reroute via a connection, filtered or not.

    CAVEAT this cell carries and A/B do not: cells A and B go through the real feed_side(), which
    wraps connecting_market() in od_source's DOT-DB1B override for any all-US pair in scope. This
    function skips that wrapper and reads raw Sabre only. Scope here is Asian destinations, not US
    airports, so the override is not expected to touch this leg - but if C or D looks stranger than
    the mechanism above predicts, check that difference before concluding the mechanism is wrong."""
    if not origin_airports or not beyond_airports:
        return {}
    oa = ",".join("?" * len(origin_airports)); ba = ",".join("?" * len(beyond_airports))
    sql = (f"SELECT destination_airport dc, SUM(passengers * {factor_indirect}) p "
           f"FROM sabre WHERE source_year=? AND origin_airport IN ({oa}) "
           f"AND destination_airport IN ({ba}) "
           f"AND connecting_airport1 IS NOT NULL "
           f"GROUP BY 1")
    con = RFEED._con(sabre_db)
    try:
        rows = con.execute(sql, [year] + list(origin_airports) + list(beyond_airports)).fetchall()
        return {r[0]: float(r[1] or 0) for r in rows}
    finally:
        con.close()


def main():
    fc = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC", aircraft="A359", freq=5)
    if not fc.get("ok"):
        print(f"Production call failed: {fc.get('error')}. STOP.")
        return

    if not _captured_beyond.get("calls") or not _captured_behind.get("calls"):
        print("STOP: monkeypatch did not capture a feed_side/behind_feed call - import order is "
              "wrong, or route_forecast.py no longer calls these the way this script assumes.")
        return

    bcall = _captured_beyond["calls"][-1]
    hcall = _captured_behind["calls"][-1]
    sabre_db, oag_db = bcall["sabre_db"], bcall["oag_db"]
    week, year = bcall["week"], bcall["year"]
    hub = bcall["hub"]
    wide_catchment = bcall["origin_airports"]
    narrow_origin = hcall["origin_airports"]          # behind_feed's own [origin], i.e. ["SJC"]
    dest_airports = hcall["dest_airports"]             # ["TPE"]
    feed_cfg_raw = _strip_preagg(bcall["kw"].get("feed_cfg"))
    factor_indirect = feed_cfg_raw.get("factor_indirect", 1.044)

    print(f"Captured production call: week={week} year={year} hub={hub}")
    print(f"  wide catchment ({len(wide_catchment)} airports): {wide_catchment}")
    print(f"  narrow origin (behind_feed's own): {narrow_origin}")
    print(f"  dest_airports: {dest_airports}\n")

    # --- known contract figures, one-way, for the sanity check ---
    KNOWN_HUB_MKT_1WAY = 719486
    KNOWN_DEST_MKT_1WAY = 185485

    # ================= BEYOND / TAIPEI SIDE =================
    # Cells A and B call the REAL feed_side() (unpatched), detail=True, and sum the "base" field of
    # its own dmap - the same base-summing convention cortex_app._feed_base uses everywhere else in
    # the codebase. feed_side builds its own scope internally for whichever origin_airports it's
    # given, so this is exactly what production would have returned for the narrow case, not a
    # manual reconstruction of its scope logic.
    side_kw = dict(bcall["kw"])
    side_kw["feed_cfg"] = feed_cfg_raw
    side_kw["detail"] = True

    _, _, dmap_A = _orig_feed_side(sabre_db, oag_db, week, wide_catchment, hub, year, **side_kw)
    cell_A_raw = sum((v.get("base") or 0) for v in dmap_A.values())
    _, _, dmap_B = _orig_feed_side(sabre_db, oag_db, week, narrow_origin, hub, year, **side_kw)
    cell_B_raw = sum((v.get("base") or 0) for v in dmap_B.values())

    # DERIVE g. route_forecast.forecast()'s own beyond_detail (captured above) already has the
    # base-year -> service-year growth factor applied; a bare feed_side() call, which is all this
    # script can do, does not. g = forecast()'s grown total / this script's own ungrown wide-catchment
    # total, both built from the identical wide catchment, so this ratio IS g cleanly, no need to
    # reach into growth/growth_years internals this script has no other route to.
    fc_beyond_total = sum((v.get("base") or 0) for v in _captured_forecast.get("beyond_detail", {}).values())
    if not cell_A_raw or not fc_beyond_total:
        print("STOP: could not derive g - forecast()'s beyond_detail or this script's own wide-"
              "catchment total came back empty. Do not trust anything below.")
        return
    g = fc_beyond_total / cell_A_raw
    print(f"Derived growth factor g = {g:.4f} (forecast()'s grown beyond total {fc_beyond_total:,.0f} "
          f"/ this script's ungrown wide-catchment total {cell_A_raw:,.0f})\n")

    cell_A = cell_A_raw * g
    cell_B = cell_B_raw * g

    # Cells C and D have no equivalent inside feed_side (it always applies the single-connection
    # filter), so these rebuild feed_side's own scope logic (hub_served + on_the_way) by hand, then
    # run the unfiltered query over it. The on_the_way centroid shifts a little between the wide and
    # narrow origin lists - both are Bay Area airports a few tens of km apart, against destinations
    # thousands of km away, so this does not meaningfully change which destinations are kept.
    scope = RFEED.hub_served(oag_db, week, hub)
    scope = [x for x in scope if x not in wide_catchment]
    scope_wide = RFEED.on_the_way(wide_catchment, hub, scope, circuity=(feed_cfg_raw or {}).get("circuity", 1.35))
    scope_narrow = RFEED.on_the_way(narrow_origin, hub, scope, circuity=(feed_cfg_raw or {}).get("circuity", 1.35))

    cell_C = sum(_connecting_market_any(sabre_db, wide_catchment, scope_wide, year, factor_indirect).values()) * g
    cell_D = sum(_connecting_market_any(sabre_db, narrow_origin, scope_narrow, year, factor_indirect).values()) * g

    print("=== SANITY CHECK: beyond/Taipei ===")
    diff_pct = abs(cell_A - KNOWN_HUB_MKT_1WAY) / KNOWN_HUB_MKT_1WAY * 100
    print(f"  Cell A (fresh, wide+filtered): {cell_A:,.0f}  vs contract: {KNOWN_HUB_MKT_1WAY:,.0f}  "
          f"({diff_pct:.1f}% difference)")
    if diff_pct > 2:
        print("  MISMATCH > 2%. STOP - do not trust cells B/C/D below without finding out why.")
        return
    print("  OK, within 2%. Proceeding.\n")

    print("=== BEYOND / TAIPEI SIDE, one-way, all single-year Sabre pulls ===")
    print(f"  A  wide catchment + single-connection filter (= production): {cell_A:,.0f}")
    print(f"  B  SJC only       + single-connection filter (catchment effect isolated): {cell_B:,.0f}")
    print(f"  C  wide catchment + any connection count      (filter effect isolated):    {cell_C:,.0f}")
    print(f"  D  SJC only       + any connection count      (both effects removed):      {cell_D:,.0f}")
    if cell_B:
        print(f"  Catchment effect (A/B): {cell_A / cell_B:.2f}x")
    if cell_C:
        print(f"  Filter effect (A/C):    {cell_A / cell_C:.2f}x")
    print(f"  Two-way, cell A x2 (compare to the 2026 table, 1,439,000): {cell_A*2:,.0f}")
    print(f"  Two-way, cell D x2 (closest proxy to a pre-refinement basis, compare to the 2025 "
          f"table, 1,097,600 - CAVEAT: cell D is grown by g, the 2025-vintage build's own growth "
          f"factor to ITS service year, FY2028, is not known here and may differ, so treat this one "
          f"comparison as illustrative, not exact): {cell_D*2:,.0f}\n")

    # ================= BEHIND / SAN JOSE SIDE =================
    cell_Ap = KNOWN_DEST_MKT_1WAY   # production figure, already known, no need to recompute here
    cell_Bp_raw = sum(RFEED.connecting_market(sabre_db, wide_catchment, dest_airports, year, factor_indirect).values())
    cell_Bp = cell_Bp_raw * g

    print("=== BEHIND / SAN JOSE SIDE, one-way ===")
    print(f"  A' SJC-fed feeders + single-connection filter (= production, behind_feed's own logic): "
          f"{cell_Ap:,.0f}")
    print(f"  B' wide catchment  + single-connection filter (SYMMETRIC test: same catchment logic as "
          f"Taipei's beyond side): {cell_Bp:,.0f}")
    if cell_Ap:
        print(f"  If San Jose got the same catchment treatment as Taipei: {cell_Bp / cell_Ap:.2f}x "
              f"the current production figure")
    print(f"  Two-way, cell A' x2 (= production, 371,000): {cell_Ap*2:,.0f}")
    print(f"  Two-way, cell B' x2 (compare to the 2025 table, 1,128,500): {cell_Bp*2:,.0f}")


if __name__ == "__main__":
    main()
