from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Window(Base):
    __tablename__ = "windows"

    window_id = Column(Integer, primary_key=True, index=True)
    canteen_id = Column(Integer, ForeignKey("canteens.canteen_id"), nullable=False, index=True)
    window_name = Column(String(50), nullable=False)
    parent_id = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    create_time = Column(DateTime, default=func.now())

    canteen = relationship("Canteen")
