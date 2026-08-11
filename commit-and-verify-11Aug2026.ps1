# Avia Solutions - the 11 August 2026 connecting build: push it, verify it, back-test it.
# PowerShell. Every command is ONE LINE; no backtick continuations, because pasting those a line
# at a time is what broke the first attempt.
#
# ============================ THE TWO MACHINES, AND WHICH IS WHICH ============================
#
#   DEV PC        C:\AviaDev          a Meridian clone. WHERE THE CODE IS EDITED.
#                                     Cowork is attached here, so every file written by a Cowork
#                                     session lands here first and NOWHERE ELSE.
#
#   WORKSTATION   C:\src\meridian     a Meridian clone. WHERE EVERYTHING RUNS.
#                 E:\Avia             the data root: oag.duckdb 16.8GB, sabre.duckdb 16.4GB,
#                                     preagg, aci, db1b, t100 and the wave caches.
#
# CODE MOVES ONE WAY AND BY ONE MEANS: git push on the Dev PC, git pull on the Workstation.
# Never by copying a file between them. That is what produced the three out-of-git app trees
# dated 3 July that are still sitting on disk.
#
# A FILE WRITTEN BY COWORK DOES NOT EXIST ON THE WORKSTATION UNTIL IT IS PUSHED AND PULLED.
# That is not a subtlety, it is the thing that wasted two rounds on 11 August: the migration
# script was written to C:\AviaDev and the Workstation was told to run it before it had it.


# =====================================================================================
# PART 1  -  DEV PC (C:\AviaDev): review, commit, PUSH
# =====================================================================================

cd C:\AviaDev

# If git refuses with "Unable to create index.lock: File exists", a Cowork session left a stale
# lock behind. Nothing is corrupted; the file is orphaned. Check, then clear it.
Get-Process git -ErrorAction SilentlyContinue
Remove-Item C:\AviaDev\.git\index.lock -ErrorAction SilentlyContinue

git status --short
git diff --stat

git add app/cortex_app.py app/cortex_dashboard.html app/route_forecast.py app/requirements.txt app/verify_connecting_build.py bt2/compare_backtest_arms.py bt2/coord_check.py bt2/migrate_oag_asia_labels.py commit-and-verify-11Aug2026.ps1 commit-message-10-11Aug2026.txt

git status --short
git commit -F commit-message-10-11Aug2026.txt
git push

# Confirm it left the machine. Expect the new commit above 58c04a6 and no ahead/behind marker.
git log --oneline -3
git status -sb


# =====================================================================================
# PART 2  -  WORKSTATION (C:\src\meridian): PULL, then prove it
# =====================================================================================

cd C:\src\meridian
git pull

# Confirm the pull actually brought the commit. If this does not name it, STOP: nothing below
# is running the code you think it is.
git log --oneline -3

# Bring the environment up to the pinned set. airportsdata is pinned at 20260803 because it
# supplies every coordinate the engine uses and an unpinned release moves the QSI share.
py -3.12 -m pip install -r app\requirements.txt

$env:AVIA_LOCAL_CACHE    = "E:\Avia"
$env:AVIA_OAG            = "E:\Avia\oag.duckdb"
$env:AVIA_SABRE          = "E:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

# Both must be True before anything else runs.
Test-Path $env:AVIA_OAG
Test-Path $env:AVIA_SABRE

py -3.12 app\test_qsi_score.py
py -3.12 app\env_report.py
py -3.12 bt2\coord_check.py
py -3.12 app\verify_connecting_build.py --quick
py -3.12 app\verify_connecting_build.py

# Expect: store vintage OAG week 2026-05-25, Sabre year 2025, then ALL 40 CHECKS PASSED.
#
# econ_baseline.py is deliberately NOT in this list. It REWRITES app\econ_baseline.json, so
# running it without the stores overwrites the golden record with failures. Run it only here,
# with the environment above set. If it has already been run somewhere without them:
#   git checkout -- app/econ_baseline.json


# =====================================================================================
# PART 3  -  WORKSTATION: the OAG store migration.  ALREADY DONE 11 August 2026.
# =====================================================================================

# Folds the Asia part-month labels (p01/p16/p23) into their parent month, so every monthly
# label becomes a complete seven-region world. Verified on 11 August: 332,978,415 rows before
# and after, 53 labels folded, 27,397,091 rows relabelled, 0 part labels left, 26 months now
# complete. Re-running --check is harmless and will report "nothing to migrate".

cd C:\src\meridian
py -3.12 bt2\migrate_oag_asia_labels.py --check
# py -3.12 bt2\migrate_oag_asia_labels.py --apply      # done; only needed on a rebuilt store


# =====================================================================================
# PART 4  -  WORKSTATION: the back-test, three arms
# =====================================================================================

cd C:\src\meridian\app

# USE THE SIX-YEAR WAVE CACHE. The 4-year cache covers flown years 2017-2019 and 3,602
# dep-arr-year pairs; the 6-year covers 2016-2019 plus 2024 and 2025, and 5,798. A route with
# no flown schedule falls back to the flat feed and appears unchanged in BOTH arms, so the
# thinner cache waters the comparison down for no reason.
$WAVE = "E:\Avia\qsi-tool\app\qsi_wave_cache_6yr.duckdb"
Test-Path $WAVE

# --resume on every arm: each finished route is flushed as it completes, so an interruption
# never loses work and re-running the same command carries on where it stopped. These runs are
# tens of minutes; discovery alone scans the whole OAG history.

py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --resume --out backtest_control_11Aug2026.csv

py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE --years 2016,2017,2018,2019 --min-gcd 1500 --qsi-feed --wave-cache $WAVE --resume --out backtest_qsifeed_11Aug2026.csv

# THE ANSWER, one command. Pairs the arms on the routes BOTH scored and runs a McNemar test on
# the routes that changed side, so a net gain of four routes in a thousand is shown as noise.
py -3.12 ..\bt2\compare_backtest_arms.py backtest_control_11Aug2026.csv backtest_qsifeed_11Aug2026.csv

# Read this line in the arm 2 output BEFORE any score:
#   "QSI feed: N routes without a flown schedule (V1 fallback), M in-run fallbacks (errors)"
# N is the dilution. M must be 0.
#
# arm 3 is split_share, deliberately NOT folded into the two above: the feed changes are
# corrections and the floor is a judgement, and mixed together there is no way to say which
# moved the score. Run it by adding --feed-fix or by setting split_floor=0 through the API.


# =====================================================================================
# PART 5  -  WORKSTATION: results go back to the Dev PC the same way
# =====================================================================================

# The CSVs are OUTPUT, not code, and do not belong in the repo. Read the comparison, and if a
# finding needs recording it goes into bt2/bt2_experiments.log ON THE DEV PC, then push, then
# pull here. Never edit a tracked file on the Workstation: it is a run host, and an edit made
# here is the fourth out-of-git copy waiting to happen.
