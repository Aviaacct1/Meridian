# Wiring the full-year capacity provider into backtest.py

Status: `fy_capacity.py` is staged and verified against `C:\Avia\oag.duckdb` (24 Jul 2026). The capacity functions reproduce the parquet capacity exactly (LHR-JFK 2018 both-way 3,816,535). The end-to-end graded backtest has NOT been run; that is the local `py -3.12` job below. All edits are additive and gated on `--fy-capacity`, so with the flag off `backtest.py` is byte-for-byte the shipped behaviour and the live demo is untouched.

## The three shipped mechanisms this replaces (only when --fy-capacity is set)

1. `weeks_by_year` returns every label per year (now mixes monthly, weekly, half-year, annual). Full-year path uses `fy_capacity.months_by_year` (monthly labels only).
2. `_operated` annualises two snapshot weeks (summer cap x28 + winter cap x24) and computes `SUM(seats_total x frequency)`, which double-counts frequency because seats_total already includes it. Full-year path uses `fy_capacity.route_capacity_fy` (sum of monthly seats_total, no x52, no double-count).
3. `oag_served.build_served_index` reads one week x52. Full-year path uses `fy_capacity.build_served_index_fy` (monthly sum), cached per year not per week.

## Edits

**a. `main()` argument (near the other flags, ~line 690):**

```python
ap.add_argument("--fy-capacity", action="store_true",
                help="read full-year monthly operated capacity (fy_capacity) instead of the "
                     "two-week snapshot annualisation; clean set = Europe/Asia 2015-18 + all 2019 H1")
```

**b. period map (where `wby = weeks_by_year(a.oag)` is built, ~line 781):**

```python
import fy_capacity as FY
wby = FY.months_by_year(a.oag) if a.fy_capacity else weeks_by_year(a.oag)
```

**c. launch enumeration.** `discover_new_routes` / `nonstop_pairs` must enumerate from the same monthly labels when `--fy-capacity` is on (a pair "new in Y" is judged on Y vs Y-1 monthly presence). Pass `a.fy_capacity` into `discover_new_routes` and, inside it, source the year's labels from `FY.months_by_year` rather than `weeks_by_year`. Keep the `min_freq` guard; `nonstop_pairs` already sums `frequency`, which for monthly labels is the year's monthly departures, so raise `--min-freq` from the weekly 3.0 to an annual-equivalent (e.g. 150) or convert inside.

**d. `asif_forecast` (signature + body).** Add `fy_capacity=False` to the signature and thread it from `run(...)`. Then:

- served index (replaces `_served_for_week(oag, asif_week, served_cache)`):
```python
if fy_capacity:
    ay = (Y - 1) if wby.get(Y - 1) else Y
    served = served_cache.get(ay) or served_cache.setdefault(
        ay, FY.build_served_index_fy(oag, ay, wby[ay]))
else:
    asif_week = sorted(wby.get(Y - 1) or wby.get(Y))[0]
    served = _served_for_week(oag, asif_week, served_cache)
```
- capacity (replaces the `_operated(oag, cap_weeks, dep, arr)` call):
```python
if fy_capacity:
    cy = next((y for y in (Y + outturn_offset, Y + 1, Y, Y - 1) if wby.get(y)), None)
    c = FY.route_capacity_fy(oag, dep, arr, cy, wby[cy]) if cy else {"annual_cap":0,"freq":0,"gcd":0,"service":"na"}
    annual_cap, freq, gcd, service = c["annual_cap"], c["freq"], c["gcd"], c["service"]
else:
    cap_weeks = wby.get(Y + outturn_offset) or wby.get(Y + 1) or wby.get(Y) or wby.get(Y - 1) or []
    annual_cap, freq, gcd, service = _operated(oag, cap_weeks, dep, arr)
```

No change to `route_forecast.py` or `cortex_app.py`: the forecast still receives `annual_capacity=annual_cap`, only the number changes.

## Two behavioural caveats to hold in the grade

- **2019 is Jan-Jun only.** `build_served_index_fy` scales a part-year to a full-year equivalent (x52/weeks) so size_m stays comparable, but H1 carries the spring build-up, so a 2019 size_m runs a little high. `route_capacity_fy` does NOT scale (it sums the months present), so a 2019 route capacity is a half-year figure; grade 2019 launches on a half-year-consistent basis or wait for H2. Flag, do not paper over.
- **Coverage.** For 2015-2018 only Europe and Asia have monthly data, so a served index or a route touching North America, Latin America, Africa, Middle East or Southwest Pacific in those years is under-summed. Run the clean set (both endpoints in a monthly region, or 2019) until the North America / Southwest Pacific monthly re-pull lands.

## Run and prove (local, py -3.12)

1. Parity control: run the backtest twice on the same clean-set launches, once without and once with `--fy-capacity`, keeping every other flag identical. The capacity column should move exactly as `launch_capacity_before_after.csv` predicts (median 0.88, spread p10 0.44 to p90 1.41 on the 373 both-direction-complete launches).
2. Grade DISH / CV / MOUSE on the `--fy-capacity` run and set it beside the shipped grade. Do not wire any live table until a layer proves out on the held-out grade.
