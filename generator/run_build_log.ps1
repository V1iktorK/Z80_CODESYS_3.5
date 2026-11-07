# run_build_log.ps1 -- zapusk build.py pod CODESYS s nadezhnym zavorom vyvoda.
#
#  Z A Ch E M  O T D E L N Y J  S K R I P T. Pryamoj zapusk
#  "CODESYS.exe --noUI > fajl" perestal rabotat posle perezagruzki: process
#  vyhodit srazu s kode 1 i pustym vyvodom. Zapusk bez --noUI otkryvaet okno
#  i zhdet polzovatelya. Start-Process s perenapravleniem potokov i
#  WaitForExit rabotaet stabilno -- poetomu vyvod sobiraem zdes.
#
#  P O Ch E M U  N E  U B I V A E M  V S E  CODESYS  P O D R Ya D.
#  Ranshe obertka delala taskkill /IM CODESYS.exe /F v cikle. Eto opasno:
#  CODESYS -- odnoekzemplyarnoe prilozhenie, i na mashine mozhet rabotat
#  Ch U Zh A Ya  s sessiya (naprimer, drugoy proekt v IDE). 13.10.2026
#  imenno tak i sluchilos: pered zapuskom byl ziv process s komandnoy
#  strokoy "...CPM6502\tools\probe_b2.py", i sborka molchala, potomu chto
#  mjutex byl zanyat im. Ubit ego -- znachit unichtozhit chuzhuyu rabotu.
#  Teper my snimaem T O L K O  svoi processy: te, u kotoryh v komandnoy
#  stroke est --runscript ili --noUI. Chuzhuyu sessiyu my ne tronem, no
#  chestno soobshchim, chto sborka nevozmozhna, i ostanovimsya.
#
#  T A J M A U T  N U Zh E N. Kompilyator uzhe dvazhdy zavisal na release
#  (CPU stoit, vyvod pust). Bez tajmauta sborka visela by do beskonechnosti.
param(
    [int]$TimeoutSec = 900,
    [string]$Profile = 'CODESYS V3.5 SP17 Patch 3',
    [string]$Exe = ''
)

$ErrorActionPreference = 'Continue'
$gen = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $gen

