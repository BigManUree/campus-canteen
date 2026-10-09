from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

# 创建数据库引擎（生产环境优化配置）
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_size=settings.db_pool_size,  # 连接池大小
    max_overflow=settings.db_max_overflow,  # 最大溢出连接数
    pool_recycle=settings.db_pool_recycle,  # 连接回收时间（秒）
    echo=False,  # 生产环境不打印 SQL
    echo_pool=False,  # 不打印连接池日志
)

# 连接池事件监听（用于监控）
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """连接建立时的回调"""
    logger.debug("数据库连接已建立")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """从连接池获取连接时的回调"""
    logger.debug("从连接池获取连接")

@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """连接归还到连接池时的回调"""
    logger.debug("连接归还到连接池")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

