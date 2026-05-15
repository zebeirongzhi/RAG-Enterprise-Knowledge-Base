@echo off
title 企业知识库 - 生产模式
echo ========================================
echo   企业知识库系统 - 启动中...
echo ========================================
echo.

cd /d D:\RAG\backend

echo [1/2] 激活 Python 环境...
call C:\Users\wangf\anaconda3\Scripts\activate.bat
call conda activate rag

echo [2/2] 启动服务...
echo.
echo   打开浏览器访问: http://localhost:8000
echo   关闭此窗口即可停止服务
echo ========================================
start http://localhost:8000

uvicorn main:app --host 0.0.0.0 --port 8000

pause
