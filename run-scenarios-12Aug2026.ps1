# Avia Solutions - the Workstation run pack for 12 August 2026 evening.
#
# Pull first. Nothing here has been run: Cowork attaches the Dev PC and cannot execute on either
# machine, so every figure below is unmeasured until you produce it.
#
# Every command is ONE LINE. A fresh shell loses the environment, which cost three runs on
# 12 August, so run the four settings again in any new window.
#
#     powershell -ExecutionPolicy Bypass -File .\run-scenarios-12Aug2026.ps1
#
# or paste the lines by hand, which is what the four settings exist for.

# ---------------------------------------------------------------------------------------------
# 1. The environment. Four settings, every session.

$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_OAG = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

# The BT2 artefacts. Without this a run writes data into the repo, which is the thing the tool
# standard exists to stop.
$env:AVIA_BT2_DIR = "E:\Avia\bt2_relaxed"

Write-Host "environment set: OAG $env:AVIA_OAG, Sabre $env:AVIA_SABRE, freq-sensitive $env:AVIA_FREQ_SENSITIVE"

# ---------------------------------------------------------------------------------------------
# 2. THE INPUT CHECK. Run this BEFORE anything else, because it decides whether the wiring can
#    proceed at all. It takes routes the training chain has already scored, asks the live path for
#    the same three numbers, and compares. A pass is a difference of zero on capa, qcx and legs_n.
#    bt2_wiring_test.py passed on 9 August and could not have caught this: it fed both sides from
#    the training rows and never called route_context.
#
#    Forty routes is forty OAG leg queries. Start there and widen if it passes.

Set-Location C:\src\meridian\app
py -3.12 bt2_input_check.py --cohort 2018 --n 40

# ---------------------------------------------------------------------------------------------
# 3. THE BASELINE, and read this before you read the result.
#
#    app/econ_baseline.json was captured on 10 August at 22:18 and it is STALE in two separate ways,
#    so `check` against it today would report about thirty moved fields and none of them would be a
#    regression.
#
#      THE ENGINE MOVED, legitimately. The frozen B789 7x case reads 67,308 each way at a load
#      factor of 0.578, which is exactly the 10 August dashboard screenshot at 134,616 two-way. The
#      12 August SJC-TPE-BASELINE entry has the same case at 203,840 two-way, capacity bound at the
#      87.5% cap. Between the two came the forecast-year default of 11 August and the connecting
#      build on top of it.
#
#      AND THE CASES MOVED. Two of the three are named "carrier seats" and CASES now passes 333 for
#      the B77W and 306 for the A359. The frozen file records 380 and 336, which are the generic
#      table figures, so it was captured before the seats argument was passed. The frozen numbers
#      describe different cases from the ones the file names.
#
#    So the baseline is RE-CAPTURED at the current commit rather than checked against. The three
#    figures it should return, from SJC-TPE-BASELINE on commit 718e143, two-way: BR B77W 4x 121,212
#    with P2P 54,486 and connecting 66,726; CI A359 5x 139,230 with 62,586 and 76,644; CI B789 7x
#    203,840 with 91,630 and 112,210. All three are CAPACITY BOUND at the plan cap, so they are
#    seats times 0.875 and not a demand forecast. If the re-capture does not return those, the
#    consolidation moved something and that is the finding of the evening.

py -3.12 econ_baseline.py capture

# ---------------------------------------------------------------------------------------------
# 4. THE SCENARIO RUNNER. A file of cases in, a table out, no Python written by the tester.
#    app/cases_sjc_tpe.json carries sixteen cases: China Airlines, EVA, Starlux, United and Delta on
#    SJC-TPE at four to seven weekly across 2027 and 2028, one case with the connectivity floor on
#    as it ships, SFO-TPE as a served control, and SJC-LHR and GOA-JFK as other routes.
#
#    Seat counts are the carriers' own configurations measured from OAG 2025 by capacity_frame, not
#    the generic type table. Growth is the post-recovery path at 7% a year, because the engine's
#    default taper measures a 20.00% CAGR, which is the clamp ceiling and a recovery burst.
#
#    It refuses to run without AVIA_FREQ_SENSITIVE, refuses to write a table in which any case
#    errored, and stops on a payload key it does not recognise rather than leaving a blank column.
#
#    WATCH STARLUX. JX was founded after 2018, is absent from the 2018 carrier_home reference, and
#    was once silently deleted from the one route it obviously belongs on. Its two cases must return
#    numbers and a HOME traffic-rights verdict, not a blank.

py -3.12 scenario_runner.py cases_sjc_tpe.json

# The frequency ladder to hold against the handover table. With the floor off, on the analyst's
# 12:00 schedule with Southwest a partner, 2027 at 4x should read 109,764 two-way demand against
# 127,296 seats, which is 86.2%. That figure is the check on the whole run: if it moves, say so
# before reading anything else in the table.

Write-Host "done. The results table sits beside the cases file as cases_sjc_tpe_results.csv."
