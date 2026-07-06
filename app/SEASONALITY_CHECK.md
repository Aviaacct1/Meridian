# Genoa case: seasonality (the flat-year-round assumption)

The assess chain runs one annual load factor, which is a daily service filling the aircraft every
month. A leisure-led transatlantic route does not do that: summer is capacity-limited and winter is
thin. `seasonality_check.py` applies a monthly demand profile to the case and tests three operating
pictures. Numbers below use the firmed case (entrant fares, $0.90/kg fuel) and a leisure profile
with an August/February demand ratio of 2.5.

| Operating picture | Annual profit |
|---|---|
| A. Nominal flat - plan LF every month (the assess headline) | $9.2m |
| B. Flat daily - fly daily all year, carry real monthly demand | $4.8m |
| C. Seasonal schedule - trim winter frequency to hold the load | $8.0m |

The finding: holding a daily schedule through the winter (B) earns about half the headline, because
January-March and November run at 57-66% load at full cost. The headline is not wrong about annual
demand; it is wrong to assume that demand sits evenly across the year. A seasonal schedule (C),
daily in summer and roughly 19-25 rotations a month in winter instead of 30, recovers $3.2m of the
$4.4m drag and lands within 13% of the headline.

So the honest planning read for Genoa is a SEASONAL operation at about $8m, not a flat daily one. A
naive daily-all-year assumption would carry an empty winter and make closer to $5m. This is the same
shape as the cost and capture findings: the demand is real, but the headline flatters it, and a
sensible operating choice (here, a seasonal schedule) is what makes the route work.

## Caveats

- The monthly profile is an ASSUMPTION. The annual ODPOO store has no month column, so the real
  Genoa-New York shape needs the monthly Sabre pull (the one Nick was asked for). Override the
  default with `--profile` once that lands. The default is anchored on the published European
  summer/winter seat swing (50-65% more August than February seats), with demand swinging harder
  than seats.
- Separately, a current demand watchpoint: Cirium has 2026 transatlantic bookings down about 14%
  Europe-to-US year on year. The case is built on 2024 data, so if that softening holds it is a
  further haircut on the demand side, on top of seasonality.
- The seasonal schedule in scenario C is a simple frequency trim to hold load. A real seasonal plan
  would also redeploy the aircraft in winter (the A321XLR could fly a different route), which would
  improve the fleet economics beyond what this single-route view shows.

## How to run

```
py -3.12 seasonality_check.py genoa_nyc
py -3.12 seasonality_check.py genoa_nyc --profile <12 comma monthly indices>   # once the Sabre pull lands
```
