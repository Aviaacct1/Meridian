# Avia Solutions - Engine V1 vs V2 A/B: does the schedule-quality QSI feed forecast better?
# ==========================================================================================
# Written 8 August 2026. The question John needs answered before departure time can become a
# search dimension in the optimiser: on a route's ACTUAL flown departure time, does building
# the connecting feed against real hub wave boards with MCT applied predict the outturn better
# than the shipped V1 feed?
#
# WHY BOTH ARMS RUN. bt_v1_baseline.csv exists but is dated 3 July 2026, and eight engine
# commits landed after it: the induced floor extension to FSC hubs, the market-size-keyed P2P
# trim, the total-preserving P2P/connecting re-split, region-weighted hub connectivity, the
# calibrated induced LF and fare tables, and the DOT integration. Comparing a V2 run today
# against that baseline would credit or blame the feed for five weeks of other work. So the
# baseline is re-run on the same code, the same day, with the same flags. The ONLY difference
# between the two arms is --qsi-feed.
#
# WHY k IS NOT SWEPT HERE. --qsi-k is a LEVEL parameter (default 0.06, its own help says
# "calibrate to outturn"), and the Claude memory qsi-schedule-banking records the wave-timed
# feed as already back-tested once and parked for not beating V1. If that test ran on an
# uncalibrated k then "did not beat V1" may be a level problem rather than a mechanism problem.
# Sweeping k blind triples the runtime and muddies the primary comparison. Instead: run the two
# arms, read the V2 arm's median forecast-to-outturn ratio, and set k from it analytically. The
# k answer falls out of the arithmetic rather than out of a search.
#
# WHY 2016-2019. The clean sample: Covid-hit 2020-2023 excluded, and 2024-2025 left alone
# because overnight_backtests.bat reserves them blind. Do not widen this without deciding to.
#
# Usage, from the app folder of a clone:
#     powershell -ExecutionPolicy Bypass -File .\run_qsi_feed_ab.ps1
#     powershell -ExecutionPolicy Bypass -File .\run_qsi_feed_ab.ps1 -Jobs 12 -MemTotal 64
#
# Safe to re-run: both arms use --resume, so an interruption never restarts from scratch and a
# completed arm is skipped.
#
# Avia Solutions Limited. All rights reserved.

param(
    # Where the stores live on THIS machine, and the only thing that differs between hosts.
    # config.py resolves every store through _env_path from AVIA_LOCAL_CACHE, so nothing is
    # hardcoded in the tool and provisioning a new host is: clone the repo, copy the data root,
    # set the variable.
    #   Workstation : E:\Avia   (the second internal NVMe; everything lives under one root so it
    #                            can be identified and copied wholesale when further workstations
    #                            are stood up for commercial launch)
    #   Dev PC      : C:\Avia   (until the stores move; see the naming and structure register)
    [string]$DataDir    = "E:\Avia",
    [string]$TempDir    = "E:\Avia\duckdb_tmp",
    [string]$OutDir     = "E:\Avia\bt_ab_08Aug2026",

    # Workstation defaults: HP Z2 Tower G1i, Core Ultra 9 285K, 64GB. On the 16GB Dev PC use
    # -Jobs 4 -MemTotal 16 -MemReserve 8, per the DuckDB run rules.
    [int]$Jobs          = 12,
    [double]$MemTotal   = 64,
    [double]$MemReserve = 12,

    [string]$Years      = "2016,2017,2018,2019",

    # The launcher and its arguments are SEPARATE. PowerShell's call operator takes the
    # executable as its first token, so "py -3.12" passed as one string is looked up as a command
    # literally named "py -3.12" and fails with CommandNotFoundException. That is what happened on
    # the first run, 8 August 2026, after preflight had already passed.
    [string]$Python     = "py",
    [string]$PythonArgs = "-3.12"
)

$ErrorActionPreference = "Stop"
$app = $PSScriptRoot
$pyArgs = @()
if ($PythonArgs) { $pyArgs = $PythonArgs.Split(" ") }
New-Item -ItemType Directory -Force $TempDir | Out-Null
New-Item -ItemType Directory -Force $OutDir  | Out-Null
$log = Join-Path $OutDir "run.log"

