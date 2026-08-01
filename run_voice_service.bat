@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run install_windows.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

set "ROBOT_IP=%ROBOT_IP%"
if "%ROBOT_IP%"=="" set "ROBOT_IP=192.168.12.1"

set "ROBOT_PASSWORD=%ROBOT_PASSWORD%"
if "%ROBOT_PASSWORD%"=="" set "ROBOT_PASSWORD=123"

set "IDLE_INTERVAL=%IDLE_INTERVAL%"
if "%IDLE_INTERVAL%"=="" set "IDLE_INTERVAL=15"

python example_integration.py --robot-ip "%ROBOT_IP%" --password "%ROBOT_PASSWORD%" --idle-interval "%IDLE_INTERVAL%"
pause
