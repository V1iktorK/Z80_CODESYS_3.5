@echo off
rem run_build_log.cmd -- sborka Z80_EMU s zapis'yu vsego vyvoda CODESYS.
rem  Tonkaya obertka: ubiraet fajly blokirovki i peredaet upravlenie
rem  PowerShell-skriptu run_build_log.ps1, gde lezhit vsya logika.
rem  Podrobnosti i istoriya pravok -- v kommentariyah .ps1 i v
rem  docs/08_PLAN_PRODOLZHENIYA.md.
setlocal
del /F /Q "%~dp0..\build\*.~u" >nul 2>&1
del /F /Q "%~dp0..\*.~u" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_build_log.ps1"
set "OUT=%~dp0..\log\codesys_out.txt"
for %%A in ("%OUT%") do set "SZ=%%~zA"
echo [gotovo] vyvod: %OUT%  (%SZ% bajt)
endlocal
