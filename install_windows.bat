@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON=python"
    ) else (
        echo Python 3 was not found. Install Python 3.10+ from https://www.python.org/downloads/windows/ and try again.
        exit /b 1
    )
)

%PYTHON% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .

echo.
echo Installation complete.
echo Run run_voice_service.bat to start the service.
pause
