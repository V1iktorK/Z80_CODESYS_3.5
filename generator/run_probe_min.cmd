@echo off
rem ============================================================================
rem run_probe_min.cmd -- minimalnyj vosproizvodyashchij test.
rem  Rezhim zadayetsya pervym argumentom (1..7). Rezultat: log\probe_N.txt
rem  i vyvod CODESYS: log\probe_N_out.txt
rem ============================================================================
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "GEN=%~dp0"
set "TOOLS=%~dp0tools"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=1"
set "OUT=%~dp0..\log\probe_%MODE%_out.txt"

:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

copy /Y "%TOOLS%\probe_min.py" "%GEN%\_probe_min_run.py" >nul

set "Z80_ROOT=%~dp0.."
set "Z80_PROBE=%MODE%"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%GEN%\_probe_min_run.py" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"

del /F /Q "%GEN%\_probe_min_run.py" >nul 2>&1
taskkill /IM CODESYS.exe /F >nul 2>&1
