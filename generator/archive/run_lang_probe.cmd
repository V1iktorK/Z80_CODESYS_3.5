@echo off
rem run_lang_probe.cmd -- yazykovoj eksperiment: ORD i literaly s '$'.
rem Kak i osnovnaya sborka: snachala ubivaem ostavshiesya processy CODESYS,
rem inache novyj zapusk molcha zhdet i rezultat budet pustym.
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "SCR=%~dp0build_lang_probe.py"
set "OUT=%~dp0..\log\lang_probe_out.txt"

:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%SCR%" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"
taskkill /IM CODESYS.exe /F >nul 2>&1
