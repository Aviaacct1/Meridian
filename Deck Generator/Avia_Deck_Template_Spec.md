# Avia Solutions route-pitch deck: precise template specification

Derived from the WR17/18/19 final SJC pitches and cross-checked against the Tampa ASD decks (Avianca Bogota-Tampa, Air France/Virgin Atlantic Paris/Manchester-Tampa). The structure holds across airports and route types, so it is the generic template for the generator. Author of any generated file: Avia Solutions.

## 1. Canonical structure (generalised)

A full bespoke deck runs circa 60-70 slides. Sequence:

1. Title: "A Unique Opportunity to Serve [Destination] from [Origin]" plus "World Routes [Year]" (or the month/year).
2. Contents, with section page numbers.
3. Overview / one-line "why this airline is well placed" summary (a dense single slide of the headline facts).
4. Summary of Route Forecast (the map slide, see section 3).
5. "Why [Destination]" section (circa 11-13 slides): airport advantage, demographics, wealth, economic strength, the destination's standout sectors.
6. Destination strength / "Major [sector] Expansion" section (circa 8-11 slides): the marquee employers and developments.
7. "Links between [Destination] and [Origin]" section (circa 5-6 slides): trade, culture, education, diaspora, company presence both ways.
8. Market impact / non-cannibalisation section (the case-study carrier, e.g. ANA at SJC).
9. "[Origin]-[Destination] Forecast" section (circa 3-4 slides): the forecast tables (section 2).
10. "[Destination] Airport" section (circo 10-15 slides): facilities, base, growth, incentives, catchment.
11. Call to action / proposed visit / meet stakeholders.
12. Thank you.
13. Appendix (circa 5-8 slides): "Choose [Airport]" summary, leisure/tourism, and the methodology and revenue-forecast detail.

Section dividers are full-bleed photographic slides with a large white section title.

The product can ship a tighter cut, but the forecast, summary-map, airport and methodology sections are the non-negotiable core, and the qualitative sections scale by route profile via the relevance engine.

## 2. Route forecast tables (exact columns)

Main route forecast, titled "Route Forecast [Airline]: [Origin] - [Destination] Traffic Forecast ([Frequency] Weekly Service)":
Market | Base Annual Demand (000s) | Annual Growth Rate | Annual Demand [Year] (000s) | Stimulation due to Direct Service | Demand After Stimulation (000s) | [Airline] Capture Rate | Forecast (000s) | PDEW

Rows are the demand segments: UK/Origin Business, Origin Leisure/VFR (Primary, Secondary, Contested), Destination Business, Destination Leisure/VFR (Primary, Secondary, Contested), then a Point-to-point total, then Connecting at [Origin] and Connecting at [Destination], then the grand total.

Passengers Connecting at [Origin], titled "Route Forecast Passengers Connecting at [Origin]":
Nr | City Code | City Name | Country | Annual Demand [Year] | [Airline] Annual Share | Annual Forecast | PDEW

Passengers Connecting at [Destination]: identical columns.

## 3. Summary / route-map slide

Titled "[Airline] Opportunity for [Airline] / Summary of Route Forecast". A clean route map with the two cities marked and a great-circle line. Three figures displayed prominently beside or on the map, each with the asterisk note "Based on AviaSolutions' [Airport] Service Area catchment analysis":
- Point to point market: [number]
- Connecting market over [Destination]: [number]
- Connecting market over [Origin]: [number]

Below, a "Schedule Options: [Aircraft]" table:
Sector | Dep. Time | Arr. Time | Op. Days | Aircraft | Seats | Annual Seats | Annual Pax | Seat Factor

This is the single most important slide and the current generator's map slide must be rebuilt to match it (proper map plus the three numbers plus the schedule table).

## 4. Economics / revenue (the full metric set, not a summary)

