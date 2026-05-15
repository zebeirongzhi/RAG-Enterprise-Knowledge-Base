@echo off
echo ========================================
echo   RAG Knowledge Base - Dev Mode
echo   Backend :8000  |  Frontend :5173
echo ========================================
echo.

cd /d D:\RAG

echo Killing old process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (taskkill /F /PID %%a 2>nul)

echo Starting backend...
start "KB-Backend" cmd /c "call C:\Users\wangf\anaconda3\Scripts\activate.bat && call conda activate rag && cd /d D:\RAG\backend && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting frontend dev server...
start "KB-Frontend" cmd /c "cd /d D:\RAG\frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo ========================================
timeout /t 3 >nul
start http://localhost:5173
