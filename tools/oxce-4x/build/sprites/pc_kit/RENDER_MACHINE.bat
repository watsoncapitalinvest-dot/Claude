@echo off
REM THE RENDER MACHINE: leave this window open. Drop .blend files in Reference\cartel (armed) or Reference\civ (no gun).
REM Each is rendered, checked and filed in Reference\sheets\cartel or \civ. Status: render_work\MACHINE_STATUS.txt
cd /d "%~dp0"
py -3.13 -c "import bpy, numpy, scipy, PIL" 2>nul
if errorlevel 1 (
  echo Installing the render modules once - about 1 GB, a few minutes...
  py install 3.13
  py -3.13 -m pip install bpy==5.3.0 numpy scipy pillow
)
py -3.13 render_cartel.py --watch
pause
