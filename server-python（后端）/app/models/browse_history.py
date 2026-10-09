"""浏览历史模型"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class BrowseHistory(Base):
    """菜品浏览历史"""
    __tablename__ = "browse_history"
    __table_args__ = {'extend_existing': True}

    history_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    browse_time = Column(DateTime, default=func.now())
    
    # 关系定义 - 使用 foreign_keys 明确指定外键，避免冲突
    dish = relationship("Dish", foreign_keys=[dish_id], lazy="joined")

