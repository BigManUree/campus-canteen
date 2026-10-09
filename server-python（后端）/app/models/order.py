from sqlalchemy import Column, Integer, String, DECIMAL, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    canteen_id = Column(Integer, ForeignKey("canteens.canteen_id"), nullable=False)
    order_type = Column(Enum("pickup", "delivery", name="order_type"), default="pickup")
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=0)  # 优惠金额
    pay_amount = Column(DECIMAL(10, 2), nullable=False)
    pay_status = Column(Integer, default=0)
    pay_time = Column(DateTime, nullable=True)  # 支付时间
    order_status = Column(Integer, default=0)
    pickup_code = Column(String(20))
    pickup_time = Column(DateTime)
    verify_time = Column(DateTime, nullable=True)  # 核销时间
    accept_time = Column(DateTime, nullable=True)  # 接单时间
    ready_time = Column(DateTime, nullable=True)  # 制作完成时间
    complete_time = Column(DateTime, nullable=True)  # 订单完成时间
    cancel_time = Column(DateTime, nullable=True)  # 取消时间
    cancel_reason = Column(String(200), nullable=True)  # 取消原因
    delivery_address = Column(String(255))
    delivery_latitude = Column(DECIMAL(10, 7))
    delivery_longitude = Column(DECIMAL(10, 7))
    remark = Column(String(500))
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    canteen = relationship("Canteen", foreign_keys=[canteen_id], lazy="joined")  # 自动加载档口信息


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    dish_name = Column(String(200), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    remark = Column(String(200))
    create_time = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="items")

