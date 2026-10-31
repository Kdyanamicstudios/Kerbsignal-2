@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 app.py
if errorlevel 1 pause
exit /b
:try_python
where python >nul 2>nul
if errorlevel 1 goto missing
python app.py
if errorlevel 1 pause
exit /b
:missing
echo Install Python 3.11 or newer from python.org with Tcl/Tk and the Python launcher.
echo Then double-click this file again.
pause
