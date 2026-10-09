from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CanteenReviewCreate(BaseModel):
    order_id: int
    canteen_id: int
    rating: int  # 总体评分 1-5
    service_rating: Optional[int] = None  # 服务态度评分
    speed_rating: Optional[int] = None  # 出餐速度评分
    content: Optional[str] = None
    images: Optional[str] = None


class CanteenReviewOut(BaseModel):
    review_id: int
    order_id: int
    canteen_id: int
    user_id: int
    rating: int
    service_rating: Optional[int] = None
    speed_rating: Optional[int] = None
    content: Optional[str] = None
    images: Optional[str] = None
    create_time: datetime

    class Config:
        from_attributes = True

