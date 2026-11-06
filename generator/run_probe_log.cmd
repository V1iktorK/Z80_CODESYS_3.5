@echo off
rem run_probe_log.cmd -- sborka proverochnogo proekta tipov s zapis'yu vyvoda.
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "SCR=%~dp0build_type_probe.py"
set "OUT=%~dp0..\log\type_probe_out.txt"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%SCR%" --noUI > "%OUT%" 2>&1
echo [exit=%ERRORLEVEL%] >> "%OUT%"
