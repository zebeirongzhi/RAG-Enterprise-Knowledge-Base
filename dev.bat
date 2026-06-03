@echo off
echo ========================================
echo   RAG Knowledge Base - Dev Mode
echo   Backend :8000  /  Frontend :5173
echo ========================================

cd /d "D:\RAG"

echo.
echo Killing old process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul

echo Starting backend...
start "KB_Backend" cmd /k "cd /d D:\RAG\backend && call C:\Users\wangf\anaconda3\Scripts\activate.bat && call conda activate rag && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting frontend dev server...
start "KB_Frontend" cmd /k "cd /d D:\RAG\frontend && npm run dev"

echo Waiting for backend to be ready...
:wait_be
timeout /t 2 >nul
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo   Still loading...
    goto wait_be
)

echo Waiting for frontend to be ready...
:wait_fe
timeout /t 2 >nul
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo   Still starting...
    goto wait_fe
)

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
start http://localhost:5173
pause
