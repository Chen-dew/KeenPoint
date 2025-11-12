@echo off
echo ========================================
echo Starting Academic Paper Assistant API
echo ========================================
echo.
echo Port: 8000
echo Docs: http://localhost:8000/docs
echo.

cd /d %~dp0
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
