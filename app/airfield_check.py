#!/usr/bin/env python3
"""
Avia Cortex - airfield capability check (runway/elevation vs aircraft), the BVI/SOU layer.
===========================================================================================
The picker used to check range and fleet only; it would happily put a 737 on a 1,400 m island
strip (John, 4 Jul 2026, EIS example). This layer models what a performance engineer would flag,
NOT the full AIP analysis - it exists to (a) stop infeasible recommendations, (b) quantify the
runway-limited payload for the economics, and (c) route MARGINAL cases into the detailed
aircraft-performance work Avia does with Airbus and Boeing.

MECHANISM (validated against the Airbus Consulting SOU runway capability study, RP2541272,
Dec 2025 - app/sou_airbus_fixture.json; run `py -3.12 airfield_check.py --validate`):
a short runway does not make a route binary; it caps the available take-off weight below MTOW,
and payload then falls with distance through the fuel load:

    L_req(T, elev, wet) = tofl_ref x (1 + 0.0038 x max(0, T-15)) x (1 + 0.07 x elev_km) x 1.07_wet
    TOW_avail = MTOW x min(1, (TORA / L_req) ^ ALPHA)          ALPHA calibrated on the SOU study
    payload   = TOW_avail - OEW - trip fuel(ESAD) x 1.05 - reserves - taxi
    max_pax   = min(seats, payload / 95 kg)

BANDS (deliberate three-way, per John):
  OK           - achievable load factor comfortably clears the plan load factor.
  MARGINAL     - runway-limited payload pinches the plan LF: recommend detailed aircraft
                 performance analysis (the Airbus/Boeing work stream). The lead generator.
  NOT FEASIBLE - cannot carry a viable load on the mission; type is dropped and alternatives
                 shown (max feasible sector at full seats / reduced payload / one-stop).
  UNKNOWN      - no runway data for the airport: FAIL OPEN, no filtering, note in output.

SCENARIO: runway_override_m = the runway-extension toggle. Forecast with the extended field
and the delta against today's constraint IS the extension business case (the BVI use case).

RUNWAY DATA: app/ourairports_runways_cache.json if present (build it once from the OurAirports
public-domain files - see build_runway_cache()), else a built-in indicative table of constrained
and demo-relevant airports. Every output carries "verify against AIP" - the tool suggests, the
consultant confirms.
"""
import argparse
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ourairports_runways_cache.json")
FIXTURE = os.path.join(HERE, "sou_airbus_fixture.json")

ALPHA = 0.268            # TOW vs runway-length exponent NEAR the limit (calibrated, Airbus SOU
                         # study: second-segment/obstacle limits flatten the curve close to MTOW)
ALPHA_FAR = 0.5          # far below the calibrated range the physics steepens towards the
                         # balanced-field rule (field length ~ weight squared -> TOW ~ L^0.5)
R_KNEE = 0.85            # switch point between the two regimes (TORA / required length)
KT_PER_C = 0.0038        # required-length growth per deg C above 15 (calibrated, SOU 17C->28C)
K_ELEV = 0.07            # +7% required length per 1,000 m elevation (density-altitude rule)
WET_FACTOR = 1.07
PAX_KG = 95.0            # per pax incl. bags (the Airbus study's assumption)
RESERVE_KG_NB = 2300.0   # narrowbody/regional fixed reserves (alternate + final); widebody x2.6
TAXI_KG_NB = 150.0
CONTINGENCY = 1.05       # JAR 5% on trip fuel
DEFAULT_TEMP_C = 23.0    # warm-season planning default when no season given

