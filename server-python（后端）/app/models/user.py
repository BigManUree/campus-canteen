from sqlalchemy import Column, Integer, String, Enum, DateTime, func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    nickname = Column(String(50))
    avatar = Column(String(255))
    gender = Column(Integer, default=0)  # 0未知1男2女
    student_no = Column(String(50))  # 学号/工号
    department = Column(String(100))  # 学院/部门
    role = Column(Enum("user", "merchant", "admin", name="user_role"), default="user")
    status = Column(Integer, default=1)
    order_viewed_all_at = Column(DateTime, nullable=True)
    order_viewed_pending_at = Column(DateTime, nullable=True)
    order_viewed_preparing_at = Column(DateTime, nullable=True)
    order_viewed_ready_at = Column(DateTime, nullable=True)
    order_viewed_delivering_at = Column(DateTime, nullable=True)
    order_viewed_refund_at = Column(DateTime, nullable=True)
    create_time = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    update_time = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())

