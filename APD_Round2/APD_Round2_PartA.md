# APD study, round two, Part A: data-store queries

Prepared by Avia Solutions. Started 20 July 2026. One running document for all Part A tasks, with CSVs alongside in the same folder. Sections are added as tasks complete.

**Basis on every figure: one-way departures**, being the sum of the `passengers` field filtered to `origin_airport`. Where a two-way figure appears it is stated as such. Sources: Sabre GDD store `C:\Avia\sabre.duckdb` (table `sabre`); OAG store `C:\Avia\oag.duckdb` (table `oag`); airport-to-country mapping `C:\Avia\airport_city_country.csv` (3,568 airports). Year labels read from source. 2020 is absent from the store and is shown as a gap throughout, never interpolated. 2013 and 2015 are POO-pulled and are labelled as such wherever they appear; all other years are ND-pulled, and level comparisons are made on ND years only.

**Status: Part A complete, A1 to A7.** Everything is run on data held as at 20 July 2026, ahead of the RFP response, so nothing waits on the full-year OAG upload. Three declared dependencies remain, each of which limits a specific output rather than the task: A2's Aer Lingus seat comparison needs the schedule upload; A4's purpose split needs NISRA and CSO survey proportions; and A5's absolute contribution test needs airport charges for BFS, CDG and BCN. A5b, A6 and A7 are unaffected by the schedule upload, because what they take from OAG is fleet mix and sector length, which are rates rather than annual totals. A5b, A6 and B7 should follow the full-year OAG upload expected by Friday 24 July 2026.

---

## A1. Paris reconciliation (blocking item)

### The discrepancy as set

T1.4 puts addressable Paris demand at 38,364 two-way and describes the screen as an upper bound. T1.4b captures 73,824 two-way, 1.92 times the screen, which breaches the bound. Barcelona behaves as expected across the same pair of methods, capturing 28,773 against a screen of 58,090, so the fault is specific to Paris rather than general to the method.

### Finding 1: Paris is already served nonstop from Belfast, so it is not a route-creation candidate

This is the primary cause, and it is not a numerical error.

OAG shows easyJet operating BFS-CDG in every year the store holds, 2015 to 2026, without a break. In the 2025 sampled weeks the service runs 16 departures across two weeks on A320 and A319 equipment, 2,766 seats, which is circa 8 departures a week or roughly daily.

Sabre confirms the traffic is mature. Of 64,602 NI-origin departures to CDG in 2025, 60,498 already travel nonstop, a nonstop share of 93.6%. Only 4,103 connect.

A screen built to size demand on unserved routes should not have contained Paris. A QSI capture model run against an already-served route returns the traffic that route already carries, so the 73,824 is substantially a re-measurement of existing easyJet nonstop traffic rather than demand a new service would create. That also accounts for the capture rate of 17.1% against Barcelona's 7.4%: the Paris nonstop exists and already holds its market.

### Finding 2: the 1.92 ratio matches the basis factor, so a departures and two-way mix is a live second cause

73,824 / 38,364 = 1.924, which sits on the 1.94 two-way-to-departures factor established in round one. Measured against the store, NI-origin departures to all Paris board points in 2025 total 72,571, within 1.7% of the 73,824 capture figure. The capture figure therefore carries a two-way label while matching a departures-basis quantity. Either the capture was computed on departures and labelled two-way, or the screen was, and the capture is right. Both cannot be on the stated basis. Resolving which needs the T1.4 and T1.4b working, which is not on this machine.

### Finding 3: the board-point asymmetry is real, and it sits on the Barcelona side

The brief asks whether the QSI catchment drew Paris from a wider board-point set than Barcelona. The data says the opposite.

| Metro | Board point | NI-origin departures 2025 | NI-bound arrivals 2025 | Nonstop share of departures |
|---|---|---:|---:|---:|
| Paris | CDG | 64,602 | 64,645 | 93.6% |
| Paris | BVA | 7,793 | 7,038 | 89.6% |
| Paris | ORY | 175 | 163 | 0.0% |
| **Paris** | **all three** | **72,571** | **71,848** | **93.0%** |
| Barcelona | BCN | 19,987 | 19,995 | 59.6% |
| Barcelona | REU (Reus) | 32,167 | 34,029 | 99.8% |
| Barcelona | GRO (Girona) | 15,172 | 15,731 | 99.1% |
| **Barcelona** | **all three** | **67,326** | **69,755** | **87.7%** |

Paris is 89% CDG, so metro and primary airport nearly coincide. Barcelona city is 19,987 alone, but the catchment including Reus and Girona is 67,326, 3.4 times larger. Reus and Girona are Ryanair fields serving the Costa Dorada and Costa Brava rather than Barcelona city, so their inclusion is a judgement that moves the market by a factor of three. If the screen and the capture applied different rules there, the two candidates were never comparable, and the capture-rate gap of 17.1% against 7.4% partly measures that. On the full catchment definition the two markets are similar in size, 72,571 against 67,326 departures, consistent with round one describing them as similar.

Dublin-origin volumes to the same board points, for market-size context: Paris 475,410 (CDG 238,940, BVA 154,295, ORY 82,175); Barcelona 459,528 (BCN 332,172, REU 88,543, GRO 38,813).

### Finding 4: OAG is presently a sample-week store, and the 2015-2016 years hold overlapping rollups

Noted while checking the Paris service. The full-year schedule upload is in progress and expected complete by Friday 24 July 2026, so most of this resolves itself; two points survive the upload.

Week labels held per year: 2015 and 2016 carry 17 labels each; 2017 to 2025 carry 2 each (late May and late October, for example 2025-05-26 and 2025-10-27); 2026 carries 1.

2015 and 2016 are full years, but they are stored as overlapping rollups of the same underlying data: a whole-year label (`2015`), monthly labels (`2015-01` to `2015-12`), half-year labels (`2015-H1`, `2015-H2`) and specific week labels (`2015-05-25`). Summing across labels therefore multiplies the same traffic several times over. The rule is to select one consistent label set within a year rather than aggregate across them. This is why BFS-CDG appears as 294 frequencies in 2015 against 16 in 2025, which reads as a collapse in service and is entirely an artefact of the label mix.

Consequences: any schedule series crossing the 2016 to 2017 boundary is invalid unless one consistent label is selected per year; and A5b, A6 and B7 all depend on this store, so each is better run after Friday's upload than before, with the basis stated on its face either way.

### Reconciled position

