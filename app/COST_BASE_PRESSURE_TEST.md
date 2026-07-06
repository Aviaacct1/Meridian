# A321XLR transatlantic cost base: pressure-test (27 June 2026)

The firmed Genoa case shows 21.3% margin and $12.7m annual profit. That number leans on the
A321XLR cost stack, which had not been scrutinised the way the demand side has. This tests the
stack against current published data. The headline: the cost STRUCTURE holds up, but the fuel
PRICE assumption is materially optimistic, and correcting it is the difference between a 21%
headline and a circa 15% planning figure.

## The cost stack (firmed case, per turnaround: out + back, 18 block hours, 182 seats)

| Line | $/turn | Share | Verdict |
|---|---|---|---|
| Fuel | 30,600 | 24% | Optimistic - priced at $0.68/kg, about 40% below current |
| Crew | 21,600 | 17% | Plausible; LCC $1,200/block-hour, not independently verified |
| Ownership | 16,880 | 13% | Sound; blended owned+leased off a $500k/mo XLR lease |
| Airport pax charges | 15,925 | 12% | Indicative placeholders (GOA/JFK), not validated tariffs |
| Admin + sales | 14,981 | 12% | 10% of net revenue, standard |
| Maintenance | 14,740 | 11% | Sound; Airbus reserve curve, validated |
| Handling | 5,871 | 5% | Indicative |
| Landing | 4,429 | 3% | Indicative |
| Insurance | 2,157 | 2% | Sound |
| Nav | 1,135 | 1% | Maverick formula |
| Catering | 819 | 1% | Sound |
| **Total** | **129,138** | | CASK $0.0547/seat-km |

## What the benchmarks say

**Fuel price - the material finding.** The model prices jet fuel at $0.68/kg, which is $2.07/US
gallon. The June 2026 IATA monitor has the global average at $141.64/barrel, roughly $3.37/gallon,
and the US spot indices sit at $3.30-3.57/gallon. That is about $1.09-1.17/kg, roughly 60% above
the model. Current prices are elevated by Strait of Hormuz supply disruption, so they are not a
fair planning basis either, but a normal through-cycle planning price is $0.85-0.95/kg
($2.60-2.90/gallon), still well above the $0.68 in the model. Fuel is a quarter of the cost, so
this assumption drives the result more than any other.

**Fuel burn.** The model uses 2,500 kg/block-hour. Published A321XLR cruise burn is circa
2,720-3,028 kg/hour (900-1,000 US gallons), so the block figure is at the low end, perhaps 5-10%
light once climb is included. Secondary to the price, but it compounds with it.

**Ownership / lease.** The A321neo leases at circa $460k/month (IBA, 2025); the model's $500k for
the longer-range XLR is reasonable, arguably slightly generous, so the ownership line is sound and
if anything conservative.

**Ex-fuel cost structure.** Stripping fuel, the model's CASK is about $0.067/seat-mile, at the
high (conservative) end of transatlantic narrowbody benchmarks. So the cost base is not understated
elsewhere; the optimism is concentrated in the fuel price.

## What it does to the result

Fuel is linear in the model, so re-pricing it alone gives:

| Jet fuel | Margin | Annual profit |
|---|---|---|
| $0.68/kg - model (too low) | 21.3% | $12.7m |
| $0.90/kg - through-cycle planning | 15.3% | $9.1m |
| $0.95/kg + burn 5% higher | 12.6% | $7.5m |
| $1.10/kg - current spot | 9.8% | $5.9m |
| $1.17/kg + burn 5% higher - stress | ~7% | ~$4m |

The reassuring part: the route stays profitable across the whole band, including the current fuel
spike. The honest part: the $12.7m headline is a low-fuel number, and the realistic planning
figure is circa 15% margin and $9m, with fuel the swing input.

## What I changed and what I recommend

- Added a per-route fuel-price lever: `fuel_price_usd_kg` on the case (and `--fuel-price` on the
  assess CLI). It defaults to the module's $0.68 so the validated Maverick E190 anchor is
  untouched, and the Genoa acceptance test stays green. Run any planning price with, e.g.,
  `py -3.12 assess.py genoa_nyc cities5000.txt --fuel-price 0.90`.
- Recommendation: adopt a through-cycle planning fuel price of about $0.90/kg as the Genoa central
  case, and carry the current $1.10/kg spot as the downside. That presents the route as circa 15%
  margin / $9m central, circa 10% / $6m under today's fuel - both viable, and defensible because
  they do not rely on a fuel price the market has not seen since before the current spike. Tell me
  the planning price you want and I will pin it in the case and refresh the reference.
- Still open, lower priority: the airport charges for GOA and JFK are indicative placeholders, not
  validated tariffs, and crew at $1,200/block-hour is a judgement pending the citation sweep.
  Neither moves the result like fuel, but both should be firmed before the case fronts a pitch.
