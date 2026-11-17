@echo off
REM Civilians on this PC, offline: every .blend in Reference\civ, unarmed poses.
cd /d "%~dp0"
call RENDER_CARTEL.bat --civ %*
