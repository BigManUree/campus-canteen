from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    item_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    dish_name = Column(String(200), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)  # 修复：单价以元为单位，与菜品表保持一致
    quantity = Column(Integer, nullable=False)
    remark = Column(String(200))
    create_time = Column(DateTime, default=func.now())

    # 添加与 Dish 的关系
    dish = relationship("Dish", foreign_keys=[dish_id])


