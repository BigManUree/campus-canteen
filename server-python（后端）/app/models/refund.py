from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, func, Enum, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    refund_amount = Column(DECIMAL(10, 2), nullable=False)
    reason = Column(String(500))  # 退款原因描述
    reason_category = Column(String(50))  # 退款原因分类：dont_want, too_long, quality, other
    refund_items = Column(Text)  # 退款菜品列表JSON（部分退款）
    status = Column(Enum("pending", "approved", "rejected", "completed", name="refund_status"), default="pending")
    admin_remark = Column(String(500))  # 管理员备注
    approve_time = Column(DateTime)  # 审批时间
    auto_approved = Column(Boolean, default=False)  # 是否自动批准
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", backref="refunds")
    order = relationship("Order", backref="refunds")

