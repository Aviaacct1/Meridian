# Knowledge Folder Asset Map for the QSI / Economics Tool

Author: Avia Solutions
Date: 26 June 2026
Scope: a deliberate sweep of `/Shared/Company Data/02 Knowledge` (25 years of material) for data and models that would enhance the tool. This replaces the earlier targeted-only searches. Paths are exact; entry IDs held in the build notes.

## Headline

The folder holds, in usable form, most of what the aircraft economics module currently estimates from public benchmarks. Two classes of asset matter most: current OEM appraiser lease rates and values (the ownership leg), and current maintenance reserve data (the maintenance leg). Both refresh on a known cadence (Airbus twice a year, Boeing annually). There is also a live in-house demand model that sits alongside QSI, and an in-house FAA operating-cost extract.

## Tier 1 - wire in first (current, machine-readable, fills a real gap)

### Aircraft ownership leg: OEM appraiser lease rates and values
`2 Industry Reports/d International Industry Bodies/Airbus/Briefings/` holds a dated A&I Forum series: Nov 2016, Nov 2017, Dec 2021, Appraiser Dec 2022, Dec 2023, April 2024, Nov 2024, Dec 2025, April 2026. Each carries an appraiser value and lease-rate deck.
- `Airbus Presentation - Dec 2025/08 - 2025-12 - Airbus Value & Lease Rate Trends.pdf` - five-appraiser market lease rate opinions, full-life and half-life, by type and age (A320ceo/neo, A321neo, A330-200/300/900, A350-900/1000). Current.
- `.../07 - 2025-12 - Leasing & Secondary Market Perspectives.pdf` - placement, availability, extension behaviour.
- Boeing equivalent: `.../Boeing/Conference Mar 2025/Aircraft Financing Outlook 2025 - European Consultant Conference.pdf` - new aircraft market values and lease rates ($M and $K/month) for 787-9, 777F and others.
Why it matters: the module's ownership $/block-hour is currently a benchmark estimate. These give current appraiser lease rates by type and age, which convert directly to an ownership rate. Refreshed twice yearly by Airbus, so a once-a-year update keeps the tool current with near-zero effort.

### Maintenance leg: Airbus maintenance reserves database (with live Excel tool)
`.../Airbus/Briefings/Airbus Presentation - Nov 2024/2024 - 2025_Maintenance Reserves Booklet_v2.pdf` plus `2024 - 2025_Maintenance Reserves booklet_Excel tool_v2.1.xlsm`.
The xlsm is structured by type (A220, A320 family, A330, A350) with per-engine-flight-cycle, per-APU-hour and landing-gear reserve logic, and a monthly reserve output. Indicative, but current and Airbus-sourced.
Why it matters: replaces the Belobaba-era maintenance anchor with current per-type reserves, and the Excel is directly ingestible rather than needing extraction from prose.

### In-house demand model alongside QSI
`0 Avia Databases/Avia - Automated Traffic Forecasting File/` - the live macro workbook (Nick Oldrini, last saved April 2026: `Copy of Traffic forecasting file_2021_..._Feb2024 GDP (003) (NO - WIP).xlsm`).
Why it matters: this is the demand-forecasting companion to QSI. Worth reading its method before we finalise how the tool moves from QSI fair-share to absolute passenger numbers; we should not reinvent what Nick already maintains.

## Tier 2 - strong cross-checks and per-type granularity

### In-house FAA operating-cost extract
`0 Avia Databases/Avia - Opex database (draft)/FAA US Opex Database 2002-2012 draft 09072013.xlsx` (three dated drafts).
Avia's own pull of US Form 41 operating cost by year. A direct, in-house cross-check for the cost rates already in the module, and the basis for a per-type $/block-hour table independent of Belobaba.

