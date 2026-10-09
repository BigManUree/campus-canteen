from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Enum, Boolean, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Notification(Base):
    """通知消息表 - 用于WebSocket消息持久化"""
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(200), nullable=False)  # 通知标题
    message = Column(Text, nullable=False)  # 通知内容
    notification_type = Column(
        Enum("urgent", "normal", "marketing", name="notification_type"), 
        default="normal"
    )  # 通知类型：urgent(紧急), normal(普通), marketing(营销)
    category = Column(String(50))  # 通知分类：refund, order, pickup, promotion等
    related_id = Column(Integer)  # 关联ID（订单ID、退款ID等）
    is_read = Column(Boolean, default=False)  # 是否已读
    is_pushed = Column(Boolean, default=False)  # 是否已推送
    priority = Column(Integer, default=0)  # 优先级：0=普通, 1=重要, 2=紧急
    create_time = Column(DateTime, default=func.now())
    read_time = Column(DateTime)  # 已读时间
    
    # 关系定义
    user = relationship("User", backref="notifications")

