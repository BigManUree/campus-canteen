"""
FastAPI 服务器启动入口（用于打包成 exe）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe
    base_path = Path(sys.executable).parent
else:
    # 开发模式
    base_path = Path(__file__).parent

sys.path.insert(0, str(base_path))

# 设置工作目录
os.chdir(base_path)

# 导入并启动 FastAPI 应用
if __name__ == "__main__":
    import uvicorn
    # 显式导入所有模块，确保 PyInstaller 能正确打包
    import app.api.v1.auth
    import app.api.v1.users
    import app.api.v1.canteens
    import app.api.v1.dishes
    import app.api.v1.orders
    import app.api.v1.media
    import app.api.v1.location
    import app.api.v1.address
    import app.api.v1.favorite
    import app.api.v1.review
    import app.api.v1.cart
    import app.api.v1.message
    import app.api.v1.window
    import app.api.v1.coupon
    import app.api.v1.statistics
    import app.api.v1.notification
    import app.api.v1.refund
    import app.api.v1.canteen_review
    import app.api.v1.export
    import app.api.v1.activity
    import app.api.v1.faq
    import app.api.v1.search
    import app.api.v1.browse
    import app.api.v1.websocket
    # 然后导入主应用
    from app.main import app
    
    # 从环境变量或配置文件读取端口
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("=" * 50)
    print("校园食堂点餐系统 - Python 后端服务")
    print("=" * 50)
    print(f"服务地址: http://localhost:{port}")
    print(f"API 文档: http://localhost:{port}/docs")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