### Aircraft Commerce per-type maintenance cost analyses
`5 Aviation general/Aircraft Statistics/Aircraft Commerce/` - per-type airframe, engine, APU, landing-gear and thrust-reverser cost-per-flight-hour studies (A340, B747-400, CRJ-100/200, narrowbody freighter, plus General Info components).
Granular maintenance build-up by type to firm individual lines where a type matters to a study.

### Operating cost per block hour, benchmark
`5 Aviation general/Aircraft Statistics/_Various/US Airlines Aircraft Operating Costs 2015.pdf` (total vs variable $/BH) and `Airline Operating Costs 2014.pdf` (A320 crew/fuel $/BH by year, 2005/2007/2012). Clean datums for sanity-checking the narrowbody anchor.

### GECAS maintenance reserve quotes
`9 Cost Model/GECAS/Maintenance Reserves Quotes (ADF CE) 12Apr13.xlsx` - per-flight reserve by flight duration (Antonio Di Francesco). In-house, ties the maintenance leg to GECAS-era leasing practice.

### Airbus XLR economics
`.../Airbus/Briefings/Airbus Presentation - April 2024/05 2024-04 Airbus A & I Forum - XLR Economics.pdf` - Airbus's own DOC-per-trip deltas vs datum (airframe maintenance -29%/FH; total maintenance +72%, ownership +47%, total DOC per trip +64% against the reference). Directly useful to the Genoa XLR argument as an OEM cross-check on our capacity-fill case.

## Tier 3 - lease-rate-factor and finance reference (ownership conversion, context)
`5 Aviation general/Aircraft Leasing and Aviation Finance/` (71 items) and `5 Aviation general/Ishka/`:
- `IBA - Lease Rate Digest Sample.pdf` - appraised lease rates by type.
- `SMBC - Aircraft Lease Rates push pull factors - Mar 2024.pdf`; `SMBC - Aircraft as an Investment - Jan 2024.pdf` - CMLR definition and drivers.
- `Ishka - Aircraft Pricing benchmarking Q2 2024.pdf` - lease rate factors circa 0.65-0.68%.
- `AviaAM - Leasing Midlife Aircraft 2017.pdf` - LRF bands by age (new 0.7-0.8%, used 0.8-1.5%).
These give the lease-rate-factor method to turn an aircraft value into a monthly lease and then an ownership $/block-hour, and to age-adjust it.

## Also noted (not core, but relevant)
- `22 Avia Credentials Library/Claude Knowledge/` - markdown knowledge files (e.g. `Avia_Project_Credentials_MRO_GSE.md`, April 2026) describing Avia's own cost-per-flight-hour and ownership/lease modelling approach. Worth reading for house method.
- `5 Aviation general/Aircraft Statistics/Aircraft Database/` - consolidated type specifications (not yet opened).
- `5 Aviation general/Aircraft Statistics/EY Aircraft Performance Data/` and `Aircraft Performance/` - performance and fuel-burn data to cross-check PaceLab.
- `2 Industry Reports/e Analyst Reports/Aviation generic/aviation demand forecasting survey of methods.pdf` - method reference for the demand side.
- `0 Avia Databases/` also holds airport financial databases (European, Italian, US, Leigh Fisher) and an Apt Infrastructure / Infrastructure Cost database - relevant to the airport charges input layer, not aircraft economics.

## Recommended sequence
1. Ingest the Airbus maintenance reserves Excel tool to replace the module's maintenance anchor per type.
2. Build the ownership leg from current OEM appraiser lease rates (Airbus Dec 2025 + Boeing Mar 2025), age-adjusted via the IBA/Ishka lease-rate-factor method. Declared, dated, overridable, consistent with the input-layer principle.
3. Cross-check the full per-type cost table against the in-house FAA Opex extract and the 2014/2015 $/BH benchmarks; record variance.
4. Read Nick's traffic forecasting workbook before finalising the QSI-to-absolute-demand step.
5. Set a once-a-year refresh against the Airbus/Boeing briefing cadence.
