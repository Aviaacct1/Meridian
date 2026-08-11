# Avia Solutions - the connecting back-test, three arms. 11 August 2026.
# Revised 12 August 2026: the route set is now PINNED, and --jobs / --preagg are on every arm.
# See "WHAT CHANGED AND WHY" at the foot of this file.
#
# RUN ON THE WORKSTATION, C:\src\meridian, after a git pull. Not on the Dev PC and not from a
# Cowork session: discovery alone scans the whole OAG history and takes minutes, and each arm is
# tens of minutes. Every line here is ONE LINE; nothing to continue.
#
# WHAT IS BEING TESTED, and why it is three arms and not two.
#
#   arm 1  control      the flat connecting feed, as it shipped before 11 August
#   arm 2  QSI feed     the per-market QSI share, departure time taken from each route's FLOWN
#                       schedule so the placeholder and the optimiser are out of the question
#   arm 3  no floor     split_share off. The connectivity floor was sized for the FLAT feed,
#                       which under-credited transfer traffic at non-US hubs. Whether it is
#                       still right under the QSI feed is a SEPARATE question from whether the
#                       QSI feed is right, and folding them into one arm leaves no way to say
#                       which moved the score.

cd C:\src\meridian
git pull
git log --oneline -3          # confirm the commit arrived; if not, stop

py -3.12 -m pip install -r app\requirements.txt

$env:AVIA_LOCAL_CACHE    = "E:\Avia"
$env:AVIA_OAG            = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE          = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

Test-Path $env:AVIA_OAG
Test-Path $env:AVIA_SABRE

# THE SIX-YEAR WAVE CACHE, not the four-year one in the repo folder. The 4-year covers flown
# years 2017-2019 and 3,602 dep-arr-year pairs; the 6-year covers 2016-2019 plus 2024 and 2025,
# and 5,798. A route with no flown schedule falls back to the flat feed and appears UNCHANGED IN
# BOTH ARMS, so the thinner cache waters the comparison down for nothing.
$WAVE = "E:\Avia\qsi-tool\app\qsi_wave_cache_6yr.duckdb"
Test-Path $WAVE

# THE PRE-AGGREGATION STORE. Turns the per-route Sabre full scans into point lookups. It engages
# on every arm and is a read-path change only, so it cannot move a score. If Test-Path returns
# False, STOP and build it with build_preagg.py rather than running without it.
$PREAGG = "E:\Avia\preagg.duckdb"
Test-Path $PREAGG

$ROUTES = "E:\Avia\backtest_routes_11Aug2026.json"

cd C:\src\meridian\app

# ---- step 0: discover ONCE, filter ONCE, and PIN the route set ----
# Two reasons, and the first is correctness rather than speed.
#
# 1. DISCOVERY DOES NOT RETURN IDENTICAL MEMBERSHIP RUN TO RUN. backtest.py says so at line 928
#    and records the case that proved it: 145 routes against 83 when a fresh discovery was
#    key-matched to an earlier one. compare_backtest_arms.py pairs on the routes ALL arms scored,
#    so three unpinned discoveries silently shrink the paired sample and the arms stop being a
#    controlled comparison. The pin makes all three arms run the same routes by construction.
# 2. It is also the whole of the slow serial phase. Run it once, not three times.
#
# AVIA_DUCKDB_THREADS IS DELIBERATELY NOT SET HERE. This phase is one process doing whole-table
# scans and it wants every core. It is pinned to 1 for the arms below, where twelve workers each
# opening a multi-threaded connection would oversubscribe the box.
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --routes-file $ROUTES --discover-only

# Read the route count and the launch-year split before going on. If the pin already exists from
# an earlier attempt, discovery is bypassed and the count is whatever was pinned then: delete the
# file to rebuild it.

$env:AVIA_DUCKDB_THREADS = "1"

# --resume on every arm. Each finished route is flushed to the CSV as it completes, so an
# interruption never loses work and re-running the identical command carries on where it stopped.
# If a run is cut off, just run the same line again.
#
# THE RESUME TRAP: resume keys on (dep, arr, year) and knows NOTHING about the arm's switches, so
# a CSV left over from a run with different settings is reused in silence. Each arm below writes
# its own file; check none of the three already exists before the first run.
Get-ChildItem backtest_control_11Aug2026.csv, backtest_qsifeed_11Aug2026.csv, backtest_nofloor_11Aug2026.csv -ErrorAction SilentlyContinue