Paris should not sit in a route-creation screen, because Belfast has a mature daily easyJet service to CDG carrying 60,498 nonstop NI-origin passengers a year. The capture figure of 73,824 is not addressable new demand; it is close to the entire existing NI-origin Paris market across all board points, 72,571 departures, which is what a capture model returns when pointed at a served route. Since round one noted that Paris carries essentially the whole route-creation benefit, the route-creation case needs rebuilding on genuinely unserved destinations, with Paris, Reus and Girona treated as served.

A single reconciled number cannot be issued from this machine. Two things are needed: the T1.4 and T1.4b working, to establish which figure carries the wrong basis; and a decision on whether the candidate set is rebuilt.

### Related: the recapture-leakage tables need a definitional fix before they feed anything

Two "top destination markets" tables were supplied during this task, both headed "Belfast catchment, 25 destination markets ranked by recapture leakage, Sabre 2025". They do not agree with each other and contain rows that cannot be right.

The same destination carries different markets across the two tables: Paris CDG reads 165,818 each-way with 37% via home in the first and 345,106 with 0% via home in the second; London LGW reads 1,799,974 against 756,537. Other destinations are identical across both (Manchester 712,673, Edinburgh 539,176). That pattern indicates the market is computed relative to the selected home airport rather than to the catchment.

Three defects follow. Via-home appears to mean via the selected airport rather than via any Belfast airport, so Paris reads 0% served from Belfast City despite a daily easyJet service from Belfast International eight miles away, and the entire market books as leakage. Self-referential rows appear, with Dublin and Belfast International both listed as destination markets of the Belfast catchment at 0% via home and 100% leakage. And connecting-hub traffic is counted as leakage, which is what puts Dubai, Toronto and Stornoway in the table at 100% leaked.

If the addressable screen was built from a leakage column defined this way, that is a second and independent route to the A1 error, because Paris would appear wholly unserved on the Belfast City view.

### What could not be produced

- The corrected row for `t14b_qsi_capture.csv` is not issued: the source file is not on this machine. Nothing under `C:\Avia`, `C:\AviaDev` or the Avia QSI Tool folder matches the round one T1 outputs.
- Check three of the brief, whether the T1.3 proportional allocation under-allocated Paris, is not run, for the same reason. It needs the allocation method, which cannot be reconstructed from the Section 0 summary figures.

**Files:** `a1_paris_boardpoints.csv`.

---

## A2. Dublin self-connect and the UK long-haul feed

### Hypothesis under test

That part of Dublin's outbound growth since 2016 is Great Britain passengers self-connecting onto Aer Lingus transatlantic services, recorded as Dublin-origin because the two tickets are unlinked. If material, Dublin's Irish-resident outbound is overstated, its inbound share understated, and part of what reads as Dublin stimulating its own market is Dublin taking UK market share.

**Verdict: indeterminate.** An earlier draft of this section concluded the hypothesis was not supported. That conclusion was withdrawn on 20 July 2026 after review. Once the duty rules are applied correctly, each piece of evidence that appeared to refute the hypothesis is equally consistent with it, because the duty structure gives passengers a direct incentive to move from the visible through-ticket channel into the invisible separate-ticket one. The three observations are set out below with that ambiguity stated, followed by the bound on what cannot be seen.

**The duty mechanics that drive the ambiguity.** Under HMRC's connected-flights rule, two flights on the same ticket or on conjunction tickets, where the onward international flight departs within 24 hours of arrival, are treated as one journey and charged at the band of the final destination. A single-ticket Great Britain to Dublin to United States itinerary therefore pays the long-haul rate of circa £94, not the £13 short-haul rate. Flights on separate tickets are never connected for duty purposes, whatever the timings, so a passenger who buys Great Britain to Dublin and Dublin to the United States separately pays only £13 on the UK departure. A stopover beyond 24 hours breaks the connection on a single ticket to the same effect.

The saving of circa £81 a passenger therefore accrues only to separate-ticket self-connectors and to those breaking the journey beyond 24 hours. It does not accrue to the single-ticket through-market at all. That matters twice over: it inverts the fiscal reading below, and it means the population that benefits from the duty gap is precisely the population this data cannot see.

Two consequences follow, both of which widen the invisible population well beyond same-day airport transfers.

**Splitting tickets does not require a second airline.** The connection test is the ticket, not the carrier. A passenger who buys an Aer Lingus ticket to Dublin and, separately, an Aer Lingus return from Dublin to the United States has two unconnected journeys and pays £13, exactly as if the first leg were on Ryanair. Carrier mix therefore carries no information about self-connect at all, since the behaviour is available on every carrier including the one selling the through fare. This removes most of the evidential weight from A2.3.

**The overnight stopover achieves the same result and looks like tourism.** A stay beyond 24 hours breaks the connection even on a single ticket. A passenger who spends one night in Dublin before flying on pays £13 rather than circa £94, and the £81 saved covers a substantial part of the night's accommodation. The duty gap therefore does not merely move the departure airport; it funds a Dublin city break, and it diverts the associated visitor spend from the United Kingdom into the Irish economy. That is a distinct economic channel and belongs in the economic module at B3 rather than only in the fiscal one.

**Why this is structurally invisible.** O&D construction breaks an itinerary into separate journeys at a stopover threshold close to the same 24 hours that the duty rule uses. The data boundary and the tax boundary very nearly coincide. So the population that avoids the long-haul charge is, by construction, recorded as two unrelated O&Ds: a Great Britain to Dublin trip and a Dublin to United States trip, indistinguishable from a British visitor to Ireland and an Irish resident flying to America. The visible connecting market at A2.1 is approximately the set that pays the long-haul rate, and everything that avoids it falls outside the measurement.

### A2.1 The visible single-ticket through-market is large but flat

Great Britain origin, single-ticket itineraries connecting at Dublin, destination United States or Canada. ND years only for level comparison; POO years labelled.

| Year | Pull | UK-origin via Dublin to North America |
|---|---|---:|
| 2013 | POO | 56,452 |
| 2014 | ND | 95,061 |
| 2015 | POO | 97,458 |
| 2016 | ND | 186,803 |
| 2017 | ND | 166,448 |
| 2018 | ND | 123,737 |
| 2019 | ND | 119,504 |
| 2020 | - | gap, absent from store |
| 2021 | ND | 67,197 |
| 2022 | ND | 113,274 |
| 2023 | ND | 180,523 |
| 2024 | ND | 154,267 |
| 2025 | ND | 187,892 |

The market is substantial, circa 188,000 one-way departures in 2025, and it is flat across the ND period: 186,803 in 2016 against 187,892 in 2025, a rise of 0.6%, with a dip through 2018 and 2019 and the COVID trough. Over the same period Dublin's own North America market grew 66.4%. The through-market therefore fell as a proportion of Dublin's North America volume, from 17.0% to 10.2%.

