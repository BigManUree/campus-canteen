from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    title = Column(String(100), default="系统通知")  # 消息标题
    content = Column(Text, nullable=False)
    type = Column(Integer, default=1)  # 1客服 2系统
    message_type = Column(String(20), default="system")  # system/order/activity
    is_read = Column(Integer, default=0)
    read_time = Column(DateTime, nullable=True)  # 阅读时间
    create_time = Column(DateTime, default=func.now())


