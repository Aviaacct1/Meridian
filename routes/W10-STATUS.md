# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. The controller reads it; John reads it on a
phone. Version 1, 22 September 2026, session 1.

## One-screen summary

- Read: routes/README.md, routes/W10-RULINGS.md v1, PROMPT-for-Fable-Routes-19Sep2026.txt,
  bt2/README.md, bt2/bt2_claimset.py, bt2/bt2_mixed_basis.py, bt2/bt2_capture.py,
  app/search_adjustments.py, app/route_forecast.py (catchment lines), bt2_experiments.log
  lines 115-140 and 377-395. Local clone HEAD read from .git: 7c15c3d (main). No git run.
- Nothing has been run yet. No figure in this file is new; every figure quotes its log line.
- BLOCKED ON THE CONTROLLER, item 1 (catchment radius): the test as specified cannot measure
  what it is meant to measure. Detail under "Conflicts seen". Items 2 and 3 are not blocked
  and their blocks are below; item 3's run is a measurement on unchanged artefacts, so it
  can go while item 1 is re-ruled without breaking the "radius before anything else changes"
  order.
- 3 October: still achievable for items 2 and 3. Item 1 depends on the re-ruling; if the
  controller keeps an accuracy re-measurement on the QSI engine back-test, W10 needs one
  timed arm before it can say, and will say by 29 September as instructed.

## What is established from the record (no new runs)

1. The claimset (bt2/bt2_claimset.py) is BT2, a gradient-boosted median regression on
   fifteen launch features from E:\Avia\bt2_relaxed. Its capture feature (qcx, capa) is
   built by bt2/bt2_capture.py from the QSI CONNECTION BUILDER (connecting competition),
   not from the catchment choice model. No file in the BT2 training chain (bt2_lib,
   bt2_g12_exp, bt2_gbm, bt2_capture, app/bt2_capture_core) references a radius, the
   catchment, or route_forecast. Verified by grep this session.
2. The catchment radius in app/route_forecast.py (haul_radius_km, 220 km; DEMAND_RADIUS_KM
   110 km; catchment_mult at line 536) reaches only qsi_capture_share, the QSI engine's
   origin capture share. Under the live engine as restarted 22 Sep (--engine bt2, umbrella
   decisions log), that share is REPLACED by BT2's p2p_demand_override for the local leg.
3. There are three separate 220 km constants in the product, not one: route_forecast
   haul_radius_km (catchment share, above); cortex_app.calibrated_forecast radius_km=220,
   which builds the COMPETING AIRPORT SET via RE.competing_airports (line 1010) and is the
   path by which BHX enters the London set and the nonstop table; and cortex_app line 2258,
   radius=220 for the catchment page. Jol item 33 (BHX under London-Paris, nonstop table)
   is the second of these, owned by W2 under ruling R6 in JOL-FEEDBACK-REGISTER.md.
4. app/search_adjustments.py is a post-hoc multiplier harness: it reads an already-scored
   back-test CSV (fc_over_out per route) and fits group factors with a 5-fold control. It
   cannot vary a radius, because the radius acts upstream of the forecast; a radius arm
   needs the engine back-test re-run per candidate.
5. The two published pairs differ in three things, not one. 89/82 on 2,915: FITTED_KW in
   bt2_claimset (it=800, minleaf=5, leaves=63), Sabre throughout, reproduces 89.2/81.4 (log
   line 120 context, docstring). 92/86 on 6,524: CALIB_KW in bt2_mixed_basis (it=1600,
   minleaf=3, leaves=95, the "memorisation rule" declared at log line 131, V1.3-RULE),
   mixed basis (595 US domestic on DOT DB1B, 5,929 on Sabre MIDT, line 138), measured on
   sklearn 1.7.2 and airportsdata 20260315, an environment the repo never declared (lines
   378 and 387). Line 137 (MIXED-EFFECT) records the same config Sabre-throughout at
   92.6/86.1 and mixed at 91.9/85.6. The script that built it is bt2/bt2_mixed_basis.py
   (line 391, MIXED-BASIS-FOUND); it was never re-run on the declared environment.
