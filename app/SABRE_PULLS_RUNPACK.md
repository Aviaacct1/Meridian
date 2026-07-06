# Sabre pulls run-pack

Three pulls, in priority order. Two run straight off your existing store; one needs a new
monthly extract (Nick). Run them on the machine with `C:\Avia\sabre.duckdb`, then paste the
printed output back and I will wire the results into the cases.

## 1. Load Sabre 2025 (quick, unblocks 2025-base forecasts)

The 2025 best-estimate file failed a CSV dialect sniff before; `sabre_ingest.py` is hardened
(strict_mode off, null_padding on, delimiter fallback). Re-run the bulk loader, which is
idempotent and only retries 2025:

```
py -3.12 C:\Avia\ingest_all_years.py
```

If it errors on column mapping (the best file may have different headers), paste the first
three lines of the 2025 file and I will map it:

```
powershell -Command "Get-Content 'C:\Avia\<World2025...csv>' -TotalCount 3"
```

Paste back: the row count it reports for 2025 (or the three header lines if it errors).

## 2. Italy-Caribbean O&D (firms the second route off the existing store)

The Caribbean market is already in the annual store, so no new pull is needed. This reads the
real Genoa-catchment to Caribbean split, cabin mix and fares, and writes the observed cache
that replaces the placeholder in the winter-sun case:

```
py -3.12 sabre_caribbean_check.py --year 2024 --write cases/genoa_caribbean_observed.json
```

Default destinations are PUJ, CUN, VRA, HAV, MBJ, POP, SDQ (Dominican Republic, Mexico, Cuba).
Adjust with `--dests` if the store uses different codes or you want a wider set. Then re-run the
case OFFLINE, so it reads the clean cache the check just wrote (do NOT add `--sabre` here, that
would re-pull and overwrite the cache):

```
py -3.12 assess.py genoa_caribbean cities5000.txt
```

If you ever do want a live pull through assess itself, always pass `--year` (e.g. `--year 2024`)
and make sure the case lists the full destination set, otherwise the pull mixes directional and
non-directional years and reads only the case's first airport. The check script above is the
reliable way in.

Paste back: the printed split and cabin summary (and the assess result), and I will firm the
fares, frequency and `econ_share` on the Caribbean case the way we did for Genoa-New York.

## 3. Monthly seasonality (turns the assumed profile into the real shape)

This is the one that needs a new pull, because the annual ODPOO store has no month column.

Preferred: a monthly Sabre O&D extract for the Genoa catchment to New York. Ask Nick for, by
travel month, calendar 2024 (or the latest full year):

- passengers, summed across cabin,
- origin_airport in GOA, MXP, LIN, BGY, TRN, BLQ,
- destination_airport in JFK, EWR, LGA,
- point of origin Italy.

The deliverable is just twelve numbers: total New-York passengers from the Genoa catchment in
each month, January to December. Feed them in:

```
py -3.12 seasonality_from_monthly.py <Jan,Feb,...,Dec passengers>
```

It prints a `--profile` string. Run the seasonality view on the real shape:

```
py -3.12 seasonality_check.py genoa_nyc --profile <printed string>
```

Proxy if the monthly Sabre extract is slow to get: OAG Schedules Analyser monthly SEAT capacity
on the incumbent Milan-New York (MXP/LIN to JFK/EWR/LGA) by month is a reasonable stand-in for
the demand shape. Twelve monthly seat totals go into the same converter. Flag it as a capacity
proxy, not demand, when we use it.

Paste back: the twelve monthly numbers (or the OAG monthly seats), and I will set the Genoa case
seasonality and refresh the business-case workbook.

## What each pull firms

| Pull | Replaces | Currently |
|---|---|---|
| Sabre 2025 | nothing yet | gap in the store |
| Italy-Caribbean O&D | `genoa_caribbean_observed.json` | PLACEHOLDER demand |
| Monthly Genoa-NY | the seasonality profile | ASSUMED leisure shape (Aug/Feb 2.5x) |
