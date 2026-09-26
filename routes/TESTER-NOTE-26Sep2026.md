# Meridian: note for Stefan and Suzanna, 26 September 2026

From John. Please play with it as much as you like before the 16 October trial; nothing you do
can break it. Tell me what confuses you, what looks wrong, and what you would be asked.

## What changed this week

- The accuracy line is now one sentence, used everywhere: "When this model was used to forecast
  the new routes that launched since 2016, 88% of its forecasts were within 20% of what the route
  went on to carry and 78% within 10%, across 6,524 launches. The past does not predict the
  future, but that is the record." Say "about six and a half thousand".
- A defect that doubled the local passengers on most forecasts was fixed today. Numbers you saw
  before 26 September are higher than the tool gives now; the new ones are the right ones.
- If you are asked what "calibrated" means: "fitted on the full history of 6,524 launches and
  graded on the same launches. On launches it never saw, a portfolio of twenty routes lands within
  20% of the actual total 94% of the time."

## How to demonstrate it

1. Ask the visitor for a route they know.
2. OPTIMISE first. Say what it is: "It reads the demand for each airline that could fly it and
   finds the aircraft and weekly frequency that carry that demand at a sensible load factor,
   daily at most. It is the tool's proposition, not a prediction of what an airline would choose."
3. Then RUN their own schedule: airline, aircraft, frequency, season, times as they give them.
4. Read three lines, not one: the passengers carried (the headline), the demand behind it, and the
   spill or fill line. If the headline equals the seats at the load factor, say "the aircraft
   fills; the demand behind it is higher".

## What to watch for (known limits, being worked on)

- AN ORANGE NOTE saying the route is outside the range of the calibrated model: fewer than 250
  passengers a year fly it today. The forecast then comes from the older market-share engine.
  Say so, and do NOT quote the accuracy sentence on that route.
- AN AIRFIELD OR RANGE BANNER at the top: the aircraft may not be able to operate from one of
  the runways, or is near its range. Optimise now sets such types aside and says so.
- CONNECTING PASSENGERS on long-haul routes into a big hub read high; the local figure is good.
  If a visitor challenges the connecting number, agree it is the least certain part.
- THIN ROUTES that do not fill the aircraft can read low. Say the range is wide on routes like it.
- Optimise can still pick a larger aircraft than an airline would launch with; a fix that bounds
  it to what airlines have actually launched on similar routes is being built.

## Access

The same address and password as before (John sends them separately). Use Chrome. If the page
says "Failed to fetch", do not retry repeatedly; message John.


## Added 26 Sep night: the schedule basis box

Optimise now first looks at what airlines launched on comparable pairs (same haul, region, carrier
type and size of market, from the 6,524 launches since 2016), searches only inside that seat and
frequency range, and picks the schedule that contributes most to the airline within a 65-85%
planned load. A grey "Schedule basis" box on the first screen says which range applied and how many
launches it rests on, and a "Carrier check" line says what the chosen airline itself has launched
on similar routes. If the box is amber and says the schedule prior is not loaded, stop and tell the
controller: that run is not the one being tested. Wait for John's go before testing; testing starts
once the workstation acceptance has passed.
