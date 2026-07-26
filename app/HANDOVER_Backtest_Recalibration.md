# Handover: full-year OAG backtest and recalibration (weekend regime)

Paste this into a new chat in the Avia QSI Tool project to start the work. It is self-contained; do not re-derive what is below, use it.

## 1. What we are doing and why

We are re-running the whole QSI backtest and recalibration on full-year operated schedules, to replace calibrations that were fit on a distorted schedule sample, and to fold in the engine logic fixes made since. The goal is a measurably more accurate engine and a stronger track record: every learned assumption, elasticity, stimulation, induced and feed parameter, and the catchment settings, re-fit on honest data and validated on a held-out grade.

Two things changed since the last calibration, and both invalidate the old numbers:

- **The schedule basis.** The previous backtest read OAG as a one-week snapshot in late May plus one in late October, then annualised from those two weeks. That skews everything that depends on capacity or seasonality: annual seats per route, frequency, achieved load factor, the induced-floor detector (measured market divided by deployed capacity), the induced load-factor table, and the seasonality profile. We are now loading full-year OAG for 2015 to 2026. By end of Friday we expect 2015 to 2019 complete; 2024 and 2025 follow. So we start the regime on 2015 to 2019 this weekend and extend as the later years land.

- **The engine.** The QSI engine has been refined since the last calibration. Catchment logic had issues in the assumptions that have been corrected, and the demand path, the induced/new-market model, the connecting feed, the P2P and connecting re-split, and the aircraft-sizing/optimiser have all moved. Parameters fit against the old engine and the old schedule sample no longer match the current engine on full-year data.

## 2. The data and the stores

- **Sabre O&D:** `C:\Avia\sabre.duckdb`, table `sabre`. Annual true-O&D, 2013 to 2025. Columns include origin/destination airport, marketing/operating airline, cabin, connecting legs, point-of-origin fields (`poo_airport`, `poo_city_name`, `poo_country`), `passengers`, `avg_base_fare_usd`, `avg_total_fare_usd`, `distance_km`, `directionality` (values `ND` and `POO`, not an outbound/return flag), `source_year`.
- **OAG schedules:** `C:\Avia\oag.duckdb`, table `oag`. This is the store being rebuilt to full-year. The OLD store held two sampled weeks per year from 2017 (late May, late October) and mixed-granularity rollups for 2015 to 2016 (a whole-year label, monthly labels, half-year labels and specific-week labels all present, so summing across labels double-counts). Do not assume the old shape.
- 16 GB box. The DuckDB run rules below are not optional.

## 3. Do this first: validate the new OAG store before trusting any run

The schedule store format is changing under us, so step one is to characterise it, not to run a backtest on assumptions.

1. `PRAGMA table_info('oag')` and list the columns. Confirm whether the full-year build carries a real date or week field, seats, frequency, aircraft, and how a year is now labelled.
2. For each year present, count distinct week/period labels and their coverage, and confirm there is no repeat of the 2015-2016 mixed-granularity rollup that double-counts. Pick one consistent label set per year and state the rule.
3. Reconcile a known route's annual seats and frequency against expectation (for example a dense trunk) to confirm the full-year sum is sane, not a two-week annualisation.
4. Confirm seats and capacity are operated capacity, not a bare schedule, and note the each-way versus two-way basis. Round-one work found a capacity-versus-schedule format trap here; check it again.

Write a short note on what the new store actually contains before anything downstream reads it.

## 4. The recalibration regime

Rebuild from the schedule up, then re-fit each learned layer, then grade honestly. Keep everything offline on the backtest until validated; do not touch the live engine tables until a layer is proven (see section 8).

**A. Rebuild the backtest spine on operated schedules.** Replace the two-week-annualised capacity with true annual operated seats and frequency per route and year from full-year OAG. This is the change that unlocks the rest, because the induced detector and the load-factor tables are ratios against capacity. This also realises the parked schedule-conditioning idea: condition each backtested launch on the airline's actual operated schedule for that year, so the engine is graded against what was really flown, not an assumed frequency.

**B. Re-fit each calibrated layer, in this order, showing full-data fit and held-out grade side by side for every candidate:**

1. Catchment: the gencost settings (`logit_scale`, `value_of_time_per_hr`), the service-value calibration and the drive-time matrix. Catchment logic was corrected, so re-fit rather than reuse.
2. Capture and destination share: the QSI capture-share and dest-share against measured O&D on domestic point-to-point where outturn exists.
3. Stimulation by carrier type (`STIM_BY_TYPE`) and the market-size P2P trim (`market_factor_for`).
4. Elasticities: own-price and airport-choice / relative-fare elasticity, now that fare is available in Sabre (`avg_base_fare_usd` as the tax-excluded price signal). This realises the parked fare-elasticity idea.
5. Induced / new-market: `INDUCED_MKT_CAP_MAX` (the detector), `INDUCED_LF` by type and haul, `INDUCED_FARE`. These were fit against distorted capacity and must be re-fit on true operated capacity. Note the FSC induced floor over-reads on feed-thin routes deployed with oversized metal; the live tool now sizes the gauge to demand and applies a load-factor floor to contain that, but the underlying floor still wants a feed-aware gate that the fuller schedule data should now make reliable.
6. Feed: the connecting parameters (`cnx_online`, `cnx_alliance`, `cnx_interline`, `behind_cap`, `circuity`, `factor_indirect`) and the total-preserving P2P/connecting re-split.
7. Size trim and the 2/3 confidence interval (`calib_interval.py`), re-fit on the new grade.
8. The all-data bucket calibration (`bucket_model.json`), re-swept once the layers above are stable.

