from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Text, func

from app.db.base import Base


class Canteen(Base):
    __tablename__ = "canteens"

    canteen_id = Column(Integer, primary_key=True, index=True)
    canteen_name = Column(String(100), nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(String(20))
    window_no = Column(String(50))
    service_type = Column(String(50), default="pickup")
    open_time = Column(String(100))
    close_time = Column(String(100))
    contact_phone = Column(String(20))
    contact_person = Column(String(50))
    description = Column(Text)
    rest_days = Column(String(100))
    sort_order = Column(Integer, default=0)
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    address = Column(String(255))
    avatar = Column(String(255))
    notice = Column(Text)
    notice_enabled = Column(Integer, default=1)
    location = Column(String(255))
    business_hours = Column(String(100))
    avg_price = Column(DECIMAL(10, 2))
    status = Column(Integer, default=1)
    merchant_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)  # 商家用户ID
    create_time = Column(DateTime, default=func.now())

