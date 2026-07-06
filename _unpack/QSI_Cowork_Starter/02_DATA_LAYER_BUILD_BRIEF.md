# QSI Auto - Data layer build brief

Version 3, updated 23 June 2026. Updated after inspecting the 2013 Sabre file (granularity), the decision to ingest the full Sabre record rather than a QSI-only subset, and a header comparison across 2013, 2016, 2017 and 2019 that confirmed one schema across all years.

This describes the new part of the process to build in Cowork. It removes the manual upload step. The tool reaches into the Avia-held Sabre and OAG data, builds its own correctly formatted starting files for any city pair, then forecasts from there. No APIs. The forecast pipeline you already calibrated does not change.

## What changed in this version

Three things are now settled.

First, the granularity question is answered. The 2013 file is itinerary-level true-origin data with full routing detail: connecting points, per-leg airlines, cabin class, and fares are all present per record. The generator is a reformat of existing data, not a rebuild of missing data, and the QSI method is untouched. Section "Confirmed Sabre schema" records the exact columns.

Second, the ingest scope is wider than first planned. Rather than filtering down to only the fields the QSI templates need, the ingest keeps the full record, including cabin class and the base and total fare and revenue figures. Those fields are what the financial analysts use separately today, and bringing them into the same store is the step towards folding that analysis into the QSI tool later. The principle: load the full Sabre record once, then derive narrow views from it per use, rather than ingesting the same 91GB twice for two teams.

Third, one schema reads all years. A header comparison across 2013 (directional) and 2016, 2017 and 2019 (non-directional) returned identical columns, character for character: same thirty-nine fields in the same order, with the seven point-of-origin fields present in every file. The directional and non-directional label does not change the layout, so the loader does not branch by year. This removes the worst case, where the non-directional years might have dropped point of origin or reshaped the file. The directional question is now a counting convention inside identical columns, not a structural one. See "Directional and non-directional handling".

## Objective

Today an analyst pulls a Sabre extract and an OAG export by hand for each route, and the tool reads those files. The new layer does that pulling itself. Give it two airport codes (or catchments) and a period, and it queries the master Sabre and OAG stores, applies the catchment mapping, and writes out the same neat extract files the existing providers already read. Everything downstream of that file is unchanged.

The store serves more than the QSI forecast. The same full-fidelity Sabre data underneath supports at least two views:

1. The QSI view. Filter to a city pair, aggregate across cabin, map to the twenty-column layout the demand provider reads. This is the front end for the forecast tool.
2. The fare and financial view. Keep cabin class and the base and total fare and revenue detail at full grain, for the financial analysis the separate team runs today and for a future module inside the QSI tool.

Both read the same store. Neither requires a second ingest.

## Two builds, one codebase

The work is built once and deployed two ways. The only difference between them is where the data paths point.

- Shared build on Egnyte. This is the day-to-day version. The store and the app live on Egnyte so the whole team can test it together in the Teams environment.
- Portable laptop build. A self-contained version for World Routes that carries the store, the reference tables, and the app on the machine, and runs with no internet.

The mechanism that makes this clean is one settings file. Every path the tool uses (Sabre store, OAG store, reference tables, output folder) lives in a single config file, and nothing is hardcoded. The shared build's config points at Egnyte. The laptop build runs a one-time packaging step that copies the store and rewrites the config to the local drive automatically, then bundles everything as a single launchable app. Switching from shared to laptop is a packaging action, not a code edit. This also clears out the old /mnt/project paths still scattered through the modules, which is overdue anyway.

You build and test on the shared version. The laptop build is produced from it when you need the offline demo, not developed on day to day.

## Architecture

The 91GB never goes near the forecast pipeline. It is read once into a local columnar store at full grain, and from then on each city-pair request reads only the small slice it needs.

```
Sabre dump (13 x circa 7GB CSV)  ->  one-time ingest (full record)  ->  local columnar store (partitioned by year)
                                                                                  |
                                          +---------------------------------------+----------------------------+
                                          |                                                                    |
                                  QSI view query                                                     fare / financial view query
                                  (city pair, aggregate cabin)                                        (city pair, keep cabin + fares)
                                          |                                                                    |
                                  write 20-column extract  ->  existing demand provider  ->  pipeline          (future module / current
                                                                                                                 separate financial analysis)

OAG schedules  ->  one-time ingest  ->  local store (partitioned by hub)  ->  query by hubs  ->  leg input  ->  existing schedule provider  ->  pipeline
```

Use DuckDB as the store. It is a single file on disk, needs no server, runs offline, reads a 7GB CSV without holding it in memory, filters tens of gigabytes in seconds, and behaves identically whether the file is on an Egnyte-mounted folder or a local drive. It embeds inside the packaged app. The ingest runs once per year-file and may take a few minutes each; queries after that are quick. This is the design that makes "any two airport codes, no internet" work at the conference, and at 7GB a year it is the only sensible way to read these files, since none will open in Excel or load whole into pandas.

## Confirmed Sabre schema

