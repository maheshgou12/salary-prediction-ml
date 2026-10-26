@echo off
title FairSalary AI - Local Offline Launcher
echo ==========================================================
echo   FairSalary AI - Starting Local and Offline Environment
echo ==========================================================
echo.

echo [1/2] Starting Backend API on http://127.0.0.1:8000 ...
start "FairSalary Backend (FastAPI)" cmd /k "cd /d %~dp0FairSalaryAI\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Frontend Dashboard on http://localhost:5173 ...
start "FairSalary Frontend (Vite React)" cmd /k "cd /d %~dp0FairSalaryAI\frontend && npm run dev"

echo.
echo ==========================================================
echo   Both services started in dedicated terminal windows!
echo   Frontend Dashboard: http://localhost:5173
echo   Backend Swagger:    http://127.0.0.1:8000/docs
echo   Status:             100%% Offline Capable (No Internet Needed)
echo ==========================================================
echo.
timeout /t 3 >nul
start http://localhost:5173
