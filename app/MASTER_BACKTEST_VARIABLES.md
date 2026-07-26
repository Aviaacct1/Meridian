# Master backtest — variable inventory

**Author:** Avia Solutions · **Date:** 10 July 2026
**Purpose:** build ONE enriched backtest row per graded route carrying every driver we can think of, so the
driver analysis (full model + within-airport scan + clustering) runs on a rich feature set, not the thin slice
currently in the file. Conclusions about "which drivers matter" are only as good as this list.

**Status legend:** `[have]` already a column · `[derive]` computable from on-disk assets · `[pull]` needs a raw
extract from the Sabre/OAG stores (C:\Avia, John runs — sandbox can't reach them) · `[outcome]` is a result, not
knowable at forecast time — keep for diagnosis but EXCLUDE from any forecast/predictive model (leakage).

## A. Route geometry
- stage length / great-circle km — `[have]` gcd_km
- haul band (sh/md/lg/xl) — `[derive]`
- domestic vs international — `[have]` dep_country vs arr_country
- within-region vs intercontinental — `[derive]` from region pair
- direction eastbound/westbound, timezone delta — `[pull]` from airport coords
- over-water / island route — `[pull]` coords + coastline

## B. Market size & demand structure
- measured O&D market ("natural") — `[have]`
- P2P share / connecting-heaviness — `[have on bt_v3]` p2p_share (add to master)
- directional demand imbalance (inbound vs outbound O&D) — `[pull]` Sabre directional O&D
- seasonality index of the O&D — `[pull]` monthly Sabre O&D
- leisure / VFR / business mix — `[pull]` Sabre booking-class or fare-basis mix (proxy)
- market maturity — years the O&D has existed at scale — `[pull]` Sabre history

## C. Capacity & supply
- deployed seats / capacity — `[have]` capacity
- seats-to-market ratio (cap / market) — `[derive]` **(the one recurring lead so far)**
- weekly frequency — `[pull]` OAG
- aircraft gauge (seats/flight) — `[pull]` OAG
- existing nonstop before launch? / nonstop share — `[have on bt_v3]`
- capacity added vs pre-existing capacity on the pair — `[pull]` OAG
- achieved load factor — `[outcome]`

## D. Competition & carrier
- carrier type (FSC/LCC/ULCC/charter) — `[have]` type
- operating carrier identity — `[have]` carrier
- number of airlines operating the ROUTE — `[pull]` OAG
- number of airlines operating at the AIRPORT — `[pull]` OAG
- new entrant vs incumbent on the pair — `[pull]` OAG history
- LCC penetration at the airport (LCC seat share) — `[pull]` OAG
- is operator the dominant carrier at the airport — `[pull]` OAG
- alliance membership of operator — `[pull]`/reference

## E. Airport role & catchment geometry
- primary/secondary within metro (proper) — `[pull]` coords + size ranking (NOT the city-group hack)
- catchment overlap with a larger neighbour (% shared) — `[derive]` catchment cells + coords
- catchment population — `[pull]`/reference (cell data)
- drive-time isolation (km/min to next airport) — `[pull]` coords
- airport size (annual seats / pax) — `[pull]` OAG (raw, not the served file)
- destinations served (count) — `[pull]` OAG
- raw hub transfer % (Sabre connecting/total) — `[pull]` Sabre (raw, not the prepared localness)
- slot-constrained flag — `[pull]`/reference
- runway length / elevation — `[derive]` ourairports_runways_cache.json

## F. Price / economics
- fare — `[outcome]` outturn_fare (used it before; it's a result — diagnosis only)
- expected/quoted fare at launch — `[pull]` if a forecast-time fare exists, else drop
- fare vs distance (yield per km) — `[derive]` from a forecast-time fare
- price vs competing routings / alternative airports — `[pull]` Sabre fare by routing

## G. Schedule quality
- frequency (daily vs weekly) — `[pull]` OAG
- wave / connection timing quality (for feed) — `[derive]` OAG wave cache (already built)
- year-round vs seasonal service — `[pull]` OAG season flag (season-grade work)

## H. Temporal / maturity
- launch year — `[have]` year
- grading offset / months matured at grade — `[derive]` **(the confound we found; make it an explicit column)**
- forecast vintage year — `[have]`

## I. Geography
- region — `[have]` · country pair — `[have]` · continent pair — `[derive]`

---
## Build workflow
1. **Claude derives/joins** everything marked `[derive]` (haul, ratios, overlap from catchment cells, runway,
   wave-timing, maturity offset, geography) onto the existing backtest columns.
2. **John runs the raw pulls** marked `[pull]` from the Sabre/OAG stores into per-route or per-airport CSVs
   (competition counts, frequencies, gauge, network size, raw transfer %, directional/seasonal O&D, coords).
   I'll write the exact queries per block.
3. **Assemble** the master file (join all on route + airport keys), mark each column forecast-time-safe or
   `[outcome]`.
4. **Re-run** the full OLS + drop-one and the within-airport driver scan on the master file. THEN conclude.