# Per-type performance anchors: OEW kg, reference take-off field length at MTOW (m, sea level
# ISA dry) and cruise ground speed kt. Published figures except where marked CAL (calibrated to
# the Airbus SOU study) or PROXY. tofl_ref is an EFFECTIVE anchor (includes typical second-
# segment/obstacle margins), not a brochure minimum.
PERF = {
    "A319": dict(oew_kg=40800,  tofl_ref_m=1750, cruise_kt=447),
    "A320": dict(oew_kg=42600,  tofl_ref_m=2000, cruise_kt=447),
    # CAL: SOU study anchor - tofl_ref belongs to the 73.5t variant Airbus analysed, NOT the
    # 79t max-gross in the aircraft DB; the curve anchors here and caps at the DB MTOW.
    "A20N": dict(oew_kg=44800,  tofl_ref_m=1807, cruise_kt=450, ref_mtow_kg=73500),
    "A321": dict(oew_kg=48500,  tofl_ref_m=2200, cruise_kt=450),
    "A21N": dict(oew_kg=50600,  tofl_ref_m=2300, cruise_kt=450),
    "A21X": dict(oew_kg=52700,  tofl_ref_m=2500, cruise_kt=450),
    "B738": dict(oew_kg=41400,  tofl_ref_m=2200, cruise_kt=447),
    "B38M": dict(oew_kg=45070,  tofl_ref_m=2350, cruise_kt=450),
    "B752": dict(oew_kg=58400,  tofl_ref_m=2070, cruise_kt=460),
    "B763": dict(oew_kg=90000,  tofl_ref_m=2600, cruise_kt=460),
    "A333": dict(oew_kg=124500, tofl_ref_m=2770, cruise_kt=470),
    "A339": dict(oew_kg=137000, tofl_ref_m=2770, cruise_kt=470),
    "B788": dict(oew_kg=119000, tofl_ref_m=2600, cruise_kt=480),
    "B789": dict(oew_kg=128850, tofl_ref_m=2800, cruise_kt=480),
    "A359": dict(oew_kg=142400, tofl_ref_m=2670, cruise_kt=480),
    "B77W": dict(oew_kg=167800, tofl_ref_m=3050, cruise_kt=480),
    "E170": dict(oew_kg=21140,  tofl_ref_m=1650, cruise_kt=430),
    "E190": dict(oew_kg=27720,  tofl_ref_m=2050, cruise_kt=430),
    "E195": dict(oew_kg=28970,  tofl_ref_m=2180, cruise_kt=430),
    "DH8D": dict(oew_kg=17120,  tofl_ref_m=1425, cruise_kt=360),
    "CRJ900": dict(oew_kg=21430, tofl_ref_m=1940, cruise_kt=430),
    "SF34": dict(oew_kg=13720,  tofl_ref_m=1300, cruise_kt=250),
    "C919": dict(oew_kg=45700,  tofl_ref_m=2000, cruise_kt=450),   # PROXY
    "C909": dict(oew_kg=24955,  tofl_ref_m=1700, cruise_kt=430),   # ARJ21-700
}

# Built-in runway overrides: ONLY entries with AIP-grade provenance that should beat the
# generic OurAirports cache (which carries physical length, not TORA, and is the source for
# everything else - 6,797 airports via ourairports_runways_cache.json). Add here only when a
# verified AIP/TORA figure differs materially from the cache. Always verify against the AIP.
BUILTIN_RUNWAYS = {
    "SOU": (1814, 13),   # TORA RWY20 per the Airbus SOU study (RP2541272); physical is 1,723 m
    "EIS": (1414, 5),    # Tortola/Beef Island - the BVI case (John, 4 Jul 2026)
    "LCY": (1508, 6),    # steep approach / special ops: length alone overstates capability
}

# Terrain / special-procedures airports where length + elevation understate the difficulty
# (steep approaches, one-way ops, terrain escape, wind limits, crew certification). Never
# cleared outright: capped at MARGINAL -> detailed performance analysis. Curated; extend.
SPECIAL_AIRPORTS = {
    "LCY": "steep approach (5.5 deg), special certification",
    "PBH": "terrain, one-way visual procedures (Paro)",
    "INN": "terrain, special approach procedures",
    "FNC": "wind limits, displaced approach (Madeira)",
    "TGU": "terrain, short field (Toncontin)",
    "ASE": "terrain, one-way ops, high elevation",
    "SBH": "short field, slope, special ops (St Barth)",
    "GIB": "wind shear off the Rock, road crossing",
    "CST": "short field", "LUA": "terrain (Lukla)",
    "QND": "terrain", "KTM": "terrain departure procedures (Kathmandu)",
    "SMI": "terrain, short field (Samos)", "SKP": "terrain procedures",
}

_RUNWAYS = None


def _runways():
    global _RUNWAYS
    if _RUNWAYS is None:
        d = {}
        try:
            if os.path.exists(CACHE):
                d.update({k.upper(): tuple(v) for k, v in json.load(open(CACHE)).items()})
        except Exception:
            pass
        # curated built-ins WIN over the generic cache: they carry AIP-grade TORA where we
        # have it (e.g. SOU 1,814 m per the Airbus study vs 1,723 m physical length)
        d.update(BUILTIN_RUNWAYS)
        _RUNWAYS = d
    return _RUNWAYS


