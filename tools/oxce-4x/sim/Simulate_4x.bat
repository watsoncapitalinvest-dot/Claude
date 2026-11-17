@echo off
rem G.I. JOE 4x - THE UNATTENDED SIMULATOR (John 17 Nov 15:00: "a testing simulator local to my computer that will run the
rem game non stop and just record data and logs ... without further AI support until we analyze the data").
rem
rem Put this file in C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x (next to OpenXcom.exe) and double-click it.
rem It plays one campaign year after another with nobody at the controls, round and round through three player
rem styles (absent, typical, aggressive) and three Cobra head starts (0, 6, 12 months), and keeps every run's account
rem and log in sim_runs\. It never touches your own saves or settings: it plays in its own folder, user_sim\.
rem
rem To stop it: close this window, or create a file called STOP.txt next to this file (it stops after the run in hand).
rem
rem WHAT IT IS: the strategy layer only. Battles are not fought on screen; the style's odds decide them. It shows
rem what Cobra builds, when, and how the money, the leads, the events and the story beats land over a year.
rem A year takes roughly a minute, so a night is several hundred years.

setlocal enabledelayedexpansion
cd /d "%~dp0"
if not exist "OpenXcom.exe" ( echo Put this file next to OpenXcom.exe. & pause & exit /b 1 )
if not exist "user\mods\GIJoe4x" ( echo Start the game once with Play_4x.bat first, so the mod is unpacked. & pause & exit /b 1 )

rem the simulator's own folder: the mod and your options copied in, nothing of yours changed
if not exist "user_sim" mkdir "user_sim"
echo Copying the mod into the simulator's own folder...
robocopy "user\mods" "user_sim\mods" /MIR /NFL /NDL /NJH /NJS /NP >nul
if exist "user\options.cfg" copy /y "user\options.cfg" "user_sim\options.cfg" >nul
for %%F in (UFO) do if exist "user\%%F" robocopy "user\%%F" "user_sim\%%F" /MIR /NFL /NDL /NJH /NJS /NP >nul

if not exist "sim_runs" mkdir "sim_runs"
set DAYS=365
set N=0
:loop
for %%S in (absent typical aggressive) do (
  for %%H in (0 6 12) do (
    if exist "STOP.txt" goto done
    set /a N+=1
    set TAG=run!N!_%%S_head%%H
    echo [!date! !time!] run !N!: %%S player, Cobra head start %%H months
    set OXCE_FASTFORWARD=%DAYS%
    set OXCE_FF_STYLE=%%S
    set OXCE_FF_HEADSTART=%%H
    set OXCE_FF_REPORT=%~dp0sim_runs\!TAG!_report.txt
    set OXCE_BATTLE_SCALE=4
    set OXCE_MAP_HIRES=4
    start "" /wait /min OpenXcom.exe -user "%~dp0user_sim" -cfg "%~dp0user_sim" -displayWidth 800 -displayHeight 500 -fullscreen false -lazyLoadResources false -debug false
    if exist "user_sim\openxcom.log" copy /y "user_sim\openxcom.log" "sim_runs\!TAG!_log.txt" >nul
    if not exist "sim_runs\!TAG!_report.txt" echo !TAG!: NO REPORT - the game stopped early, see the log >> "sim_runs\problems.txt"
    findstr /c:"[FATAL]" /c:"[ERROR]" "sim_runs\!TAG!_log.txt" >nul 2>&1 && echo !TAG!: errors in the log >> "sim_runs\problems.txt"
  )
)
goto loop
:done
del "STOP.txt" >nul 2>&1
echo Stopped after !N! runs. Everything is in sim_runs\.
pause
