@echo off
REM Cartel render on this PC. Needs Blender 5.x and Python 3 (python.org or the Python install manager).
cd /d "%~dp0"
python -m pip install --quiet numpy pillow scipy
python render_cartel.py %*
echo.
echo Finished. Sheets: C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\Reference\sheets\cartel
pause
