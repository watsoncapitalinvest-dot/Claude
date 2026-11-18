@echo off
rem G.I. JOE 4x - JOE LAB. The offline hub: campaign simulator, battle simulator, strategy runs, the render machine,
rem every run kept, balance numbers, design notes. Put this and joe_lab.py next to OpenXcom.exe and double-click this.
rem It runs on this PC only: no internet, no AI. It uses the Python the render machine installed (py -3.13).
cd /d "%~dp0"
py -3.13 -c "import tkinter" >nul 2>&1 || ( echo Python 3.13 is not installed. Run Reference\walk16_kit\SETUP_v3.bat once, then try again. & pause & exit /b 1 )
start "" py -3.13 joe_lab.py