**Why this does not settle the question.** A flat visible through-market alongside a growing Dublin transatlantic operation is what substitution looks like as well as what absence looks like. These single-ticket passengers pay the long-haul rate of circa £94; a passenger who splits the same journey across two tickets pays £13. Passengers moving from the first channel to the second would hold the visible series flat while the invisible one grew, producing exactly the pattern above.

### A2.2 Dublin's North America traffic by point of origin: UK residents are negligible, and Irish-resident demand is the growth

| Year | Pull | Ireland | UK | Other | Total | UK share |
|---|---|---:|---:|---:|---:|---:|
| 2016 | ND | 470,843 | 1,896 | 629,150 | 1,101,890 | 0.2% |
| 2017 | ND | 542,292 | 4,190 | 746,642 | 1,293,125 | 0.3% |
| 2018 | ND | 738,640 | 2,611 | 968,435 | 1,709,686 | 0.2% |
| 2019 | ND | 736,371 | 2,770 | 1,006,336 | 1,745,477 | 0.2% |
| 2021 | ND | 429,962 | 3,583 | 484,103 | 917,649 | 0.4% |
| 2022 | ND | 547,344 | 1,062 | 702,207 | 1,250,615 | 0.1% |
| 2023 | ND | 645,161 | 1,834 | 923,316 | 1,570,312 | 0.1% |
| 2024 | ND | 796,838 | 11,596 | 1,006,151 | 1,814,585 | 0.6% |
| 2025 | ND | 894,682 | 1,862 | 937,466 | 1,834,011 | 0.1% |

Growth 2016 to 2025: total +66.4%, Irish-resident +90.0%, other-resident +49.0%. Irish-resident demand nearly doubled and is the larger part of the growth. The "other" half is predominantly North American residents flying home, which is legitimate inbound.

**This does not disprove the hypothesis, and cannot.** A UK resident buying a separate Dublin-to-US ticket has that journey's point of origin recorded at Dublin, not in Britain, which is the same mechanism as Trap 1. Separate-ticket self-connects are therefore invisible in this field by construction. The 0.1% UK share measures the visibility of the field, not the absence of the behaviour.

### A2.3 Aer Lingus's own Great Britain feed has shrunk, which cuts against a GB-fed hub

Great Britain to Dublin, nonstop, by marketing carrier, one-way departures.

| Year | Total | Ryanair (FR) | Aer Lingus (EI) | British Airways (BA) |
|---|---:|---:|---:|---:|
| 2016 | 4,045,025 | 2,683,138 | 852,718 | 278,353 |
| 2019 | 4,524,015 | 2,742,247 | 874,986 | 771,295 |
| 2025 | 4,357,296 | 2,990,425 | 675,390 | 622,640 |

Change 2016 to 2025: total +7.7%, Ryanair +11.5%, British Airways +123.7%, Aer Lingus **-20.8%**.

An earlier draft read this as the strongest evidence against the hypothesis, on the reasoning that a carrier building a Great Britain-fed hub would grow its own Great Britain feed. That reading does not survive the duty rules.

Aer Lingus is the carrier that can sell the through ticket, and the through ticket is the tax-disadvantaged product: it carries the connected-flight charge at the long-haul band, circa £94, while the same journey split across two tickets carries £13. The passenger has an £81 incentive to abandon Aer Lingus's through product and buy the cheapest Great Britain to Dublin seat separately. Ryanair does not interline onto Aer Lingus transatlantic services, so any Ryanair passenger continuing across the Atlantic is on separate tickets by construction, self-connecting, and paying the short-haul rate.

Aer Lingus's through-feed falling 20.8% while Ryanair's point-to-point carriage rises 11.5%, a gain of 307,287 departures, is therefore precisely the signature that substitution into self-connect would produce. The observation is consistent with the hypothesis and with its negation, and it cannot separate them.

It is weaker still than that. Because the connection test is the ticket rather than the carrier, an Aer Lingus passenger can split an Aer Lingus itinerary and pay £13, so the 675,390 Aer Lingus Great Britain to Dublin departures remaining in 2025 may themselves contain self-connectors. Carrier mix cannot identify the behaviour in either direction, and this table should be read as market context rather than as evidence on the hypothesis.

### A2.4 Bounding the invisible residual: the propensity test

Since separate-ticket self-connects cannot be seen, the residual is bounded by asking whether Irish-recorded North America demand is larger than Irish residents can plausibly account for.

| Metric | United Kingdom | Ireland |
|---|---:|---:|
| Resident departures to North America, 2025 | 6,007,901 | 1,074,191 |
| Population 2025 | 69,487,000 | 5,458,600 |
| Departures per head per year | 0.0865 | 0.1968 |
| Of which departing Dublin | 1,862 (0.03%) | 894,682 (83.3%) |

Irish residents make 2.28 times as many North America trips per head as UK residents. At UK-equivalent propensity, Irish-resident demand would be 472,169 against the 1,074,191 observed, an excess of **602,022 one-way departures**.

That 602,022 is an upper bound and should not be read as an estimate of self-connect traffic. It assumes Ireland ought to look like Britain on North America propensity, which is a weak assumption: Ireland has a diaspora relationship with the United States, a concentration of US corporate employment, and the only US preclearance facilities in Europe, all of which raise genuine Irish-resident propensity. The true figure lies somewhere between zero and 602,022 and cannot be resolved from this data. B7 item 6 asks the same question and should be treated as this analysis rather than repeated.

### The fiscal reading, corrected

An earlier draft of this section put circa £15.4m a year of duty not collected, by applying the £81 differential to the 187,892 single-ticket through-market plus the 1,862 UK point-of-origin Dublin departures. **That figure is withdrawn. It is wrong, and the sign is inverted.**

Under the connected-flights rule those 187,892 single-ticket passengers are charged at the band of their final destination, so they pay the long-haul rate of circa £94 on the UK departure. They are duty revenue at the long-haul band, not duty foregone. Applying a saving to them reversed the direction of the effect.

The duty gap is real, but it attaches only to separate-ticket self-connectors and to journeys broken beyond 24 hours, and neither appears in this data. A UK resident's separate Dublin to United States ticket carries a Dublin point of origin, so it cannot be distinguished from Irish-resident demand. **No fiscal figure for the Dublin routing differential can be issued from this data.** What can be said is the unit rate, £81 a passenger, and that the volume it applies to is unmeasured and structurally invisible in the point-of-origin field.

