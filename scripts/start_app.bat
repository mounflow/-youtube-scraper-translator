@echo off
echo Starting API Server...
start "YouTube API" cmd /k "uvicorn api:app --reload --port 8000"

timeout /t 3

echo Starting Web UI...
streamlit run ui.py
