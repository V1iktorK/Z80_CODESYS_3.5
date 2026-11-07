# set_repo_meta.ps1 -- opisanie i temy (topics) repozitoriya cherez GitHub API.
#
#  Z A Ch E M. Git ne hranit ni opisanie repozitoriya, ni temy -- eto svojstva
#  na GitHube. CLI `gh` na etoj mashine ne ustanovlen, poetomu obraschaemsya k
#  REST API, a token berem iz togo zhe hranilishcha, chtem polzuetsya git
#  (credential.helper = manager). Token N I K O G D A ne pechataetsya.
#
#  ZAPUSK:  powershell -NoProfile -ExecutionPolicy Bypass -File tools\set_repo_meta.ps1
param(
    [string]$Owner = 'V1iktorK',
    [string]$Repo  = 'Z80_CODESYS_3.5',
    [string]$Description = '',
    #  T E M Y  --  S T R O K O J  cherez zapyatuyu, a ne massivom.
    #  Pri zapuske "powershell -File script.ps1 -Topics a,b,c" vyrazhenie
    #  a,b,c ne prevrashchaetsya v massiv: prihodit odna stroka s zapyatymi.
    #  Poetomu razdelyaem sami.
    [string]$Topics = ''
)

$ErrorActionPreference = 'Stop'

$inp = "protocol=https`nhost=github.com`n`n"
$cred = $inp | git credential fill 2>$null
$tok = ($cred | Where-Object { $_ -like 'password=*' }) -replace '^password=', ''
if (-not $tok) {
    Write-Host '[meta] ne udalos poluchit token iz git credential manager'
    exit 2
}
$user = ($cred | Where-Object { $_ -like 'username=*' }) -replace '^username=', ''
Write-Host ("[meta] token poluchen (dlina " + $tok.Length + "), polzovatel: " + $user)

$hdr = @{
    Authorization          = "Bearer $tok"
    Accept                 = 'application/vnd.github+json'
    'User-Agent'           = 'Z80_EMU-metadata'
    'X-GitHub-Api-Version' = '2022-11-28'
}
$base = "https://api.github.com/repos/$Owner/$Repo"

# --- 1. opisanie ---
if ($Description) {
    $body = @{ description = $Description; homepage = '' } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Method Patch -Uri $base -Headers $hdr `
                -Body ([Text.Encoding]::UTF8.GetBytes($body)) `
                -ContentType 'application/json; charset=utf-8'
        Write-Host ("[meta] opisanie zadano: " + $r.description)
    } catch {
        Write-Host ("[meta] OSHIBKA opisaniya: " + $_.Exception.Message)
    }
}

# --- 2. temy ---
if ($Topics) {
    #  V A Zh N O: names dolzhen byt PLOSKIJ massiv strok. Esli massiv
    #  sobran cherez ",@(...)", poluchaetsya vlozhennyj [["z80"]], i GitHub
    #  otvechaet 422 Unprocessable Entity (provereno: imenno v etom bylo delo).
    $names = @()
    foreach ($x in ($Topics -split ',')) {
        $nm = $x.Trim().ToLower()
        if ($nm) { $names += $nm }
    }
    $body = (@{ names = $names } | ConvertTo-Json -Compress)
    Write-Host ("[meta] otpravlyaem: " + $body)
    try {
        $r = Invoke-RestMethod -Method Put -Uri "$base/topics" -Headers $hdr `
                -Body ([Text.Encoding]::UTF8.GetBytes($body)) `
                -ContentType 'application/json; charset=utf-8'
        Write-Host ("[meta] temy zadany: " + ($r.names -join ', '))
    } catch {
        Write-Host ("[meta] OSHIBKA tem: " + $_.Exception.Message)
    }
}

# --- 3. proverka ---
try {
    $r = Invoke-RestMethod -Method Get -Uri $base -Headers $hdr
    Write-Host ("[meta] proverka: description = " + $r.description)
    $t = Invoke-RestMethod -Method Get -Uri "$base/topics" -Headers $hdr
    Write-Host ("[meta] proverka: topics = " + ($t.names -join ', '))
} catch {
    Write-Host ("[meta] proverka OSHIBKA: " + $_.Exception.Message)
}
