# Forecast back-test — overnight run brief

**Date:** 30 June 2026
**Author:** Avia Solutions

## What this does

`backtest.py` grades the tool's forecast against reality, automatically, across the whole OAG
history. It needs no hand-built route list: the OAG store is the inventory. A nonstop airport
pair that has scheduled service in year Y but not in Y-1 or Y-2 is a route that launched around
Y. For each one it:

1. forecasts the route AS IF standing the year before, using the Y-1 OAG served index and the
   Y-1 Sabre year for propensity (no peeking at post-launch data), with the prior capture (0.30);
2. reads the OUTTURN: what the sector actually carried in the first full year after launch
   (Sabre, point-to-point plus all connecting feed, both directions);
3. tags the airline TYPE (FSC / LCC / ULCC / Regional) from the OAG carrier category;
4. reports forecast / outturn per route and the **median ratio by type** — the calibration
   factor we fold back into each type's prior.

## Run it

Quick sanity pass first (one year, long-haul only, capped — a few minutes):

```
cd "C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool\app"
py -3.12 backtest.py --oag "C:\Avia\oag.duckdb" --sabre "C:\Avia\sabre.duckdb" --start-year 2017 --min-gcd 1500 --limit 40
```

Then the full overnight run (all launch years 2017-2025, every type, writes a CSV):

```
py -3.12 backtest.py --oag "C:\Avia\oag.duckdb" --sabre "C:\Avia\sabre.duckdb" --out backtest_full.csv
```

Knobs: `--start-year YYYY` one year only; `--min-gcd 1500` drop short sectors; `--limit N` cap
routes; `--capture 0.30` the prior; `--radius-km 220`. Every route is wrapped, so one failure
never stops the run; failures print as ERROR lines.

## How to read it

The by-type summary at the end is the prize. `fc/out` above 1 means the tool over-forecasts that
type, below 1 means it under-forecasts. We expect the residuals to differ by type (that is the
whole point), e.g. the tool may track FSC long-haul but under-read big connecting hubs, or
over-read thin ULCC point-to-point. Paste the by-type medians and the `within +/-20%` line back
and we tune each type's capture / propensity prior from real evidence, not a guess.

## Honest caveats (so the numbers are read right)

- Capture is the **prior 0.30**, not yet the OAG-QSI share (that rebuild is queued). So this
  back-test mainly grades the DEMAND sizing (catchment x propensity) and the prior capture, which
  is the right first thing to calibrate.
- Outturn includes connecting feed; the tool's forecast is catchment demand both ways. For a big
  hub-feed route the tool will read low until the connecting-feed layer is calibrated — that
  under-read is itself a finding, not a bug.
- Propensity uses the raw ODPOO store, which we know runs below the MI basis (the Genoa 0.0218
  vs 0.0424 gap). A uniform low bias across types points at that basis; a type-varying bias
  points at capture. The back-test separates the two.
- First run builds a served index per as-if week (cached), so the first few routes are slower.
