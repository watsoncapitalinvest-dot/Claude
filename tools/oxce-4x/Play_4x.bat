@echo off
rem G.I. Joe X-COM 4x battlescape test build.
rem First run copies the original X-COM game files from the Steam install into the UFO folder here.
cd /d "%~dp0"
set "XC=C:\Program Files (x86)\Steam\steamapps\common\XCom UFO Defense\XCOM"
if exist "UFO\GEODATA\" goto play
if not exist "%XC%\GEODATA\" goto missing
echo Copying X-COM game files from your Steam install (one time only)...
for %%D in (GEODATA GEOGRAPH MAPS ROUTES SOUND TERRAIN UFOGRAPH UFOINTRO UNITS) do robocopy "%XC%\%%D" "UFO\%%D" /E /NFL /NDL /NJH /NJS /NP >nul
if not exist "UFO\GEODATA\" goto missing
:play
set OXCE_BATTLE_SCALE=4
set OXCE_MAP_HIRES=4
start "" OpenXcom.exe
exit /b 0
:missing
echo Could not find the X-COM game files.
echo Expected them in: %XC%
echo Copy GEODATA, GEOGRAPH, MAPS, ROUTES, SOUND, TERRAIN, UFOGRAPH, UFOINTRO and UNITS into the UFO folder next to this file.
pause
exit /b 1
