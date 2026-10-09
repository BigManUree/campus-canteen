from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Favorite(Base):
    __tablename__ = "favorites"

    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    create_time = Column(DateTime, default=func.now())
    
    # 关系定义
    dish = relationship("Dish", backref="favorites")