The 2013 file is a comma-delimited CSV, quoted fields, one header row, circa 7GB, sorted by passengers descending. Thirty-nine columns plus a trailing empty column from the line-ending comma. The same header was confirmed on 2016, 2017 and 2019, so this layout holds for every year. The columns, in order:

```
Itinerary                      routing type (NON-STOP, and connecting types deeper in the file)
Origin Airport                 board point airport
Destination Airport            final destination airport
Marketing Airline              itinerary marketing carrier
Operating Airline              itinerary operating carrier
Cabin Class                    e.g. DISCOUNT COACH
Year
Connecting Airport1 / City1 / Country1
Connecting Airport2 / City2 / Country2
Connecting Airport3 / City3 / Country3      up to three connections
Leg1-4 Mkt Aln                 per-leg marketing airline (up to four legs)
Leg1-4 Op Aln                  per-leg operating airline (up to four legs)
Point Of Origin Airport / Airport Name / City / City Name / Country / Country Name / Region Name   true origin
Airline Share                  carrier share of the market, percent
Passengers                     annual passengers (fractional, from sampling factor-up)
PPDEW                          passengers per day each way (= annual passengers / 365)
Avg. Base Fare(USD)
Base Revenue(USD)
Avg. Total Fare(USD)
Total Revenue(USD)
Distance (km)
```

Notes that matter for the ingest:

- Direct or indirect comes straight off the Itinerary column. NON-STOP is direct; any value with a connecting airport populated is indirect. No need to derive it from the connection fields.
- Empty leg and connection fields arrive as two spaces inside quotes, not as true blanks. Normalise them to null on load or every per-leg filter will misbehave.
- Passengers are fractional because the data is factored up from the Sabre sample. Keep them fractional in the store; round only on output if at all.
- One O-D market is spread across many rows, split by origin airport, destination airport, marketing and operating airline, cabin class, routing, and point of origin. Aggregation level is a query-time choice, which is exactly why the store holds the full grain.
- Distance is a whole number in 2013 (1081) and a decimal in the later years (449.0). Cast Distance to a float on load and it is a non-issue; an integer assumption would fail on the later files.

The set is twelve zip files covering 2013 to 2025, with 2020 and 2021 combined into one file and 2025 marked "Best", which usually means a part-year or best-estimate cut. Treat the combined 2020-21 file and the 2025 "Best" file as known data-quality caveats when reading any time series across them.

## Directional and non-directional handling

The schema is identical across the cuts, confirmed by the header comparison, so this is no longer a parsing problem. The directional years (2013 and 2015, labelled POO or Poo) and the non-directional years (the rest, labelled ND in various orders) carry the same columns, including point of origin. What can still differ is how passengers are attributed for a true-origin market: a directional cut splits a market by which end the journey started, a non-directional cut combines the two. The header check cannot see this, because every file shows both directions as separate rows; it shows up only in the totals for an asymmetric market.

So the step is tag-and-confirm, not build-and-branch:

1. Tag every row with the directionality of its source file, carried as a column in the store, so any view can filter to a consistent basis.
2. Confirm the counting convention with one query after the first loads: take a single asymmetric market, for example a summer leisure O-D that skews heavily one way, and compare its passenger split across a directional year and a non-directional year. That five-minute check tells you whether the two cuts can be read on the same basis or need converting.
3. Decide one basis for the QSI view and the fare view to report on, and hold to it rather than mixing the two silently across years.

The directional years are 2013 and 2015. Everything from 2014 and 2016 onward is non-directional. Only two of the thirteen are directional, so if the cross-year check shows the conventions do not reconcile, the practical answer is to standardise on the non-directional basis and treat 2013 and 2015 accordingly, rather than the other way round.

## QSI view: column mapping

The QSI demand provider reads a twenty-column layout. The generator produces it from the Sabre store as follows:

```
Mod Org City        <- Point Of Origin City, grouped by catchment table
Org City            <- Point Of Origin City
Mod Dest City       <- Destination Airport, mapped to city, grouped by catchment
Mod Dest City Name  <- Destination city name
Mod Dest Country    <- Destination country
Dest City           <- Destination Airport mapped to city
Direct/Indirect     <- Itinerary column (NON-STOP = Direct, else Indirect)
Origin (airport)    <- Origin Airport
Destination(airport)<- Destination Airport
OperatingAirline    <- Operating Airline (see decision below)
ConnectPoint1-3     <- Connecting Airport1-3
Segment1-4 Airline  <- Leg1-4 Op Aln (see decision below)
Passengers          <- Passengers, summed across cabin
RevenueInUSD        <- Total Revenue(USD), summed across cabin
AvgFareInUSD        <- Avg. Total Fare(USD), passenger-weighted across cabin
```

Three design decisions to settle with Nick before the generator is final, because the old hand-pulled extracts made them implicitly:

1. Marketing or operating carrier. The new data splits the two; the old extract had one airline field. QSI capture is usually scored on the marketing carrier that sells the service, so confirm which the method expects and map accordingly, for both the itinerary airline and the per-leg fields.
2. True origin or board point. The data carries both Point Of Origin and Origin Airport. QSI is an O-D market method, so true origin is the natural basis, but confirm against how the analysts built the reference forecasts.
3. Cabin aggregation. The QSI view sums across cabin; the fare view keeps it. Confirm the QSI method wants a single all-cabin demand figure, which it almost certainly does.