The order-of-magnitude comparison the brief asks for stands on the rate alone: the duty gap driving a Great Britain passenger toward Dublin for a transatlantic journey is £81 a head, against the £13 at issue for short-haul departures from Northern Ireland. That is the comparison, and it does not require a volume to make.

### What would actually test this

Three tests, none of which the current data supports and two of which become available with the full-year schedules.

1. **Survey cross-check against air arrivals, the strongest test and runnable now.** Sabre gives Great Britain to Dublin air O&D. The CSO and Fáilte Ireland publish surveyed inbound visitors from Great Britain, with purpose and length of stay. Air arrivals materially in excess of surveyed visitors to Ireland would bound the population that flew to Dublin without visiting Ireland, or stayed only the single night that the duty saving funds. Unlike the propensity bound at A2.4, this is anchored in an independent measurement rather than an assumption about how Ireland ought to behave. It also catches the overnight-stopover population, which the timing test below cannot.

2. **Connection-bank timing, after the schedule upload.** If Great Britain to Dublin arrivals cluster in the hours before the Aer Lingus transatlantic departure wave, that is a self-connect signature, because point-to-point traffic has no reason to align systematically with a long-haul bank. Needs full-year OAG schedules with times. Note the limit: this catches only same-day transfers, and by construction misses everyone taking the overnight break.

3. **Great Britain origin-city mix, runnable now.** If self-connect is material, Dublin usage should over-index from Great Britain cities with weak or absent direct United States service, and under-index from cities with strong direct service. Sabre carries the Great Britain to Dublin city detail and the city-to-United States direct volumes.

4. **Great Britain side propensity bound, runnable now.** The same method applied to Ireland in A2.4, run in reverse: compare Great Britain to Dublin point-to-point growth against plausible Ireland-visiting demand, treating any excess as a candidate volume with the same upper-bound caveats. Test 1 supersedes this where the survey data allows, being measured rather than assumed.

### A2.5 Survey cross-check: air arrivals against surveyed visitors

Test 1 above, run on 20 July 2026. It produces a measured bound in place of the assumed one at A2.4, and it turned up a direct measurement of the transfer population that had not been identified before.

**The CSO measures transfer passengers directly.** The CSO Passenger Survey classifies everyone departing Ireland on overseas routes, and one of its same-day categories is foreign-resident transfer passengers. That category runs 898,600 in 2023, 896,800 in 2024 and 866,200 in 2025. This is a survey measurement of same-day transfer traffic through Irish ports and airports, all nationalities, and it is not modelled. It does not isolate Great Britain residents, and being same-day it excludes anyone taking the overnight break.

**The same table is the source of the leakage figure in Section 0.** The CSO's other same-day category, Northern Ireland residents heading outbound via an airport or seaport in Ireland, reads 1,011,300 in 2023, 804,700 in 2024 and 936,900 in 2025. Those match the Section 0 cross-border leakage figures of 1,011,200, 804,700 and 936,700 to within rounding, so the provenance of the leakage baseline is confirmed as this table.

**The cross-check itself.**

| Year | Sabre GB-resident air arrivals into Ireland | CSO GB overnight visitors, air and sea | Gap |
|---|---:|---:|---:|
| 2023 | 3,595,115 | 2,371,400 | 1,223,715 |
| 2024 | 3,843,320 | 2,439,800 | 1,403,520 |
| 2025 | 4,144,695 | 2,411,200 | 1,733,495 |

The gap is large and it is widening. Across 2023 to 2025 Sabre Great Britain air arrivals into Ireland rose 15.3%, while surveyed Great Britain overnight visitors rose 1.7% and measured same-day transfers fell 3.6%. Growth in Great Britain air arrivals is therefore not appearing as growth in Great Britain visitors to Ireland, nor in the transfer count.

**The bound.** Allocating every CSO same-day transfer and every other same-day visitor to Great Britain, which over-allocates because both categories cover all nationalities, gives a maximum CSO-attributable figure of 3,526,400 for 2025 against Sabre air arrivals of 4,144,695. That leaves an unexplained residual of at least **618,295** one-way arrivals. The true residual is larger, because the CSO overnight figure includes sea arrivals from Great Britain while the Sabre figure is air only.

**What the residual is not evidence of.** It is a gap between two differently constructed measurements, and several explanations compete before self-connect is reached. The CSO excludes Northern Ireland residents and anyone departing via Northern Ireland ports, while Sabre's GB point of origin includes Northern Ireland. The CSO counts overnight visitors and same-day travellers on a survey basis calibrated to passenger flow, with its own error. Sabre coverage may differ between years. And a genuine same-day business and leisure market exists on a route this short which the CSO records at only 249,000 across all nationalities, a figure that looks low for a market of this size and may itself be the anomaly.

What can be said is this. Three independent quantities now bear on the question: a measured same-day transfer population of circa 866,000 a year through Irish ports; a residual of at least circa 618,000 Great Britain air arrivals that no CSO category accounts for; and a divergence in which Great Britain air arrivals grew ten times faster than surveyed Great Britain visitors over 2023 to 2025. None of the three isolates Great Britain self-connect traffic, and the verdict on A2 remains indeterminate. But the space the hypothesis would occupy is now measured rather than assumed, and it is not empty.

### A2.6 Great Britain origin-city cut

Test 3 above. If self-connect is material, Dublin usage should be heavier from Great Britain places with weak direct United States access. Run at region level rather than airport level, because airport-level United States demand is meaningless where airports share a catchment: Luton records 86 United States passengers in 2025 not because Luton has no transatlantic demand but because that demand departs from Heathrow and Gatwick.

Great Britain residents, 2025, one-way departures.

| Region | Total outbound | To Dublin | Dublin rate | US and Canada demand | Of which nonstop | Direct share |
|---|---:|---:|---:|---:|---:|---:|
| London | 52,634,929 | 1,312,136 | 2.49% | 4,107,873 | 3,176,649 | 77.3% |
| North West | 14,875,293 | 559,082 | 3.76% | 611,599 | 333,479 | 54.5% |
| Scotland | 10,813,845 | 470,213 | 4.35% | 503,562 | 133,990 | 26.6% |
| Midlands | 6,430,266 | 334,869 | 5.21% | 52,423 | 6,084 | 11.6% |
| South West and Wales | 4,735,661 | 230,754 | 4.87% | 37,714 | 29 | 0.08% |
| Yorkshire and North East | 3,999,809 | 229,322 | 5.73% | 93,856 | 6,734 | 7.2% |

