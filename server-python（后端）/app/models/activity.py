from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.db.base import Base


class Activity(Base):
    __tablename__ = "activities"

    activity_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(255))
    content = Column(Text)
    cover_image = Column(String(255))
    organizer = Column(String(100))
    location = Column(String(255))
    contact_name = Column(String(50))
    contact_phone = Column(String(30))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)  # 0下线，1发布
    sort_order = Column(Integer, default=0)
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
