from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.db.base import Base


class CanteenReview(Base):
    __tablename__ = "canteen_reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    canteen_id = Column(Integer, ForeignKey("canteens.canteen_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 评分 1-5
    service_rating = Column(Integer)  # 服务态度评分
    speed_rating = Column(Integer)  # 出餐速度评分
    content = Column(Text)
    images = Column(Text)
    create_time = Column(DateTime, default=func.now())