def runway_for(iata, override_m=None):
    """(tora_m, elevation_m) or (None, None) when unknown. override_m = extension scenario."""
    r = _runways().get((iata or "").upper())
    if override_m:
        return float(override_m), (r[1] if r else 0.0)
    return (float(r[0]), float(r[1])) if r else (None, None)


def tow_available(code, tora_m, temp_c=DEFAULT_TEMP_C, elev_m=0.0, wet=True, mtow_kg=None):
    """Runway-limited take-off weight (kg) for the type at this field. The calibrated power
    curve is anchored at (ref_mtow_kg, tofl_ref_m) - the weight variant it was calibrated on -
    and CAPPED at the operating MTOW; far below the calibrated range the exponent steepens to
    the balanced-field rule so a genuinely short strip is not flattered (the EIS lesson)."""
    from aircraft_economics import AIRCRAFT
    p = PERF.get(code)
    ac = AIRCRAFT.get(code)
    if not p or not ac or not tora_m:
        return None
    mtow = float(mtow_kg or ac["mtow_kg"])
    ref_w = float(p.get("ref_mtow_kg") or ac["mtow_kg"])
    l_req = (p["tofl_ref_m"]
             * (1.0 + KT_PER_C * max(0.0, float(temp_c) - 15.0))
             * (1.0 + K_ELEV * float(elev_m) / 1000.0)
             * (WET_FACTOR if wet else 1.0))
    r = tora_m / l_req
    if r >= R_KNEE:
        tow = ref_w * r ** ALPHA                     # covers r > 1: slow growth above the
    else:                                            # anchor until the MTOW cap bites
        tow = ref_w * (R_KNEE ** ALPHA) * (r / R_KNEE) ** ALPHA_FAR
    return min(tow, mtow)


def mission_pax(code, tora_m, dist_nm, temp_c=DEFAULT_TEMP_C, elev_m=0.0, wet=True,
                mtow_kg=None, pax_kg=PAX_KG):
    """Max passengers on the mission at the runway-limited weight (payload = pax only)."""
    from aircraft_economics import AIRCRAFT
    p = PERF.get(code)
    ac = AIRCRAFT.get(code)
    if not p or not ac:
        return None
    tow = tow_available(code, tora_m, temp_c, elev_m, wet, mtow_kg)
    if tow is None:
        return None
    wide = ac.get("category", "").startswith("Wide")
    reserves = RESERVE_KG_NB * (2.6 if wide else 1.0)
    taxi = TAXI_KG_NB * (2.0 if wide else 1.0)
    trip = ac["fuel_burn_kg_per_bh"] * (float(dist_nm) / p["cruise_kt"]) * CONTINGENCY
    payload = tow - p["oew_kg"] - trip - reserves - taxi
    seats = ac["econ_seats"] + ac["bus_seats"]
    return max(0, min(seats, int(payload / pax_kg)))


def capability(code, origin_iata, dist_km, temp_c=None, plan_lf=0.85,
               runway_override_m=None):
    """The three-band verdict for one type at one origin field.
    Returns dict(band, tora_m, tow_avail, max_pax, seats, lf_max, note). Band UNKNOWN when
    runway data is missing (fail open - callers must not filter on UNKNOWN)."""
    from aircraft_economics import AIRCRAFT
    ac = AIRCRAFT.get(code)
    if not ac or code not in PERF:
        return {"band": "UNKNOWN", "note": "no performance anchors for this type"}
    tora, elev = runway_for(origin_iata, runway_override_m)
    if not tora:
        return {"band": "UNKNOWN", "tora_m": None,
                "note": "no runway data for this airport - add to the cache or verify AIP"}
    t = DEFAULT_TEMP_C if temp_c is None else float(temp_c)
    dist_nm = float(dist_km) / 1.852
    pax = mission_pax(code, tora, dist_nm, t, elev)
    tow = tow_available(code, tora, t, elev)
    seats = ac["econ_seats"] + ac["bus_seats"]
    lf_max = (pax / seats) if seats else 0.0
    if pax is None or pax <= 0 or lf_max < 0.60:
        band = "NOT_FEASIBLE"
        note = (f"runway-limited: cannot carry a viable load over {dist_km:.0f} km from "
                f"{origin_iata} ({tora:.0f} m TORA). Verify against AIP.")
    elif lf_max < plan_lf + 0.03:
        band = "MARGINAL"
        note = (f"runway-limited to ~{pax} seats ({lf_max*100:.0f}% of cabin) on this mission - "
                f"recommend detailed aircraft performance analysis (Airbus/Boeing work). "
                f"Verify against AIP.")
    else:
        band = "OK"
        note = f"field check clears at ~{pax} seats available. Indicative; verify against AIP."
    # extreme elevation is thrust-limited in ways the length model does not capture: never
    # clear it outright - route it into the detailed performance work.
    if band == "OK" and (elev or 0) > 2500:
        band = "MARGINAL"
        note = (f"high-elevation field ({elev:.0f} m): length check clears but density-altitude "
                f"thrust limits need detailed aircraft performance analysis. Verify against AIP.")
    # terrain / special-procedures fields: the length model cannot see the approach plate
    sp = SPECIAL_AIRPORTS.get((origin_iata or "").upper())
    if band == "OK" and sp:
        band = "MARGINAL"
        note = (f"special-procedures airport ({sp}): length check clears but operations need "
                f"detailed aircraft performance analysis. Verify against AIP.")
    return {"band": band, "tora_m": tora, "elev_m": elev, "tow_avail_kg": round(tow) if tow else None,
            "max_pax": pax, "seats": seats, "lf_max": round(lf_max, 3), "temp_c": t, "note": note}


