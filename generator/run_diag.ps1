# run_diag.ps1 -- universalnyj zapusk lyubogo diagnosticheskogo skripta pod CODESYS.
#
#  Z A Ch E M  E D I N Y J  Z A P U S K A T E L'. Klyuch --noUI posle
#  perezagruzki perestal rabotat (process vyhodit s kode 1 i pustym vyvodom),
#  a zapusk bez nego otkryvaet okno i zhdet polzovatelya. Rabotaet tolko
#  Start-Process s perenapravleniem potokov i WaitForExit -- poetomu vse
#  diagnosticheskie skripty idut cherez etot fajl.
#
#  Z A Ch E M  N E  U B I V A E M  V S E  CODESYS. On odnoekzemplyarnyj,
#  no na mashine mozhet rabotat chuzhaya sessiya (vash IDE s drugim proektom).
#  Snimaem tolko svoi processy -- te, u kotoryh v komandnoy stroke est
#  --runscript ili --noUI.
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [int]$TimeoutSec = 600,
    [string]$OutName = 'diag',
    [string]$Profile = 'CODESYS V3.5 SP17 Patch 3'
)

$ErrorActionPreference = 'Continue'
$gen = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $gen
$exe = 'C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe'
$log = Join-Path $root 'log'
if (-not (Test-Path $log)) { New-Item -ItemType Directory -Path $log | Out-Null }

# skript dolzhen lezhat V GENERATOR, ryadom s build.py
$src = Join-Path (Join-Path $gen 'tools') $Script
if (-not (Test-Path $src)) {
    Write-Host ("[diag] NET SKRIPTA: " + $src)
    exit 3
}
$run = Join-Path $gen ('_run_' + $Script)
Copy-Item $src $run -Force

$out = Join-Path $log ($OutName + '_out.txt')
$err = Join-Path $log ($OutName + '_err.txt')
$env:Z80_ROOT = $root

$all = @(Get-CimInstance Win32_Process -Filter "Name='CODESYS.exe'" -ErrorAction SilentlyContinue)
$mine = @($all | Where-Object { $_.CommandLine -and ($_.CommandLine -match '--runscript' -or $_.CommandLine -match '--noUI') })
$theirs = @($all | Where-Object { $mine.ProcessId -notcontains $_.ProcessId })
foreach ($p in $mine) { taskkill /F /PID $p.ProcessId 2>&1 | Out-Null }
if ($mine.Count -gt 0) { Start-Sleep -Seconds 3 }

if ($theirs.Count -gt 0) {
    Write-Host "[diag] ZANYaTO: rabotaet chuzhaya sessiya CODESYS. Zakroyte CODESYS i povtorite."
    foreach ($p in $theirs) { Write-Host ("[diag]   PID " + $p.ProcessId) }
    Remove-Item $run -Force -ErrorAction SilentlyContinue
    exit 2
}

foreach ($f in @($out, $err)) { if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue } }

$p = Start-Process -FilePath $exe `
    -ArgumentList @("--profile=`"$Profile`"", "--runscript=`"$run`"", '--noUI') `
    -RedirectStandardOutput $out -RedirectStandardError $err -PassThru

$done = $p.WaitForExit($TimeoutSec * 1000)
if (-not $done) {
    Write-Host ("[diag] TAJMAUT " + $TimeoutSec + " s")
    try { $p.Kill() } catch { }
    Start-Sleep -Seconds 2
}

if (Test-Path $err) {
    $e = Get-Content $err -Raw -ErrorAction SilentlyContinue
    if ($e -and $e.Trim().Length -gt 0) { Add-Content -Path $out -Value $e }
}

Remove-Item $run -Force -ErrorAction SilentlyContinue
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Write-Host ("[diag] gotovo: " + $out)