The inverse relationship the test predicted is present. London, with 77.3% of its transatlantic demand travelling nonstop, uses Dublin at 2.49% of outbound. Yorkshire and the North East, at 7.2% direct, uses Dublin at 5.73%, more than twice the rate.

**It is not decisive, and three confounds prevent it being read as support.** Region size tracks direct United States access almost exactly, since large regions are the ones that sustain nonstop transatlantic service, so size and access cannot be separated on six observations. The relationship is also not clean: South West and Wales has the weakest direct access of any region at 0.08% yet a lower Dublin rate than Yorkshire, which breaks the monotonic pattern the hypothesis predicts. And Dublin traffic from these regions is overwhelmingly visiting friends and relatives, with the Irish diaspora concentrated in precisely the places showing the highest rates, Liverpool at 8.46%, Glasgow at 5.52% and Birmingham at 5.44%. Diaspora geography explains the same pattern without any reference to transatlantic access.

Suggestive, consistent with the hypothesis, equally consistent with the distribution of Irish family ties across Great Britain. A2 stays indeterminate.

### What could not be produced

- Aer Lingus transatlantic departing seats from Dublin, to set against the Great Britain feed in A2.3, is not issued. It needs the OAG store, which currently holds two sampled weeks a year from 2017 and cannot give annual seat counts. This runs after Friday's upload.
- Item 4's capacity leg is answered through the propensity route above rather than through Dublin transatlantic capacity, for the same reason. It should be re-run against capacity once the schedules land.
- Origin-city detail for A2.3 is held in `a2_gb_dub_p2p_by_carrier.csv` at carrier level; the city cut is not yet run.

**Files:** `a2_gb_via_dub_northamerica.csv`, `a2_dub_northamerica_by_poo.csv`, `a2_gb_dub_p2p_by_carrier.csv`, `a2_propensity_bound.csv`, `a2_survey_crosscheck.csv`, `a2_survey_crosscheck_bound.csv`.

---

## A3. Inbound volume series, formalised

Inbound is defined as departures by travellers whose point of origin is not local: for the Northern Ireland airports, everyone other than a Northern Ireland resident identified by point-of-origin city; for Dublin, everyone other than an Irish resident. Absolute volumes, one-way departures, ND years for level comparison with 2013 and 2015 labelled as POO pulls.

**The series reproduces round one exactly**, which confirms the definition: Northern Ireland inbound of 1,348,403 in 2016 and 1,274,726 in 2025, Dublin 5,391,545 and 5,919,715, against round one's 1,348,403, 1,274,726, 5,391,546 and 5,919,715.

| Year | Pull | BFS | BHD | LDY | NI total | Dublin |
|---|---|---:|---:|---:|---:|---:|
| 2013 | POO | 549,521 | 457,039 | 62,390 | 1,068,950 | 4,472,638 |
| 2014 | ND | 566,729 | 470,751 | 70,037 | 1,107,518 | 4,322,851 |
| 2015 | POO | 621,528 | 491,037 | 61,448 | 1,174,015 | 5,202,210 |
| 2016 | ND | 796,383 | 486,100 | 65,918 | 1,348,403 | 5,391,545 |
| 2017 | ND | 868,221 | 479,113 | 42,760 | 1,390,094 | 5,811,100 |
| 2018 | ND | 879,261 | 481,822 | 44,380 | 1,405,464 | 6,302,420 |
| 2019 | ND | 895,314 | 472,093 | 45,685 | 1,413,093 | 6,322,098 |
| 2020 | - | gap | gap | gap | gap | gap |
| 2021 | ND | 722,714 | 233,888 | 27,106 | 983,708 | 2,953,280 |
| 2022 | ND | 757,147 | 279,988 | 28,312 | 1,065,449 | 4,425,925 |
| 2023 | ND | 934,130 | 368,947 | 28,269 | 1,331,348 | 5,381,308 |
| 2024 | ND | 942,789 | 380,082 | 34,338 | 1,357,210 | 5,895,680 |
| 2025 | ND | 889,193 | 346,363 | 39,170 | 1,274,726 | 5,919,715 |

### The Northern Ireland decline is Belfast City and Derry, not Belfast International

The aggregate figure conceals opposite movements. Across 2016 to 2025, Belfast International inbound **rose 11.7%**, from 796,383 to 889,193. Belfast City fell 28.7%, from 486,100 to 346,363, and Derry fell 40.6%. The headline 5.5% decline in Northern Ireland inbound is therefore a City and Derry story, and it runs alongside the same airport shift found in the resident catchment, where Belfast International took share from Belfast City throughout the period.

### The comparison is sensitive to the base year, and 2016 flatters the gap

Measured 2016 to 2025 the divergence is stark: Northern Ireland down 5.5%, Dublin up 9.8%. Measured from the 2019 peak both are down and the gap is much narrower: Northern Ireland down 9.8%, Dublin down 6.4%. Dublin grew strongly to 2019 and has not recovered that level, so a 2016 base captures Dublin's run-up while a 2019 base does not. The appraisal should state which base it uses and why, because the choice moves the apparent divergence from 15.3 points to 3.4.

### Source markets

Top markets by inbound volume, one-way departures.

| | 2016 | 2019 | 2025 |
|---|---|---|---|
| **NI** total | 1,348,284 | 1,412,971 | 1,274,613 |
| NI, Great Britain | 1,079,096 | 1,085,404 | 924,352 |
| NI, Spain | 92,977 | 116,902 | 149,329 |
| NI, United States | 16,899 | 16,856 | 13,313 |
| **Dublin** total | 5,391,440 | 6,321,994 | 5,919,623 |
| Dublin, Great Britain | 1,991,911 | 2,042,581 | 1,954,851 |
| Dublin, United States | 580,060 | 936,985 | 852,390 |
| Dublin, Germany | 385,504 | 487,065 | 416,775 |

Two movements carry the story. Northern Ireland's inbound decline is a Great Britain decline: down 154,744 or 14.3% since 2016, while Spain rose 60.6% and partly offset it. Great Britain has fallen from 80.0% to 72.5% of Northern Ireland inbound. Dublin's growth is North American: Great Britain inbound to Dublin is flat, down 1.9%, while United States inbound rose 46.9%.

**North America definition, settled.** Round one gives 2025 North America inbound as 14,988 for Northern Ireland and 963,504 for Dublin. A United States and Canada definition returns 14,852 and 957,034, short by 136 and 6,470. Mexican-resident inbound in 2025 is 132 and 6,450, which closes both gaps to 4 and 20 passengers, or rounding. **Round one's North America is United States, Canada and Mexico**, and that definition is adopted here.

