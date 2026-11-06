# start_plc_runtime.ps1 -- podnyat' sluzhbu PLK i ZAPISAT' chto poluchilos.
#
#  Z A Ch E M  O T D E L N Y J  F A J L. Zapuskaetsya s povysheniem cherez
#  Start-Process -Verb RunAs, i v etom rezhime nel zya nichego uvidel: okno
#  skryto, vyvod poteryan. Poetomu vsyo, chto nuzhno znat (udalsya li zapusk,
#  kakaya oshibka), pishem v fajl, a potom chitaem ego uzhe bez povysheniya.
#
#  Dva rezhima:
#     parametr net      -- start sluzhby
#     -Stop             -- ostanovit' sluzhbu (chtoby vernut' kak bylo)
param([switch]$Stop)

$ErrorActionPreference = 'Continue'
$svc = 'CODESYS Control Win V3'
$out = Join-Path $env:TEMP 'plc_runtime_start.log'

function W([string]$s) { Add-Content -Path $out -Value $s -Encoding UTF8 }

Set-Content -Path $out -Value ("=== {0} {1} ===" -f (Get-Date -Format 'HH:mm:ss'), $(if ($Stop) { 'STOP' } else { 'START' })) -Encoding UTF8

try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = New-Object Security.Principal.WindowsPrincipal($id)
    W ("admin: " + $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
} catch {
    W ("admin: ne opredelit -- " + $_.Exception.Message)
}

$s = Get-Service $svc -ErrorAction SilentlyContinue
if (-not $s) {
    W "OSHIBKA: sluzhba '$svc' ne najdena"
    exit 1
}
W ("do: " + $s.Status + " / StartType=" + $s.StartType)

if ($Stop) {
    try { Stop-Service $svc -Force -ErrorAction Stop; W "stop: OK" }
    catch { W ("stop OSHIBKA: " + $_.Exception.Message) }
} else {
    try {
        Start-Service $svc -ErrorAction Stop
        W "start: OK"
    } catch {
        W ("start OSHIBKA: " + $_.Exception.Message)
        W ("  HRESULT: " + ("0x{0:X8}" -f $_.Exception.HResult))
        #  sc.exe daet bolee ponyatnyj kod
        $sc = & sc.exe start $svc 2>&1
        W ("  sc start: " + (($sc | Out-String).Trim()))
    }
}

Start-Sleep -Seconds 3
$s2 = Get-Service $svc -ErrorAction SilentlyContinue
W ("posle: " + $s2.Status)

#  poslednie sobytiya po sluzhbe -- oni obychno i govoryat prichinu
try {
    $ev = Get-WinEvent -FilterHashtable @{LogName = 'System'; StartTime = (Get-Date).AddMinutes(-5)} -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match 'CODESYS' } | Select-Object -First 4
    foreach ($e in $ev) {
        W ("  event [{0}, id={1}] {2}" -f $e.TimeCreated.ToString('HH:mm:ss'), $e.Id,
           $e.Message.Substring(0, [Math]::Min(160, $e.Message.Length)).Replace("`n", ' '))
    }
} catch { }

W "=== KONEC ==="