6. The declared baseline (line 389, 13 Aug; reproduced by the controller 22 Sep,
   E:\Avia\probe\claimset-22Sep.log): calibrated 83.2/70.0, blind 60.9, tier A 88.2,
   portfolios of 10 and 20 87.7/93.2, segments 72.6/39.8, n=6,524, Sabre throughout,
   FITTED_KW, build python 3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0,
   airportsdata 20260803.

## Conflicts seen (for the controller)

W10-RULINGS item 1 asks W10 to fit radius and capture in one pass through
search_adjustments.py with its cross-validation control, on the claimset baseline, with the
whole claimset as the pass mark. As the code stands:

- The claimset cannot move when the radius moves (facts 1 and 2 above). A radius arm would
  return 83.2/70.0 on every setting, which passes rule (d) by construction and measures
  nothing. Reporting that as "no worsening" would be a false result.
- search_adjustments.py cannot fit a radius (fact 4). The only instrument that measures the
  radius is app/backtest.py, the QSI engine's own back-test, whose blind figure is 16.9%
  within +-20% on the 8 Aug control run (bt2/README.md), and that is a different engine
  from the one the claim describes and, since 22 Sep, from the one the product runs.
- The symptom (BHX inside London) comes from the competing-airport radius in cortex_app,
  not from haul_radius_km (fact 3), and is already assigned to W2 under R6.

W10's view, for the controller and John to rule on. (A) Treat item 1 as a competing-set
and display question, owned by W2 under R6, with rule (b) applied there: the constant
changes on by default or not at all. W10 records in the calibration record, with the greps,
that the catchment radius does not enter the published figures, so the accuracy condition
of the 22 Sep ruling is met by construction and stated as such. (B) If John wants the QSI
engine measured anyway, W10 runs app/backtest.py on the six-year set at 220 km and at the
banded values (FSC short haul 100, LCC short haul and all long haul 150), scores each arm
with search_adjustments.py's baseline row, and reports; cost is one timed arm first, and
it measures the fallback engine, not the client number. W10 recommends (A) and proceeds
with items 2 and 3 meanwhile. W10 runs nothing on item 1 until re-ruled.

## John's specification, verbatim

Not yet pasted. If John pastes the original catchment radius text into the W10 chat it
goes here unchanged for the controller to replace item 1.

## Runs this session

None. Log lines: none. bt2/bt2_experiments.log unchanged (515 lines, last 15 Aug).

## Blocks for John

Block 1, pull and confirm HEAD (W10 read 7c15c3d from the mounted clone).

**DevPC**
```
cd C:\AviaDev
git pull
git log -1 --oneline
```

Block 2, item 2, the baseline. Same script, sample, target and cohorts as the controller's
22 Sep run. Runs where E: is visible. Paste the window output into the W10 chat; the
Tee-Object file is the workstation's copy.

**Workstation Actual**
```
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_TARGET  = "nonstop"
py -3.12 bt2_paths.py
py -3.12 bt2_claimset.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\claimset-W10-22Sep.log
```

Block 3, item 3, the mixed basis on the declared environment, run only after block 2 has
matched. Same shell, same variables.

**Workstation Actual**
```
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_TARGET  = "nonstop"
py -3.12 bt2_mixed_basis.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\mixed-W10-22Sep.log
```

What W10 checks in the pastes: block 2 must read n=6,524, target nonstop, build sklearn
1.9.0 and airportsdata 20260803, and the eight figures to the decimal; any difference stops
W10 and goes to the controller. Block 3 prints four lines under section 2; the pair that
reproduces 92/86 would be "mixed, US domestic on DOT" calibrated within +-20% and the
+-10% line below it. Expected, from the sklearn sensitivity at line 378: lower than 92/86.

## Commit block

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/CALIBRATION-RECORD-2026.md routes/COMMIT-MSG-22Sep2026-w10-session1.txt
git commit -F routes/COMMIT-MSG-22Sep2026-w10-session1.txt
git push
```