# ---------------------------------------------------------------- CODESYS.exe
#  I S K A T '  C O D E S Y S,  A  N E  Z H D A T'  N U Zh N O J  V E R S I I.
#  Ran'she put' byla zhestko propisana, i na lyuboj drugoj mashine skript
#  molcha ne zapuskalsya. Poryadok poiska:
#    1) parametr -Exe '...\CODESYS.exe';
#    2) peremennaya okruzheniya CODESYS_EXE;
#    3) standartnyj katalog tekushchej versii (3.5.17.30);
#    4) poisk lyuboj ustanovlennoj versii v Program Files.
function Find-Codesys {
    param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) { return $Hint }
    if ($env:CODESYS_EXE -and (Test-Path $env:CODESYS_EXE)) { return $env:CODESYS_EXE }
    $known = 'C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe'
    if (Test-Path $known) { return $known }
    foreach ($r in @('C:\Program Files (x86)', 'C:\Program Files')) {
        if (-not (Test-Path $r)) { continue }
        $f = Get-ChildItem -Path $r -Filter 'CODESYS.exe' -Recurse -Depth 4 `
                -ErrorAction SilentlyContinue |
             Where-Object { $_.FullName -like '*CODESYS*\Common\CODESYS.exe' } |
             Select-Object -First 1
        if ($f) { return $f.FullName }
    }
    return ''
}

$exe = Find-Codesys -Hint $Exe
if (-not $exe) {
    Write-Host '[build] NE NAJDEN CODESYS.exe.'
    Write-Host '[build] Ukazhite put: generator\run_build_log.cmd -Exe "C:\...\CODESYS.exe"'
    Write-Host '[build] ili zadajte peremennuyu okruzheniya CODESYS_EXE.'
    exit 2
}
$script = Join-Path $gen 'build.py'
#  U N I K A L' N Y E  I M E N A  F A J L O V  P E R E Kh V A T A  N A  K A Zh D Y J  Z A P U S K.
#  P O Ch E M U. Pri postoyannyh imenah byvalo tak: predydushchij (uzhe
#  ubityj) process CODESYS eshche derzhit deskriptory starogo fajla, i novyj
#  Start-Process molcha NE PISAL v nego nichego. Naruzhno -- "sborka proshla,
#  oshibok net", a na samom dele vyvod poteryalsya.
$stamp = [guid]::NewGuid().ToString('N').Substring(0, 8)
$out = Join-Path $root ("log\codesys_" + $stamp + ".out")
$err = Join-Path $root ("log\codesys_" + $stamp + ".err")
$outFinal = Join-Path $root 'log\codesys_out.txt'

$env:Z80_ROOT = $root

# ---------------------------------------------------------------- proverka
$all = @(Get-CimInstance Win32_Process -Filter "Name='CODESYS.exe'" -ErrorAction SilentlyContinue)
$mine = @($all | Where-Object { $_.CommandLine -and ($_.CommandLine -match '--runscript' -or $_.CommandLine -match '--noUI') })
$theirs = @($all | Where-Object { $mine.ProcessId -notcontains $_.ProcessId })

Write-Host ("[build] vsego processov CODESYS: " + $all.Count)

foreach ($p in $mine) {
    Write-Host ("[build] ubiraem svoj process PID " + $p.ProcessId)
    taskkill /F /PID $p.ProcessId 2>&1 | Out-Null
}
if ($mine.Count -gt 0) { Start-Sleep -Seconds 4 }

if ($theirs.Count -gt 0) {
    Write-Host ""
    Write-Host "[build] S B O R K A  N E V O Z M O Z H N A."
    Write-Host "[build] Rabotaet chuzhaya sessiya CODESYS (veroyatno, vash IDE):"
    foreach ($p in $theirs) {
        $cl = $p.CommandLine
        if ($cl.Length -gt 160) { $cl = $cl.Substring(0, 160) + '...' }
        Write-Host ("[build]   PID " + $p.ProcessId + " : " + $cl)
    }
    Write-Host "[build] CODESYS odnoekzemplyarnyj: poka ona rabotaet, nas zapusk"
    Write-Host "[build] molcha zhdet. Zakroyte CODESYS i zapustite sborku snova."
    Write-Host "[build] (Ubivat chuzhuyu sessiyu my namerenno ne stanem.)"
    exit 2
}

# ---------------------------------------------------------------- zapusk
Write-Host ("[build] EXE    : " + $exe)
Write-Host ("[build] skript : " + $script)
Write-Host ("[build] vyvod  : " + $out)

foreach ($f in @($out, $err)) {
    if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
}

#  O C H I S T K A  K A T A L O G A  B U I L D -- O B Ya Z A T E L N A.
#  build.py udalyaet tolko "Z80_EMU.project*" i "*.precompilecache", a fajly
#  *.opt ostayutsya. S nimi sleduyushchij zapusk CODESYS padal na pervom zhe
#  shage ("sozdanie proekta s ustrojstvom") i M O L Ch A: ni oshibki,
#  ni itoga v konsoli, a v build.log -- odna stroka. Vyyasneno opytom:
#  posle polnoj ochistki kataloga ta zhe sborka prohodit.
$buildDir = Join-Path $root 'build'
if (Test-Path $buildDir) {
    Get-ChildItem $buildDir -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}

$p = Start-Process -FilePath $exe `
    -ArgumentList @("--profile=`"$Profile`"", "--runscript=`"$script`"", '--noUI') `
    -RedirectStandardOutput $out -RedirectStandardError $err `
    -PassThru

Write-Host ("[build] zapushchen PID " + $p.Id + ", zhdem do " + $TimeoutSec + " s")

$done = $p.WaitForExit($TimeoutSec * 1000)
if (-not $done) {
    Write-Host "[build] TAJMAUT: kompilyator ne otvetil za $TimeoutSec s -- ubiraem process"
    try { $p.Kill() } catch { }
    Start-Sleep -Seconds 3
} else {
    Write-Host ("[build] zavershen, kod " + $p.ExitCode)
}

#  P O Ch E M U  U B I V A E M  V S E  CODESYS  P O S L E  R A B O T Y.
#  WaitForExit vozvrashchaet upravlenie, kogda vyhodit R O D I T E L S K I J
#  process, no CODESYS ostavlyaet dochernij -- i tot derzhit fajlovye
#  deskriptory perenapravlennyh potokov. Poka on zhiv, fajl vyvoda ostayetsya
#  P U S T Y M, hotya sborka uzhe zavershilas. Iz-za etogo odna i ta zhe sborka
#  davala to "17 oshibok", to "pustotu" -- i kogda-to pokazalos, chto
#  "kompilyator zavis" (a on uzhe zakonchil i spoko jno zhdat nechego).
#  U b i v a t ' v s e  bezopasno: v nachale my ubedilis, chto chuzhoj sessii
#  net (inache vyshli by s kodom 2), znachit lyuboj CODESYS sejchas -- nash.
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 3
taskkill /IM CODESYS.exe /F 2>&1 | Out-Null
Start-Sleep -Seconds 2

#  K O D I R O V K A  V Y V O D A.
#  Provereno na etoj mashine: CODESYS 3.5 SP17 pishet konsol v UTF-8.
#  Poetomu snachala probuem UTF-8 V  S T R O G O M  rezhime (on padaet na
#  nevalidnyh posledovatel nostyah), i tolko esli ne vyshlo -- cp866.
#  P E R V A Ya  V E R S I Ya  etogo fajla dekodirovala vsegda v cp866 i tem
#  samym isporchila horoshij UTF-8 log: poluchalis "krakozyabry", i test T7
#  ne mog najti ni "Error", ni "zavershena".
$strictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
function Convert-Text([byte[]]$bytes) {
    if ($null -eq $bytes -or $bytes.Length -eq 0) { return '' }
    try {
        return $strictUtf8.GetString($bytes)
    } catch {
        return [System.Text.Encoding]::GetEncoding(866).GetString($bytes)
    }
}

$parts = @()
foreach ($f in @($out, $err)) {
    if (Test-Path $f) {
        $bytes = [System.IO.File]::ReadAllBytes($f)
        $txt = Convert-Text $bytes
        if ($txt.Length -gt 0) { $parts += $txt }
    }
}
$rc = if ($done) { $p.ExitCode } else { 'timeout' }
$merged = ($parts -join "`n") + "`n[exit=" + $rc + "]`n"
[System.IO.File]::WriteAllText($outFinal, $merged, (New-Object System.Text.UTF8Encoding($false)))
Remove-Item $out, $err -Force -ErrorAction SilentlyContinue

$sz = (Get-Item $outFinal -ErrorAction SilentlyContinue).Length
Write-Host ("[build] itogovyj vyvod: " + $sz + " bajt")
