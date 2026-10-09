from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Dish(Base):
    __tablename__ = "dishes"

    dish_id = Column(Integer, primary_key=True, index=True)
    canteen_id = Column(Integer, ForeignKey("canteens.canteen_id"), nullable=False)
    window_id = Column(Integer, ForeignKey("windows.window_id"), default=0)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2))
    spicy_level = Column(Integer, default=0)
    allergen = Column(String(200))
    calorie = Column(Integer)
    images = Column(Text)
    stock = Column(Integer, default=999)
    sales = Column(Integer, default=0)
    status = Column(Integer, default=1)
    media_path = Column(String(255))
    media_type = Column(Enum("audio", "video", name="dish_media_type"), nullable=True)
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    canteen = relationship("Canteen")
    window = relationship("Window")
