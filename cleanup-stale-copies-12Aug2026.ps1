# Avia Solutions - inventory the out-of-git app trees before anything is deleted. 12 August 2026.
#
# WHAT THIS FILE USED TO DO, AND WHY IT NO LONGER DOES IT. The first version deleted three app\
# trees outright, on the strength of the 11 August handover calling them "three out-of-git app
# copies" whose deletion "finishes that day's work". THE DRY RUN SHOWED THEY ARE NOT CODE COPIES.
# The OneDrive one holds venv\, data\, cases\, reference_tables\ and _archive_old_versions\, and at
# top level qsi_wave_cache_6yr.duckdb at 329MB, qsi_wave_cache.duckdb at 134MB,
# bias_correction_model.joblib, airport_attributes.json, cities5000.txt, served_2026-05-25.json and
# the bt_v1_6yr and bt_v2_6yr back-test artefacts. C:\Avia\qsi-tool\app and E:\Avia\qsi-tool\app are
# 38GB each and were never inventoried at all. Deleting them blind would have destroyed reference
# data and a deliberate archive.
#
# So this now REPORTS, and purges only what is regenerable. Nothing else is removed by any switch.
#
#     .\cleanup-stale-copies-12Aug2026.ps1                inventory, changes nothing
#     .\cleanup-stale-copies-12Aug2026.ps1 -PurgeCaches   remove venv, __pycache__, _dt_cache only
#
# IF POWERSHELL REFUSES TO RUN IT. "running scripts is disabled on this system" is the default
# execution policy, not a fault in the file, and every .ps1 in this repo hits it:
#     powershell -ExecutionPolicy Bypass -File .\cleanup-stale-copies-12Aug2026.ps1
# The standing fix, once per account, noting Carte and aviaremote1 have separate profiles:
#     Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# If that reports "overridden by a policy defined at a more specific scope", group policy is setting
# it and the Bypass form above is the way in.
#
# Avia Solutions Limited. All rights reserved.

param([switch]$PurgeCaches)

$ErrorActionPreference = "Stop"
Write-Host "Avia app-tree inventory$(if ($PurgeCaches) { ' - PURGING CACHES' } else { ' - report only, nothing will be changed' })`n"

$live = @("C:\AviaDev", "C:\src\meridian")
$oneDriveProject = "C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool"
$targets = @("C:\Avia\qsi-tool\app", "E:\Avia\qsi-tool\app", (Join-Path $oneDriveProject "app"))

# Regenerable: a virtual environment, bytecode and a scratch cache all rebuild from the repo and a
# pip install. Everything else is treated as possibly irreplaceable until someone says otherwise.
$regenerable = @("venv", ".venv", "__pycache__", "_dt_cache", "preagg.duckdb.tmp")
# Anything matching these is DATA and its presence blocks deletion of the tree that holds it.
$dataExt = @(".duckdb", ".csv", ".json", ".joblib", ".pkl", ".xlsx", ".xlsm", ".pptx", ".docx", ".txt", ".parquet")

function Show-Tree([string]$path) {
    Write-Host "`n=== $path"
    if (-not (Test-Path $path)) { Write-Host "    not on this machine"; return }
    if (Test-Path (Join-Path $path ".git")) { Write-Host "    CONTAINS .git - this is a repo, not a stale copy. Left alone."; return }

    $all = Get-ChildItem $path -Recurse -File -Force -ErrorAction SilentlyContinue
    $regen = $all | Where-Object { $p = $_.FullName.Substring($path.Length); ($regenerable | Where-Object { $p -like "*\$_\*" }).Count -gt 0 -or $_.Extension -eq ".pyc" }
    $keep  = $all | Where-Object { $regen -notcontains $_ }
    $data  = $keep | Where-Object { $dataExt -contains $_.Extension } | Sort-Object Length -Descending
    $code  = $keep | Where-Object { $_.Extension -in @(".py", ".ps1", ".html", ".md") }

    $mb = { param($x) [math]::Round((($x | Measure-Object Length -Sum).Sum / 1MB), 1) }
    Write-Host ("    total        {0,7} files  {1,10} MB" -f $all.Count, (& $mb $all))
    Write-Host ("    regenerable  {0,7} files  {1,10} MB   venv, __pycache__, _dt_cache, .pyc" -f $regen.Count, (& $mb $regen))
    Write-Host ("    code         {0,7} files  {1,10} MB" -f $code.Count, (& $mb $code))
    Write-Host ("    DATA         {0,7} files  {1,10} MB   <- blocks deletion of this tree" -f $data.Count, (& $mb $data))
    if ($data) {
        Write-Host "    largest data files:"
        $data | Select-Object -First 8 | ForEach-Object {
            Write-Host ("      {0,8:N1} MB  {1}" -f ($_.Length / 1MB), $_.FullName.Substring($path.Length + 1))
        }
    }
    if ($PurgeCaches -and $regen.Count -gt 0) {
        foreach ($d in $regenerable) {
            $t = Join-Path $path $d
            if (Test-Path $t) { Remove-Item $t -Recurse -Force; Write-Host "    PURGED  $d" }
        }
        Get-ChildItem $path -Recurse -File -Filter "*.pyc" -Force -ErrorAction SilentlyContinue | Remove-Item -Force
        Write-Host "    purge complete. Data and code untouched."
    }
}

Write-Host "1. THE OUT-OF-GIT APP TREES"
foreach ($t in $targets) { Show-Tree $t }

Write-Host "`n`n2. GIT REPOS ON THIS MACHINE, and which of them is live"
foreach ($p in ($live + @("C:\Avia\qsi-tool", "E:\Avia\qsi-tool"))) {
    if (-not (Test-Path $p)) { Write-Host ("    {0,-22} not on this machine" -f $p); continue }
    $isRepo = Test-Path (Join-Path $p ".git")
    $ca = Join-Path $p "app\cortex_app.py"
    # (Get-Content).Count counts EVERY line. Measure-Object -Line skips blanks, which is why the
    # first version of this script printed 1982 where the note beside it said 2,154. Same file.
    $lines = if (Test-Path $ca) { (Get-Content $ca).Count } else { "no cortex_app.py" }
    $flag = if ($isRepo) { "repo" } else { "NOT a repo" }
    Write-Host ("    {0,-22} {1,-11} cortex_app.py {2} lines" -f $p, $flag, $lines)
}
Write-Host "`n    Both live trees should read the SAME line count. A repo reading fewer is a stale"
Write-Host "    clone that someone could run by mistake: pull it or delete it, do not leave it."

Write-Host "`n`n3. WHAT TO DO WITH WHAT IS ABOVE"
Write-Host "    - regenerable: safe to purge, rebuilds from the repo plus pip install."
Write-Host "    - DATA: decide file by file. Anything not already on the data root should be moved"
Write-Host "      there, not deleted. The wave caches, the bt_v1/v2 artefacts, airport_attributes,"
Write-Host "      bias_correction_model and reference_tables are the ones to look at first."
Write-Host "    - code: compare against the repo before removing anything. It is five days behind,"
Write-Host "      which means it is superseded, not that it is empty."
if (-not $PurgeCaches) { Write-Host "`nReport only. -PurgeCaches removes the regenerable folders and nothing else." }
