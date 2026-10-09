@echo off
echo ============================================================
echo 启动服务器
echo ============================================================
echo.

cd /d "%~dp0"

echo 检查虚拟环境...
if not exist "venv\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在
    echo 请先运行: python -m venv venv
    pause
    exit /b 1
)

echo 启动 FastAPI 服务器...
echo 地址: http://localhost:8000
echo 文档: http://localhost:8000/docs
echo WebSocket: ws://localhost:8000/api/ws/notifications
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================================
echo.

venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

