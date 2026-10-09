from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.db.base import Base


class FAQ(Base):
    __tablename__ = "faqs"

    faq_id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False)  # 问题
    answer = Column(Text, nullable=False)  # 答案
    category = Column(String(50))  # 分类：订单、支付、配送、其他等
    sort_order = Column(Integer, default=0)  # 排序
    status = Column(Integer, default=1)  # 0禁用，1启用
    view_count = Column(Integer, default=0)  # 查看次数
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

