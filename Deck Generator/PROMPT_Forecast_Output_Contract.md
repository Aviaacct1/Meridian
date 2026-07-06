# Prompt to paste into the route forecast chat

Copy everything below the line.

---

I am building the Avia-style deck generator, which consumes your forecast output and renders our house pitch deck. I need you to extend the route forecast model to emit a single structured "deck data contract" for any route, holding every field the deck needs, so the deck builds with no manual data entry.

Do not change the calibrated forecast method or any number it produces. This is purely about exposing the outputs in one consistent, named structure. The deck template and the exact columns it expects are documented in `Deck Generator/Avia_Deck_Template_Spec.md` in the project; read it first.

Deliver two things:
1. A single JSON object per route (the contract below), emitted by the model.
2. An Excel workbook that mirrors it, one sheet per block, since the workbook is also a client deliverable.

Use BA London Heathrow to San Jose as the worked example and populate it in full with the validated reference numbers, as the acceptance test. Keep the structure generic and route-agnostic, driven by the RouteCase, so Genoa to New York or any pair fills the same contract. For every field, tell me whether the model already produces it or it needs adding, and for anything new give the formula or source.

## The contract

**1. Route metadata**
airline name, airline IATA code, origin airport + city code, destination airport + city code, hub airport, aircraft type, seats, frequency per week, service year, great-circle distance (km and nm), and the three catchment headline figures (see block 2).

**2. Summary and schedule (the map slide)**
- point_to_point_market (annual, two-way)
- connecting_market_over_hub (annual)
- connecting_market_over_destination (annual)
- schedule rows, one per sector plus a total: sector, dep time, arr time, operating days, aircraft, seats, annual seats, annual pax, seat factor.

**3. Route forecast table (segment level)**
One row per demand segment: Origin Business; Origin Leisure/VFR Primary, Secondary, Contested; Destination Business; Destination Leisure/VFR Primary, Secondary, Contested. Each row with:
base_annual_demand, annual_growth_rate, demand_at_service_year, stimulation_factor, demand_after_stimulation, capture_rate, forecast, pdew.
Then summary rows: point_to_point_total, connecting_at_hub_total, connecting_at_destination_total, grand_total, each with the same columns where they apply.

**4. Connecting at hub (origin) table**
One row per connecting city, ranked by forecast: nr, city_code, city_name, country, annual_demand, airline_share, annual_forecast, pdew. Plus a total row. Include city_name and country from a lookup, since the deck prints them.

**5. Connecting at destination table**
Same columns as block 4.

**6. Revenue forecast (three service years)**
For each of Year 1, 2, 3: passengers by flow (point to point, connecting at hub, connecting at destination, total), annual capacity, implied load factor, and revenue by flow (point to point, connecting at hub, connecting at destination, cargo, ancillary, total).

**7. Market forecast scenario (detailed economics, Year 1)**
equipment, weekly departures, total departures (annual, two-way), block hours per departure, cabin seats by class (business, premium coach, coach), total seats, seats per departure, load factor by cabin, total load factor, average one-way point-to-point fare, average one-way connecting fare, average one-way blended fare, yield (rev/RPK), PRASK, passenger revenue, cargo revenue, ancillary revenue, total revenue, TRASK. Add CASK and breakeven load factor if the economics module produces them.

**8. Revenue build (for the two charts)**
- by_flow: for Years 1 to 3, the revenue split across point to point, connecting at hub, connecting at destination, cargo, ancillary.
- by_cabin: for Years 1 to 3, the revenue split across business, premium coach, coach.

**9. Catchment**
- zones: primary, secondary, contested, each with a one-line definition and, if available, the geometry or the population/demand in each band.
- top_markets_beyond_hub: the bar-chart data, top markets by annual demand from the catchment over the hub (city, annual_demand).

## Derived-metric definitions (implement exactly so the deck and the model agree)

- pdew (passengers per day each way) = annual two-way passengers / 728 (that is 52 weeks x 7 days x 2 directions). Check: BA P2P forecast 82,700 gives 113.6.
- annual_growth_rate = compound annual growth from the base year to the service year, per segment.
- stimulation_factor = the multiplier applied to the segment for new direct service (1.0 where none).
- yield (rev/RPK) = passenger revenue / (passengers x distance_km).
- PRASK = passenger revenue / ASK, where ASK = seats x distance_km x frequency x 52 x 2.
- TRASK = total revenue / ASK.
- airline_share (connecting tables) = airline annual forecast / city annual demand.

## What I need back

1. The JSON schema and the Excel layout.
2. The BA LHR-SJC contract fully populated as the worked example.
3. A field-by-field note of what already exists versus what you have added, with the source or formula for each new field. Flag anything that cannot be produced without a method change, so I can decide separately.

Keep our house style on any text fields and set the workbook author to "Avia Solutions". The forecast logic stays exactly as calibrated; this is an output layer only.
