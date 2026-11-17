@echo off
REM Cartel render on this PC, offline. Uses the Python 3.13 + Blender module that SETUP_v3.bat installed.
cd /d "%~dp0"
py -3.13 -c "import bpy, numpy, scipy, PIL" 2>nul
if errorlevel 1 (
  echo Installing the render modules once - about 1 GB, a few minutes...
  py install 3.13
  py -3.13 -m pip install bpy==5.3.0 numpy scipy pillow
)
py -3.13 render_cartel.py %*
echo.
echo Finished. Sheets: C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\Reference\sheets\cartel
echo Log: C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\render_work\render_log.txt
pause
