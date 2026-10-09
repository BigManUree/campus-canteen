from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
import time

from app.api.v1 import (
    auth,
    users,
    canteens,
    dishes,
    orders,
    media,
    location,
    address,
    favorite,
    review,
    cart,
    message,
    window,
    coupon,
    statistics,
    notification,
    refund,
    canteen_review,
    export,
    activity,
    faq,
    search,
    browse,
    websocket,
)
from app.core.logging import logger
from app.core.config import get_settings

settings = get_settings()

# ============================================================
# FastAPI 应用初始化
# ============================================================
app = FastAPI(
    title="校园食堂点餐系统 API",
    description="基于 FastAPI + SQLAlchemy + MySQL 的后端服务",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production() else None,  # 生产环境可选择关闭文档
    redoc_url="/redoc" if not settings.is_production() else None,
    openapi_url="/openapi.json" if not settings.is_production() else None,
)

# ============================================================
# 中间件配置
# ============================================================

# 1. CORS 跨域配置（必须在其他中间件之前）
cors_origins = settings.get_cors_origins_list()
cors_methods = settings.get_cors_methods_list()
cors_headers = settings.get_cors_headers_list()
cors_expose_headers = settings.get_cors_expose_headers_list()

logger.info(f"CORS 配置: origins={cors_origins}, credentials={settings.cors_allow_credentials}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
    expose_headers=cors_expose_headers if cors_expose_headers else None,
    max_age=settings.cors_max_age,
)

# 2. GZip 压缩（提升传输效率）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的日志"""
    start_time = time.time()

    logger.info(f"请求开始: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"状态码={response.status_code} 耗时={process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"请求异常: {request.method} {request.url.path} "
            f"错误={str(e)} 耗时={process_time:.3f}s"
        )
        raise

# ============================================================
# 全局异常处理
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证错误"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    logger.warning(f"参数验证失败: {request.url.path} - {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "errors": errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未捕获的异常: {request.url.path} - {repr(exc)}", exc_info=True)

    if settings.is_production():
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试"
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )

# ============================================================
# 应用生命周期事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("校园食堂点餐系统 API 启动中...")
    logger.info(f"运行环境: {settings.env}")
    logger.info(f"数据库: {settings.database_url.split('@')[-1]}")
    logger.info(f"监听地址: {settings.host}:{settings.port}")
    logger.info("=" * 60)

    try:
        from app.services.scheduler_service import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 60)
    logger.info("校园食堂点餐系统 API 正在关闭...")
    logger.info("=" * 60)

    try:
        from app.services.scheduler_service import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {e}", exc_info=True)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(canteens.router, prefix="/api")
app.include_router(dishes.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(location.router, prefix="/api")
app.include_router(address.router, prefix="/api")
app.include_router(favorite.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(message.router, prefix="/api")
app.include_router(window.router, prefix="/api")
app.include_router(coupon.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(notification.router, prefix="/api/notification", tags=["通知"])
app.include_router(refund.router, prefix="/api/refund", tags=["退款"])
app.include_router(canteen_review.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(faq.router, prefix="/api")
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(browse.router, prefix="/api", tags=["浏览历史"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

from app.storage import media as media_store

uploads_dir = Path(media_store.get_upload_dir())
try:
    uploads_dir.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.warning(f"上传文件目录创建失败: {uploads_dir} - {e}")

if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    logger.info(f"上传文件目录已挂载: /uploads -> {uploads_dir}")
else:
    logger.warning(f"上传文件目录不存在: {uploads_dir}")


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico")
def favicon():
    favicon_path = static_dir / "favicon.ico"
    if favicon_path.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(favicon_path))
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    """健康检查端点"""
    logger.info("health check ok")
    return {"status": "ok", "version": "1.0.0"}


@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """处理 OPTIONS 预检请求
    
    虽然 CORSMiddleware 会自动处理 OPTIONS 请求，
    但显式添加此端点可以确保所有路径都能正确响应预检请求
    """
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600",
        }
    )

