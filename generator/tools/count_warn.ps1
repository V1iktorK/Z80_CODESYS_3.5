# count_warn.ps1 -- skolko preduprezhdenij kazhdogo vida daet sborka
# s zadannym spiskom programm v zadache.
#
#   powershell -File count_warn.ps1 -Pous "TEST_Z80"
#
#  B E Z  K I R I L L I C Y  V  F A J L E. Windows PowerShell 5.1 chitaet
#  .ps1 v ANSI-kodirovke, esli net BOM. Kak tolko v fajle poyavlyalas
#  kirillica (put k proektu ili slovo iz loga), parser razsypalsya na
#  "Unexpected token". Poetomu put berem iz raspolozheniya skripta,
#  a iz loga ishchem tolko latinskie priznaki.
param([string]$Pous = '')

$ErrorActionPreference = 'Continue'
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$gen = Split-Path -Parent $tools
$dst = Split-Path -Parent $gen
$log = Join-Path $dst 'log\codesys_out.txt'
$runner = Join-Path $gen 'run_build_log.ps1'

if ($Pous) { $env:Z80_TASK_POUS = $Pous } else { Remove-Item Env:\Z80_TASK_POUS -ErrorAction SilentlyContinue }

$ok = $false
for ($i = 1; $i -le 4; $i++) {
    Get-Process -Name CODESYS -ErrorAction SilentlyContinue |
        ForEach-Object { try { $_.Kill() } catch { } }
    Start-Sleep -Seconds 5
    & powershell -NoProfile -ExecutionPolicy Bypass -File $runner *> $null
    if (Test-Path $log) {
        $t = Get-Content $log -Raw
        if ($t -and $t.Length -gt 400 -and $t.Contains('C0:')) { $ok = $true; break }
    }
}
if (-not $ok) { Write-Output 'LOG NOT CAPTURED'; exit 1 }

$t = Get-Content $log -Raw
$w2i = ([regex]::Matches($t, 'WORD')).Count
$errs = ([regex]::Matches($t, ': Error:')).Count
$warns = ([regex]::Matches($t, ': Warning:')).Count
$c196 = ([regex]::Matches($t, 'C196')).Count
$c139 = ([regex]::Matches($t, 'C139')).Count
$addr = ([regex]::Matches($t, '%IX')).Count + ([regex]::Matches($t, '%QX')).Count
Write-Output ("err={0} warn={1} C196={2} C139={3} addrWarn={4}" -f $errs, $warns, $c196, $c139, $addr)
