# Avia Solutions - the connecting back-test, three arms. 11 August 2026.
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

cd C:\src\meridian\app

# --resume on every arm. Each finished route is flushed to the CSV as it completes, so an
# interruption never loses work and re-running the identical command carries on where it stopped.
# If a run is cut off, just run the same line again.

# ---- arm 1: control, the flat feed ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --resume --out backtest_control_11Aug2026.csv

# ---- arm 2: the QSI feed ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --qsi-feed --wave-cache $WAVE --resume --out backtest_qsifeed_11Aug2026.csv

# ---- arm 3: the QSI feed with the connectivity floor OFF ----
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --qsi-feed --wave-cache $WAVE --no-split-floor --resume --out backtest_nofloor_11Aug2026.csv

# ---- the answer ----
# Pairs the arms on the routes ALL of them scored, reports median / +-20% / +-50% for each, and
# runs a McNemar test on the routes that changed side, so a net gain of four routes in a thousand
# is shown as the noise it is. Pairing matters: on 9 August two headline rates said one thing and
# the 3,697 paired routes said another.
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
