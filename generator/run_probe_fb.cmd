@echo off
rem ============================================================================
rem run_probe_fb.cmd -- probe FB na oshibki C32.
rem   run_probe_fb.cmd "FB_ALU_Z80,FB_IO_Ports"
rem Rezultat: log\probe_fb.txt i vyvod CODESYS v log\probe_fb_out.txt
rem ============================================================================
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "GEN=%~dp0"
set "OUT=%~dp0..\log\probe_fb_out.txt"
set "ROOT=%~dp0.."

if "%~1"=="" (
  echo ukazhite spisok FB cherez zapyatuyu
  exit /b 1
)

:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

rem ochistka kataloga build: s ostatkami CODESYS padaet na pervom shage
if exist "%ROOT%\build" (
  del /F /Q "%ROOT%\build\*" >nul 2>&1
  rmdir /S /Q "%ROOT%\build" >nul 2>&1
)
mkdir "%ROOT%\build" >nul 2>&1

copy /Y "%~dp0tools\probe_fb.py" "%GEN%_probe_fb_run.py" >nul

set "Z80_ROOT=%ROOT%"
set "Z80_FBS=%~1"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%GEN%_probe_fb_run.py" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"

del /F /Q "%GEN%_probe_fb_run.py" >nul 2>&1
taskkill /IM CODESYS.exe /F >nul 2>&1