## Fare and financial view

Retain at full grain for this view: Cabin Class, Avg Base Fare, Base Revenue, Avg Total Fare, Total Revenue, Airline Share, PPDEW, Distance, the Point Of Origin fields, and both the marketing and operating airline detail. This is the data the financial analysts work with separately today. Bringing it into the same store now, even before a tool module uses it, means the eventual financial module is a new view over data already loaded, not another ingest. No build work is needed on this view yet beyond keeping the columns; the decision is simply not to discard them at load.

## OAG ingest

Same pattern. Ingest the OAG schedule download once, partition by hub airport and period, query to build the leg input the schedule provider reads (the Leg 1.1 / 2.1 / 1.2 / 2.2 structure).

For the POC, scope the OAG download to European schedules. That keeps the file size down and covers intra-European city pairs, on the condition that the demo only uses origin-destination pairs that route over European hubs. The moment a pair connects over a Gulf, Turkish, or US hub, the schedule store needs those hubs in it, or the connection builder has nothing to route through. Hold the World Routes demo to European O-Ds and this is not a problem.

## Reference tables

Three lookups must exist as maintained tables the generator reads, not values buried in code:

1. Airport-to-city and catchment mapping (for example SFO, OAK, and SJC as one Bay Area service area). The "any two airport codes" promise depends entirely on this table being right. The Sabre data is keyed at both airport and city level and carries city names, so the table can be seeded from the data itself and then corrected for catchment grouping.
2. Sabre factor-up by market. The data is already factored up from the sample (passengers are fractional), so confirm whether any further adjustment is needed or whether the supplied figures are final.
3. Alliance membership and the LCC list (the connection builder already uses these, so point the generator at the same source).

Seed the catchment table from how the analysts currently define service areas. That is a first-session question for Nick.

## The generator

Input: origin airport or catchment, destination airport or catchment, period, direction.

Steps: resolve each end to its catchment, query the Sabre store for those markets on the agreed directionality basis, aggregate to the chosen grain, format to the twenty-column layout, write the demand file; query the OAG store for the relevant hubs, build the leg input, write the schedule file. Drop both into the tool's input location and run Path B as it already works.

Output: files identical in shape to what an analyst pulls by hand, so the pipeline cannot tell the difference between a generated input and a manual one.

## Acceptance test

This is the checkpoint before any auto-generated forecast is trusted. Take two or three of the 70 analyst forecasts. Generate the Sabre and OAG inputs from the master store for the same route and period. Confirm the generated extract reproduces the analyst's own hand-pulled extract: the demand totals and the connecting split should match. If the generated input reproduces the analyst's input, every rule Nick has already calibrated still holds and you know the front end is faithful. Only then move on to running the wider set.

## Build sequence

1. Confirm granularity. Done. Itinerary-level true-origin data, full routing, cabin and fare detail present.
2. Ingest one Sabre year (2013) to DuckDB at full grain, with the directionality tag and the two-space-null normalisation. Validate by querying one large market and checking passengers and revenue against a known analyst extract.
3. Build the reference tables (catchment, factor-up confirmation, alliance and LCC).
4. Build the QSI view generator. Test it against one analyst extract until it reproduces it. Settle the three mapping decisions here.
5. Ingest the remaining years, all on the one schema. Tag each with its directionality cut and run the cross-year counting check once.
6. Repeat ingest and generator for OAG, Europe scope.
7. Wire the QSI generator into the portal as the input step for Path B, replacing the manual upload.
8. Run the acceptance test on two or three routes.
9. Produce the laptop build: package the store, reference tables, and app, with the config rewritten to local paths automatically.

The fare and financial view needs no build step of its own yet. It is served by keeping the columns at step 2 and 5.

## Open questions for the first session

- Directionality counting convention. The schema is confirmed identical across years, so the only open part is whether the directional (2013, 2015) and non-directional (all other years) cuts count an asymmetric market on the same basis. Settle with the one cross-year query after the first loads, then fix a single reporting basis.
- Mapping decisions. Marketing against operating carrier; true origin against board point; all-cabin demand for the QSI view. Confirm against how the reference forecasts were built.
- OAG export format. Which OAG Analyser schema Nick will download, and whether it matches what oag_parser.py already reads.
- Egnyte home and consolidation. Settle 18 Products as the canonical Sabre home and clear the duplicate set under 07 Current Projects/Development, so 91GB does not live in two places.
- Catchment definitions. How the analysts currently hold service-area mappings, so the reference table can be seeded from real practice.

## First Cowork action

All thirteen years uploaded and uncompressed under 18 Products/Data/Sabre, a Europe OAG download alongside, and two or three complete old forecasts (each with its QSI workbook and the analyst's own Sabre and OAG extracts) for the acceptance test. With those in place, step 2 starts in the first session.
