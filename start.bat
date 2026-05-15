@echo off
title RAG Knowledge Base - Production
echo ========================================
echo   RAG Knowledge Base - Starting...
echo ========================================
echo.

cd /d D:\RAG\backend

echo [1/2] Activating Python env...
call C:\Users\wangf\anaconda3\Scripts\activate.bat
call conda activate rag

echo [2/2] Starting server at http://localhost:8000
echo   Close this window to stop the server.
echo ========================================
start http://localhost:8000

uvicorn main:app --host 0.0.0.0 --port 8000

pause
