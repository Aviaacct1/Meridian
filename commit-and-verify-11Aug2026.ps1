# Avia Solutions - verify the 11 August 2026 connecting build, then back-test it.
# PowerShell. Every command is ONE LINE: no backtick continuations, because pasting them a
# line at a time is what broke the first attempt.
#
# WHERE THINGS ARE, checked on 11 August rather than assumed:
#
#   WORKSTATION   C:\AviaDev            a Meridian clone
#                 E:\Avia               THE DATA ROOT. oag.duckdb 16.8GB, sabre.duckdb 16.4GB,
#                                       preagg, aci, db1b, t100, and the wave caches
#                 C:\Avia               a second copy of the same stores, same sizes, mtimes
#                                       seconds apart. Both give identical results; E: is the one
#                                       to use because the workstation is built around it
#   DEV PC        C:\src\meridian       a Meridian clone, NO STORES
#
# So the verification and the back-test run on the WORKSTATION. On the dev PC they can only fail,
# and they fail on a missing path rather than on anything to do with the code.


# =====================================================================================
# PART 1  -  DEV PC: edit, commit, push.  (Done for this change set: commit 58c04a6.)
# =====================================================================================

cd C:\src\meridian
git status
git add -A
git commit -F commit-message-9-11Aug2026.txt
git push

# If git refuses with "Unable to create index.lock: File exists", a Cowork session has left a
# stale lock. Check nothing is running, then clear it:
#   Get-Process git -ErrorAction SilentlyContinue
#   Remove-Item .git\index.lock


# =====================================================================================
# PART 2  -  WORKSTATION: pull, then prove the repo produces the 11 August numbers
# =====================================================================================

cd C:\AviaDev
git pull

$env:AVIA_LOCAL_CACHE    = "E:\Avia"
$env:AVIA_OAG            = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE          = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

# Confirm the paths before running anything. Both must be True.
Test-Path $env:AVIA_OAG
Test-Path $env:AVIA_SABRE

py -3.12 app\test_qsi_score.py
py -3.12 app\env_report.py
py -3.12 app\verify_connecting_build.py --quick
py -3.12 app\verify_connecting_build.py

# Expect: store vintage OAG week 2026-05-25, Sabre year 2025, then
#         ALL 35 CHECKS PASSED  (39 with the optimiser section).
# Confirmed on E:\Avia on 11 August 2026.
#
# econ_baseline.py is deliberately NOT in this list. It REWRITES app\econ_baseline.json, so
# running it without the stores overwrites the golden record with failures. Run it only on the
# workstation with the environment set above, and if it has already been run elsewhere:
#   git checkout -- app/econ_baseline.json


# =====================================================================================
# PART 3  -  only once Part 2 is green: the back-test, three arms
# =====================================================================================

cd C:\AviaDev\app

# USE THE SIX-YEAR WAVE CACHE. There are two, and the difference decides how much of the test
# is real. The 4-year cache in the repo folder covers flown years 2017-2019 and 3,602 dep-arr-year
# pairs; the 6-year cache on E: covers 2016-2019 plus 2024 and 2025, and 5,798 pairs. A route with
# no flown schedule falls back to the flat feed and appears unchanged in BOTH arms, so the thinner
# cache waters the comparison down for no reason.
$WAVE = "E:\Avia\qsi-tool\app\qsi_wave_cache_6yr.duckdb"
Test-Path $WAVE

# USE --resume ON EVERY ARM. Each finished route is flushed to the CSV as it completes, so an
# interruption never loses work and re-running the same command carries on where it stopped. These
# runs are tens of minutes; discovery alone scans the whole OAG history and takes minutes.

# arm 1, control: the flat connecting feed as it shipped
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --resume --out backtest_control_11Aug2026.csv

# arm 2: the QSI feed, departure time taken from each route's FLOWN schedule
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --qsi-feed --wave-cache $WAVE --resume --out backtest_qsifeed_11Aug2026.csv

# THE ANSWER, one command. Pairs the arms on the routes BOTH scored, reports the median and the
# +/-20% for each, and runs a McNemar test on the routes that changed side so a net gain of four
# routes out of a thousand is shown as the noise it is.
py -3.12 ..\bt2\compare_backtest_arms.py backtest_control_11Aug2026.csv backtest_qsifeed_11Aug2026.csv

# Read this line in the arm 2 output BEFORE reading any score:
#   "QSI feed: N routes without a flown schedule (V1 fallback), M in-run fallbacks (errors)"
# N is the dilution. M must be 0.
#
# arm 3 is split_share, and it is deliberately NOT folded into the two above: the feed changes are
# corrections and the floor is a judgement, and mixed together there is no way to say which moved
# the score.
