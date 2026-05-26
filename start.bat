@echo off
title RAG Knowledge Base - Production
echo ========================================
echo   RAG Knowledge Base - Starting...
echo ========================================
echo.

cd /d D:\RAG\backend

echo [0/4] Killing old process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (taskkill /F /PID %%a 2>nul)

echo [1/4] Starting backend server...
start "KB_Backend" cmd /k "cd /d D:\RAG\backend && call C:\Users\wangf\anaconda3\Scripts\activate.bat && call conda activate rag && uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/4] Waiting for backend to be ready...
:wait_backend
timeout /t 2 >nul
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo   Still loading model...
    goto wait_backend
)
echo   Backend ready!

echo [3/4] Starting ngrok tunnel...
set NGROK_PATH=C:\Users\wangf\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe
start "KB_Ngrok" cmd /k ""%NGROK_PATH%" http 8000 --log=stdout"

echo [4/4] Waiting for ngrok tunnel...
:wait_ngrok
timeout /t 2 >nul
for /f "delims=" %%u in ('powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:4040/api/tunnels' -Method Get; $r.tunnels[0].public_url } catch { Write-Output '' }" 2^>nul') do set "NGROK_URL=%%u"
if "%NGROK_URL%"=="" (
    echo   Establishing tunnel...
    goto wait_ngrok
)

echo.
echo ========================================
echo   Local:    http://localhost:8000
echo   Public:   %NGROK_URL%
echo   Close the KB_Backend ^& KB_Ngrok
echo   windows to stop the server.
echo ========================================
start %NGROK_URL%

echo.
echo Press any key to close this window...
pause >nul
