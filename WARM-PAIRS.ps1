# =====================================================================
#  Demo warm list - WORKSTATION, against its own localhost (no Cloudflare,
#  no 100-second limit). 19 August 2026: Sabre will be asked to name a live
#  city pair on Thursday; each run pays the per-origin catchment, drive and
#  board caches once, so any pair sharing a warmed origin answers fast.
#  Pairs chosen through Sabre's eyes: the demo cases, the recents, and the
#  famous markets a data vendor reaches for. Portal must be running.
#
#  Run:  powershell -NoProfile -ExecutionPolicy Bypass -File C:\src\meridian\WARM-PAIRS.ps1
# =====================================================================
$portal = if ($env:MERIDIAN_URL) { $env:MERIDIAN_URL } else { "http://localhost:8010" }
$h = @{}
if ($env:QSI_PASSWORD) {
    $tok = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("warm:" + $env:QSI_PASSWORD))
    $h["Authorization"] = "Basic $tok"
}
$pairs = "SJC,TPE,BR", "GOA,JFK,", "EDI,AUS,", "BRS,BOS,", "LHR,JFK,BA", "MAN,JFK,",
         "FRA,JFK,LH", "KRK,LHR,FR", "SIN,LHR,SQ", "DXB,JFK,EK", "NRT,SFO,NH", "AMS,JFK,KL"
foreach ($p in $pairs) {
    $a = $p.Split(",")
    $u = "$portal/api/forecast?origin=$($a[0])&dest=$($a[1])&season=annual"
    if ($a[2]) { $u += "&airline=$($a[2])" }
    Write-Host -NoNewline "warming $($a[0])-$($a[1])$(if($a[2]){' ('+$a[2]+')'}) ... "
    $t0 = Get-Date
    try {
        Invoke-RestMethod $u -Headers $h -TimeoutSec 900 | Out-Null
        Write-Host ("done in {0:n0}s" -f ((Get-Date) - $t0).TotalSeconds)
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)"
    }
}
Write-Host "Warm list complete. A repeat run should show every pair in a few seconds."
