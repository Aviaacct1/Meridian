# Avia Solutions - Task 1, the calibrated model and the Cortex path on ONE sample. 12 August 2026.
#
# RUN ON THE WORKSTATION, C:\src\meridian, after a git pull. Every line here is ONE LINE.
# It runs no engine and scans no store, so it is seconds, not the minutes the bt2 chain takes.
#
# WHAT IT ANSWERS, and it is not one number. The 60.4% and the 16.8% differ in population, in
# target and in grading year, so this reports both engines on the pin's own two denominators,
# beside the calibrated model on its native terms, with McNemar on each.

cd C:\src\meridian
git pull
git log --oneline -3          # confirm the commit arrived; if not, stop

# All four, every time. A fresh shell loses them.
$env:AVIA_LOCAL_CACHE    = "E:\Avia"
$env:AVIA_OAG            = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE          = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

# The sample folder the published figures were measured on. bt2_forecast.py line 56 calls the
# relaxed folder the current production population, so it is the one to score.
$env:AVIA_BT2_DIR = "E:\Avia\bt2_relaxed"
$env:AVIA_APP_DIR = "C:\src\meridian\app"

Test-Path $env:AVIA_BT2_DIR
Test-Path E:\Avia\backtest_routes_11Aug2026.json

# The control arm, which is the Cortex path as it ships. Correct the path if the arm CSVs were
# written somewhere other than the app folder.
$ARM = "C:\src\meridian\app\backtest_control_11Aug2026.csv"
Test-Path $ARM

cd C:\src\meridian\bt2

py -3.12 bt2_pin_score.py --arm $ARM --pin E:\Avia\backtest_routes_11Aug2026.json --out E:\Avia\pin_score_12Aug2026.csv

# ============================ HOW TO READ IT ============================
#
# 1. THE CONTROL LINE FIRST, before any comparison. "native blind, its own population and its own
#    target" should read about 59.8%. That figure was reproduced on the Dev PC on 12 August, four
#    cohorts, relaxed sample, Sabre throughout, n=4,287, and it stands against the published 60.4%
#    which uses six cohorts and regrades US domestic launches onto the DOT. If it comes back far
#    from 59.8%, the sample folder or the cohort list is wrong and nothing below it means anything.
#
# 2. THE OVERLAP LINE. How many of the routes the arm graded the calibrated model can answer at
#    all. That number is the size of Task 2: the pin routes it cannot answer are the ones whose
#    market sits below the training floor, which is the leaked secondary airport case.
#
# 3. LOCAL MARKET is the like-for-like comparison. Both engines are forecasting the pair's own
#    passengers there and both are graded against the same pure P2P outturn.
#
# 4. WHOLE SECTOR is the client's quantity and the calibrated model is expected to read LOW on it,
#    because it forecasts the local market and the denominator includes connecting passengers.
#    That gap is the thing to decide about, not a fault to correct in the run.
#
# Avia Solutions Limited. All rights reserved.
