# Face-validity register probe (W1, 27 Sep 2026). Runs every register row as a fixed-input Run on one
# or more Meridian servers and writes one CSV row per (route, port): demand split, connecting share,
# ratio to the analyst's figure, and the economics basis (fare, cost, margin, contribution).
#
#   Workstation, a normal window, from C:\src\meridian:
#     powershell -ExecutionPolicy Bypass -File .\tools\probe_register.ps1 -Ports 8010 -Tag golive
#     powershell -ExecutionPolicy Bypass -File .\tools\probe_register.ps1 -Ports 8010,8011 -Tag feed
#
# The password is read with Read-Host and never stored. Output: E:\Avia\probe\register_<Tag>_<stamp>.csv
param([object[]]$Ports = @(8010), [string]$Tag = "run", [int]$Year = 2027, [string]$OutDir = "E:\Avia\probe")

# -File passes "8010,8011" as one string; -Command passes an array. Accept both.
$Ports = @($Ports | ForEach-Object { "$_" -split "[, ]+" } | Where-Object { $_ } | ForEach-Object { [int]$_ })
$pw = Read-Host "Meridian password" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw))
$hdr = @{ Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("meridian:$plain")) }
$plain = $null

# Register rows (routes/FACE-VALIDITY-REGISTER-25Sep2026.md section A). analyst = two-way figure as stated.
$rows = @(
  @{n="1";  o="NOC"; d="FRA"; al="LH"; ac="E195";   f=3; s="annual"; seats=0;   analyst=19379},
  @{n="2";  o="NOC"; d="BER"; al="LH"; ac="E195";   f=3; s="annual"; seats=0;   analyst=19277},
  @{n="3";  o="NOC"; d="MUC"; al="LH"; ac="E195";   f=3; s="annual"; seats=0;   analyst=15770},
  @{n="4";  o="NOC"; d="CDG"; al="AF"; ac="A223";   f=4; s="annual"; seats=0;   analyst=54390},
  @{n="5";  o="NOC"; d="ZRH"; al="WK"; ac="A20N";   f=1; s="summer"; seats=0;   analyst=9475},
  @{n="6";  o="NOC"; d="CPH"; al="SK"; ac="CRJ900"; f=2; s="annual"; seats=0;   analyst=16146},
  @{n="7";  o="NOC"; d="KTW"; al="W6"; ac="A320";   f=1; s="annual"; seats=0;   analyst=13538},
  @{n="8";  o="AHB"; d="IST"; al="TK"; ac="B738";   f=7; s="annual"; seats=0;   analyst=94631},
  @{n="9";  o="AHB"; d="IST"; al="XY"; ac="A21N";   f=7; s="annual"; seats=0;   analyst=106538},
  @{n="10"; o="AHB"; d="DXB"; al="XY"; ac="A21N";   f=7; s="annual"; seats=0;   analyst=106830},
  @{n="11"; o="AHB"; d="ADD"; al="ET"; ac="B38M";   f=3; s="annual"; seats=0;   analyst=44504},
  @{n="12"; o="AHB"; d="KWI"; al="J9"; ac="A21N";   f=3; s="annual"; seats=0;   analyst=46729},
  @{n="13"; o="AHB"; d="DEL"; al="XY"; ac="A21N";   f=4; s="annual"; seats=0;   analyst=61296},
  @{n="14"; o="EDI"; d="BOS"; al="B6"; ac="A21N";   f=7; s="annual"; seats=153; analyst=91062},
  @{n="15"; o="EDI"; d="JFK"; al="B6"; ac="A21N";   f=7; s="annual"; seats=153; analyst=94397},
  @{n="16"; o="EDI"; d="ATL"; al="DL"; ac="B763";   f=5; s="summer"; seats=211; analyst=58439},
  @{n="17"; o="EDI"; d="PVG"; al="HO"; ac="B789";   f=2; s="annual"; seats=322; analyst=52753},
  @{n="18"; o="EDI"; d="HKG"; al="HX"; ac="A333";   f=2; s="annual"; seats=311; analyst=52404},
  @{n="19"; o="EDI"; d="CAN"; al="CZ"; ac="B788";   f=2; s="annual"; seats=228; analyst=36391},
  @{n="20"; o="EDI"; d="DEL"; al="6E"; ac="A21N";   f=2; s="summer"; seats=220; analyst=39686},
  @{n="21"; o="BLQ"; d="JFK"; al="UA"; ac="A21X";   f=7; s="annual"; seats=0;   analyst=0},
  @{n="C";  o="SJC"; d="TPE"; al="CI"; ac="A359";   f=7; s="annual"; seats=0;   analyst=120000}
)

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$out = Join-Path $OutDir ("register_{0}_{1}.csv" -f $Tag, $stamp)
$res = New-Object System.Collections.Generic.List[object]

foreach ($x in $rows) {
  foreach ($port in $Ports) {
    $q = "origin=$($x.o)&dest=$($x.d)&airline=$($x.al)&aircraft=$($x.ac)&freq=$($x.f)&season=$($x.s)&forecast_year=$Year"
    if ($x.seats -gt 0) { $q += "&seats=$($x.seats)" }
    Write-Host ("row {0} {1}-{2} {3} {4} {5}x {6} on {7} ..." -f $x.n, $x.o, $x.d, $x.al, $x.ac, $x.f, $x.s, $port)
    $r = $null
    try { $r = Invoke-RestMethod -Headers $hdr -Uri "http://127.0.0.1:$port/api/forecast?$q" -TimeoutSec 900 }
    catch { Write-Host ("  FAILED: " + $_.Exception.Message); $res.Add([pscustomobject]@{row=$x.n; pair="$($x.o)-$($x.d)"; port=$port; error=$_.Exception.Message}); continue }
    $loc = [double]($r.demand.p2p_carried); $cnx = [double]($r.demand.connecting_carried)
    $two = 2 * [double]$r.demand.total
    $ec = $r.economics
    $res.Add([pscustomobject]@{
      row=$x.n; pair="$($x.o)-$($x.d)"; airline=$x.al; aircraft=$x.ac; freq=$x.f; season=$x.s; port=$port
      engine=$r.forecast_engine.local_leg; feed_level=$r.feed_level.level_engine
      two_way=[math]::Round($two); local_ew=[math]::Round($loc); cnx_ew=[math]::Round($cnx)
      cnx_share=$(if (($loc + $cnx) -gt 0) { [math]::Round($cnx / ($loc + $cnx), 3) } else { $null })
      analyst=$x.analyst; ratio=$(if ($x.analyst -gt 0) { [math]::Round($two / $x.analyst, 2) } else { $null })
      lf=$r.capacity.load; seats=$r.capacity.seats
      fare=$ec.econ_fare; market_fare=$ec.market_fare; fare_proxy=$ec.fare_is_proxy; econ_lf=$ec.econ_lf; bus_lf=$ec.bus_lf
      econ_seats_cfg=$ec.cost_model.econ_seats; bus_seats_cfg=$ec.cost_model.bus_seats; bus_fare=$ec.cost_model.bus_fare
      prorate=$ec.prorate; connecting_share_econ=$ec.connecting_share
      revenue_turn=$ec.revenue; total_cost_turn=$ec.total_cost; fuel_turn=$ec.fuel; own_turn=$ec.ownership
      margin=$ec.margin; contribution_yr=$ec.annual_contribution_before_ownership
      warnings=(($r.warnings) -join " | ")
    })
  }
}
$res | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $out
$res | Format-Table row, pair, port, engine, feed_level, two_way, local_ew, cnx_ew, cnx_share, ratio, lf, fare, margin -AutoSize
Write-Host "written: $out"
