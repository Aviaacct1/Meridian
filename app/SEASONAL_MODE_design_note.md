# Seasonal forecast mode + optimise extension - design note

Author: Avia Solutions. Status: design, no code yet.

## Goal

The tool forecasts an annual service. Add an explicit seasonal option - annual, summer, winter - so a
user can forecast a service that runs only part of the year (for example four a week for the 28 summer
weeks), and so optimise can choose the schedule shape, not just the departure time and frequency. This
serves the primary user, an airport building a case to an airline, which often is a seasonal case, and
it lets us grade a seasonal forecast against a single-season actual, which removes the seasonal
mismatch that currently reads as an over-forecast.

## What already exists (the foundation)

- Seasonal capacity: `backtest._operated` now blends the two OAG pulls, summer weekly capacity times
  ~28 weeks plus winter times ~24, so a route absent from the winter pull is not credited a full year.
- Service tag: every back-test route is tagged annual / summer / winter from which pulls it appears in.
- Seasonality engine: `seasonality_engine.py` distributes an annual forecast into monthly indices
  (route-specific from Sabre, else regional/leisure defaults), preserving the annual total. It already
  gives the summer and winter shares of annual demand.
- Seasonal economics: `seasonality_check.py` compares flat-daily against a seasonal schedule and
  reports the profit of each (the Genoa case: 9.2m flat headline, 8.0m seasonal, 4.8m flat-daily
  through an empty winter).

The seasonal mode joins these; it does not rebuild any of them.

## The forecast mode

Add a `season` input to the forecast: `annual` (default, unchanged), `summer`, or `winter`.

For a seasonal mode the three quantities all move to the season:

- Demand = annual demand times the season's share of the monthly profile (from seasonality_engine;
  for a leisure route summer carries well over half the year, so a summer service is not half an
  annual one).
- Capacity = the season's weekly capacity times its week count (28 summer, 24 winter), which the
  seasonal-capacity work already computes from OAG.
- Weeks and costs run over the season only, which is what makes a seasonal case profitable - it drops
  the loss-making winter weeks a flat-daily schedule would fly.

Carried forecast stays capped at season capacity times the plan load factor, exactly as the annual
path caps at annual capacity. Nothing in the demand engine changes; the season scales the demand and
swaps the capacity and cost base.

## Optimise extension

Optimise currently loops airline x frequency and keeps the maximum annual profit. Add the season as a
third axis: for each candidate, evaluate annual, summer and winter, take each one's demand share and
season capacity, and cost it over the season's weeks using the `seasonality_check` economics. Return
the shape with the best annual profit, and surface it in the result as, for example, "summer service,
4 a week, 28 weeks" alongside the aircraft and frequency it already reports. A route with a heavy
seasonal peak and a weak off-season will now optimise to a seasonal operation instead of an annual one
that a flat load factor flatters.

## Calibration - and why a chunk of it works now

Grade a seasonal forecast against a single-season actual, like for like.

- One-season routes (tagged summer or winter): the annual Sabre outturn IS the single-season actual,
  because the route never flew the other season. So we can forecast these in their season and grade
  against the existing annual outturn with no new data. These are a large share of the seasonal tail
  we measured, and they move from "excluded because an annual forecast reads them as over" to
  "forecast in-season and counted", which adds calibration signal rather than dropping it.
- Year-round routes with a seasonal peak (the Genoa case): the annual outturn mixes the seasons, so
  grading a summer forecast needs the demand split within the year. That needs the monthly Sabre pull
  requested from Nick (2023-2025), which also firms the seasonality_engine profiles that are currently
  assumed.

So the one-season calibration lands immediately; the year-round seasonal calibration lands when the
monthly pull arrives.

## Data status

- Seasonal capacity: in hand (OAG two-season pulls).
- Season demand share: assumed profiles today (seasonality_engine defaults); measured once the monthly
  Sabre pull lands.
- One-season actuals: in hand (annual outturn = season outturn for one-season routes).
- Year-round monthly actuals: pending Nick's 2023-2025 monthly O&D pull.

## Where this leaves the error picture

With the annual engine carrying the market-size factor and the seasonal engine grading summer and
winter against their single-season actuals, the seasonal-mismatch error and most of the empty-plane
artefact are gone. The remaining category is genuine under-forecasting against what flew, which is
overwhelmingly the induced, new-market routes. That is a modelling problem for the stimulation and
comparable-market layer, not a factor, and it is the one that matters most to an airport pitching a
market the history cannot yet see.

## Build order

1. Market-size factor into the annual engine (already sized, agrees across four years) plus one
   confirming run. Independent of this note.
2. Seasonal forecast mode: the `season` input, demand-share scaling, season capacity and cost base.
3. Optimise extension: the season axis and the seasonal economics, surfaced in the result.
4. One-season calibration: forecast the tagged one-season routes in-season, grade against the annual
   outturn, size any residual seasonal factor.
5. Year-round seasonal demand and its calibration: when the monthly Sabre pull arrives.
6. Induced under-read: separate modelling track, highest airport value.
