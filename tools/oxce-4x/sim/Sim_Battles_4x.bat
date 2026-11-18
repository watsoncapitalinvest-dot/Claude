@echo off
rem G.I. JOE 4x - THE BATTLE SIMULATOR (John 17 Nov 18:09-18:12: "an offline simulator that can run the game and test it").
rem
rem Put this file in C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x (next to OpenXcom.exe) and double-click it.
rem The computer plays EVERY New Battle mission, one after another, playing the Joes as well as Cobra, and starts
rem again from the first when it has done them all. Each battle is its own run of the game, so a crash costs one
rem battle and the next one starts. Your saves and settings are never touched: it plays in user_sim\.
rem
rem What you get, in sim_battles\:
rem   results.txt                one line a battle: WIN / LOSS / CRASH / HANG / STUCK / NO RESULT, turns, score, losses
rem   problems.txt               only the runs that went wrong, and runs whose log has errors
rem   r<run>_m<mission>\         that battle's pictures (briefing, turns, debrief, any stuck screen), events.txt, its log
rem
rem To stop it: close this window, or create a file called STOP.txt next to this file (it stops after the battle in hand).
rem WHAT IT IS: it finds crashes, hangs, screens nobody can get past, turns that never end and errors in the log.
rem It cannot tell whether a mission is fun or fair - the Joes are played by Cobra's AI, which is not a player.

setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist "OpenXcom.exe" ( echo Put this file next to OpenXcom.exe. & pause & exit /b 1 )
if not exist "user\mods\GIJoe4x" ( echo Start the game once with Play_4x.bat first, so the mod is unpacked. & pause & exit /b 1 )

if not exist "user_sim" mkdir "user_sim"
echo Copying the mod into the simulator's own folder...
robocopy "user\mods" "user_sim\mods" /MIR /NFL /NDL /NJH /NJS /NP >nul
if exist "user\options.cfg" copy /y "user\options.cfg" "user_sim\options.cfg" >nul
for %%F in (UFO) do if exist "user\%%F" robocopy "user\%%F" "user_sim\%%F" /MIR /NFL /NDL /NJH /NJS /NP >nul
if not exist "sim_battles" mkdir "sim_battles"

set RUN=0
:round
set M=0
:next
if exist "STOP.txt" goto done
set /a RUN+=1
set D=sim_battles\r!RUN!_m!M!
if exist "!D!" rmdir /s /q "!D!"
mkdir "!D!"
echo [!date! !time!] battle !RUN!: New Battle mission !M!
set OXCE_BATTLESIM=!M!
set OXCE_BATTLESIM_OUT=%~dp0!D!
set OXCE_BATTLESIM_TURNS=30
rem how each side plays: defensive, normal or aggressive
set OXCE_BATTLESIM_JOES=normal
set OXCE_BATTLESIM_COBRA=normal
set OXCE_BATTLE_SCALE=4
set OXCE_MAP_HIRES=4
start "" /wait OpenXcom.exe -user "%~dp0user_sim" -cfg "%~dp0user_sim" -displayWidth 1280 -displayHeight 800 -fullscreen false -debug false
set CODE=!errorlevel!
if exist "user_sim\openxcom.log" copy /y "user_sim\openxcom.log" "!D!\log.txt" >nul
set R=
if exist "!D!\result.txt" set /p R=<"!D!\result.txt"
if not defined R set R=CRASH mission !M! exit code !CODE! - see !D!\log.txt
echo r!RUN! m!M!: !R!>> "sim_battles\results.txt"
echo    !R!
echo !R! | findstr /b /c:"NO MISSION" >nul && goto wrap
echo !R! | findstr /b /c:"WIN" /c:"LOSS" >nul || echo r!RUN! m!M!: !R!>> "sim_battles\problems.txt"
findstr /c:"[FATAL]" /c:"[ERROR]" "!D!\log.txt" >nul 2>&1 && echo r!RUN! m!M!: errors in the log - see !D!\log.txt>> "sim_battles\problems.txt"
set /a M+=1
goto next
:wrap
rmdir /s /q "!D!"
if !M!==0 goto done
echo Every mission played. Starting again from the first.
goto round
:done
del "STOP.txt" >nul 2>&1
echo Stopped after !RUN! battles. Everything is in sim_battles\.
pause
