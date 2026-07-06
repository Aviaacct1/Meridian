# QSI Tool - Handover Note

**Date:** 27 June 2026
**Author:** Avia Solutions
**Purpose:** Carry the build into a fresh chat without losing context. Read this first, then the project memory files. Everything below reflects the state at the end of the 27 June session.

---

## 1. What the tool is

A route-forecasting tool that takes a proposed air route and runs it end to end: who lives in the catchment, how much of the market a service would win, the resulting passenger forecast, and the route, annual and network profitability. It turns the manual SJC-era analysis into a repeatable engine, while keeping the validated QSI method unchanged.

The QSI method is frozen and must not change:

    qsi = frequency x ET-coefficient x connection-type-coefficient x service-level-coefficient

ET-coefficient = 1 / ((int(excess_hours / 0.1) + 1) ^ 0.8); connection-type ONLINE 1.0 / ALLIANCE 0.75 / INTERLINE 0.25; service-level nonstop 1.0 / one-stop 0.20 / two-stop 0.40. QSI1 and QSI2 (reverse direction) are averaged. These coefficients are validated against the analyst lookup and reproduced exactly; do not alter them.

---

## 2. Current state: the chain is closed

The tool now runs as one chain, every link built and feeding the next:

    catchment (who lives near the airport x destination trip-rate)
      -> addressable market + leakage
      -> QSI capture (schedule fair-share a home nonstop wins)
      -> passenger forecast (x stimulation, recapture of leaked demand)
      -> implied load factor for a proposed aircraft + frequency
      -> revenue -> route P&L -> annual P&L -> network / fleet P&L

`app/route_assessment.py` (`assess_route`) ties the whole chain in one call.

---

## 3. Module inventory (app/)

**Demand side**

- `qsi_score.py` - single source of truth for the QSI formula (ET_FACTOR 0.8, connection and service coefficients, `et_coeff`, `itinerary_qsi`). Built to stop coefficient drift across the codebase. Validated: reproduces the analyst ET lookup exactly.
- `oag_store.py` - SQL leg loader from `oag.duckdb`. `load_legs_for_market(db, week, catchment, proposed_hub, bidirectional)` pulls a market-scoped set of legs and maps store rows to the `build_connections` leg format. `list_weeks()`, `_dedupe()`. Bidirectional adds catchment-departing and hub-to-beyond legs for QSI2.
- `run_multihub_qsi.py` - the multi-hub QSI run. Now imports from `qsi_score`, takes `--db`/`--week` (store-driven) and `--qsi2` (reverse-direction averaging). The `arr1` filter excludes catchment-origin legs, which removed the intra-catchment over-counting that was diluting capture.

**Catchment side**

- `catchment.py` - the airport-choice engine. `Airport` (code, lat, lon, fare, attractiveness, service_value), `Locale` (name, population, propensity, business_share, lat, lon, drive_min, demand_by_purpose), `CatchmentParams` (method, value_of_time, vot_by_purpose, surface cost, speed, road factor, logit_scale). Two modes: drivetime (nearest airport plus a contested band) and gencost (logit on generalised cost = surface cost + value-of-time x access time + fare - service_value, attractiveness as a size multiplier). `run_catchment` returns per-airport catchment, a leakage matrix and repatriable demand; `segment=True` allocates business and leisure separately with their own value-of-time. `calibrate()` grid-fits logit_scale and a value-of-time multiplier to observed shares. `addressable_market()`, `forecast_from_addressable()`, `apply_observed_overlay()` (cell-data blend), `drive_times_from_provider()` (isochrone hook). Validated on real Istanbul slide data (IST 74.4% / SAW 17.2% / NEW 8.3%); calibration recovered an observed Genoa/Milan 28/72 split near-exactly.
- `geonames.py` - offline population loader. Reads a free GeoNames dump into `Locale` objects so a population-weighted catchment runs with no internet. `load_geonames(path, countries, bbox, min_pop, propensity, business_share, propensity_fn, feature_codes)` and `near_point(path, lat, lon, radius_km, ...)`. Validated offline end to end (GeoNames population -> Locale -> run_catchment, no network).
- `routing.py` - real road drive times ("half one" of the isochrone upgrade). `osrm_table` (public or self-hosted OSRM, no key) and `ors_matrix` (OpenRouteService, free key) return a road-minutes matrix; `build_drive_time_matrix(...)` derives it once online and caches it to JSON; `load_drive_time_matrix(...)` fills each locale's `drive_min` offline thereafter; `make_great_circle_provider()` exercises the `drive_times_from_provider` hook with no internet. Stdlib only (urllib), nothing to install. Validated: build -> cache -> offline reload round-trips identically; the catchment then runs on real road minutes; missing pairs fall back to the great-circle proxy automatically.
- `route_assessment.py` - the orchestrator. `assess_route(...)` runs catchment -> addressable -> forecast and, given an aircraft, frequency and economics kwargs, the implied load factor and the route and annual P&L.
- `sabre_catchment.py` - the observed airport-choice split from `sabre.duckdb` (the calibration target). `origin_airport_split(db, airports, poo_cities/poo_country, ...)` returns, for residents of a catchment, how many passengers actually departed each airport (Sabre point-of-origin). `catchment_poo_cities(...)` lists candidate point-of-origin city codes.
- `calibrate_genoa.py` - one-command calibration: GeoNames locales -> cached road times -> Sabre observed split -> `calibrate()` -> fitted parameters to `genoa_catchment_params.json`. `--discover` lists the point-of-origin cities first.
- `route_demand.py` - route-specific demand. `calibrate_service_values` (fits per-airport NYC service constants to the observed Sabre split), `market_allocation`, `bounded_repatriation` (the defensible figure, bounded by the home catchment x capture), `repatriation` (raw scenario, over-reaches - do not use raw).
- `genoa_nyc.py` - the whole chain on one route: catchment -> calibrated demand -> bounded repatriation -> implied load factor -> route + annual P&L. `--ppt` renders the deck. Knobs: `--capture --freq --econ-share --bus-fare --fare-basis --plan-lf --incentive`.
- `route_deck.py` - on-brand forecast + P&L deck (`build_deck`) driven by live data: forecast dict + the `compute()` cost stack. Used by `genoa_nyc.py --ppt`.