**C. Seasonality.** With real monthly schedules, validate and re-fit the seasonality profile (`season_share`) against actual operated seasonal capacity, rather than inferring it from two snapshot weeks.

## 5. The honest scorecard and the discipline

Use the existing scorecard, do not invent a new one, and quote all tiers, not one number:

- **DISH** = fit on all data, grade all data. The ceiling and the quotable historical-fit number.
- **CV** = k-fold, whole airports or whole routes held out, graded unseen. Does it generalise.
- **MOUSE** = fit the earlier years, grade the latest year present. The strongest test available before real outturn.
- **HUMAN** = 2026-27 outturn on 2025-26 forecasts. The only fully clean test; we wait for it.

Discipline that has bitten before:

- The target is a CV or MOUSE that crosses 50% within plus or minus 20%, not just a high DISH. DISH near 55% is already reachable; the job is a correction that generalises.
- The maturity confound: an offset-0 grade (launch year outturn) rewards features that predict immaturity, which a matured forecast will not have. Grade on a mature outturn as well, and treat a lift that appears only at offset-0 with suspicion.
- The data structure: 2013 and 2015 are POO-pulled, other years ND-pulled; there is a capture step at the 2015-2016 boundary, so base absolute-level series on ND years; 2020 is absent and must be shown as a gap, never interpolated. Point of origin cannot identify a resident once they cross into another country's booking system, so do not use it for cross-border leakage magnitude.
- Spread, not bias: a multiplicative factor on any grouping only shifts a group's median, it cannot compress within-group spread. Past attempts to lift plus-or-minus-20% with post-hoc factors hit that wall. Real gains come from engine input changes (schedule conditioning, fare elasticity, induced modelling, connectivity), which is exactly what the full-year data enables.

## 6. Key files and harnesses (all in `C:\AviaDev\app` unless noted)

- `route_forecast.py`: the engine. `forecast()` is `measured market x share x dest-share x stimulation x factors`, capped at capacity, plus connecting feed, with the induced floor and the all-data bucket nudge.
- `cortex_app.py`: `calibrated_forecast`, `api_forecast`, `api_optimise`; the live wiring and the calibrated parameter set.
- `backtest.py`: the grader; `--induced-floor` threads the induced path and captures `base_fare`/`outturn_fare`. Also `back_test.py`, `back_test_v2.py`, `back_test_cohort.py` in `C:\Avia`.
- `search_adjustments.py`: the leaderboard that scores many candidate adjustments through the DISH/CV/MOUSE scorecard; add a hypothesis in one line. Free-factor space is parked (no held-out lift); the untested space is cause and attribute-keyed adjustments.
- `build_master_backtest.py` + `master_backtest.csv`: the master file, spine plus airport-year features joined at pre-launch vintage (launch year minus one), with leakage discipline (fare and load factor are outcomes, not inputs).
- `calib_interval.py`, `analyze_induced.py`, `analyze_feed.py`: the layer-specific calibration and diagnostics.
- `airport_attributes.json`, `airport_catchment_geo.csv`, `bucket_model.json`, `bucket_correct.py`.

## 7. DuckDB and environment run rules

- 16 GB box. Cap DuckDB memory (`SET memory_limit`, total divided by the number of workers), set a named `temp_directory`, use `--resume` for long runs, run four jobs not eight. Do not use pandas for the heavy pulls; aggregate in SQL.
- The sandbox cannot reach `C:\Avia`; a local session mounts it. John runs the heavy jobs with `py -3.12`.
- Mount truncation hazard: a freshly edited file read back through a bash mount can return a truncated or corrupted tail and throw a false syntax or null-byte error. Verify file contents with the Read tool, which returns the true file, before believing a parse error. Never run git from the sandbox.

## 8. Working method (how John wants this run)

- Treat it as a science project. Test everything; do not declare anything settled, dead or impossible before it has been tested. This has been a repeated correction; language should be "parked pending test", not "closed".
- For every candidate, show the full-data fit and the held-out grade together, never one without the other.
- Do not confound a run: do not mix a regime break (COVID) or a maturity difference into a comparison and attribute the result to the change under test.
- The engine and the live demo are currently in a good state. Do the calibration offline on the backtest, prove each layer on the held-out grade, and only then wire the updated table into `route_forecast.py` / `cortex_app.py`. Do not destabilise the demo mid-calibration.

## 9. Sequence for the weekend

1. Validate the new full-year OAG store (section 3) and write the note.
2. Rebuild the backtest spine on 2015 to 2019 operated schedules; confirm annual capacity and seasonality are now real, not annualised.
3. Re-fit the catchment settings and the capture/dest-share, then stimulation, then elasticities, grading each on DISH/CV/MOUSE. Bank a before-and-after on the plus-or-minus-20% hit rate at each step.
4. Re-fit induced and feed on true capacity; re-sweep the bucket model once the layers are stable.
5. Produce a before-and-after track record: the old sample-week calibration versus the new full-year calibration, on the same held-out grade, so the improvement is measured, not asserted.
6. Hand back a short changelog of every parameter that moved and by how much, and a list of any layer that did not improve (kept honest, not buried).

Extend to 2024 and 2025 when those years finish loading, then re-fit once more on the full 2015 to 2025 span before the human grade arrives with 2026-27 outturn.

## 10. Memories to read first

In the project memory: the QSI working method, the search harness, the induced modelling note, the feed recalibration note, the schedule-conditioning note, the fare-elasticity note, the accuracy plan, the airport-diagnosis method, the DuckDB run rules, and the rollback baseline. They carry the detail behind each layer above.
