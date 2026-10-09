from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.dish import DishOut


class CartItemIn(BaseModel):
    dish_id: int
    quantity: int
    remark: Optional[str] = None


class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    remark: Optional[str] = None


class CartItemOut(BaseModel):
    item_id: int
    dish_id: int
    dish_name: str
    price: float  # 修复：以元为单位，与菜品表保持一致
    quantity: int
    remark: Optional[str] = None
    create_time: datetime
    dish: Optional[DishOut] = None  # 添加完整的菜品信息

    class Config:
        from_attributes = True


