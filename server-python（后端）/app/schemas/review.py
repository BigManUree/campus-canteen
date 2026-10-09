from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewUserOut(BaseModel):
    user_id: int
    nickname: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    """创建评价请求

    兼容前端可能使用的驼峰命名：orderId / dishId。
    """

    order_id: int = Field(..., alias="orderId")
    dish_id: int = Field(..., alias="dishId")
    rating: int = Field(..., ge=1, le=5, description="评分1-5星")
    content: Optional[str] = None
    images: Optional[str] = None  # JSON字符串，图片路径列表
    media_path: Optional[str] = None  # 音视频路径
    media_type: Optional[str] = None  # audio或video
    is_anonymous: bool = True

    class Config:
        # 允许同时使用字段名和别名（order_id / orderId 都可以）
        populate_by_name = True


class ReviewReplyIn(BaseModel):
    reply_content: str = Field(..., min_length=1, max_length=1000, description="回复内容")


class ReviewOut(BaseModel):
    review_id: int
    order_id: int
    dish_id: int
    user_id: int
    rating: int
    content: Optional[str] = None
    images: Optional[str] = None
    media_path: Optional[str] = None
    media_type: Optional[str] = None
    is_anonymous: bool = True
    user: Optional[ReviewUserOut] = None
    reply_content: Optional[str] = None
    reply_time: Optional[datetime] = None
    reply_user_id: Optional[int] = None
    create_time: datetime

    class Config:
        from_attributes = True
