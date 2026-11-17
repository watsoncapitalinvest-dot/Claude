@echo off
REM RENDER MACHINE app. Double-click to open the window.
cd /d "%~dp0"
py -3.13 -c "import bpy, numpy, scipy, PIL, tkinter" 2>nul
if errorlevel 1 (
  echo Installing the render modules once - about 1 GB, a few minutes...
  py install 3.13
  py -3.13 -m pip install bpy==5.3.0 numpy scipy pillow
)
where pyw >nul 2>nul
if errorlevel 1 (
  start "Render Machine" /min py -3.13 render_app.py
) else (
  start "" pyw -3.13 render_app.py
)
