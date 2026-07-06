# Deck data contract: schema, workbook layout, and field-by-field source note

A single structured object per route holding every field the house deck needs, so the deck builds with no manual data entry. This is an output layer only: it exposes the forecast model's outputs in one named structure and does not change the calibrated method or any number it produces. Author of every generated file is set to "Avia Solutions".

## Delivered

- `deck_contract.py` - the emitter. Defines the contract, computes the derived metrics exactly per spec, and writes both the JSON and the workbook. Generic and RouteCase-driven; `ba_lhr_sjc_reference()` returns the fully populated worked example, `build_contract(case, outputs)` is the model-driven path (the documented integration point).
- `ba_lhr_sjc_deck_contract.json` - the BA London Heathrow to San Jose contract, fully populated from the validated 2015 deck.
- `ba_lhr_sjc_deck_contract.xlsx` - the workbook mirror, one sheet per block, 169 formulas, zero formula errors.

## Acceptance test (BA LHR-SJC)

Reproduces the validated deck exactly. Point-to-point forecast 82,708 at PDEW 113.6; connecting at London 45,011 at 61.8; connecting at San Jose 2,628 at 3.6; grand total 130,346 at 179.0. All three PDEW values confirm the divisor: forecast / 728. Year-1 revenue $121.7m, load factor 83.7%, derived yield $0.101/RPK, PRASK $0.0845, TRASK $0.0907 on the 8,618 km sector.

## The contract (nine blocks)

1. **route_metadata** - airline name and IATA, origin and destination airport and city codes, hub, aircraft, seats, frequency, service year, distance (km and nm), and the three catchment headline figures.
2. **summary_and_schedule** - the three market figures (point-to-point, connecting over hub, connecting over destination) and the schedule table (sector, dep, arr, op days, aircraft, seats, annual seats, annual pax, seat factor).
3. **segment_forecast** - one row per demand segment (origin business; origin leisure/VFR primary, secondary, contested; destination business; destination leisure/VFR primary, secondary, contested) with base demand, growth, demand at service year, stimulation, demand after stimulation, capture, forecast, PDEW; then the point-to-point, connecting and grand totals; plus the competition buckets (direct / no-direct) the proven method uses.
4. **connecting_at_hub** - per city: nr, code, name, country, demand, airline share, forecast, PDEW, plus total.
5. **connecting_at_destination** - same columns, the behind-destination feed.
6. **revenue_forecast** - Years 1 to 3: passengers by flow, capacity, implied load factor, revenue by flow (point to point, connecting at hub, connecting at destination, cargo, ancillary, total).
7. **economics_year1** - the Market Forecast Scenario: equipment, departures, block hours, cabin seats by class, load factors, the three average one-way fares, yield, PRASK, passenger/cargo/ancillary/total revenue, TRASK, and CASK plus breakeven load factor where the economics module produces them.
8. **revenue_build** - by_flow and by_cabin across Years 1 to 3, the two chart series.
9. **catchment** - zone definitions (primary, secondary, contested) and the top markets beyond the hub for the bar chart.

The workbook carries these as sheets `1_Route_Metadata` through `9_Catchment`, plus a `Contract` cover sheet. Derived columns (PDEW, airline share, implied load factor, sheet totals) are live Excel formulas so the workbook recalculates; base inputs are values.

## Derived-metric definitions (implemented exactly)

PDEW = annual two-way passengers / 728. Airline share = airline annual forecast / city annual demand. Yield = passenger revenue / (passengers x distance_km). ASK = seats x distance_km x frequency x 52 x 2. PRASK = passenger revenue / ASK. TRASK = total revenue / ASK. Annual growth rate = compound rate base year to service year, per segment. Stimulation = the multiplier for new direct service (1.0 where none).

## Field-by-field: what the model already produces versus what is added

Status key: EXISTS = the model emits it today; DERIVED = computed in this output layer from existing outputs (formula given), no new data; ADD-INPUT = needs a new input or lookup that does not touch the forecast numbers; METHOD-EXTENSION = needs a model addition, flagged for a separate decision.

### Block 1 - route metadata

