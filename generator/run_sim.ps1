# run_sim.ps1 -- zapusk emulyatora v SIMULYATSII i proverka vstroennyh testov.
#
#  O T L I Ch I E  O T  run_build_log.ps1: eta obertka N E  O Ch I Shch A E T
#  katalog build. Kak raz naoborot -- ej nuzhen uzhe sobrannyj
#  build\Z80_EMU.project, chtoby otkryt ego i vojti v onlajn.
#  (Probnaya obertka run_probe_fb.ps1 katalog chistit, poetomu ona dlya
#  etoj zadachi ne podhodit -- proekt propadal.)
#
#  Por ya d o k  r a b o t y:
#     1) generator\run_build_log.ps1   -- sobrat proekt
#     2) generator\run_sim.ps1         -- vypolnit i prochitat testy
param(
    [string]$Script = 'tools\run_simulation.py',
    [int]$TimeoutSec = 600,
    [string]$Profile = 'CODESYS V3.5 SP17 Patch 3'
)

$ErrorActionPreference = 'Continue'
$gen = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $gen
$exe = 'C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe'
$script = Join-Path $gen $Script
$proj = Join-Path $root 'build\Z80_EMU.project'

if (-not (Test-Path $proj)) {
    Write-Host "[sim] NET PROEKTA: $proj"
    Write-Host "[sim] Snachala soberite: generator\run_build_log.ps1"
    exit 1
}

$stamp = [guid]::NewGuid().ToString('N').Substring(0, 8)
$out = Join-Path $root ("log\sim_" + $stamp + ".out")
$err = Join-Path $root ("log\sim_" + $stamp + ".err")
$outFinal = Join-Path $root 'log\sim_codesys.txt'

$env:Z80_ROOT = $root

# ---------------------------------------------------------------- proverka
$all = @(Get-CimInstance Win32_Process -Filter "Name='CODESYS.exe'" -ErrorAction SilentlyContinue)
$mine = @($all | Where-Object { $_.CommandLine -and ($_.CommandLine -match '--runscript' -or $_.CommandLine -match '--noUI') })
$theirs = @($all | Where-Object { $mine.ProcessId -notcontains $_.ProcessId })

foreach ($p in $mine) {
    taskkill /F /PID $p.ProcessId 2>&1 | Out-Null
}
if ($mine.Count -gt 0) { Start-Sleep -Seconds 4 }

if ($theirs.Count -gt 0) {
    Write-Host "[sim] Z A P U S K  N E V O Z M O Z H E N: rabotaet chuzhaya sessiya CODESYS."
    foreach ($p in $theirs) { Write-Host ("[sim]   PID " + $p.ProcessId) }
    exit 2
}

foreach ($f in @($out, $err)) {
    if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
}

Write-Host ("[sim] proekt : " + $proj)
Write-Host ("[sim] skript : " + $script)

$p = Start-Process -FilePath $exe `
    -ArgumentList @("--profile=`"$Profile`"", "--runscript=`"$script`"", '--noUI') `
    -RedirectStandardOutput $out -RedirectStandardError $err `
    -PassThru

Write-Host ("[sim] zapushchen PID " + $p.Id + ", zhdem do " + $TimeoutSec + " s")

$done = $p.WaitForExit($TimeoutSec * 1000)
if (-not $done) {
    Write-Host "[sim] TAJMAUT -- ubiraem process"
    try { $p.Kill() } catch { }
    Start-Sleep -Seconds 3
}

#  CODESYS ostavlyaet dochernij process s deskriptorami -- bez ubijstva
#  fajl vyvoda ostanetsya pustym (sm. kommentarij v run_build_log.ps1).
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 3
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 2

$strictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
function Convert-Text([byte[]]$bytes) {
    if ($null -eq $bytes -or $bytes.Length -eq 0) { return '' }
    try { return $strictUtf8.GetString($bytes) }
    catch { return [System.Text.Encoding]::GetEncoding(866).GetString($bytes) }
}

$parts = @()
foreach ($f in @($out, $err)) {
    if (Test-Path $f) {
        $txt = Convert-Text ([System.IO.File]::ReadAllBytes($f))
        if ($txt.Length -gt 0) { $parts += $txt }
    }
}
$rc = if ($done) { $p.ExitCode } else { 'timeout' }
$merged = ($parts -join "`n") + "`n[exit=" + $rc + "]`n"
[System.IO.File]::WriteAllText($outFinal, $merged, (New-Object System.Text.UTF8Encoding($false)))
Remove-Item $out, $err -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== VYVOD KONSOLI CODESYS ==="
Get-Content $outFinal -Encoding UTF8 | Select-Object -Last 40 | ForEach-Object { Write-Host ("  " + $_) }
Write-Host ""
$simLog = Join-Path $root 'log\sim_out.txt'
if (Test-Path $simLog) {
    Write-Host "=== REZULTAT PROGONA (log\sim_out.txt) ==="
    Get-Content $simLog -Encoding UTF8 | Select-Object -Last 40 | ForEach-Object { Write-Host ("  " + $_) }
} else {
    Write-Host "=== log\sim_out.txt NE SOZDAN -- skript ne doshel do konca ==="
}
