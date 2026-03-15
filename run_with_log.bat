@echo off
echo ========================================
echo YouTube Video Downloader with Logging
echo ========================================
echo.

chcp 65001 > nul
cd /d "%~dp0"

REM Create logs directory if not exists
if not exist logs mkdir logs

set LOG_FILE=logs\download_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

echo Log file: %LOG_FILE%
echo.

REM Run with output redirection
python main.py -u "https://www.youtube.com/watch?v=eMZmDH3T2bY" -c chrome -y 2>&1 | tee -a %LOG_FILE%

echo.
echo Log saved to: %LOG_FILE%
pause
