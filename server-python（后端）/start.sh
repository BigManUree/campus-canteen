#!/bin/bash

echo "========================================"
echo "校园食堂点餐系统 - Python 后端启动脚本"
echo "========================================"
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[错误] 虚拟环境不存在，请先执行以下命令创建："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "[警告] .env 文件不存在，正在从 config.example.env 创建..."
    cp config.example.env .env
    echo "[提示] 请编辑 .env 文件，配置数据库连接等信息"
    echo ""
fi

# 启动服务
echo "[信息] 正在启动 FastAPI 服务..."
echo "[信息] API 文档地址: http://localhost:8000/docs"
echo "[信息] 按 Ctrl+C 停止服务"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