function Say($m) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Write-Host $line
    Add-Content -Path $log -Value $line
}

# --- Preflight. Every one of these has cost somebody a night somewhere. -------------------
Say "PREFLIGHT"
$need = @(
    @{ p = Join-Path $DataDir "oag.duckdb";              why = "schedules" },
    @{ p = Join-Path $DataDir "sabre.duckdb";            why = "O&D" },
    @{ p = Join-Path $app     "qsi_wave_cache.duckdb";   why = "flown times and wave boards for --qsi-feed; WITHOUT IT V2 reads the OAG store live and the run takes far longer" }
)
$missing = @()
foreach ($n in $need) {
    if (Test-Path $n.p) {
        $gb = [math]::Round((Get-Item $n.p).Length / 1GB, 2)
        Say ("  OK       {0}  ({1} GB)" -f $n.p, $gb)
    } else {
        Say ("  MISSING  {0}  <- {1}" -f $n.p, $n.why)
        $missing += $n.p
    }
}
# preagg is optional: absent means full Sabre scans, which is slower but identical in result.
$preagg = Join-Path $app "preagg.duckdb"
$preaggArg = @()
if (Test-Path $preagg) { $preaggArg = @("--preagg", $preagg); Say "  OK       preagg present, point lookups instead of full Sabre scans" }
else { Say "  NOTE     preagg.duckdb absent: full Sabre scans, slower, same answer" }

if ($missing.Count -gt 0) {
    Say "STOPPING. Copy the files above from the Dev PC and re-run. Nothing has been written."
    exit 1
}

# Record what produced these numbers. A run that cannot say which code and which data made it
# is a run that cannot be defended six weeks later, which is the fault this whole exercise
# spent 8 August fixing.
Push-Location $app
$commit = (& git rev-parse --short HEAD 2>$null)
$branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
Pop-Location
Say ("PROVENANCE  commit {0} on {1}  |  host {2}  |  years {3}  |  jobs {4}" -f $commit, $branch, $env:COMPUTERNAME, $Years, $Jobs)

# --- The two arms. Identical but for --qsi-feed. ------------------------------------------
$common = @(
    "--oag",         (Join-Path $DataDir "oag.duckdb"),
    "--sabre",       (Join-Path $DataDir "sabre.duckdb"),
    "--years",       $Years,
    "--jobs",        $Jobs,
    "--mem-total",   $MemTotal,
    "--mem-reserve", $MemReserve,
    "--temp-dir",    $TempDir,
    "--resume"
) + $preaggArg

$v1Out = Join-Path $OutDir "bt_v1_08Aug2026.csv"
$v2Out = Join-Path $OutDir "bt_v2_qsifeed_08Aug2026.csv"

Say "ARM 1 of 2: V1, the shipped feed. This is the control and it must run on today's code."
& $Python @pyArgs (Join-Path $app "backtest.py") @common --out $v1Out 2>&1 | Tee-Object -Append -FilePath $log
Say ("ARM 1 done, exit {0}" -f $LASTEXITCODE)

Say "ARM 2 of 2: V2, --qsi-feed at the default k. The only flag that differs."
& $Python @pyArgs (Join-Path $app "backtest.py") @common --qsi-feed --wave-cache (Join-Path $app "qsi_wave_cache.duckdb") --out $v2Out 2>&1 | Tee-Object -Append -FilePath $log
Say ("ARM 2 done, exit {0}" -f $LASTEXITCODE)

Say "BOTH ARMS COMPLETE"
Say ("  control : {0}" -f $v1Out)
Say ("  test    : {0}" -f $v2Out)
Say "READ IN THIS ORDER, and read the fallback count FIRST."
Say "  1. the V1-fallback count in the ARM 2 output. --qsi-feed silently falls back to V1 on"
Say "     any route with no flown departure time in the wave cache. If most routes fell back,"
Say "     the arms are near-identical by construction and the comparison says nothing."
Say "  2. within +-20% on both arms, on the same routes only."
Say "  3. the V2 median forecast-to-outturn ratio. k is a level knob, so a systematic bias is"
Say "     read straight off it and k solved rather than searched."
