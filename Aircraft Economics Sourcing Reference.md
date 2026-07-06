# Aircraft Operating Cost & Airline Unit Economics — Sourcing Reference

Avia Solutions | prepared 27 June 2026 | for the route-profitability (aircraft economics) module

A citable reference for the public sources of aircraft operating cost and airline unit economics, with figures, vintage, access (free vs paywalled) and reliability flags. Use it to (a) cite cost assumptions in client deliverables and (b) calibrate the tool's per-aircraft cost rates. Every figure carries its source so it can be independently checked.

---

## 1. Operating-cost databases

### Free and citable in client work

**US DOT Form 41, Schedule P-5.2, via BTS TranStats.** Aircraft operating expense by aircraft type for US Part 121 carriers, split variable (fuel, maintenance, crew) and fixed (depreciation, rentals, insurance); combine with T-100/P-52 block hours for a per-block-hour figure. Free, no login (TranStats DB_ID=135, https://www.transtats.bts.gov/Tables.asp?DB_ID=135). Quarterly, ~6-9 month lag, history to ~1990. The de facto industry standard; caveat: self-reported, US carriers only, some allocation noise.

**FAA, "Economic Values for FAA Investment and Regulatory Decisions," Section 4 — Aircraft Operating Costs.** Pre-computes Form 41 cost per block hour by aircraft size category, so you can cite ready-made figures. Free PDF, year-ending June 2023 (https://www.faa.gov/regulations_policies/policy_guidance/benefit_cost/econ-value-section-4-op-costs.pdf). Selected totals per block hour: narrowbody <165k lb fuel $2,322 / maint $1,004 / crew $1,336 / total ≈ $5,250; narrowbody ≥165k lb ≈ $5,650; twin-aisle widebody ≈ $10,200-11,300; regional jet 61-99 seats fuel $1,480 / maint $667 / crew $904 / total $3,329. Best single free source for current category-level per-block-hour cost.

**MIT Airline Data Project.** Form 41 processed into CASM, yield, load factor, utilisation by US airline over ~20 years (http://web.mit.edu/airlinedata/www/). Free. Frozen at CY2019 (last update June 2020) — use for method, structure and history, not current levels.

### Authoritative, partly paywalled

**ICAO iCADS — "Unit Average Cost by Aircraft Type."** Average flight-operations, maintenance/overhaul and depreciation unit cost for 190+ aircraft types, annually from 1998 (https://data.icao.int/iCADS/Product/View/88). Summary tables free; detailed data a paid ICAO product. The global-coverage complement to US-only Form 41.

**IATA economics / Jet Fuel Price Monitor.** Industry cost structure and fuel price; mostly free (https://www.iata.org/en/publications/economics/fuel-monitor/). High for fuel and cost-share context, not aircraft-type granularity.

**Aircraft Commerce — Owner's & Operator's Guides and maintenance analyses.** The most granular public bottom-up maintenance build-ups by type (man-hours, shop-visit costs), expressed per flight hour and per flight cycle. Subscription ~£197/yr; some older PDFs openly hosted. Best for cost *structure* and the maintenance flight-hour-to-cycle (FH:FC) sensitivity; escalate dated dollar levels for inflation. Example (Issue 30, 2003): A330 total maintenance ≈ $978/FH at 3.0 FH:FC (medium-haul) versus $664/FH at 7.0 FH:FC (long-haul) — maintenance cost per hour falls sharply as sectors lengthen.

### Commercial subscription — cite the provider, not raw data

**Cirium (Diio) and OAG** — schedules/capacity (ASK) and O&D traffic/fares, the backbone for converting per-hour cost into route P&L. Paid; industry standard.

**RDC Aviation — AirportCharges and Apex.** Landing/passenger/navigation fees by airport, plus a route operating-cost and profitability dataset. Paid. Directly relevant to airport client work and to the charges input layer of the model (see Section 6).

**Leasing/appraisers — Cirium Ascend, IBA, Avitas.** Aircraft values and monthly lease rates, i.e. the ownership/capital leg. IBA summaries free, full data paid. Indicative new-aircraft figures (IBA, 2024): A320neo and 737 MAX 8 value ≈ $55m, lease ≈ $400k/month; A321neo ≈ $64m, ≈ $460k/month; 787-9 ≈ $1.0m/month; A330-900neo ≈ $800-900k/month; mid-life 737-800/A320ceo ≈ $230-250k/month.

---

## 2. Operating cost per block hour, by aircraft type

### Anchor table — US DOT Form 41 (Belobaba, MIT), data year 2013

Source: Peter Belobaba, MIT, "Airline Operating Costs" Module 12, 2016, using Form 41 2013 system data (http://aviation.itu.edu.tr/img/aviation/datafiles/Lecture%20Notes/Network%20Fleet%20Schedule%20Planning%202015-2016/Lecture%20Notes/Module%2012%20-%20Operating%20Costs.pdf). Figures are Aircraft Operating Cost (crew + fuel + maintenance + ownership), i.e. the direct leg only; full cost is roughly double once ground handling (~30%) and system overhead (~20%) are added.

| Type | Avg seats | AOC / block hour | Avg stage (mi) |
|---|---|---|---|
| E190 | 100 | $3,612 | 599 |
| 737-700 | 139 | $4,358 | 762 |
| A320ceo | 150 | $4,479 | 1,181 |
| 757-200 | 177 | $5,839 | 1,523 |
| A330-200 | 272 | $8,795 | 3,645 |
| 747-400 | 375 | $15,153 | 4,861 |

A320 component split (2013, $/block hour): crew $652, fuel $2,385, maintenance $716, ownership $726, total $4,567. Same type across carriers ran $4,053 (Spirit) to $4,903 (United) — proof that a single per-type figure carries a 2-17% airline spread.

### Recent per-flight-hour cross-check — EUROCONTROL / IATA ACMG (FY2019, USD-2022)

Source: EUROCONTROL "Standard Inputs for Economic Analyses" v10.0.1, Table 12.1 (https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/aircraft_operating_costs.html). Per flight hour, all-in (fuel, crew, ownership, charges, handling, maintenance): 737NG $4,337; A320 family $4,829; 757 $5,357; 767 $6,675; A330 $7,827; 787 $7,184; 777 $9,507; E190 $4,097; Dash 8 $1,921.

### Fuel burn by type (the leg to price separately)

Cruise/block burn, from published OEM/Aircraft Commerce data (compiled at https://en.wikipedia.org/wiki/Fuel_economy_in_aircraft and Aircraft Commerce flight-ops issues): A320neo ~2,200-2,400 kg/hr; A320ceo ~2,500; 737 MAX 8 ~2,000-2,300; 737-800 ~2,400-2,500; A321neo ~2,400-2,600; A321XLR ~2,700-3,000 (no clean independent data published yet — use A321LR plus weight delta); E190 ~1,100; ATR72 ~620-760; Q400 ~610-700; A330-300 ~6,000; A330-900neo ~5,400; 787-8 ~5,000; 787-9 ~5,400; A350-900 ~5,800; 777-300ER ~6,800-7,100. Re-price to the current fuel scenario (Section 5). New-generation types (neo/MAX/E2) burn ~15-20% less per seat than the prior generation.

---

## 3. CASK (unit cost) by airline and business model

Each carrier's own published figure, by its own definition — **not directly comparable as published** (different currencies, miles vs km, and "ex-fuel" definitions). Convert to one unit and stage-length-adjust (Section 5) before ranking.

**Low-cost.** Wizz Air F26 (yr to Mar 2026): total 4.35 €c/ASK, ex-fuel 3.02 €c/ASK, stage 1,749 km (https://s204.q4cdn.com/169340705/files/doc_news/Final-Results-2026.pdf). easyJet FY25 (yr to Sep 2025): total 6.14 p/ASK, ex-fuel 4.46 p/ASK, cost per seat £79.34, sector 1,293 km (https://s203.q4cdn.com/522538739/files/doc_financials/2025/q4/FY25-RNS.pdf). Ryanair publishes no CASK — only cost per passenger (~€62/pax FY26; ex-fuel ~€36/pax on its own competitive slide).

**Full-service Europe (FY2024).** IAG: group total 8.06 €c/ASK, non-fuel 5.84 €c/ASK; BA non-fuel 4.96 p/ASK (https://www.iairgroup.com/media/tbshppll/iag-results-presentation-fy24-final.pdf). Lufthansa Group Passenger Airlines: ex-fuel 6.6 €c/ASK, RASK 9.2 €c (segment only, excludes fuel/ETS/FX) (https://report.lufthansagroup.com/ecomaXL/files/Ergebnispraesentation_2024_EN.pdf). Air France-KLM: net cost 8.24 €c/ASK — a net metric deducting fuel, ETS and non-passenger revenue, so not a like-for-like ex-fuel CASK; ex-fuel given only as +4.5% YoY.

**US majors (FY2024, US cents per ASM — divide by 1.609 for per-ASK).** Delta total 19.30¢, CASM-ex 13.54¢; United total 16.70¢, ex 12.58¢, stage 1,490 mi; American total 17.61¢, ex 13.50¢, stage 842 mi. American's much shorter stage mechanically inflates its per-ASM cost — the textbook reason to stage-length-adjust.

**Long-haul and regional bookends.** Singapore Airlines FY24/25: total 9.1 S¢/ASK, ex-fuel 6.0 S¢/ASK, avg trip ~4,533 km. Within one group, Norwegian mainline 0.73 NOK/ASK (ex-fuel 0.50) at 1,292 km sectors versus regional Widerøe ~2.9 NOK/ASK at 276 km — a ~4x gap that is almost entirely stage length, the single cleanest illustration of the effect.

---

## 4. RASK / unit revenue and yield

Same comparability warnings as CASK. easyJet FY24 RASK 6.65 p/ASK. Wizz F24 total RASK 4.17 €c/ASK (ticket 2.30, ancillary 1.86). Air France-KLM FY24 RASK 8.90 €c/ASK; IAG passenger RASK ≈ 8.2 €c/ASK. US FY2024 (¢/ASM): Delta TRASM 21.37, PRASM 17.65; United TRASM 17.88; American TRASM 18.51. Singapore Airlines passenger yield 10.3 S¢/RPK. Industry (IATA 2024): record 83.5% load factor, real average return fare ~$252. Ryanair reports no RASK (per-passenger only; ancillary ~34% of revenue). Regional carriers under capacity-purchase agreements (e.g. SkyWest) report a contracted fee, not market RASK, and are not comparable.

---

## 5. Methodology

**Cost taxonomy (ICAO Form EF, free, https://www.icao.int/sites/default/files/sp-files/sustainability/Documents/STA-Excel-Forms/English/Form_EF-Instructions_en.pdf).** Direct operating cost = flight operations (crew, fuel, insurance, equipment rentals), maintenance, flight-equipment depreciation, and (ICAO only) user charges; indirect = station/ground handling, passenger services, ticketing & sales, general & admin. Two traps: cabin crew sits in passenger services, not flight operations; and operating-lease cost and owned-aircraft depreciation are different lines depending on how the aircraft is financed (why "cash operating cost" and EBITDAR exist to normalise owned versus leased fleets). Note US DOT Form 41 excludes user charges from DOC whereas ICAO includes them — reconcile before any cross-source comparison.

**Fuel.** Cost = burn × jet fuel price on a matched unit. Constants (ATAG): 1 barrel = 42 US gal; density ~0.8 kg/L; ≈ 3.03 kg per US gallon. Price (IATA Jet Fuel Price Monitor, free): spot ~$119/bbl late June 2026; IATA FY2026 forecast average ~$152/bbl (do not conflate the weekly spot with the annual forecast). Representative narrowbody en-route burn ≈ 2,406 kg/block hour (EUROCONTROL).

**Ownership.** Monthly lease ÷ (block hours/day × 30.4). At Cirium global utilisation (narrowbody ~9.3 block hr/day ≈ 3,400/yr; widebody ~13.6 ≈ 4,950/yr), a $400k/month A320neo ≈ $1,300-1,600/block hour. Utilisation is the key denominator — low utilisation inflates per-hour ownership and maintenance.

**Maintenance.** Industry blended $1,522/flight hour FY2024 (IATA MCX, public PDF). By type, ~$980-1,050/FH for an A320, ~$1,130-1,190 for an A321 (Aircraft Commerce, 2006 — escalate), ~$1,710-2,100 for a 777-200ER. Maintenance per hour is route-structure dependent via the FH:FC ratio, not a flat per-aircraft constant.

**Stage-length adjustment (the key comparison rule).** Adjusted CASM = CASM × √(stage length / 1,000 miles) (Virgin America SEC filing citing the MIT formula). Much cost is per-departure (landing/handling, one turnaround, takeoff fuel, ownership over more ASK), so unit cost falls with stage length by geometry; without normalising, a long-haul carrier looks artificially efficient. In the Virgin America worked example the adjustment reversed the apparent legacy-versus-LCC ranking.

---

## 6. How this calibrates the tool

The tool's `aircraft_economics.py` holds per-block-hour rates by type. Recommended calibration:

1. Anchor the per-type cost *structure and relativities* on the Belobaba 2013 Form 41 table (Section 2), scale to current levels using the FAA year-ending-2023 category totals, and keep the 2013 per-type ratios. This replaces benchmark estimates with citable figures.
2. Supply the fuel leg independently as burn × current fuel price (Section 5), so fuel re-prices cleanly with the scenario.
3. Take ownership from lease rates ÷ utilisation, and maintenance with the FH:FC sensitivity rather than a flat per-hour constant.
4. Airport charges and incentives are a per-route input layer, not a stored database: pull both airports' charges from RDC AirportCharges at build time, enter them, and model the home airport's incentives (discounted/waived charges, marketing support) as an explicit line. The far end's charges are the known weak point and should be flagged in any output.

**Caveats to carry into client work.** Form 41 and MIT are US-carrier-only and MIT is frozen at 2019; Belobaba per-type is 2013 (re-price fuel and inflate labour/ownership); Aircraft Commerce dollar levels are dated; OEM fuel figures are vendor-biased; the A321XLR has no clean independent published cost data yet; and CASK/RASK figures are not comparable across carriers without unit conversion and stage-length adjustment.
