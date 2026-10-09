import os
import sys
from pathlib import Path
from loguru import logger

# 移除默认处理器
logger.remove()

# 从环境变量读取配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "")
ENV = os.getenv("ENV", "development")

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 控制台输出
logger.add(
    sink=sys.stdout,
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=ENV == "development",  # 生产环境不显示变量值
)

# 文件输出（如果配置了日志文件）
if LOG_FILE:
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 普通日志（按天轮转）
    logger.add(
        sink=str(log_path),
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        backtrace=True,
        diagnose=False,  # 文件日志不显示变量值
    )
    
    # 错误日志（单独文件）
    error_log_path = log_path.parent / f"{log_path.stem}_error{log_path.suffix}"
    logger.add(
        sink=str(error_log_path),
        level="ERROR",
        format=LOG_FORMAT,
        rotation="10 MB",  # 按大小轮转
        retention="90 days",  # 错误日志保留90天
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,  # 错误日志显示详细信息
    )

__all__ = ["logger"]

