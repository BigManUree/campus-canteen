from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    rating = Column(Integer, nullable=False)
    content = Column(Text)
    images = Column(Text)
    media_path = Column(String(255))
    media_type = Column(String(20))
    is_anonymous = Column(Boolean, nullable=False, default=True, server_default="1")
    reply_content = Column(Text)
    reply_time = Column(DateTime)
    reply_user_id = Column(Integer, ForeignKey("users.user_id"))
    create_time = Column(DateTime, default=func.now())

    user = relationship("User", foreign_keys=[user_id], backref="reviews")
    dish = relationship("Dish", backref="dish_reviews")
    order = relationship("Order", backref="order_reviews")
    reply_user = relationship("User", foreign_keys=[reply_user_id])