def max_sector_km(code, origin_iata, temp_c=None, plan_lf=0.85, runway_override_m=None):
    """Longest sector (km) the type can fly from this field with plan_lf of the cabin - the
    honest alternative shown when the asked route is NOT_FEASIBLE."""
    lo, hi = 100.0, 18000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        c = capability(code, origin_iata, mid, temp_c, plan_lf, runway_override_m)
        if c.get("band") in ("OK",):
            lo = mid
        else:
            hi = mid
    return round(lo, -1)


def screen(codes, origin_iata, dest_iata, dist_km, temp_c=None, plan_lf=0.85,
           runway_override_m=None):
    """Both-ends check for a candidate list. Returns {code: worst-band capability dict};
    the binding end is whichever field gives the lower max_pax. UNKNOWN never filters."""
    out = {}
    for code in codes:
        a = capability(code, origin_iata, dist_km, temp_c, plan_lf, runway_override_m)
        b = capability(code, dest_iata, dist_km, temp_c, plan_lf)
        pick = a
        if a.get("band") == "UNKNOWN" and b.get("band") != "UNKNOWN":
            pick = b
        elif b.get("band") != "UNKNOWN" and (b.get("max_pax") or 9999) < (a.get("max_pax") or 9999):
            pick = dict(b, note=f"destination field binds: {b['note']}")
        out[code] = pick
    return out


def build_runway_cache(runways_csv, airports_csv=None, out=CACHE):
    """One-off: build the global cache. Only runways.csv is needed
    (https://davidmegginson.github.io/ourairports-data/runways.csv - public domain); the
    ICAO->IATA mapping and elevations come from the airportsdata package. Pass airports.csv
    as well to prefer OurAirports' own mapping. {IATA: [longest_open_runway_m, elevation_m]}."""
    ident = {}
    if airports_csv and os.path.exists(airports_csv):
        for r in csv.DictReader(open(airports_csv, encoding="utf-8")):
            ia = (r.get("iata_code") or "").strip().upper()
            if ia:
                try:
                    elev = float(r.get("elevation_ft") or 0) * 0.3048
                except ValueError:
                    elev = 0.0
                ident[r["ident"]] = (ia, elev)
    else:
        import airportsdata
        for icao, rec in airportsdata.load().items():   # keyed by ICAO ident
            ia = (rec.get("iata") or "").strip().upper()
            if ia:
                try:
                    elev = float(rec.get("elevation") or 0) * 0.3048   # airportsdata is feet
                except (ValueError, TypeError):
                    elev = 0.0
                ident[icao] = (ia, elev)
    best = {}
    for r in csv.DictReader(open(runways_csv, encoding="utf-8")):
        if str(r.get("closed", "0")).strip() in ("1", "yes", "true"):
            continue
        who = ident.get(r.get("airport_ident"))
        if not who:
            continue
        ia, elev = who
        try:
            ln = float(r.get("length_ft") or 0) * 0.3048
        except ValueError:
            continue
        if ln > 0 and (ia not in best or ln > best[ia][0]):
            best[ia] = (round(ln), round(elev))
    json.dump(best, open(out, "w"))
    print(f"runway cache: {len(best)} airports -> {out}")
    return out


