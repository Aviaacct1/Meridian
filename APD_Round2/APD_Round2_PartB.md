# APD study, round two, Part B: published sources and desk research

Prepared by Avia Solutions, 20 July 2026. Companion to `APD_Round2_PartA.md`. Run in the same session as Part A rather than separately, because the RFP response falls on Friday 24 July 2026 and the purpose is to establish what can and cannot be evidenced before then.

**Status:** B1, B2 and B6 complete, being the three the brief prioritises as the largest unvalidated numbers. B3, B4, B4b, B4c, B5 and B7 not yet run; a capability assessment for each is at the end.

**Headline: two of the three priorities changed the model's inputs, and the third changed its premise.**

---

## B1. Fiscal

### HMRC does not publish a Northern Ireland attribution

UK APD receipts were **£4,195m in 2024-25**, up £350m or 9% on the prior year. The APD Bulletin publishes chargeable passengers, declarations and receipts by rate band. It does not publish a regional or Northern Ireland breakdown, and no such attribution appears in the accompanying statistics tables.

**Consequence for the appraisal.** The fiscal cost of abolition in Northern Ireland cannot be validated against any published figure. It must either be modelled bottom-up, which A7 now does, or obtained from HMRC or the Treasury directly. This is one of the two items the brief anticipates may only be resolvable through the Department at contract initiation, and that expectation is confirmed.

### The bottom-up estimate reconciles on a plausibility check

A7 produces a bottom-up duty yield of **circa £48.5m** on 2025 volumes at 2025-26 statutory rates, against the model's provisional £51m. Absent a published NI figure, the available check is proportional:

| Test | Value |
|---|---|
| NI bottom-up duty | £48.5m |
| As share of UK receipts (£4,195m) | 1.16% |
| NI share of UK departures | circa 3% |
| NI blended rate (A7) | £10.83 |
| UK average duty per departure | circa £28 |
| Rate ratio | 0.39 |
| Expected NI receipt share (3% x 0.39) | 1.17% |

The two independent routes give 1.16% and 1.17%. That is a consistency check rather than a validation, but it confirms the bottom-up figure is the right order and that the gap between NI's 3% passenger share and its 1.2% receipts share is explained by the domestic weighting and the near-absence of long-haul.

### Block grant adjustment: the mechanism, and the trap in it

The 2013 devolution of direct long-haul APD was expected to cost circa £5m a year; the block grant adjustment applied since has run at circa £2.3m a year.

The mechanism, as set out for the equivalent Scottish devolution, is that the block grant is reduced by the estimated duty generated in the territory in the year before devolution, then indexed to growth in comparable receipts per person in the rest of the United Kingdom. The principle is that neither government should be better or worse off purely from devolving the power.

**The consequence is the single most important fiscal point in this study and it should be stated plainly in the appraisal.** Devolution transfers no resources. If Northern Ireland sets rates below the rest of the United Kingdom, the block grant adjustment continues to be indexed to rest-of-UK receipts while actual receipts fall, so the Northern Ireland budget absorbs the entire cost of the reduction. The Scottish financial memorandum states this directly: if rates were reduced below levels in the rest of the UK, there would be a reduction in the Scottish budget. Abolition is therefore not a transfer from the Exchequer to Northern Ireland; it is a charge on the Northern Ireland block grant of roughly the full £48.5m, recurring and indexed.

### Administrative and set-up cost: the Scottish precedent

From the Air Departure Tax (Scotland) Bill financial memorandum:

| Item | Set-up | Annual running |
|---|---:|---:|
| Revenue Scotland | £1,455,000 | £555,000 |
| Scottish Fiscal Commission | £75,000 | £55,000 |
| Aircraft operators (industry) | - | £75,000 |
| **Total** | **£1,530,000** | **£685,000** |

Revenue Scotland's set-up splits as £1,110,000 staff, £190,000 non-salary, £35,000 other and £120,000 IT, the last including a 41% Treasury optimism-bias uplift for outsourced IT and VAT at 20%. First-year cost including programme close-down was £700,000. Industry cost is £745 per aircraft operator across an assumed 100 operators making quarterly returns at two days each.

Two caveats before this is read across. These are 2016 estimates for a tax that has still not commenced, so they are neither outturn nor inflated to current prices. And HMRC confirmed there would be no net additional cost from switching APD off in Scotland, so no reimbursement was required, which is a useful precedent for a Northern Ireland equivalent.

### Why the Scottish tax was deferred, and what it means here

