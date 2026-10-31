@echo off
cd /d "%~dp0"
echo This installs the optional websocket-client and sounddevice Python packages.
py -3 -m pip install websocket-client sounddevice
if errorlevel 1 echo Installation failed. See the error above.
pause