**Economics side**

- `aircraft_economics.py` - the cost stack. Sector-aware heavy maintenance from the Airbus reserves (all Airbus types), ownership as a blended owned-plus-leased cost of capital by airline type and age (lessor load stripped out), utilisation by airline type and sector, crew by airline type. `RoutePnL`, `AnnualRoutePnL`, `network_pnl()`, and the bridge helpers (`route_pnl_from_config`, `route_pnl_from_revenue`, `airline_type_from_carrier`, `map_aircraft_code`). The E190 / Maverick anchor stays on hand-set values and the regression is intact ($14,912 cost / 32.7% margin; John's run confirmed 22,098 / 14,905 / 7,193 / 32.5%). Every output carries the directional-guidance disclaimer.
- `output_workbook.py` - `StandardOutputWriter` renders the turnaround and annual P&L with the cost bases and the disclaimer.
- `economics_slide.py` - PowerPoint route-economics P&L slide (Avia navy).
- `build_business_case.py` - one-command forecast + revenue + economics -> workbook.
- `network_report.py` - multi-route network workbook.
- `sabre_ingest.py` - one-off annual Sabre ODPOO CSV -> `sabre.duckdb` (streaming, robust CSV read with fallbacks).
- Test harnesses: `test_economics_wiring.py`, `test_network.py` (run locally on John's machine).

**Data stores**

- `sabre.duckdb` - circa 15 GB, table `sabre` (ODPOO point-of-origin demand).
- `oag.duckdb` - circa 165 MB, table `oag` (schedule/capacity route inventory).

---

## 4. Key principles to preserve

- **QSI formula is frozen.** Validate first, then layer measurable improvements; never change the coefficients.
- **Full override (POC principle).** Every key input must be user-overridable (technical users craft bespoke inputs) with sensible auto-defaults (non-technical users). Catchment included.
- **Offline must work.** A laptop / World Routes version runs on stored assumptions with no internet. GeoNames gives the offline population layer; great-circle drive-time proxy is the offline default.
- **Economics is directional.** The disclaimer stays on every economics output: directional guidance, not an airline's actual cost base.
- **Citation-first.** Every number should trace to a citable source with a date. The full assumptions-register citation sweep is deferred to pre-launch; current stage is POC moving to test/beta.

---

## 5. What is left

**On John's machine (consolidation)**

- Point `qsi_market.py` and `QSIEngine` at `qsi_score` so all QSI scoring runs through the one module; retire the old coefficient copies.
- Run the SJC-HKG acceptance test (expected circa 65.6%) before retiring anything.
- Re-point `goa_nyc_forecast` at the store and the catchment bridge functions.

**Data-dependent**

- **Genoa real run is under way.** The cache is built (`genoa_drive.json`, 885 locales x 7 airports, real OSRM road times). The first real catchment run exposed that the airport-size pull is uncalibrated and far too strong (GOA retained 4% of its natural catchment, implausible). Fixed by adding a calibrated `att_exponent` (size-pull dampening) to `catchment.py` and `calibrate()`. NEXT: run `calibrate_genoa.py` against `sabre.duckdb` to fit `att_exponent`, `logit_scale` and value-of-time to the real Sabre point-of-origin split, then the Genoa shares are calibrated. Decide whether to calibrate the general (all-destinations) catchment or the New-York route case first.
- Load Sabre 2025 into `sabre.duckdb`.
- Ingest Monday's additional OAG weeks and re-run the calibration.

**Real road drive times - DONE (27 June, "half one").** `routing.py` replaces the great-circle proxy with cached OSRM / OpenRouteService road times. `build_genoa_cache.py` is a one-command builder (Genoa airports, centre and 220 km radius baked in): download a GeoNames dump, then `py -3.12 build_genoa_cache.py cities5000.txt` writes `genoa_drive.json`. Must be run on a machine with internet and from the same dump used at run time (the cache keys to locale coordinates). Use `--ors-key` or a self-hosted `--osrm` for anything past a quick try; the public OSRM demo is rate-limited. Validated offline end to end via the proxy path. Next: run it for real for Genoa, then calibrate.

**Deferred to pre-final-product ("half two")**

- **Switch catchment population to isochrone-summed gridded data** (John's call, 27 June). City-centroid population from GeoNames is a proxy; real catchments do not follow city boundaries. Before the final product, sum population within real drive-time bands using a raster / H3 source: GHS-POP (EU JRC, 100m / 1km) or Kontur (400m H3 hexagons, free on the Humanitarian Data Exchange). This needs raster / GIS handling (GDAL / GEOS / PROJ under rasterio / geopandas) and isochrone polygons (ORS or Valhalla). Deliberately held until a real calibration case (Genoa) shows the centroid proxy costs material accuracy, so the heavier engine launches proven rather than just heavier. The GeoNames-plus-`routing.py` path is the POC / beta route; gridded-plus-isochrone is the production upgrade.
- Full assumptions-register citation sweep.

---

## 6. Where we are, and what is left

The Genoa-New York case is built end to end and validated on real data: GeoNames population, OSRM road times, a catchment calibrated to the Sabre point-of-origin split (SSE 0.0009), a bounded route demand, an implied load factor, the route and annual P&L, and three decks (a forecast+P&L deck `genoa_nyc.py --ppt`, and a plain-English explainer). The realistic case is a daily A321XLR at ~85% load, ~11% margin, 74% breakeven, ~$5.5m a year. Two sanity-checks were caught and fixed: the Sabre fare is round-trip (halved to one-way), and the plan load factor is capped at 85% not the demand-implied 95%.

What is left, in priority order:

1. **Generalise the route case (the POC-to-product step) — FOUNDATION BUILT, needs refinement.** `route_engine.py` (`assess(origin, dest, ...)`) now runs ANY city pair: resolves airports via `airportsdata`, finds competing airports near the origin, builds the GeoNames catchment, allocates with the Genoa-calibrated parameters, sizes demand by a propensity, and runs the economics for the great-circle sector. Validated end to end on Bristol-NY, Edinburgh-Boston, Genoa-NY. THREE refinements needed before it's trustworthy for arbitrary pairs: (a) restrict competing airports to those with real scheduled service from the OAG store (raw radius sweeps in tiny airfields and the wrong hubs — Bristol's 250 km pulled in all of London, 51m pop); (b) resolve a city to its main commercial airport(s) (New York came back as NYS not JFK/EWR/LGA); (c) a propensity / demand-sizing model calibrated to the Genoa benchmark, refined against Sabre where a market has data. Runtime data backbone = GeoNames + airportsdata + OAG (165 MB); Sabre (15 GB) only for offline calibration. The live app (`cortex_app.py`) currently drives the baked Genoa case; point it at `route_engine.assess` once the three refinements land, and it becomes the any-two-cities tool John wants.
2. **Firm the Genoa case inputs.** Cabin mix (premium share and fare) is the last judgement input on the economics; confirm the Sabre fare basis by eyeballing a few raw rows; consider the capture rate (0.65 assumed).
3. **Catchment refinements (for the final product, not needed for a sound number).** Add Nice with a calibrated border penalty so the natural catchment (currently ~3.3m, a little high) is right; sharpen the access sensitivity against a known diversion case so the route scenario stands alone without the hand bound; then half-two, isochrone-summed raster population (GHS-POP / Kontur), only if the centroid proxy proves materially off.
4. **Local consolidation (your machine).** Point `qsi_market` / `QSIEngine` at `qsi_score`; run the SJC-HKG acceptance test (~65.6%); re-point `goa_nyc_forecast` at the store and catchment bridge.
5. **Data refreshes.** Load Sabre 2025. OAG weeks DONE (29 Jun): `oag.duckdb` now holds 17 twice-yearly weeks (May+Oct 2015-2019 and 2023-2026; 2020-22 absent by design), 7 regions each, ~700-820k flights/week. Note: `ingest_all_oag.py` now enumerates with `os.listdir` not `glob` (glob returned nothing on the Egnyte virtual drive where listdir worked). Next: use the QSI of these schedules to set per-airport service strengths in the route cases instead of hand-set values.
6. **Pre-launch.** Full assumptions-register citation sweep.

**Start the next chat on item 1: generalise the route pipeline so it runs any origin-destination, then re-run Genoa-New York through the general path to confirm it reproduces these numbers.** Items 2 and 4 are good parallel/quick wins.

Project memory files hold the detail: `qsi-project-state`, `qsi-catchment-design`, `qsi-method-improvements`, `qsi-aircraft-economics`, `qsi-knowledge-assets`, `qsi-oag-scope`, `qsi-open-judgement-calls`, `qsi-people`.

---

## 7. Recurring sandbox note

The OneDrive mount can serve a stale or truncated copy of a just-edited file. When testing in the Linux sandbox, treat the Edit / Write result as authoritative and, if a test imports a module that was just edited, copy the current file into the test directory (or write it to `/tmp`) before running.
