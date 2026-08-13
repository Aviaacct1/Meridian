# Handover: 15 August 2026

Version 1.0, written 14 August evening. Avia Solutions. Read this, then
`bt2/bt2_experiments.log` from the 14 August entries, most recent last.

---

## What 14 August closed, so nobody reopens it

**The optimiser objective needed no code.** The 0.7 connecting weight test named in the 14 August
runbook could not have moved the answer: `route_feed.optimise_departure` scores a departure as
`b_pax + h_pax`, connecting only, and local demand does not vary with departure time anywhere in the
engine, so the argmax is identical for any positive weight. The chosen times also match the market,
00:30 for China Airlines, 02:00 for EVA and 00:30 for United against actual SFO departures of 01:05,
01:15 and 23:55. The P2P collapse from 83,408 to 55,306 is the capacity cap crowding, not the
departure time: `route_forecast` line 823 is `carried = min(total_demand, capacity x plan cap)` and
the two legs compete for the same seats. Do not re-run the weight test.

**LF-CAP-OPEN is closed and 0.875 stays.** Measured on 4,963 real launches. Haul does not move the
centre, 2.0 points across four cuts, but it does move the upper tail, and a cap lives in the tail.
Carrier type is monotone with haul held, FSC below LCC below ULCC by 4 to 7 points at the median. At
a constant 85.5th percentile the crossed cells run 0.853 to 0.900, and 0.875 is the midpoint of the
marginal range 0.862 to 0.888. Worst case from one global cap is 2.5 points, 2.9% of carried, on the
15.6% of routes where it binds. The deciding argument is that the cap is absorbing a demand over-read
rather than expressing a load factor: of 818 pinned routes on the 10 July arm, 422 still over-forecast
by more than 20%. The measurement belongs to `schedule_sizing.PLANNING_LF`, not to the brake.

**The contract is fixed and held by invariants.** Four defects, all in the contract layer, none in
the engine. `app/contract_legs_check.py` runs four checks over a folder of contracts and 16 of 16
pass. Run it after every `deck_from_cases` run.

**Shipped and verified:** the carrier's own seat count now survives a client-fixed gauge, the curfew
cost and the unrestricted departure are on the page with their basis, and the seat count states
whether it came from the carrier's configuration or the generic table.

---

## Job 1, and it is the product rather than the presentation: DOT for the US market

**Why.** John's ruling, 14 August: US airports do not trust Sabre, they trust US government data.
Tampa, San Jose and O'Hare will not buy a product that reads a GDS sample for their own domestic
market. This is a commercial requirement, not a labelling one.

**What already exists.** `app/od_source.py` implements the rule in full and says so in its own
docstring: "for US domestic markets the tool leads with DB1B... Sabre runs underneath for the
commuter/EAS tail DB1B cannot see". Three modes, `dot`, `auto` and `sabre`, and it returns a source
label. `AVIA_OD_SOURCE` defaults to `sabre`, so it is off. This is the default-off register pattern
again: built, verified, never switched on.

**Why turning it on does not fix SJC-TPE.** `od_source` governs the POINT TO POINT market and
selects DB1B only for all-US markets. SJC-TPE is international, so the switch changes nothing on this
route whichever way it is set. The leg that is entirely US domestic is the behind-San Jose connecting
feed, built in `route_feed`, and `route_feed` does not consult `od_source` at all. So the DOT
capability reaches the leg that cannot use it and not the leg that can.

**The three pieces, in order.**

1. Route the behind leg through `od_source` so US domestic feed markets read DB1B with Sabre
   underneath for the tail DB1B cannot see. `route_feed.behind_market` is the entry point. This is
   the piece that earns the claim.
2. Carry `od_source`'s label into the payload and through `forecast_to_contract` into the contract,
   the way `forecast_engine` and `feed_level` already report themselves, so every slide's source line
   states what was actually read.
3. Set the default. Recommendation: `auto` for US markets. A switch that has to be remembered is a
   switch that will be forgotten, and the whole US proposition depends on it being on.

**Until this is done the source line stays "Sabre MI and OAG".** Writing DOT DB1B onto a slide
produced from a Sabre run would be the same fault as the four found in the contract, committed on
purpose. After it is done the line reads "DOT DB1B for the US domestic markets, Sabre MI for
international, OAG schedules", which is both true and the sentence that sells.

**Re-measure after.** Changing the behind leg's data source changes the connecting forecast, so the
SJC-TPE reconciliation and any published figure have to be re-read, not assumed to hold.

---

## Job 2: the forecast pack, John's corrections

`deck/forecast_pack.py` renders 13 pages from a contract and the content budget is clean. The page
list is a copy of the forecast section of `China Airlines TPE-SJC Forecast 17Sep25.pptx`, slides 6, 7
and 32 to 41. John reviewed the first render on 14 August. His corrections, with what each needs:

**Straightforward.**

- No images anywhere. Almost certainly one cause: `forecast_pack` renders without a resolver, while
  the Observatory path passes `avia_slots.SlotResolver`. Fixing that should restore the cover image
  and the divider image together.
- The disclaimer must read The Aviation Observatory, or Meridian by The Aviation Observatory. This is
  not an Avia Solutions product. It must also name who it was prepared for.