On that basis: Northern Ireland 21,206 in 2016, 20,100 in 2019 and 14,984 in 2025, a fall of **29.3%**; Dublin 669,373, 1,055,559 and 963,484, a rise of **43.9%**. Both reproduce round one exactly. Dublin's North American inbound is 64 times Northern Ireland's.

**Files:** `a3_inbound_volumes.csv`, carrying every year, airport and point-of-origin country.

---

## A4. Journey purpose segmentation

The brief asks for a business, leisure and visiting-friends split estimated from cabin, booking class, advance purchase, day of week and length of stay. **Four of those five signals are not in this store, and the fifth does not work in this market.** What can be produced instead is a route-level business-leaning indicator, which is set out below with its limits. The passenger-level split the economic module needs has to come from survey sources.

### What the store holds, signal by signal

| Signal | Present | Usable here |
|---|---|---|
| Cabin class | Yes | No, see below |
| Booking class | No, only the cabin grouping | - |
| Advance purchase | No booking-date field | No |
| Day of week | No date field; the store is annual O&D | No |
| Length of stay | No date field | No |
| Fare | Yes, `avg_base_fare_usd` | Weakly, and only within a distance band |

### Cabin class cannot segment this market

Northern Ireland origin departures, 2025, by cabin:

| Cabin | Passengers | Share | Mean base fare USD |
|---|---:|---:|---:|
| Discount coach | 4,440,340 | 99.23% | 535 |
| Business | 25,022 | 0.56% | 1,397 |
| Premium coach | 8,387 | 0.19% | 1,173 |
| First | 1,037 | 0.02% | 1,841 |

The total of 4,474,786 reconciles with the Section 0 figure of 4,474,788 Northern Ireland airport departures.

Premium cabins account for 0.77% of all departures, and the reason is the carrier mix rather than the traveller mix. easyJet, Ryanair and Jet2 operate single-class aircraft, so a business traveller flying Belfast to Manchester is recorded in exactly the same cabin as a family flying to Malaga. Manchester carries 386,546 Northern Ireland passengers in 2025 and records 2 in a premium cabin, which is a statement about the aircraft, not about why people are travelling. Cabin therefore identifies purpose only on the handful of routes flown by full-service carriers.

### Fare needs a distance control, and the obvious control fails

Raw mean fare ranks routes by sector length: Tenerife at 3,077 km reads 196 dollars and Edinburgh at 229 km reads 66. Dividing by distance inverts the same artefact rather than removing it, because short sectors carry a higher fare per kilometre by construction. On fare per 1,000 km Glasgow tops the network at 449 dollars, purely for being the shortest sector at 174 km. Neither raw fare nor fare per kilometre isolates purpose.

Comparing routes **within** a distance band does work. The London airports sit between 493 and 553 km and can be read against each other:

| Destination | Distance km | Mean base fare USD | Premium share |
|---|---:|---:|---:|
| Heathrow | 519 | 173 | 0.28% |
| London City | 526 | 147 | 2.24% |
| Luton | 493 | 108 | 0.00% |
| Gatwick | 553 | 119 | 0.00% |
| Southampton | 515 | 97 | 0.00% |
| Stansted | 529 | 95 | 0.00% |

Heathrow and London City command a clear fare premium over Gatwick, Luton and Stansted at the same sector length, and they are also the only two carrying any premium cabin. Two independent signals agree, which is what makes the indicator worth having.

### The route-level business-leaning indicator

On the combined evidence of premium share and within-band fare, the business-leaning routes from Northern Ireland are Amsterdam (9.27% premium, KLM), London City (2.24%), Geneva (0.96%), Budapest (0.81%) and Heathrow (0.28%). The leisure-leaning routes are the Spanish, Portuguese, Turkish and Canary Islands destinations together with Stansted, Luton and East Midlands, all effectively at zero premium and priced at or below the network average for their distance.

This is a route characteristic, not a passenger segmentation. It detects only business travel that buys a premium cabin or pays a fare premium, and on a single-class route sold at one price it detects nothing at all. It should not be converted into passenger counts by purpose.

### What must come from survey

The business, leisure and visiting-friends split has to be supplied externally, and both sources exist. The CSO Passenger Survey gives the Ireland side directly: for 2025, 40% of overnight foreign visitors travelled for holiday, leisure or recreation, 35% to visit friends and relatives and 15% for business, with 10% other. NISRA publishes the Northern Ireland equivalents, and its external overnight visitor tables are already flagged as outstanding at B3 item 2, which this task now depends on.

The practical consequence for the appraisal: journey purpose enters the model as a survey-derived proportion applied to Sabre volumes, not as a segmentation measured within the traffic data. That should be stated in the method rather than implied, because the two are not equivalent and the survey proportions carry their own sampling error.

**Files:** `a4_cabin_fare_by_destination.csv`, `a4_business_intensity.csv`.

---

## A5. Route economics for Paris and Barcelona

Run through the QSI tool's aircraft economics module (`aircraft_economics.py`), which carries validated FSC, LCC and ULCC cost structures including the A319, A320 and 737-800.

**First, a premise correction carried from A1.** The brief describes Paris and Barcelona as "the two viable candidates" for route creation. Neither is unserved. easyJet operates Belfast International to Paris CDG roughly daily, carrying 60,498 nonstop Northern Ireland passengers in 2025, and also operates Barcelona, thinly, with 11,904 nonstop. So this section reads as the economics of adding or upgrading frequency on partly-served routes, not of creating new ones.

### Route inputs, measured

| Route | Nonstop pax 2025 | Base fare USD | Total fare USD | Distance km | Equipment flown |
|---|---:|---:|---:|---:|---|
| BFS-CDG | 60,498 | 110 | 131 | 869 | A319 (156 seats), A320 (186) |
| BFS-BCN | 11,904 | 174 | 184 | 1,606 | A319 (156) |

Base fare is the carrier's fare excluding tax and is the correct revenue basis. Block time is modelled as 30 minutes fixed plus distance at 750 km/h, since the OAG elapsed-time field is empty in the sampled weeks. Load factors are declared assumptions, 90% for the LCC cases and 94% for the ULCC cases, and are consistent with the observed traffic against roughly daily service.

### The contribution figures are not usable yet, and the reason is airport charges

The model returns profit per turn of 11,288 dollars for an A320 on CDG and 24,701 for a 737-800 on Barcelona, at margins of 26% to 40%. **Those margins are not credible for European short-haul and should not be quoted.** The cause is identified and fixable.

