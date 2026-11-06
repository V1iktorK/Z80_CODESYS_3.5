# run_codesys.ps1 - запуск скрипта в CODESYS Scripting Engine (headless) с повторами.
#
# Зачем повторы: CODESYS - single-instance приложение. Если предыдущий процесс ещё не
# освободил мьютекс, новый запуск молча завершается с кодом 1, не выполнив скрипт
# (в stdout пусто, лог-файл скрипта пуст). Поэтому: убить хвосты, подождать, запустить,
# дождаться завершения, проверить, что лог непустой, иначе повторить.
#
# Usage:
#   powershell -File run_codesys.ps1 -Script "C:\path\to\script.py"
#   powershell -File run_codesys.ps1 -Script "..." -Log "C:\path\to\script.log"

param(
    [Parameter(Mandatory = $true)][string]$Script,
    [string]$Log,
    [int]$MaxAttempts = 6
)

$ErrorActionPreference = 'Stop'
$codesysExe = 'C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe'
$profile    = 'CODESYS V3.5 SP17 Patch 3'

if (-not (Test-Path $Script)) { throw "script not found: $Script" }
$Script = (Resolve-Path $Script).Path
if (-not $Log) { $Log = [System.IO.Path]::ChangeExtension($Script, '.log') }
$stdout = [System.IO.Path]::ChangeExtension($Script, '.stdout.txt')

function Stop-CodesysLeftovers {
    # Vazhno: posle Kill protsess umiraet NE mgnovenno i prodolzhaet derzhat
    # odnoinstansnyj mutex CODESYS. Esli zapustit novyj protsess srazu, on
    # molcha zavershitsya s kodom 1, ne vypolniv skript (log ostanetsya pustym).
    # Poetomu posle ubijstva ZHDEM, poka protsessov realno ne ostanetsya.
    for ($i = 0; $i -lt 20; $i++) {
        $pr = Get-Process -Name CODESYS -ErrorAction SilentlyContinue
        if (-not $pr) { break }
        $pr | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    Start-Sleep -Seconds 3
}

function Wait-CodesysExit {
    param([int]$TimeoutSec = 360)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (-not (Get-Process -Name CODESYS -ErrorAction SilentlyContinue)) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Stop-CodesysLeftovers
    Start-Sleep -Seconds 4

    if (Test-Path $Log) { Remove-Item $Log -Force -ErrorAction SilentlyContinue }
    # ВАЖНО: -ArgumentList должен быть ОДНОЙ строкой с явными кавычками.
    # Если передать массив, PowerShell 5.1 склеит элементы через пробел без кавычек,
    # и CODESYS получит --profile=CODESYS (обрезанный) -> "Некорректный профиль версии".
    $argLine = '--profile="' + $profile + '" --runscript="' + $Script + '" --noUI'
    $p = Start-Process -FilePath $codesysExe -ArgumentList $argLine -PassThru -NoNewWindow `
                       -RedirectStandardOutput $stdout -RedirectStandardError "$stdout.err"
    [void](Wait-CodesysExit)
    Start-Sleep -Seconds 2

    $logOk = (Test-Path $Log) -and ((Get-Item $Log).Length -gt 0)
    Write-Host ("attempt {0}: exit={1} log={2}" -f $attempt, $p.ExitCode, $(if ($logOk) { 'OK' } else { 'EMPTY' }))
    if ($logOk) { break }
}

Write-Host '--- stdout ---'
Get-Content $stdout -ErrorAction SilentlyContinue
if (Test-Path "$stdout.err") {
    $err = Get-Content "$stdout.err" -ErrorAction SilentlyContinue
    if ($err) { Write-Host '--- stderr ---'; $err }
}
Write-Host '--- log ---'
Get-Content $Log -ErrorAction SilentlyContinue
