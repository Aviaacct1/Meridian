#!/usr/bin/env python3
"""
Avia Solutions - calibrate the Genoa catchment against the Sabre observed split.
================================================================================
Ties the pieces together into one command. It:
  1. builds the Genoa locales from the GeoNames dump (real population),
  2. fills real road drive times from the cached matrix (genoa_drive.json),
  3. reads the OBSERVED airport-choice split from the Sabre store (who departed where),
  4. calibrates the size-pull (att_exponent), access weight (logit_scale) and value-of-time
     to that observed split,
  5. writes the fitted parameters to genoa_catchment_params.json for reuse.

RUN (on the machine with sabre.duckdb + the dump + the cache):
    cd "C:\\Users\\Carte\\OneDrive\\Documents\\Claude\\Projects\\Avia QSI Tool\\app"
    py -3.12 calibrate_genoa.py cities5000.txt --sabre "C:\\Avia\\sabre.duckdb"

First run with --discover to see which point-of-origin city codes feed these airports, then
pass the Genoa-catchment ones with --poo-cities GOA,SVN,SPE,...  (defaults to point-of-origin
country IT, which is a reasonable first cut for a NW-Italy catchment).
"""
import argparse, json, math, os, sys


GENOA_CENTRE = (44.4133, 8.8375)
AIRPORTS = {  # code: (lat, lon, approx annual pax in millions = raw size pull, pre-damping)
    "GOA": (44.4133, 8.8375, 1.2),  "MXP": (45.6306, 8.7281, 28.5),
    "LIN": (45.4451, 9.2767, 9.3),  "BGY": (45.6739, 9.7042, 17.0),
    "TRN": (45.2008, 7.6497, 4.5),  "BLQ": (44.5354, 11.2887, 9.9),
    # NCE (Nice) deliberately EXCLUDED from calibration: it is a French airport whose
    # traffic is overwhelmingly French, so it is absent from the Italian-origin Sabre target,
    # and raw drive time overstates Italian cross-border use (needs a border penalty, not
    # straight drive time). Add it back only with a calibrated border penalty if a western-
    # Liguria study needs it; it is a minor competitor for a Genoa catchment.
}
SSE_OK = 0.05   # above this the observed target is suspect (e.g. a single-city tautology)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import geonames as G, routing as R, sabre_catchment as S
    from catchment import Airport, CatchmentParams, calibrate, run_catchment, addressable_market

    ap = argparse.ArgumentParser(description="Calibrate the Genoa catchment to the Sabre split.")
    ap.add_argument("geonames_txt")
    ap.add_argument("--cache", default=os.path.join(here, "genoa_drive.json"))
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--radius-km", type=float, default=220.0)
    ap.add_argument("--min-pop", type=float, default=5000.0)
    ap.add_argument("--poo-cities", default=None, help="comma POO city codes; else --poo-country")
    ap.add_argument("--poo-country", default="IT")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--discover", action="store_true", help="list the top POO cities and exit")
    ap.add_argument("--out", default=os.path.join(here, "genoa_catchment_params.json"))
    ap.add_argument("--force", action="store_true", help="save even a poor (high-SSE) fit")
    a = ap.parse_args()

    codes = list(AIRPORTS)
    if a.discover:
        for c, nm, pax in S.catchment_poo_cities(a.sabre, codes, poo_country=a.poo_country, year=a.year):
            print(f"  {c}  {(nm or ''):28} {pax:>12,.0f}")
        return

    # 1-2. locales + real road times
    locs = G.near_point(a.geonames_txt, GENOA_CENTRE[0], GENOA_CENTRE[1], a.radius_km,
                        countries=["IT", "FR"], min_pop=a.min_pop, propensity=1.0)
    R.load_drive_time_matrix(locs, a.cache)
    airports = [Airport(c, lat=la, lon=lo, attractiveness=sz) for c, (la, lo, sz) in AIRPORTS.items()]
    print(f"{len(locs):,} locales, real road times loaded, {len(airports)} airports")

    # 3. observed split from Sabre
    poo_cities = a.poo_cities.split(",") if a.poo_cities else None
    observed = S.origin_airport_split(a.sabre, codes, poo_cities=poo_cities,
                                      poo_country=(None if poo_cities else a.poo_country), year=a.year)
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

    # 5. save fitted params + the GOA leakage view at the fit
    res = run_catchment(locs, airports, best['params'], home="GOA")
    addr = addressable_market(res, "GOA")
    if best['sse'] > SSE_OK and not a.force:
        print(f"\nWARNING: SSE {best['sse']:.3f} > {SSE_OK} - this observed target looks invalid "
              f"(e.g. a single point-of-origin city is a tautology, not a catchment split). "
              f"NOT saving over {os.path.basename(a.out)}. Re-run with a valid target, or --force to override.")
        return
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"logit_scale": best['logit_scale'], "att_exponent": best['att_exponent'],
                   "vot_mult": best['vot_mult'], "value_of_time_per_hr": best['params'].value_of_time_per_hr,
                   "airports": AIRPORTS, "sse": best['sse'],
                   "modelled": best['modelled'], "observed": best['observed']}, f, indent=2)
    print(f"\nGOA at the fit: natural {res['home_natural']:,.0f}, retains "
          f"{res['home_retained']:,.0f} ({res['home_retained']/max(res['home_natural'],1):.0%}), "
          f"leaks {res['home_leaked']:,.0f}")
    print(f"saved fitted parameters to {a.out}")


if __name__ == "__main__":
    main()
