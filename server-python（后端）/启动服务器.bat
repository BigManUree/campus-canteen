@echo off
chcp 65001 >nul
echo ============================================================
echo 启动校园食堂点餐系统后端服务
echo ============================================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先创建虚拟环境
    echo.
    echo 创建虚拟环境命令:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 检查 .env 文件
if not exist ".env" (
    echo.
    echo ⚠️  警告: .env 文件不存在
    echo 正在从 config.example.env 复制...
    copy config.example.env .env
    echo.
    echo ✅ 已创建 .env 文件
    echo ⚠️  请编辑 .env 文件，修改数据库密码等配置
    echo.
    pause
)

REM 启动服务
echo.
echo 正在启动服务器...
echo 访问地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================================
echo.

python run_server.py

pause

