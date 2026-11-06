@echo off
rem ============================================================================
rem run_diag_progs.cmd -- zapustit generator\tools\diag_progs.py pod CODESYS.
rem
rem  Z A Ch E M  K O P I R U E M. CODESYS ispolnyaet tolko skripty, lezhashchie
rem  R Ya D O M  s  build.py, v kataloge generator\. Skript vo vlozhennom
rem  kataloge (generator\tools\) on molcha ignoriruet.
rem
rem  P E R E D  Z A P U S K O M  u b i v a e m CODESYS: on odnoekzemplyarnyj,
rem  i ostavshijsya process zastavlyaet novyj zapusk molcha zhdAT.
rem  timeout tut NE ispolzuem -- pod perenapravleniem vvoda on padaet
rem  ("Input redirection is not supported"), i pauza mezhdu popytkami
rem  taskkill propadaet.
rem ============================================================================
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "GEN=%~dp0"
set "TOOLS=%~dp0tools"
set "OUT=%~dp0..\log\diag_progs_out.txt"

rem --- 1. ubrat vse zapushchennye CODESYS ---
:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

rem --- 2. skopirovat skript k build.py (inache CODESYS ego ne najdet) ---
copy /Y "%TOOLS%\diag_progs.py" "%GEN%\_diag_progs_run.py" >nul

rem --- 3. zapusk ---
set "Z80_ROOT=%~dp0.."
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%GEN%\_diag_progs_run.py" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"

rem --- 4. uborka ---
del /F /Q "%GEN%\_diag_progs_run.py" >nul 2>&1
taskkill /IM CODESYS.exe /F >nul 2>&1