The module's airport table holds charges for five airports only: EDI, GOA, JFK, LCY and PUJ. Belfast, Paris CDG and Barcelona are not among them, so Edinburgh was used as a declared proxy at both ends of both routes. That understates cost three ways. Charles de Gaulle and Barcelona are major hubs with charges well above a UK regional airport. The Edinburgh record carries ground handling at zero, so no handling cost enters the turn at all. And enroute navigation charges compute to zero, when Eurocontrol charges on these sectors are material.

The contribution-shortfall test therefore remains open, exactly as it did in round one, and for the same reason: sector costs are not yet sourced. What is needed is a charging schedule for BFS, CDG and BCN, either from the published airport schedules or from RDC, plus Eurocontrol unit rates. With those the module will produce a defensible answer, since its fuel, crew, maintenance and ownership legs are already validated.

### The duty effect, which is robust to the cost gap

Air Passenger Duty is charged on the departure from the United Kingdom only, not on the return sector. An initial run applied it to both legs of the turn and roughly doubled the benefit; the figures below are corrected to one direction, and net the 5% sales and 5% overhead that scale with revenue. Sterling is converted at 1.30 dollars, a declared assumption to be confirmed.

| Route | Aircraft | Type | Outbound pax | Duty capture at £13 | At £15 |
|---|---|---|---:|---:|---:|
| BFS-CDG | A320 | LCC | 162 | $2,464 | $2,843 |
| BFS-CDG | A319 | LCC | 130 | $1,971 | $2,274 |
| BFS-CDG | B738 | ULCC | 178 | $2,702 | $3,118 |
| BFS-BCN | A319 | LCC | 130 | $1,971 | $2,274 |
| BFS-BCN | B738 | ULCC | 178 | $2,702 | $3,118 |

**The ratio that does not depend on the cost model.** Band A duty of £13 equals 15.4% of the achievable one-way base fare on Paris, where the fare is 110 dollars or circa £85, and 9.7% on Barcelona at 174 dollars or circa £134. That is the size of the prize either way it falls: if the airline captures the duty it is a margin improvement of that order, and if the passenger captures it, it is a price reduction of that order available to stimulate demand. On a short, cheap sector the duty is proportionally largest, which is why the Paris-type route is more duty-sensitive than the longer leisure sectors.

### What could not be produced

- Seasonality. The Sabre store is annual O&D with no month or date field, so no seasonal profile can be derived from it. The OAG store's two sampled weeks, late May and late October, give only a crude summer against winter capacity indication, and that improves once the full-year schedules load.
- The contribution position with and without duty, in absolute terms, pending the airport charges above.

**Files:** `a5_route_pl.csv` (modelled, carrying the charge caveat), `a5_duty_capture.csv`.

---

## A5b. Aircraft gauge sensitivity on the route viability test

Required passengers are annual two-way seats multiplied by the breakeven load factor, where annual two-way seats are gauge times weekly frequency times 52 times two directions. Because A5 established that the absolute cost position is not yet reliable, the test is run across a range of breakeven load factors rather than at a single modelled one. A breakeven of 75% reproduces round one's figure of roughly 25,700 for a 110-seat aircraft at three times weekly, so that column is directly comparable with the earlier work.

Two-way passengers required:

| Gauge | Weekly | Annual two-way seats | At 50% BE | At 65% | At 75% | At 85% |
|---|---:|---:|---:|---:|---:|---:|
| 110 | 3 | 34,320 | 17,160 | 22,308 | 25,740 | 29,172 |
| 110 | 2 | 22,880 | 11,440 | 14,872 | 17,160 | 19,448 |
| 130 | 3 | 40,560 | 20,280 | 26,364 | 30,420 | 34,476 |
| 130 | 2 | 27,040 | 13,520 | 17,576 | 20,280 | 22,984 |
| 180 | 3 | 56,160 | 28,080 | 36,504 | 42,120 | 47,736 |
| 180 | 2 | 37,440 | 18,720 | 24,336 | 28,080 | 31,824 |

**Smaller gauge does not bring any additional destination above the line.** Taking the most favourable combination in the whole grid, 110 seats at twice weekly on a 75% breakeven, requiring 17,160 two-way passengers:

| Candidate | Captured demand | Required | Position |
|---|---:|---:|---|
| Paris | 73,824 | 17,160 | clears, but already served daily by easyJet, see A1 |
| Barcelona | 28,773 | 17,160 | clears |
| Lisbon | 8,582 | 17,160 | short by 8,578; needs 2.0 times the captured demand |
| Rome | 5,722 | 17,160 | short by 11,438; needs 3.0 times |
| Madrid | 5,713 | 17,160 | short by 11,447; needs 3.0 times |

The gap is not a near miss that a smaller aircraft closes. Lisbon needs its captured demand to double and Rome and Madrid need theirs to treble, at the single most generous gauge, frequency and breakeven combination tested. Even at an implausible 50% breakeven with 110 seats twice weekly, requiring 11,440, Lisbon at 8,582 still fails.

The finding is stronger than the arithmetic suggests, for the reason the brief anticipates. Capture is a function of schedule quality, so dropping from three times weekly to twice reduces capture as well as the requirement. This test holds captured demand constant at its three-times-weekly level while lowering the requirement to the twice-weekly figure, which flatters the smaller-gauge case. The candidates still fail. The airports' argument that the absence of a 100 to 130 seat type is itself the constraint is therefore not supported on these demand figures.

**Files:** `a5b_gauge_sensitivity.csv`.

---

## A6. Emissions by route

CO2 per departing passenger is derived from the aircraft actually flown on each route, from OAG, and the validated per-block-hour fuel burn in the QSI economics module, at 3.16 kg CO2 per kg of fuel and a declared 88% load factor. Block time is modelled as 30 minutes plus distance at 750 km/h. The OAG sampled weeks are a limitation on volumes but not on this calculation, because what is taken from OAG is the fleet mix on each route, which is a rate rather than a total; annual passenger weights come from Sabre, which is complete.

Coverage is 61 routes and 4,230,991 of 4,474,787 Northern Ireland departures, or 94.6%.

| Destination | km | NI pax 2025 | kg CO2 per departing pax |
|---|---:|---:|---:|
| Manchester | 295 | 386,546 | 41 |
| Gatwick | 555 | 337,101 | 65 |
| Edinburgh | 231 | 310,186 | 37 |
| Birmingham | 364 | 275,385 | 44 |
| Stansted | 526 | 253,624 | 61 |
| Heathrow | 502 | 180,654 | 54 |
| Alicante | 1,868 | 136,819 | 149 |
| Malaga | 2,002 | 129,157 | 157 |
| Tenerife | 3,074 | 98,658 | 225 |
| Lanzarote | 2,919 | 80,665 | 215 |

