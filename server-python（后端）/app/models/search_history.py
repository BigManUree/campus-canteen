from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey

from app.db.base import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    keyword = Column(String(100), nullable=False)
    search_type = Column(String(20), default="all")  # dish, canteen, all
    create_time = Column(DateTime, default=func.now())


class HotSearch(Base):
    __tablename__ = "hot_search"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, unique=True)
    search_count = Column(Integer, default=1)
    rank = Column("rank", Integer, default=0)  # 使用引号避免保留字冲突
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

