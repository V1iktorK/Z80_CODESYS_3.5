@echo off
rem run_build_verbose.cmd -- sborka s MAKSIMALNO podrobnym vyvodom kompilyatora.
rem CODESYS pechataet nomer POU i stroku tolko pri povyshennom urovne soobshchenij.
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "SCR=%~dp0build.py"
set "OUT=%~dp0..\log\codesys_verbose.txt"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%SCR%" --noUI --verbose > "%OUT%" 2>&1
echo [exit=%LEVEL%] >> "%OUT%"
