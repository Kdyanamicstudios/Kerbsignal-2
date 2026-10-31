@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (set "RACE_PY=py -3") else (set "RACE_PY=python")
%RACE_PY% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>nul
if errorlevel 1 goto missing

echo This creates RaceEngineer.exe in the extracted main folder.
echo It installs PyInstaller and the optional live-voice packages using pip.
echo An internet connection is required.
echo.
pause
%RACE_PY% -m pip install --upgrade pyinstaller websocket-client sounddevice
if errorlevel 1 goto failed
%RACE_PY% -m PyInstaller --noconfirm --clean --windowed --onefile --name RaceEngineer --distpath "%~dp0.." --workpath "%TEMP%\RaceEngineerBuild" --specpath "%TEMP%\RaceEngineerBuild" --hidden-import websocket --hidden-import sounddevice --add-data "engineer\recognize.ps1;engineer" --add-data "engineer\render_cues.ps1;engineer" --add-data "engineer\list_voices.ps1;engineer" --add-data "engineer\speak.ps1;engineer" app.py
if errorlevel 1 goto failed
echo.
echo Done. The application is RaceEngineer.exe in the main extracted folder.
echo Double-click RaceEngineer.exe to run it.
pause
exit /b 0
:missing
echo Python 3.11 or newer is needed on this PC to build the executable.
echo Install it from https://www.python.org/downloads/windows/ and run this file again.
pause
exit /b 1
:failed
echo The executable build failed. Read the error above.
pause
exit /b 1