This is the most transferable finding in B1. The Air Departure Tax (Scotland) Act 2017 was to apply from 1 April 2018. **It now commences on 1 April 2027, a delay of nine years**, caused throughout by a single question: whether exempting Highlands and Islands flights constitutes a subsidy, first under state aid rules and latterly under the Subsidy Control Act 2022. A consultation, Delivering Scotland's Air Departure Tax, ran from 29 January to 26 March 2026, and the resolution removes the exemption for international flights leaving Highlands and Islands airports while extending it in other respects.

Any Northern Ireland APD differential raises the same class of question: a regionally differentiated tax treatment that must clear the Subsidy Control Act 2022. The Scottish experience indicates that question is capable of delaying implementation by most of a decade. The appraisal should treat subsidy control as a delivery risk with a timeline attached, not a legal footnote.

---

## B2. Environmental

### The parameter, sourced

The DESNZ Green Book supplementary guidance carbon value for 2025 is **£273 per tonne CO2e** in 2022 prices, with a plus or minus 50% sensitivity range, rising to £398 per tonne by 2050.

### The decisive arithmetic, using A6's measured emissions

A6 measures Northern Ireland emissions at **0.0839 tonnes CO2 per departing passenger**, against the model's provisional 0.11.

| Treatment | Carbon value | Cost per departing passenger |
|---|---:|---:|
| Full DESNZ, provisional 0.11 t | £273/t | £30.03 |
| **Full DESNZ, measured 0.0839 t** | £273/t | **£22.90** |
| UK ETS market price, measured | £49.05/t | £4.12 |
| Provisional ETS adjustment of 0.20 | £54.60/t | £4.58 |

**The A6 correction reduces the carbon cost by £7.13 a passenger, or 23.7%, but does not change the sign of the answer.** At the full gross DESNZ value, each departing passenger carries £22.90 of carbon cost against a Band A duty of £13 being removed to stimulate them. The carbon cost is 1.76 times the duty. On those two terms alone the case cannot pay, which confirms the brief's expectation even after the emissions parameter is corrected downward.

**What decides the appraisal is therefore the ETS treatment, not the emissions figure.** And the provisional adjustment of 0.20 can now be checked rather than assumed: the UK allowance price of £49.05 against the DESNZ value of £273 implies an adjustment of **0.180**. The provisional 0.20 is close and slightly generous; 0.18 reproduces the market price exactly.

### The double-counting case is stronger than when the parameter was set

Two developments matter. **Free allocation for aircraft operators was fully phased out on 1 January 2026**, so aviation now pays the full allowance price on every in-scope tonne, with no free element. And A6 establishes that **94.4% of Northern Ireland departures fall within UK ETS scope**, covering UK domestic and UK to EEA flights.

Taken together: from January 2026 essentially all Northern Ireland aviation CO2 is already fully priced inside a capped trading scheme at circa £49 a tonne. Applying the full £273 DESNZ value gross on top of that prices the same tonne twice, and the cap means the marginal tonne does not add to total emissions in any case. That is the substance of the double-counting question the brief raises, and the answer is that it applies to almost the whole of the traffic rather than a portion of it.

The auction reserve price is £22 a tonne, adjusting annually with the GDP deflator from 1 January 2027, which gives a floor for scenario work.

### Directly relevant live consultation

The UK government has consulted on the **impact of the end of aviation free allocation on regional connectivity**. That is the same policy question this study addresses, from the other direction, and it should be read and cited in the response.

### What remains outstanding in B2

CORSIA applicability, the SAF mandate trajectory and its effect on emissions per passenger over the appraisal period, and surface access emissions saved when a passenger flies from Belfast rather than driving to Dublin. None is run here. The last of these is straightforward once a representative drive distance is agreed and can be computed from the leakage volume.

---

## B6. Airport capacity constraints

**The brief's premise is out of date by seven years, and the correction changes what the appraisal must model.**

The brief states that Belfast City is capped at 2m departing seats for sale with a movement cap of 48,000 sought to rise to 61,000, and that any uplift runs into the cap quickly. The seats-for-sale cap was raised from 1.5m to 2m, with movements adjusted from 45,000 to 48,000, but on **24 July 2019 the Department for Infrastructure signed a Modified Planning Agreement which removes the Seats for Sale restriction entirely**, endorsing the Planning Appeals Commission's independent report following the public inquiry.

In its place sits a noise regime:

- a noise control contour, where the area experiencing average equivalent daytime noise of 57dB shall not exceed 5.2 km measured over the summer period;
- a quota count system running alongside the contour, classifying each movement by noise, with the summer total capped;
- a departure noise limit, with levies payable to the Community Fund when exceeded;
- penalties for late flights, increased on the previous voluntary scheme;
- continuous descent approach, fixed electrical ground power at all stands, and a noise insulation scheme for properties above 63dB.

The airport reports compliance to the Department annually by 31 March.

