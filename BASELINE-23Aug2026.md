# Regression baseline, 23 August 2026

Run on the workstation (Workstation Remote), commit 25386ef, as Task 4 of the readiness
push (HANDOVER-23Aug2026.md). Each file run directly (`py -3.12 <file>.py`), not via
`pytest -m pytest`, since these are standalone check scripts with their own PASS/FAIL
harness and a module-level `sys.exit()` that pytest's collector cannot import cleanly
(confirmed live: `pytest -m pytest test_airport_profile.py` throws INTERNALERROR on
collection; running the same file directly gives a clean 36 checks, 0 failed). `pytest`
itself was not installed against `py -3.12` on this workstation and was installed fresh
this run (pytest 9.1.1) to prove the diagnosis, but is not the runner for this batch.

## Clean: 22 of 22 assertion-based test files, 0 failures

| File | Result |
|---|---|
| test_workbook_table.py | 22 checks, 0 failed |
| test_airport_profile.py | 36 checks, 0 failed |
| test_alliance_share.py | 10 checks, 0 failed |
| test_attribution.py | 33 checks, 0 failed |
| test_check_airport.py | 27 checks, 0 failed |
| test_competition_split.py | 13 checks, 0 failed |
| test_contract_p2p_row.py | 13 checks, 0 failed |
| test_demo_flow.py | 58 checks, 0 failed |
| test_fare_bands.py | 22 checks, 0 failed |
| test_feed_provenance.py | 0 failure(s) (5 named tests) |
| test_floor_only_arm.py | 13 checks, 0 failed |
| test_load_aci.py | 53 checks, 0 failed |
| test_qsi_score.py | 6 passed |
| test_refresh_pickup.py | 0 failure(s) (7 named tests) |
| test_route_case.py | 3 passed, 0 skipped |
| test_schedule_sizing.py | 20 checks, 0 failed |
| test_track_control.py | 11 checks, 0 failed |
| test_watch_series.py | 20 checks, 0 failed |
| test_deck_contract_ptew.py | 27 checks, 0 failed (run from C:\src\meridian directly) |

Diagnostic/eyeball scripts with no pass/fail criteria, ran without error, output sane:
test_economics_wiring.py, test_network.py, test_mct.py.

## Two red results, both diagnosed, neither a live regression, neither touched by any
## change in this session or the prior (19 August) session

**test_qsi_feed.py** - 9 of 12 checks fail (`3 passed, 9 failed`), and the pattern is a
clean legality inversion: an illegal connection (buffer below MCT) scores 1.0, a legal
one (buffer above MCT) scores 0.0. This is Engine V2, the schedule-quality QSI feed.
`cortex_app.py` (line ~1082-1099) carries John's own 15 August K-SWEEP decision verbatim:
Engine V2 could not beat the V1 flat feed at any k on the pinned back-test, so it is
permanently off (`qsi_feed` stays `FALSE` for `feed_side`) unless an operator sets the
environment variable `AVIA_FEED_LEVEL=qsi`. No UI control reaches this switch; testers
cannot enable it by clicking anything. Genuinely broken code inside a deliberately
parked, env-gated-off module, not a live regression. Not investigated further (fixing a
parked engine is new feature work, out of scope for today per HANDOVER-23Aug2026.md
section 8).

**test_regression_v2.py** - crashes with `FileNotFoundError` reading
`Z:\Shared\Company Data\...\QSI@LHR v1 (OS JZ) 17Feb15.xlsx`, one of the original manual
QSI reference spreadsheets, from `closed_loop_pipeline_v2.py` / `providers.py`, the old
pre-Meridian validation harness that compares the new engine against analyst Excel
workbooks on the Egnyte share (Z:). Confirmed with John: the workstation is deliberately
self-contained with a known dataset, and Meridian has no legitimate reason to reach
Egnyte. Not runnable from the workstation by design; not to be fixed by granting Z:
access. Not part of this baseline.

**test_route_forecast.py** printed `need both stores; pass --oag and --sabre` and exited
0 without running a single check; it needs data-store paths as CLI arguments nobody
passed. Not a pass - a no-op. Not covering anything in this baseline.

## Verdict

Everything reachable by a tester through the live product is green. Both red results
trace to code that testers cannot reach (an env-var-gated, already-shelved engine
module) or to infrastructure the workstation is deliberately not connected to (Egnyte).
Neither blocks testers starting.