| Field | Status | Source / formula |
|---|---|---|
| airline_name, airline_iata | ADD-INPUT | New RouteCase fields (identity only). |
| origin_airport | EXISTS | RouteCase.home. |
| destination_airport | EXISTS | RouteCase.primary_dest. |
| origin_city_code, destination_city_code | ADD-INPUT | Airport-to-city lookup (the same lookup that supplies city_name/country in blocks 4-5). |
| hub_airport | ADD-INPUT | New RouteCase field; defaults to the origin for a hub carrier. |
| aircraft_type | EXISTS | RouteCase.aircraft. |
| seats | ADD-INPUT | New RouteCase field (or the sum of the cabin config); the model holds the aircraft, not the seat count. |
| frequency_per_week | EXISTS | RouteCase.frequency. |
| service_year | ADD-INPUT | New RouteCase field (the deck's maturity year). |
| distance_km, distance_nm | EXISTS / DERIVED | RouteCase.sector_nm; km = nm x 1.852 (or haversine on the airport coordinates). |

### Block 2 - summary and schedule

| Field | Status | Source / formula |
|---|---|---|
| point_to_point_market | EXISTS | The catchment-to-destination O&D market (the base demand before capture). |
| connecting_market_over_hub | EXISTS | Sum of connecting_feed's per-market demand over the hub. |
| connecting_market_over_destination | METHOD-EXTENSION | The behind-destination (home-feed) side; the connecting-feed layer currently does the over-hub side only. The method is in the decks; the home-feed table is the known next addition. |
| schedule: seats, annual seats, annual pax, seat factor | EXISTS | Model: seats x frequency x 52 x 2, annual pax and load factor from the demand and economics. |
| schedule: dep_time, arr_time, operating days | ADD-INPUT | Schedule assumption (the decks assume a schedule; a route input). |

### Block 3 - segment forecast

| Field | Status | Source / formula |
|---|---|---|
| Point-to-point, connecting and grand totals (base, demand at year, after stim, capture, forecast) | EXISTS | The validated model totals. |
| PDEW (all rows) | DERIVED | forecast / 728. |
| The eight-segment split (business vs leisure/VFR x primary/secondary/contested), per segment | METHOD-EXTENSION | The model produces the validated point-to-point total, not the eight-way split. Producing it needs three inputs that allocate the existing total without changing it: the primary/secondary/contested zone demand (the catchment module has zones, so partly EXISTS), a business versus leisure/VFR split (Sabre fare-class shares or a benchmark, ADD-INPUT), and per-segment growth (the econometric/GDP forecasts the deck used, e.g. UK 9.0%, US leisure 7.5%). |
| Per-segment capture_rate | METHOD-EXTENSION (judgement) | The deck's per-segment capture (UK business 40%, leisure 20%, etc.) is analyst judgement, not a model output. Decision for you: either carry analyst per-segment captures as inputs to reproduce the segment table, or emit the point-to-point total only and let the deck present that. The validated total is unaffected either way. |
| Competition buckets (direct / no-direct) | EXISTS | The proven method buckets connecting demand this way; it falls straight out of the connecting layer once calibrated. |

### Block 4 - connecting at hub

| Field | Status | Source / formula |
|---|---|---|
| annual_demand, annual_forecast | EXISTS | connecting_feed per city. |
| airline_share | DERIVED | forecast / demand. |
| city_name, country | ADD-INPUT | Airport-to-city/country lookup (the deck prints them; codes come from the model). |
| pdew | DERIVED | forecast / 728. |

### Block 5 - connecting at destination

| Field | Status | Source / formula |
|---|---|---|
| Whole table | METHOD-EXTENSION | Same columns as block 4 but the behind-destination home-feed; needs the home-feed side of the connecting layer (the block-2 extension above). For BA this is a small flow (2,628), so the worked example carries the totals and the buckets and flags the per-city list as extractable identically. |

### Block 6 - revenue forecast (three years)

| Field | Status | Source / formula |
|---|---|---|
| Year-1 passengers and revenue, total | EXISTS | The model's Year-1 demand and route P&L (econ + business revenue, cargo). |
| Years 2 and 3 | DERIVED | Project pax by the existing segment growth, revenue by pax x fare; a projection layer, no new method. |
| annual_capacity | EXISTS | seats x frequency x 52 x 2. |
| implied_load_factor | DERIVED | total pax / capacity. |
| revenue by flow (point to point vs connecting) | DERIVED | pax-by-flow x fare-by-flow; the model holds the fares. |
| cargo | EXISTS | route P&L cargo revenue. |
| ancillary | ADD-INPUT | Industry benchmark per passenger or as a percentage; a new assumption, not a forecast number. |

### Block 7 - economics, Year 1

| Field | Status | Source / formula |
|---|---|---|
| equipment, weekly and total departures, block hours per departure | EXISTS | RouteCase and the P&L (annual turnarounds, sector block hours). |
| total seats, seats per departure | EXISTS | Model. |
| total load factor | EXISTS | route P&L load factor. |
| average one-way fares (point to point, connecting, blended) | EXISTS / DERIVED | Model fares; or revenue/pax by flow. |
| yield, PRASK, TRASK | DERIVED | Per the formulas above. |
| passenger, cargo, total revenue | EXISTS | route P&L. |
| ancillary revenue | ADD-INPUT | Benchmark (as block 6). |
| CASK, breakeven load factor | EXISTS | The economics module produces both; null in the BA worked example because BA's cost base was not in the deck's revenue table, but the model emits them for a model-run route. |
| cabin seats by class (business, premium coach, coach) | ADD-INPUT | The model carries a two-class economy/premium share; the three-class split needs a cabin config input. |
| load factor by cabin | METHOD-EXTENSION | Needs a cabin-level demand allocation (split the forecast across cabins); a small addition, no change to the total. |

### Block 8 - revenue build

| Field | Status | Source / formula |
|---|---|---|
| by_flow (Years 1 to 3) | DERIVED | Aggregated from block 6. |
| by_cabin (Years 1 to 3) | METHOD-EXTENSION | Needs the cabin fare x cabin pax split (the block-7 cabin allocation). |

### Block 9 - catchment

| Field | Status | Source / formula |
|---|---|---|
| zone definitions | ADD-INPUT | Short text per zone (carried here). |
| zone geometry / population / demand per band | EXISTS | The catchment module's cell-level apportionment; wired from the model. |
| top_markets_beyond_hub | EXISTS | connecting_feed demand ranked. |

## What needs a method decision, separately

Three items are genuine additions rather than re-exposed outputs, and none changes a calibrated number:

The behind-destination connecting feed (the connecting_market_over_destination figure and the whole of block 5, and by extension the home-feed share of block 6). This is the home-feed side of the connecting layer, already flagged as the next addition; the method is in the decks.

The eight-segment point-to-point split with per-segment growth and capture (block 3). The model gives the validated total; the segment table needs a business/leisure split, per-segment growth, and per-segment capture, the last of which is analyst judgement. The cleanest path is to carry these as named inputs on the RouteCase so the deck table reproduces, while the model's total stays the single source of truth.

The cabin layer (three-class seats, per-cabin load factor, by-cabin revenue, blocks 7 and 8). A cabin config plus a cabin-level allocation of the existing forecast and fares; small, and again no change to totals.

Everything else is either already produced or a pure derivation in this output layer. The forecast logic is untouched.

## Wiring: emitting the contract from a model run

`build_contract(case, outputs, connecting=, growth_rate=, ancillary_per_pax=)` is now wired to the live `assess()` output and is the counterpart to the BA reference. It maps the model's `natural`, `directional_demand`, `capture`, `route_pnl` and `annual_pnl` into the contract, derives PDEW, yield, PRASK and TRASK exactly per spec, and emits a `_need` note wherever a field needs one of the three flagged additions. Verified on the offline Genoa run: the Year-1 revenue it builds reconciles exactly to the model's annual net revenue ($46.42m), and point-to-point market, carried forecast and PDEW all flow correctly.

Run it from a model run:

```
py -3.12 deck_contract.py --case cases/genoa_nyc.json --assess genoa_nyc_case.json [--connecting feed.json] [--growth 0.045]
```

with no arguments it emits the BA reference worked example. The deck generator calls `emit_from_assess(...)` directly.

## Airline and aircraft inputs

The contract runs in two airline modes, set on the RouteCase. Airline-specific: the client gives the city pair and the target airline (`airline_name`, `airline_iata`, `alliance`), and the connecting layer and fleet are scoped to that carrier. Airline-agnostic: leave the airline blank and the deck reads "Generic", for a pitch not yet aimed at a named carrier.

Aircraft is set either way, two ways. Explicit: `aircraft` names an AIRCRAFT code and, optionally, `cabin_config` gives the three-class split. Automatic: set `aircraft` to "AUTO" and `aircraft_select.select_aircraft()` chooses the gauge that can fly the route's range and maximises the airline's profit on the route's demand. It is a real profit search, not a rule of thumb: every range-feasible candidate is run through the same validated route economics, filled from the demand at the planned frequency (capped at the load-factor ceiling, so an over-large aircraft shows a weak load factor and an under-size one spills demand), and ranked by annual profit. When an airline is named the candidate set is its plausible fleet (`FLEET_BY_AIRLINE`, seeded for the common SJC carriers and extensible from Egnyte fleet data); agnostic runs consider every in-range type. Verified on Genoa: against ~155 seats of each-way demand it picks the A321XLR over a too-small A321 (more spill, lower profit) and a too-large A339 (empty, negative margin), which is the gauge the case already uses.

No external data was needed for this; the model's aircraft database carries range, seats and the full economics. The airline-to-fleet and alliance maps are the one place Egnyte fleet data would extend coverage beyond the carriers seeded so far.
