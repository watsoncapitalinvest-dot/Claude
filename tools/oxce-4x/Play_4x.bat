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
rem mod_update.zip, mod_update_2.zip, mod_update_3.zip, mod_update_4.zip, mod_update_5.zip, mod_update_6.zip, mod_update_7.zip, mod_update_8.zip, mod_update_9.zip, mod_update_10.zip, mod_update_11.zip, mod_update_12.zip, mod_update_13.zip, mod_update_14.zip, mod_update_15.zip, mod_update_16.zip, mod_update_17.zip, mod_update_18.zip, mod_update_19.zip, mod_update_20.zip, mod_update_21.zip, mod_update_22.zip, mod_update_23.zip, mod_update_24.zip, mod_update_25.zip, mod_update_26.zip, then mod_update_27.zip, mod_update_28.zip, mod_update_29.zip, mod_update_30.zip, mod_update_31.zip, mod_update_32.zip, mod_update_33.zip, mod_update_34.zip, mod_update_35.zip, mod_update_36.zip, mod_update_37.zip, mod_update_38.zip, mod_update_39.zip, mod_update_40.zip, mod_update_41.zip, mod_update_42.zip, mod_update_43.zip, mod_update_44.zip, mod_update_45.zip, mod_update_46.zip, mod_update_47.zip, mod_update_48.zip, mod_update_49.zip, mod_update_50.zip, mod_update_51.zip, mod_update_52.zip, mod_update_53.zip, mod_update_54.zip, mod_update_55.zip, mod_update_56.zip, mod_update_57.zip, mod_update_58.zip, mod_update_59.zip, mod_update_60.zip, mod_update_61.zip, mod_update_62.zip, mod_update_63.zip, mod_update_64.zip, mod_update_65.zip, mod_update_66.zip, next to this file are unpacked into user\mods before the game starts
rem (in that order: each is newer than the one before), then renamed so each runs once.
for %%Z in (mod_update mod_update_2 mod_update_3 mod_update_4 mod_update_5 mod_update_6 mod_update_7 mod_update_8 mod_update_9 mod_update_10 mod_update_11 mod_update_12 mod_update_13 mod_update_14 mod_update_15 mod_update_16 mod_update_17 mod_update_18 mod_update_19 mod_update_20 mod_update_21 mod_update_22 mod_update_23 mod_update_24 mod_update_25 mod_update_26 mod_update_27 mod_update_28 mod_update_29 mod_update_30 mod_update_31 mod_update_32 mod_update_33 mod_update_34 mod_update_35 mod_update_36 mod_update_37 mod_update_38 mod_update_39 mod_update_40 mod_update_41 mod_update_42 mod_update_43 mod_update_44 mod_update_45 mod_update_46 mod_update_47 mod_update_48 mod_update_49 mod_update_50 mod_update_51 mod_update_52 mod_update_53 mod_update_54 mod_update_55 mod_update_56 mod_update_57 mod_update_58 mod_update_59 mod_update_60 mod_update_61 mod_update_62 mod_update_63 mod_update_64 mod_update_65 mod_update_66) do (
  if exist "%%Z.zip" (
    echo Applying %%Z.zip...
    powershell -NoProfile -Command "Expand-Archive -Force -Path '%%Z.zip' -DestinationPath 'user\mods'"
    if exist "%%Z_applied.zip" del "%%Z_applied.zip"
    ren "%%Z.zip" "%%Z_applied.zip"
  )
)
set OXCE_BATTLE_SCALE=4
set OXCE_MAP_HIRES=4
rem The 64-bit game (x64\OpenXcom.exe, its own DLLs beside it) when it is there: no 4 GB memory ceiling (17 Nov crash).
if exist "x64\OpenXcom.exe" goto play64
start "" OpenXcom.exe -user "%~dp0user" -cfg "%~dp0user" -fullscreen true -displayWidth %W% -displayHeight %H% -battlescapeScale 6 -lazyLoadResources false -debug false
exit /b 0
:play64
start "" "x64\OpenXcom.exe" -data "%~dp0." -user "%~dp0user" -cfg "%~dp0user" -fullscreen true -displayWidth %W% -displayHeight %H% -battlescapeScale 6 -lazyLoadResources false -debug false
exit /b 0
:missing
echo Could not find the X-COM game files.
echo Put the "XCom UFO Defense" folder from Steam next to this file, or copy GEODATA, GEOGRAPH, MAPS,
echo ROUTES, SOUND, TERRAIN, UFOGRAPH, UFOINTRO and UNITS into a UFO folder next to this file.
pause
exit /b 1
