@echo off
rem G.I. Joe X-COM 4x battlescape test build.
rem First run copies the original X-COM game files into the UFO folder here.
cd /d "%~dp0"
if exist "UFO\GEODATA\" goto play
set "XC=%~dp0XCom UFO Defense\XCOM"
if exist "%XC%\GEODATA\" goto copy
set "XC=C:\Program Files (x86)\Steam\steamapps\common\XCom UFO Defense\XCOM"
if exist "%XC%\GEODATA\" goto copy
goto missing
:copy
echo Copying X-COM game files (one time only)...
for %%D in (GEODATA GEOGRAPH MAPS ROUTES SOUND TERRAIN UFOGRAPH UFOINTRO UNITS) do robocopy "%XC%\%%D" "UFO\%%D" /E /NFL /NDL /NJH /NJS /NP >nul
if not exist "UFO\GEODATA\" goto missing
:play
rem Full screen at the desktop resolution, battlescape at screen/4 so the 4x map lands 1:1 on screen.
set W=1920
set H=1080
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; 'set W=' + $b.Width; 'set H=' + $b.Height" > "%TEMP%\oxce4x_res.bat" 2>nul
if exist "%TEMP%\oxce4x_res.bat" call "%TEMP%\oxce4x_res.bat"
if not exist "user\" mkdir "user"
rem A mod_update.zip next to this file is unpacked into user\mods before the game starts, then renamed so it runs once.
if exist "mod_update.zip" (
  echo Applying mod_update.zip...
  powershell -NoProfile -Command "Expand-Archive -Force -Path 'mod_update.zip' -DestinationPath 'user\mods'"
  if exist "mod_update_applied.zip" del "mod_update_applied.zip"
  ren "mod_update.zip" "mod_update_applied.zip"
)
set OXCE_BATTLE_SCALE=4
set OXCE_MAP_HIRES=4
start "" OpenXcom.exe -user "%~dp0user" -cfg "%~dp0user" -fullscreen true -displayWidth %W% -displayHeight %H% -battlescapeScale 6 -lazyLoadResources false
exit /b 0
:missing
echo Could not find the X-COM game files.
echo Put the "XCom UFO Defense" folder from Steam next to this file, or copy GEODATA, GEOGRAPH, MAPS,
echo ROUTES, SOUND, TERRAIN, UFOGRAPH, UFOINTRO and UNITS into a UFO folder next to this file.
pause
exit /b 1