# ---- arm 1: control, the flat feed ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --routes-file $ROUTES --preagg $PREAGG --jobs 12 --resume --out backtest_control_11Aug2026.csv

# ---- arm 2: the QSI feed ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --routes-file $ROUTES --preagg $PREAGG --jobs 12 --qsi-feed --wave-cache $WAVE --resume --out backtest_qsifeed_11Aug2026.csv

# ---- arm 3: the QSI feed with the connectivity floor OFF ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --routes-file $ROUTES --preagg $PREAGG --jobs 12 --qsi-feed --wave-cache $WAVE --no-split-floor --resume --out backtest_nofloor_11Aug2026.csv

# ---- the answer ----
# The three-way call first: it intersects all three arms, so the level table is one common sample
# and the three rates are comparable line for line. Then the two pairwise calls, because McNemar
# is run between the FIRST TWO files given and each pair has its own paired sample.
py -3.12 ..\bt2\compare_backtest_arms.py backtest_control_11Aug2026.csv backtest_qsifeed_11Aug2026.csv backtest_nofloor_11Aug2026.csv
py -3.12 ..\bt2\compare_backtest_arms.py backtest_control_11Aug2026.csv backtest_qsifeed_11Aug2026.csv
py -3.12 ..\bt2\compare_backtest_arms.py backtest_qsifeed_11Aug2026.csv backtest_nofloor_11Aug2026.csv


# ============================ HOW TO READ IT ============================
#
# 1. BEFORE any score, find this line in the arm 2 and arm 3 output:
#
#      "QSI feed: N routes without a flown schedule (V1 fallback), M in-run fallbacks (errors)"
#
#    M MUST BE 0. If it is not, something is failing silently and the scores are meaningless.
#    N is the dilution: those routes fell back to the flat feed and are identical in both arms.
#    If N is more than about a third of the sample, rebuild the wave cache before concluding
#    anything, because most of the comparison is then comparing an arm against itself.
#    NOTE THE TIMING: this line prints at the END of the run, after the CSV is written. It cannot
#    be read early, so it is the first thing to look at when an arm finishes and before any score.
#
# 2. Read FORECAST over PURE P2P for the demand test and FORECAST over TOTAL OUTTURN for the
#    connecting change. The feed can only move the second one.
#
# 3. The verdict line is the point. "no effect" and "not measurable" both mean DO NOT SHIP IT on
#    this evidence. Only "MEASURABLE" is a result, and even then look at how many routes moved:
#    fewer than 30 changing side is underpowered whatever the p value says.
#
# 4. Findings are recorded in bt2/bt2_experiments.log ON THE DEV PC, then pushed and pulled. The
#    CSVs are output and do not belong in the repo. Never edit a tracked file on the Workstation.
#
#
# ==================== WHAT CHANGED AND WHY, 12 AUGUST ====================
#
# The 11 August version of this file omitted three things the same day's handover called for, and
# the first of them would have cost the experiment rather than the clock.
#
#   --routes-file   ADDED, with a --discover-only step to write it. Without it each arm runs its
#                   own discovery, the three route sets differ, and the paired sample the verdict
#                   rests on is smaller than it should be for no reason anyone would see.
#   --jobs 12       ADDED. It defaults to 1, so all three arms would have run single-process.
#   --preagg        ADDED. Without it every route full-scans Sabre.
#
# Also removed from the three arm lines: --years and --min-gcd. They are discovery-time filters
# and the pin has already applied them; leaving them on the arms is misleading rather than wrong.
#
# STILL OPEN, and John's call rather than a defect: the arms run launch years 2016-2019 only,
# while the six-year wave cache also covers 2024 and 2025. Adding 2024 would put post-COVID
# launches in the sample and the BT2 programme measured one extra cohort at +1.7 points. 2025
# launches cannot be graded, because the outturn year would be 2026 and Sabre stops at 2025.
#
# Avia Solutions Limited. All rights reserved.
