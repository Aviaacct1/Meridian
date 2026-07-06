# Engine V2 - the 6-year back-test protocol (clean sample, Covid excluded)

John, 4 Jul 2026: extend the back-test sample to launch years **2016, 2017, 2018, 2019, 2024,
2025** (2020-2023 excluded as Covid-hit and recovery; results there test the pandemic, not the
engine), both to find further refinements and because a public Track-record page built on a
2017-2018 sample alone would look odd. This runbook is the full sequence; every step is a
PowerShell command from the app directory. All V2 work stays opt-in; nothing changes the live
tool until Step 6 passes.

**Data caveat:** a 2025 launch has no complete first-full-year outturn until 2027, so most 2025
routes will drop from the grading stats (backtest drops them automatically). 2016-2019 and 2024
carry the calibration; 2025 rides along for coverage and for the Track-record page's recency.
The discovery step prints which requested years lack Y-1/Y OAG coverage; if 2015 weeks are absent
from the store, 2016 will be thin too - the printout will say so.

## Step 0 - pick lambda on the current cache first (fast, do it today)
The V2-vs-V1 verdict on 2017-2018 passed overall (ALL/HUB/material-feed all better re-centred)
but the sharpest slice - forecastable AND feed-heavy, n=293 - was a small V1 win (med|ln| .315 vs
.339). Before the big sample, tune the share exponent on exactly that slice
(**pinned_ffslice.json**, already in app/; the existing qsi_wave_cache.duckdb covers it):

    py -3.12 backtest.py --qsi-feed --routes-file pinned_ffslice.json --qsi-k 0.65 --qsi-k-behind 1.41 --qsi-lambda 1.5 --out bt_ff_l15.csv
    py -3.12 backtest.py --qsi-feed --routes-file pinned_ffslice.json --qsi-k 0.65 --qsi-k-behind 1.41 --qsi-lambda 2.0 --out bt_ff_l20.csv
    py -3.12 backtest.py --qsi-feed --routes-file pinned_ffslice.json --qsi-k 0.65 --qsi-k-behind 1.41 --qsi-lambda 0.7 --out bt_ff_l07.csv
    py -3.12 compare_mct.py bt_v1_baseline.csv bt_ff_l15.csv     (repeat per lambda)

~40 min per lambda. Read: the lambda whose med|ln| on ALL (this file IS the sharp slice) beats
both lambda=1.0 (bt_v2_hubfeed's 0.339 on this slice) and V1's 0.315. If no lambda gets under
V1, the feed-heavy forecastable wash stands and V2's case rests on the broader slices - still a
pass, but flag it honestly. lambda > 1 sharpens winner-take-most; lambda < 1 flattens shares.

## Step 1 - discover and pin the 6-year route set (minutes)
    py -3.12 backtest.py --years 2016,2017,2018,2019,2024,2025 --routes-file pinned_6yr.json --discover-only

Prints the per-year route counts and any years without OAG coverage, writes the pin, exits.
Expect roughly 2-3x the 2017-2018 set (4,000), so plan for the run times below to scale.

## Step 2 - rebuild the wave cache for the new set (minutes)
    py -3.12 wave_cache.py --oag C:\Avia\oag.duckdb --routes-file pinned_6yr.json --out qsi_wave_cache_6yr.duckdb

## Step 3 - V1 baseline on the 6-year set (long; overnight)
    py -3.12 backtest.py --feed-fix --routes-file pinned_6yr.json --out bt_v1_6yr.csv

Needed regardless of V2: this is also the evidence base for the Track-record page, and the old
baseline only covers 2017-2018. At the observed pace (~8.3 s/route) 10,000 routes ~ 23 h; if
that is too long for one sitting, split by year with --years per run and concatenate the CSVs
(the pin guarantees identical membership per year across A/B runs).

## Step 4 - V2 on the same set at the chosen knobs (long; overnight)
    py -3.12 backtest.py --qsi-feed --routes-file pinned_6yr.json --wave-cache qsi_wave_cache_6yr.duckdb --qsi-k 0.65 --qsi-k-behind 1.41 --qsi-lambda <best from Step 0> --out bt_v2_6yr.csv

If the Step 3/4 FSC-forecastable medians drift off ~1.0, trim --qsi-k proportionally (it scales
the feed linearly; 2017-2018 said 0.65/1.41 with FSC-forecastable at 1.07 vs V1's 1.04).

## Step 5 - the verdict
    py -3.12 compare_mct.py bt_v1_6yr.csv bt_v2_6yr.csv

Acceptance: V2 no worse re-centred on ALL / HUB / material-feed, and the pre/post-Covid years
individually sane (compare by-year medians in the two printouts; a model that only wins in
2017-2018 is curve-fit, not better).

## Step 6 - before any default flip
Phase 4 face validity (dep-time optimiser: optimum/flown >= 1, biggest gaps on known slot/curfew
constraints, e.g. the SJC 23:00 embargo case) and Phase 5 joint reweight of stimulation/P2P
priors on the full sample. Only then does feed_cfg['qsi_feed'] become default-on.

## Current state (4 Jul 2026)
- V1 baseline 2017-2018: bt_v1_baseline.csv (FSC-forecastable median 1.04, hub 1.09).
- V2 at k 0.65/1.41 on the 1,519-route hub/feed set: BEATS V1 re-centred on ALL (.631 vs .664),
  HUB (.650 vs .675), material-feed (.463 vs .493); small V1 win on forecastable+feed-heavy
  (.315 vs .339) -> Step 0. 151 routes had no flown schedule and fell back to V1 (counted).
- k=0.06 first-run artefact documented in the memory notes: LEVEL the feed before reading
  dispersion; implied k from matched feed levels, beyond 0.65 / behind 1.41.