**Network average, passenger-weighted: 83.9 kg, or 0.0839 tonnes CO2 per departing passenger.**

**This is 23.7% below the provisional 0.11 tonnes currently in the model.** Given that B2 identifies the carbon treatment as the parameter that decides the appraisal, a 24% overstatement of emissions per passenger is material to the result and should be corrected before any appraisal run. The reason for the gap is structural: two thirds of Northern Ireland departures are short domestic sectors at 33 to 65 kg per passenger, and they pull the weighted average well below a figure derived from a typical short-haul international sector.

Caveats to carry: the 88% load factor is declared, not measured; non-CO2 effects including contrails and NOx are excluded, and if the appraisal applies a radiative forcing multiplier it must be applied on top of this figure rather than assumed within it; and 5.4% of departures sit on routes where the OAG aircraft could not be matched.

### UK ETS scope split

| Scope | 2025 departures | Share |
|---|---:|---:|
| UK domestic | 2,957,793 | 66.1% |
| UK to EEA | 1,266,425 | 28.3% |
| Other | 250,568 | 5.6% |

**94.4% of Northern Ireland departures fall within UK ETS scope**, which covers UK domestic and UK to EEA flights. That is high enough that the double-counting question B2 raises, where a traded-sector instrument is already in force over the same emissions, applies to almost the whole of the traffic rather than to a portion of it.

**Files:** `a6_emissions_by_route.csv`, `a6_ets_scope_split.csv`.

---

## A7. Domestic and Band A departure split

Banding follows the statutory basis, which is the distance from London to the destination country's capital, not the flown sector. That distinction matters here: the Canary Islands are Band A because Madrid is inside 2,000 miles, although the sector from Belfast is nearly 3,000 km. Classifying on sector distance would have wrongly placed roughly 200,000 Canaries passengers in Band B.

| Year | Pull | Domestic | Band A | Band B/C | Total | Domestic share |
|---|---|---:|---:|---:|---:|---:|
| 2016 | ND | 3,016,235 | 903,277 | 102,914 | 4,022,428 | 75.0% |
| 2019 | ND | 3,133,398 | 1,149,589 | 100,453 | 4,383,440 | 71.5% |
| 2023 | ND | 2,813,700 | 1,059,421 | 113,544 | 3,986,666 | 70.6% |
| 2024 | ND | 3,086,926 | 1,350,551 | 91,996 | 4,529,475 | 68.2% |
| 2025 | ND | 2,957,793 | 1,417,875 | 99,118 | 4,474,787 | 66.1% |

The 2025 total reconciles with the Section 0 figure of 4,474,788. The network has internationalised steadily: the domestic share has fallen from 75.0% in 2016 to 66.1% in 2025, with Band A rising from 22.5% to 31.7%.

Band B and C traffic of 99,118 is not a long-haul network from Belfast, which barely exists. It is connecting traffic on single tickets to long-haul destinations, and it is correctly classified here because the connected-flights rule charges the whole journey at the final destination band. That also means it is charged at circa £94 rather than £7, which is why it carries weight out of proportion to its 2.2% volume share.

### The blended rate, computed rather than assumed

At 2025-26 statutory reduced rates of £7 domestic, £13 Band A and circa £94 Band B:

| Band | 2025 departures | Rate | Duty |
|---|---:|---:|---:|
| Domestic | 2,957,793 | £7 | £20.7m |
| Band A | 1,417,875 | £13 | £18.4m |
| Band B/C | 99,118 | circa £94 | £9.3m |
| **Total** | **4,474,787** | **blended £10.83** | **£48.5m** |

**The model's £11 blended assumption is close to right**, overstating by roughly 1.6%. The bottom-up duty yield on 2025 volumes at 2025-26 rates is **circa £48.5m**, which is the figure B1 should reconcile against HMRC receipts. The provisional £51m in the model sits between this and what 2026-27 rates would produce, since Band A rises to £15 from April 2026.

Two refinements for B1. Premium cabins pay the standard rate rather than the reduced rate, and at 0.77% of departures that adds roughly £0.5m, not material but not zero. And the Band B/C rate used here is a single economy figure; the actual mix across Bands B and C, and across reduced and standard rates, should be resolved against the HMRC schedule.

**Files:** `a7_band_split.csv`.

---

## Queries and method

All queries read-only against the stores named at the head, DuckDB memory capped at 5 to 6 GB with a named temp directory and 4 threads. Reported aggregates are passenger sums, not row counts. North America is defined as country codes US and CA from the airport mapping file. Great Britain is country code GB in that file, which covers the United Kingdom including Northern Ireland. Nonstop is tested as `connecting_airport1` null or empty. Single-ticket connection at Dublin is tested as `connecting_airport1 = 'DUB'`.

## Sources

- Sabre GDD store and OAG store as above.
- [Population and Migration Estimates, April 2025 - CSO Ireland](https://www.cso.ie/en/releasesandpublications/ep/p-pme/populationandmigrationestimatesapril2025/keyfindings/)
- [Provisional population estimate for the UK: mid-2025 - ONS](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/bulletins/provisionalpopulationestimatefortheuk/mid2025)
- APD rates: Band A £13 to March 2026 and £15 from April 2026, and long-haul economy circa £94, as set out in the round two brief Section 0 and its HMRC source.
- [Air Passenger Duty and connected flights - GOV.UK](https://www.gov.uk/guidance/air-passenger-duty-and-connected-flights), for the 24-hour rule, the same-ticket or conjunction-ticket requirement, and the charging of connected journeys at the final destination band.
- [Inbound Tourism December 2025 - CSO Ireland](https://www.cso.ie/en/releasesandpublications/ep/p-ibt/inboundtourismdecember2025/), published 29 January 2026, for full-year Great Britain visitor numbers (Table 2), the departing-passenger categories including transfers and Northern Ireland residents (Table 1), and the survey methodology and exclusions.
- [Rates for Air Passenger Duty - GOV.UK](https://www.gov.uk/guidance/rates-and-allowances-for-air-passenger-duty) and [APD banding reforms from 1 April 2023](https://www.gov.uk/government/publications/air-passenger-duty-banding-reforms-from-april-2023/air-passenger-duty-banding-reforms-and-rates-from-1-april-2023-to-31-march-2024), for the domestic band (£6.50 from April 2023, £7 from April 2024 and held for 2025-26), Band A, and the four-band structure introduced in April 2023.
- QSI tool aircraft economics module (`aircraft_economics.py`), for validated FSC, LCC and ULCC cost structures and per-block-hour fuel burn by type.
