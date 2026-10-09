from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from app.db.base import Base


class OrderStatusLog(Base):
    __tablename__ = "order_status_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    old_status = Column(Integer, nullable=True)
    new_status = Column(Integer, nullable=False)
    operator_id = Column(Integer, nullable=True)
    operator_name = Column(String(50), nullable=True)
    description = Column(String(200), nullable=True)
    create_time = Column(DateTime, default=func.now(), server_default=func.now())

