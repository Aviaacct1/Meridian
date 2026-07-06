# Items 2 and 4: findings and the steps that need your machine

This covers the firming of the Genoa inputs (item 2) and the QSI consolidation (item 4).
The parts I could settle in the sandbox are settled; the parts that need `sabre.duckdb` or
the full pipeline are written up as exact queries and commands for you to run.

## Item 2: firm the Genoa inputs

### Capture rate (0.65 assumed): the case is capped, so the upside is settled and the
### watchpoint is the downside

The daily A321XLR is capacity-limited at the 85% planning load factor, so the headline
economics do not move once demand fills the aircraft. Working the chain through:

- GOA's New-York catchment is 92,542/year; it carries 7,036 today; the leaked pool is 85,506.
- The economy cabin reaches the 85% cap at capture 0.57; the business cabin at capture 0.64.
- At capture 0.65 (the assumption) both cabins are at the cap, annual profit $5.52m, margin 10.7%.
  Any capture above 0.64 gives the same P&L and simply spills more demand.
- The route breaks even at capture circa 0.48 (economy load factor falls to the 73.5% breakeven).
  At capture 0.45 it loses money: annual -$2.2m, economy load factor 69%.

So the 0.65 assumption has a comfortable cushion to the 0.48 breakeven, and choosing 0.65 versus
0.80 makes no difference to the result. The number that matters is whether capture could fall
below circa 0.60. My recommendation: keep 0.65 as the central case, present it as "viable for any
capture above circa 0.5, fully realised above circa 0.64", and stop treating 0.65 as a fragile
point estimate. It is not the sensitive input; the premium fare is (below).

### Fare basis: confirm round-trip vs one-way (one query)

The chain halves the Sabre `avg_total_fare_usd` ($690.55) to a $345 one-way economy fare, on the
read that the field is round-trip. Confirm by eyeballing a few raw rows on your machine:

```sql
-- duckdb C:\Avia\sabre.duckdb
SELECT origin_airport, destination_airport, cabin_class, passengers,
       ROUND(avg_base_fare_usd, 0)  AS base_ow_or_rt,
       ROUND(avg_total_fare_usd, 0) AS total_ow_or_rt,
       directionality, source_year
FROM sabre
WHERE origin_airport IN ('GOA','MXP','LIN','BGY','TRN','BLQ')
  AND destination_airport IN ('JFK','EWR','LGA')
  AND source_year = 2024
ORDER BY passengers DESC
LIMIT 25;
```

A transatlantic economy fare circa $690 reads as round-trip; a one-way economy on this market in
2024 sits nearer $350-450. If the rows confirm round-trip, the $345 one-way stands and the
`--fare-basis rt` default is right. If they read one-way, run with `--fare-basis ow`.

### Cabin mix (econ_share 0.90, premium fare $750/$1,300): set from the data (one query)

```sql
-- duckdb C:\Avia\sabre.duckdb
SELECT cabin_class,
       SUM(passengers) AS pax,
       ROUND(SUM(passengers * avg_total_fare_usd) / SUM(passengers), 0) AS pax_wtd_fare
FROM sabre
WHERE origin_airport IN ('GOA','MXP','LIN','BGY','TRN','BLQ')
  AND destination_airport IN ('JFK','EWR','LGA')
  AND source_year = 2024
GROUP BY cabin_class
ORDER BY pax DESC;
```

Read off two things: the premium share (BUSINESS + FIRST + PREMIUM COACH as a fraction of total)
sets `econ_share`; the passenger-weighted BUSINESS fare (halved if round-trip) sets the realistic
premium fare. The case currently assumes a 90/10 economy/premium split with a $750 realistic
business fare and $1,300 as the full-business sensitivity. A leisure-led Genoa market may carry a
premium share below 10%; if so, lower `econ_share` and the premium fare accordingly. The premium
fare is the input the result is genuinely sensitive to (the capture rate is not), so it is worth
setting from the Sabre cabin figures rather than by assumption.

Override on the assess CLI once you have the figures, e.g.
`py -3.12 assess.py genoa_nyc cities5000.txt --sabre "C:\Avia\sabre.duckdb" --econ-share 0.93 --bus-fare 650`.

## Item 4: point QSI scoring at the single module

### State

- `run_multihub_qsi.py` already imports `itinerary_qsi` from `qsi_score` and scores through it.
  No change needed; it is done.
- `qsi_score.py` is the single source of truth and is now locked by `test_qsi_score.py`, which
  asserts it reproduces the analyst ET lookup exactly (0.10 -> 0.574 ... 6.10 -> 0.037) plus the
  connection and service coefficients. Run it any time with `py -3.12 test_qsi_score.py`.
- `QSIEngine` (in `closed_loop_pipeline_v2.py`) already has the correct ET formula and the
  service-level coefficient (nonstop 1.0 / one-stop 0.20). Its ET maths is identical to
  `qsi_score.et_coeff`. The one difference is the alliance coefficient: `QSIEngine` reads it from
  `RouteConfig`, where the default is still 0.615 (the 2013 code value), while `qsi_score` and the
  2024 SJC workbook use 0.75.
- `qsi_market.py` and `goa_nyc_forecast.py` are not in the project working copy; they live only in
  `C:\Avia`. Re-point those on your machine.

### The one decision: alliance coefficient 0.615 vs 0.75

My recommendation: adopt 0.75. The SJC-HKG acceptance number (circa 65.6%) comes from the 2024
Cathay workbook, which uses 0.75, so the engine has to use 0.75 to reproduce it. The 0.615 is an
inherited 2013 default that pre-dates the validated workbook. Changing it shifts the BA LHR-SJC
regression (the handover already flagged a re-baseline after the service-coefficient fix), so do
both together: change the value, run SJC-HKG to confirm 65.6%, then re-baseline BA.

Change in `route_config.py` (the single place the engine reads it from):

```python
self.alliance_coeff = 0.75      # was 0.615; align to the 2024 SJC workbook and qsi_score
```

### The gate, then retire (your machine)

The handover sequence is: point at `qsi_score`, run the SJC-HKG acceptance test, then retire the
old coefficient copies. The acceptance run needs the Cathay 2024 OAG in the store and the local
pipeline, so it is yours to run:

```
py -3.12 run_multihub_qsi.py --db C:\Avia\oag.duckdb --week <SJC 2024 week> \
   --catchment SFO,LAX,SJC,SAN,OAK --proposed CX,HKG,SJC,<dep>,<arr>,<fly> --qsi2
```

If it lands at circa 65.6%, the consolidation is confirmed and the `C:\Avia` copies of the
coefficients in `qsi_market.py` / `goa_nyc_forecast.py` can be retired in favour of importing from
`qsi_score`. If it does not, do not retire anything; paste the number and I will work the gap.
`test_qsi_score.py` guards the frozen method throughout, so any accidental coefficient change
during the consolidation fails the test rather than slipping through.
