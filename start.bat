@echo off
title RAG Knowledge Base - Production
echo ========================================
echo   RAG Knowledge Base - Starting...
echo ========================================
echo.

cd /d D:\RAG\backend

echo [0/3] Killing old process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (taskkill /F /PID %%a 2>nul)

echo [1/3] Starting backend server...
start "KB_Backend" cmd /k "cd /d D:\RAG\backend && call C:\Users\wangf\anaconda3\Scripts\activate.bat && call conda activate rag && set HF_HUB_OFFLINE=1 && set TRANSFORMERS_OFFLINE=1 && uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Waiting for server to be ready...
:wait
timeout /t 2 >nul
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo   Still loading... (model initialization takes ~20s)
    goto wait
)

echo [3/3] Server ready! Opening browser...
echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Close the KB_Backend window to stop.
echo ========================================
start http://localhost:8000

echo.
echo Press any key to close this window...
pause >nul
