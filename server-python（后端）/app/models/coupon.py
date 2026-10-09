from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Coupon(Base):
    __tablename__ = "coupons"

    coupon_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 优惠券名称
    description = Column(String(255))  # 描述
    coupon_type = Column(Enum("discount", "cash", name="coupon_type"), default="discount")  # 类型：折扣或现金
    discount_value = Column(DECIMAL(10, 2))  # 折扣值或减免金额；折扣券填 8 表示 8 折
    min_amount = Column(DECIMAL(10, 2), default=0)  # 最低消费金额
    max_discount = Column(DECIMAL(10, 2))  # 最大优惠金额（折扣券）
    total_count = Column(Integer, default=-1)  # 总数量，-1表示不限
    used_count = Column(Integer, default=0)  # 历史字段名，实际含义为已领取数量
    start_time = Column(DateTime, nullable=False)  # 开始时间
    end_time = Column(DateTime, nullable=False)  # 结束时间
    status = Column(Integer, default=1)  # 状态：0禁用，1启用
    create_time = Column(DateTime, default=func.now())

    @property
    def claimed_count(self):
        return self.used_count or 0


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.coupon_id"), nullable=False)
    status = Column(Integer, default=0)  # 0未使用，1已使用，2已过期
    used_time = Column(DateTime)  # 使用时间
    used_order_id = Column(Integer, ForeignKey("orders.order_id"))  # 使用的订单ID
    get_time = Column(DateTime, default=func.now())  # 领取时间
    expire_time = Column(DateTime)  # 过期时间

    coupon = relationship("Coupon")

