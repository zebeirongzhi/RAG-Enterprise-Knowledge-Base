@echo off
echo ========================================
echo   企业知识库系统 - 开发模式
echo   后端 :8000  |  前端 :5173 (热更新)
echo ========================================
echo.

cd /d D:\RAG

echo 启动后端服务...
start "知识库-后端" cmd /c "call C:\Users\wangf\anaconda3\Scripts\activate.bat && call conda activate rag && cd /d D:\RAG\backend && uvicorn main:app --host 0.0.0.0 --port 8000"

echo 启动前端开发服务器...
start "知识库-前端" cmd /c "cd /d D:\RAG\frontend && npm run dev"

echo.
echo 两个服务正在启动...
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo ========================================
timeout /t 3 >nul
start http://localhost:5173
