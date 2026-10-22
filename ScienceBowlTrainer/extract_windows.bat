@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup_windows.bat first to install dependencies.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" extract_science_bowl.py --input input --output output
if errorlevel 1 echo Extraction failed. Check messages above.
echo.
echo Check output\file_report.csv and output\questions_needing_review.csv.
pause
