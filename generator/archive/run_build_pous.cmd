@echo off
rem ============================================================================
rem run_build_pous.cmd -- sborka polnogo proekta s zadannym spiskom programm
rem v zadache. Sposob bisekcii: sushchaem spisok, poka ne propadut oshibki.
rem
rem   run_build_pous.cmd "PLC_PRG"
rem   run_build_pous.cmd "PRG_InitMemory,TEST_Z80"
rem   run_build_pous.cmd ""            -- zadacha bez programm
rem
rem Vyvod: log\codesys_out.txt (pereza P I S Y V A E T S Ya)
rem ============================================================================
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "GEN=%~dp0"
set "OUT=%~dp0..\log\codesys_out.txt"
set "ROOT=%~dp0.."

:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

del /F /Q "%ROOT%\build\*.~u" >nul 2>&1
del /F /Q "%ROOT%\*.~u" >nul 2>&1

set "Z80_TASK_POUS=%~1"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%GEN%build.py" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"

taskkill /IM CODESYS.exe /F >nul 2>&1
