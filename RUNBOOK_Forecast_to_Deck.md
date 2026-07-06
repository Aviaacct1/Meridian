# Runbook: route forecast to deck

How to drive the tool end to end, from a city pair to a finished pitch deck, in either of its two modes. The forecast method is the validated one; this is purely the order of operations and what each step needs.

## The chain

```
RouteCase ──▶ assess.py ──▶ <case>_case.json ──┐
(catchment → demand → load factor → route P&L)  │
connecting_feed.py ──▶ connecting feed ─────────┤
aircraft_select.py ──▶ best gauge + LOPA ───────┤──▶ deck_contract.py ──▶ contract.json + .xlsx ──▶ build_ba_v3.js ──▶ deck.pptx
segment_model.py ──▶ 8-segment table ───────────┘            (via contract_to_deck.js adapter)
```

The forecast, the contract and the deck are separate steps with clean handoffs: the contract JSON is the single boundary between the model and the deck, so the deck builds with no manual data entry.

## Two modes

**Mode A — fully specified.** You tell it the aircraft, the cabin config and the schedule. Set `aircraft`, `cabin_config` and the schedule on the RouteCase and run the chain. Use this when the airline has told you what they would fly.

**Mode B — optimise the equipment.** Set `aircraft` to `"AUTO"`; the tool picks the gauge and the LOPA that maximise profit on the route's cabin demand (premium-rich where the front fills, denser where it does not), then forecasts on that. You still hand it the schedule (times and frequency); choosing the schedule itself is the one piece not yet built, and it pairs with the connecting calibration.

## Prerequisites

- Python 3.12 with `duckdb`, `pandas`, `lxml`, `openpyxl`; Node for the deck (`pptxgenjs`).
- Stores on your machine (`C:\Avia`): `sabre.duckdb` (demand, cabin split, outturn) and `oag.duckdb` (schedules, the connecting QSI). A GeoNames `cities5000.txt` for the catchment.
- For an offline / World Routes run, a case can point at cached observed splits and run with no Sabre connection.

## Steps

**1. Forecast (catchment → demand → economics).**
```
py -3.12 app/assess.py <case> cities5000.txt --sabre "C:\Avia\sabre.duckdb" --year 2024
```
Writes `<case>_case.json` (population, natural/repatriated demand, capture, frequency, route P&L, annual P&L). Offline: drop `--sabre` to use the case's cached observed split.

**2. Aircraft + LOPA (Mode B).**
```
py -3.12 app/aircraft_select.py --nm <sector> --demand <each-way> --freq 7 --airline BA
```
Or in code, `select_aircraft_and_lopa(...)` returns the best `(aircraft, variant)` netted against cost; `default_cabin_mix(econ_share)` supplies the cabin shares until the live Sabre split is wired. Skip this in Mode A.

**3. Connecting feed (hub routes).**
```
py -3.12 app/connecting_feed.py --oag-db "C:\Avia\oag.duckdb" --week <wk> --sabre "C:\Avia\sabre.duckdb" --catchment SFO,SJC,OAK --proposed BA,LHR,SJC,1300,0800,635 --base-yr 2024
```
Gated: the connecting-QSI dispersion is still being calibrated against the four deck fixtures (`calibrate_feed_qsi.py`). Until that's settled, treat connecting numbers as provisional.

**4. Segment table (block 3).** `segment_model.build_segment_table(segments, base_year, service_year)` builds the eight-segment point-to-point table bottom-up; the business/leisure split comes from the route's Sabre cabin mix, and the sum reconciles to the validated total.

**5. Build the contract (JSON + workbook).**
```
py -3.12 "Deck Generator/deck_contract.py" --case app/cases/<case>.json --assess <case>_case.json [--connecting feed.json] [--growth 0.045]
```
Or `emit_from_assess(...)` / `build_contract(case, outputs, connecting=, segment_rows=, cabin=, growth_rate=, ancillary_per_pax=)`. Writes `<case>_deck_contract.json` and `.xlsx` (author Avia Solutions, one sheet per block). With no arguments it emits the BA reference worked example.

**6. Build the deck.**
```
cd "Deck Generator"
set DECK_CONTRACT=<case>_deck_contract.json
node build_ba_v3.js
```
`contract_to_deck.js` adapts the contract into the deck's arrays; the builder reads them. Point `DECK_CONTRACT` at a different contract and the same builder renders a different route.

## Supporting tools

- **LOPA store** (`app/lopa.py`, `app/lopa_store.json`): seat config by airline+aircraft, with named variants and a type-average fallback. `get_lopa(aircraft, airline, variant)` never returns nothing for a known type.
- **Annual LOPA refresh** (`app/lopa_refresh.py`): rebuilds the store from Wikipedia fleet pages once a year (`--airline BA` or `--all`); review the diff, since carrier formatting varies. SeatGuru shut down Oct 2025, so this replaces the per-pitch website lookup.
- **Validation** (`app/validate_sjc.py`, `app/sector_diag.py`): the analyst-vs-model-vs-outturn back-test on your Sabre store.

## What each step needs, and what's gated

| Step | Needs | Status |
|---|---|---|
| Forecast (P2P + economics) | Sabre or a cached split | works |
| Aircraft + LOPA selection | the LOPA store (built) | works; cabin mix defaults from econ_share |
| Segment table | the Sabre cabin/fare-class split | engine built; uses the default until the live split is wired |
| Contract + workbook | the above | works |
| Deck | the contract | works |
| Connecting feed | `oag.duckdb` | built; dispersion calibration pending the full OAG |
| Behind-destination (home) feed | the connecting layer | not built; rides with the OAG calibration |
| Schedule-time optimisation | the connecting QSI | not built; the next capability, paired with the OAG work |
| Live BA 2024/25 refresh | your Sabre store | your-PC run |

So today the chain runs end to end for the point-to-point forecast, the economics with optimised aircraft and LOPA, the contract and the deck. The connecting feed runs but its capture levels are still being calibrated; the home feed and the schedule optimiser are the two capabilities that wait on the OAG data.
