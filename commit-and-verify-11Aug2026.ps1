# Avia Solutions - commit the 11 August 2026 connecting build, then prove it.
# PowerShell. Run part 1 on the DEV PC, part 2 on the WORKSTATION.
# Nothing here is destructive: no reset, no checkout, no force.

# =====================================================================================
# PART 1  -  DEV PC: review, commit, push
# =====================================================================================

cd C:\AviaDev

# FIRST: clear the stale index lock.
#
# A read-only `git status` run from the Cowork session on 11 August left a zero-byte
# .git/index.lock behind. git status refreshes the index, which takes the lock, and the mount
# denies the unlink, so the lock is stranded. `git add` and `git commit` then refuse. Nothing
# is corrupted and no git process is running; the file is simply orphaned.
#
# Check no real git process is running, then remove it:
Get-Process git -ErrorAction SilentlyContinue        # expect nothing
Remove-Item C:\AviaDev\.git\index.lock -ErrorAction SilentlyContinue

# THE RULE, and it is already in the notes: never run git against the mounted repo from a
# Cowork session, not even a read-only status. Commit messages are handed over as files and
# every git command is run here, in a real shell.

# What is about to be committed. Read this before going further.
git status
git diff --stat

# The eight engine files, the acceptance test, the diagnostics, and the message itself.
git add app/cortex_app.py `
        app/cortex_dashboard.html `
        app/qsi_feed.py `
        app/qsi_score.py `
        app/route_feed.py `
        app/route_forecast.py `
        app/test_qsi_score.py `
        app/wave_cache.py `
        app/verify_connecting_build.py `
        bt2 `
        commit-message-9-11Aug2026.txt

# Confirm the staged set is what you expect, then commit and push.
git status --short
git commit -F commit-message-9-11Aug2026.txt
git push

# Should now read: your branch is ahead of 'origin/main' by 1 commit -> then level after the push.
git log --oneline -2
git status -sb


# =====================================================================================
# PART 2  -  WORKSTATION: pull, then prove the repo produces today's numbers
# =====================================================================================

cd C:\AviaDev          # or wherever the workstation clone lives
git pull

# The environment. AVIA_FREQ_SENSITIVE must be 1: without it qsi_share reads 0.3200
# instead of 0.2510 and every connecting figure below moves with it.
$env:AVIA_LOCAL_CACHE    = "C:\Avia"
$env:AVIA_OAG            = "C:\Avia\oag.duckdb"
$env:AVIA_SABRE          = "C:\Avia\sabre.duckdb"
$env:AVIA_FREQ_SENSITIVE = "1"

# 1. The frozen QSI method. Six tests, seconds.
py -3.12 app\test_qsi_score.py

# 2. The golden-file rollback record. Expect IDENTICAL or a named diff.
py -3.12 app\econ_baseline.py

# 3. Today's numbers. Circa 75 seconds on --quick, circa four minutes in full.
#    Exits non-zero on any failure, so it can be wired into a deploy step.
py -3.12 app\verify_connecting_build.py --quick
py -3.12 app\verify_connecting_build.py

# Expect: ALL 35 CHECKS PASSED (39 with the optimiser section).
# A failure here where step 1 passed is the environment, not the code: check
# AVIA_FREQ_SENSITIVE is 1 and that the stores are OAG week 2026-05-25 and Sabre 2025.


# =====================================================================================
# PART 3  -  only once part 2 is green: the back-test, three arms
# =====================================================================================

cd C:\AviaDev\app

# arm 1, control: the flat connecting feed as it shipped
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE `
    --years 2017,2018,2019 --min-gcd 1500 `
    --out backtest_control_11Aug2026.csv

# arm 2: the QSI feed, departure time taken from each route's FLOWN schedule
py -3.12 backtest.py --oag $env:AVIA_OAG --sabre $env:AVIA_SABRE `
    --years 2017,2018,2019 --min-gcd 1500 --qsi-feed `
    --wave-cache qsi_wave_cache.duckdb `
    --out backtest_qsifeed_11Aug2026.csv

# Read this line in the arm 2 output BEFORE reading any score:
#   "QSI feed: N routes without a flown schedule (V1 fallback), M in-run fallbacks (errors)"
# N is the dilution: those routes fall back to the flat feed and appear unchanged in BOTH
# arms. If N is more than about a third, rebuild the wave cache before drawing a conclusion.
#
# arm 3 is split_share, and it is deliberately NOT folded into the two above: the feed
# changes are corrections and the floor is a judgement, and mixed together there is no way
# to say which moved the score.
