# Code-tree reconciliation - 26 July 2026

Prepared by Avia Solutions | branch `reconcile/dot-merge-20260726`

## The problem

Two `app` trees had diverged and both held real work:

- `C:\AviaDev\app` (this git repo): the shipped accuracy engine (market-size trim,
  split_share, hub connectivity, induced floor), the accuracy R&D toolkit
  (`--decompose`, `fy_capacity.py`, `analyze_decomp.py`, airport-factor work) and the
  newer Observatory / Meridian branding (sign-in / welcome / loading / error screens,
  demo no-password entry), cortex_app dated 23 July.
- `C:\Users\Carte\OneDrive\...\Avia QSI Tool\app` (mounted by Cowork): the 25 July US
  DOT integration, layered onto a copy that had forked from git in early July, BEFORE
  the market-size trim (commit 57f5cd2, 7 Jul) and the split_share / hub-connectivity
  work (6e05d5d / dac8028, 9 Jul), and before the welcome / loading screens.

Cause: Cowork was mounted on the OneDrive copy, so the DOT work went onto a stale
engine and never met the accuracy-arc commits.

## Direct consequence for the accuracy work (answers Step 1)

The Projects `MARKET_FACTOR_BY_TYPE` carried the RETIRED Item-9 flat trim
(`FSC/ULCC 0.85, LCC 0.95, Regional 0.90`), not the shipped `_SIZE_TRIM`
(`[(15000,0.765),(50000,0.821),(150000,0.809),(inf,0.745)]`). So the size trim was
NOT active in the build the 25 July haul run used. That is why `bt_haul_b35.csv`
read forecastable median 1.26 rather than circa 1.0. The two-sided haul slope from
that run is confounded (measured without the size trim, split_share or hub
connectivity) and must be re-cut on the unified engine before it is believed.

## Decision

`C:\AviaDev\app` is canonical (git history + the accuracy engine + the newer
branding). The 25 July DOT integration was re-applied onto it. Nothing of the
branding is at risk: AviaDev already holds the fuller version.

## What was merged onto AviaDev (all additive, all default-OFF)

| File | Change | Inert when |
|---|---|---|
| `od_source.py` | NEW (copied from Projects) - DB1B/Sabre O&D selector | `AVIA_OD_SOURCE` unset -> returns Sabre, byte-identical |
| `econ_benchmark.py` | NEW (copied from Projects) - carrier CASM resolver | only read when `AVIA_ECON_FORM41=1` |
| `config.py` | + DB1B / T100 / Form41 / CASM store registration | pure additions, no existing value changed |
| `route_forecast.py` | market fetch routed through `od_source`; DB1B coverage skip; `AVIA_HAUL_TRIM` block (uses `gcd_est`); `od_source`/`haul_trim` on the result dict | `od_source` defaults to Sabre; DB1B skip cannot trigger; `haul_trim=1.0` when the flag is off; kept `_SIZE_TRIM`, split_share, hub_localness intact |
| `backtest.py` | growth-term market query routed through `od_source` | defaults to Sabre; `SC` still used for `nonstop_share` |
| `aircraft_economics.py` | + Form 41 CASM calibration (2 dataclass fields, calibration block, 2 result fields, `AVIA_ECON_FORM41` opt-in), kept AviaDev's ownership/crew override logic | inactive unless a CASM benchmark is supplied / `AVIA_ECON_FORM41=1` |

Pre-merge copies of the three edited-and-shared files are in the session scratch
(`premerge_backup/`), and the git-committed versions remain at 5859a70.

## Verification done (sandbox)

- `py_compile` clean on all six files.
- `od_source`, `config`, `econ_benchmark` import; `config.DB1B_DUCKDB` resolves.
- The SJC inbound override is present in AviaDev as `airport_capture.dest_thin_factor`
  / `AIRPORT_DEST_THIN` (SJC 2.0x under 200k), called from `route_forecast` line ~498.
  The memory's `AIRPORT_DEST_CAPTURE` name was superseded; nothing was lost.
- Divergence sweep: the four files newer-by-timestamp in Projects
  (`route_engine`, `track_record`, `methodology_page`, `diag_water_catchment`) are
  byte-identical (OneDrive re-touched mtimes). Projects-only `.py` files are pre-fork
  scratch / superseded modules; not re-added.

The sandbox CANNOT run `git` here: this mount denies file unlink, so the stale
`.git/index.lock` cannot be cleared and `git add`/`commit` fail. Do the commit on
Windows.

## Windows-side steps (John)

1. `cd C:\AviaDev` then `del .git\index.lock`
2. `git status` - review. You should be on `reconcile/dot-merge-20260726`.
3. `git add -A && git commit -m "Reconcile: re-apply 25 Jul DOT integration onto the accuracy engine (od_source, econ_benchmark, config stores, haul-trim, DB1B, Form41); branding intact"`
4. INERT BASELINE TEST (the acceptance gate): run the NA backtest with every flag OFF
   (`AVIA_OD_SOURCE`, `AVIA_HAUL_TRIM`, `AVIA_ECON_FORM41` all unset) and confirm it
   reproduces the pre-merge AviaDev baseline exactly. If it matches, the DOT re-apply
   is proven inert and the engine is sound.
5. Economics spot-check: one route's P&L with `AVIA_ECON_FORM41` unset must match
   pre-merge; then with `AVIA_ECON_FORM41=1` confirm the CASM anchor behaves.
6. Once validated, regenerate the OneDrive `Avia QSI Tool\app` as a mirror of
   `C:\AviaDev\app` (or point Cowork at `C:\AviaDev` directly) so the fork cannot recur.

## Then the accuracy work is unblocked on ONE tree

Step 0 (multi-horizon grading) partly exists here already: `backtest.py` carries
`outturn_offset` and `--mature`/`--y3`. Note the watchpoint the plan flags: the
forecast is grown with `growth_years=1 + outturn_offset`, so regrading to Y2/Y3
currently also grows the NUMERATOR - the retired H7 overshoot. Step 0 must hold
`growth_years` fixed and move only the outturn (denominator) year.
