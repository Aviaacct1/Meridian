# Generalised route pipeline

The Genoa-New York chain is now driven by a `RouteCase` rather than hard-coded constants, so the
same three steps run any origin-destination. The hard-coded Genoa scripts (`genoa_nyc.py`,
`build_genoa_cache.py`, `calibrate_genoa.py`) are untouched and still work; these generalise them.

## The four new files

- `route_case.py` - the `RouteCase` object. Holds everything route-specific: home airport,
  catchment centre/radius, GeoNames countries and min population, the candidate airports (each with
  a raw size pull and flags for calibration / cache-only), the destination market airports, the
  Sabre point-of-origin scope, the aircraft/sector/airspace, and the planning defaults. Serialises
  to JSON. A `genoa_nyc()` factory reproduces the validated case.
- `build_cache.py` - builds a case's road drive-time cache once (general `build_genoa_cache.py`).
- `calibrate_catchment.py` - fits the catchment to the Sabre observed split (general
  `calibrate_genoa.py`), writing the case's params file.
- `assess.py` - the whole chain end to end (general `genoa_nyc.py`): catchment -> demand ->
  load factor -> route and annual P&L, with an optional deck.

Route cases live in `app/cases/`. The first is `cases/genoa_nyc.json`, with its offline observed
split in `cases/genoa_nyc_observed.json`.

## Running a case

```
# 1. build the drive-time cache (needs internet; OSRM/ORS or self-hosted)
py -3.12 build_cache.py genoa_nyc cities5000.txt --ors-key YOUR_KEY

# 2. calibrate the catchment to the Sabre observed split (needs sabre.duckdb)
py -3.12 calibrate_catchment.py genoa_nyc cities5000.txt --sabre "C:\Avia\sabre.duckdb"

# 3. assess the route end to end
py -3.12 assess.py genoa_nyc cities5000.txt --sabre "C:\Avia\sabre.duckdb"      # live Sabre
py -3.12 assess.py genoa_nyc cities5000.txt                                     # offline (cached split)
py -3.12 assess.py genoa_nyc cities5000.txt --ppt                               # render the deck
```

Every case default is overridable on the assess CLI: `--capture --freq --econ-share --bus-fare
--econ-fare --fare-basis --plan-lf --incentive --radius-km --min-pop`. The full-override (POC)
principle is preserved: the case sets sensible defaults; the CLI overrides any of them.

Offline works: `assess.py` reads the observed split from the case's cached JSON when no `--sabre`
store is given, so a laptop / World Routes run needs no Sabre connection. A live `--sabre` run
refreshes that cache.

## Parity

`assess.py genoa_nyc cities5000.txt` with no overrides reproduces the validated reference case
(`genoa_nyc_case.json`) exactly: population 19,536,487; GOA New-York natural catchment 92,542;
repatriated 55,579; route profit 15,170 at 10.7% margin, 73.5% breakeven; annual profit 5,521,979.
Maximum difference across every numeric field is 0.

## Adding a new route

Copy `cases/genoa_nyc.json` to `cases/<your_case>.json` and edit it: home airport, catchment
centre/radius, countries, the candidate airports (set `cache_only`/`calibrate` for cross-border
competitors), the destination market, the Sabre point-of-origin scope, the aircraft and sector,
the overflown airspace. Then run the three steps above with `<your_case>` in place of `genoa_nyc`.
Per-case data files (`<case>_drive.json`, `<case>_catchment_params.json`, `<case>_observed.json`)
are found whether they sit in `cases/` or beside the app modules.

## Note on aircraft economics inputs

The reference case uses a $750 realistic business fare (the `bus_fare_ow` default in the Genoa
case), with $1,300 held as the full-business-cabin sensitivity (`premium_fare_ow`). Airport charges
for GOA and JFK in `aircraft_economics.py` are indicative placeholders, not validated tariffs; the
charges layer is a per-route input and should be firmed before any external use.