**What this means for the appraisal.** Belfast City is not constrained by a passenger or seat ceiling. It is constrained by a noise envelope, which is a different modelling problem: capacity within the envelope depends on fleet noise performance, so quieter aircraft permit more movements for the same contour, and fleet renewal loosens the constraint over the appraisal period rather than leaving it fixed. Uplift should therefore be modelled against the noise quota and the contour, with an assumption about fleet renewal, and not against a seat cap that no longer exists.

Belfast International and City of Derry positions are not established here and remain outstanding. Belfast International's runway and movement headroom is not thought to be binding, but that should be confirmed rather than assumed.

---

## Capability assessment on the items not yet run

For the RFP response, what is deliverable and what is not:

| Item | Position |
|---|---|
| B3 economic multipliers | Deliverable. NISRA and ONS input-output tables are published. The NISRA detailed external overnight trips tables are the dependency shared with A4, and are the single most important outstanding source in the study. |
| B4 comparators | Deliverable from published sources. The Republic's 2014 abolition is the closest read-across and Part A already establishes the duty history. |
| B4b Edinburgh and Glasgow | Deliverable. Passenger series are published by the CAA; the divergence narrative needs airline basing and route development fund evidence, which is documented. |
| B4c structural advantages | Deliverable. Preclearance, Aer Lingus basing, Tourism Ireland and IDA spend are all documented publicly. |
| B5 alternative interventions | Deliverable, with the caveat that additionality evidence for route development funding is thin and contested, and should be presented as such. |
| B7 Dublin counterfactual | Partly deliverable. The announced Aer Lingus changes can be verified against company and IAG statements and modelled manually onto the summer 2026 base, but must be labelled a press-report scenario. Filed summer 2027 schedules are not available until late October 2026, inside the delivery window if awarded. B7 item 6 is the same calculation as A2.4 and should not be run twice. |

---

## Sources

- [Air Passenger Duty Bulletin - HMRC](https://www.gov.uk/government/statistics/air-passenger-duty-bulletin), for receipts and the absence of a regional breakdown.
- [Air Departure Tax - gov.scot](https://www.gov.scot/policies/taxes/air-departure-tax/), for the 1 April 2027 commencement, the Highlands and Islands exemption design and the January 2026 consultation.
- [Air Departure Tax (Scotland) Bill financial memorandum](https://www.parliament.scot/-/media/files/legislation/bills/previous-bills/air-departure-tax-scotland-bill/introduced/financial-memorandum-air-departure-tax-scotland-bill.pdf), for set-up and running costs, the block grant adjustment mechanism and the rate-reduction consequence.
- [Air Passenger Duty (Setting of Rate) Bill explanatory and financial memorandum - NI Assembly](https://www.niassembly.gov.uk/assembly-business/legislation/2011-2016-mandate/primary-legislation-current-bills/air-passenger-duty-setting-of-rate-bill/air-passenger-duty--setting-of-rate-bill---explanatory-and-financial-memorandum/), for the 2013 devolution cost.
- [Northern Ireland Interim Fiscal Framework - GOV.UK](https://www.gov.uk/government/publications/northern-ireland-interim-fiscal-framework-implementation-update-relative-funding-methodology/northern-ireland-interim-fiscal-framework-implementation-update), for block grant adjustment principles.
- [Traded carbon values used for modelling purposes, 2025 - GOV.UK](https://www.gov.uk/government/publications/traded-carbon-values-used-for-modelling-purposes-2025) and the DESNZ [valuation of energy use and greenhouse gas emissions for appraisal](https://assets.publishing.service.gov.uk/media/65aadd020ff90c000f955f17/valuation-of-energy-use-and-greenhouse-gas-emissions-for-appraisal.pdf), for the £273 central value.
- [UK Emissions Trading Scheme policy overview - GOV.UK](https://www.gov.uk/government/publications/uk-emissions-trading-scheme-uk-ets-policy-overview/uk-emissions-trading-scheme-uk-ets-a-policy-overview) and [ICAP UK ETS profile](https://icapcarbonaction.com/en/ets/uk-emissions-trading-scheme-uk-ets), for allowance price, auction reserve price and the end of aviation free allocation.
- [UK ETS: impact of end of aviation free allocation on regional connectivity consultation - GOV.UK](https://www.gov.uk/government/consultations/uk-emissions-trading-scheme-regional-aviation-connectivity/uk-emissions-trading-scheme-impact-of-end-of-aviation-free-allocation-on-regional-connectivity-consultation-accessible-webpage).
- [Department signs new Modified Planning Agreement with George Best Belfast City Airport - DfI, 24 July 2019](https://www.infrastructure-ni.gov.uk/news/department-signs-new-modified-planning-agreement-george-best-belfast-city-airport), for the removal of the seats-for-sale restriction and the noise regime.