# ------------------------------------------------------------------ validation
def validate(fixture_path=FIXTURE, tol=0.05):
    """Reproduce the Airbus SOU study (the lock test). PASS = every mission row within tol."""
    fx = json.load(open(fixture_path))
    tora = fx["airport"]["tora_m"]
    temps = {"winter": 17.0, "summer": 28.0}
    code, mtow = "A20N", fx["aircraft"]["mtow_kg"]
    print(f"{'dest':5} {'season':7} {'esad':>6} {'rwy':>4} {'Airbus':>7} {'model':>6} {'err':>7}")
    worst, fails = 0.0, 0
    for m in fx["missions"]:
        for rwy, key in (("02", "pax_rwy02"), ("20", "pax_rwy20")):
            got = mission_pax(code, float(tora[rwy]), m["esad_nm"], temps[m["season"]],
                              elev_m=13.0, wet=True, mtow_kg=mtow)
            want = m[key]
            err = (got - want) / want
            worst = max(worst, abs(err))
            flag = "" if abs(err) <= tol else "  FAIL"
            fails += abs(err) > tol
            print(f"{m['dest']:5} {m['season']:7} {m['esad_nm']:>6} {rwy:>4} {want:>7} "
                  f"{got:>6} {err*100:>6.1f}%{flag}")
    # structural checks the study headlines
    tw = {s: {r: tow_available(code, float(tora[r]), temps[s], 13.0, True, mtow)
              for r in ("02", "20")} for s in temps}
    print(f"\nrunway-limited TOW  model vs Airbus:")
    for s, want in (("winter", fx["runway_limited_tow_kg"]["winter_17C"]),
                    ("summer", fx["runway_limited_tow_kg"]["summer_28C"])):
        for r in ("02", "20"):
            e = (tw[s][r] - want[r]) / want[r]
            print(f"  {s} rwy{r}: {tw[s][r]:,.0f} vs {want[r]:,} ({e*100:+.1f}%)")
    ok = fails == 0
    print(f"\n{'PASS' if ok else 'FAIL'}: worst mission error {worst*100:.1f}% "
          f"(tolerance {tol*100:.0f}%), {fails} rows out")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Airfield capability check / SOU-study validation.")
    ap.add_argument("origin", nargs="?", help="origin IATA, e.g. EIS")
    ap.add_argument("--type", default=None, help="aircraft code, e.g. A20N (default: all)")
    ap.add_argument("--dist", type=float, default=None, help="sector km")
    ap.add_argument("--temp", type=float, default=None)
    ap.add_argument("--extend", type=float, default=None, help="runway extension scenario (m)")
    ap.add_argument("--validate", action="store_true", help="reproduce the Airbus SOU study")
    ap.add_argument("--build-cache", nargs="+", metavar="RUNWAYS_CSV [AIRPORTS_CSV]",
                    help="build the global runway cache from OurAirports runways.csv "
                         "(airports.csv optional; airportsdata fills the mapping otherwise)")
    a = ap.parse_args()
    if a.validate:
        raise SystemExit(0 if validate() else 1)
    if a.build_cache:
        build_runway_cache(*a.build_cache)
        return
    if not a.origin:
        print("give an origin IATA (or --validate / --build-cache)")
        return
    from aircraft_economics import AIRCRAFT
    codes = [a.type] if a.type else sorted(PERF)
    tora, elev = runway_for(a.origin, a.extend)
    print(f"{a.origin.upper()}: TORA {tora or 'unknown'} m, elev {elev or 0:.0f} m"
          + (f"  [EXTENSION SCENARIO {a.extend:.0f} m]" if a.extend else ""))
    for code in codes:
        if code not in AIRCRAFT:
            continue
        if a.dist:
            c = capability(code, a.origin, a.dist, a.temp, runway_override_m=a.extend)
            print(f"  {code:7} {c['band']:13} {c.get('max_pax','-'):>4}/{c.get('seats','-'):>3} pax  {c['note']}")
        else:
            ms = max_sector_km(code, a.origin, a.temp, runway_override_m=a.extend)
            print(f"  {code:7} max sector at 85% cabin: {ms:,.0f} km")


if __name__ == "__main__":
    main()
