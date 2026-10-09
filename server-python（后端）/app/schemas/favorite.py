from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FavoriteToggle(BaseModel):
    dish_id: int


class FavoriteCreate(BaseModel):
    user_id: int
    dish_id: int


class DishInFavorite(BaseModel):
    """收藏列表中的菜品信息"""
    dish_id: int
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    images: Optional[str] = None
    stock: int
    sales: int = 0
    status: int
    spicy_level: int = 0
    calorie: Optional[int] = None
    canteen_id: int
    
    class Config:
        from_attributes = True


class FavoriteOut(BaseModel):
    favorite_id: int
    dish_id: int
    user_id: int
    create_time: datetime
    dish: Optional[DishInFavorite] = None  # 包含菜品详细信息

    class Config:
        from_attributes = True