- "Load factor", not "Planned load factor".
- The connecting tables need a three-letter airport code column before the city name, and years on
  the base demand and forecast headings.

**Needs a column the contract does not carry.** The traffic forecast table must match slide 32: base
annual demand labelled with its year, a traffic growth column from base year to forecast year, **base
annual demand at the forecast year before stimulation**, a stimulation rate column, forecast traffic
labelled with its year, and the six notes underneath. The contract carries the base year figure and
the post-stimulation figure and nothing between them, so the un-stimulated forecast-year column has to
be added at `forecast_to_contract`.

**Needs a build.** The table must carry "with direct competition" and "no direct competition" rows.
The analyst captures the two halves at different rates, 0.0% against 1.5% at Taipei and 0.2% against
4.7% at San Jose. Meridian has one blended rate per side. Producing those rows means deciding, per
O&D, whether a nonstop alternative exists. See Job 3: this is the best candidate for the 19% gap.

**Needs a map and figures that were never wired.** The catchment page must be a map with population at
each end of the route. `deck_contract` line 280 says it plainly: "Zone geometry and per-band
population/demand come from the catchment module; definitions here, figures wired from the model."
They were never wired. Both the map and the population figures need building.

**Also wanted:** a route map with a great circle and the schedule options, as on the 2025 deck.

---

## Job 3: why our connecting leg reads 19% below the analyst

**The comparison, corrected.** The 25,999 the log has been reconciling against since 11 August is the
analyst's BASE YEAR, not his forecast. Slide 32 of the September deck carries his table in full:
point to point 131.2k grown 33.0% to 174.5k, stimulated x1.20 to 209.4k, captured at 35.0% for 73.3k;
connecting at TPE 1,097.6k at 1.5% for 16.0k; connecting at SJC 1,128.5k at 1.6% for 18.6k; grand
total 107.9k at 259 per trip each way. FEED-LEVELS records his beyond as 12,007 and behind as 13,992;
multiplied by his own 33.0% those give 15,969 and 18,609, within 0.2% of his stated figures.

**On the matched year**, SJC-TPE CI A359 306 4x 2028 floor off against his YE Jun 2028:

| | Meridian | Analyst | |
|---|---|---|---|
| Total | 111,384 | 107,900 | +3.2% |
| Point to point | 83,379 | 73,300 | +13.8% |
| Connecting | 27,976 | 34,600 | -19.1% |

The errors offset, which is why the total lands inside 3%. Do not quote the total agreement without
saying so.

**The candidate, and it is testable.** His competition split. A single blended connecting capture
cannot represent a market where half the O&Ds already have a nonstop, and the two halves he captures
at 0.0%/1.5% and 0.2%/4.7% differ by more than an order of magnitude on the San Jose side. Building
it serves Job 2 as well.

**Two other differences recorded, not yet tested.** His stimulation is 1.20 on point to point and 1.00
on both connecting legs. And his three slide 7 market figures are defined differently from ours:
point to point 174,500 against our 368,464, over Taipei 1,097,600 against 696,196, over San Jose
1,128,500 against 179,481. Both sides footnote the same catchment, so this is a definition gap inside
one named catchment and it is resolvable against Sabre.

---

## Carried, and still John's

- `origin_share` 0.62 and `business_share_destination` 0.22 in `app/segment_inputs.py`. Placeholders
  with no measured source. They gate the eight-segment table, which is why `segment_forecast` reports
  50%.
- `avg_ow_fare_connecting`, `cask` and `ancillary_revenue` are empty. The first is what the whole
  revenue build stands on.
- The average one-way point to point fare reads 2,055.65 and `total_revenue` is 2,078 per available
  seat. The arithmetic is internally consistent and the passenger counts are confirmed as one-way
  segments by the PDEW cross-check. Whether 2,055 is right needs a sourced comparison against Sabre's
  measured fare, and it multiplies through every revenue figure on the deck.
- Accounts, and the save-preferred-routes button that waits on them.

---

## Do not disturb

The connecting feed runs at `qsi_k` 1.0. RECUT-RESULT measured it over-reading actual connecting
traffic by circa ten times on the median back-test route, and FLOOR-EVIDENCED-WAS-MISREAD removed the
softening that made that look smaller. It is exposed as a parameter and defaults to the shipped value.
Note that this route reads 19% BELOW a human forecast on the same leg, and SJC-TPE-IS-INSIDE
established the route is not atypical, so the two findings are not yet reconciled.

The half-year OAG union is built and off behind `AVIA_BT2_HALFYEAR`. It changes `capa`, `qcx` and
`legs_n` for the 2016 and 2017 training years and needs a capture rebuild and a re-measure.

The published claims stay unless John decides otherwise.

---

## Working rules

Verify, do not assert. Before comparing two numbers, state what basis each is on. Follow a field back
to where it is set before reasoning about it: four of the five faults found on 14 August were a figure
that had quietly changed what it measured while keeping its name, and two more were introduced by
generalising from a truncated or partial read.

Ask before running anything over about twenty minutes. House style throughout, including code
comments.

Avia Solutions Limited. All rights reserved.
