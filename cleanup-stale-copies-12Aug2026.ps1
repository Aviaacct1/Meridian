# Avia Solutions - remove the out-of-git app copies and the superseded kickoffs. 12 August 2026.
#
# WHY. Open item 3 of the 11 August handover, never actioned, and it has now cost real time twice.
# Three app\ trees exist outside git. None is a repo. On 11 August two rounds were lost writing a
# file to one place and running it from another, and on 12 August a whole session was lost because
# Cowork attaches the OneDrive project folder automatically and a fresh session reasonably took the
# stale app\ inside it for the working copy: cortex_app.py there is 1,627 lines against the real
# 2,154 and predates the connecting build entirely.
#
# RUN IT ON BOTH MACHINES. The targets are split across them and the script skips whatever it does
# not find, so the same command is correct on each:
#     Dev PC        the OneDrive project folder
#     Workstation   C:\Avia\qsi-tool\app and E:\Avia\qsi-tool\app
#
# DRY RUN BY DEFAULT. It prints what it would do and changes nothing. Add -Execute to act.
#     .\cleanup-stale-copies-12Aug2026.ps1
#     .\cleanup-stale-copies-12Aug2026.ps1 -Execute
#
# Avia Solutions Limited. All rights reserved.

param([switch]$Execute)

$ErrorActionPreference = "Stop"
$mode = if ($Execute) { "EXECUTE" } else { "DRY RUN, nothing will be changed. Add -Execute to act." }
Write-Host "Avia stale-copy cleanup - $mode`n"

# The live trees. Anything at or under one of these is NEVER touched, whatever the target list says.
$protected = @("C:\AviaDev", "C:\src\meridian")

$oneDriveProject = "C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool"

function Test-Protected([string]$path) {
    $full = [System.IO.Path]::GetFullPath($path)
    foreach ($p in $protected) {
        if ($full -eq $p -or $full.StartsWith($p + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Remove-StaleTree([string]$path, [string]$why) {
    if (-not (Test-Path $path)) { Write-Host "  skip     $path  (not on this machine)"; return }
    if (Test-Protected $path) { Write-Host "  REFUSED  $path  (inside a live tree)"; return }
    # A tree carrying .git is a repo and is never a stale copy, whatever it is called.
    if (Test-Path (Join-Path $path ".git")) { Write-Host "  REFUSED  $path  (contains .git)"; return }
    $n = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $mb = [math]::Round(((Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB), 1)
    if ($Execute) {
        Remove-Item $path -Recurse -Force
        Write-Host "  REMOVED  $path  ($n files, $mb MB)  $why"
    } else {
        Write-Host "  would remove  $path  ($n files, $mb MB)  $why"
    }
}

function Remove-StaleFile([string]$path, [string]$why) {
    if (-not (Test-Path $path)) { Write-Host "  skip     $path  (not here)"; return }
    if (Test-Protected $path) { Write-Host "  REFUSED  $path  (inside a live tree)"; return }
    if ($Execute) { Remove-Item $path -Force; Write-Host "  REMOVED  $path  $why" }
    else { Write-Host "  would remove  $path  $why" }
}

# ---- 1. Move the wave caches to the data root BEFORE deleting the tree that holds them ----
# They are data, not code, and they must not live inside an app tree. run-backtest-11Aug2026.ps1
# already points at E:\Avia\qsi_wave_cache_pin_12Aug2026.duckdb, so nothing in the runbook breaks;
# the six-year cache is kept because it is expensive to rebuild and is still a valid artefact.
Write-Host "1. wave caches out of the app tree"
$waveSrc = "E:\Avia\qsi-tool\app"
if (Test-Path $waveSrc) {
    $caches = Get-ChildItem $waveSrc -Filter "*.duckdb" -File -ErrorAction SilentlyContinue
    if (-not $caches) { Write-Host "  none found in $waveSrc" }
    foreach ($c in $caches) {
        $dest = Join-Path "E:\Avia" $c.Name
        if (Test-Path $dest) { Write-Host "  skip     $($c.Name)  (already at E:\Avia)"; continue }
        if ($Execute) { Move-Item $c.FullName $dest; Write-Host "  MOVED    $($c.Name) -> E:\Avia\" }
        else { Write-Host "  would move    $($c.Name) -> E:\Avia\" }
    }
} else {
    Write-Host "  skip     $waveSrc  (not on this machine)"
}

# ---- 2. The three out-of-git app trees ----
Write-Host "`n2. out-of-git app trees"
Remove-StaleTree "C:\Avia\qsi-tool\app"            "3 July copy, predates the 8 August consolidation"
Remove-StaleTree "E:\Avia\qsi-tool\app"            "3 July copy, predates the 8 August consolidation"
Remove-StaleTree (Join-Path $oneDriveProject "app") "7 August copy, cortex_app.py 1,627 lines against the real 2,154"

# ---- 3. Referenced nowhere ----
Write-Host "`n3. unreferenced"
Remove-StaleTree (Join-Path $oneDriveProject "app_avia_style") "referenced nowhere"

# ---- 4. Superseded kickoffs, so nobody pastes the wrong one ----
# Superseded by "HANDOVER Meridian - one model and a scenario runner - 12Aug2026.md".
Write-Host "`n4. superseded kickoff prompts"
Remove-StaleFile (Join-Path $oneDriveProject "KICKOFF - Wire BT2 into Meridian - 13Aug2026.md") "superseded"
Remove-StaleFile (Join-Path $oneDriveProject "KICKOFF - One Meridian model - 13Aug2026.md")     "superseded"
Remove-StaleFile (Join-Path $oneDriveProject "KICKOFF prompt - Meridian back-test - 12Aug2026.md") "back-test is run and logged"

# ---- 5. Prove the live tree is untouched ----
Write-Host "`n5. the live tree, which must be unchanged"
foreach ($p in $protected) {
    if (Test-Path $p) {
        $git = if (Test-Path (Join-Path $p ".git")) { "repo OK" } else { "NO .git - CHECK THIS" }
        $ca = Join-Path $p "app\cortex_app.py"
        $lines = if (Test-Path $ca) { (Get-Content $ca | Measure-Object -Line).Lines } else { "absent" }
        Write-Host "  $p  $git  cortex_app.py $lines lines"
    } else {
        Write-Host "  $p  not on this machine"
    }
}

Write-Host "`nDone. $mode"
if (-not $Execute) { Write-Host "Re-run with -Execute to apply." }
