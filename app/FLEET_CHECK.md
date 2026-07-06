# Genoa case: fleet utilisation and redeployment

The single-route P&L charges aircraft ownership at a fully-utilised per-block-hour rate: the lease
spread over the aircraft's assumed annual block hours (5,425 for this A321XLR). That rate only
recovers the lease if the aircraft actually flies those hours. A daily long-haul does not, and that
is the quiet assumption inside the Genoa headline. `fleet_check.py` makes it explicit.

## Fleet reality (firmed case, $0.90/kg fuel)

| | |
|---|---|
| Block hours/year | 6,552 |
| Aircraft required | 1.21 -> 2 physical |
| Per-aircraft utilisation | 3,276 BH/yr (60% of the 5,425 full-util rate) |
| Spare fleet capacity | 4,298 BH/yr (~239 long-haul rotations) |

A daily Genoa-New York commits two A321XLRs (a ~9-hour each-way sector cannot turn daily on one
aircraft) but only generates 1.21 aircraft of flying. Each aircraft sits at 60% utilisation.

## The ownership-recovery gap

The route P&L charges ownership at $938/block-hour, which is the lease amortised over 5,425 hours.
Fly only 3,276 and the lease is not recovered:

| | |
|---|---|
| Ownership charged in the P&L | $6.1m/yr (full-util rate x hours flown) |
| True cost if 2 aircraft fly Genoa only | $10.2m/yr (blended lease $424k/mo x 2) |
| Standalone ownership gap | $4.0m/yr |

## What the headline assumes

| | |
|---|---|
| Network headline profit (fleet fully utilised) | $9.1m |
| True STANDALONE profit (Genoa's fleet only) | $5.1m |

The $9.1m is a network number. It holds only if the two aircraft are kept busy across the network;
the redeployment must fill 4,298 spare block-hours, about 239 long-haul rotations, to earn it. As a
standalone startup flying nothing but Genoa, the true figure is $5.1m, because the aircraft is 60%
utilised and the lease is not recovered. Fleet redeployment is therefore load-bearing for the
headline, not optional upside.

## Fleet sharing keeps the count down

A second long-haul fitted inside Genoa's spare capacity (illustrative, about 4x/week) costs no extra
aircraft: run separately the two routes need 2 + 1 = 3 aircraft, shared they need 2, saving one
aircraft's lease of roughly $5m a year. The per-block-hour ownership model is self-correcting here:
once both routes fly, their combined per-BH ownership charges recover the full two-aircraft lease,
which is exactly why the per-BH rate is valid at full utilisation and understated below it.

## How this ties to seasonality

The seasonal finding and the fleet finding are the same lever seen twice. Genoa's winter is thin, so
a seasonal schedule frees aircraft time precisely when a counter-seasonal route (winter sun) needs
it. The natural Genoa operation is a summer-peak transatlantic schedule with the aircraft redeployed
to winter flying, which both lifts winter utilisation and earns the headline ownership rate. The
honest planning picture for Genoa is therefore: about $5m as an isolated single route, about $8m as a
seasonal schedule, and back toward the $9m headline only as part of a network that keeps the fleet
busy year-round.

## How to run

```
py -3.12 fleet_check.py genoa_nyc
```
