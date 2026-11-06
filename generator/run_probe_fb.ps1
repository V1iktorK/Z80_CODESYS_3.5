# run_probe_fb.ps1 -- probe FB na oshibki C32 (bisekciya po ekzemplyaram).
#
#  Z A Ch E M  S V O J  Z A P U S K. Variant cherez .cmd s
#  "%EXE% ... --noUI > fajl" na etoj mashine daet exit=-1 i pustoj vyvod.
#  Rabotaet tolko Start-Process s perenapravleniem potokov -- tak zhe,
#  kak v run_build_log.ps1.
#
#  ZAPUSK:  powershell -File run_probe_fb.ps1 -Fbs "FB_ALU_Z80,FB_IO_Ports"
param(
    [Parameter(Mandatory = $true)][string]$Fbs,
    [string]$Script = 'tools\probe_fb.py',
    [int]$TimeoutSec = 900,
    [string]$Profile = 'CODESYS V3.5 SP17 Patch 3'
)

$ErrorActionPreference = 'Continue'
$gen = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $gen
$exe = 'C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe'
#  U N I K A L' N Y E  I M E N A  F A J L O V  N A  K A Zh D Y J  Z A P U S K.
#  P O Ch E M U. Ranshe imena byli postoyannymi, i kogda predydushchij (uzhe
#  ubityj) process CODESYS eshche derzhal deskriptory starogo fajla, novyj
#  Start-Process molcha NE PISAL v nego nichego. Naruzhno eto vyglyadelo kak
#  "kompilyator zavershilsya, a oshibok net" -- i tri proby iz chetyreh
#  pokazali pustotu vmesto real nogo rezul tata. Teper kazhdyj zapusk pishet
#  v svoj fajl, a potom on kopiruetsya v obychnoe imya.
$stamp = [guid]::NewGuid().ToString('N').Substring(0, 8)
$out = Join-Path $root ("log\probe_fb_" + $stamp + ".out")
$err = Join-Path $root ("log\probe_fb_" + $stamp + ".err")
$outFinal = Join-Path $root 'log\probe_fb_out.txt'

# ---------------------------------------------------------------- processy
$all = @(Get-CimInstance Win32_Process -Filter "Name='CODESYS.exe'" -ErrorAction SilentlyContinue)
$mine = @($all | Where-Object { $_.CommandLine -and ($_.CommandLine -match '--runscript' -or $_.CommandLine -match '--noUI') })
foreach ($p in $mine) { taskkill /F /PID $p.ProcessId 2>&1 | Out-Null }
if ($mine.Count -gt 0) { Start-Sleep -Seconds 4 }
if ((@($all | Where-Object { $mine.ProcessId -notcontains $_.ProcessId })).Count -gt 0) {
    Write-Host "[probe] rabotaet chuzhaya sessiya CODESYS -- ostanavlivayus"
    exit 2
}

# ---------------------------------------------------------------- podgotovka
#  Skript proby mozhno podmenit cherez -Script (po umolchaniyu probe_fb.py).
#  Eto nuzhno, chtoby tem zhe nadezhnym zapuskatel em zapuskat i drugie
#  proby (naprimer, probe_index.py -- kakoy tip indeksa nuzhen massivu).
$probe = Join-Path $gen $Script
$runner = Join-Path $gen '_probe_fb_run.py'
Copy-Item $probe $runner -Force

$buildDir = Join-Path $root 'build'
if (Test-Path $buildDir) {
    Get-ChildItem $buildDir -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}
foreach ($f in @($out, $err)) {
    if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
}

$env:Z80_ROOT = $root
$env:Z80_FBS = $Fbs

Write-Host ("[probe] FB: " + $Fbs)

