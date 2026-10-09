"""
API装饰器工具
用于统一处理错误和日志记录
"""
from functools import wraps
from fastapi import HTTPException
from app.core.logging import logger
import traceback


def handle_api_errors(error_message: str = "操作失败"):
    """
    统一处理API错误的装饰器
    
    Args:
        error_message: 错误消息前缀
        
    Usage:
        @handle_api_errors("获取数据失败")
        def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                error_detail = f"{error_message}: {str(e)}"
                logger.error(f"{error_detail}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=error_detail)
        return wrapper
    return decorator

