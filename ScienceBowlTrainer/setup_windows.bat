@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo  Science Bowl Trainer - First-time Setup
 echo ========================================
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -m venv .venv
    ) else (
        python -m venv .venv
    )
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Could not find Python. Install Python 3.11+ and reopen VS Code.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
 echo.
 echo Setup complete. Run start_windows.bat to open the trainer.
 pause
 exit /b 0
:failed
 echo.
 echo Installation failed. Review the error messages above.
 pause
 exit /b 1
