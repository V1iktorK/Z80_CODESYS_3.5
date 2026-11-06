@echo off
rem run_build.cmd -- headless build of Z80_EMU inside CODESYS.
rem Written as a file so the Cyrillic path never has to survive a shell argument.
setlocal
set "EXE=C:\Program Files (x86)\CODESYS 3.5.17.30\CODESYS\Common\CODESYS.exe"
set "SCR=%~dp0build.py"
"%EXE%" --profile="CODESYS V3.5 SP17 Patch 3" --runscript="%SCR%" --noUI
echo [exit=%ERRORLEVEL%]