Revenue Forecast table, "Revenue Forecast for [Origin] - [Destination] ([Frequency] weekly service)", by year (Yr1, Yr2, Yr3):
Passenger Demand (Point to Point, Connecting at [Destination], Connecting at [Origin], Total) | Annual Capacity | Implied Load Factor | Revenue Forecast (Point to Point, Connecting at [Destination], Connecting at [Origin], Cargo, Ancillary, Total)

Market Forecast Scenario table (the detailed economics, this is the depth to reach):
Equipment | Weekly Departures | Total Departures | Block Hours/Dep | Cabin Seats by class (Business, Premium Coach, Coach) | Total Seats | Cabin Seats/Dep | Total Seats/Dep | Cabin LF by class | Total LF | Average One-Way P2P Fare | Average One-Way Cnx Fare | Average One-Way Fare | Yield (Rev/RPK) | PRASK | Passenger Revenue | Cargo Revenue | Ancillary Revenue | Total Revenue | TRASK

Charts:
- Revenue Build Up by Flow: bar chart, Year 1 split (local, connecting at origin, connecting at destination, cargo, ancillary) and the same across Yr1-Yr3.
- Revenue Build Up by Cabin: stacked bar, Business / Premium Coach / Coach across Yr1-Yr3.

## 5. Catchment and methodology slides

Catchment: a map of the service area titled "[Airport] Catchment Area", with the primary / secondary / contested zones delineated.

Methodology (the appendix detail, five slides):
1. Summary of Forecast Methodology: base demand grown to maturity, Sabre MI O&D adjusted for non-MIDT channels, service-area-only demand, business vs leisure/VFR split, growth from GDP/trade/econometric forecasts, subsidiary and alliance connectivity.
2. Schedules: assumed schedule, layover, frequency, aircraft.
3. Point to Point Methodology: Sabre MI, compound growth, stimulation from new direct service, capture from frequency-share and leakage analysis.
4. Connecting Markets Methodology: Sabre MI, double-connection exclusion, growth to maturity, the QSI model (total elapsed time, connection type online/interline/alliance, frequency).
5. Revenue Forecast Methodology: passenger growth from QSI, fares from MIDT weighted down with a business-fare reduction and cabin splits, spill estimation, cargo from aircraft performance with conservative yield, ancillary from industry benchmarks.

## 6. House style (to match exactly)

- Colours: dark blue primary (backgrounds, titles, headings), white, a light blue / cyan accent for sub-headings and bullets, and orange as a sparing accent (map circles, occasional highlight). Charts use blues, greens, oranges and greys.
- Fonts: Arial / Helvetica bold for titles and section headers; Arial or Calibri for body.
- Layout: a consistent top title bar carrying the deck title and "World Routes [Year]"; page number and airline logo bottom right; "AviaSolutions analysis" credit bottom left of data slides; full-bleed image section dividers; light-blue circular bullets; two and three-column content; key numbers enlarged in call-out boxes; small-font source notes under tables.

Note the on-slide credit is written "AviaSolutions" (one word); generated-file author metadata remains "Avia Solutions".

## 7. Deltas to apply to the current generator

1. Repalette from navy/gold to the house dark blue + cyan + orange; switch headers to Arial.
2. Rebuild the summary slide: proper map, the three catchment figures with the asterisk note, and the schedule-options table.
3. Restore the full forecast tables with the exact columns above (000s, growth rate, stimulation, capture, PDEW), including both connecting-city tables.
4. Replace the four-card economics slide with the Market Forecast Scenario table (yields, PRASK, TRASK, cabin LFs, fares) plus the revenue-forecast table and the two revenue-build charts.
5. Add the five methodology slides verbatim in structure.
6. Add the catchment map slide with primary/secondary/contested.
7. Section dividers become full-bleed image slots; add the title-bar header and the "AviaSolutions analysis" credit.
8. Keep the relevance engine driving which qualitative sections appear and how deep, so the same template serves SJC, Tampa, Genoa or any pair.
