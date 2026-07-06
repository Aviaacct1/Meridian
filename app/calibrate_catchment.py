#!/usr/bin/env python3
"""
Avia Solutions - calibrate any route case's catchment to the Sabre observed split.
==================================================================================
The general version of calibrate_genoa.py. One command:
  1. builds the case's locales from the GeoNames dump (real population),
  2. fills real road drive times from the cached matrix,
  3. reads the OBSERVED airport-choice split from the Sabre store (who departed where),
  4. calibrates the size-pull (att_exponent), access weight (logit_scale) and value-of-time
     to that observed split,
  5. writes the fitted parameters to the case's params file for reuse.

RUN (on the machine with sabre.duckdb + the dump + the cache):
    py -3.12 calibrate_catchment.py genoa_nyc cities5000.txt --sabre "C:\\Avia\\sabre.duckdb"

Use --discover first to see which point-of-origin city codes feed these airports, then pass the
catchment ones with --poo-cities A,B,C. Defaults to the case's poo_country (a reasonable first
cut for a single-country catchment). The calibration target excludes cache-only / non-calibrated
airports (e.g. a cross-border competitor absent from the country's origin records).
"""
import argparse, json, os, sys

SSE_OK = 0.05   # above this the observed target is suspect (e.g. a single-city tautology)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G, routing as R, sabre_catchment as S
    from catchment import Airport, CatchmentParams, calibrate, run_catchment, addressable_market
    from route_case import RouteCase

    ap = argparse.ArgumentParser(description="Calibrate a route case's catchment to the Sabre split.")
    ap.add_argument("case", help="route case id or path to a case JSON")
    ap.add_argument("geonames_txt")
    ap.add_argument("--cache", default=None, help="drive-time cache (default: the case's drive_cache)")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--radius-km", type=float, default=None)
    ap.add_argument("--min-pop", type=float, default=None)
    ap.add_argument("--poo-cities", default=None, help="comma POO city codes; else the case poo_country")
    ap.add_argument("--poo-country", default=None)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--discover", action="store_true", help="list the top POO cities and exit")
    ap.add_argument("--out", default=None, help="fitted-params JSON (default: the case's params_file)")
    ap.add_argument("--force", action="store_true", help="save even a poor (high-SSE) fit")
    a = ap.parse_args()

    case, base_dir = RouteCase.load_with_dir(a.case)
    radius_km = a.radius_km if a.radius_km is not None else case.radius_km
    min_pop = a.min_pop if a.min_pop is not None else case.min_pop
    cache = a.cache or case.resolve_existing("drive_cache", base_dir, [here], f"{case.case_id}_drive.json")
    out = a.out or case.resolve_existing("params_file", base_dir, [here], f"{case.case_id}_catchment_params.json")
    poo_country = a.poo_country or case.poo_country
    poo_cities = a.poo_cities.split(",") if a.poo_cities else (case.poo_cities or None)

    # the calibration target airports (cache-only / non-calibrated competitors excluded)
    cal = case.calibration_airports()
    codes = [x.code for x in cal]

    if a.discover:
        for c, nm, pax in S.catchment_poo_cities(a.sabre, codes, poo_country=poo_country, year=a.year):
            print(f"  {c}  {(nm or ''):28} {pax:>12,.0f}")
        return

    # 1-2. locales + real road times
    locs = G.near_point(a.geonames_txt, case.centre_lat, case.centre_lon, radius_km,
                        countries=case.countries, min_pop=min_pop, propensity=1.0)
    R.load_drive_time_matrix(locs, cache)
    airports = [Airport(x.code, lat=x.lat, lon=x.lon, attractiveness=x.size_pull_m) for x in cal]
    print(f"{len(locs):,} locales, real road times loaded, {len(airports)} calibration airports")

    # 3. observed split from Sabre
    observed = S.origin_airport_split(a.sabre, codes, poo_cities=poo_cities,
                                      poo_country=(None if poo_cities else poo_country), year=a.year)
    tot_obs = sum(observed.values()) or 1.0
    print("\nOBSERVED airport choice of the catchment's residents (Sabre point-of-origin):")
    for c in sorted(observed, key=lambda k: -observed[k]):
        print(f"  {c}  {observed[c]/tot_obs:5.1%}   {observed[c]:>12,.0f}")

    # 4. calibrate size-pull + access weight + value-of-time to the observed split
    best = calibrate(locs, airports, observed)
    print(f"\nFITTED: logit_scale {best['logit_scale']}  att_exponent {best['att_exponent']}  "
          f"vot_mult {best['vot_mult']}   (SSE {best['sse']:.5f})")
    print("  modelled vs observed:")
    for c in codes:
        print(f"    {c}  model {best['modelled'].get(c,0):5.1%}  obs {best['observed'].get(c,0):5.1%}")

    # 5. save fitted params + the home leakage view at the fit
    res = run_catchment(locs, airports, best['params'], home=case.home)
    addressable_market(res, case.home)
    if best['sse'] > SSE_OK and not a.force:
        print(f"\nWARNING: SSE {best['sse']:.3f} > {SSE_OK} - this observed target looks invalid "
              f"(e.g. a single point-of-origin city is a tautology, not a catchment split). "
              f"NOT saving over {os.path.basename(out)}. Re-run with a valid target, or --force.")
        return
    airports_meta = {x.code: [x.lat, x.lon, x.size_pull_m] for x in cal}
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"logit_scale": best['logit_scale'], "att_exponent": best['att_exponent'],
                   "vot_mult": best['vot_mult'], "value_of_time_per_hr": best['params'].value_of_time_per_hr,
                   "airports": airports_meta, "sse": best['sse'],
                   "modelled": best['modelled'], "observed": best['observed']}, f, indent=2)
    print(f"\n{case.home} at the fit: natural {res['home_natural']:,.0f}, retains "
          f"{res['home_retained']:,.0f} ({res['home_retained']/max(res['home_natural'],1):.0%}), "
          f"leaks {res['home_leaked']:,.0f}")
    print(f"saved fitted parameters to {out}")


if __name__ == "__main__":
    main()