# ---------------------------------------------------------------- zapusk
$p = Start-Process -FilePath $exe `
    -ArgumentList @("--profile=`"$Profile`"", "--runscript=`"$runner`"", '--noUI') `
    -RedirectStandardOutput $out -RedirectStandardError $err -PassThru

$done = $p.WaitForExit($TimeoutSec * 1000)
if (-not $done) {
    Write-Host "[probe] TAJMAUT -- ubiraem process"
    try { $p.Kill() } catch { }
    Start-Sleep -Seconds 3
}

Remove-Item $runner -Force -ErrorAction SilentlyContinue

#  P O Ch E M U  U B I V A E M  V S E  CODESYS  P O S L E  R A B O T Y.
#  WaitForExit vozvrashchaet upravlenie, kogda vyhodit R O D I T E L S K I J
#  process, no CODESYS ostavlyaet dochernij -- i tot derzhit fajlovye
#  deskriptory perenapravlennyh potokov. Poka on zhiv, fajly vyvoda ostayutsya
#  P U S T Y M I, hotya sborka uzhe zavershilas. Imenno iz-za etogo odna i ta zhe
#  proba davala to "4 oshibki", to "pustotu".
#  U b i v a t ' v s e  bezopasno: v nachale my U B E D I L I S, chto chuzhoj sessii
#  net (inache by uzhe vyshli s kodom 2), znachit lyuboj CODESYS sejchas -- nash.
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 3
#  na vsyakij sluchaj -- eshche raz, esli dochernij process uspel pererodit sya
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 2

#  O Zh I D A N I E  G O T O V N O S T I  L O G A.
#  Start-Process perenapravlyaet potoki v fajly, no CODESYS (i ego dochernie
#  processy) mogut derzhat nepotrachennye fajlovye deskriptory eshche nekotoroe
#  vremya posle vyhoda roditelya. Esli prochitat fajl srazu, on okazyvaetsya
#  P U S T Y M -- a sborka pri etom uzhe zavershilas. Iz-za etogo odna i ta zhe
#  proba davala to "4 oshibki", to "pustotu". Zhdem, poka razmer perestanet
#  menyat sya (ili poka ne vyderzhim predel).
$deadline = (Get-Date).AddSeconds(30)
$lastSize = -1
while ((Get-Date) -lt $deadline) {
    $sz1 = if (Test-Path $out) { (Get-Item $out).Length } else { 0 }
    $sz2 = if (Test-Path $err) { (Get-Item $err).Length } else { 0 }
    if (($sz1 + $sz2) -gt 0 -and ($sz1 + $sz2) -eq $lastSize) { break }
    $lastSize = $sz1 + $sz2
    Start-Sleep -Milliseconds 500
}

# ---------------------------------------------------------------- vyvod
$strict = New-Object System.Text.UTF8Encoding($false, $true)
function Convert-Text([byte[]]$bytes) {
    if ($null -eq $bytes -or $bytes.Length -eq 0) { return '' }
    try { return $strict.GetString($bytes) }
    catch { return [System.Text.Encoding]::GetEncoding(866).GetString($bytes) }
}
$parts = @()
foreach ($f in @($out, $err)) {
    if (Test-Path $f) {
        $txt = Convert-Text ([System.IO.File]::ReadAllBytes($f))
        if ($txt.Length -gt 0) { $parts += $txt }
    }
}
$merged = ($parts -join "`n")
[System.IO.File]::WriteAllText($outFinal, $merged, (New-Object System.Text.UTF8Encoding($false)))
Remove-Item $out, $err -Force -ErrorAction SilentlyContinue

$t = if (Test-Path $outFinal) { Get-Content $outFinal -Raw } else { '' }
if ($null -eq $t) { $t = '' }
$nerr = ([regex]::Matches($t, ': Error:')).Count
$nwarn = ([regex]::Matches($t, ': Warning:')).Count
$itog = '<net itoga>'
if ($t -match '(Компиляция завершена[^\r\n]*)') { $itog = $Matches[1] }
Write-Host ("[probe] oshibok: " + $nerr + ", preduprezhdenij: " + $nwarn)
Write-Host ("[probe] " + $itog)
