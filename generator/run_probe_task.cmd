@echo off
rem run_probe_task.cmd -- zapustit generator\tools\probe_task.py pod CODESYS.
rem  Skript kopiruetsya k build.py: CODESYS ispolnyaet tolko skripty,
rem  lezhashchie v kataloge generator\.
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "GEN=%~dp0"
set "TOOLS=%~dp0tools"
set "OUT=%~dp0..\log\probe_task_out.txt"

:killloop
taskkill /IM CODESYS.exe /F >nul 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
tasklist /FI "IMAGENAME eq CODESYS.exe" 2>nul | find /I "CODESYS.exe" >nul
if not errorlevel 1 goto killloop

copy /Y "%TOOLS%\probe_task.py" "%GEN%\_probe_task_run.py" >nul

set "Z80_ROOT=%~dp0.."
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%GEN%\_probe_task_run.py" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"

del /F /Q "%GEN%\_probe_task_run.py" >nul 2>&1
taskkill /IM CODESYS.exe /F >nul 2>&1

