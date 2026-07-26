# Northern Ireland - Dublin catchment and APD removal: can our Sabre MIDT and OAG data do the job?

Data feasibility test. Prepared by Avia Solutions. Purpose: establish, before we respond to the RFP, whether Avia's existing Sabre MIDT and OAG holdings can identify the Northern Ireland / Dublin catchment and support an estimate of the impact of removing Air Passenger Duty. This memo shows what we tested and what the data returned, so the RFP response rests on demonstrated capability rather than assumption.

## Scope of the test

Two questions from the RFP drove the test. First, can we identify the catchment, meaning the airport choice of Northern Irish air travellers across Belfast International (BFS), Belfast City (BHD), City of Derry (LDY) and, by leakage, Dublin (DUB). Second, can we measure the cross-border leakage to Dublin and its history, which is the quantity an APD-removal impact estimate turns on.

We ran the test on the Sabre MIDT origin and destination store covering 2013-2025 and confirmed the presence of the OAG schedule store. The MIDT store carries, per O&D itinerary: origin and destination airports, marketing and operating airline, cabin, connecting points, point-of-origin fields (airport, city, city name, country, country name, region name), passengers, average base and total fare in USD, base and total revenue, distance, and a directionality flag. Fares therefore exist at O&D level, which matters for the impact question.

## Finding 1: the Northern Ireland airport split is measurable and clean

Where all the airports sit inside one jurisdiction, MIDT point of origin behaves. Filtering to Northern Irish residents by home city (point-of-origin city in the Northern Ireland town set) and splitting their departures across the three NI airports gives a stable, readable series.

| Year | NI resident pax | BFS | BHD | LDY |
|------|----------------:|----:|----:|----:|
| 2013 | 2,366,367 | 58.3% | 36.1% | 5.5% |
| 2015 | 2,497,812 | 60.6% | 36.0% | 3.5% |
| 2017 | 2,882,663 | 69.1% | 28.9% | 1.9% |
| 2019 | 2,970,482 | 72.8% | 25.3% | 1.9% |
| 2021 | 2,126,280 | 74.5% | 23.0% | 2.4% |
| 2023 | 2,655,431 | 74.1% | 24.1% | 1.8% |
| 2025 | 3,200,117 | 73.2% | 24.7% | 2.2% |

The catchment has shifted, and the direction is consistent across twelve years: Belfast International rose from 58% to 73% of the resident split, Belfast City fell from 36% to 25%, and Derry more than halved to circa 2%. That movement is the low-cost carrier concentration at Aldergrove, and the data captures it cleanly. For the catchment-identification component of the RFP, within Northern Ireland the data works.

## Finding 2: cross-border leakage to Dublin does not survive in MIDT point of origin

This is the component the impact estimate depends on, and it is where the data test returned a warning rather than a number. We show the full path because the failure mode is not obvious.

### The first cut looked like a clean answer, and was not

Filtering by point-of-origin country (GB) across all four airports and reading Dublin's share of that population produced an apparently coherent leakage series: 31.3% in 2013 rising to circa 35% by 2015 and settling at 32.2% in 2025, with Belfast and Dublin GB-origin volumes moving together year on year.

| Year | Belfast (GB-poo) | Dublin (GB-poo) | Dublin share |
|------|-----------------:|----------------:|-------------:|
| 2013 | 3,224,486 | 1,468,261 | 31.3% |
| 2015 | 3,440,125 | 1,826,555 | 34.7% |
| 2019 | 4,055,752 | 2,042,581 | 33.5% |
| 2025 | 4,124,414 | 1,954,851 | 32.2% |

Read at face value this says a third of the catchment leaks to Dublin, worth circa 1.95m passengers in 2025. That reading is wrong.

### The diagnostic: who is actually at Dublin

Breaking the GB-origin Dublin departures down by point-of-origin city exposes the problem. The 2025 mix is:

| Point-of-origin city | Pax at Dublin (GB-poo, 2025) |
|----------------------|-----------------------------:|
| London | 853,223 |
| Manchester | 227,136 |
| Birmingham | 170,606 |
| Edinburgh | 130,340 |
| Liverpool | 109,257 |
| Bristol | 105,707 |
| Glasgow | 104,909 |
| Leeds | 87,475 |
| Newcastle | 51,848 |
| Nottingham | 41,226 |

Belfast does not appear in the top fifteen. These are British mainland residents, and what shows as a Dublin departure is the return half of a Britain-to-Dublin round trip: the point of origin stays with the traveller's home city across both legs, so a Londoner on the Dublin-to-London leg carries a London point of origin. Britain-Dublin is one of the densest short-haul markets in Europe, so those return legs dominate the GB-origin count at Dublin. The corroborating signature was already visible in the destination breakdown of the "leakage": every top destination was a GB airport (Heathrow, Manchester, Edinburgh, Glasgow, Liverpool), which is British inbound traffic going home, and not a route a Northern Irish resident would drive to Dublin to fly.

The retained side carries a smaller version of the same effect. GB-origin departures from Belfast International are 2,342,188 from Belfast itself, then a tail of London (168,538), Liverpool, Edinburgh and other British cities visiting Belfast and flying home. So point-of-origin country contaminates both airports, and more heavily at Dublin.

### The correction, and what it reveals

