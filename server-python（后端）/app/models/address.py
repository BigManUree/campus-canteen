from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, func

from app.db.base import Base


class UserAddress(Base):
    __tablename__ = "user_addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    receiver = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    building = Column(String(100), nullable=False)
    room = Column(String(50), nullable=False)
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    is_default = Column(Integer, default=0)
    create_time = Column(DateTime, default=func.now())


