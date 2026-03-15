@echo off
echo ========================================
echo YouTube Video Downloader & Translator
echo ========================================
echo.

REM Switch to UTF-8 encoding
chcp 65001 > nul

REM Change to script directory
cd /d "%~dp0"

echo Current directory: %CD%
echo Python version:
python --version
echo.

echo Starting download and translation...
echo.

REM Run the main script
python main.py -u "https://www.youtube.com/watch?v=eMZmDH3T2bY" -c chrome -y

echo.
echo ========================================
echo Process completed!
echo ========================================
pause