Identifying the traveller by home city rather than country removes the British mainland return legs. On that clean basis, Northern Irish residents departing from Dublin fall to 56 passengers in 2025, and Dublin's share of the resident split reads 0.0% in every year from 2013 to 2025 (the corrected trend table in Finding 1 carries the DUB column at 0.0% throughout; it is omitted there for width).

That figure is not credible as an absence of leakage, and the reason is a property of the data rather than of Northern Irish behaviour. MIDT point of origin tracks residence well for British mainland travellers, which the London-shows-as-London evidence above confirms. A Northern Irish resident who books and departs through the Irish system is assigned an Irish point of origin and becomes indistinguishable from a Dublin resident. Once the traveller crosses into the Irish booking ecosystem, MIDT point of origin no longer identifies them as Northern Irish. The genuine leakage is therefore neither in the GB-origin pool (which holds British visitors) nor recoverable from the Irish-origin pool (where it merges with real Dublin demand).

The directionality field does not rescue this. It holds two values, ND (55,028,066 records) and POO (9,959,428), rather than an outbound-versus-inbound flag, so it does not by itself separate a return leg from an outbound one.

The consequence for the RFP: the size of NI-to-Dublin leakage, and its year-by-year history, do not survive in MIDT point of origin for this cross-border pair. Both MIDT figures the test produced are unusable in opposite directions, the country-level cut over-counting through contamination and the city-level cut under-counting through Irish point-of-origin coding.

## What each RFP component needs, mapped to what the data returned

| RFP component | Signal it needs | What the test showed |
|---------------|-----------------|----------------------|
| Identify the NI catchment (airport choice within NI) | Resident airport split | Delivered cleanly by MIDT point-of-origin city (Finding 1) |
| Size the leakage to Dublin | Count of NI residents departing Dublin | Not recoverable from MIDT point of origin (Finding 2); needs a residence-anchored source that MIDT is not |
| History / trend of leakage | Leakage series by year | Same limitation as size; the MIDT series is contamination, not leakage |
| Route breadth as a leakage driver | Dublin vs Belfast schedule and destinations | Schedule-based and independent of point of origin; available in OAG (store confirmed present, not yet exercised in this test) |
| Frequency and fare on overlapping routes | Departures and O&D fare, both airports | Frequency in OAG; O&D fares present in MIDT (avg base and total fare, USD); measurable without point of origin |
| Impact of removing APD | Demand response to a fare change, applied to a leakage base | The fare and demand relationship on overlapping routes is in the data; the leakage base it must be applied to is the quantity Finding 2 cannot supply from MIDT |

The pattern the test establishes: MIDT and OAG measure schedules, fares and within-jurisdiction airport choice directly, and they do not measure the cross-border leakage count that the impact estimate is built on.

## APD policy timeline (reference)

The duty history is public policy and gives dated events for any impact work.

The Republic of Ireland Air Travel Tax began in Budget 2009, at €10 per passenger for destinations more than 300 km from Dublin and €2 below that. It moved to a flat €3 from 1 March 2011 after an EU internal-market objection to the distance banding, and it was abolished on 1 April 2014.

In the United Kingdom, direct long-haul APD in Northern Ireland was reduced to the short-haul (Band A) rate in September 2011 and then devolved and set to zero from 1 January 2013, to protect the Belfast-Newark service. Short-haul APD in Northern Ireland stayed at the full UK rate. That reduced (economy) short-haul rate was £12 from 2010, £13 from April 2012 and held to 2023, then £15 from 2024. The standing wedge on a short-haul departure is therefore circa £13-15 at Belfast against nothing at Dublin after April 2014, applied to almost all of Belfast's flying, since the zero rate covers only direct long-haul.

## Methods and files

All queries ran read-only against the Sabre MIDT store (`C:\Avia\sabre.duckdb`) at 2013-2025 coverage; the OAG store (`C:\Avia\oag.duckdb`) is present and confirmed. Northern Irish residents are defined by point-of-origin city membership of the Northern Ireland town set (Belfast, Londonderry/Derry and the district towns). Airports: BFS, BHD, LDY, DUB.

Scripts (in `C:\AviaDev\app`): `catchment_trend_ni.py` (point-of-origin country trend, the contaminated first cut), `leakage_why.py` (breadth-versus-choice split, also on the contaminated base), `apd_experiment.py` (year series against the policy events, contaminated base), `leakage_diag.py` (the diagnostic and the point-of-origin-city correction). The contaminated scripts are retained as the evidence trail for the failure mode, not as producing usable leakage figures.

## Sources

- [Air Travel Tax (Republic of Ireland) - Wikipedia](https://en.wikipedia.org/wiki/Air_Travel_Tax)
- [Air Passenger Duty historical rates - GOV.UK](https://www.gov.uk/government/statistics/air-passenger-duty-bulletin/air-passenger-duty-rates)
- [Air Passenger Duty (Setting of Rate) Act (Northern Ireland) 2012 - legislation.gov.uk](https://www.legislation.gov.uk/nia/2012/5/notes/division/5/1)
- [Northern Ireland scraps APD on long-haul flights - Cheapflights](https://www.cheapflights.co.uk/news/northern-ireland-scraps-air-passenger-duty-on-long-haul-flights)
- [Air Passenger Duty - Wikipedia](https://en.wikipedia.org/wiki/Air_Passenger_Duty)
