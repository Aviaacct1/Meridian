# =====================================================================
#  Meridian weekly data refresh - WORKSTATION scheduled-task target.
#  Item 8, 16 August 2026. Avia Solutions.
#
#  What it does, in order:
#    1. refresh_pickup.py --plan-only   the plan into the log, always
#    2. POST /api/refresh/begin         portal closes its store connections
#                                       and read-pauses /api (503, honest)
#    3. refresh_pickup.py --execute     the OAG monthly loads in the plan;
#                                       Sabre annual files are planned only,
#                                       never auto-run (a 7GB load is a
#                                       deliberate act)
#    4. POST /api/refresh/end           portal re-opens against the new files
#  The end call runs in a finally block, so a failed ingest can never leave
#  the portal paused. Status lands in refresh_status.json (the Watch page's
#  freshness line); the full transcript lands in the log folder.
#
#  Register the weekly task ONCE (any admin PowerShell; Monday 06:30 so the
#  weekend's Egnyte uploads are in before the working week):
#    schtasks /Create /TN "Meridian weekly refresh" /SC WEEKLY /D MON /ST 06:30 ^
#      /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\src\meridian\refresh_weekly.ps1"
#  The task must run as the logged-on user so E: (a per-logon mapping) and
#  QSI_PASSWORD are visible; refresh_pickup falls back to D:\Avia paths only
#  where config resolves them.
#
#  Environment (all optional):
#    MERIDIAN_URL        portal base, default http://localhost:8010
#    QSI_PASSWORD        sent as Basic auth to the origin gate, as set for the portal
#    AVIA_REFRESH_LOGS   log folder, default E:\Avia\refresh_logs
#  A watched run is this file with -PlanOnly first, then without, reading the
#  log between the two: RUNSHEET-refresh-commissioning-16Aug2026.md.
# =====================================================================
param([switch]$PlanOnly)

$stamp  = Get-Date -Format "yyyy-MM-dd_HHmm"
$logDir = if ($env:AVIA_REFRESH_LOGS) { $env:AVIA_REFRESH_LOGS } else { "E:\Avia\refresh_logs" }
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$log    = Join-Path $logDir "refresh_$stamp.log"
$portal = if ($env:MERIDIAN_URL) { $env:MERIDIAN_URL } else { "http://localhost:8010" }
$appDir = Join-Path $PSScriptRoot "app"

function Write-Log([string]$line) {
    $line | Tee-Object -FilePath $log -Append
}

function Invoke-Portal([string]$path) {
    # Best effort: a portal that is not running holds no connections, so an
    # unreachable portal is stated and the refresh proceeds.
    try {
        $headers = @{}
        if ($env:QSI_PASSWORD) {
            $tok = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("refresh:" + $env:QSI_PASSWORD))
            $headers["Authorization"] = "Basic $tok"
        }
        $r = Invoke-RestMethod -Method Post -Uri ($portal + $path) -Headers $headers -TimeoutSec 15
        Write-Log ("portal {0}: {1}" -f $path, $r.state)
    } catch {
        Write-Log ("portal {0} unreachable ({1}); continuing - a portal that is down holds no store connections" `
                   -f $path, $_.Exception.Message)
    }
}

Write-Log ("== Meridian watched refresh, {0} ==" -f $stamp)
& py -3.12 (Join-Path $appDir "refresh_pickup.py") 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) {
    Write-Log "PLAN FAILED (exit $LASTEXITCODE); nothing was changed. Read the log."
    exit $LASTEXITCODE
}
if ($PlanOnly) {
    Write-Log "Plan only; nothing was changed. Re-run without -PlanOnly to execute."
    exit 0
}

Invoke-Portal "/api/refresh/begin"
$code = 1
try {
    & py -3.12 (Join-Path $appDir "refresh_pickup.py") --execute 2>&1 | Tee-Object -FilePath $log -Append
    $code = $LASTEXITCODE
} finally {
    Invoke-Portal "/api/refresh/end"
}
Write-Log ("== refresh finished, exit {0}. Status: refresh_status.json; the Watch page shows it. ==" -f $code)
exit $code
